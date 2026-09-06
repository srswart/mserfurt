---
advance:
  id: "ADV-SS-CURRICULUM-004"
  title: "Stroke Learning — Shared Primitive Practice and Transfer"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","evo","handvalidate","tests"]
  started_at: "2026-09-06T04:10:57Z"
  implementation_completed_at: "2026-09-06T04:49:20Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "shared/training/konrad_hand_recovery/stroke_language_v1/strokes/synthetic/S1.json", "shared/training/konrad_hand_recovery/stroke_language_v1/strokes/real_attempt/report.json"]
  model_usage: []
  status: complete
---

## Objective

Actually fit a reusable primitive vocabulary, then prove its improvement and reuse. Controller configuration selection alone is not stroke learning.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
Implementation and synthetic training/replay are complete. Real-source fitting is blocked at live G0 with zero evaluations. No learned real hand, learned letter recipes, CI or owner approval is claimed.

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

- [x] branch: confirm authorization before branches or commits.
- [x] tidy: assess narrowly required preparation; preserve unrelated work.
- [x] test: commit failing behavioral tests before feature implementation when commits are authorized.
- [x] feat/evaluate: Freeze primitive exercise definitions, initialization, limits, training/development membership and the loss contract. Begin with fixed nib, pressure and nominal speed; disable depletion, fatigue, expressive rhythm, tremor and warp.
- [x] feat/evaluate: Implement bounded optimization of shared primitive geometry/attachment-port parameters, not selection among fixed controller profiles. Log actual parameter deltas, evaluations and before/after objective components.
- [x] feat/evaluate: Use known-program synthetic targets to test recoverability first. Fit real primitive hypotheses only with live G0-admitted training evidence: source-derived segments or latent stroke assignments inside word crops, with masks and uncertainty. Never count several slices of one occurrence as independent support.
- [x] feat/evaluate: Compare frozen handcrafted primitives with fitted shared primitives under matched budgets. Freeze the primitive checkpoint before letter-recipe learning; defer global end-to-end refinement until staged transfer has been demonstrated.
- [x] feat/evaluate: Freeze up to eight primitive families and seeds 7/19/41; cap each ablation/seed at 5000 primitive-or-composed-target renders or 1800 seconds, whichever occurs first. One diagnosed revision maximum; failed fits issue a stop/revise report.
- [x] feat/evaluate: Produce stroke-only sheets at common physical scale, reference/hypothesis/initial/fitted/actual panels, native metrics and parameter changes. Include held-out scales, positions and compositions to test transfer rather than memorizing exercises.
- [x] evidence: record red/green commands, actual budget use, hashes, scope and outcome before marking completion.

## Validation Gates

- [x] S1: genuine shared-parameter learning beats the frozen-prior baseline on predeclared development/held-out synthetic exercises while satisfying shape/port constraints.
- [x] Actual neutral execution preserves the learned nominal primitive inside frozen engineering tolerances; training never compensates for controller errors by corrupting the nominal target.
- [x] Real-source and synthetic checkpoint status are separate. Missing labels/calibration/support blocks reference-grounded acceptance, not synthetic language tests.
- [x] Reviewer sees visible stroke-level before/after evidence; static pixels do not establish true historical stroke order, force or timing.

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

- [x] Frozen fixtures, splits, constraints, objective/limits and model/code identities.
- [x] Before/after practice sheets, decomposition proofs and transfer results.
- [x] Replay and neutral direct/sampled/actual comparisons; real review only when performed.
- [x] `arrive plan check`, `git diff --check`, focused tests and clean-checkout validation.
- [x] Before authorized merge, run `arrive pr check --strict --json`; record installed-tool limitations separately from provider CI.

### Executed outcome

- Red commit 36b569a failed before the learning module existed. No preparatory refactor was needed. Local focused/regression validation passes 122 tests in 86.65 seconds. A clean clone of cba4d05 passes the same 122 tests in 80.40 seconds and independently re-evaluates the frozen S1 bundle with the same passing hashes; imports resolve to the clone, not the original checkout.
- Implemented bounded coordinate optimization of shared primitive interior control points. Endpoints, port cones, recipes, nib/pressure/speed and all expressive controls remain fixed. Synthetic targets are known handcrafted strokes, not manuscript-derived trajectories.
- Six families, seeds 7/19/41 and two fresh workers per seed completed. Fitting render counts are 586/586/584 against a frozen 5000/1800-second cap. Initial held-out loss 0.49101268 falls to 0.08150537/0.08566833/0.06495253. Seed 41 is selected by development loss. Test images are scored only after fitting and cannot affect the selected model.
- Frozen-prior versus fitted-shared comparisons include unseen scale/position and paired compositions. All six primitive families change. The unchanged supplied i/u recipes receive the learned shared stem/exit parameters; they are decomposition/transfer demonstrations, not learned letters or new context rules.
- Actual neutral primitive image losses range 0.0203–0.0554, max corridor error about 0.2 mm, exact coverage and contact schedules preserved. Synthetic S1 passes. Independent evaluation re-fits frozen inputs and verifies actual traces/ownership and transfer pixels, not just a pass summary.
- Complete practice sheets, shared decomposition, before/target/after transfer PNGs, compressed actual traces, parameter-update ledgers and a sample index are retained. The full replay passes unchanged.
- Native reference mode revalidates G0 and supports explicit source/model-bound native word exercise assignments. The actual v3 attempt stops before fitting: zero admitted observations, calibration and genuine target review missing. No synthetic bypass or real training result is invented.
- Plan/diff checks pass. Strict PR metadata check retains the installed three-part-ID parser limitation; provider CI and human appearance review remain absent.

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
