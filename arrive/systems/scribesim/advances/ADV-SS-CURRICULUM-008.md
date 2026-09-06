---
advance:
  id: "ADV-SS-CURRICULUM-008"
  title: "Gesture Learning — Fixed-Tool Construction Practice and Transfer"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","evo","handvalidate","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: "2026-09-06T13:30:02Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration", "shared/training/konrad_hand_recovery/stroke_gestures_v2/gestures/run-002/report.json"]
  model_usage: []
  status: complete
---

## Objective

Fit bounded shared gesture constructions at fixed tool settings and demonstrate transfer beyond the original six isolated primitive demonstrations.

**Work kind:** Implementation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Runner implementation and bounded subset learning complete; broader gesture
coverage remains blocked and its unexecuted experiment task is left unchecked.
No real hand, full S1-gesture readiness or provider CI is claimed.

## Behavioral Change

After this Advance: A dedicated training runner emits an immutable gesture checkpoint and visible before/target/fitted/actual practice sheets. Letter recipes remain supplied probes, not learned-letter claims.

## Component Impact

- `scribesim/curriculum/gesture_learning.py (planned)`
- `tests/test_gesture_learning.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/gestures/ (planned runs)`

These are planned implementation/evidence locations, not existing APIs.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-GESTURE-001](ADV-SS-GESTURE-001.md)
- [ADV-SS-CURRICULUM-004](ADV-SS-CURRICULUM-004.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [x] branch: confirm authorization before creating branches or commits.
- [x] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [x] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [x] Consume the coverage workbook, frozen primitive checkpoint and migrated/compiler-validated model. Separate original primitive S1 provenance from any newly supported vocabulary; unsupported families remain debt, not guessed curves.
- [x] Freeze shared primitive geometry and constant full-edge action profiles while fitting bounded primitive selections, transforms and declared joins inside gestures. If new primitive geometry is necessary, stop and scope a separately bounded primitive experiment and revalidate S1; do not fit all layers together.
- [x] Use up to three predeclared ablations: fixed supplied construction, bounded placement fitting, and bounded discrete composition plus placement. Use the common three-seed/budget contract; freeze objectives and allowed parameters before training, development selects checkpoints.
- [ ] Test directional/topological variants supported by the workbook: continuous underturn/overturn/compound curves, bowls/loops and entry/exit constructions. Show an explicit lifted finishing pass separately from continuous motion.
- [x] Freeze held-out scales, placements and composition combinations, not merely new random seeds. Reject combinations that exceed expanded-letter limits rather than increasing the limits.
- [x] Emit parameter deltas and equal-scale initial/target/fitted nominal/sampled desired/actual-neutral panels, numbered segment/contact overlays and shared-gesture transfer into multiple supplied letter probes.
- [x] Use live G0 and matching accepted lower-layer identities before real fitting. With current missing admission, run declared synthetic mechanics and record zero real fitting evaluations.
- [x] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [x] Training changes bounded shared gesture parameters and shows held-out transfer relative to initialization; supplied letter probes are not reported as learned letters.
- [x] Model/code/tool/split identities, evaluation counts, actual traces and replay commands are persisted; the immutable original S0/S1 bundle is retained.
- [x] Emit candidates and full negative evidence for HANDVALIDATE-013. Runner completion is not S1-gesture acceptance or permission for dynamic actions.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

A hand-authored gesture demo can masquerade as learning. Publish fitted parameter deltas and disjoint transfer evidence; rollback to the original frozen fixed-tool model without deleting failed runs.

Review estimate: 40 minutes, not a measured reviewability score.

## Evidence

- [x] Frozen inputs, criteria and identities; complete render/time and revision ledger.
- [x] Readable equal-scale evidence and a reproducible command/sample index under the planned bundle.
- [x] Scope-qualified decision with negative/null/unresolved outcomes and genuine review only when performed.
- [x] Tidy assessment and TDD red/green evidence for code changes; focused tests and clean-checkout replay where applicable.
- [x] `arrive plan check`, changed-link checks and `git diff --check`.
- [x] Before authorized merge, run `arrive pr check --strict --json`; report installed-tool limitations separately from provider CI. Never claim unobserved CI or owner approval.

## Bug Fixes

Fixed contact corridor reporting in the new gesture adapter: exclude pen-up
travel from the on-surface metric. Motion, targets and thresholds are unchanged.
One diagnosed rerun preserves the original evidence rather than overwriting it.

## Changes Made

### 2026-09-06 — plan: Scope TD-018 gesture and intentional-action work

- Added to Pass 15 phase `td018-gestures`.
- Implementation, experiments and acceptance remain pending.

### 2026-09-06 — complete: Bounded shared construction lesson

- Red: `8f55561`; first implementation/evidence: `e80e40c`.
  Metric red test: `66306b4`; repaired adapter and run-002: `9087cb6`.
  No preparatory refactor or canonical renderer/controller changes.
- All six learned primitives and fixed profiles remain frozen. Fit one shared
  stem-terminal construction over supplied i/u probes, selecting rise versus
  exit and bounded scale/rotation. The initial program is explicitly perturbed,
  not a historical baseline. No independent per-letter geometry was fitted.
- Three seeds x three ablations: held-out loss 0.4424 fixed, 0.3116 placement-only,
  0.0 composition/placement. Exact zero is expected for this representable
  synthetic target, not evidence of real-hand recovery. Development selects.
- Each attempt uses 396 initial renders plus 378 verification renders (including
  setup/presentation); two attempts total 1548. Wall times 32.18s and 32.15s.
  One diagnosed revision, no further search, no real fitting renders.
- Actual contact image losses 0.049–0.079, corridor 0.2mm and preserved contacts.
  The run-001 all-motion metric included air and is retained with its old code
  identity; run-002 is current. Thresholds and generated trajectories did not change.
- Broad underturn/overturn/compound-return coverage is NOT learned. That
  unsupported task remains unchecked; the required bounded follow-up is
  [scoped separately](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/gestures/primitive-extension-request.md).
  Do not proceed to action fitting on this subset demonstration.
- 42 focused/regression tests pass locally (9.60s) and in clean clone
  `/tmp/td018-learning-clean.uW0GYq` at `9087cb6` (10.69s).
  Full hash-seed-839 rerun matches all semantic files; only elapsed receipts differ.
- Strict PR metadata check ran and hit the existing `ids: []` parser limitation.
  No provider CI or owner appearance approval is claimed.
- [Samples, outcomes and replay](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/gestures/README.md).

## Check for Understanding

1. Which shared parameters are fitted here, and which primitive/tool parameters remain frozen?
2. What unseen construction proves reuse rather than reproduction of supplied letter recipes?
