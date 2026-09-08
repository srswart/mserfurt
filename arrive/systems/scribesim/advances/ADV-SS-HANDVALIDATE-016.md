---
advance:
  id: "ADV-SS-HANDVALIDATE-016"
  title: "Foundation Readiness — Independent Gesture Transfer and Next-Stage Eligibility"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","curriculum","gesture","handflow","pathguide","tests"]
  started_at: "2026-09-06T16:02:10Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api","migration"]
  evidence: []
  model_usage: []
  status: in_progress
---

## Objective

Decide whether stable execution and a genuinely learned return vocabulary now justify a new bounded action/null-validation experiment, without granting premature letter or real-hand readiness.

**Work kind:** Independent evaluation and admission integration. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Implementation started 2026-09-08. No preparatory refactor is required: the independent evaluator is a new module and historical pinned helpers remain unchanged. Provider CI and human review are not claimed.

## Behavioral Change

The deliverable and acceptance boundary are specified in the tasks and gates below.
This record belongs to `td018-foundation-repair`; existing completed records and
failed evidence remain unchanged.

## Component Impact

- `scribesim/handvalidate/foundation_gestures.py (planned independent evaluator)`
- `scribesim/curriculum/pen_actions.py and scribesim/handvalidate/pen_actions.py (explicit foundation-manifest admission only)`
- `tests/test_handvalidate_foundation_gestures.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/evaluation/ (planned immutable evidence)`

Existing components remain incubating. No separate renderer/controller or new component.

## Dependencies

- [ADV-SS-CURRICULUM-011](ADV-SS-CURRICULUM-011.md)
- [ADV-SS-HANDVALIDATE-015](ADV-SS-HANDVALIDATE-015.md)
- [ADV-SS-HANDVALIDATE-014](ADV-SS-HANDVALIDATE-014.md)

Plan dependencies order work, not runtime admission. Consume only matching,
independently validated layer/tool/code identities. Real fitting additionally
requires live G0 and accepted real lower layers; source uncertainty and locked
test isolation are not repaired by this synthetic phase.

### Available frozen learning input (2026-09-07)

CURRICULUM-011 run-003 completes the approved no-refit seed-7 measurement and
unchanged seed-19/41 search. Freeze its report SHA
`7dbec24cd0bf82e9f45d55c5417cf2c36551ee7dfe6294bd7b0c409219066911` and use
`shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/gestures/run-003/seed-{7,19,41}/attachment/first/candidate.json`.
All primary files have SHA `d8b26fba2655b0bba961865fb74b543829cb1b11ac850afd672dd02ba0822e5a`.
The repaired diagnostics retain explicit inter-gesture lifts; run-002's paired
image evidence remains invalid. Reconstruct matching primitive admission and
independent gesture proofs instead of copying the learning report's pass label.
This input note does not start or complete HANDVALIDATE-016.

## Planned Implementation Tasks

- [ ] branch: confirm implementation/commit/merge authorization and preserve unrelated work.
- [ ] tidy: assess narrow preparation; commit any required behavior-preserving refactor separately.
- [ ] test: commit failing behavioral tests before implementation when commits are authorized; planning-only edits do not claim TDD execution.
- [ ] Freeze final acceptance before proofs; reconstruct current baseline, primitive gate, gesture candidates, tool/controller/compiler, target/split and metric identities. Recompute per-seed held-out and actual metrics without calling an optimizer.
- [ ] Replay continuous/repartitioned gestures, independent held-out attachments, lifted pairs, overlap and spaces with dt/arc refinement. Measure every required contact entry/exit rather than relying on image or corridor averages.
- [ ] Detect wrong ports/directions, detached per-letter copies, undeclared lifts/air, overbuilt contributors and erased counters using predeclared independent controls. Retain old global failures and report unresolved scope.
- [ ] Implement an explicit new foundation-manifest input that verifies current evidence instead of editing old pinned reports or copying a pass label. Preserve historical replay; changed model/tool/controller/split/code identities require reevaluation.
- [ ] Publish one layered sample index and disposition for motion, old primitives, new returns, shared gestures, missing inventory, action/null experiment eligibility, S1-action and real G0/G1/G2. Do not label a constant fixed tool as an accepted null action without its separate evidence.
- [ ] Issue STOP/REVISE or eligibility to scope the next bounded experiment. Do not run action/letter fitting here; register new follow-up records/evidence for the previous phase's unexecuted selected-action work. Keep CURRICULUM-005 blocked until matching S1-action and its other runtime prerequisites pass.
- [ ] evidence: record commands, identities, actual budgets, sample paths and outcome before completion; keep unexecuted tasks unchecked.

## Validation Gates

- [ ] Required motion, primitive and gesture scopes pass independently for all required seeds, including held-out topology and exact contact/ownership; failed or absent evidence blocks that scope.
- [ ] Fresh-process results and current manifests agree; status edits, stale hashes, missing provenance or unsupported inventory cannot authorize training.
- [ ] The phase exits with learned visible foundation evidence or an explicit failure—not more scaffolding counted as learning. Foundation acceptance is not S1-action, learned letters, real appearance approval or a default switch.

## Budget and Stop Rules

Use [Addendum B Section 7](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#7-budgets-and-stop-rules):
5000 renders or 1800 seconds per seed including first/replay/control/refinement work; zero optimization; at most one diagnosed rerun.
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
