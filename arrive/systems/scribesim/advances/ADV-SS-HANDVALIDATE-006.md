---
advance:
  id: ADV-SS-HANDVALIDATE-006
  title: Parameter Sensitivity Gates — Prove Reviewed Guided Parameters Are Active and Safe
  system: scribesim
  primary_component: handvalidate
  components:
  - handvalidate
  - handflow
  - training
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
  - metrics
  evidence:
  - tests:integration
  - snapshot
  status: proposed
---

## Objective

Add a dedicated sensitivity bench so TD-014 can prove which `HandProfile` parameters are actually active in the reviewed guided path and reject inert or unsafe tuning claims.

## Planned Implementation Tasks

- [ ] implement a reviewed proof sensitivity bench that renders low/high parameter comparisons for activated controls
- [ ] add deterministic delta metrics for pixel change, width change, baseline displacement, and pressure/ink variation
- [ ] classify parameters as inactive, active-safe, or active-unsafe based on measured deltas and legibility gates
- [ ] write dashboard/report outputs that make inert parameters obvious

## Validation Gates

- [ ] activated parameters show non-trivial deterministic output deltas on reviewed proofs
- [ ] inactive parameters fail clearly instead of producing misleading tuning studies
- [ ] stressed variants only pass when corridor and nominal legibility remain within allowed bounds

## Risk + Rollback

Sensitivity metrics can become noisy if they are not normalized against image size and proof content. Keep the bench deterministic and limited to small reviewed proof sets until the metric behavior is stable.

## Evidence

- [ ] reviewed parameter sensitivity dashboard
- [ ] tests proving inactive parameters are detected as inert
- [ ] tests proving activated parameters produce measurable deltas
