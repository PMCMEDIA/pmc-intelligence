"""Read-only StrategyIQ completion checks for editable PMC presentation export.

Checks are informational and do not mutate a saved project or approvals.
"""
from pmc_template_library import template_status, validate_slide

def export_readiness(project):
    template = template_status()
    outline = project.get('deck_outline') or []
    included = [slide for slide in outline if isinstance(slide, dict) and slide.get('include', True)]
    departments = list((project.get('strategy') or {}).get('departments', {}))
    approved = project.get('department_approvals') or {}
    issues = []
    warnings = []
    if not template.get('ready'):
        issues.append('Approved PMC master PowerPoint is unavailable.')
    if not included:
        issues.append('Build a draft presentation before exporting.')
    master_count = sum(bool(slide.get('template_key')) for slide in included)
    if included and master_count != len(included):
        issues.append('This presentation contains legacy slides; rebuild with the approved PMC master.')
    for index, slide in enumerate(included, 1):
        if not slide.get('template_key'):
            continue
        try:
            validate_slide(slide)
        except (ValueError, TypeError, KeyError) as error:
            issues.append('Slide {}: {}'.format(index, error))
    if project.get('deck_needs_review'):
        warnings.append('The strategy changed after the draft deck was built. Review and rebuild as needed.')
    unapproved = [name for name in departments if not approved.get(name)]
    if unapproved:
        warnings.append('Departments awaiting approval: ' + ', '.join(unapproved))
    if not project.get('competitive_intelligence'):
        warnings.append('Competitive research has not been added to this project.')
    if not project.get('campaign_outlook'):
        warnings.append('Industry benchmark and KPI forecast has not been generated.')
    if not project.get('investment_allocations'):
        warnings.append('Investment allocations have not been completed.')
    return {
        'ready_for_master_export': not issues,
        'ready_for_final_approval': not issues and not warnings,
        'blocking_issues': issues,
        'review_warnings': warnings,
        'included_slides': len(included),
        'master_slides': master_count,
        'departments': len(departments),
        'approved_departments': len(departments) - len(unapproved),
        'template': template,
    }
