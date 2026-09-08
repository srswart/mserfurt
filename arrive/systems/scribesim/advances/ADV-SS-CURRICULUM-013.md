---
advance:
  id: "ADV-SS-CURRICULUM-013"
  title: "Foundation Geometry Accuracy — Bounded Finer Shared Scales"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum", "gesture", "handvalidate", "tests"]
  started_at: "2026-09-08T10:13:26Z"
  implementation_completed_at: "2026-09-08T10:37:13Z"
  review_time_estimate_minutes: 45
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 110
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "local:bounded-scale-experiment", "local:fresh-process-replay"]
  model_usage: []
  status: complete
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
- [x] Freeze code/spec before any target render; execute seeds 7/19/41 and separate-process replays within 5000 renders/1800 seconds per seed.
- [x] Evaluate 21 fixtures, three contexts, closed counter, four refinements and nine adversarial controls; preserve negative evidence and stop conditions.
- [x] Publish native examples, selected bytes, provenance and a conditional handle-repair decision.
- [ ] Validate, update this Advance and plan, then merge locally; do not claim provider CI or human review.

## Bug Fixes

No runtime defects or retries. This is new learning scope, not a repair to
historical evidence. The old grid's resolution limitation is addressed only by
the newly frozen uniform neighborhood; no old grid or target is edited.

## Risk + Rollback

Fine scaling may leave irreducible primitive-shape error or regress an accepted
underturn. Do not transfer old acceptance to changed bytes or compensate with
pen actions. Preserve all attempts. Roll back only the new opt-in experiment;
old reports, candidates and defaults remain unchanged. Handle repair is a
separately frozen conditional primitive-layer experiment, not an inline retry.

Reviewability checkpoint: `arrive score --base 4fe4cf7 --json` reports red 110
after staging (93 before completion metadata), dominated by the 998 generated
manifest artifacts, with a mechanical 577.8-minute estimate. Retain this
inseparable evidence rather than omit failures, workers or
replay. Review the small isolated code change separately from generated evidence:
tests, implementation and evidence have separate commits. Independent acceptance
is split into HANDVALIDATE-018; handle work is omitted because it is unnecessary.
The 45-minute human review estimate is not a record of review performed.

## Evidence

- [x] tdd:red-green
- [x] tests:unit
- [x] Bounded first/replay receipts, candidate identities, local metrics and native examples.
- [x] Unchanged targets, thresholds and source acceptance identities.

[Results and native samples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/finer_scales/README.md),
[complete experiment](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/finer_scales/run-001/report.json),
and [verification receipt](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/finer_scales/verification.json).

## CI Evidence Notes

Run local focused checks, `arrive plan check` and `arrive pr check --strict --json`
before merge. Record provider CI and human review only if actually supplied.
The strict parser again returns `ids=[]` despite the explicit Advance ID in all
three metadata fields. Ten inherited artifact-doctor issues remain. Plan/rule
checks pass; no provider CI or human review is claimed.

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

### 2026-09-08 — complete: scale-only accuracy pass

- Execution `dff8a31`: all seeds choose `[0.83,1.17,0.87]`; local actual/target
  maxima are underturn 0.019606, overturn 0.019777 and compound 0.020162, all
  below unchanged 0.05. All global quality, mechanical, context, counter and
  nine-control checks pass. **No shared return-handle repair is necessary here.**
- 8484 renders, 2828 per seed including replay; 2112 train/development scoring
  calls. Maximum cumulative seed time 437.912 seconds, within 1800. Zero retries.
  Every seed matches 165 non-clock artifacts exactly; all 998 manifest artifacts
  and current code identities verify after execution.
- All primitive, action and recipe dictionaries remain unchanged. Source
  admission reconstructs after the run; changed candidate file SHA is
  `6ff3e478799ab1a63d970d1e99fd5d5c454c12557047e5506fec911a65baf4ba`.
- 89 focused tests pass; all 16 new tests pass in a clean committed checkout.
  Broader selection: 329 pass and 18 inherited failures. The same 18 reproduce
  on pre-change `4fe4cf7` (17 other tests pass in that baseline subset).
- Native examples and the browsable foundation index are updated. Register
  HANDVALIDATE-018 as planned independent no-refit evaluation and align the
  future letter dependency. No S1-action, letter, word, fatigue or real promotion.

## Check for Understanding

1. Why does a relative learning pass not imply absolute target accuracy?
2. Which three parameters may change, and why must offsets be derived?
3. Why are inspected independent fixtures now regressions rather than new holdouts?
4. What evidence triggers primitive-layer investigation instead of pen-action fitting?
