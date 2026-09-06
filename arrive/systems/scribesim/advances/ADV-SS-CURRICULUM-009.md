---
advance:
  id: "ADV-SS-CURRICULUM-009"
  title: "Pen-Action Learning — Frozen-Path Rotation and Edge-Release Ablations"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","nibcontact","pathguide","handflow","handvalidate","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: "2026-09-06T14:39:10Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration"]
  model_usage: []
  status: complete
---

## Objective

Test whether bounded intentional pen actions fix named shape failures beyond the accepted fixed-tool gesture baseline, while keeping geometry and later session effects out of the optimizer.

**Work kind:** Implementation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Implementation/evaluation status and any unexecuted acceptance work are recorded below. No provider CI or owner approval is claimed.

## Behavioral Change

After this Advance: A staged action runner produces independently attributable fixed/rotation, full/partial-edge and separate terminal-construction evidence, including a valid null profile when added action complexity is unnecessary.

## Component Impact

- `scribesim/curriculum/pen_actions.py (planned)`
- `tests/test_pen_action_learning.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/actions/ (planned runs)`

These are planned implementation/evidence locations, not existing APIs.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-HANDVALIDATE-013](ADV-SS-HANDVALIDATE-013.md)
- [ADV-SS-PATHGUIDE-006](ADV-SS-PATHGUIDE-006.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [x] branch: confirm authorization before creating branches or commits.
- [x] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [x] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [x] Require matching accepted S1-gesture scope and the frozen tool/controller contract. Freeze path geometry, composition, pressure/speed and adequate ink before rotation or edge-release fitting; real runs also revalidate live G0.
- [x] Predeclare at most three ablations: fixed versus rotation-only; full edge versus edge-release-only with orientation held fixed; and a separate bounded explicit finishing-pass comparison. Do not combine rotation/release or optimize path geometry simultaneously.
- [ ] Fit at most four knots per active track under the frozen numeric/rate envelopes. Keep a fixed profile valid; activate an action only for a named failure with measurable sensitivity and held-out benefit.
- [ ] For a finishing comparison, use a coverage-supported existing shared gesture with an explicit lift, frozen geometry/action and a predeclared allowed placement set. Record all overlap owners and enforce expanded-letter budgets; it is a structural test, not a hidden renderer touch-up.
- [ ] Use seeds 7/19/41 with common render/time caps and one diagnosed revision. Freeze train/development/held-out compositions, objectives, bounds and selection rules; development alone selects checkpoints.
- [ ] Emit equal-scale baseline/fitted desired/actual footprints, path/orientation/edge overlays, parameter deltas and held-out scale/construction transfer. Show unchanged paths alongside changed ink geometry.
- [x] Report actions as supported, null/unnecessary, unresolved or rejected; never force extra movement merely to make samples look different. Persist all failures for HANDVALIDATE-014.
- [x] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] Each fitted action changes only its declared freedoms and shows actual execution sensitivity, not just darker pixels or nominal-only improvement.
- [x] Constant profiles and justified null decisions remain selectable without a false activation claim; unsupported historical properties remain unknown.
- [ ] Produce identity-bound candidates, complete budgets and negative evidence. Runner completion cannot certify S1-action, G1/G2 or readiness for real letter training.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

Additional knobs can compensate for wrong path geometry and defeat layer isolation. Freeze lower layers and one track per trial, reject hidden touch-ups, and retain fixed-tool candidates as the rollback.

Review estimate: 40 minutes, not a measured reviewability score.

## Evidence

- [x] Frozen inputs, criteria and identities; complete render/time and revision ledger.
- [x] Readable equal-scale evidence and a reproducible command/sample index under the planned bundle.
- [x] Scope-qualified decision with negative/null/unresolved outcomes and genuine review only when performed.
- [x] Tidy assessment and TDD red/green evidence for code changes; focused tests and clean-checkout replay where applicable.
- [x] `arrive plan check`, changed-link checks and `git diff --check`.
- [x] Before authorized merge, run `arrive pr check --strict --json`; report installed-tool limitations separately from provider CI. Never claim unobserved CI or owner approval.

## Bug Fixes

None implemented. Defects discovered during execution require a recorded
diagnosis and bounded repair; unrelated changes and threshold relaxation are excluded.

## Changes Made

### 2026-09-06 — plan: Scope TD-018 gesture and intentional-action work

- Added to Pass 15 phase `td018-pen-actions`.
- Implementation, experiments and acceptance remain pending.

### 2026-09-06 — complete: Implementation outcome

- Runner implementation complete; actual fitting and transfer experiments are
  BLOCKED and remain unchecked below. Completion does not mean learned actions.
- Red `cd56993`; frozen search contract `312d5b4`; initial runner `cdfd38f`.
  Full constant-track/tool-binding red `3b0ea2c`; guarded attempts `72e4849`.
  Baseline-binding red `11432a2`; final admission binding/attempts `5ef7188`.
- No preparatory refactor. Proposals isolate rotation, edge release and separate
  explicit lifted finishing within the existing shared/expanded budgets.
  Pure tests verify unchanged primitives/gestures, fixed ties and development
  selection; a null-selection unit test uses a fitness stub, not ink training.
- Implemented bounded fitting core, fixed-model lesson manifest reader and
  desired/actual evidence exports for future admitted lessons. The accepted
  rendered-lesson execution path is NOT exercised or accepted in this phase.
- Pinned upstream hashes, current code, tool contract and selected model binding
  prevent status edits or model substitution. Current prerequisites fail:
  S1-gesture blocked, missing coverage, stale legacy code identities and failed
  bridge convergence. Real mode also requires live G0/real lower layers.
- Two synthetic and two real admission attempts: all zero renders, zero target
  pixels opened, zero optimization, no candidates or justified null outcome.
  One diagnosed binding revision; current checks take 0.0140/0.0143 seconds.
- 10 focused tests pass locally. Combined 65 tests pass in clean clone
  `/tmp/td018-action-learning-final.I1sZg8` at `5ef7188` (15.40s).
  Fresh hash-seed-839 synthetic/real reports are byte-identical; wall receipts vary.
- Strict PR metadata check hits existing `ids: []` parser limitation, not CI.
  Plan/link/diff checks pass. Source data, old frozen evidence and controller
  position code remain unchanged; no thresholds relaxed or gate refreshed.
- [Blocked outcomes, contract and replay](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/actions/README.md).

## Check for Understanding

1. Which named shape failure motivates each action, and which parameters must not move during its test?
2. When is a null action the correct result rather than a failed attempt at expressiveness?
