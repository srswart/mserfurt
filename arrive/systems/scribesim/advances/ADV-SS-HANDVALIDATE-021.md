---
advance:
  id: "ADV-SS-HANDVALIDATE-021"
  title: "Upright Construction — Independent Continuous-Contact Evaluation"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "curriculum", "gesture", "tests"]
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
  status: in_progress
---

## Objective

Independently evaluate a reviewed, frozen upright pen-down construction without
refitting or weakening existing gates. Follows
[TD-018 Addendum B section 13](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#13-upright-pen-down-construction-repair).
Depends on GESTURE-003, CURRICULUM-015 and its explicit owner-review checkpoint.

## Behavioral Change

Separate actual contact/overlap/timing and geometric/image evidence from nominal
construction and owner appearance. Use new immutable artifacts and an independent
reader; do not invoke the builder's decision function as validation. Mechanical
success cannot override the owner's repair verdict or grant context permission.

## Component Impact

- `handvalidate`: proposed `upright_letters` frozen replay and read-only evidence reader.
- `curriculum` / `gesture`: consume exact reviewed candidate and new contract identities.
- `tests`: independent gates, adversarial controls, replay and archive immutability.
- Proposed outputs: `letters/upright/validation/` under the existing training tree.

## Planned Implementation Tasks

- [x] branch: create `advance/ss-handvalidate-021` after CURRICULUM-015 merges.
- [x] prerequisite: owner endorses the frozen CURRICULUM-015 nominal n/u/m; candidate-bound keep verdicts recorded. This is not actual-ink review.
- [x] prerequisite: freeze independent analytic target provenance/version, candidate/code hashes and all evaluation budgets before scoring.
- [x] tidy: isolate reader/measurement logic without mutating frozen source artifacts.
- [x] test: commit failing independent decision, ownership and archive tests first.
- [x] feat/fix: implement no-fit actual-motion and full-frame image evaluation.
- [ ] evaluate: isolated strokes/reversals, n/u/m and predeclared transfer probes at seeds 7/19/41 with fresh-process replay.
- [ ] evaluate: inserted lift, gap, false smooth reversal, overlap-owner, geometry/tool, climbing, desired-as-actual and visible-shift controls.
- [ ] evaluate: base/arc/time for letters; subdivision only within unchanged caps.
- [ ] evidence: immutable reports, actual/nominal comparison samples, independent reader and renewed owner review request.
- [ ] merge: update implementation outcome separately from all acceptance flags.

## Bug Fixes

- [ ] Ensure inter-gesture ownership changes do not imply actual pen lifts.
- [ ] Detect retracing accumulation and missing overlap contributors, not only crossings.
- [ ] Reject cropped ink, substituted desired motion and stale source identities.

## Risk + Rollback

The new target must be independently defined from reviewed requirements, never
candidate pixels/cubics. Keep absolute/local image limits 0.05, relative loss
0.75, nominal level residual 1e-8 and actual landmark limit 0.05 mm unchanged.
The relative comparison uses both candidates against the same new target; reject
an undefined ratio. Freeze proposed angle/clearance criteria separately after
review. Preserve failures, use zero automatic retries and require a new explicit
scope for any fitting. Exact fixtures/render/time budgets are prerequisites, not
permission to inherit an unrelated old budget. Roll back by withholding new
admission, never erasing failed evidence. S2/real/context remain false unless
their separately explicit acceptance requirements are satisfied; no fatigue.

## Evidence

- [ ] tidy:preparatory if needed, otherwise record why isolation suffices.
- [ ] tdd:red-green; tests:unit and tests:integration.
- [ ] Complete full-frame traces/images, source identities and fresh-process replay.
- [ ] All negative controls fail for the intended reason; independent reader verifies archive integrity.
- [ ] Candidate-bound actual-ink owner review, distinct from numerical results.

## CI Evidence Notes

Run targeted/broader tests, plan/rules/whitespace and strict PR metadata checks.
Record only real provider/run evidence. Recalculate reviewability on actual work;
split test, implementation and evidence commits before merge.

## Changes Made

### 2026-09-09 - implementation and pre-score protocol freeze

New isolated `upright_targets`, `upright_measurement`, `upright_letters` and
`upright_evidence` modules leave all frozen builders, controllers and previous
readers untouched. No preparatory refactoring is needed. The target accepts only
the frozen specification and fixture: vertical lines and round-number semicircles,
not candidate curves/pixels. This is an independent synthetic yardstick, **not an
owner-approved aesthetic target**. New aesthetic angle/clearance thresholds are
not invented; slant and repeated coverage remain diagnostics.

The pre-score spec pins candidate `01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd`,
its report and nominal KEEP record, the old comparison candidate, ten fixtures,
four refinements, unchanged numeric gates and 5,000 renders/1,800 seconds per seed
including replay, zero retries and zero optimization. The runner writes complete
code/spec identities before executing any candidate. Source subdivision uses two
exact internal cubics, not extra references: all existing caps validate, including
six expanded references for m. It can therefore be measured for full letters.

Red: `c937cc0` missing evaluator import; `5e43d25` exercises a synthetic two-letter
retrace and fails on serialized identity/air-field handling. Green: seven new
tests pass. The broader five-file suite has 70 passes and five pre-existing stale
admission failures in `test_curve_tangents.py`; no archived source is repinned.
The synthetic integration fixture is not the reviewed candidate and does not
score it. Actual candidate evaluation has not run at this checkpoint.

### 2026-09-09 - prerequisite: nominal appearance checkpoint satisfied

The owner approves CURRICULUM-015's nominal n/u/m appearance; all three verdicts
are keep in its separate candidate-bound owner-review record. The candidate and
frozen evidence are unchanged. This Advance remains planned: independent target,
fixture, criterion and budget freeze still precedes execution. No refitting or
physical validation is performed by recording the feedback.

### 2026-09-08 - plan: register independent evaluation after visual review

No render, target revision, fitting or acceptance occurs when registering this
Advance. Exact target/fixture/budget freeze and reviewed candidate are execution
prerequisites. HANDVALIDATE-020's archived evidence remains unchanged.
Planning checks pass for the plan, generated rules and whitespace. The installed
strict PR metadata parser returns `ids=[]` despite explicit Advance IDs in the
title and labels; no provider CI or implementation test pass is claimed.

## Check for Understanding

1. Why must a nominal preview and an actual-ink owner review be separate?
2. How is continuous contact proven without losing individual gesture ownership?
3. Why cannot an undefined ratio or isolated subdivision proof pass a whole-letter gate?
