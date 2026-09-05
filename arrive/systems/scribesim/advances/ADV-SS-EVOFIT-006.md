---
advance:
  id: "ADV-SS-EVOFIT-006"
  title: "Konrad Nominal Recovery — Bounded Topology Search and Context Fitting"
  system: "scribesim"
  primary_component: "evo"
  components: ["evo", "handvalidate", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: "2026-09-05T18:45:28Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence:
    - "shared/training/konrad_hand_recovery/nominal_recovery_v1/synthetic/report.json"
    - "shared/training/konrad_hand_recovery/nominal_recovery_v1/real_attempt_final/report.json"
  model_usage: []
  status: complete
---

## Objective

Fit reusable nominal programs to the admitted word observations using bounded structural proposals, shared geometry and context selection, as specified in TD-018 section 6.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
Implementation and bounded synthetic evaluation are complete. The real-corpus attempt is blocked at G0 with zero fitting evaluations. No recovered Konrad model or promotion is claimed.

## Behavioral Change

After implementation: A replayable search can improve both structure and geometry; each scored candidate renders its own marks. The exported model generates new words without reading test images or keeping per-word geometry.

## Component Impact

Primary component: `evo`. Impacted components:
`evo`, `handvalidate`, `tests`.

Implemented paths:

- scribesim/evofit/recovery.py (new)
- scribesim/evofit/repertoire.py (proposal and composition integration)
- tests/test_repertoire_recovery.py (new); focused ARRIVE test selector coverage
- shared/training/konrad_hand_recovery/ (immutable run bundles)

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-EVOFIT-005](ADV-SS-EVOFIT-005.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [x] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [x] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [x] test: establish failing behavioral tests for the contracts below before implementation.
- [x] feat/evaluate: Generate skeleton-chain/loop proposals and a bounded monotone character-alignment lattice from cleaned training word masks; retain ambiguity and provenance.
- [x] feat/evaluate: Implement split/merge, short-branch and loop/contact alternatives under the repertoire bounds; treat skeleton paths as hypotheses.
- [x] feat/evaluate: Alternate bounded form/transition assignment with shared geometry, spacing and nib refinement; cap context beam at 32 states per text position.
- [x] feat/evaluate: Implement multiscale masked ink/contour loss, counter and spacing terms, and complexity penalties; reject mapping/topology violations before scoring.
- [x] feat/evaluate: Limit nuisance alignment to frozen translation/isotropic-scale bounds; prohibit arbitrary word warps and target-conditioned generation.
- [x] feat/evaluate: Run matched-budget fixed-topology and structural/context ablations with three seeds, 5,000 word-render evaluations and 30 minutes per seed caps after a smoke profile.
- [x] feat/evaluate: Select on development only; export frozen checkpoint, full trace, component losses, support counts, runtime and stop reason for later locked evaluation.
- [x] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [x] Changing locked-test pixels cannot change proposals, checkpoint selection, learned parameters or context rules.
- [x] A synthetic missing-loop/branch case can select an alternative structure that the v1 fixed-topology search cannot express.
- [x] Known wrong-letter, filled-counter and aspect-distortion controls do not beat their correct counterparts under the frozen objective.
- [x] Budgets terminate predictably, checkpoints replay, and unavailable/unsupported structures produce explicit unresolved results.
- [ ] Real-data ablations: blocked by G0 (zero admitted observations); not executed. Matched-budget synthetic ablations are complete and are not substitutes for this acceptance gate.

Focused validation: Use synthetic known-structure recovery, held-out isolation, stale-cache rejection, real-candidate image sensitivity, mask semantics, budget termination and new-context composition regressions.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: Topology freedom can overfit uncertain labels, and search may be expensive. Keep shared support constraints, fixed budgets, adverse controls and independent evaluation; split the proposal engine and fitter into smaller follow-up Advances if review exceeds the estimate.

Rollback: Use the retained v1 fitter or previous frozen checkpoint; discard only candidate selection, retaining negative evidence and source provenance.

Review estimate: 40 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Actual local evidence follows; no provider CI or human approval has occurred.

- [x] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [x] `tdd:red-green`: capture focused failing and passing test commands and results.
- [x] fixed-topology versus structural/context ablation report at matched budgets
- [x] exported reusable hand, checkpoint/configuration/source hashes and search trace
- [x] train/development panels, unresolved-symbol diagnostics and actual runtime
- [x] Record local integration checks separately from provider CI and owner review.
- [x] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

Initialization timeouts now return an explicit unresolved result rather than leaking StopIteration. Duplicate observation IDs cannot overwrite frozen per-observation alignment. Cache content corruption is rejected.

### Actual execution and boundaries

- No preparatory tidy was needed: the opt-in engine composes the new repertoire without changing the production fitter or defaults.
- Red: focused recovery tests failed module import, committed as `9a83a22`; additional initialization-timeout regression failed before its fix, committed as `c71bca4`.
- Green: 7 recovery tests passed; combined TD-018 and prior word-recovery/nominal-review suite passed 58 tests in 13.24 seconds.
- Training-only thinning/graph chains and counter-loop hypotheses retain observation IDs and three monotone alignment alternatives; the lattice caps at 32 states. These are priors for contact trajectories, not historical stroke-order findings.
- Candidate operations include chain replacement, split/merge, short branches, lifts, context assignment and bounded inter-form joins, shared cubic controls, advance, spacing and nib changes. Every score renders that candidate, and all train/development render calls count against the same per-run budget. Rejected repertoire limits are reported rather than truncated during search.
- The frozen synthetic-tested objective combines native masked ink overlap at three morphological scales, contour, projections/spacing, counter and mass terms plus complexity. Known background constrains extra marks; unknown pixels are not white training targets. Translation +/-2 pixels and scale multipliers 0.95/1/1.05 are estimated on the initial raster and frozen, not reoptimized per candidate.
- After a 24-render smoke, all nine ablations used exactly 5,000 rendered-word evaluations each and stopped on evaluation_budget, below the 1,800-second cap. Seeds 7/19/41: fixed development loss 0.3962/0.3992/0.3969; structural 0.0664/0.0890/0.0684; context 0.0846/0.1146/0.1102. These are synthetic missing-loop controls, not manuscript accuracy. Runtime per run was 8.44–14.25 seconds.
- The selected synthetic checkpoint was structural seed 7; full component traces, rejected-operation counts, support, alignments, source fixtures and hashes are retained. Its equal-scale train/development panel was inspected.
- Actual corpus execution is recorded separately in `real_attempt_final/`: G0 blocked, zero evaluations, no locked-test scoring. The earlier `real_attempt/` is retained as negative evidence. Real-source loss calibration and fit remain unexecuted, not silently waived by this implementation completion.
- `arrive plan check` passed. Strict PR check was run with the Advance ID; installed parser again returned ids=[] for the three-part repository identifier. No provider CI evidence exists.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Why is an ink skeleton only a proposal for a broad-nib trajectory?
2. What prevents the fitter from memorizing whole-word images or selecting on test data?
