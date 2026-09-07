---
advance:
  id: "ADV-SS-HANDVALIDATE-015"
  title: "Foundation Primitive Acceptance — Independent Current-Code S1 Extension"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","curriculum","gesture","handflow","tests"]
  started_at: "2026-09-07T13:05:58Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  model_usage: []
  status: in_progress
---

## Objective

Independently accept or reject the repaired baseline and newly learned return primitives before continuous gesture fitting.

**Work kind:** Independent evaluation. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Implementation is underway under the user's implement/update/merge workflow.
Independent proofs and controls must execute before any acceptance decision.

## Behavioral Change

The deliverable and acceptance boundary are specified in the tasks and gates below.
This record belongs to `td018-foundation-repair`; existing completed records and
failed evidence remain unchanged.

## Component Impact

- `scribesim/handvalidate/foundation_primitives.py (planned evaluator)`
- `tests/test_handvalidate_foundation_primitives.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitive_evaluation/ (planned immutable evidence)`

Existing components remain incubating. No separate renderer/controller or new component.

## Dependencies

- [ADV-SS-CURRICULUM-010](ADV-SS-CURRICULUM-010.md)

Plan dependencies order work, not runtime admission. Consume only matching,
independently validated layer/tool/code identities. Real fitting additionally
requires live G0 and accepted real lower layers; source uncertainty and locked
test isolation are not repaired by this synthetic phase.

## Planned Implementation Tasks

- [ ] branch: confirm implementation/commit/merge authorization and preserve unrelated work.
- [ ] tidy: assess narrow preparation; commit any required behavior-preserving refactor separately.
- [ ] test: commit failing behavioral tests before implementation when commits are authorized; planning-only edits do not claim TDD execution.
- [ ] Freeze evaluation criteria and reconstruct artifact, model, primitive, tool, controller, compiler, target/split and metric identities. Reject hand-edited statuses or stale baseline admission before candidate proofs.
- [ ] Replay all three selected seeds in fresh processes without optimizer calls. Recompute original-baseline preservation, new-family held-out benefit and realized contact/corridor/refinement metrics from frozen candidates.
- [ ] Run independently predeclared wrong-port/direction, detached geometry, hidden connector/lift, extra contributor and erased-counter controls. Preserve original global sensitivity failures and use exact ownership/local blank regions, not one aggregate score.
- [ ] Check composition-disjoint attachment transfer, shared-parameter propagation and matched direct/sampled/actual scale. Report learned versus hypothetical inventory and synthetic versus real evidence separately.
- [ ] Issue a scoped current-code primitive S1 extension decision naming required lower/upper returns, old baseline identity and missing inventory. Reject undefined mandatory ports/counters; no dynamic-action or letter approval.
- [ ] Publish the sample index, budgets, full replay identities and stop/revise/proceed. A blocked evaluation can finish honestly, but cannot mark an unexecuted learning experiment complete.
- [ ] evidence: record commands, identities, actual budgets, sample paths and outcome before completion; keep unexecuted tasks unchecked.

## Validation Gates

- [ ] Every required family and seed meets the predeclared learning, contact, refinement and negative-control criteria; no aggregate pass masks a failed family.
- [ ] Fresh-process replay matches identities and semantic results; fabricated, stale, unsupported or detached checkpoints fail closed.
- [ ] CURRICULUM-011 receives runtime permission only from a matching pass for its required primitive inventory. Real G0/real-layer acceptance remains separate and blocked unless genuinely established.

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
Review estimate is 35 minutes, not measured review or approval.

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
