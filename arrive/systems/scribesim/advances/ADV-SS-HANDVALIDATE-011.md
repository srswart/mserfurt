---
advance:
  id: "ADV-SS-HANDVALIDATE-011"
  title: "Konrad Layered Acceptance — Stroke Transfer and Revalidated G0–G2"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","evo","curriculum","pathguide","tests"]
  started_at: "2026-09-06T03:57:59Z"
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

Audit the learned stroke language through primitive, letter, within-word and inter-word transfer, then decide real nominal/neutral acceptance. Reuse benchmark and bridge infrastructure, not the independent per-character curve model as the candidate.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
This is a planned outcome record. The timestamp records drafting only;
implementation, experimental execution, CI and owner approval are not claimed.

## Behavioral Change

After implementation: Frozen S0–S4 checkpoints and their visible learning/transfer evidence accompany either identity-bound real G0/G1/neutral G2 results or an explicit stop at the first failed prerequisite. Familiar catalog shapes and controller-profile selection cannot certify shared-stroke learning.

## Component Impact

Primary component: `handvalidate`. Planned paths and artifacts:

- `scribesim/evofit/reference_dataset.py and stroke_language.py (live G0 and layered model)`
- `scribesim/curriculum/stroke_learning.py, letter_recipes.py, letter_context.py and word_context.py (planned checkpoint/evidence sources)`
- `scribesim/handvalidate/nominal.py and bridge.py`
- `tests/test_reference_dataset.py, tests/test_repertoire_recovery.py, tests/test_handvalidate_nominal_specimen.py, tests/test_repertoire_pathguide.py`
- `shared/training/konrad_hand_recovery/stroke_language_v1/acceptance/ (new evidence and stage sample index)`

No component stage changes. Add narrow ownership/test selectors only if required.

## Dependencies

- [ADV-SS-EXEMPLAR-008](ADV-SS-EXEMPLAR-008.md)
- [ADV-SS-CURRICULUM-007](ADV-SS-CURRICULUM-007.md)
- [ADV-SS-HANDVALIDATE-008](ADV-SS-HANDVALIDATE-008.md)
- [ADV-SS-PATHGUIDE-005](ADV-SS-PATHGUIDE-005.md)

Dependencies order implementation; live identity-bound gate records separately
authorize real candidate execution. Completed blocked experiments do not pass gates.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before creating a branch or committing.
- [ ] tidy: assess preparatory changes; avoid unrelated refactoring.
- [ ] test: establish and record failing behavioral tests before implementation.
- [ ] feat/evaluate: Recompute v3 integrity, admission, source-line leakage and symbol/context coverage. Freeze calibration from independent admitted train/development repeats and negative shape controls, excluding test observations.
- [ ] feat/evaluate: Obtain genuine target review against the existing benchmark contract, recording reviewer identity, date and artifact hashes. Emit blocked G0 when evidence or review is missing; never fill review fields on the owner's behalf.
- [ ] feat/evaluate: Revalidate S0–S4 model/code identities, fixed lower-layer checkpoints, objective/limit freezes, bounded training ledgers and composition-disjoint transfer evidence. Replay selected staged checkpoints for seeds 7/19/41; this Advance performs evaluation, not another unbudgeted optimization run.
- [ ] feat/evaluate: Prove primitives are shared across letters and both context layers preserve lineage. Compare frozen-prior, learned and context-off/spacing-only/stroke-context results as appropriate. Reject per-letter residual curves or per-word caches used to bypass the hierarchy.
- [ ] feat/evaluate: Adapt model identity checks, compilation and nominal/bridge evidence to the versioned stroke language, preserving strict rejection of stale summaries and old schema-2 models posing as new checkpoints. Freeze criteria before candidate proof inspection. Build the unchanged three-line and five-string nominal specimen; unsupported inventory blocks G1 and is reported, not normalized away. Collect genuine appearance and independent-reading review.
- [ ] feat/evaluate: Only after live G1 passes, freeze model-bound development tolerances and evaluate the exact neutral repertoire bridge for G2. Revalidate code/configuration identities after any controller changes before later G3 execution.
- [ ] feat/evaluate: Keep test reservations locked through development. If a later evaluation opens them, record that exposure and never reuse those observations as a fresh test set.
- [ ] feat/evaluate: Issue a stop/revise/proceed decision with all negative results. A failed gate ends real downstream execution; require a new budget before another recovery search.
- [ ] evidence: record red/green commands, artifact identities and the actual outcome before marking implementation complete.

## Validation Gates

- [ ] Missing source calibration, insufficient support, stale review identities or forged pass summaries block G0/G1/G2.
- [ ] Every real layer checkpoint has matching accepted lower-layer lineage and transfer evidence; parameter changes propagate through all dependent identities. Old curriculum completion does not satisfy S0–S4.
- [ ] Fresh processes reproduce the selected model, proof pixels, exact text ownership and neutral trajectory metrics.
- [ ] Reports distinguish infrastructure completion, numeric engineering results, human review and real gate acceptance.
- [ ] A blocked run records zero downstream evaluations where the prerequisite failed; completed failure evidence is not permission for folio integration.

## Invariant Impact

Preserve exact text, source provenance, native geometry, leakage-resistant
splits, deterministic replay and the separation of implementation completion
from model acceptance. Production defaults and prior evidence remain unchanged.

## Risk + Rollback

Calibration or reviewed proofs can leak into fitting or stale acceptance can survive a changed model. Bind evidence to exact artifacts and stop at the first failed gate; retain prior bundles unchanged.

Review estimate: 40 minutes, not a measured reviewability score.

## Evidence

Planned evidence: stroke practice, letter assembly, pair/triple context and word-sequence sheets; frozen S0–S4 learning/transfer/ablation ledgers; revalidated G0; nominal G1/reading review and neutral G2 when allowed; otherwise exact scope debt and first blocking reason. Synthetic and real-stage acceptance remain separately labeled.

- [ ] Record focused tests and reproducibility checks.
- [ ] Run `arrive plan check` and `git diff --check`.
- [ ] Before an authorized merge, run `arrive pr check --strict --json` and record any installed-tool limitation separately from provider CI.
- [ ] Do not claim provider CI or human approval without actual evidence.

## Bug Fixes

No implementation changes yet; this record scopes the diagnosed repair/evaluation.

## Changes Made

### 2026-09-06 — plan: Scope the post-guided repair

- Added to Pass 15, phase `td018-repair`, ahead of folio work.
- Existing benchmark/nominal/guided completion records and negative evidence remain unchanged.

### 2026-09-06 — revision: Shared stroke-language curriculum first

- Moved to phase `td018-word-context`; supersedes the earlier `td018-repair` ordering.
- Strokes, letter recipes, within-word context and inter-word context are separate learned layers.
- Ink, fatigue and other expressive work are deferred; no implementation or acceptance is claimed.

## Check for Understanding

1. Which evidence allows fitting to start, and which separately allows guided execution?
2. What changes invalidate a previously passing gate?
