---
advance:
  id: "ADV-SS-HANDVALIDATE-018"
  title: "Foundation Geometry Accuracy — Independent Finer-Scale Acceptance"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "curriculum", "gesture", "tests"]
  started_at: "2026-09-08T10:31:14Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  model_usage: []
  status: in_progress
---

## Objective

Independently evaluate the frozen CURRICULUM-013 scale-only candidates without
refitting. This is the next acceptance boundary, not work executed by the learning
Advance. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).

## Behavioral Change

An explicit new consumer verifies changed scale lineage, immutable primitive and
tool identities, current source evidence and independent physical measurements.
Old candidate-specific admission APIs remain unchanged and must reject replacement
bytes. A complete learning report alone cannot grant S1-action/null acceptance.

## Component Impact

Opt-in handvalidate module, focused tests and a separate immutable evaluation
bundle using existing incubating components. No primitive, target or controller
changes. No new component is required.

## Dependencies

- [ADV-SS-CURRICULUM-013](ADV-SS-CURRICULUM-013.md)
- [ADV-SS-HANDVALIDATE-017](ADV-SS-HANDVALIDATE-017.md)

The completed [learning manifest](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/finer_scales/run-001/report.json)
has SHA-256 `9a1ac0bc066d31e4c57c82529f70af000a3364bf26a57275386b2736171a76b8`.
All seeds select `[0.83,1.17,0.87]`; candidate file SHA-256 is
`6ff3e478799ab1a63d970d1e99fd5d5c454c12557047e5506fec911a65baf4ba`.
Independent implementation must verify these bytes rather than silently choosing
another checkpoint. The learning measurements do not transfer acceptance.

## Planned Implementation Tasks

- [x] branch: `advance/ss-handvalidate-018` under implementation/update/merge authorization.
- [x] tidy: no refactor required; preserve all pinned historical modules.
- [ ] test: commit observed failing admission, lineage, scope and metric tests first.
- [ ] feat/fix: consumer-pin the completed CURRICULUM-013 manifest and reconstruct all source identities, candidate selections, artifacts and replay evidence.
- [ ] Verify exactly three shared scale changes and derived endpoint-coincident attachments; reject altered primitives, ports, actions, recipes and per-occurrence overrides.
- [ ] Freeze new withheld transforms/contexts before evaluation. Treat all previously inspected or learning-scored fixtures as regressions, not new holdouts. Target definitions and numerical limits remain unchanged.
- [ ] Execute seeds 7/19/41 with zero fitting; at most 5000 renders/1800 seconds per seed including first/replay, controls and presentation. Preserve failures and use no silent retries.
- [ ] Require absolute 0.05 global and occurrence-local actual/target bounds at all four refinements; retain full-frame, motion, exact ownership/contact, blank-pocket, closed-counter and nine adversarial checks.
- [ ] Reevaluate underturn too: its old scoped acceptance cannot transfer to different candidate bytes. Report accepted/missing inventory explicitly.
- [ ] Publish native comparison sheets and manifest-backed scoped admission; no letters, real hand, fatigue or default-renderer promotion.
- [ ] Update the Advance and plan, validate and merge under the user's usual workflow.

## Bug Fixes

None identified. Missing measurement or runtime defects must remain distinct
from geometric residuals; neither warrants an unapproved refit.

## Risk + Rollback

Reusing inspected evidence as independent validation or inheriting acceptance
from old bytes would overstate readiness. Require fresh scoped measurement and
full identity reconstruction. Revert only new opt-in admission, preserve every
historical report, and leave legacy consumers and defaults unchanged.

## Evidence

- [ ] tdd:red-green
- [ ] tests:unit and current-code clean replay
- [ ] Frozen selected inputs, independent metrics, adversarial controls and budgets
- [ ] Explicit scoped admission and negative unsupported-inventory tests

## CI Evidence Notes

Run local checks and strict PR metadata validation before merge. Do not claim
provider CI or human review without actual evidence.

## Changes Made

### 2026-09-08 — test: start independent acceptance implementation

Implementation starts at 11:03:16 UTC. Freeze nine fresh same-family holdouts,
21 learning-fixture regressions, three fresh plus three regression mechanical
contexts, unchanged counter/control diagnostics and a single no-refit attempt.
New evaluator and tests use existing incubating components; no new runtime or
primitive code is required. Observe and commit tests before implementation.

### 2026-09-08 — docs: register independent follow-up

Planned only. No independent render, acceptance decision or fitting budget is
spent by creating this record.

## Check for Understanding

1. Why must unchanged primitives be verified again when only scales changed?
2. Why is old underturn acceptance insufficient for new candidate bytes?
3. Which fixtures may count as fresh independent holdouts?
4. Why do absolute image accuracy and mechanical fidelity need separate checks?
