---
advance:
  id: ADV-SS-PATHGUIDE-004
  title: Exemplar-Fit Guide Freeze — Promote Evo-Derived Nominal Glyphs and Joins
  system: scribesim
  primary_component: pathguide
  components:
  - pathguide
  - training
  - guides
  started_at: null
  started_by: null
  implementation_completed_at: null
  implementation_completed_by: null
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - data_quality
  evidence:
  - dataset
  - snapshot
  status: proposed
---

## Objective

Convert accepted evofit nominal forms into promoted `DensePathGuide` assets for handflow, replacing the current toy or clone-based active review guides.

## Planned Implementation Tasks

- [ ] convert accepted evofit proposals into dense path guides with provenance
- [ ] freeze promoted glyph and join guides for the active review slice
- [ ] render nominal guides directly for legibility review before controller use
- [ ] replace clone- or toy-derived active review guides with exemplar-fit assets

## Validation Gates

- [ ] nominal guide renders are legible on the promoted review slice
- [ ] exact-symbol guide coverage remains 1.0 for the review slice
- [ ] no promoted uppercase or diacritic guide is a lowercase clone or normalization fallback

## Risk + Rollback

Do not promote a guide set just because it is exact-symbol complete. If nominal renders are unreadable, the guide set stays blocked and handflow does not consume it.

## Evidence

- [ ] committed exemplar-fit guide catalog
- [ ] direct nominal-render review panel
- [ ] coverage and provenance report for the promoted guide set
