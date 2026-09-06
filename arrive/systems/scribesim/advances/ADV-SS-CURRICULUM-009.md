---
advance:
  id: "ADV-SS-CURRICULUM-009"
  title: "Pen-Action Learning — Frozen-Path Rotation and Edge-Release Ablations"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","nibcontact","pathguide","handflow","handvalidate","tests"]
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

Test whether bounded intentional pen actions fix named shape failures beyond the accepted fixed-tool gesture baseline, while keeping geometry and later session effects out of the optimizer.

**Work kind:** Implementation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Drafting timestamp only: no implementation, investigation run, gate pass, CI or owner approval is claimed.

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

- [ ] branch: confirm authorization before creating branches or commits.
- [ ] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [ ] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [ ] Require matching accepted S1-gesture scope and the frozen tool/controller contract. Freeze path geometry, composition, pressure/speed and adequate ink before rotation or edge-release fitting; real runs also revalidate live G0.
- [ ] Predeclare at most three ablations: fixed versus rotation-only; full edge versus edge-release-only with orientation held fixed; and a separate bounded explicit finishing-pass comparison. Do not combine rotation/release or optimize path geometry simultaneously.
- [ ] Fit at most four knots per active track under the frozen numeric/rate envelopes. Keep a fixed profile valid; activate an action only for a named failure with measurable sensitivity and held-out benefit.
- [ ] For a finishing comparison, use a coverage-supported existing shared gesture with an explicit lift, frozen geometry/action and a predeclared allowed placement set. Record all overlap owners and enforce expanded-letter budgets; it is a structural test, not a hidden renderer touch-up.
- [ ] Use seeds 7/19/41 with common render/time caps and one diagnosed revision. Freeze train/development/held-out compositions, objectives, bounds and selection rules; development alone selects checkpoints.
- [ ] Emit equal-scale baseline/fitted desired/actual footprints, path/orientation/edge overlays, parameter deltas and held-out scale/construction transfer. Show unchanged paths alongside changed ink geometry.
- [ ] Report actions as supported, null/unnecessary, unresolved or rejected; never force extra movement merely to make samples look different. Persist all failures for HANDVALIDATE-014.
- [ ] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] Each fitted action changes only its declared freedoms and shows actual execution sensitivity, not just darker pixels or nominal-only improvement.
- [ ] Constant profiles and justified null decisions remain selectable without a false activation claim; unsupported historical properties remain unknown.
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

- Added to Pass 15 phase `td018-pen-actions`.
- Implementation, experiments and acceptance remain pending.

## Check for Understanding

1. Which named shape failure motivates each action, and which parameters must not move during its test?
2. When is a null action the correct result rather than a failed attempt at expressiveness?

