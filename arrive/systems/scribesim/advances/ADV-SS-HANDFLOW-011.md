---
advance:
  id: "ADV-SS-HANDFLOW-011"
  title: "Source-Tangent Continuity — Frozen Primitive Reevaluation"
  system: "scribesim"
  primary_component: "handflow"
  components: ["handflow", "handvalidate", "curriculum", "tests"]
  started_at: "2026-09-07T14:57:28Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
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

Repair the artificial desired-velocity direction jump exposed by HANDVALIDATE-015
and independently reevaluate the same frozen candidates. User authorizes this
follow-up; prior update/merge workflow applies. No fitting or threshold relaxation.
See [the exact seam diagnosis](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitive_evaluation/diagnosis.md).

## Behavioral Change

Planned opt-in `curve-tangent-v1` derives velocity direction from validated source
cubic derivatives while reusing the curve clock, corner/rest policy, controller
and tool. Legacy timing/defaults and immutable reports remain untouched. Only a
fresh matching independent pass may grant fixed-tool shared-gesture permission.

## Component Impact

Handflow gains a versioned planner adapter; handvalidate gains execution/evaluation
adapters around the existing controller/compiler/renderer. No component promotion,
alternate controller or renderer. Existing evaluator gains explicit dispatch only.

## Planned Implementation Tasks

- [x] branch: `advance/ss-handflow-011`, clean start, authorized update/merge workflow.
- [x] tidy: no frozen lower-layer refactor needed; preserve existing execution identities.
- [ ] test: commit observed red seam, all-family subdivision, provenance, corner/reentry and fail-closed reader tests before implementation.
- [ ] fix: source-derivative direction adapter with explicit version and stationary rejection.
- [ ] evidence: refresh original baseline, all-family actual refinements and full motion protocol under the new mode.
- [ ] evaluation: three frozen candidates, five held-out fixtures, local benefits and seven adversarial controls, clean fresh-process replay, zero fitting.
- [ ] admission: pinned current-code reader, complete numeric proofs, exact required inventory and execution version.
- [ ] publish: full-frame samples, budgets, failures, next-step decision; update plan and merge when finished.

## Budget and Stop Rules

[Frozen protocol](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/tangent_evaluation/spec-v1.json):
5000 renders / 1800 seconds per seed including setup, baseline, first/replay,
controls and presentation; zero optimizer calls; at most one diagnosed rerun.
Stop on invalid inputs or any failed required proof. Old failures remain immutable.

## Bug Fixes

Pending: chord-derived desired direction jumps at equivalent cubic subdivision
seams although geometry and elapsed source clock agree. Do not clamp acceleration,
drop seam samples, guess source ownership or reset controller pose.

## Risk + Rollback

Retiming must not confuse overlap owners or change contact geometry. Stationary
derivatives/cusps remain unsupported and fail closed. Roll back by choosing the
unchanged legacy mode, never by reusing new-mode acceptance for that mode.

## Evidence

- [ ] tdd:red-green and focused/expanded tests; disclose existing failures separately.
- [ ] Immutable candidates, sources, criteria, budgets, traces and current-code replay.
- [ ] Plan, local links, artifact/identity checks, rule sync and diff checks.
- [ ] Strict PR-ID check before merge; disclose installed parser limitation, not provider CI.

## CI Evidence Notes

Local validation is not provider CI or human appearance approval. No remote push
requested. Review estimate is not measured review or acceptance.

## Changes Made

### 2026-09-07 — plan: Freeze the authorized source-tangent repair

- New scoped Advance follows HANDVALIDATE-015's failed compound subdivision proof.
- Models, old geometry/tool/controller/compiler and thresholds remain fixed.
