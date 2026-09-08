---
advance:
  id: "ADV-SS-CURRICULUM-013"
  title: "Foundation Geometry Accuracy — Bounded Finer Shared Scales"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum", "gesture", "handvalidate", "tests"]
  started_at: "2026-09-08T10:13:26Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
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

Test a bounded finer shared-scale grid before deciding whether return-handle
repair is necessary. User authorized this experiment on 2026-09-08, retaining
targets and thresholds. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).

## Behavioral Change

An isolated opt-in experiment learns three shared scales on immutable admitted
primitive curves. Worst-construction train/development ranking replaces a
mean-only objective for this new protocol, not for any historical run. The
absolute 0.05 quality limit and all existing physical gates remain unchanged.
No replacement receives independent acceptance through this learning Advance.

## Component Impact

New `scribesim/curriculum/finer_scales.py`, focused tests and `foundation_repair/finer_scales/`
evidence; existing components remain incubating. No controller, renderer, primitive,
old protocol or target-generator edits. Tidy assessment: no refactor needed.

## Planned Implementation Tasks

- [x] branch: `advance/ss-curriculum-013-finer-scales`, under standing update/merge authorization.
- [x] tidy: assessed; preserve pinned modules rather than refactor.
- [x] test: observe and commit failing tests before implementation.
- [x] feat/fix: bounded selector, strict shared lineage, admission and immutable journaled execution.
- [ ] Freeze code/spec before any target render; execute seeds 7/19/41 and separate-process replays within 5000 renders/1800 seconds per seed.
- [ ] Evaluate 21 fixtures, three contexts, closed counter, four refinements and nine adversarial controls; preserve negative evidence and stop conditions.
- [ ] Publish native examples, selected bytes, provenance and a conditional handle-repair decision.
- [ ] Validate, update this Advance and plan, then merge locally; do not claim provider CI or human review.

## Bug Fixes

None yet. This is new learning scope, not a repair to historical evidence.

## Risk + Rollback

Fine scaling may leave irreducible primitive-shape error or regress an accepted
underturn. Do not transfer old acceptance to changed bytes or compensate with
pen actions. Preserve all attempts. Roll back only the new opt-in experiment;
old reports, candidates and defaults remain unchanged. Handle repair is a
separately frozen conditional primitive-layer experiment, not an inline retry.

## Evidence

- [x] tdd:red-green
- [x] tests:unit
- [ ] Bounded first/replay receipts, candidate identities, local metrics and native examples.
- [ ] Unchanged targets, thresholds and source acceptance identities.

## CI Evidence Notes

Run local focused checks, `arrive plan check` and `arrive pr check --strict --json`
before merge. Record provider CI and human review only if actually supplied.

## Changes Made

### 2026-09-08 — docs/test: freeze bounded scale-only scope

Preserve the preceding analytical investigation and create a 343-proposal grid
at offsets -0.03 through +0.03, step 0.01, around the frozen three scales.
Nine previously inspected independent fixtures are regression-only; six fresh
fixtures are withheld until selection. No automatic revision allowance.

### 2026-09-08 — feat: isolated finer-scale experiment

`05368a2` records the observed missing-module failure before implementation.
All 16 focused tests now pass. Live source reconstruction verifies matching
foundation admission and the complete prior underturn-only scoped-null report.
The new module reuses unchanged physical measurement, controls and journaled
budgets; current targets and criteria are checked before any scoring.

## Check for Understanding

1. Why does a relative learning pass not imply absolute target accuracy?
2. Which three parameters may change, and why must offsets be derived?
3. Why are inspected independent fixtures now regressions rather than new holdouts?
4. What evidence triggers primitive-layer investigation instead of pen-action fitting?
