"""Master-field editors in both views, with local fixtures only."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unittest
from urllib.parse import urlparse
from playwright.sync_api import expect
import hub_browser as base
from proposal_blueprint import default_outline
from workspace_core import apply_patch

class TemplateBrowserTests(unittest.TestCase):
    setUpClass=classmethod(base.HubBrowserTests.setUpClass.__func__)
    tearDownClass=classmethod(base.HubBrowserTests.tearDownClass.__func__)
    setUp=base.HubBrowserTests.setUp
    tearDown=base.HubBrowserTests.tearDown
    assert_no_overflow=base.HubBrowserTests.assert_no_overflow
    go=base.HubBrowserTests.go
    def api(self,route):
        request=route.request;path=urlparse(request.url).path
        if path.endswith('/workspace/deck'):
            self.project['deck_outline']=default_outline(self.project);self.revision+=1
            route.fulfill(json={'project':self.project,'revision':str(self.revision)});return
        if path.endswith('/workspace') and request.method=='POST':
            body=request.post_data_json
            if body['revision']!=str(self.revision):route.fulfill(status=409,json={'error':'Conflict'});return
            self.project=apply_patch(self.project,body['patch']);self.revision+=1;self.writes+=1
            route.fulfill(json={'project':self.project,'revision':str(self.revision)});return
        base.HubBrowserTests.api(self,route)
    def test_default_preview_uses_master_and_mobile_edits_persist(self):
        p=self.page;p.set_viewport_size({'width':375,'height':950});p.goto(self.origin+'/#strategy')
        p.get_by_role('button',name='Open project',exact=True).click()
        p.locator('#buildDeck').click()
        expect(p.locator('#projectContent')).to_contain_text('PMC master connected')
        expect(p.locator('#projectContent')).to_contain_text('reference slide 1')
        p.locator('[data-mode="advanced"]').click()
        field=p.get_by_role('textbox',name='Slide 1 · title',exact=True)
        field.fill('Manual mobile revision\nMarketing Proposal')
        p.locator('#saveProject').click();expect(p.locator('#saveState')).to_have_text('Saved')
        p.locator('[data-mode="ai"]').click()
        expect(p.locator('#projectContent')).to_contain_text('Manual mobile revision')
        self.go('hub');self.go('strategy')
        expect(p.locator('#projectContent')).to_contain_text('Manual mobile revision')
        self.assert_no_overflow()
    def test_fixed_agency_copy_is_not_a_freeform_editor(self):
        p=self.page;p.goto(self.origin+'/#strategy')
        p.get_by_role('button',name='Open project',exact=True).click()
        p.locator('#buildDeck').click();p.locator('[data-mode="advanced"]').click()
        self.assertEqual(p.get_by_role('textbox',name='Slide 2 · copy',exact=True).count(),0)
        expect(p.locator('#projectContent')).to_contain_text('Approved agency copy')
        expect(p.locator('#projectContent')).to_contain_text('This is where brand gravity is born.')
        self.assert_no_overflow()

if __name__=='__main__':unittest.main(verbosity=2)
