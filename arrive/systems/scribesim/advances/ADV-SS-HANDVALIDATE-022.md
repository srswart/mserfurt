---
advance:
  id: "ADV-SS-HANDVALIDATE-022"
  title: "Upright Targets — Read-only Yardstick Reconciliation"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "curriculum", "tests"]
  started_at: "2026-09-09T06:55:47Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 0
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
- [ ] test: saved-pixel recomputation, corrupted input rejection and no execution/rendering.
- [ ] feat/fix: read-only reconciliation report with pinned inputs and no new thresholds.
- [ ] design: distinguish approved regression anchors from independent style targets.
- [ ] evidence: publish measurements, update phase and merge locally.

## Bug Fixes

- [ ] Correct interpretation of an arbitrary analytic style mismatch as a possible reason to refit approved shapes; no claim of a new controller bug.

## Risk + Rollback

- Risk: laundering candidate-derived references into independent validation or silently removing a failed gate.
- Rollback: retain all existing archives, source pins and failed decisions; withhold any new admission. No core evaluator, candidate, target, threshold, training or fatigue change.
- Budget: zero controller executions, zero raster renders, zero optimization. Only hash verification, saved-pixel arithmetic and analytic geometry inspection.

## Evidence

- [x] tidy:preparatory not required; isolation is deliberate.
- [ ] tdd:red-green.
- [ ] tests:unit and saved-evidence integration.
- [ ] Deterministic report; unchanged HANDVALIDATE-021 archive and owner bindings.

## CI Evidence Notes

Run focused tests and plan/rules/whitespace checks. Record strict PR metadata
result separately from provider CI. No provider run or owner target endorsement
may be inferred from this investigation.

## Changes Made

### 2026-09-09 - freeze read-only investigation

User authorizes the next yardstick reconciliation step. Freeze source report,
specification, verification receipt and actual-ink approval before diagnostic
arithmetic. New outputs live outside existing run archives. Template scaffold:
ARRIVE 0.1.24, fingerprint d0972eaefbbf79a3.

## Check for Understanding

1. Why can an approved appearance and a failed independent target score coexist?
2. Why is a reference copied from this candidate a regression anchor, not independent evidence?
3. What must be approved and frozen before a replacement style target is scored?
