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
  evidence: []
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

- `scribesim/curriculum/foundation_primitives.py (planned bounded fitting)`
- `scribesim/evofit/foundation_contract.py (contract consumption)`
- `tests/test_foundation_primitives.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitives/ (planned immutable evidence)`

Existing components remain incubating. No separate renderer/controller or new component.

## Dependencies

- [ADV-SS-HANDFLOW-010](ADV-SS-HANDFLOW-010.md)
- [ADV-SS-GESTURE-002](ADV-SS-GESTURE-002.md)

Plan dependencies order work, not runtime admission. Consume only matching,
independently validated layer/tool/code identities. Real fitting additionally
requires live G0 and accepted real lower layers; source uncertainty and locked
test isolation are not repaired by this synthetic phase.

## Planned Implementation Tasks

- [ ] branch: confirm implementation/commit/merge authorization and preserve unrelated work.
- [ ] tidy: assess narrow preparation; commit any required behavior-preserving refactor separately.
- [ ] test: commit failing behavioral tests before implementation when commits are authorized; planning-only edits do not claim TDD execution.
- [ ] Before target access/search, rerun the HANDFLOW-010 baseline revalidator with current compiler/tool/controller identities. Verify historical provenance separately; stale code-bound passes or failed original-baseline metrics cannot authorize this fit.
- [ ] Freeze independent return target specifications, nontrivial initializations, train/development/held-out scales and attachment pairings, metrics and at most three ablations before any optimization. Targets must not be exported by the candidate grammar or selected from its exact finite grid.
- [ ] Fit only the two permitted shared return geometries; keep old six primitive parameters, ports as contracted, tool, controller, action profiles and supplied scaffolds fixed. No action fitting, per-letter residuals, context changes or silent extra families.
- [ ] Execute seeds 7/19/41 within the common render/time cap. Development alone selects; report initial quality and fixed/null controls without degrading a baseline just to manufacture improvement. Hold out actual attachment combinations, not only resized copies.
- [ ] Save candidate checkpoints and enlarged initial/independent-target/learned-nominal/sampled/actual sheets, direction/port overlays, unchanged-old-primitive proofs and all failures. Persist actual render/time/revision and selection ledgers.
- [ ] Hand frozen candidates to HANDVALIDATE-015; do not self-certify new S1 acceptance or start gesture fitting. If admitted-input training cannot run, leave this learning Advance in progress with the experiment unchecked.
- [ ] evidence: record commands, identities, actual budgets, sample paths and outcome before completion; keep unexecuted tasks unchecked.

## Validation Gates

- [ ] Required new families each show held-out loss ratio < 0.75 relative to the frozen nontrivial initial model for every required seed; absent/failed families cannot be averaged away.
- [ ] Actual contact/corridor/ownership and frozen execution/refinement bounds are reported per family; independent evaluation still decides acceptance.
- [ ] An executed bounded learning experiment, immutable candidates and unseen-attachment evidence exist. A proposal generator, mock fitness test, zero-render admission attempt or practice playback alone is not completion.

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

- [ ] Frozen inputs, independent targets/controls, criteria and scope-specific identities.
- [ ] Actual work/budget ledger, equal-scale samples, failures and executable replay commands.
- [ ] Focused red/green regression tests and clean-checkout replay when code changes.
- [ ] `arrive plan check`, changed local-link checks and `git diff --check`.
- [ ] Before an authorized merge run `arrive pr check --strict --json`; report installed ID-parser limitations separately from provider CI.
- [ ] Scope-qualified result; no unperformed learning, candidate evaluation or human review counted as complete.

## Bug Fixes

None yet. The planned diagnosis/repair is not an implemented or validated fix.

## Changes Made

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
