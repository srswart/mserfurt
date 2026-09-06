---
advance:
  id: "ADV-SS-NIBCONTACT-002"
  title: "Intentional Nib Contact — Shifted Edge Footprints and Canonical Sweep"
  system: "scribesim"
  primary_component: "nibcontact"
  components: ["nibcontact","gesture","evo","handvalidate","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: "2026-09-06T14:12:03Z"
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

Extend the existing broad-edge swept-nib path to support the frozen orientation and partial-edge contract without a parallel renderer or ink-depletion workaround.

**Work kind:** Implementation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Implementation/evaluation status and any unexecuted acceptance work are recorded below. No provider CI or owner approval is claimed.

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

- [x] branch: confirm authorization before creating branches or commits.
- [x] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [x] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [x] Implement the frozen tool width/thickness and active-edge interval geometry in a focused helper called by the canonical sweep. Extend existing rendering paths; do not create an independent brush or acceptance-only renderer.
- [x] Apply unwrapped orientation and asymmetric surviving-edge endpoints in the declared physical frame. Transform y-up/y-down orientation and edge-side conventions consistently; reject invalid or unsupported fields.
- [x] Separate geometric contact from pressure and optical deposition on the new opt-in action path. Keep adequate constant ink and pressure; no reservoir/dip repair, pressure deformation or direction-width double application.
- [x] Preserve the exact legacy full-edge fixed-tool mode and prior bundle playback. Any new semantics require an explicit version; no default switch or rewriting frozen evidence.
- [x] Validate against the independent fixtures from NIBCONTACT-001, including left/right endpoint translations, fixed-angle lines/arcs, wraps and declared overlap geometry.
- [x] Reject stationary dabs/nonconstant pressure-speed tracks until separately scoped; unsupported actions cannot degrade silently to centered width reduction or opacity.
- [x] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [x] Full-contact legacy fixtures remain equivalent; asymmetric edge cases produce the expected translated endpoints, not just equal scalar widths.
- [x] Rotation/release alter swept geometry with constant ink and pressure; frozen analytic and convergence checks pass.
- [x] Direct and trajectory renderers use the same helper while test expectations remain independent. This implementation pass is not S1-action or historical pen acceptance.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

Changing a shared renderer could alter frozen legacy output or hide pressure/ink coupling. Gate new fields behind the versioned opt-in contract and retain the old full-contact call path and regression fixtures.

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

- Authorized feature branch and per-Advance local merge; no preparatory refactor needed.
- Red geometry/legacy tests: `49eb8e2`; implementation `181e295`.
  Evidence-builder red: `c3fa40e`; immutable proofs `3fdc385`.
- Single physical footprint helper feeds the existing canonical sweep; the
  bridge uses the same sweep for nominal/actual versioned contact samples.
  Legacy call path and frozen pixel hash are unchanged; old readers reject new fields.
- Eight independent fixture checks pass: maximum oracle disagreement 0.021383
  (bound 0.05), refinement 0.006514 or less (bound 0.03). Directed edge reflection
  and endpoint translation tested; fixed pressure/width and unsupported dabs fail closed.
- 25 renders in 0.2733s, no optimization or revision. 49 tests pass locally
  (3.60s) and clean clone `/tmp/td018-contact-clean.Ardmyb` at `3fdc385` (3.75s).
  Hash-seed-839 report/PNG replay is byte-identical; only wall receipt differs.
- Whole-file renderer/bridge identities change deliberately. Older frozen gate
  records are retained unchanged and must fail current admission as stale.
  Pixel compatibility does not refresh an acceptance identity; no new S1 pass.
- Strict PR metadata check ran and hit the existing three-part-ID parser
  limitation (`ids: []`), not provider CI. Plan/link/diff checks pass.
- [Samples and replay](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/contact/README.md).

## Check for Understanding

1. Where is the single source of truth for active nib footprint geometry?
2. How do the tests distinguish correct partial-edge motion from a centered shrink?
