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
  - tests:integration
  - dashboard
  status: complete
---

## Objective

Require stronger validation before any crop becomes a promoted exemplar.

## Planned Implementation Tasks

- [x] add stronger glyph/join promotion gates beyond score threshold and margin
- [x] include legibility proxy or review workflow evidence for promoted crops
- [x] require stable cluster membership and competitor separation for promoted symbols
- [x] report promoted exemplar coverage separately from automatic admission coverage

## Validation Gates

- [x] promoted exemplars are rejected when cluster assignment is unstable against competing symbols
- [x] promoted exemplars cannot pass on score margin alone
- [x] dashboards show why a crop passed or failed promotion

## Risk + Rollback

This may collapse the promoted set at first. That is acceptable; a small honest exemplar set is better than a large mislabeled one.

## Evidence

- [x] promotion-gate report for the active review slice
- [x] per-symbol pass/fail explanations for promoted glyphs
- [x] integration tests covering cluster-instability rejection

## Implementation Notes

Promoted exemplars now pass through explicit glyph and join gates driven by `self_ncc_score`, `competitor_margin`, `cluster_consistency`, `cluster_separation`, and `occupancy_balance_score`. The corpus builder emits `promotion_gate_report.json` and `promotion_gate_report.md` with per-symbol pass/fail explanations, and only gate-passing `auto_admitted` candidates are written into `promoted_exemplars`. Focused handvalidate/exemplar/evofit/CLI tests cover both the report bundle and rejection of a mislabeled competing-symbol candidate. A fresh rebuild of the long-running active-review workspace corpus should be run separately to materialize the new report in the committed bundle.
