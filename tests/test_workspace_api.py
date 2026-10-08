"""Integration tests run with the application's actual Flask/SQLite dependencies."""
import copy
import json
import os
import tempfile
import unittest
from unittest.mock import patch

# The CI job uses a separate test database, never live project data.
_tmp = tempfile.TemporaryDirectory()
os.environ['DATABASE_PATH'] = os.path.join(_tmp.name, 'projects.db')
os.environ['SECRET_KEY'] = 'test-only-workspace-key'
from app import app
from storage import get, save
from workspace_core import revision
from test_workspace_core import sample


class WorkspaceApiTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.project = sample()
        self.project['workflow_version'] = 1
        self.project['measurement_approved'] = False
        save('test@pmcne.com', self.project)
        with self.client.session_transaction() as session:
            session['owner'] = 'test@pmcne.com'
        self.base = '/api/projects/sample/workspace'

    def saved(self): return get('test@pmcne.com', 'sample')
    def body(self, **extra): return {'revision': revision(self.saved()), **extra}

    def test_home_contains_two_modes(self):
        data = self.client.get('/').get_data(as_text=True)
        self.assertIn('AI Strategy', data)
        self.assertIn('Advanced Builder', data)
        self.assertIn('workspace_modes.js', data)
        self.assertNotIn('Waiting for Department Approvals', data)

    def test_unauthenticated(self):
        self.assertEqual(app.test_client().get(self.base).status_code, 401)

    def test_missing_project(self):
        self.assertEqual(self.client.get('/api/projects/missing/workspace').status_code, 404)

    def test_mode_patch_changes_only_view(self):
        before = self.saved()
        r = self.client.post(self.base, json=self.body(patch={'workspace_mode':'advanced'}))
        self.assertEqual(r.status_code, 200)
        after = self.saved()
        self.assertEqual({k:v for k,v in after.items() if k!='workspace_mode'}, before)

    def test_conflict_rejects_stale_session(self):
        first = self.body(patch={'workspace_mode':'advanced'})
        self.assertEqual(self.client.post(self.base, json=first).status_code, 200)
        first['patch'] = {'budget':'99999'}
        self.assertEqual(self.client.post(self.base, json=first).status_code, 409)
        self.assertNotEqual(self.saved().get('budget'), '99999')

    def test_suggestion_does_not_change_project(self):
        before = self.saved()
        with patch('workspace_api.build_strategy', return_value={'executive':'Suggested change'}):
            r = self.client.post(self.base+'/suggestion', json={'section':'executive'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(before, self.saved())

    def test_draft_preserves_edited_outline_before_approval(self):
        before = self.saved()
        r = self.client.post(self.base+'/deck', json=self.body())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.saved()['deck_outline'], before['deck_outline'])
        self.assertEqual(self.saved()['department_approvals'], before['department_approvals'])
        self.assertEqual(self.saved()['workflow_version'], 2)
        self.assertEqual(self.client.get('/api/projects/sample/deck.pptx').status_code, 200)

    def test_explicit_rebuild_and_restore(self):
        before = self.saved()['deck_outline']
        r = self.client.post(self.base+'/deck', json=self.body(rebuild=True))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.saved()['previous_deck_outline'], before)
        rebuilt = copy.deepcopy(self.saved()['deck_outline'])
        r = self.client.post(self.base+'/restore-deck', json=self.body())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.saved()['deck_outline'], before)
        self.assertEqual(self.saved()['previous_deck_outline'], rebuilt)

    def test_bad_payloads_rejected(self):
        self.assertEqual(self.client.post(self.base, json={'revision':'x','patch':{'id':'other'}}).status_code, 409)
        for suffix in ['/deck','/suggestion','/restore-deck']:
            self.assertEqual(self.client.post(self.base+suffix, json=[]).status_code, 400)

    def test_cross_origin_writes_rejected(self):
        r = self.client.post(self.base, json=self.body(patch={'workspace_mode':'advanced'}), headers={'Origin':'https://elsewhere.example'})
        self.assertEqual(r.status_code, 403)

    def test_new_project_defaults_to_ai_without_questions(self):
        with patch('app.research_url', return_value={'ok':False,'error':'Fixture'}):
            r = self.client.post('/api/projects', json={'client':'Local fixture', 'industry':'Other'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['workspace_mode'], 'ai')
        self.assertTrue(r.json['strategy']['departments'])
        self.assertFalse(r.json.get('discovery_answers'))

if __name__=='__main__':unittest.main()
