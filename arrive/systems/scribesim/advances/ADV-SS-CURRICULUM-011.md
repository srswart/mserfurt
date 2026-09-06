---
advance:
  id: "ADV-SS-CURRICULUM-011"
  title: "Foundation Gesture Learning — Underturn, Overturn and Compound Transfer"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","evo","handflow","handvalidate","tests"]
  started_at: "2026-09-06T16:02:10Z"
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

Actually learn reusable fixed-tool continuous return constructions, then demonstrate unseen combinations without fitting letters or copying independent curves.

**Work kind:** Learning implementation and bounded experiment. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Timestamp records drafting only; implementation, experiments, CI and review are not claimed.

## Behavioral Change

The deliverable and acceptance boundary are specified in the tasks and gates below.
This record belongs to `td018-foundation-repair`; existing completed records and
failed evidence remain unchanged.

## Component Impact

- `scribesim/curriculum/foundation_gestures.py (planned bounded gesture fitting)`
- `tests/test_foundation_gestures.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/gestures/ (planned immutable evidence)`

Existing components remain incubating. No separate renderer/controller or new component.

## Dependencies

- [ADV-SS-HANDVALIDATE-015](ADV-SS-HANDVALIDATE-015.md)
- [ADV-SS-GESTURE-002](ADV-SS-GESTURE-002.md)

Plan dependencies order work, not runtime admission. Consume only matching,
independently validated layer/tool/code identities. Real fitting additionally
requires live G0 and accepted real lower layers; source uncertainty and locked
test isolation are not repaired by this synthetic phase.

## Planned Implementation Tasks

- [ ] branch: confirm implementation/commit/merge authorization and preserve unrelated work.
- [ ] tidy: assess narrow preparation; commit any required behavior-preserving refactor separately.
- [ ] test: commit failing behavioral tests before implementation when commits are authorized; planning-only edits do not claim TDD execution.
- [ ] Require a live matching HANDVALIDATE-015 primitive pass, repaired execution and the audited grammar. Freeze every primitive curve and fixed action/tool parameter before gesture optimization.
- [ ] Predeclare required underturn, overturn and compound constructions with independent synthetic targets and train/development/held-out topology or attachment pairings. Do not treat the old supplied i/u recipes as learned letters.
- [ ] Fit only shared gesture reference choices and audited attachment/placement transforms. No primitive refitting, per-letter residuals, profile activation, hidden finishing pass, context learning or expanded-cap bypass.
- [ ] Run seeds 7/19/41 and at most three ablations within fixed budgets. Include fixed and placement-only controls; development selects before held-out scoring. A representable exact-grid target or scale-only transfer is insufficient evidence.
- [ ] Publish enlarged equal-scale initial/target/fitted/sampled/actual sheets and constituent/direction/port overlays for isolated gestures, lifted pairs and withheld attachments. Make failures visible and show multiple instances sharing the same learned parameters.
- [ ] Freeze selected candidates for HANDVALIDATE-016. Remain in progress if only tooling or blocked admission is delivered; do not finish this learning Advance without its actual bounded experiment.
- [ ] evidence: record commands, identities, actual budgets, sample paths and outcome before completion; keep unexecuted tasks unchecked.

## Validation Gates

- [ ] Every required construction and seed achieves frozen held-out benefit with shared lower-layer identities unchanged; topology-disjoint transfer is present.
- [ ] Actual execution preserves continuous contact within a gesture, explicit lifted separation and exact overlap owners; stable endpoint/refinement checks remain mandatory.
- [ ] No learned alphabet, historical hand or S1-action claim is inferred. Missing required gesture coverage blocks the corresponding inventory and final acceptance.

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

### 2026-09-06 — plan: Prioritize reliable learned stroke foundations

- Added the bounded work to Pass 15 `td018-foundation-repair`.
- Implementation and acceptance remain pending under Addendum B.

## Check for Understanding

1. Which exact evidence and identities permit this Advance's experiment to run?
2. What visible learned or independently evaluated result distinguishes completion from scaffolding?

