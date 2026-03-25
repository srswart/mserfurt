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
  - tests:integration
  status: proposed
---

## Objective

Keep `coverage_promoted` and other repair-only samples out of the reviewable exemplar tier, even when they remain necessary for pipeline accounting.

## Planned Implementation Tasks

- [ ] isolate `coverage_promoted` and fallback-filled samples into a non-reviewable repair bucket
- [ ] prevent repair samples from entering `promoted_exemplars`
- [ ] keep summary coverage metrics honest by distinguishing repaired coverage from promoted exemplar coverage
- [ ] update downstream stages so repair samples never seed nominal guide recovery

## Validation Gates

- [ ] no `coverage_promoted` sample appears in promoted exemplar manifests or panels
- [ ] dashboards show repaired coverage as separate debt, not success
- [ ] downstream nominal-form stages fail clearly if they attempt to consume repair-only assets

## Risk + Rollback

Coverage numbers will look worse before they look better. That is intended: repair samples should expose remaining debt instead of masking it.

## Evidence

- [ ] manifests that isolate repair-only samples
- [ ] dashboard section for repaired coverage debt
- [ ] tests proving repaired samples cannot leak into promoted exemplar inputs
