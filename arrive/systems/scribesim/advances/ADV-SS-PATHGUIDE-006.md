---
advance:
  id: "ADV-SS-PATHGUIDE-006"
  title: "Gesture Action Bridge — Desired Tracks, Realized Contact and Ownership"
  system: "scribesim"
  primary_component: "pathguide"
  components: ["pathguide","handflow","gesture","nibcontact","handvalidate","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api","migration"]
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Carry intentional gesture actions through the existing planner/controller into auditable actual trajectory fields, rather than painting the desired profile as if it had been achieved.

**Work kind:** Implementation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Drafting timestamp only: no implementation, investigation run, gate pass, CI or owner approval is claimed.

## Behavioral Change

After this Advance: Versioned guides and actual traces retain bounded orientation/contact state and full layer ownership. Tracking lag, rate limiting and unsupported actions become measurable failures, not hidden ideal playback.

## Component Impact

- `scribesim/pathguide/gesture_actions.py (planned adapter)`
- `scribesim/handflow/planning.py and controller.py (existing execution path)`
- `scribesim/handvalidate/model.py and bridge.py (realized fields and painting)`
- `tests/test_gesture_action_bridge.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/action_bridge/ (planned traces/proofs)`

These are planned implementation/evidence locations, not existing APIs.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-NIBCONTACT-002](ADV-SS-NIBCONTACT-002.md)
- [ADV-SS-PATHGUIDE-005](ADV-SS-PATHGUIDE-005.md)
- [ADV-SS-HANDFLOW-008](ADV-SS-HANDFLOW-008.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before creating branches or commits.
- [ ] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [ ] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [ ] Sample desired pose/action tracks by physical gesture arc length, retaining topology across primitive boundaries and transforming tangents, angle and edge side into the physical frame.
- [ ] Extend versioned planner/controller state with supported realized orientation and active-edge interval. Use frozen actuator rate/tracking bounds; define deterministic updates and initialization at explicit contact/lift events.
- [ ] Keep pressure/speed constant and session expression disabled. Reuse the existing controller; do not add a second simulator or make desired action values stand in for realized state.
- [ ] Render actual proofs exclusively from realized pose/contact fields. Persist desired versus actual tracking errors, topology and primitive/gesture/profile/letter/word/line spans with multiple overlap contributors.
- [ ] Reject missing required new fields in old readers, stale model/tool IDs and unsupported action tracks. Preserve legacy guide/repertoire operation through explicit version handling.
- [ ] Test deliberately rate-limited action tracking, swapped edge sides, wrap transitions, gesture segmentation, no-ink air motion and word-space boundaries. Desired-perfect/actual-wrong fixtures must fail.
- [ ] Publish direct/sampled/actual panels and fresh-process traces under the frozen synthetic tool contract; real G1/G2 prerequisites still apply to real proof execution.
- [ ] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] Actual tracking/contact errors and convergence meet the independently frozen bounds; failed actuation remains visible even when desired playback is perfect.
- [ ] Every realized mark has exact continuous-contact and logical ownership; explicit lifts and spaces create no ink connectors.
- [ ] Legacy replay remains unchanged or unsupported migrations fail explicitly. Controller implementation does not itself approve a learned action profile.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

An apparently perfect bridge may simply echo desired contact values. Include forced-lag/unsupported-action tests, retain desired/actual separation and roll back new version adapters without changing prior snapshots.

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

1. Which state fields prove the controller realized an action instead of copying its requested profile?
2. How are orientation and left/right contact transformed without swapping the physical edge?

