---
advance:
  id: "ADV-SS-HANDVALIDATE-015"
  title: "Foundation Primitive Acceptance — Independent Current-Code S1 Extension"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","curriculum","gesture","handflow","tests"]
  started_at: "2026-09-07T13:05:58Z"
  implementation_completed_at: "2026-09-07T13:30:58Z"
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  model_usage: []
  status: complete
---

## Objective

Independently accept or reject the repaired baseline and newly learned return primitives before continuous gesture fitting.

**Work kind:** Independent evaluation. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Executed under the user's implement/update/merge workflow. The independent
evaluation is complete with a **FAIL** decision. S1 and gesture-fitting permission
remain false; the next task is source-tangent continuity repair, not new learning.

## Behavioral Change

An independent evaluator reconstructs frozen candidates, original baseline,
analytic targets, complete-frame actual motion and all-cubic subdivision in fresh
processes. Seven adversarial controls and a consumer-pinned current-code S1 reader
fail closed. All three seeds reproduce image benefit, but the compound's desired
acceleration at a subdivided upper-return seam is 402.432 > 250 mm/s². No aggregate
or visually similar ink can override that failure. Historical evidence is unchanged.

## Component Impact

- `scribesim/handvalidate/foundation_primitives.py`: independent evaluator and scoped readiness reader.
- `tests/test_handvalidate_foundation_primitives.py`: eleven behavioral/regression tests.
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitive_evaluation/`: immutable evidence, sample index and required-fix diagnosis.

Existing components remain incubating. No separate renderer/controller or new component.

## Dependencies

- [ADV-SS-CURRICULUM-010](ADV-SS-CURRICULUM-010.md)

Plan dependencies order work, not runtime admission. Consume only matching,
independently validated layer/tool/code identities. Real fitting additionally
requires live G0 and accepted real lower layers; source uncertainty and locked
test isolation are not repaired by this synthetic phase.

## Implementation Tasks

- [x] branch: used `advance/ss-handvalidate-015` under the established commit/merge authorization; starting tree clean.
- [x] tidy: assessed preparation; isolated evaluator needs no changes/refactor to frozen lower-layer code.
- [x] test: `2ac8df1` records seven observed red tests and the criteria freeze before implementation `7114491`.
- [x] Freeze and reconstruct artifact/model/tool/controller/compiler/target/split/metric lineage; reject stale or fabricated prerequisite status before proof execution.
- [x] Replay all three selected seeds in clean fresh processes with zero optimizer calls; recompute original baseline, held-out benefit and actual contact/refinements.
- [x] Execute all seven predeclared adversarial controls. Preserve below-0.1 global sensitivity failures and require exact ownership/contact/local blank guards.
- [x] Check topology-disjoint attachments, shared-parameter propagation and matched full-frame initial/target/candidate/sampled/actual scale.
- [x] Issue `S1-foundation-primitives-v1` **FAIL**, required lower/upper returns named, missing inventory explicit. Reader rejects this report despite completed evaluation.
- [x] Publish equal-scale samples, budgets, replay identities and the source-tangent repair proposal. No gesture-learning or repaired-motion experiment is counted as executed.
- [x] Record actual commands, identities, budgets, paths and scope-qualified outcome; retain all failed evidence.

## Validation Gates

- [ ] All required acceptance criteria pass: **unmet**. Every seed fails compound subdivision desired acceleration, 402.432 > 250 mm/s²; S1/gesture permission remain false.
- [x] Fresh-process replay matches all 37 non-wall artifacts per seed; failed/fabricated/stale evidence and unsupported inventory fail closed.
- [x] CURRICULUM-011 remains runtime-blocked despite completed dependency records. Real G0, actions and learned letters remain separate and unaccepted.

## Budget and Stop Rules

Use [Addendum B Section 7](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#7-budgets-and-stop-rules):
5000 renders or 1800 seconds per seed including first/replay/control/refinement work; zero optimization; at most one diagnosed rerun.
Run-001 uses 612 renders per seed including replay (1836 total), with recorded
first-plus-replay times 18.513/18.218/19.792 seconds. Zero optimization and zero
diagnosed reruns; no attempt to fit away or relax the failed desired-motion gate.
Keep immutable attempts and a cumulative ledger. Stop on unmet prerequisites or
budget exhaustion; no threshold relaxation, hidden extra search or guessed approval.

## Invariant Impact

Exact text, source/test isolation, shared lower-layer lineage, deterministic
replay and realized-contact ownership remain mandatory. Old freezes are immutable.
No fatigue, ink depletion/dips, stochastic rhythm, tremor, warp, historical
calibration claims or default renderer promotion.

## Risk + Rollback

A visually similar image can conceal contact instability, missing vocabulary or
copied geometry. Preserve failed cases and explicit execution/contract versions;
rollback to the prior mode without treating historical acceptance as current.
Review estimate is 35 minutes, not measured review or approval.

## Evidence

- [x] Frozen inputs, independent targets/controls, criteria and scope-specific identities.
- [x] Actual work/budget ledger, equal-scale samples, failures and executable replay commands.
- [x] Eleven new tests pass; all first/replay workers use clean checkout `7114491`. Expanded testing reproduces twelve failures also present on baseline `87d5faf`: one missing-nib-angle constructor plus eleven obsolete gesture-lineage expectations; no unrelated fixes.
- [x] Plan, changed local links, immutable artifact manifests, current identities and diff checks pass; ten pre-existing doctor issues unchanged and no stale generated rules.
- [x] Strict PR metadata check executed before merge. Installed parser returns `ids=[]` for this repository's `ADV-SS-*` ID; no successful strict gate or provider CI claimed.
- [x] Scope-qualified failed acceptance; no unperformed learning, repaired execution, provider CI or human review claimed.

## Bug Fixes

Closes an evaluation coverage gap: prior subdivision helper split only `stem`;
the new evaluator independently splits every cubic, including both returns.
The newly exposed chord-tangent desired-acceleration defect is diagnosed, **not
repaired**. Existing source geometry, compiler, controller and clock remain unchanged.

## Changes Made

### 2026-09-07 — 7114491: Independent evaluation complete, acceptance fails closed

- `2ac8df1` freezes criteria and seven red tests; `7114491` implements the independent evaluator/readiness reader. Eleven final tests pass; no preparatory refactor was needed.
- All seeds preserve the original baseline and reproduce full/family-local benefits. Seven adversarial controls detect mutations; known global sensitivity failures stay failures under the unchanged 0.1 minimum.
- Clean first/replay artifacts match exactly, including the new compound failure. 1836 total renders, zero optimization/revisions, no changed candidate or historical hashes.
- `480ed50` preserves failed evidence and regressions. Final clean expanded suite: 190 passes / 12 failures, versus baseline 179 passes / the identical 12 failures. All eleven new tests pass; no existing source code is modified.
- The upper-return artificial seam has desired acceleration 402.431643 mm/s²; actual acceleration is 147.491782 and event-time drift 1.78e-15 s. Stable images and clock do not admit this desired-motion failure.
- [Evaluation and samples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitive_evaluation/README.md), [diagnosis and required next fix](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitive_evaluation/diagnosis.md), [verification](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitive_evaluation/verification.json).
- S1 and gesture permission remain false. Source-tangent repair plus refreshed no-refit current-code admission must precede CURRICULUM-011; no alphabet, actions, fatigue or historical hand is accepted.

### 2026-09-06 — plan: Prioritize reliable learned stroke foundations

- Added the bounded work to Pass 15 `td018-foundation-repair`.
- Implementation and acceptance remain pending under Addendum B.

## Check for Understanding

1. Which exact evidence and identities permit this Advance's experiment to run?
2. What visible learned or independently evaluated result distinguishes completion from scaffolding?
