---
advance:
  id: "ADV-SS-HANDFLOW-011"
  title: "Source-Tangent Continuity — Frozen Primitive Reevaluation"
  system: "scribesim"
  primary_component: "handflow"
  components: ["handflow", "handvalidate", "curriculum", "tests"]
  started_at: "2026-09-07T14:57:28Z"
  implementation_completed_at: "2026-09-07T15:29:11Z"
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  model_usage: []
  status: complete
---

## Objective

Repair the artificial desired-velocity direction jump exposed by HANDVALIDATE-015
and independently reevaluate the same frozen candidates. User authorizes this
follow-up; prior update/merge workflow applies. No fitting or threshold relaxation.
See [the exact seam diagnosis](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/primitive_evaluation/diagnosis.md).

## Behavioral Change

Opt-in `curve-tangent-v1` derives velocity direction from validated source
cubic derivatives while reusing the curve clock, corner/rest policy, controller
and tool. Legacy timing/defaults and immutable reports remain untouched. Only a
fresh matching independent pass grants fixed-tool shared-gesture permission.
Run-002 passes for all three frozen candidates: compound subdivision desired
acceleration falls from 402.431643 to 126.422220 mm/s², without changing geometry.
CURRICULUM-011 is now eligible to freeze this admission; fitting has not started.

## Component Impact

Handflow gains a versioned planner adapter; handvalidate gains execution/evaluation
adapters around the existing controller/compiler/renderer. No component promotion,
alternate controller or renderer. Existing evaluator gains explicit dispatch only.

## Implementation Tasks

- [x] branch: `advance/ss-handflow-011`, clean start, authorized update/merge workflow.
- [x] tidy: no frozen lower-layer refactor needed; preserve existing execution identities.
- [x] test: `715711c` commits fourteen red tests before implementation; `ea3f1f8` commits seven red adapter/accounting tests before the single diagnosed fix. Twenty-seven final tests pass.
- [x] fix: source-derivative direction adapter, explicit version, exact provenance/owner checking and stationary rejection; legacy functions unchanged.
- [x] evidence: fresh original baseline plus 51 new-mode executions in 13 groups, covering all original families, six motion fixtures and fixed physical bridge.
- [x] evaluation: all three frozen candidates, five held-out fixtures, local benefits and seven adversarial controls pass; 40 non-wall artifacts per seed replay exactly.
- [x] admission: consumer-pinned current-code reader rechecks complete numeric proofs and required inventory, and requires `curve-tangent-v1` rather than legacy fallback.
- [x] publish: full-frame samples, budgets, retained adapter stop and next-step decision; plan updated under authorized merge workflow.

## Budget and Stop Rules

[Frozen initial protocol](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/tangent_evaluation/spec-v1.json)
and [single diagnosed revision](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/tangent_evaluation/spec-v2.json):
5000 renders / 1800 seconds per seed including setup, baseline, first/replay,
controls and presentation; zero optimizer calls; at most one diagnosed rerun.
Run-001 stops on the baseline-format adapter before candidate evaluation. Run-002
passes after proving a lossless one-occurrence diagnostic adapter, not weakening
migration. Cumulative per-seed use is 1178 renders and 61.020/55.982/55.809 seconds;
total 3534 renders, zero optimization. The one diagnosed retry is used; no hidden
budget reset or additional fitting. Old failures remain immutable.

## Bug Fixes

Fixed chord-derived desired direction jumps at equivalent subdivision seams using
validated analytic directions. Fixed the new diagnostic baseline adapter's attempted
migration of a generic crossing-enabled exercise by proving exact single-occurrence
compiled equivalence instead. Source crossing declarations, compiler, controller,
renderer and legacy clock code remain unchanged. No clamping or sample removal.

## Risk + Rollback

Retiming must not confuse overlap owners or change contact geometry. Stationary
derivatives/cusps remain unsupported and fail closed. Roll back by choosing the
unchanged legacy mode, never by reusing new-mode acceptance for that mode.

## Evidence

- [x] tdd:red-green; twenty-seven new unit/regression tests pass. Expanded baseline reproduces twelve existing failures; no unrelated changes.
- [x] Immutable candidates, sources, criteria, budgets, traces and clean current-code first/replay workers for every seed. Current admission reader accepts only the matching new-mode report.
- [x] Plan, 207 changed local links, current identities, artifact manifests, rule sync and diff checks pass. Ten existing doctor issues remain unchanged.
- [x] Strict PR-ID check executed before merge; installed parser returns `ids=[]` for `ADV-SS-HANDFLOW-011`. No successful strict gate, provider CI or human review claimed.

## CI Evidence Notes

Local validation is not provider CI or human appearance approval. No remote push
requested. Review estimate is not measured review or acceptance.

## Changes Made

### 2026-09-07 — 571a70d: Repair and independent no-refit reevaluation pass

- `291bf01` adds the planner/execution/evaluation adapters after red `715711c`; old compiler/controller/tool/clock and training/measurement identities remain unchanged.
- Run-001 uses 972 renders including replay and stops before candidate evaluation on a strict migration refusal. `ea3f1f8` preserves that failure and freezes the diagnosed revision with seven red tests.
- `571a70d` proves original single-occurrence baseline geometry and subtracts retained first-attempt accounting from the same allowance before retrying. Run-002 uses 2562 more renders, all required proofs pass, zero optimization.
- All three seeds' candidates remain byte-identical to original selection. 40 non-wall artifacts per seed replay exactly; prior false S1 artifacts stay unchanged. New scoped S1 requires `curve-tangent-v1` and the consumer-pinned report identity.
- `01e6c1e` preserves accepted evidence and admission regressions. Final clean expanded suite: 217 passes / 12 failures, versus pre-change baseline 190 passes / the identical 12 failures. All 27 new tests pass; no unrelated failure is fixed or counted as passing.
- [Results and samples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/tangent_evaluation/README.md), [current decision](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/tangent_evaluation/run-002/S1-primitives.json), [verification](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/tangent_evaluation/verification.json).
- Next: CURRICULUM-011 bounded shared-gesture learning with frozen primitives and the admitted execution mode. No learned letters, dynamic actions, historical hand or fatigue acceptance.

### 2026-09-07 — plan: Freeze the authorized source-tangent repair

- New scoped Advance follows HANDVALIDATE-015's failed compound subdivision proof.
- Models, old geometry/tool/controller/compiler and thresholds remain fixed.
