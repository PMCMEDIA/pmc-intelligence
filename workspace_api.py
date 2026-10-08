"""Shared state, optimistic concurrency, and non-destructive draft operations."""
from datetime import datetime, timezone
import json
from urllib.parse import urlsplit
from flask import Blueprint, jsonify, request, session
from storage import db, get
from strategy_engine import build_strategy
from deck_engine import default_outline
from workspace_core import apply_patch, revision, synchronize_sections

workspace = Blueprint('workspace', __name__)


def package(project):
    return {'project': project, 'revision': revision(project), 'generation_kind': 'template-guided'}


@workspace.before_request
def require_login():
    if request.method == 'POST' and request.headers.get('Origin'):
        origin = urlsplit(request.headers['Origin'])
        # Render terminates TLS upstream; compare the host rather than the internal scheme.
        if origin.scheme not in ('http', 'https') or origin.netloc.lower() != request.host.lower():
            return jsonify({'error': 'Use the PMC workspace to save changes.'}), 403
    if not session.get('owner'):
        return jsonify({'error': 'Sign in to your PMC workspace.'}), 401


def transaction(pid, change, expected):
    """Compare and update inside the same SQLite write transaction."""
    if not isinstance(expected, str) or not expected:
        return jsonify({'error': 'Reload the saved project before editing.'}), 400
    with db() as connection:
        connection.execute('BEGIN IMMEDIATE')
        row = connection.execute('SELECT data FROM projects WHERE id=?', (pid,)).fetchone()
        if not row:
            return jsonify({'error': 'Project not found.'}), 404
        project = json.loads(row['data'])
        # storage.get adds created_by for legacy records; use identical read/write representations.
        if not project.get('created_by'):
            owner_row = connection.execute('SELECT owner FROM projects WHERE id=?', (pid,)).fetchone()
            project['created_by'] = owner_row['owner']
        if revision(project) != expected:
            return jsonify({'error': 'This shared project changed in another session. Your edits are still on this screen. Reload the saved version before applying them.', 'conflict': True}), 409
        try:
            updated = change(project)
        except ValueError as error:
            return jsonify({'error': str(error)}), 400
        now = datetime.now(timezone.utc).isoformat()
        connection.execute('UPDATE projects SET data=?,status=?,updated_at=? WHERE id=?',
                           (json.dumps(updated), updated.get('status', 'Strategy Draft'), now, pid))
    return jsonify(package(updated))


@workspace.get('/api/projects/<pid>/workspace')
def read_workspace(pid):
    project = get(session['owner'], pid)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
    return jsonify(package(project))


@workspace.post('/api/projects/<pid>/workspace')
def save_workspace(pid):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Expected project JSON.'}), 400
    return transaction(pid, lambda p: apply_patch(p, data.get('patch')), data.get('revision'))


@workspace.post('/api/projects/<pid>/workspace/suggestion')
def suggest_section(pid):
    """Return a suggestion only. This route never changes saved strategy content."""
    project = get(session['owner'], pid)
    if not project:
        return jsonify({'error': 'Project not found.'}), 404
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Expected project JSON.'}), 400
    section = data.get('section')
    if section != 'executive' and section not in (project.get('strategy') or {}).get('departments', {}):
        return jsonify({'error': 'Unknown strategy section.'}), 400
    generated = build_strategy(project, project.get('research') or {})
    candidate = generated.get('executive', '') if section == 'executive' else {
        'recommendations': generated.get('departments', {}).get(section, []),
        'details': generated.get('department_sections', {}).get(section, {}),
    }
    return jsonify({'section': section, 'candidate': candidate, 'revision': revision(project),
                    'note': 'Generated using the current PMC rules and templates. Review before replacing your edited section.'})


@workspace.post('/api/projects/<pid>/workspace/deck')
def draft_deck(pid):
    """Drafts do not require approvals and never overwrite edited slides implicitly."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Expected project JSON.'}), 400
    def change(project):
        rebuild = data.get('rebuild') is True
        if project.get('deck_outline') and not rebuild:
            project['workflow_version'] = max(2, int(project.get('workflow_version') or 1))
            return project
        updated = synchronize_sections(project)
        if updated.get('deck_outline'):
            updated['previous_deck_outline'] = updated['deck_outline']
        updated['deck_outline'] = default_outline(updated)
        updated['deck_needs_review'] = False
        updated['workflow_version'] = max(2, int(updated.get('workflow_version') or 1))
        updated['status'] = 'Draft Deck Ready'
        # Approval flags deliberately remain untouched.
        return updated
    return transaction(pid, change, data.get('revision'))


@workspace.post('/api/projects/<pid>/workspace/restore-deck')
def restore_deck(pid):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Expected project JSON.'}), 400
    def change(project):
        if not project.get('previous_deck_outline'):
            raise ValueError('No previous deck version is available.')
        project['deck_outline'], project['previous_deck_outline'] = project['previous_deck_outline'], project.get('deck_outline', [])
        project['deck_needs_review'] = True
        return project
    return transaction(pid, change, data.get('revision'))
