---
advance:
  id: "ADV-SS-HANDVALIDATE-009"
  title: "Konrad Expressive Specimen — Controlled Variation and G3 Evaluation"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "handflow", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: "2026-09-06T03:52:03Z"
  review_time_estimate_minutes: 25
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence:
    - "shared/training/konrad_hand_recovery/expressive_specimen_v1/synthetic/report.json"
    - "shared/training/konrad_hand_recovery/expressive_specimen_v1/synthetic/G3.json"
    - "shared/training/konrad_hand_recovery/expressive_specimen_v1/real_attempt/G3.json"
  model_usage: []
  status: complete
---

## Objective

Establish whether coherent state improves the accepted three-line specimen while preserving its letterforms, text and nominal quality.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
Implementation and full synthetic sensitivity evaluation are complete. Synthetic G3 fails on unsafe ink/combined settings; real G3 is blocked before execution by missing accepted G1/G2 evidence. No appearance acceptance or model promotion is claimed.

## Behavioral Change

After implementation: Each expressive control is classified as inactive, active-safe or active-unsafe using its actual output and state trace. G3 combines deterministic checks, bounded variation and concrete appearance review.

## Component Impact

Primary component: `handvalidate`. Impacted components:
`handvalidate`, `handflow`, `tests`.

Implemented paths:

- scribesim/handvalidate/expressive.py (focused G3 CLI, actual-state audit and sensitivity evaluation)
- tests/test_handvalidate_expressive.py and tests/test_handflow_repertoire_state.py
- shared/training/konrad_hand_recovery/expressive_specimen_v1/

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-HANDFLOW-008](ADV-SS-HANDFLOW-008.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [x] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [x] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [x] test: establish failing behavioral tests for the contracts below before implementation.
- [x] feat/evaluate: Reuse the accepted G1/G2 proof inventory and freeze control bounds before evaluating expressive candidates.
- [x] feat/evaluate: Render neutral, one-control-at-a-time and combined variants over three explicit seeds at equal scale.
- [x] feat/evaluate: Measure contact/dip consistency, pressure/width/angle/spacing deltas, corridor deviation and text coverage separately from appearance.
- [x] feat/evaluate: Compare same-seed fresh-process replays and changed-seed variants; flag inert knobs and unsafe combinations.
- [x] feat/evaluate: Record owner rubric decisions for the expressive specimen and issue G3 with offending controls and rollback recommendations.
- [x] feat/evaluate: Reuse useful sensitivity concepts from HANDVALIDATE-006 without claiming that its broader deferred scope is complete.
- [x] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] Real G1/G2 quality remains unaccepted and blocks candidate execution. Synthetic neutral retains the engineering bounds; the ink/combined candidates do not.
- [ ] All controls are active, but ink/combined exceed frozen image bounds. Pressure/angle/rhythm are active-safe on the synthetic cases only; the unsafe settings are not accepted.
- [x] Three seeds preserve one coherent hand; all same-seed fresh-process replays match.
- [ ] Actual expressive owner acceptance is missing. The evaluator requires all rubric categories, exact bound identities and reviewed output before a pass; no scalar proxy replaces review.

Focused validation: Inject an inert profile field, a double-consumption event, an unsafe angle excursion and a hidden state reset; each must fail or be classified correctly. Validate the real proof bundle and missing-review behavior.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: Larger random deltas can be mistaken for handwriting improvement. Require intended causal effects, bounded outputs and preservation of accepted forms before owner appearance acceptance.

Rollback: Revert to the neutral G2-passing profile or disable individual unsafe controls; do not enlarge variation ranges to improve a scalar score.

Review estimate: 25 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Actual local evidence follows. The reviewer record is a pending identity-bound template, not a completed human review.

- [x] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [x] `tdd:red-green`: capture focused failing and passing test commands and results.
- [x] neutral/individual/combined three-line comparison bundle
- [x] per-control sensitivity matrix and multi-seed state reports
- [x] G3 reviewer record, replay evidence and stop/proceed decision
- [x] Record local integration checks separately from provider CI and owner review.
- [x] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

The audit detects double consumption, unrecorded ink/time/position/fatigue/motor resets, unsafe angles, unowned text and rendered samples inconsistent with actual state. Inactive and unsafe controls cannot be counted as improvement.

### Actual execution and decision

- Authorized branch `feat/td018-expressive-specimen`. No preparatory refactor was required: the bench reuses the persistent session and actual broad-edge playback, not a new controller.
- Red: module/state/conservation/sensitivity tests failed before implementation (`02094f8`). Green: the combined ten-file TD-018 suite passed 90 tests in 79.39 seconds, including the filesystem-backed multi-seed/replay fixture. The test fixture uses shorter unaccepted text; the recorded full benchmark uses the original full three-line inventory and is reported separately.
- Full execution: 18 sessions (neutral/ink/pressure/angle/rhythm/combined times seeds 7/19/41), each repeated by a fresh worker using a different Python hash seed. All 15 active-control rows replay exactly and have zero state-audit errors. All three neutral cases meet their numerical/replay checks. Frozen seeded sessions are also independently rerun by the artifact evaluator.
- The complete three-line inventory is preserved; all per-line masked losses and word-gap measurements are retained. Every contact sample has exact text ownership and actual-state coordinates/pressure/nib width. Traces use deterministic gzip encoding to keep the full evidence reviewable without discarding samples.
- Outcome: pressure, angle and rhythm are active-safe on all three synthetic seeds (worst per-line image loss approximately 0.230–0.234). Ink and combined are active-unsafe for every seed: ink loss approximately 0.646, combined 0.630–0.654, exceeding the frozen 0.35 bound. Visible over-fading before a boundary refill was inspected in the three-line ink sheet. Do not reinterpret this as handwriting improvement or relax the bound after the result.
- `synthetic/G3.json` is fail, with explicit offending controls and neutral rollback. `real_attempt/G3.json` is blocked without execution. The owner review template is pending; the implementation outcome does not satisfy appearance or upstream model acceptance.
- Runtime candidate evaluation revalidates G2/G1, model/contract identity, actual artifact hashes, isolated control configurations, exact three-line inventory and report/review identity. An edited summary cannot forge a pass; the evaluator re-executes the frozen sessions and compares both traces and reviewed pixels.
- Broader existing pathguide/handflow/integration checks: 24 passed and one failed because an old test omits required TrackPlanSample.nib_angle_deg. A local clone checked out at pre-phase `c904bde` (`/tmp/td018-guided-baseline.HMWOGy`) reproduced the same failure. It was not changed by this phase.
- `arrive plan check` passes. Strict PR check was executed and retains the known installed three-part-ID parser limitation. No provider CI or owner approval is claimed.

### Final integration verification

- Feature checkpoint `846f1fa` was cloned into `/tmp/td018-guided-clean.2x1alA` without workspace-only assets. All 90 focused tests passed in 76.59 seconds. The explicit extraction-import refusal regression also ensures this new path cannot silently depend on ignored extraction modules through the editable installation.
- The committed full expressive bundle was independently evaluated in that clone. Frozen seeded trajectories and images replayed, and the same G3 failure was reproduced for ink/combined on seeds 7/19/41, with missing real prerequisites and owner review still explicit.
- Prior per-Advance local merges are `26e8c90` (guided bridge) and `39f9941` (persistent execution). The final merge completes implementation records, not runtime acceptance. Folio and broader tremor/warp scopes remain planned/deferred.
- Next action: repair/admit the reference corpus for genuine nominal recovery/acceptance, and revise the unsafe ink configuration without relaxing the recorded post-hoc bounds. Keep neutral/default production behavior unchanged.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. How is an active but harmful control distinguished from an inactive one?
2. What evidence makes coherent variation different from a larger pixel difference?
