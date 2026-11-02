import unittest
from unittest.mock import patch
from ai_research_planner import research_plan, enabled

class AIPlannerTests(unittest.TestCase):
    @patch('ai_research_planner._request')
    def test_filters_unsourced_benchmarks_and_reconciles_budget(self, request):
        request.return_value={
            'benchmarks':[{'metric':'CPC','value':4,'source_url':'https://example.org/research'},
                          {'metric':'CTR','value':2,'source_url':''}],
            'research_findings':[], 'competitors':[],
            'recommended_budget':{'total':10000,'period':'monthly'},
            'department_allocations':[{'department':'Digital Media','amount':6000},
                                      {'department':'SEO / AEO','amount':4000}],
            'uncertainties':[]
        }
        result=research_plan({'client':'Test Client','industry':'Other'})
        self.assertEqual(len(result['benchmarks']),1)
        self.assertEqual(sum(x['amount'] for x in result['department_allocations']),10000)
        self.assertEqual(result['approval_status'],'Unapproved recommendations')

    @patch('ai_research_planner._request')
    def test_mismatched_allocation_does_not_apply(self, request):
        request.return_value={'recommended_budget':{'total':10000},
                              'department_allocations':[{'department':'Digital Media','amount':4000}]}
        result=research_plan({'client':'Test'})
        self.assertEqual(result['department_allocations'],[])
        self.assertTrue(result['uncertainties'])

    @patch.dict('os.environ',{'OPENAI_API_KEY':''})
    def test_not_enabled_without_key(self):
        self.assertFalse(enabled())

if __name__=='__main__':
    unittest.main()
