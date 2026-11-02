# PMC Intelligence

Internal strategy-building application for PMC Media Group.

## Current milestone
- New client intake
- Public website research
- Smart discovery questions
- Department strategy workspace
- Editable PowerPoint export architecture

## Deployment
Designed for Render using `gunicorn app:app`.

> Important: add the approved PMC master PowerPoint at `templates/PMC_Master_Strategy.pptx` before enabling deck export.

## AI research and planning (optional)

Set `OPENAI_API_KEY` in the Render service environment to enable the AI planning
endpoint. Optionally set `PMC_RESEARCH_MODEL` (default `gpt-4.1`).
The configured model/account must support Responses API web search, and the
service needs outbound access to `api.openai.com`. Never commit the key.

On new client creation, the UI saves the base strategy first and then requests
an AI research plan when configured. A research failure does not delete the
project. The plan can also be refreshed from the AI Strategy screen.

Research plans include source links, competitor observations, benchmark rows,
recommended budgets and allocations, website scope, social and production
deliverables, and KPI scenarios. They remain **unapproved drafts**. The team
must verify sources, costs, scope and client economics. The budget action copies
proposed allocations into the editable investment builder only after user
confirmation; it never silently overwrites approved work.

Production and social pricing must use verified PMC rates. When no rates are
available, estimates should be null, not fabricated. AI-recommended website
page counts are scope estimates, not counts of sitemap URLs. The existing
forecast engine remains a separate assumption-based model until sourced
benchmarks are integrated into its calculations.

Deployment checks: configure the key, create a test project, confirm source
links and reconciliation, test the apply-budget action, verify project reopen
and deck export, and review request costs and timeouts.
