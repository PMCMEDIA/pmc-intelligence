import copy
import unittest
from workspace_core import apply_patch, revision, synchronize_sections


def sample():
    return {'id':'sample', 'client':'Example', 'created_by':'sample@pmcne.com',
            'strategy':{'executive':'Edited executive', 'departments':{'Digital Media':['Search'], 'Production':['Film']},
                        'department_sections':{'Digital Media':{'tactics':['Outdated'], 'objective':'Original'}}},
            'department_details':{'Digital Media':{'objective':'Edited objective', 'kpis':'Qualified leads'}},
            'department_approvals':{'Digital Media':True,'Production':True}, 'strategy_approved':True,
            'investment_allocations':[{'department':'Digital Media','amount':3000,'percent':100}],
            'investment_approved':True, 'tactics_approved':True, 'measurement_approved':True,
            'deck_outline':[{'title':'Edited slide','body':'Manual copy','include':True}],
            'website_pricing':{'pages':20,'page_rate':850}, 'custom_field':'Preserve me'}


class WorkspaceCoreTests(unittest.TestCase):
    def test_default_project_read_does_not_require_mode(self):
        self.assertNotIn('workspace_mode', sample())
    def test_mode_change_preserves_all_other_fields(self):
        p=sample(); updated=apply_patch(p,{'workspace_mode':'advanced'})
        self.assertEqual({k:v for k,v in updated.items() if k!='workspace_mode'},p)
    def test_mode_switch_does_not_mutate_original(self):
        p=sample(); before=copy.deepcopy(p); apply_patch(p,{'workspace_mode':'ai'});self.assertEqual(before,p)
    def test_invalid_mode(self):
        with self.assertRaises(ValueError): apply_patch(sample(),{'workspace_mode':'bogus'})
    def test_cannot_change_identity(self):
        with self.assertRaises(ValueError): apply_patch(sample(),{'id':'other'})
    def test_reject_wrong_shapes(self):
        for patch in [{'strategy':[]},{'deck_outline':{}},{'strategy_approved':'yes'}]:
            with self.assertRaises(ValueError): apply_patch(sample(),patch)
    def test_invalid_recommendations(self):
        with self.assertRaises(ValueError): apply_patch(sample(),{'strategy':{'departments':{'Digital Media':'wrong'}}})
    def test_reject_nonfinite_and_negative(self):
        for amount in [-1,float('inf'),float('nan')]:
            with self.assertRaises(ValueError): apply_patch(sample(),{'investment_allocations':[{'department':'Digital Media','amount':amount}]})
    def test_changed_department_reopens_only_affected_approval(self):
        p=sample(); s=copy.deepcopy(p['strategy']);s['departments']['Digital Media']=['Paid Social']
        changed=apply_patch(p,{'strategy':s})
        self.assertFalse(changed['department_approvals']['Digital Media'])
        self.assertTrue(changed['department_approvals']['Production'])
        self.assertTrue(changed['deck_needs_review'])
        self.assertEqual(changed['deck_outline'],p['deck_outline'])
    def test_executive_change_reopens_departments(self):
        p=sample();s=copy.deepcopy(p['strategy']);s['executive']='New copy'
        changed=apply_patch(p,{'strategy':s})
        self.assertFalse(any(changed['department_approvals'].values()))
    def test_budget_edit_flags_review_without_erasing_prices(self):
        p=sample();changed=apply_patch(p,{'budget':'5000 monthly'})
        self.assertFalse(changed['investment_approved']);self.assertFalse(changed['tactics_approved'])
        self.assertEqual(p['website_pricing'],changed['website_pricing'])
    def test_unknown_fields_preserved(self):
        self.assertEqual(apply_patch(sample(),{'workspace_mode':'ai'})['custom_field'],'Preserve me')
    def test_manual_edits_win_in_export(self):
        p=synchronize_sections(sample());s=p['strategy']['department_sections']['Digital Media']
        self.assertEqual(s['tactics'],['Search']);self.assertEqual(s['objective'],'Edited objective');self.assertEqual(s['success'],'Qualified leads')
    def test_revision_order_stable_and_content_sensitive(self):
        p=sample();self.assertEqual(revision(p),revision(dict(reversed(list(p.items())))))
        q=copy.deepcopy(p);q['status']='New';self.assertNotEqual(revision(p),revision(q))
    def test_same_content_does_not_reopen_approval(self):
        p=sample();self.assertTrue(apply_patch(p,{'strategy':copy.deepcopy(p['strategy'])})['measurement_approved'])

if __name__=='__main__':unittest.main()
