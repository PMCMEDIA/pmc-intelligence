# PMC master-driven draft decks

Release: `pmc-master-v1`

## Source of truth

The existing tracked `PMC_Intelligence_Local_Test_FIXED (1).zip` includes the
86-slide approved PMC strategy reference at
`PMC_Intelligence_Local_Test_FIXED/master/PMC_Master_Strategy.pptx`.
The renderer pins the nested PowerPoint to SHA-256
`5235c0d4977c26481d971f6c2c65c07ca838407eda8f5c3ba583f3ef293d61e4`.
Selected slide XML and content match the later uploaded DeQuattro reference.
The uploaded copy differs in saved dates and font packaging; those metadata and
font binaries are not carried into new decks.

No new external template download, credential, disk path, or database migration
is required. Changing the source template requires reviewing the shape mappings
and updating the pin. The authenticated `/api/strategy-template` and public health
check report availability; they do not return client content or the source file.

## What this release does

- Uses actual editable PMC slide XML, agency artwork, themes and standard copy.
- Maps 18 reusable master layouts to one saved project, preview and PowerPoint.
- Keeps source cover/agency/executive/department/channel/SEO/social/creative/web/
  investment/closing order, selecting only the scoped channels and departments.
- Derives an asset-requirements slide from the channel deliverables specified by
  PMC. These requirements are not a completed shoot schedule or price quote.
- Carries the saved website estimate into a native editable table: discovery,
  unique mockup templates, billable pages at the saved rate (default $850),
  technical work and adjustment. Other allocation periods stay unconfirmed when
  no period was saved. Website pricing is not automatically added again to media.
- Keeps the same field values in Advanced Builder, AI preview and exported file.
- Uses bounded fields, text splitting, conservative fit checks and explicit
  errors instead of dropping text. Some editable text bounds and paragraph
  styles are normalized to prevent source-slide overlaps with new client copy.

## Existing projects and edits

Existing saved legacy outlines are not silently replaced. `Build draft deck`
continues to open them. `Rebuild from current strategy` explicitly adopts the
master library and retains the previous outline for restoration.

Advanced Builder edits dynamic slide fields and four-column investment table
cells. Fixed agency copy is read-only in the app and remains editable as native
PowerPoint objects after export. Excluding and reordering slides are supported.
A field edit is a deck-level edit: changing it does not silently change the
underlying strategy or estimator. Rebuilding is explicit and uses saved strategy.

## Source-client separation

The exporter creates a new allowlisted OOXML package. It removes the sample
client cover logos, restaurant cover photo, notes, comments, thumbnails,
embedded fonts, unused slides, source metadata, external hyperlinks and
unreferenced assets. The cover uses the master's own generic PMC rocket artwork.
Sample prices, demographics, rankings, ROI claims and contract clauses are not
reused. Standard PMC agency wording is preserved, not rewritten as client facts.

## Boundaries

This release does not connect an LLM or change the rule/template-based strategy
generator. It is the reusable master-driven output foundation. Client-specific
research synthesis, automatic social audits/pricing and production-rate pricing
remain separate work. Saved placeholder benchmark scenarios are not treated as
sourced forecasts or automatically published in a client-ready master deck.

The in-app deck preview is editable text in source-slide order, not a pixel-rendered
PowerPoint thumbnail preview. Exported PowerPoints retain the source slide design.
Source font names remain in text styles but font files are not embedded; installed
fonts affect rendering in the recipient's PowerPoint application.

Validation includes real-master package integrity/client-content checks, native
editable shape/table parsing, saved-field/preview/export consistency, old-outline
preservation and rebuild/restore API tests, and mobile browser fixture tests.
No live client projects are created or modified by automated tests.
