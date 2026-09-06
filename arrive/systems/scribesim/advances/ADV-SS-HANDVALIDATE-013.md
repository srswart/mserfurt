---
advance:
  id: "ADV-SS-HANDVALIDATE-013"
  title: "Gesture Evaluation — Continuity, Shared Transfer and S1-Gesture Decision"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","gesture","curriculum","pathguide","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Independently evaluate fixed-tool continuous gesture learning before action fitting or letter construction, including failure controls and fresh-process actual execution.

**Work kind:** Evaluation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Drafting timestamp only: no implementation, investigation run, gate pass, CI or owner approval is claimed.

## Behavioral Change

After this Advance: An identity-bound S1-gesture report separates representation validity, learned transfer, execution fidelity, real-source status and owner review, with an explicit stop/revise/proceed decision.

## Component Impact

- `scribesim/handvalidate/gestures.py (planned evaluator)`
- `tests/test_handvalidate_gestures.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/gesture_evaluation/ (planned report/sample index)`

These are planned implementation/evidence locations, not existing APIs.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-CURRICULUM-008](ADV-SS-CURRICULUM-008.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before creating branches or commits.
- [ ] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [ ] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [ ] Reconstruct the frozen experiment and all shared dependencies instead of trusting a pass summary. Freeze acceptance criteria before opening evaluation proofs; changed lower-layer identities require new evidence.
- [ ] Replay all three selected seed checkpoints in fresh processes. Check continuous versus repartitioned execution, explicit lifts, overlap contributors, exact text and shared-primitive/gesture propagation.
- [ ] Compare initial/fitted nominal, sampled desired and actual controller footprints at equal scale. Measure contact schedule, endpoints, corridor/counter preservation and frozen segmentation/timestep convergence tolerances.
- [ ] Run undeclared-lift, detached per-letter geometry, overbuilt-terminal and erased-counter controls. A shape metric that cannot distinguish them blocks acceptance.
- [ ] Consume the frozen NIBCONTACT-001 failed controls: hidden connector 0.0102 and overbuilt terminal 0.0966 are below the unchanged global 0.1 sensitivity minimum. Predeclare local attachment/counter and exact contact/contributor checks before new candidates; global similarity alone cannot pass them.
- [ ] Score the frozen held-out construction fixtures without new optimization. Use the common evaluation replay/budget contract; record actual work and stop on the first unmet prerequisite.
- [ ] Publish a browsable sample index, coverage debt, S1-gesture synthetic/real scopes and the readiness decision. Current blocked G0 must not be repaired by reusing test images or treating owner silence as approval.
- [ ] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] Continuity, reuse, held-out learning and actual execution each meet their predeclared criteria; a single aggregate image score cannot mask a failed required check.
- [ ] Fresh-process evidence matches code/model/tool identities; mutation, stale gate and unsupported-capability controls fail closed.
- [ ] Supported synthetic scope may proceed independently of blocked real scope. Failed or unresolved fixed-tool gesture acceptance blocks action fitting and real downstream promotion even if this Advance is complete.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

Evaluation may accidentally refit the candidate or accept intended rather than actual contact. Read frozen candidates only, persist actual traces and retain failed reports; rollback never turns an earlier pass into new-schema acceptance.

Review estimate: 35 minutes, not a measured reviewability score.

## Evidence

- [ ] Frozen inputs, criteria and identities; complete render/time and revision ledger.
- [ ] Readable equal-scale evidence and a reproducible command/sample index under the planned bundle.
- [ ] Scope-qualified decision with negative/null/unresolved outcomes and genuine review only when performed.
- [ ] Tidy assessment and TDD red/green evidence for code changes; focused tests and clean-checkout replay where applicable.
- [ ] `arrive plan check`, changed-link checks and `git diff --check`.
- [ ] Before authorized merge, run `arrive pr check --strict --json`; report installed-tool limitations separately from provider CI. Never claim unobserved CI or owner approval.

## Bug Fixes

None implemented. Defects discovered during execution require a recorded
diagnosis and bounded repair; unrelated changes and threshold relaxation are excluded.

## Changes Made

### 2026-09-06 — plan: Scope TD-018 gesture and intentional-action work

- Added to Pass 15 phase `td018-gestures`.
- Implementation, experiments and acceptance remain pending.

## Check for Understanding

1. Which checks distinguish continuous gesture learning from primitive demos and renderer playback?
2. Why can a completed evaluation still block the next training stage?
