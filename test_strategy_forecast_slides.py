import unittest
from unittest.mock import patch
from proposal_blueprint import default_outline

def sample(roi=False):
    return {
      'client':'Example Client',
      'strategy':{'executive':'Increase qualified demand.',
                  'departments':{'Digital Media':['Paid search']},
                  'department_sections':{'Digital Media':{'objective':'Generate qualified leads'}}},
      'campaign_outlook':{'source_type':'Modeled Assumption','roi_ready':roi,
        'scenarios':[{'scenario':'Expected','search_budget':1000,'cpc':5,
          'clicks':200,'conversion_rate':5,'conversions':10,'cpa':100,
          'projected_revenue':5000,'roas':5,'roi_percent':400}]}
    }

class ForecastSlidesTests(unittest.TestCase):
    @patch('proposal_blueprint.template_status',return_value={'ready':True})
    @patch('proposal_blueprint.make_slide')
    def test_kpi_values_are_present_and_labeled(self, make, status):
        def slide(key,fields,title=None,department=None,rows=None):
            return {'template_key':key,'fields':fields,'title':title,'include':True}
        make.side_effect=slide
        result=default_outline(sample())
        copy='\n'.join(x.get('fields',{}).get('copy','') for x in result)
        self.assertIn('Estimated conversions: 10',copy)
        self.assertIn('NOT independently sourced benchmarks',copy)
        self.assertNotIn('ROI Scenario Outlook',str([x['title'] for x in result]))
    @patch('proposal_blueprint.template_status',return_value={'ready':True})
    @patch('proposal_blueprint.make_slide')
    def test_roi_requires_explicit_readiness(self, make, status):
        make.side_effect=lambda key,fields,title=None,department=None,rows=None:{'template_key':key,'fields':fields,'title':title,'include':True}
        result=default_outline(sample(roi=True))
        self.assertTrue(any(x['title']=='ROI Scenario Outlook' for x in result))
        copy='\n'.join(x.get('fields',{}).get('copy','') for x in result)
        self.assertIn('Modeled revenue: $5,000',copy)

if __name__=='__main__':unittest.main()
