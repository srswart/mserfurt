---
advance:
  id: "ADV-SS-GESTURE-003"
  title: "Upright Construction — Explicit Pen-down Gesture Connections"
  system: "scribesim"
  primary_component: "gesture"
  components: ["gesture", "pathguide", "handflow", "handvalidate", "tests"]
  started_at: "2026-09-08T18:57:52Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
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

Remove the representational blocker to pen-down upward movements, following
[TD-018 Addendum B section 13](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#13-upright-pen-down-construction-repair).
Depends on HANDVALIDATE-020's owner feedback, not its appearance acceptance.

## Behavioral Change

A new opt-in contract permits explicit smooth/corner inter-gesture connections
without changing legacy lift semantics. Contact-run identity is separate from
gesture/action ownership. Intentional reversals retain contact and corner-aware
timing. Unsupported gaps, smooth reversals and undeclared overlaps fail closed.
Fixed tool/actions and existing primitive/gesture/expanded-reference caps remain.

## Component Impact

- `gesture`: versioned schema, connection validation and source lineage.
- `pathguide` / `handflow`: connected-boundary sampling and actual contact timing.
- `handvalidate` / `tests`: contact-run, overlap-owner and legacy regression proofs.
- Existing components suffice; no new component or default activation is required.

## Planned Implementation Tasks

- [ ] branch: create `advance/ss-gesture-003` from the verified integration branch.
- [ ] tidy: inspect boundaries; separate any necessary no-behavior refactor.
- [ ] test: commit failing tests before changing the compiler or executor.
- [ ] feat/fix: add an explicit new version and reject implicit legacy migration.
- [ ] feat/fix: preserve primitive/gesture/action ownership within one contact run.
- [ ] evaluate: test coincident smooth joins, corner reversals and genuine lifts.
- [ ] evaluate: reject gap, tangent, overlap-owner, cap and false-contact controls.
- [ ] evidence: preserve legacy outputs and source snapshots; audit identity invalidation.
- [ ] merge: update this Advance and plan after checks; do not grant geometry admission.

## Bug Fixes

- [ ] `_lower` currently mandates a lift after the first gesture; contact cannot be repaired by changing sample labels.
- [ ] Audit all gesture-boundary consumers for an implicit lift or action/contact reset.
- [ ] Define retracing/finite-width overlap ownership beyond proper centerline crossings.

## Risk + Rollback

Schema/identity changes can invalidate old live admission. Preserve historical
bytes and source snapshots; never rewrite pinned receipts to hide this. Constant
actions do not excuse lost action ownership. Disable the new opt-in version to
roll back; keep old validators and reject unsupported conversion. No cap increase,
target change, fitting, S2, context or fatigue follows from contract completion.

## Evidence

- [ ] tidy:preparatory, if required; otherwise explain why isolation needs none.
- [ ] tdd:red-green with separate test and implementation commits.
- [ ] tests:unit and tests:integration for nominal and actual contact boundaries.
- [ ] Legacy byte/output compatibility and fail-closed source-identity checks.

## CI Evidence Notes

Before merge run local tests, plan/rules/whitespace checks and
`arrive pr check --strict --json`. Record provider/run metadata only when present;
local checks are not provider CI. Recalculate reviewability for the actual diff
and split implementation if required. Planning estimates are not measured review.

## Changes Made

### 2026-09-08 - plan: register the contact-contract prerequisite

Source inspection confirms mandatory inter-gesture lifts and immutable old
foundation geometry. The owner explicitly requires pen-down upstrokes. This
record scopes implementation; no compiler, candidate or evidence was changed.
Planning checks pass for the plan, generated rules and whitespace. The installed
strict PR metadata parser returns `ids=[]` despite explicit Advance IDs in the
title and labels; no provider CI or implementation test pass is claimed.

## Check for Understanding

1. Why is contact-run identity distinct from gesture ownership?
2. Why must a pen-down reversal use corner timing rather than a smooth join?
3. Why does changing a compiler hash invalidate admission rather than update an old receipt?
