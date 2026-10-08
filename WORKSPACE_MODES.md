# AI Strategy / Advanced Builder

Release: workspace-modes-1

The default home screen presents the saved, generated strategy immediately; no discovery answer or approval gate hides it. Advanced Builder edits the same project, not a duplicate. Existing projects without workspace_mode default to ai. A saved explicit advanced preference is retained.

Changes use field-scoped patches and a SHA-256 revision check inside a SQLite write transaction. Switching modes alone does not alter recommendations, pricing or approvals. Errors and stale-save conflicts retain the browser's unsaved content. This protects new workspace saves; legacy full-project save endpoints are unchanged and do not gain multi-user conflict protection in this release.

Section suggestions are read-only until explicitly accepted. Draft decks can be built before approval. Existing edited outlines are reused unless explicitly rebuilt; one prior outline is retained for restoration. Manual objectives, KPI copy and recommendation lists take precedence when drafting.

The existing strategy generator is rule/template-based, not a newly connected LLM. Exact preservation of the DeQuattro/Viva master presentation is NOT implemented by this change. Social auditing/pricing and production dependency pricing remain separate work. The UI labels these limitations. It does not invent missing forecasts, prices or research.

No database schema, storage path, project ID, account or disk is changed. The prior interface remains at /classic. The existing session-based authentication is unchanged; this is not an authentication-hardening release.

Validation: Python compile checks, Node syntax check, 15 local core unit tests, and Chromium fixture tests for mode switches, pricing retention, manual edits, suggestion cancellation, draft-before-approval, slide edits, dark mode, 375px single-column/no-overflow layout and conflict retention. Flask/SQLite route and export tests run in GitHub Actions using requirements.txt. Fixture browser tests do not claim live research or live Render verification.
