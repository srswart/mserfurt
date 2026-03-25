---
advance:
  id: ADV-SS-REFSELECT-008
  title: Exemplar Harvest — Manuscript Sampling for TD-014 Nominal Guide Recovery
  system: scribesim
  primary_component: refselect
  components:
  - refselect
  - training
  - provenance
  started_at: 2026-03-24T00:00:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T00:00:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 3
  risk_flags:
  - external_dependency
  evidence:
  - provenance
  - sample
  - tests:integration
  status: complete
---

## Objective

Use the existing IIIF/reference-selection pipeline to acquire a provenance-backed sample set of 30–40 manuscript folios suitable for exemplar-driven glyph recovery.

## Planned Implementation Tasks

- [x] define target manifests and sampling strategy for the intended hand family
- [x] fetch and sample candidate folios through the existing TD-009 tooling
- [x] freeze the selected folio set with provenance and local paths
- [x] emit a review summary showing manuscript source, labels, and selected pages

## Validation Gates

- [x] selected folios are provenance-backed and reproducible
- [x] sample set contains enough clean text pages to support glyph/join exemplar extraction
- [x] full-resolution or extraction-resolution assets are available locally for downstream TD-014 work

## Risk + Rollback

This stage depends on external IIIF sources and variable manuscript quality. If the selected manuscript family is too inconsistent, resample or narrow the source set rather than weakening downstream gates.

## Evidence

- [x] committed selection manifest or provenance record for the exemplar harvest
- [x] local sample inventory with 30–40 folios
- [x] review summary of the selected corpus
