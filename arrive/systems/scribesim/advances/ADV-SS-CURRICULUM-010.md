---
advance:
  id: "ADV-SS-CURRICULUM-010"
  title: "Foundation Primitive Learning — Shared Lower and Upper Returns"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","evo","handflow","handvalidate","tests"]
  started_at: "2026-09-06T20:35:04Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration", "experiment:executed-incomplete", "replay:clean-checkout"]
  model_usage: []
  status: in_progress
---

## Objective

Actually fit the missing return primitives on independent synthetic targets while preserving the old six primitives, fixed tool and repaired execution.

**Work kind:** Learning implementation and bounded experiment. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Implementation started under the user's complete-and-merge workflow. Completion
requires executed, admitted-input learning and all stated learning gates; no
independent acceptance or human appearance approval is implied.

## Behavioral Change

The deliverable and acceptance boundary are specified in the tasks and gates below.
This record belongs to `td018-foundation-repair`; existing completed records and
failed evidence remain unchanged.

## Component Impact

- `scribesim/curriculum/foundation_primitives.py (implemented bounded fitting and evidence)`
- `scribesim/evofit/foundation_contract.py (contract consumption)`
- `tests/test_foundation_primitives.py (twelve tests)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitives/ (two immutable attempts)`

Existing components remain incubating. No separate renderer/controller or new component.

## Dependencies

- [ADV-SS-HANDFLOW-010](ADV-SS-HANDFLOW-010.md)
- [ADV-SS-GESTURE-002](ADV-SS-GESTURE-002.md)

Plan dependencies order work, not runtime admission. Consume only matching,
independently validated layer/tool/code identities. Real fitting additionally
requires live G0 and accepted real lower layers; source uncertainty and locked
test isolation are not repaired by this synthetic phase.

## Planned Implementation Tasks

- [x] branch: implementation on `advance/ss-curriculum-010`; prior complete-and-merge authorization retained, but no merge while required measurements fail.
- [x] tidy: reused the existing controller/compiler/renderer unchanged; no separate preparatory refactor was necessary.
- [x] test: `785af31`, `dbe04ca` and `2c2fd27` precede their implementations and record observed red failures. Twelve new tests pass.
- [x] Before target access/search, rerun the HANDFLOW-010 baseline revalidator with current compiler/tool/controller identities. Verify historical provenance separately; stale code-bound passes or failed original-baseline metrics cannot authorize this fit.
- [x] Freeze independent return target specifications, nontrivial initializations, train/development/held-out scales and attachment pairings, metrics and at most three ablations before any optimization. Targets must not be exported by the candidate grammar or selected from its exact finite grid.
- [x] Fit only the two permitted shared return geometries; keep old six primitive parameters, ports as contracted, tool, controller, action profiles and supplied scaffolds fixed. No action fitting, per-letter residuals, context changes or silent extra families.
- [x] Execute seeds 7/19/41 within the common render/time cap. Development alone selects; report initial quality and fixed/null controls without degrading a baseline just to manufacture improvement. Hold out actual attachment combinations, not only resized copies.
- [x] Save candidate checkpoints and enlarged initial/independent-target/learned-nominal/sampled/actual sheets, direction/port overlays, unchanged-old-primitive proofs and all failures. Persist actual render/time/revision and selection ledgers. Compound sheets retain their diagnosed crop rather than concealing it.
- [ ] Hand frozen candidates to HANDVALIDATE-015; do not self-certify new S1 acceptance or start gesture fitting. If admitted-input training cannot run, leave this learning Advance in progress with the experiment unchecked.
- [x] evidence: record commands, identities, actual budgets, sample paths and incomplete outcome; keep the failed gate and unready independent handoff unchecked.

## Validation Gates

- [ ] Required new families each show held-out loss ratio < 0.75 relative to the frozen nontrivial initial model for every required seed; absent/failed families cannot be averaged away.
- [x] Actual contact/corridor/ownership and frozen execution/refinement bounds are reported per family; independent evaluation still decides acceptance. Image checks inherit the documented crop and do not certify the omitted region.
- [x] An executed bounded learning experiment, immutable candidates and unseen-attachment evidence exist. Required compound evidence fails, so this does not complete the learning Advance.

## Budget and Stop Rules

Use [Addendum B Section 7](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#7-budgets-and-stop-rules):
seeds 7/19/41; at most three ablations; 5000 total renders or 1800 seconds per ablation/seed per attempt; one diagnosed revision, all setup and direct/sampled/actual/presentation work charged.
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
Review estimate is 40 minutes, not measured review or approval.

## Evidence

- [x] Frozen inputs, independent targets/controls, criteria and scope-specific identities.
- [x] Actual work/budget ledger, equal-scale samples, failures and executable replay commands.
- [x] Focused red/green regression tests and clean-checkout replay when code changes.
- [x] `arrive plan check`, changed local-link checks and `git diff --check`.
- [x] Strict PR check executed and installed ID-parser limitation disclosed; no merge or provider CI claimed. Rerun required checks before any later authorized merge.
- [x] Scope-qualified incomplete result; no unperformed learning, independent acceptance or human review counted as complete.

## Bug Fixes

`e74d85d` fixes construction of strict boundary handles without weakening the
validator: reject out-of-range requested lengths, then move only a numerically
unrepresentable boundary length inward by at most sixteen floating-point steps.
The second discovered defect is the compound comparison frame; its repair is
proposed, not implemented or authorized by the exhausted automatic revision.

## Changes Made

### 2026-09-07 — e74d85d: Fitted candidates, reproduced measurement failure

- Run-002 revalidates all 239 motion gates and the original baseline before target access, then executes all seeds. Both return families fit; all old-six/tool/port/scaffold parameters remain unchanged.
- Selected handles are lower 0.23/0.37 and upper 0.30/0.31 for every seed. Four valid held-out fixtures have full-image ratios 0.232461–0.409520; corresponding family-local checks pass. Seed order does not affect exhaustive development selection.
- The compound's lower-return endpoint is y=13.15 mm, outside the frozen y=13 mm frame edge. Its local before/after loss is zero and the required ratio is undefined. Each seed correctly fails; the improving compound average cannot hide the missing measurement.
- Run-002 spends 2134/1831/1831 renders and 208.406950/193.208989/193.558916 seconds, including 303 baseline renders charged to seed 7. There are 5046 optimization evaluations. Run-001 remains unchanged; the single automatic revision is used.
- Clean hash-seed-839 replay matches all 111 non-wall-clock artifacts byte-for-byte, including failures. Expanded local and clean suites each have 150 passes and one pre-existing constructor failure; twelve new tests pass. Plan validates, ten existing doctor issues remain, rules are not stale, and strict PR-ID parsing remains an installed-tool limitation.
- [Results and samples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitives/README.md), [ledger](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitives/ledger.json), [verification](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitives/verification.json).
- [Proposed no-refit full-frame measurement](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitives/measurement-request.md) requires additional user approval. No new candidate selection or threshold change is proposed. This Advance remains in progress and unmerged; HANDVALIDATE-015 remains planned.

### 2026-09-07 — 53e2f46: First admitted attempt stopped on numeric representation

- Fresh baseline passed all 239 gates. Run-001 then stopped after 842 optimization evaluations and 1158 total renders (107.382996 s), before held-out access, because a valid boundary handle projected slightly outside its strict range through floating-point arithmetic.
- Preserved run-001; `2c2fd27` reproduces the boundary fault and verifies subdivision ownership. Spec-v2 freezes the single allowed diagnosed revision: reject out-of-range requested values and construct boundary cubics using bounded inward representable steps. No target/grid/gate or old-primitive change.
- The learning experiment remains incomplete until all three seeds and required unseen-attachment proofs execute successfully. No merge or independent acceptance is claimed.

### 2026-09-06 — plan: Prioritize reliable learned stroke foundations

- Added the bounded work to Pass 15 `td018-foundation-repair`.
- Implementation and acceptance remain pending under Addendum B.

## Check for Understanding

1. Which exact evidence and identities permit this Advance's experiment to run?
2. What visible learned or independently evaluated result distinguishes completion from scaffolding?
3. Why does the cropped compound family invalidate an improving aggregate, and why should the next step remeasure frozen candidates rather than refit them?
