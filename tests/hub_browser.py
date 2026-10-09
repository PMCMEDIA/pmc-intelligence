"""Browser regression tests with fixture API responses; never read or mutate live projects."""
import copy
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest
from urllib.parse import urlparse, parse_qs
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ENV = Environment(loader=FileSystemLoader(ROOT / 'templates'), autoescape=select_autoescape(['html']))
ENV.globals['url_for'] = lambda endpoint, filename: '/static/' + filename
PROJECT = {'id':'hub-fixture','client':'Sidebar QA Client','industry':'Professional Services','status':'Draft','workspace_mode':'ai',
 'goal':'Qualified inquiries','budget':'$5,000 monthly','strategy':{'executive':'Original strategy summary.','facts':[],
 'departments':{'Digital Media':['Google Search'],'SEO / AEO':['Priority page improvements'],'Creative / Website':['Website conversion paths']},
 'department_sections':{}},'department_details':{},'department_approvals':{},
 'investment_allocations':[{'department':'Digital Media','amount':5000,'percent':100}],
 'tactic_allocations':{'Digital Media':[{'name':'Google Search','percent':100,'kpi':'Qualified inquiries'}]},
 'website_pricing':{'pages':4,'page_rate':850,'discovery':500,'templates':2,'mockup_rate':400,'technical':0,'adjustment':0,'notes':''}}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            logged = parse_qs(parsed.query).get('signed', ['1'])[0] == '1'
            data = ENV.get_template('workspace.html').render(logged_in=logged, login_error='').encode()
            mime = 'text/html'
        elif parsed.path.startswith('/static/'):
            path = (ROOT / parsed.path.lstrip('/')).resolve()
            if not path.is_relative_to((ROOT / 'static').resolve()) or not path.is_file():
                self.send_error(404); return
            data = path.read_bytes(); mime = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        else:
            self.send_error(404); return
        self.send_response(200); self.send_header('Content-Type', mime); self.end_headers(); self.wfile.write(data)

class HubBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.origin = 'http://127.0.0.1:' + str(cls.server.server_port)
        cls.pw = sync_playwright().start()
        opts = {'headless':True}
        if os.getenv('CHROMIUM_PATH'): opts['executable_path'] = os.environ['CHROMIUM_PATH']
        cls.browser = cls.pw.chromium.launch(**opts)
    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.server.shutdown(); cls.server.server_close()
    def setUp(self):
        self.context = self.browser.new_context(viewport={'width':1440,'height':950})
        self.page = self.context.new_page(); self.errors = []; self.project = copy.deepcopy(PROJECT); self.revision = 1; self.writes = 0
        self.page.on('pageerror', lambda error:self.errors.append(str(error)))
        self.page.route('**/api/**', self.api)
    def tearDown(self):
        self.context.close(); self.assertEqual(self.errors, [])
    def api(self, route):
        request = route.request; path = urlparse(request.url).path
        if path == '/api/projects': data = [{'id':self.project['id'],'client':self.project['client'],'owner':'fixture@pmcne.com','status':'Draft'}]
        elif path.endswith('/workspace'):
            if request.method == 'POST':
                body = request.post_data_json
                if body['revision'] != str(self.revision):
                    route.fulfill(status=409,json={'error':'Conflicting save'}); return
                self.project.update(body['patch']); self.revision += 1; self.writes += 1
            data = {'project':self.project,'revision':str(self.revision)}
        elif path.endswith('/workspace/deck'):
            self.project['deck_outline'] = [{'title':'Fixture Strategy Deck','body':'Saved draft copy','type':'content','include':True}]
            self.revision += 1; data = {'project':self.project,'revision':str(self.revision)}
        else: route.fulfill(status=404,json={'error':'Not part of this fixture'}); return
        route.fulfill(json=data)
    def assert_no_overflow(self):
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1'))
    def go(self, route):
        if self.page.viewport_size['width'] < 1100: self.page.locator('#sidebarToggle').click()
        self.page.locator('#hubSidebar [data-hub-link="'+route+'"]').first.click()
        expect(self.page.locator('[data-hub-panel="'+route+'"]')).to_be_visible()
    def test_desktop_tools_and_history(self):
        p = self.page; p.goto(self.origin)
        expect(p.locator('#hubHome')).to_be_visible()
        (ROOT/'artifacts').mkdir(exist_ok=True)
        p.screenshot(path=str(ROOT/'artifacts/approved-hub-desktop.png'), animations='disabled')
        expect(p.locator('#hubSidebar')).to_be_visible()
        expect(p.locator('#sidebarToggle')).to_be_hidden()
        self.assertEqual(p.locator('.rocket-future-nav a').count(), 7)
        expect(p.locator('#hubHome')).to_contain_text('Launch smarter.')
        self.assertEqual(p.locator('.launch-tile').count(), 8)
        first = p.locator('.launch-tile').nth(0).bounding_box()
        fourth = p.locator('.launch-tile').nth(3).bounding_box()
        fifth = p.locator('.launch-tile').nth(4).bounding_box()
        self.assertAlmostEqual(first['y'], fourth['y'], delta=1)
        self.assertGreater(fifth['y'], first['y'] + 150)
        expect(p.locator('.launch-bottom')).to_contain_text('Mission Control')
        hero_box = p.locator('.launch-hero').bounding_box()
        self.assertGreater(hero_box['height'], 450)
        self.assertIn('rocket-reference-art.webp', p.locator('.launch-hero-art').evaluate("(e) => getComputedStyle(e).backgroundImage"))
        for tool in ['competitoriq','radar','launchpad']:
            self.go(tool); expect(p.locator('#tool-'+tool)).to_contain_text('not an active service'); self.assert_no_overflow()
        (ROOT/'artifacts').mkdir(exist_ok=True)
        p.screenshot(path=str(ROOT/'artifacts/desktop-hub-tools.png'), animations='disabled')
        p.go_back(); expect(p.locator('#tool-radar')).to_be_visible()
        p.go_forward(); expect(p.locator('#tool-launchpad')).to_be_visible()
        self.go('strategy'); expect(p.locator('[data-mode="ai"]')).to_have_attribute('aria-pressed','true')
    def test_mobile_drawer_focus_themes_and_widths(self):
        p = self.page
        for width in [320,375,430,768,1099]:
            p.set_viewport_size({'width':width,'height':812}); p.goto(self.origin)
            self.assert_no_overflow()
            if width == 375:
                (ROOT/'artifacts').mkdir(exist_ok=True)
                p.screenshot(path=str(ROOT/'artifacts/approved-hub-mobile.png'), animations='disabled')
            p.locator('#sidebarToggle').click()
            expect(p.locator('#hubSidebar')).to_have_attribute('role','dialog')
            self.assertTrue(p.locator('#hubFrame').evaluate('(e)=>e.inert'))
            expect(p.locator('#sidebarClose')).to_be_focused()
            p.keyboard.press('Shift+Tab'); expect(p.locator('.sidebar-signout')).to_be_focused()
            p.keyboard.press('Tab'); expect(p.locator('#sidebarClose')).to_be_focused()
            p.wait_for_function("Math.abs(document.getElementById('hubSidebar').getBoundingClientRect().x) < 1")
            self.assert_no_overflow(); p.keyboard.press('Escape')
            expect(p.locator('#sidebarToggle')).to_be_focused()
            self.assertFalse(p.locator('#hubFrame').evaluate('(e)=>e.inert'))
            self.go('radar'); self.assert_no_overflow()
            expect(p.locator('#sidebarToggle')).to_have_attribute('aria-expanded','false')
            p.locator('#themeToggle').click(); expect(p.locator('html')).to_have_attribute('data-theme','dark')
            p.reload(); expect(p.locator('html')).to_have_attribute('data-theme','dark')
            if width == 375:
                p.locator('#sidebarToggle').click()
                (ROOT/'artifacts').mkdir(exist_ok=True)
                p.screenshot(path=str(ROOT/'artifacts/mobile-sidebar-dark.png'), animations='disabled')
                p.keyboard.press('Escape')
            p.locator('#themeToggle').click()
        p.set_viewport_size({'width':375,'height':812}); p.locator('#sidebarToggle').click()
        p.set_viewport_size({'width':1440,'height':950}); self.assert_no_overflow()
        self.assertFalse(p.locator('#hubFrame').evaluate('(e)=>e.inert'))
        self.assertEqual(p.evaluate('document.body.style.position'),'')
    def test_unsaved_project_survives_hub_and_tools(self):
        p = self.page; p.set_viewport_size({'width':375,'height':812}); p.goto(self.origin+'/#strategy')
        p.get_by_role('button',name='Open project',exact=True).click()
        p.locator('[data-mode="advanced"]').click()
        p.get_by_role('textbox',name='Executive summary',exact=True).fill('Manually preserved summary.')
        p.get_by_role('spinbutton',name='Billable development pages',exact=True).fill('12')
        p.get_by_role('textbox',name='Website scope notes',exact=True).fill('Retain this scope.')
        before = self.writes
        for route in ['hub','competitoriq','radar','launchpad','strategy']: self.go(route)
        self.assertEqual(self.writes,before)
        expect(p.get_by_role('textbox',name='Executive summary',exact=True)).to_have_value('Manually preserved summary.')
        expect(p.get_by_role('spinbutton',name='Billable development pages',exact=True)).to_have_value('12')
        expect(p.get_by_role('textbox',name='Website scope notes',exact=True)).to_have_value('Retain this scope.')
        p.locator('#saveProject').click(); expect(p.locator('#saveState')).to_have_text('Saved')
        self.assertEqual(self.project['website_pricing']['pages'],12)
        p.locator('[data-mode="ai"]').click(); expect(p.locator('#projectContent')).to_contain_text('Manually preserved summary.')
        p.locator('#buildDeck').click(); expect(p.locator('#projectContent')).to_contain_text('Fixture Strategy Deck')
        self.assert_no_overflow()
    def test_signed_out_landing_and_tools(self):
        p = self.page; p.set_viewport_size({'width':320,'height':700}); p.goto(self.origin+'/?signed=0')
        expect(p.locator('#loginEmail')).to_be_visible(); self.assert_no_overflow()
        p.locator('#loginEmail').fill('person@pmcne.com')
        self.go('hub'); self.go('launchpad'); self.go('strategy')
        expect(p.locator('#loginEmail')).to_have_value('person@pmcne.com')
        self.assertEqual(p.locator('#workspace').count(),0)

if __name__ == '__main__': unittest.main(verbosity=2)
