---
advance:
  id: "ADV-SS-HANDVALIDATE-024"
  title: "Approved Appearance — Held-out Placement Physical Validation"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "tests"]
  started_at: "2026-09-09T08:55:15Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 60
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

Execute the owner-authorized HANDVALIDATE-023 prepared placement protocol with
frozen candidate, references and reader. Measure known n/u/m/mu and held-out
un/nu/um/nn/uu/mm without fitting, changing style targets or expanding admission.

## Behavioral Change

A separate bounded physical validation reports mechanics, exact known-base
regression identity and diagnostic style/nominal comparisons. New actual samples
remain pending owner review. Fixed placements are not joins or contextual learning.

## Planned Implementation Tasks

- [x] branch: advance/ss-handvalidate-024.
- [x] tidy: no core edits; reuse frozen runtime and arithmetic through opt-in scripts.
- [x] test: fail-closed decision, reference roles, source preflight and retry boundaries.
- [ ] feat/fix: execution harness and separate raw-evidence reader.
- [ ] evidence: one immutable run, all three seeds and fresh-process replays.
- [ ] docs/merge: publish samples, update advance/plan and merge locally; no push.

## Bug Fixes

- [ ] Make visible-shift negative control compare against unshifted actual ink,
  rather than an analytic target that already fails for the unchanged candidate.

## Risk + Rollback

- Risk: candidate-derived references could be mistaken for independent quality or
  approval could leak from old samples into unseen placements.
- Rollback: withhold new evidence; preserve all attempts. Never change frozen
  core sources, candidate, targets or thresholds. S2/real/context remain false.
- Budget: new owner authorization, 5,000 renders / 1,800 seconds per seed including
  replay, zero retries and fitting. Freeze code/reader/vector references before scoring.

## Evidence

- [x] tidy:preparatory unnecessary; preserve old frozen source identities.
- [x] tdd:red-green: red collection failure recorded before implementation.
- [ ] tests:unit and raw-evidence verification.

## CI Evidence Notes

Run focused tests and local plan/rules/whitespace/strict PR metadata checks.
Do not equate local results or merge with provider CI or held-out owner approval.

## Changes Made

### 2026-09-09 - execution authorization and red tests

Owner explicitly authorizes running the prepared validation. New authorization
pins the prepared protocol/registry/report without editing historical snapshots.
Red test commit 2f0b8a4 precedes implementation. ARRIVE template 0.1.24.

## Check for Understanding

1. Why is exact known-base replay not a new quality or generalization gate?
2. Which losses are diagnostic, and which unchanged mechanical limits are gates?
3. Why do six successful placements still need owner review and not authorize context?
