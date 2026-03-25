---
advance:
  id: ADV-SS-HANDVALIDATE-005
  title: Exemplar Promotion Gates — Legibility and Cluster Consistency for Reviewable Glyphs
  system: scribesim
  primary_component: handvalidate
  components:
  - handvalidate
  - refextract
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
  - tests:integration
  - dashboard
  status: proposed
---

## Objective

Require stronger validation before any crop becomes a promoted exemplar.

## Planned Implementation Tasks

- [ ] add stronger glyph/join promotion gates beyond score threshold and margin
- [ ] include legibility proxy or review workflow evidence for promoted crops
- [ ] require stable cluster membership and competitor separation for promoted symbols
- [ ] report promoted exemplar coverage separately from automatic admission coverage

## Validation Gates

- [ ] promoted exemplars are rejected when cluster assignment is unstable against competing symbols
- [ ] promoted exemplars cannot pass on score margin alone
- [ ] dashboards show why a crop passed or failed promotion

## Risk + Rollback

This may collapse the promoted set at first. That is acceptable; a small honest exemplar set is better than a large mislabeled one.

## Evidence

- [ ] promotion-gate report for the active review slice
- [ ] per-symbol pass/fail explanations for promoted glyphs
- [ ] integration tests covering cluster-instability rejection
