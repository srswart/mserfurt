---
advance:
  id: "ADV-SS-HANDVALIDATE-019"
  title: "Standalone Stem — Independent Synthetic Fixed-Null Admission"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "curriculum", "tests"]
  started_at: "2026-09-08T16:54:02Z"
  implementation_completed_at: "2026-09-08T17:08:04Z"
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 110
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green"]
  model_usage: []
  status: complete
---

## Objective

Close CURRICULUM-005's named standalone-stem prerequisite without changing or
refitting the stem. Preserve all historical reports and scoped readers.

## Behavioral Change

Add an explicit consumer-pinned standalone-stem fixed-null reader. The exact
unchanged synthetic primitive/gesture/action bytes are checked at unit scale,
zero rotation, translated placements and a lifted pair. This is neither a
trained historical stem nor S2/letter/context acceptance.

## Dependencies

- [ADV-SS-CURRICULUM-005](ADV-SS-CURRICULUM-005.md)
- [ADV-SS-HANDVALIDATE-018](ADV-SS-HANDVALIDATE-018.md)

## Planned Implementation Tasks

- [x] branch: `advance/ss-handvalidate-019`, standing implement/update/merge authorization.
- [x] tidy: no pinned historical refactor; new shared immutable-replay helper only.
- [x] test: `8b77419` records missing-module failure; 14 behavioral tests pass before experiment.
- [x] feat/fix: exact lineage, analytic target, four physical refinements, local/global loss, blank region, ownership and five adversarial guards.
- [x] evaluate: seeds 7/19/41 and replay pass; 312 renders, 104 per seed, maximum 123.789 seconds, zero fitting/retries.
- [x] evidence: the live reader reconstructs all 140 artifacts, physical/control proofs and budgets; local merge receipt follows.

## Bug Fixes

The earlier return-only admission did not cover the standalone stem. No model
geometry, clock, renderer or acceptance threshold is repaired by this Advance.

## Risk + Rollback

Do not turn fixture coverage into universal translation, rotated-stem or letter
approval. Downstream placed occurrences retain their own physical/frame checks.
Only synthetic fixed-tool stem scope can be admitted; real, other gestures and
other tools fail closed. Remove only the new opt-in modules and evidence to
roll back. Existing source and historical evidence remain byte-identical.

## Evidence

- [x] tdd:red-green and tests:unit
- [x] [Frozen specification and results](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/stem_evaluation/README.md)
- [x] 72 focused tests pass; 14 new tests pass in clean `3340c3a` checkout. Plan, generated rules and whitespace checks pass.

## CI Evidence Notes

Run `arrive pr check --strict --json` before merge. Report installed parser
limitations separately; no provider CI or human appearance approval is inferred.

## Changes Made

### 2026-09-08 — feat: freeze independent standalone-stem evaluation

Two opt-in modules plus tests/specification; no new component or stage change.
The generic replay helper preserves complete immutable manifests and cumulative
budgets, and will also serve the separately versioned alignment experiment.

### 2026-09-08 — feat: complete scoped admission

Worst local actual/target loss 0.0022966003, unchanged limit 0.05. All four
refinements and five controls pass. Each seed replays 22 non-clock artifacts.
The published report hash is
`14a8ded4d6e29be259ff1dcb4c04607c44f5e7a5a9eb61727e0869150eb7dee0`.
The reader returns accepted stem/fixed-null scope, with S2 and real false.
Reviewability Red 110 is dominated by the inseparable replay manifest; tests,
runtime and evidence are separate commits. No pinned old runtime changes.

## Check for Understanding

1. Why does accepted underturn/overturn not automatically admit standalone stem?
2. Which exact identities and physical checks does the stem reader require?
3. Why is a scoped stem pass still not letter or historical-hand acceptance?
