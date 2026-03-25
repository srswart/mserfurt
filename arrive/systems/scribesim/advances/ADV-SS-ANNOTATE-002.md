---
advance:
  id: ADV-SS-ANNOTATE-002
  title: Local Annotation Workbench — View Folios, Draw Bounds, and Label Glyphs and Joins
  system: scribesim
  primary_component: annotate
  components:
  - annotate
  - refselect
  - refextract
  started_at: 2026-03-25T00:00:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-25T00:00:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 3
  risk_flags:
  - workflow_change
  evidence:
  - tests:integration
  - dataset
  status: complete
---

## Objective

Build a local browser-based tool that lets the operator open manuscript references, draw glyph/join bounds, label them, and save reviewed annotations with provenance.

## Planned Implementation Tasks

- [x] serve a local web UI for browsing harvested reference folios and current coverage debt
- [x] support box creation/editing for glyphs and joins directly on the manuscript image
- [x] support explicit labels, quality tiers, notes, and repeated samples per symbol across documents
- [x] persist reviewed annotations to a local manifest format with source image path and pixel bounds

## Validation Gates

- [x] the UI can open a local reference folio and save multiple labeled samples
- [x] glyph and join annotations remain distinguishable in the saved manifest
- [x] every saved annotation preserves manuscript provenance and exact pixel coordinates

## Risk + Rollback

Keep the first version simple. A stable local annotation loop matters more than ambitious editing features.

## Evidence

- [x] local annotation workbench launcher and browser UI
- [x] sample reviewed annotation manifest bootstrap
- [x] integration test for save/load of labeled glyph and join regions

## Implementation Notes

The new `scribesim.annotate.workbench` module provides a stdlib-backed local web server and a single-page annotation UI with no extra frontend build step. The workbench reads the reviewed coverage ledger, resolves the frozen harvested folio set from the corpus manifest, serves local manuscript images, and persists reviewed glyph/join rectangles into a dedicated `reviewed_manifest.toml` with exact source-image provenance and pixel bounds. The CLI entrypoint is `scribesim annotate-reviewed-exemplars`, and a bootstrap reviewed manifest now lives under `shared/training/handsim/reviewed_annotations/workbench_v1/`.
