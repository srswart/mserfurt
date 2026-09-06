---
advance:
  id: "ADV-SS-CURRICULUM-008"
  title: "Gesture Learning — Fixed-Tool Construction Practice and Transfer"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","evo","handvalidate","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Fit bounded shared gesture constructions at fixed tool settings and demonstrate transfer beyond the original six isolated primitive demonstrations.

**Work kind:** Implementation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Drafting timestamp only: no implementation, investigation run, gate pass, CI or owner approval is claimed.

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

- [ ] branch: confirm authorization before creating branches or commits.
- [ ] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [ ] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [ ] Consume the coverage workbook, frozen primitive checkpoint and migrated/compiler-validated model. Separate original primitive S1 provenance from any newly supported vocabulary; unsupported families remain debt, not guessed curves.
- [ ] Freeze shared primitive geometry and constant full-edge action profiles while fitting bounded primitive selections, transforms and declared joins inside gestures. If new primitive geometry is necessary, stop and scope a separately bounded primitive experiment and revalidate S1; do not fit all layers together.
- [ ] Use up to three predeclared ablations: fixed supplied construction, bounded placement fitting, and bounded discrete composition plus placement. Use the common three-seed/budget contract; freeze objectives and allowed parameters before training, development selects checkpoints.
- [ ] Test directional/topological variants supported by the workbook: continuous underturn/overturn/compound curves, bowls/loops and entry/exit constructions. Show an explicit lifted finishing pass separately from continuous motion.
- [ ] Freeze held-out scales, placements and composition combinations, not merely new random seeds. Reject combinations that exceed expanded-letter limits rather than increasing the limits.
- [ ] Emit parameter deltas and equal-scale initial/target/fitted nominal/sampled desired/actual-neutral panels, numbered segment/contact overlays and shared-gesture transfer into multiple supplied letter probes.
- [ ] Use live G0 and matching accepted lower-layer identities before real fitting. With current missing admission, run declared synthetic mechanics and record zero real fitting evaluations.
- [ ] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] Training changes bounded shared gesture parameters and shows held-out transfer relative to initialization; supplied letter probes are not reported as learned letters.
- [ ] Model/code/tool/split identities, evaluation counts, actual traces and replay commands are persisted; the immutable original S0/S1 bundle is retained.
- [ ] Emit candidates and full negative evidence for HANDVALIDATE-013. Runner completion is not S1-gesture acceptance or permission for dynamic actions.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

A hand-authored gesture demo can masquerade as learning. Publish fitted parameter deltas and disjoint transfer evidence; rollback to the original frozen fixed-tool model without deleting failed runs.

Review estimate: 40 minutes, not a measured reviewability score.

## Evidence

- [ ] Frozen inputs, criteria and identities; complete render/time and revision ledger.
- [ ] Readable equal-scale evidence and a reproducible command/sample index under the planned bundle.
- [ ] Scope-qualified decision with negative/null/unresolved outcomes and genuine review only when performed.
- [ ] Tidy assessment and TDD red/green evidence for code changes; focused tests and clean-checkout replay where applicable.
- [ ] `arrive plan check`, changed-link checks and `git diff --check`.
- [ ] Before authorized merge, run `arrive pr check --strict --json`; report installed-tool limitations separately from provider CI. Never claim unobserved CI or owner approval.

## Bug Fixes

None implemented. Defects discovered during execution require a recorded
diagnosis and bounded repair; unrelated changes and threshold relaxation are excluded.

## Changes Made

### 2026-09-06 — plan: Scope TD-018 gesture and intentional-action work

- Added to Pass 15 phase `td018-gestures`.
- Implementation, experiments and acceptance remain pending.

## Check for Understanding

1. Which shared parameters are fitted here, and which primitive/tool parameters remain frozen?
2. What unseen construction proves reuse rather than reproduction of supplied letter recipes?

