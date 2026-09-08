---
advance:
  id: "ADV-SS-HANDVALIDATE-020"
  title: "Independent Level-Assembly Validation and Appearance Review"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "curriculum", "tests"]
  started_at: "2026-09-08T17:50:21Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 45
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit"]
  model_usage: []
  status: in_progress
---

## Objective

Independently validate the frozen rotated returns and level n/u/m assemblies,
and give the owner an explicit appearance-review sheet. Follow
[TD-018 Addendum B section 11](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#11-level-assembly-and-standalone-stem-admission).
No context, fatigue, fitting, target revision or relaxed threshold is authorized.

## Behavioral Change

New opt-in validation measures exact isolated rotated occurrences and complete
frozen recipes against the unchanged target version, with independent level and
decision logic, full-frame/local image checks, four physical refinements,
negative controls and three first/replay seeds. A numeric pass is explicitly
separate from pending human appearance/reading approval; it cannot release S2.

## Dependencies

- [ADV-SS-CURRICULUM-014](ADV-SS-CURRICULUM-014.md)
- [ADV-SS-HANDVALIDATE-019](ADV-SS-HANDVALIDATE-019.md)

## Planned Implementation Tasks

- [x] branch: `advance/ss-handvalidate-020`, standing update/merge workflow.
- [x] tidy: no refactor of pinned modules; reuse immutable replay infrastructure unchanged.
- [ ] test: commit failing independent geometry, target, numeric and scope tests.
- [ ] feat/fix: freeze protocol and candidate/source hashes before measurement.
- [ ] evaluate: unchanged candidates and thresholds, six fixtures, four refinements, negative controls, seeds 7/19/41 with replay; 5000 renders/1800 seconds per seed, zero retries.
- [ ] review: enlarged guided actual-ink sheet and numbered stroke construction; leave owner verdict pending.
- [ ] evidence: report actual outcome, preserve failures, update and merge locally.

## Bug Fixes

The new gate accepts finite numeric scalars consistently before/after JSON,
without changing the frozen prior checker or its mixed worker/root receipts.

## Risk + Rollback

Matching synthetic targets cannot establish intended style or historical
legibility. Isolated rotated occurrences and exact whole recipes are bounded
coverage, not a transform envelope or accepted alphabet. Negative lineage guards
are not image-sensitivity evidence; retain an explicit rendered image control.
Remove only new opt-in validation/review artifacts to roll back. Preserve old
code/evidence and keep S2, real, context and fatigue permissions false.

## Evidence

- [x] tidy:preparatory assessed; no pinned runtime cleanup required.
- [ ] tdd:red-green
- [ ] tests:unit and clean-checkout validation
- [ ] Independent numeric/physical proofs, manifests, controls and replay budgets
- [ ] Appearance sheet published; owner approval is not inferred

## CI Evidence Notes

Run local plan/rules/whitespace and strict PR metadata checks before merge.
Record installed parser/schema limitations separately; no provider CI claim.

## Changes Made

### 2026-09-08 — plan: register bounded independent validation

Owner approved the proposed validation/review work. No new primitive fitting,
expanded alphabet, word/context learning or fatigue is included.

## Check for Understanding

1. Why are rotated returns newly scoped occurrences rather than inherited admission?
2. How does independent level/decision logic avoid merely repeating the curriculum verdict?
3. Which negative controls exercise images, and which only exercise exact lineage?
4. Why does a numeric pass still leave human appearance and S2 approval pending?
