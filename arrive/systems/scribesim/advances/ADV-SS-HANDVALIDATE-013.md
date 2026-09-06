---
advance:
  id: "ADV-SS-HANDVALIDATE-013"
  title: "Gesture Evaluation — Continuity, Shared Transfer and S1-Gesture Decision"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","gesture","curriculum","pathguide","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: "2026-09-06T13:44:02Z"
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration", "shared/training/konrad_hand_recovery/stroke_gestures_v2/gesture_evaluation/run-001/S1-gesture.json"]
  model_usage: []
  status: complete
---

## Objective

Independently evaluate fixed-tool continuous gesture learning before action fitting or letter construction, including failure controls and fresh-process actual execution.

**Work kind:** Evaluation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Evaluation implementation and execution are complete. S1-gesture remains blocked:
missing broad vocabulary and failed lifted-pair contact-entry convergence.
The failed acceptance checkbox remains unchecked. No owner approval or CI is claimed.

## Behavioral Change

After this Advance: An identity-bound S1-gesture report separates representation validity, learned transfer, execution fidelity, real-source status and owner review, with an explicit stop/revise/proceed decision.

## Component Impact

- `scribesim/handvalidate/gestures.py`
- `tests/test_handvalidate_gestures.py`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/gesture_evaluation/`

These are implemented evaluator, test and immutable evidence locations.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-CURRICULUM-008](ADV-SS-CURRICULUM-008.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [x] branch: confirm authorization before creating branches or commits.
- [x] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [x] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [x] Reconstruct the frozen experiment and all shared dependencies instead of trusting a pass summary. Freeze acceptance criteria before opening evaluation proofs; changed lower-layer identities require new evidence.
- [x] Replay all three selected seed checkpoints in fresh processes. Check continuous versus repartitioned execution, explicit lifts, overlap contributors, exact text and shared-primitive/gesture propagation.
- [x] Compare initial/fitted nominal, sampled desired and actual controller footprints at equal scale. Measure contact schedule, endpoints, corridor/counter preservation and frozen segmentation/timestep convergence tolerances.
- [x] Run undeclared-lift, detached per-letter geometry, overbuilt-terminal and erased-counter controls. A shape metric that cannot distinguish them blocks acceptance.
- [x] Consume the frozen NIBCONTACT-001 failed controls: hidden connector 0.0102 and overbuilt terminal 0.0966 are below the unchanged global 0.1 sensitivity minimum. Predeclare local attachment/counter and exact contact/contributor checks before new candidates; global similarity alone cannot pass them.
- [x] Score the frozen held-out construction fixtures without new optimization. Use the common evaluation replay/budget contract; record actual work and stop on the first unmet prerequisite.
- [x] Publish a browsable sample index, coverage debt, S1-gesture synthetic/real scopes and the readiness decision. Current blocked G0 must not be repaired by reusing test images or treating owner silence as approval.
- [x] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [ ] Continuity, reuse, held-out learning and actual execution each meet their predeclared criteria; a single aggregate image score cannot mask a failed required check.
- [x] Fresh-process evidence matches code/model/tool identities; mutation, stale gate and unsupported-capability controls fail closed.
- [x] Supported synthetic scope may proceed independently of blocked real scope. Failed or unresolved fixed-tool gesture acceptance blocks action fitting and real downstream promotion even if this Advance is complete.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

Evaluation may accidentally refit the candidate or accept intended rather than actual contact. Read frozen candidates only, persist actual traces and retain failed reports; rollback never turns an earlier pass into new-schema acceptance.

Review estimate: 35 minutes, not a measured reviewability score.

## Evidence

- [x] Frozen inputs, criteria and identities; complete render/time and revision ledger.
- [x] Readable equal-scale evidence and a reproducible command/sample index under the planned bundle.
- [x] Scope-qualified decision with negative/null/unresolved outcomes and genuine review only when performed.
- [x] Tidy assessment and TDD red/green evidence for code changes; focused tests and clean-checkout replay where applicable.
- [x] `arrive plan check`, changed-link checks and `git diff --check`.
- [x] Before authorized merge, run `arrive pr check --strict --json`; report installed-tool limitations separately from provider CI. Never claim unobserved CI or owner approval.

## Bug Fixes

Evaluation exposes a lifted-pair re-entry instability: arc-step refinement changes
the second contact endpoint by 0.399871 mm (limit 0.01 mm). Read-only diagnosis
implicates discrete desired-sample integration and corridor projection after air
travel. No controller repair or threshold relaxation is included; preserve this
failure as the starting regression for separately scoped fixed-tool repair.

## Changes Made

### 2026-09-06 — plan: Scope TD-018 gesture and intentional-action work

- Added to Pass 15 phase `td018-gestures`.
- Implementation, experiments and acceptance remain pending.

### 2026-09-06 — complete: Independent evaluation; STOP / REVISE

- User authorized per-Advance branches, updates and local merges. No push.
  No preparatory refactor needed; new evaluator is an opt-in sibling.
- Red tests committed in `fec2d8a`; missing evaluator module failed collection.
  Criteria committed before evaluation; local physical guard rectangles refined
  in `2148f7d` before any evaluation run. Implementation/evidence: `bfdb5e4`.
- Verify pinned training freeze/report, lower S1 artifacts/code, source-coverage
  identity, reconstructed synthetic targets, all three ablations and selected
  checkpoints. Evaluation never calls the optimizer; tests enforce this.
- All three seeds independently replay byte-identical semantic JSON and actual
  traces under hash seeds 7/839. Exact cubic subdivision, timestep refinement,
  held-out scores, image/corridor and contact/contributor checks are measured.
  Existing compiler regressions cover shared propagation and declared overlaps.
- 73 renders per seed attempt; first plus replay for three seeds and six
  presentation/control renders total 444 in 21.39 seconds. Zero optimization,
  zero evaluation revisions; no source pixels opened or real fitting attempted.
- All three seeds FAIL lifted-pair arc-step endpoint convergence: 0.399871 mm
  against 0.01 mm. The image change 0.022739 passes 0.03 but cannot override
  endpoint failure. S1-gesture and action fitting remain blocked even for the
  narrow construction lesson. Broad returns/loops also remain unsupported.
- Original global hidden-connector / overbuilt-terminal sensitivity failures
  remain 0.010179 / 0.096616 below 0.1. Predeclared local blank-region fractions
  0.058459 / 0.094282 exceed 0.01 and reject them; clean guards score zero.
  Erased counter is rejected locally; these are independent synthetic guards,
  not learned-counter or new nib-renderer acceptance. Undeclared lifts, painted
  air, extra contributors, detached geometry and stale identities fail closed.
- 51 tests pass locally (12.51s), then in clean clone
  `/tmp/td018-evaluation-clean.ArMCrI` at `bfdb5e4` (12.73s).
  Full hash-seed-839 replay in `/tmp/td018-evaluation-replay.vrbCLd` matches
  every semantic artifact; measured wall receipts vary. Validation replay is
  separate verification, not additional candidate search.
- `arrive plan check`, changed-link validation and `git diff --check` pass.
  Canonical controllers/renderers, frozen primitive evidence and references
  remain byte-unchanged. Generated agent rules have no stale files.
- Strict PR metadata check ran; installed parser returns `ids: []` for this
  repository's three-part Advance IDs. Provider CI is unobserved. Artifact
  doctor retains the same 10 pre-existing unrelated errors; none is repaired
  or represented as a passing provider check. No genuine owner review occurred.
- [Samples, reproduction and required fixed-tool repairs](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/gesture_evaluation/README.md).

## Check for Understanding

1. Which checks distinguish continuous gesture learning from primitive demos and renderer playback?
2. Why can a completed evaluation still block the next training stage?
