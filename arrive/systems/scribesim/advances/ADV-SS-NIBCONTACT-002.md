---
advance:
  id: "ADV-SS-NIBCONTACT-002"
  title: "Intentional Nib Contact — Shifted Edge Footprints and Canonical Sweep"
  system: "scribesim"
  primary_component: "nibcontact"
  components: ["nibcontact","gesture","evo","handvalidate","tests"]
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

Extend the existing broad-edge swept-nib path to support the frozen orientation and partial-edge contract without a parallel renderer or ink-depletion workaround.

**Work kind:** Implementation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Drafting timestamp only: no implementation, investigation run, gate pass, CI or owner approval is claimed.

## Behavioral Change

After this Advance: Nominal and trajectory painting share one physical footprint calculation. Left/right edge release shifts the contact footprint correctly, and deliberate rotation changes geometry rather than only darkness.

## Component Impact

- `scribesim/evo/nib_contact.py (planned footprint helper)`
- `scribesim/evo/renderer.py (canonical sweep integration)`
- `scribesim/handvalidate/bridge.py (same footprint consumption)`
- `tests/test_nib_contact.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/contact/ (planned geometry fixtures)`

These are planned implementation/evidence locations, not existing APIs.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-NIBCONTACT-001](ADV-SS-NIBCONTACT-001.md)
- [ADV-SS-GESTURE-001](ADV-SS-GESTURE-001.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before creating branches or commits.
- [ ] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [ ] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [ ] Implement the frozen tool width/thickness and active-edge interval geometry in a focused helper called by the canonical sweep. Extend existing rendering paths; do not create an independent brush or acceptance-only renderer.
- [ ] Apply unwrapped orientation and asymmetric surviving-edge endpoints in the declared physical frame. Transform y-up/y-down orientation and edge-side conventions consistently; reject invalid or unsupported fields.
- [ ] Separate geometric contact from pressure and optical deposition on the new opt-in action path. Keep adequate constant ink and pressure; no reservoir/dip repair, pressure deformation or direction-width double application.
- [ ] Preserve the exact legacy full-edge fixed-tool mode and prior bundle playback. Any new semantics require an explicit version; no default switch or rewriting frozen evidence.
- [ ] Validate against the independent fixtures from NIBCONTACT-001, including left/right endpoint translations, fixed-angle lines/arcs, wraps and declared overlap geometry.
- [ ] Reject stationary dabs/nonconstant pressure-speed tracks until separately scoped; unsupported actions cannot degrade silently to centered width reduction or opacity.
- [ ] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] Full-contact legacy fixtures remain equivalent; asymmetric edge cases produce the expected translated endpoints, not just equal scalar widths.
- [ ] Rotation/release alter swept geometry with constant ink and pressure; frozen analytic and convergence checks pass.
- [ ] Direct and trajectory renderers use the same helper while test expectations remain independent. This implementation pass is not S1-action or historical pen acceptance.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

Changing a shared renderer could alter frozen legacy output or hide pressure/ink coupling. Gate new fields behind the versioned opt-in contract and retain the old full-contact call path and regression fixtures.

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

1. Where is the single source of truth for active nib footprint geometry?
2. How do the tests distinguish correct partial-edge motion from a centered shrink?

