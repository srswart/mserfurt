---
advance:
  id: ADV-SS-EXEMPLAR-006
  title: Coverage Backfill Quarantine — Keep Repaired Samples out of Promoted Exemplars
  system: scribesim
  primary_component: refextract
  components:
  - refextract
  - training
  - handvalidate
  started_at: 2026-03-26T00:00:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-26T00:00:00Z
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
  - tests:integration
  status: complete
---

## Objective

Keep `coverage_promoted` and other repair-only samples out of the reviewable exemplar tier, even when they remain necessary for pipeline accounting.

## Planned Implementation Tasks

- [x] isolate `coverage_promoted` and fallback-filled samples into a non-reviewable repair bucket
- [x] prevent repair samples from entering `promoted_exemplars`
- [x] keep summary coverage metrics honest by distinguishing repaired coverage from promoted exemplar coverage
- [x] update downstream stages so repair samples never seed nominal guide recovery

## Validation Gates

- [x] no `coverage_promoted` sample appears in promoted exemplar manifests or panels
- [x] dashboards show repaired coverage as separate debt, not success
- [x] downstream nominal-form stages fail clearly if they attempt to consume repair-only assets

## Risk + Rollback

Coverage numbers will look worse before they look better. That is intended: repair samples should expose remaining debt instead of masking it.

## Evidence

- [x] manifests that isolate repair-only samples
- [x] dashboard section for repaired coverage debt
- [x] tests proving repaired samples cannot leak into promoted exemplar inputs

## Implementation Notes

This advance adds a non-reviewable `repair_only` tier to the automatic corpus builder. Coverage backfill now lands in `repair_only` instead of `auto_admitted`, summary and manifest outputs report repair-only debt explicitly, and promoted exemplar selection continues to exclude repair samples. `scribesim.evofit.build_evofit_targets` now rejects `repair_only` as an allowed input tier so repair-only assets cannot seed nominal-form recovery by mistake.
