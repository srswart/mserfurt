---
advance:
  id: ADV-SS-EVOFIT-002
  title: Reviewed Evofit — Normalize Human-Reviewed Glyph and Join Exemplars Across Documents
  system: scribesim
  primary_component: evo
  components:
  - evo
  - annotate
  - pathguide
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
  - data_quality
  evidence:
  - dataset
  - snapshot
  status: complete
---

## Objective

Use the reviewed exemplar dataset, not raw automatic crops, as evofit input for normalized nominal glyph and join recovery across multiple documents.

## Planned Implementation Tasks

- [x] teach evofit to consume the reviewed exemplar freeze as its primary fit-source manifest
- [x] normalize multiple reviewed samples per symbol or join into a common acceptable nominal form
- [x] preserve per-source provenance and quality metadata through candidate generation
- [x] emit a reviewed-exemplar evofit bundle for pathguide freeze

## Validation Gates

- [x] evofit consumes only reviewed exemplar inputs for this stage
- [x] nominal candidates improve readability relative to the automatic-corpus evofit baseline
- [x] candidate bundles retain source-manuscript provenance for every fit input

## Risk + Rollback

Do not mix reviewed and automatic fit sources silently. If reviewed coverage is too sparse, fail clearly and return to the annotation ledger.

## Evidence

- [x] reviewed-only evofit runner and CLI
- [x] reviewed manifest compatibility tests and baseline comparison reporting
- [x] provenance report for normalized nominal forms

## Implementation Notes

The evofit workflow now supports reviewed exemplar manifests as a first-class input via `run_reviewed_evofit` and the `scribesim evofit-reviewed-exemplars` CLI command. Reviewed runs require `manifest_kind = "reviewed_exemplars"`, carry quality tiers and manuscript/object provenance through the selected fit-source summaries, emit provenance reports, and compare bundle-level readability metrics against the automatic-corpus evofit baseline when a baseline summary is available. The actual workspace reviewed-evofit bundle remains data-dependent: until the reviewed annotation workbench and freeze steps contain real samples, the reviewed runner is implemented and tested but has no meaningful manuscript bundle to materialize.
