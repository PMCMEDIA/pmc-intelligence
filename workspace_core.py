"""Non-destructive project updates for the two strategy workspace views."""
import copy
import hashlib
import json
import math

EDITABLE = {
    'workspace_mode', 'strategy', 'department_details', 'department_approvals',
    'discovery_answers', 'investment_allocations', 'tactic_allocations',
    'website_pricing', 'forecast_inputs', 'deck_outline', 'deck_branding',
    'strategy_approved', 'investment_approved', 'tactics_approved',
    'measurement_approved', 'workspace_locks', 'deck_needs_review',
    'budget', 'goal', 'strategy_context', 'status',
}
CONTENT = {
    'strategy', 'department_details', 'investment_allocations', 'tactic_allocations',
    'website_pricing', 'forecast_inputs', 'budget', 'goal', 'strategy_context',
}
OBJECTS = {
    'strategy', 'department_details', 'department_approvals', 'tactic_allocations',
    'website_pricing', 'forecast_inputs', 'deck_branding', 'workspace_locks',
}
ARRAYS = {'discovery_answers', 'investment_allocations', 'deck_outline'}
FLAGS = {'strategy_approved', 'investment_approved', 'tactics_approved', 'measurement_approved', 'deck_needs_review'}


def revision(project):
    return hashlib.sha256(json.dumps(project, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def apply_patch(project, patch):
    """A mode-only change never changes recommendations, pricing or approvals."""
    if not isinstance(patch, dict) or set(patch) - EDITABLE:
        raise ValueError('Unrecognized project fields.')
    if 'workspace_mode' in patch and patch['workspace_mode'] not in ('ai', 'advanced'):
        raise ValueError('Choose AI Strategy or Advanced Builder.')
    for key in OBJECTS & patch.keys():
        if not isinstance(patch[key], dict):
            raise ValueError(key + ' must be an object.')
    for key in ARRAYS & patch.keys():
        if not isinstance(patch[key], list):
            raise ValueError(key + ' must be a list.')
    for key in FLAGS & patch.keys():
        if not isinstance(patch[key], bool):
            raise ValueError(key + ' must be true or false.')
    # Reject invalid numeric values before they can reach budgeting or export.
    def check_numbers(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Numbers must be finite.')
        if isinstance(value, dict):
            for v in value.values(): check_numbers(v)
        elif isinstance(value, list):
            for v in value: check_numbers(v)
    check_numbers(patch)
    if 'strategy' in patch:
        strategy = patch['strategy']
        if not isinstance(strategy.get('departments', {}), dict) or not isinstance(strategy.get('department_sections', {}), dict):
            raise ValueError('Strategy departments and sections must be objects.')
        if any(not isinstance(v, list) or any(not isinstance(x, str) for x in v) for v in strategy.get('departments', {}).values()):
            raise ValueError('Department recommendations must be lists of text.')
    for row in patch.get('investment_allocations', []):
        if not isinstance(row, dict) or not isinstance(row.get('department'), str):
            raise ValueError('Each allocation needs a department.')
        for key in ('amount', 'percent'):
            value = row.get(key)
            if value is not None and (not isinstance(value, (int, float)) or value < 0):
                raise ValueError('Allocations cannot be negative.')
    result = copy.deepcopy(project)
    result.update(copy.deepcopy(patch))
    if CONTENT & patch.keys():
        changed = {key for key in CONTENT & patch.keys() if project.get(key) != result.get(key)}
        if changed:
            result['deck_needs_review'] = bool(project.get('deck_outline'))
            result['measurement_approved'] = False
        before = (project.get('strategy') or {}).get('departments', {})
        after = (result.get('strategy') or {}).get('departments', {})
        old_sections = (project.get('strategy') or {}).get('department_sections', {})
        new_sections = (result.get('strategy') or {}).get('department_sections', {})
        approvals = result.setdefault('department_approvals', {})
        for name in set(before) | set(after):
            if before.get(name) != after.get(name) or old_sections.get(name) != new_sections.get(name) or (project.get('department_details') or {}).get(name) != (result.get('department_details') or {}).get(name):
                approvals[name] = False
        if changed & {'goal', 'strategy_context'}:
            for name in after: approvals[name] = False
            result['strategy_approved'] = False
        if 'strategy' in changed and (project.get('strategy') or {}).get('executive') != (result.get('strategy') or {}).get('executive'):
            for name in after:
                approvals[name] = False
        if changed & {'investment_allocations', 'tactic_allocations', 'website_pricing', 'budget'}:
            result['investment_approved'] = False
            result['tactics_approved'] = False
        if changed & {'strategy', 'department_details'}:
            result['strategy_approved'] = bool(after) and all(approvals.get(name) for name in after)
    return result


def synchronize_sections(project):
    """Manual department edits take precedence in both preview and export."""
    result = copy.deepcopy(project)
    strategy = result.setdefault('strategy', {})
    sections = strategy.setdefault('department_sections', {})
    for name, recommendations in strategy.get('departments', {}).items():
        section = sections.setdefault(name, {})
        section['tactics'] = list(recommendations)
        section['recommendations'] = list(recommendations)
        details = (result.get('department_details') or {}).get(name, {})
        for field, destination in [('objective', 'objective'), ('kpis', 'success')]:
            if field in details:
                section[destination] = details[field]
    return result
