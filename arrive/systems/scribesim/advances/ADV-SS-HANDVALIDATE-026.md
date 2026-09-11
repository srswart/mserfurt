---
advance:
  id: "ADV-SS-HANDVALIDATE-026"
  title: "Stroke Context — Owner Usefulness and Frozen-Rule Transfer Review"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","curriculum","gesture","tests"]
  started_at: "2026-09-10T03:54:13.857346+00:00"
  implementation_completed_at: ~
  review_time_estimate_minutes: 55
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Determine whether physically valid neighbor-aware forms/transitions are intelligible and useful to the owner, and assess only explicitly authorized, provenance-frozen transfer without turning reviewed examples into unseen evidence.

Follows [TD-018 Addendum D](../../../../docs/tech-direction/TD-018-addendum-d-stroke-context-transitions.md).
Planning only: no implementation, training, physical execution, CI or acceptance
is claimed by creation of this advance. Existing components suffice.

## Behavioral Change

Owner judgments distinguish meaningful adaptation, no useful difference, reduced readability and preference for separate lettering. Any transfer claim consumes a frozen rule set and independently validated held-out scope; completion does not imply learned or historical-hand acceptance.

## Component Impact

- `scripts/stroke_context_review.py (planned)`
- `tests/test_stroke_context_review.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/review/ (planned)`

Keep new adapters opt-in and outside frozen core identity scans. Exact paths and
any required migration must be frozen before implementation, not inferred as
permission to change canonical sources or add identity-scanned spec files.

## Dependencies

- [ADV-SS-HANDVALIDATE-025](ADV-SS-HANDVALIDATE-025.md)

Owner scope/protocol approvals in Addendum D are independent gates, not implied
by a dependency's implementation status. C006's full completion is not a
prerequisite for consuming its specifically pinned P2 mechanical evidence.

## Planned Implementation Tasks

- [ ] workflow: preserve all existing uncommitted work; no branches, commits or merges without explicit later authorization.
- [ ] tidy: assess narrowly required preparation; do not refactor frozen sources or unrelated components.
- [ ] Require the independent mechanical report, exact actual examples and source/frame/metric identities; prepare full-frame review using saved evidence where available.
- [ ] Present normal-scale and synchronized diagnostic views with honest labels; collect observations about entry/body/exit and transition intent rather than force a total ranking of near-identical images.
- [ ] Bind actual owner review/abstention to exact examples; distinguish mechanical pass, visible effect, usefulness and broad admission. The old paused grid supplies no automatic labels.
- [ ] Freeze rule/parameter tables and development decisions before opening any reserved evaluation material; verify split provenance was declared before hypothesis selection.
- [ ] Reconcile existing C006 sealed reservations and prohibit training/design use; authorize exact transfer inventory and cumulative budget separately before generating or inspecting new held-out physical evidence.
- [ ] Evaluate composition-disjoint reuse with identity, spacing and matched-advance controls; no development retuning, per-word exceptions or post-failure threshold changes.
- [ ] Retain negative/no-effect/unsupported outcomes and state the precise checkpoint scope; recommend a separate later proposal for correlated variability only if contextual mechanics and usefulness warrant it.
- [ ] Keep C006 and downstream word-context completion conditional on explicit owner/checkpoint decisions; no S2/real/context-training or fitting permission follows automatically.

## Bug Fixes

- [ ] No code fix is implemented by this planning advance; preserve earlier fixed clock/contact/measurement behavior and failed artifacts.

## Risk + Rollback

- Risk: Visually obvious changes or previously exposed strings could be mistaken for useful, generalizable handwriting.
- Rollback: Retain the simpler validated baseline and report no useful adaptation if warranted. Preserve sealed reservations, unfavorable owner feedback and all failed transfer evidence without further tuning.
- Keep fixed tool/action, no-fatigue and no-fitting constraints. Proposed new
  geometry, frames or criteria require prospective approval; no phase-level
  reset of the old time/render debit is permitted.

## Evidence

- [ ] Actual owner judgments are collected or explicitly pending, never invented from image differences.
- [ ] Any transfer verdict has frozen split/rules, full independent evidence and authorized resources; otherwise transfer remains pending.
- [ ] Clear outcome and scope-qualified handoff precede word-context or later variability proposals.
- [ ] Record test-first evidence where code changes, exact commands, source/report
  pins and local results; do not fabricate tidy/test/physical success during planning.
- [ ] Run plan, generated-rule, local-link and whitespace checks for the final scope.

## CI Evidence Notes

Local checks are not provider CI. Before any separately authorized merge, run
`arrive pr check --strict --json` and record provider/tool limitations honestly.
No branch, commit or merge is part of the current planning authorization.

## Changes Made

### 2026-09-10 — planned from the owner-approved stroke-context direction

- Defined a bounded deliverable and stop gates; implementation and evaluation
  remain unstarted. See Addendum D for retained baseline pins and budget limits.

