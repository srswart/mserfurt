---
advance:
  id: "ADV-SS-HANDVALIDATE-024"
  title: "Approved Appearance — Held-out Placement Physical Validation"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "tests"]
  started_at: "2026-09-09T08:55:15Z"
  implementation_completed_at: "2026-09-09T09:32:50Z"
  review_time_estimate_minutes: 926
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 120
  risk_flags: ["auth"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration"]
  model_usage: []
  status: complete
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
- [x] feat/fix: execution harness and separate raw-evidence reader.
- [x] evidence: one immutable run, all three seeds and fresh-process replays.
- [ ] docs/merge: publish samples, update advance/plan and merge locally; no push.

## Bug Fixes

- [x] Make visible-shift negative control compare against unshifted actual ink,
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
- [x] tests:unit and raw-evidence verification.

## CI Evidence Notes

Run focused tests and local plan/rules/whitespace/strict PR metadata checks.
Do not equate local results or merge with provider CI or held-out owner approval.

53 focused tests pass: 33 harness/contract tests in 110.69 s and 20 existing
reconciliation/raw-reader/replay/measurement tests in 48.43 s. The latter includes
one tiny synthetic ii controller unit test, two image renders and one owner-mask
generation call, separate from the journaled candidate experiment. New harness
and contract tests prohibit physical execution/rendering. No fitting occurs.

Local test evidence is recorded as local-unit-validation, provider unknown,
workflow "53 focused tests; no provider CI", implementation d718d05. The installed
CLI automatically added ci:passed; that unqualified tag is removed here because
no provider pipeline ran. Its local receipt remains in .arrive/evidence/ci.
The installed strict PR metadata parser returns ids=[] despite explicit
title/body/label IDs. No parser repair or provider CI success is claimed.

## Changes Made

### 2026-09-09 - independent inspection and completion

The consumer-pinned read-only inspector passes all 1,808 artifacts and all six
worker decisions, reconstructing raw trace/mask/image evidence with zero controller
executions and zero rerenders. All six independent style channels remain FAIL;
all six new appearance verdicts remain pending. Inspection SHA256:
`bda0a94c03a4d8a870cf398137e29c1e093349c0b8f1345a71a4da0caa3c499d`.
Receipt, review record and gallery sit outside the immutable run. Source/core
identities and all previous evidence remain intact. Plan, generated-rule, whitespace,
local-link and review-pin checks pass. Final ARRIVE score is red 120, estimated
926 minutes, dominated by immutable generated evidence; rationale is below.

### 2026-09-09 - frozen physical run and review samples

Green implementation d718d05 follows red 2f0b8a4. The opt-in runner and separate
reader live in scripts, preserving all 206 old core identities and all earlier
archives. Source/candidate/derived-vector/reader freeze precedes scoring. No new
component is needed; existing incubating handvalidate selectors route both APIs.

Evidence commit e955011 preserves the single immutable run. All ten fixtures at
four refinements pass mechanics, levels, ports, tracking and exact-event
convergence. All three seed/replay pairs match; 24 known-base anchor comparisons
match and all eleven controls detect in all six workers. New held-out nominal
losses are report-only; independent style remains diagnostic under the approved
new contract, with historical H021 numeric failure intact. Appearance for the
six new pairs stays pending; S2/real/context and overall admission remain withheld.

The experiment uses 1,086 renders and 240 controller executions, zero fitting
and retries. Seeds 7/19/41 each debit 362 renders and respectively 327.683,
326.274 and 351.945 seconds including replay. New authorized per-seed caps are
5,000 / 1,800; no prior allowance is reused. Raw/pixel/mask evidence and the
44,145,873-byte pre-scoring vector freeze produce 1,808 pinned artifacts.
Root report SHA256:
`25b0e886ab643ff5dee969d1393b1f3f1e235e75f945e3c94025aedcfffe36b4`.

The new gallery emphasizes actual ink for un/nu/um/nn/uu/mm, with expandable
derived nominal and analytic diagnostics, complete-frame/native-detail controls
and direct full-resolution image links. Desktop 1440x1000 and mobile 390x844
checks verify readable panels and functioning controls. The complete gallery
has zero console errors/warnings; before the root report existed, it correctly
withheld samples instead of showing partial/reconstructed results.

Reviewability is red because one immutable physical experiment contains 1,809
archive files and 1,455,316 generated text lines, including the exact vector
freeze. Splitting or rewriting its frozen manifest to reduce the score would
destroy its evidence boundary. Red tests, 347 lines of runner/reader behavior,
immutable evidence and documentation are separate reviewable commits; automated
hash/raw-evidence verification covers the bulk data. The reported estimate is
not completed human review, and no appearance verdict is inferred from it.

### 2026-09-09 - execution authorization and red tests

Owner explicitly authorizes running the prepared validation. New authorization
pins the prepared protocol/registry/report without editing historical snapshots.
Red test commit 2f0b8a4 precedes implementation. ARRIVE template 0.1.24.

## Check for Understanding

1. Why is exact known-base replay not a new quality or generalization gate?
2. Which losses are diagnostic, and which unchanged mechanical limits are gates?
3. Why do six successful placements still need owner review and not authorize context?
