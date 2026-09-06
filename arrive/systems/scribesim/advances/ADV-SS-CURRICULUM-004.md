---
advance:
  id: "ADV-SS-CURRICULUM-004"
  title: "Stroke Learning — Shared Primitive Practice and Transfer"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","evo","handvalidate","tests"]
  started_at: "2026-09-06T04:10:57Z"
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

Actually fit a reusable primitive vocabulary, then prove its improvement and reuse. Controller configuration selection alone is not stroke learning.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
Drafting timestamp only: no implementation, training, CI or owner approval is claimed.

## Behavioral Change

Actually fit a reusable primitive vocabulary, then prove its improvement and reuse. Controller configuration selection alone is not stroke learning. The new curriculum must produce visible layer-specific
learning and transfer evidence before downstream acceptance.

## Component Impact

- `scribesim/curriculum/stroke_learning.py (new)`
- `scribesim/evofit/stroke_language.py and recovery.py (shared-parameter fitting)`
- `tests/test_stroke_learning.py (new)`
- `shared/training/konrad_hand_recovery/stroke_language_v1/strokes/ (new immutable evidence)`

Use tracked modules and scoped test selectors; clean-checkout imports are required.
No production renderer or component stage changes.

## Dependencies

- [ADV-SS-EVOFIT-007](ADV-SS-EVOFIT-007.md)
- [ADV-SS-EXEMPLAR-008](ADV-SS-EXEMPLAR-008.md)

Completion is not acceptance. Synthetic scaffolding may execute with explicitly
unaccepted inputs. Reference-derived fitting requires live G0, and real layer
acceptance requires the matching accepted lower-layer checkpoint. Do not import
an older curriculum's pass summary as evidence of shared-stroke learning.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before branches or commits.
- [ ] tidy: assess narrowly required preparation; preserve unrelated work.
- [ ] test: commit failing behavioral tests before feature implementation when commits are authorized.
- [ ] feat/evaluate: Freeze primitive exercise definitions, initialization, limits, training/development membership and the loss contract. Begin with fixed nib, pressure and nominal speed; disable depletion, fatigue, expressive rhythm, tremor and warp.
- [ ] feat/evaluate: Implement bounded optimization of shared primitive geometry/attachment-port parameters, not selection among fixed controller profiles. Log actual parameter deltas, evaluations and before/after objective components.
- [ ] feat/evaluate: Use known-program synthetic targets to test recoverability first. Fit real primitive hypotheses only with live G0-admitted training evidence: source-derived segments or latent stroke assignments inside word crops, with masks and uncertainty. Never count several slices of one occurrence as independent support.
- [ ] feat/evaluate: Compare frozen handcrafted primitives with fitted shared primitives under matched budgets. Freeze the primitive checkpoint before letter-recipe learning; defer global end-to-end refinement until staged transfer has been demonstrated.
- [ ] feat/evaluate: Freeze up to eight primitive families and seeds 7/19/41; cap each ablation/seed at 5000 primitive-or-composed-target renders or 1800 seconds, whichever occurs first. One diagnosed revision maximum; failed fits issue a stop/revise report.
- [ ] feat/evaluate: Produce stroke-only sheets at common physical scale, reference/hypothesis/initial/fitted/actual panels, native metrics and parameter changes. Include held-out scales, positions and compositions to test transfer rather than memorizing exercises.
- [ ] evidence: record red/green commands, actual budget use, hashes, scope and outcome before marking completion.

## Validation Gates

- [ ] S1: genuine shared-parameter learning beats the frozen-prior baseline on predeclared development/held-out synthetic exercises while satisfying shape/port constraints.
- [ ] Actual neutral execution preserves the learned nominal primitive inside frozen engineering tolerances; training never compensates for controller errors by corrupting the nominal target.
- [ ] Real-source and synthetic checkpoint status are separate. Missing labels/calibration/support blocks reference-grounded acceptance, not synthetic language tests.
- [ ] Reviewer sees visible stroke-level before/after evidence; static pixels do not establish true historical stroke order, force or timing.

## Invariant Impact

Exact text, source uncertainty, split isolation, shared-parameter lineage,
deterministic compilation and actual trajectory ownership remain mandatory.
Synthetic mechanics, real-source fitting and human appearance acceptance are
separate. Layer gates S0–S4 supplement, not replace, G0–G4.

## Risk + Rollback

A layer can disguise copied character geometry or memorized words as learning.
Reject unrestricted residuals and per-instance lookup; retain frozen lower-layer
checkpoints, ablations and failed evidence. Revert only the new opt-in model,
not historical snapshots or production defaults. Review estimate: 40 minutes.

## Evidence

- [ ] Frozen fixtures, splits, constraints, objective/limits and model/code identities.
- [ ] Before/after practice sheets, decomposition proofs and transfer results.
- [ ] Replay and neutral direct/sampled/actual comparisons; real review only when performed.
- [ ] `arrive plan check`, `git diff --check`, focused tests and clean-checkout validation.
- [ ] Before authorized merge, run `arrive pr check --strict --json`; record installed-tool limitations separately from provider CI.

## Bug Fixes

None implemented. This planned Advance addresses the missing layered-learning
contract, not the later ink or fatigue defects.

## Changes Made

### 2026-09-06 — plan: Adopt shared-stroke layered learning

- Added to Pass 15 phase `td018-strokes`.
- Deferred expressive work until strokes, letters and both context levels are proven.

## Check for Understanding

1. What changes are learned at this layer, and which lower-layer parameters stay frozen?
2. Which visible transfer test prevents this layer from merely reproducing supplied shapes?

