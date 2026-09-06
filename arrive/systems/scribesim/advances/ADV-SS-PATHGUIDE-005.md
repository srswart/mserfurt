---
advance:
  id: "ADV-SS-PATHGUIDE-005"
  title: "Konrad Guided Bridge — Preserve Forms, Contact and Text Ownership"
  system: "scribesim"
  primary_component: "pathguide"
  components: ["pathguide", "handflow", "handvalidate", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: "2026-09-06T03:22:46Z"
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence:
    - "shared/training/konrad_hand_recovery/guided_bridge_v1/synthetic/report.json"
    - "shared/training/konrad_hand_recovery/guided_bridge_v1/real_attempt/G2.json"
  model_usage: []
  status: complete
---

## Objective

Convert a G1-passing repertoire into DensePathGuide inputs without losing contextual choices, stroke structure, physical scale or text ownership; establish G2.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
Implementation and synthetic diagnostic execution are complete. Actual candidate integration is blocked by G1; synthetic G2 fails its width bound. Neither is promoted.

## Behavioral Change

After implementation: The selected WordPlan is sampled into physical trajectories with explicit lifts and an ownership sidecar. Direct nominal, sampled playback and neutral guided output can be compared independently.

## Component Impact

Primary component: `pathguide`. Impacted components:
`pathguide`, `handflow`, `handvalidate`, `tests`.

Implemented paths:

- scribesim/pathguide/repertoire.py (new adapter and ownership sidecar)
- scribesim/handvalidate/bridge.py (focused bridge bench)
- scribesim/handflow/model.py and controller.py (actual sample-to-plan attribution)
- scribesim/pathguide/io.py and scribesim/evofit/workflow.py (defer optional extraction imports until needed)
- tests/test_repertoire_pathguide.py (new); focused ARRIVE test selector coverage

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-HANDVALIDATE-008](ADV-SS-HANDVALIDATE-008.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [x] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [x] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [x] test: establish failing behavioral tests for the contracts below before implementation.
- [x] feat/evaluate: Require a matching G1-pass model/configuration record before candidate integration.
- [x] feat/evaluate: Sample cubics by arc length in physical millimetres, preserving baseline orientation, nib/pressure priors, entry/exit tangents and explicit air travel.
- [x] feat/evaluate: Resolve contextual forms before composing the dense word guide; preserve form/stroke/text-span ownership in a versioned sidecar.
- [x] feat/evaluate: Keep existing DensePathGuide loading compatible and reject adapters that drop unknown metadata required for exact attribution.
- [x] feat/evaluate: Compare nominal sweep, sampled playback and actual neutral-controller trajectory at matching scale, nib and development-frozen tolerances.
- [x] feat/evaluate: Emit G2 metrics and panels; retain guide-aligned trajectories solely for diagnostics.
- [x] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [x] The exact selected forms, contact schedule, intended intersections and logical spans survive conversion.
- [ ] Full equivalence is not accepted: sampled playback is close, but actual neutral output exceeds the synthetic maximum width-delta bound. Real tolerances and G1 remain unavailable.
- [x] The evaluated image is rendered from actual controller trajectory, not aligned or substituted guide geometry.
- [ ] Actual G1 appearance/coverage acceptance is still missing; real G2 execution is blocked.

Focused validation: Use asymmetric orientation fixtures, contextual variants, lifts, loops, shared ligature attribution and round-trip physical units. Inject an aligned-versus-actual discrepancy and verify the bench detects actual output degradation.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: A converter can make a good hand fail through coordinate or contact errors while aligned diagnostics conceal the loss. Compare each stage separately and keep actual output authoritative.

Rollback: Remove the opt-in repertoire adapter selection; keep existing guide catalogs and the accepted nominal specimen available.

Review estimate: 30 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Actual local evidence is recorded below. Provider CI and owner acceptance are not claimed.

- [x] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [x] `tdd:red-green`: capture focused failing and passing test commands and results.
- [x] nominal/playback/neutral-guided comparison panels
- [x] ownership sidecar, conversion invariants and G2 report
- [x] sampling convergence and coordinate-transform regression results
- [x] Record local integration checks separately from provider CI and owner review.
- [x] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

None implemented in this planning change. Record scoped defects and their
regressions here during execution; do not imply unrelated renderer defects are fixed.

### Execution outcome

- Authorized branch: `feat/td018-guided-bridge`. Tidy assessment: no broad refactor needed. Two legacy extraction imports were made function-local so the tracked bridge does not require ignored extraction packages at import time; a subprocess actively rejects those dependencies.
- Red: module-contract tests failed before implementation (`8fe94e2`); a finite-bound regression then exposed an accidental NaN pass (`30ad200`) and was fixed. The early convergence test was strengthened so another failed metric could not mask the NaN defect.
- Green: focused bridge and nominal/recovery regressions pass. The broad pathguide/handflow check had 27 passing tests and one legacy constructor mismatch: `test_desired_velocity_affects_acceleration` omits the already-required nib_angle_deg field. This change does not alter that constructor.
- The adapter resolves the whole WordPlan first, samples physical arc length, flips y above baseline into physical y-down, records declared air/contact transitions and shared ligature/join spans. Versioned JSON preserves the DensePathGuide object plus mandatory per-sample ownership; existing TOML loaders are unchanged. Intentional crossings are retained, rather than routed through the legacy zero-intersection validator.
- SimulationResult now reports actual trajectory-to-plan indices with a backward-compatible default. Bridge imagery is painted from the actual trajectory using the same broad-edge primitive and physical frame as nominal playback; aligned samples cannot conceal injected displacement.
- `guided_bridge_v1/synthetic/` retains three nominal/sampled/actual panels and ownership sidecars. Panel inspected. G2 is fail because maximum width delta exceeds 0.5 mm in all three synthetic cases. This exposes the legacy direction-dependent width prior; it is not an accepted hand result.
- `real_attempt/G2.json` records G1 refusal before conversion/controller execution. Real runs require matching live nominal artifacts/review and development-frozen tolerance identity. Synthetic diagnostics have no runtime acceptance authority.
- `arrive plan check` passes. Strict PR check is run but the installed parser cannot recognize the repository’s three-part Advance ID. No provider CI or owner approval is claimed.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Why must allograph selection precede conversion to a word guide?
2. Which trajectory is allowed to paint the reviewed image, and why?
