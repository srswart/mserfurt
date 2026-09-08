---
advance:
  id: "ADV-SS-CURRICULUM-012"
  title: "Foundation Action or Null — Bounded Experiment on Accepted Shared Gestures"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","handflow","pathguide","nibcontact","handvalidate","tests"]
  started_at: "2026-09-08T03:50:00Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api","migration"]
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Scope and execute the previously unexecuted selected-action/null experiment only after matching independent foundation admission. Prefer an explicit fixed-tool null hypothesis for the three accepted constructions unless a named local defect justifies one bounded physical pen action.

Drafting only. This record registers gated follow-up work, not execution or approval.
Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).

## Behavioral Change

Matching foundation admission, complete scoped candidate evidence and deterministic replay are required. Missing action coverage stays unresolved. Real fitting additionally requires live G0 and accepted real lower layers.

## Component Impact

`scribesim/curriculum/foundation_actions.py` (planned), existing explicit foundation admission APIs, focused tests and `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/actions/` (planned).
Existing components remain incubating; no separate controller or renderer.

## Dependencies

- [ADV-SS-HANDVALIDATE-016](ADV-SS-HANDVALIDATE-016.md)
- [ADV-SS-CURRICULUM-004](ADV-SS-CURRICULUM-004.md)

## Planned Implementation Tasks

- [ ] branch: confirm implementation/update/merge authorization and preserve unrelated work.
- [ ] tidy: assess minimal behavior-preserving preparation separately.
- [ ] test: commit observed failing behavioral tests before implementation.
- [ ] Require a consumer-pinned HANDVALIDATE-016 report, live primitive/gesture/tool/controller identities and an explicit required inventory. A completed Advance or historical HANDVALIDATE-014 stop is not admission.
- [ ] Investigate and freeze the smallest useful action/null scope before any target access. Name the local failure if testing rotation, edge release or finishing; do not invent dynamic work when the fixed tool already satisfies the scoped construction.
- [ ] Freeze independent project-authored targets, train/development/held-out splits, controls, metrics and numerical limits. A null candidate needs affirmative scoped target/transfer/contact evidence, not merely a constant action dictionary or absence of selected proposals.
- [ ] Keep primitive curves and shared gesture attachments immutable. The foundation schema rejects dynamic tools: any necessary explicit versioned action extension must preserve old replay and pass physical bridge/ownership/refinement tests first. No bypass of the legacy or foundation grammar.
- [ ] For a justified action, fit only the predeclared bounded profile and select on development, never held-out pixels. Otherwise evaluate the predeclared null without optimization. Report active/null/unresolved separately for each required action and construction.
- [ ] Execute seeds 7, 19 and 41 with first/replay/control/refinement costs charged: at most 5000 renders or 1800 seconds per seed, one diagnosed revision. Preserve failed attempts and cumulative accounting; no open-ended search or threshold relaxation.
- [ ] Publish equal-scale native-resolution target/nominal/desired/actual examples, selected candidate bytes, source/compiled ownership and local counter/blank evidence. Complete actual work or record an explicit stop; scaffolding does not complete a learning task.
- [ ] Freeze selected candidate manifests for HANDVALIDATE-017. No S1-action, letters, words, fatigue, default switch or real-hand approval is granted here.

## Validation Gates

- [ ] Matching foundation admission, complete scoped candidate evidence and deterministic replay are required. Missing action coverage stays unresolved. Real fitting additionally requires live G0 and accepted real lower layers.
- [ ] Fresh-process results match current pinned source, target, compiler, tool, controller and metric identities.
- [ ] Missing or failed evidence blocks the affected scope; completion is not promotion.

## Bug Fixes

None implemented; future scoped work only.

## Risk + Rollback

A global image score can hide malformed contact, lost counters or copied geometry.
Use exact source/owner checks and frozen local guards. Revert only new opt-in behavior;
keep historical evidence, controllers and defaults unchanged. Review time is an estimate.

## Evidence

- [ ] tdd:red-green and actual focused/expanded test results.
- [ ] Frozen candidate/target/metric manifests, visible samples and cumulative budgets.
- [ ] Clean-checkout fresh-process replay and current strict admission reconstruction.
- [ ] `arrive plan check`, changed local-link checks and `git diff --check`.
- [ ] `arrive pr check --strict --json` before an authorized merge; report local parser limitations separately from provider CI.
- [ ] No unexecuted learning, owner review or provider CI counted as complete.

## Changes Made

### 2026-09-08 — plan: Register the previously unexecuted action/null work

- HANDVALIDATE-016 registers this explicit follow-up instead of promoting old blocked action evidence.
