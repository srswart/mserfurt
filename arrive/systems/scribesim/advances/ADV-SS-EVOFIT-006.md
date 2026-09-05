---
advance:
  id: "ADV-SS-EVOFIT-006"
  title: "Konrad Nominal Recovery — Bounded Topology Search and Context Fitting"
  system: "scribesim"
  primary_component: "evo"
  components: ["evo", "handvalidate", "tests"]
  started_at: "2026-09-05T17:30:14Z"
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

Fit reusable nominal programs to the admitted word observations using bounded structural proposals, shared geometry and context selection, as specified in TD-018 section 6.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
This is a planned outcome record. The timestamp records drafting; implementation
has not started and no execution, CI or owner approval is claimed.

## Behavioral Change

After implementation: A replayable search can improve both structure and geometry; each scored candidate renders its own marks. The exported model generates new words without reading test images or keeping per-word geometry.

## Component Impact

Primary component: `evo`. Impacted components:
`evo`, `handvalidate`, `tests`.

Planned paths (new modules and commands are not available yet):

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

- [ ] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [ ] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [ ] test: establish failing behavioral tests for the contracts below before implementation.
- [ ] feat/evaluate: Generate skeleton-chain/loop proposals and a bounded monotone character-alignment lattice from cleaned training word masks; retain ambiguity and provenance.
- [ ] feat/evaluate: Implement split/merge, short-branch and loop/contact alternatives under the repertoire bounds; treat skeleton paths as hypotheses.
- [ ] feat/evaluate: Alternate bounded form/transition assignment with shared geometry, spacing and nib refinement; cap context beam at 32 states per text position.
- [ ] feat/evaluate: Implement multiscale masked ink/contour loss, counter and spacing terms, and complexity penalties; reject mapping/topology violations before scoring.
- [ ] feat/evaluate: Limit nuisance alignment to frozen translation/isotropic-scale bounds; prohibit arbitrary word warps and target-conditioned generation.
- [ ] feat/evaluate: Run matched-budget fixed-topology and structural/context ablations with three seeds, 5,000 word-render evaluations and 30 minutes per seed caps after a smoke profile.
- [ ] feat/evaluate: Select on development only; export frozen checkpoint, full trace, component losses, support counts, runtime and stop reason for later locked evaluation.
- [ ] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] Changing locked-test pixels cannot change proposals, checkpoint selection, learned parameters or context rules.
- [ ] A synthetic missing-loop/branch case can select an alternative structure that the v1 fixed-topology search cannot express.
- [ ] Known wrong-letter, filled-counter and aspect-distortion controls do not beat their correct counterparts under the frozen objective.
- [ ] Budgets terminate predictably, checkpoints replay, and unavailable/unsupported structures produce explicit unresolved results.
- [ ] Real-data results include fixed-topology and context ablations; an unsuccessful run is reported as such rather than promoted.

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

Pending implementation; none of these evidence types is claimed as completed.

- [ ] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [ ] `tdd:red-green`: capture focused failing and passing test commands and results.
- [ ] fixed-topology versus structural/context ablation report at matched budgets
- [ ] exported reusable hand, checkpoint/configuration/source hashes and search trace
- [ ] train/development panels, unresolved-symbol diagnostics and actual runtime
- [ ] Record local integration checks separately from provider CI and owner review.
- [ ] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

None implemented in this planning change. Record scoped defects and their
regressions here during execution; do not imply unrelated renderer defects are fixed.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Why is an ink skeleton only a proposal for a broad-nib trajectory?
2. What prevents the fitter from memorizing whole-word images or selecting on test data?

