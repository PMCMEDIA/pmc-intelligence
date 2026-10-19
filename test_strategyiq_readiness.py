import unittest
from unittest.mock import patch
from strategyiq_readiness import export_readiness

class ReadinessTests(unittest.TestCase):
    @patch('strategyiq_readiness.template_status', return_value={'ready':True})
    def test_missing_deck_blocks_export(self, _):
        result=export_readiness({'strategy':{'departments':{'SEO / AEO':['Improve search']}}})
        self.assertFalse(result['ready_for_master_export'])
        self.assertTrue(any('draft presentation' in x for x in result['blocking_issues']))
        self.assertFalse(result['ready_for_final_approval'])

    @patch('strategyiq_readiness.template_status', return_value={'ready':True})
    def test_legacy_slides_not_master_ready(self, _):
        result=export_readiness({'deck_outline':[{'title':'Legacy','include':True}]})
        self.assertFalse(result['ready_for_master_export'])

    @patch('strategyiq_readiness.validate_slide')
    @patch('strategyiq_readiness.template_status', return_value={'ready':True})
    def test_master_slide_ready_but_review_pending(self, _, validate):
        result=export_readiness({'deck_outline':[{'template_key':'cover','include':True}],
          'strategy':{'departments':{'Digital Media':['Search']}},
          'department_approvals':{'Digital Media':False}})
        self.assertTrue(result['ready_for_master_export'])
        self.assertFalse(result['ready_for_final_approval'])
        validate.assert_called_once()

    @patch('strategyiq_readiness.validate_slide')
    @patch('strategyiq_readiness.template_status', return_value={'ready':True})
    def test_valid_complete_project(self, _, validate):
        result=export_readiness({'deck_outline':[{'template_key':'cover','include':True}],
          'strategy':{'departments':{'SEO / AEO':['Content']}},
          'department_approvals':{'SEO / AEO':True},
          'competitive_intelligence':{'candidates':[]},
          'campaign_outlook':{'scenarios':[]},
          'investment_allocations':[{'department':'SEO / AEO','amount':1000}]})
        self.assertTrue(result['ready_for_final_approval'])

if __name__ == '__main__':
    unittest.main()
