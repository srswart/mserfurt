---
advance:
  id: ADV-SS-PATHGUIDE-004
  title: Reviewed Exemplar-Fit Guide Freeze — Promote Cleanup-Aware Evo-Derived Nominal Glyphs and Joins
  system: scribesim
  primary_component: pathguide
  components:
  - pathguide
  - training
  - guides
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

Convert accepted reviewed-evofit nominal forms into promoted `DensePathGuide` assets for handflow, replacing the current toy or clone-based active review guides.

## Planned Implementation Tasks

- [x] convert accepted reviewed-evofit proposals into dense path guides with raw/cleaned exemplar provenance
- [x] freeze promoted glyph and join guides for the active review slice
- [x] render nominal guides directly for legibility review before controller use
- [x] replace clone- or toy-derived active review guides with reviewed exemplar-fit assets

## Validation Gates

- [x] nominal guide renders are emitted on the promoted review slice for direct review before controller use
- [x] exact-symbol guide coverage remains explicit in the promoted guide report and gate summary
- [x] promoted guides preserve reviewed raw-vs-cleaned provenance instead of relying on lowercase clones or normalization fallback metadata

## Risk + Rollback

Do not promote a guide set just because it is exact-symbol complete. If nominal renders are unreadable, or if the accepted proposals do not preserve raw-vs-cleaned reviewed provenance clearly, the guide set stays blocked and handflow does not consume it.

## Evidence

- [x] reviewed exemplar-fit guide freeze module and CLI
- [x] direct nominal-render review panel
- [x] coverage and provenance report for the promoted guide set

## Implementation Notes

This advance adds `scribesim.pathguide.freeze.freeze_reviewed_evofit_guides`, which consumes the reviewed evofit bundle, promotes structurally convertible proposals into accepted `DensePathGuide` assets, and writes both overlay and direct nominal-render panels for review. The promoted guide catalog now preserves reviewed raw and cleaned source lineage in accepted guide sources, and the bundle emits both validation and coverage/provenance reports so handflow can consume a stable reviewed-lane guide catalog rather than exploratory proposal outputs.
