---
advance:
  id: "ADV-SS-NIBCONTACT-001"
  title: "Pen-Contact Investigation — Tool Semantics, Calibration and Frozen Controls"
  system: "scribesim"
  primary_component: "nibcontact"
  components: ["nibcontact","gesture","evo","pathguide","handflow","handvalidate","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Freeze a testable broad-edge footprint/action contract and determine which intentional actions are identifiable, representable and worth testing, without attributing unobserved force laws to a historical quill.

**Work kind:** Investigation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Drafting timestamp only: no implementation, investigation run, gate pass, CI or owner approval is claimed.

## Behavioral Change

After this Advance: An engineering calibration/feasibility report defines units, action/rate envelopes, physical fixtures, independent expected geometry, negative controls and convergence criteria before renderer/controller changes or fitting.

## Component Impact

- `scribesim/evo/renderer.py (read-only canonical sweep audit)`
- `scribesim/handvalidate/bridge.py and model.py (read-only actual-field audit)`
- `scribesim/pathguide/ and scribesim/handflow/ (read-only execution audit)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/tool_contract/ (planned fixtures/report)`

These are planned implementation/evidence locations, not existing APIs.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-CURRICULUM-004](ADV-SS-CURRICULUM-004.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before creating branches or commits.
- [ ] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [ ] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [ ] Audit the canonical swept-nib, direct/sampled/actual bridges, pressure/darkness coupling and controller orientation/contact fields. Identify desired fields that currently lack a realized state; publish an explicit implementation gap table.
- [ ] Specify a fixed adequate-ink, constant dimensionless-pressure/speed baseline; declare nib width/thickness, coordinate frame, unwrapped angles, active-edge endpoint fractions and angular/contact-rate bounds. Calibrated physical measurements and declared synthetic assumptions must be labeled separately.
- [ ] Freeze analytic or independently constructed footprint expectations for fixed-angle lines/arcs, rotation, left/right edge release, wraps, y-axis conversion, explicit lifts and two-pass terminals. Do not validate a new renderer solely against images produced by that same renderer.
- [ ] Freeze numeric image/edge endpoint, pose/contact, counter and timestep/arc-length convergence tolerances before implementation results are inspected; bind them to code/tool/fixture identities and describe any development-only calibration.
- [ ] Define at most three controlled comparisons: fixed versus rotation, full versus partial edge, and declared finishing overlap. Paths are frozen for action comparisons; finishing topology is a separate structural comparison with a declared lift, not a hidden action knob.
- [ ] Bound investigation to a code audit and at most three fixture families, 100 total diagnostic renders and 900 seconds of automated probes. No fitting or manuscript-test access. Allow one diagnosed revision; further exploration or physical tool acquisition needs a new scope/budget.
- [ ] Classify stationary dabs and pressure-dependent deformation as supported by a separately versioned calibrated contract or explicitly deferred. The initial implementation excludes them unless this design and its Advances are revised.
- [ ] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] A versioned contract distinguishes mechanical pressure, shifted contact footprint and optical ink; orientation is independent of travel direction.
- [ ] Every proposed action has explicit finite bounds, expected geometry and falsifying controls. Uncalibrated historical tool properties are marked unknown.
- [ ] Record proceed with a declared synthetic tool model, revise, or stop; investigation completion cannot claim a physically calibrated historical pen or an action gate pass.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

Inverse-width inference can manufacture a seemingly exact pen model. Keep uncertainty and fixed-tool fallback; do not alter renderer defaults or claim calibration from static pixels alone.

Review estimate: 30 minutes, not a measured reviewability score.

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

- Added to Pass 15 phase `td018-gesture-investigation`.
- Implementation, experiments and acceptance remain pending.

## Check for Understanding

1. How does releasing one side of the nib move its footprint, not merely change width or darkness?
2. Which numeric expectations come from independent geometry, physical measurement, or declared assumptions?

