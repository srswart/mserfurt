---
advance:
  id: "ADV-SS-HANDVALIDATE-025"
  title: "Stroke Context — Independent Physical Boundary Validation"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","gesture","handflow","pathguide","curriculum","tests"]
  started_at: "2026-09-10T03:54:13.857346+00:00"
  implementation_completed_at: ~
  review_time_estimate_minutes: 75
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

**Current gate:** CURRICULUM-016's H1–H3 progression is paused after owner
indistinguishable feedback. [Addendum E](../../../../docs/tech-direction/TD-018-addendum-e-boundary-construction.md)
proposes a new boundary-construction investigation, not a physical candidate.
Do not execute the old1152-run inventory for either the paused hypotheses or
any new construction. A useful reviewed demonstrator and a newly enumerated,
independently checked protocol/budget are required first.

Independently validate the frozen local-form/transition demonstrator in actual motion, including cross-letter contact/ownership, exact events and current-baseline preservation under an explicitly authorized resource budget.

Follows [TD-018 Addendum D](../../../../docs/tech-direction/TD-018-addendum-d-stroke-context-transitions.md).
Planning only: no implementation, training, physical execution, CI or acceptance
is claimed by creation of this advance. Existing components suffice.

## Behavioral Change

A separately pinned physical runner and read-only evidence consumer distinguish representation, desired-path validity and actual finite-nib motion. Failed contact, local geometry or timing gates cannot be overridden by aggregate image similarity.

## Component Impact

- `scripts/stroke_context_physical.py (planned)`
- `scripts/stroke_context_evidence.py (planned)`
- `tests/test_stroke_context_physical.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/physical/ (planned)`

Keep new adapters opt-in and outside frozen core identity scans. Exact paths and
any required migration must be frozen before implementation, not inferred as
permission to change canonical sources or add identity-scanned spec files.

## Dependencies

- [ADV-SS-CURRICULUM-016](ADV-SS-CURRICULUM-016.md)

Owner scope/protocol approvals in Addendum D are independent gates, not implied
by a dependency's implementation status. C006's full completion is not a
prerequisite for consuming its specifically pinned P2 mechanical evidence.

## Planned Implementation Tasks

- [ ] workflow: preserve all existing uncommitted work; no branches, commits or merges without explicit later authorization.
- [ ] tidy: assess narrowly required preparation; do not refactor frozen sources or unrelated components.
- [ ] Require owner-approved demonstrator, complete hypotheses/arms/fixtures/refinements/seeds/replay inventory and independently frozen criteria before preparing execution.
- [ ] Carry forward C006's failure/recovery debits; explicitly approve feasible cumulative or separate accounting, storage/time/render limits and zero automatic retries before physical work.
- [ ] Add negative tests for fake lifts, air mislabeled contact, false smooth reversals, missing retrace/connector ownership, undeclared body changes, swapped selectors, duplicate events, crop/DPI errors and forged identities.
- [ ] Prepare runner/reader/control/source pins without executing; block execution unless the owner separately authorizes the concrete prepared protocol.
- [ ] Use fixed tool/actions, unchanged existing numeric thresholds and exact null/regression outputs; obtain prospective approval for genuinely new transition-specific metrics instead of deriving limits from failures.
- [ ] Execute only the approved finite inventory, initially retaining seeds7/19/41 and fresh-process replay unless the owner explicitly approves another protocol; journal all failures, supervision, presentation and control costs.
- [ ] Reconstruct raw physical contact, global/local containment, baseline/x-height, ports, overlap contributors and clock/corner events independently from saved traces and pixels.
- [ ] Preserve original and failed evidence, verify source identities before/after, and produce a scoped mechanical verdict with owner appearance and fitting flags still false.

## Bug Fixes

- [ ] No code fix is implemented by this planning advance; preserve earlier fixed clock/contact/measurement behavior and failed artifacts.

## Risk + Rollback

- Risk: A connected image can conceal false contact, invalid reversals, excessive overlap or a resource-budget reset.
- Rollback: Stop at the first required gate failure, preserve every reservation/artifact and keep acceptance withheld. Any measurement repair or recovery requires a separately approved scope, not automatic refitting.
- Keep fixed tool/action, no-fatigue and no-fitting constraints. Proposed new
  geometry, frames or criteria require prospective approval; no phase-level
  reset of the old time/render debit is permitted.

## Evidence

- [ ] No physical execution starts before concrete protocol/resource approval; a new phase never resets a ledger.
- [ ] Every required complete frame, local/contact gate, adverse control and exact replay passes; incomplete evidence withholds clearance.
- [ ] Independent raw reconstruction and source/artifact integrity are reported separately from owner approval, CI and merge.
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
