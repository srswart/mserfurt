---
advance:
  id: "ADV-SS-HANDVALIDATE-022"
  title: "Upright Targets — Read-only Yardstick Reconciliation"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "curriculum", "tests"]
  started_at: "2026-09-09T06:55:47Z"
  implementation_completed_at: "2026-09-09T07:02:46Z"
  review_time_estimate_minutes: 110
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 64
  risk_flags: []
  evidence: ["tdd:red-green", "tests:unit", "tests:integration"]
  model_usage: []
  status: complete
---

## Objective

Explain the conflict between owner-approved actual n/u/m and failed independent
semicircle-target gates, using saved evidence only. Document the prospective
evaluation contract before any replacement target or fitting experiment.
Follows TD-018 Addendum B section 13 and HANDVALIDATE-021's actual-ink KEEP.

## Behavioral Change

Report target-versus-nominal, target-versus-actual, nominal-versus-actual and
desired-versus-actual image differences as distinct measurements. Disclose
geometric convention differences without attributing nonlinear loss to additive
causes. Keep historical numeric failure and all acceptance restrictions intact.

## Planned Implementation Tasks

- [x] branch: `advance/ss-handvalidate-022`.
- [x] tidy: unnecessary; external diagnostic script preserves frozen source identities.
- [x] test: saved-pixel recomputation, corrupted input rejection and no execution/rendering.
- [x] feat/fix: read-only reconciliation report with pinned inputs and no new thresholds.
- [x] design: distinguish approved regression anchors from independent style targets.
- [x] evidence: publish measurements, update phase and merge locally at `948d94c`; no push.

## Bug Fixes

- [x] Correct interpretation of an arbitrary analytic style mismatch as a possible reason to refit approved shapes; no claim of a new controller bug.

## Risk + Rollback

- Risk: laundering candidate-derived references into independent validation or silently removing a failed gate.
- Rollback: retain all existing archives, source pins and failed decisions; withhold any new admission. No core evaluator, candidate, target, threshold, training or fatigue change.
- Budget: zero controller executions, zero raster renders, zero optimization. Only hash verification, saved-pixel arithmetic and analytic geometry inspection.

## Evidence

- [x] tidy:preparatory not required; isolation is deliberate.
- [x] tdd:red-green.
- [x] tests:unit and saved-evidence integration.
- [x] Deterministic report; unchanged HANDVALIDATE-021 archive and owner bindings.

## CI Evidence Notes

Run focused tests and plan/rules/whitespace checks. Record strict PR metadata
result separately from provider CI. No provider run or owner target endorsement
may be inferred from this investigation.

Four new tests pass in 2.21 s; combined target/event reader/replay/measurement suite
passes 34 tests in 49.06 s. No old admission tests or frozen guards are changed.
Plan/rules/whitespace and local Markdown links validate. Strict PR parser still
reports `ids=[]` despite explicit title/body/label IDs; no provider CI claim.
Reviewability is red 64, estimated 109.2 minutes (rounded to 110), with separate
scope, red-test, implementation, immutable report and design commits. This is a
machine estimate, not completed human review.

## Changes Made

### 2026-09-09 - owner approves prospective reference contract

Owner: “I have reviewed it -- approved.” Record design approval as
`reviewed-synthetic-appearance-contract-v1` in the reconciliation directory's
`contract-review.json`, pinning the pre-approval document at `a7ca2ac` and section
14C body hashes. TD-018 and the current plan now distinguish approved design from
pending implementation and concrete protocol freeze. No repeat review of this
same design or approved n/u/m appearance is needed.

This documentation-only checkpoint changes no evaluator, candidate, target,
threshold, measured result or archived approval. New experiment budgets, fitting
and S2/real/context admission are not inferred. Earlier entries preserve the
then-pending design state; HANDVALIDATE-022 investigation remains complete.
Reviewed revision/section hashes verify; the diagnostic report reproduces with
all 1,256 archived artifacts unchanged. Plan/rules/whitespace checks pass. Existing
strict PR metadata parser limitation persists; no provider CI or experiment rerun.

### 2026-09-09 - local merge receipt

Merged `advance/ss-handvalidate-022` into local master at `948d94c`. The scoped
investigation/design is complete; prospective reference-contract approval and
implementation are deliberately not claimed. No push, provider CI, new scored
experiment or acceptance. Final read-only report replay, source/archive pins,
plan/rules/whitespace and report links pass. Owner-approved shapes stay unchanged.

### 2026-09-09 - measured reconciliation and prospective contract

Red `3c480d0` requires the missing diagnostic module. Green `923b56c` adds only
`scripts/handvalidate_upright_targets.py`, outside frozen evaluator identities.
It verifies source pins, all 1,256 archived artifacts and the existing independent
reader/owner bindings; it recomputes all saved nominal/actual target losses and
desired tracking losses at four refinements plus nominal-to-actual diagnostics.
The prior pinned receipt supplies motion/replay evidence; no new motion check
execution, rendering, fitting or acceptance is claimed.

Report in `letters/upright/validation/reconciliation-001/report.json` (training
tree), evidence commit `0791eb7`, SHA256
`f56d560e345b686e8dc06d2a5cef55ea4a8956d7b3f608e0069c330462ce3eae`.
Tests reproduce it deterministically and reject changed pins/path escapes and
report overwrites. All budgets are zero. The original candidate, target, limits,
reports, code freeze and actual-ink owner KEEP remain unchanged.

Base n/u/m target-to-nominal loss is 0.382013/0.232303/0.590033; nominal-to-actual
loss is 0/0.000302/0.000957. Maximum nominal-to-actual over all fixtures/refinements
is 0.00665819. Approved letter port spans exceed analytic spans by 18.16–20.18%;
rise attachment and asymmetric return heights also differ. This supports a
style/construction mismatch rather than poor execution of the approved shape.
It is not additive causal loss attribution or a new threshold-based pass.

TD-018 Addendum B section 14 separates owner approval, mechanical fidelity,
candidate-derived regression references and independent style provenance. The
preferred prospective contract preserves approved synthetic appearance as a
regression anchor with explicit style diagnostics. It is proposed, not activated:
new target roles/gates and any independent style specification require review and
a pre-score freeze. No relabeling can remove HANDVALIDATE-021's failed gate or
grant S2/real/context permission. Findings and exact reproduction command are in
the reconciliation README. No new component is needed; handvalidate remains
incubating and the existing invariant on all-required-gates admission is retained.

### 2026-09-09 - freeze read-only investigation

User authorizes the next yardstick reconciliation step. Freeze source report,
specification, verification receipt and actual-ink approval before diagnostic
arithmetic. New outputs live outside existing run archives. Template scaffold:
ARRIVE 0.1.24, fingerprint d0972eaefbbf79a3.

## Check for Understanding

1. Why can an approved appearance and a failed independent target score coexist?
2. Why is a reference copied from this candidate a regression anchor, not independent evidence?
3. What must be approved and frozen before a replacement style target is scored?
