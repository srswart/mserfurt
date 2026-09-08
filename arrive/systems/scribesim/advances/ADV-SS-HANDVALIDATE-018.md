---
advance:
  id: "ADV-SS-HANDVALIDATE-018"
  title: "Foundation Geometry Accuracy — Independent Finer-Scale Acceptance"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "curriculum", "gesture", "tests"]
  started_at: "2026-09-08T10:31:14Z"
  implementation_completed_at: "2026-09-08T11:27:11Z"
  review_time_estimate_minutes: 45
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 110
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "local:independent-no-refit", "local:fresh-process-replay"]
  model_usage: []
  status: complete
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
- [x] test: commit observed failing admission, lineage, scope and metric tests first.
- [x] feat/fix: consumer-pin the completed CURRICULUM-013 manifest and reconstruct all source identities, candidate selections, artifacts and replay evidence.
- [x] Verify exactly three shared scale changes and derived endpoint-coincident attachments; reject altered primitives, ports, actions, recipes and per-occurrence overrides.
- [x] Freeze new withheld transforms/contexts before evaluation. Treat all previously inspected or learning-scored fixtures as regressions, not new holdouts. Target definitions and numerical limits remain unchanged.
- [x] Execute seeds 7/19/41 with zero fitting; at most 5000 renders/1800 seconds per seed including first/replay, controls and presentation. Preserve failures and use no silent retries.
- [x] Require absolute 0.05 global and occurrence-local actual/target bounds at all four refinements; retain full-frame, motion, exact ownership/contact, blank-pocket, closed-counter and nine adversarial checks.
- [x] Reevaluate underturn too: its old scoped acceptance cannot transfer to different candidate bytes. Report accepted/missing inventory explicitly.
- [x] Publish native comparison sheets and manifest-backed scoped admission; no letters, real hand, fatigue or default-renderer promotion.
- [ ] Update the Advance and plan, validate and merge under the user's usual workflow.

## Bug Fixes

Before any evaluation rendering, a focused failing test exposed vacuous acceptance
of the requested names when the decision helper received no seed records. The
helper now requires all three ordered, complete seeds before any scoped decision.
No source evidence, physical code, targets or fitting behavior changes.

## Risk + Rollback

Reusing inspected evidence as independent validation or inheriting acceptance
from old bytes would overstate readiness. Require fresh scoped measurement and
full identity reconstruction. Revert only new opt-in admission, preserve every
historical report, and leave legacy consumers and defaults unchanged.

Reviewability: final staged score is red 110, with a mechanical 726.6-minute
estimate dominated by 1370 generated manifest artifacts. Keep the complete
first/replay evidence together rather than trim duplicate proofs or omit workers.
Tests, implementation, the pre-render guard fix and evidence have separate
commits; only one new runtime module is added, with no changes to existing
runtime code. Letter learning is a separate Advance. The 45-minute human review
estimate is not a claim of review performed.

## Evidence

- [x] tdd:red-green
- [x] tests:unit and current-code clean replay
- [x] Frozen selected inputs, independent metrics, adversarial controls and budgets
- [x] Explicit scoped admission and negative unsupported-inventory tests

[Results and examples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/scale_evaluation/README.md),
[independent manifest](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/scale_evaluation/run-001/S1-actions.json),
and [verification](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/scale_evaluation/verification.json).

## CI Evidence Notes

Run local checks and strict PR metadata validation before merge. Do not claim
provider CI or human review without actual evidence.
Local plan/rule checks pass. The strict parser still returns `ids=[]` for an
explicit Advance ID in title/body/label; artifact doctor retains ten inherited
issues. No provider CI, push or human appearance acceptance is claimed.

## Changes Made

### 2026-09-08 — complete: all declared finer-scale null scopes pass

- Execution `9c09768`: all seeds and separate-process replays complete 30
  fixtures (nine fresh, 21 regressions), six contexts, the unchanged closed
  counter and nine controls. Worst local losses are 0.022382 / 0.022258 /
  0.022128 for underturn / overturn / compound, below unchanged 0.05. Every
  global and physical check passes; the three scoped nulls are independently
  accepted for the exact finer-scale candidate bytes.
- 3036 renders, 1012 per seed including replay; zero fitting or retries. Maximum
  cumulative seed time 249.026 seconds. Each seed replays 227 non-clock artifacts
  exactly. All 1370 manifest artifacts verify through the actual new admission
  API with the learning fitter and selector forbidden.
- 145 prior learning artifacts per worker (870 total) remeasure identically,
  including old ink and traces. No candidate, primitive, tool, target, criterion
  or historical report changed. Old candidate-specific readers remain strict.
- 116 focused tests pass; 27 new tests pass in a clean committed checkout.
  Broader tests: 356 pass and 18 inherited failures, all reproduced on pre-task
  `ac5fdb3` (17 other tests pass in that baseline subset).
- Publish the exact admission hash
  `49e72a04df648ef1295b94e8436c34cdb385a992d7b173c0316899a05f6f837b`
  and native examples. Letter/real approval remains false; CURRICULUM-005 must
  explicitly scope and verify its next bounded recipe experiment.

### 2026-09-08 — test: start independent acceptance implementation

Implementation starts at 11:03:16 UTC. Freeze nine fresh same-family holdouts,
21 learning-fixture regressions, three fresh plus three regression mechanical
contexts, unchanged counter/control diagnostics and a single no-refit attempt.
New evaluator and tests use existing incubating components; no new runtime or
primitive code is required. Observe and commit tests before implementation.

`09b1911` records the initial missing-module failure, followed by `024b427`'s
independent source reader and evaluator (25 tests pass). `ffbe57c` adds the
observed empty-seed decision failure before its fix. Source reconstruction
verifies all six learning workers, the exact recorded search and development
selection, cumulative budgets, replay and compiled-source identities without
calling a fitter or selector. Runtime checks still use the pinned physical code.

### 2026-09-08 — docs: register independent follow-up

Planned only. No independent render, acceptance decision or fitting budget is
spent by creating this record.

## Check for Understanding

1. Why must unchanged primitives be verified again when only scales changed?
2. Why is old underturn acceptance insufficient for new candidate bytes?
3. Which fixtures may count as fresh independent holdouts?
4. Why do absolute image accuracy and mechanical fidelity need separate checks?
