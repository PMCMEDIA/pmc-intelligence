"""Theme regression checks against real templates/CSS, with no live project access."""
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from hub_browser import Handler

ROOT = Path(__file__).resolve().parents[1]

class ThemeRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = 'http://127.0.0.1:' + str(cls.server.server_port)
        cls.pw = sync_playwright().start()
        opts = {'headless': True}
        if os.getenv('CHROMIUM_PATH'):
            opts['executable_path'] = os.environ['CHROMIUM_PATH']
        cls.browser = cls.pw.chromium.launch(**opts)
        (ROOT / 'artifacts').mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def check_button(self, page):
        button = page.locator('#themeToggle')
        self.assertEqual(button.count(), 1)
        expect(button).to_be_visible()
        self.assertTrue(button.evaluate('''e => {
            const r=e.getBoundingClientRect();
            return r.height>=44 && r.x>=0 && r.right<=innerWidth+1 &&
              e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));
        }'''))
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1'))
        return button

    def test_home_control_colors_and_persistence_at_all_breakpoints(self):
        for signed in (0, 1):
            for width in (320, 375, 430, 768, 1099, 1100, 1440, 1920):
                with self.subTest(signed=signed, width=width):
                    context = self.browser.new_context(viewport={'width': width, 'height': 950})
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda err: errors.append(str(err)))
                    page.route('**/api/**', lambda route: route.fulfill(json=[]))
                    try:
                        page.goto(self.origin + '/?signed=' + str(signed) + '#hub')
                        expect(page.locator('#hubHome')).to_be_visible()
                        button = self.check_button(page)
                        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
                        light = page.locator('.launch-tile').first.evaluate('(e)=>getComputedStyle(e).backgroundColor')
                        button.click()
                        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
                        dark = page.locator('.launch-tile').first.evaluate('(e)=>getComputedStyle(e).backgroundColor')
                        self.assertNotEqual(light, dark)
                        self.assertEqual(page.evaluate('localStorage.getItem("pmc-theme")'), 'dark')
                        page.reload()
                        expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
                        self.check_button(page)
                        if width >= 1100:
                            self.assertAlmostEqual(page.locator('.launch-hero').bounding_box()['y'], 0, delta=1)
                        if signed == 1 and width in (375, 1440):
                            page.screenshot(path=str(ROOT / 'artifacts' / f'theme-restored-{width}-dark.png'), animations='disabled')
                        button.click()
                        expect(page.locator('html')).to_have_attribute('data-theme', 'light')
                        if signed == 1 and width in (375, 1440):
                            page.screenshot(path=str(ROOT / 'artifacts' / f'theme-restored-{width}-light.png'), animations='disabled')
                        self.assertEqual(errors, [])
                    finally:
                        context.close()

    def test_theme_switch_does_not_clear_intake_and_workspace_palette_changes(self):
        context = self.browser.new_context(viewport={'width': 1440, 'height': 950})
        page = context.new_page()
        page.route('**/api/**', lambda route: route.fulfill(json=[]))
        try:
            page.goto(self.origin + '/?signed=1#strategy')
            field = page.locator('#intakeForm input[name="client"]')
            field.fill('Keep this unsaved client brief')
            light = field.evaluate('(e)=>getComputedStyle(e).backgroundColor')
            self.check_button(page).click()
            dark = field.evaluate('(e)=>getComputedStyle(e).backgroundColor')
            self.assertNotEqual(light, dark)
            expect(field).to_have_value('Keep this unsaved client brief')
            page.locator('#hubSidebar [data-hub-link="hub"]').first.click()
            self.check_button(page).click()
            page.locator('#hubSidebar [data-hub-link="strategy"]').first.click()
            expect(field).to_have_value('Keep this unsaved client brief')
            expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        finally:
            context.close()

if __name__ == '__main__':
    unittest.main(verbosity=2)
