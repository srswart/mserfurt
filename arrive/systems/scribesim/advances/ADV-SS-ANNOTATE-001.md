---
advance:
  id: ADV-SS-ANNOTATE-001
  title: Reviewed Coverage Ledger — Symbol and Join Gaps for Manual Exemplar Work
  system: scribesim
  primary_component: annotate
  components:
  - annotate
  - refextract
  - handvalidate
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
  - dashboard
  - dataset
  status: complete
---

## Objective

Expose how many auto-admitted, promoted, reviewed, and missing samples exist for every required glyph and join before manual labeling begins.

## Planned Implementation Tasks

- [x] build a coverage ledger over the active review corpus, promoted exemplar set, and required symbol/join inventory
- [x] report counts per symbol and join, grouped by source manuscript and quality tier
- [x] surface blocking gaps and debt explicitly for manual annotation planning
- [x] freeze the ledger to a machine-readable manifest and a human review summary

## Validation Gates

- [x] every required symbol and join appears in the ledger, even when count is zero
- [x] auto-admitted, promoted, reviewed, and missing counts are distinguished clearly
- [x] the ledger is reproducible from frozen input manifests

## Risk + Rollback

If the first ledger is noisy, prefer honest over-complete reporting. The purpose is to expose debt, not to present a polished dashboard.

## Evidence

- [x] reviewed coverage ledger manifest
- [x] human-readable gap summary
- [x] per-symbol and per-join count table

## Implementation Notes

The new `scribesim.annotate.ledger` module builds a deterministic coverage ledger from the frozen active-review corpus manifest, promoted exemplar manifest, and the harvested selection manifest. It restores manuscript-level grouping for auto-admitted crops by mapping sanitized canvas labels back through the frozen selection manifest, includes the full required glyph and join inventory even when counts are zero, and leaves reviewed counts at zero until the annotation workbench begins exporting reviewed manifests. The committed ledger bundle now lives under `shared/training/handsim/reviewed_annotations/coverage_ledger_v1/`.
