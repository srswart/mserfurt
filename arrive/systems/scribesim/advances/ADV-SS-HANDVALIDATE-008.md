---
advance:
  id: "ADV-SS-HANDVALIDATE-008"
  title: "Konrad Nominal Specimen — Unseen Words and Three-Line Acceptance"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "evo", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: "2026-09-05T19:00:15Z"
  review_time_estimate_minutes: 25
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence:
    - "shared/training/konrad_hand_recovery/nominal_specimen_v1/freeze.json"
    - "shared/training/konrad_hand_recovery/nominal_specimen_v1/G1.json"
  model_usage: []
  status: complete
---

## Objective

Evaluate the frozen repertoire against G1 and deliver the first concrete three-line specimen before any new controller realism work.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
Implementation and the bounded seed-diagnostic run are complete. G1 is blocked: no accepted G0 corpus, real recovered checkpoint, real-source tolerances, owner appearance review or independent reading. No model is promoted.

## Behavioral Change

After implementation: The project can inspect reconstruction, unseen combinations and manuscript text side by side, with exact coverage, per-word evidence and a recorded pass/fail/blocked decision that scalar loss cannot override.

## Component Impact

Primary component: `handvalidate`. Impacted components:
`handvalidate`, `evo`, `tests`.

Implemented paths (focused sibling module, reusing baseline/specimen helpers):

- scribesim/handvalidate/nominal.py (G1 evaluator, CLI and panels)
- scribesim/handvalidate/specimen.py (existing helpers reused unchanged)
- scribesim/evofit/recovery.py (export source/baseline/config identities for the G1 boundary)
- tests/test_handvalidate_nominal_specimen.py
- shared/training/konrad_hand_recovery/nominal_specimen_v1/ (proofs, test report and review record)

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-EVOFIT-006](ADV-SS-EVOFIT-006.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [x] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [x] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [x] test: establish failing behavioral tests for the contracts below before implementation.
- [x] feat/evaluate: Freeze selected checkpoint/configuration and confirm G0 split/coverage artifacts before opening locked test inputs.
- [x] feat/evaluate: Render the three proof lines plus at least five unseen strings, separating real referenced unseen words from unscored synthetic combinations.
- [x] feat/evaluate: Report repeated-word and unseen-word losses, worst cases, mapping coverage, exclusions and fresh-process deterministic replay.
- [x] feat/evaluate: Generate equal-scale randomized baseline/candidate panels with the fixed reference sheet and per-category appearance rubric.
- [x] feat/evaluate: Capture owner appearance review and independent-reading status honestly; leave missing readings/review blocked without inventing approval.
- [x] feat/evaluate: Issue G1 and a stop/revise/proceed recommendation after the initial run and at most one diagnosed revision; disclose test reuse and reserve a new test set for a subsequent version.
- [x] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [x] Exact logical-to-visible coverage is 1.0 with zero aliases or undeclared normalization on the frozen proof inventory.
- [ ] Real G1 acceptance remains blocked: synthetic controls and replay pass, but real-source metric tolerances are not calibrated/frozen. No locked test is scored.
- [ ] Actual three-line owner acceptance and preference: missing. The evaluator requires every category and baseline preference before passing; its positive unit fixture is not owner approval.
- [x] Unavailable independent readings are explicit; image agreement is never labeled OCR accuracy or paleographic approval.

Focused validation: Gate fixtures reject incomplete coverage, missing owner review, stale model identity, blank test groups and an aggregate gain hiding required per-case failures. Reproduce the actual three-line artifact from its frozen manifest.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: Cherry-picked words or post-hoc thresholds can make a poor hand appear successful. Freeze texts/configuration in advance, show all required cases and require the concrete visual review.

Rollback: Retain the best neutral baseline and mark the candidate unpromoted; do not export it into the guided track while G1 fails or is blocked.

Review estimate: 25 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Actual local evidence follows. The report and review template explicitly record missing real evaluation/review, not invented completion.

- [x] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [x] `tdd:red-green`: capture focused failing and passing test commands and results.
- [x] nominal three-line PNG and equal-scale source/baseline/candidate proof bundle
- [x] locked evaluation report, reviewer record and G1 decision
- [x] fresh-process replay hashes and diagnosed revision/stop decision
- [x] Record local integration checks separately from provider CI and owner review.
- [x] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

G1 rejects omitted or aliased text, stale artifacts, forged per-case summaries, contaminated unseen inventory and explicit appearance rejection. Missing evidence is blocked; adverse evidence fails. No production or guided-renderer defects are changed.

### Actual execution and decision

- Tidy assessment: a sibling `nominal.py` avoids expanding the baseline CLI; no production refactor was needed. The implemented commands replace only the proposed nominal hand-proof interface, not future guided integration.
- Red: missing-module gate tests failed before implementation (`e17067c`). Explicit visual-rejection and contaminated-unseen tests then failed before their fixes (`59fec28`).
- Green: 16 nominal tests passed, including a filesystem-backed positive scoring/review fixture with an explicitly mocked synthetic readiness boundary. Combined repertoire/recovery/reference/specimen/prior word tests passed 74 tests in 18.88 seconds. Synthetic reviewer identities are test data only.
- `python -m scribesim.handvalidate.nominal build --output shared/training/konrad_hand_recovery/nominal_specimen_v1` generated the frozen three-line and five-string bundle. Two fresh workers with PYTHONHASHSEED 7 and 917 produced identical rasters for both candidate and baseline across all eight cases. The three-line image was visually inspected; it remains visibly catalog-like, not accepted Konrad handwriting.
- The default diagnostic compares contextual catalog priors with a neutral catalog adapter, labeled as such. It does not substitute a seed for a recovered candidate or mislabel either as a production CLI baseline. The original benchmark reference sheet is copied unchanged.
- A real-corpus checkpoint requires matching dataset, contract, initial baseline, selected model and run configuration hashes. Freeze/config identities are written before locked scoring. The evaluator checks actual rendered pixels, exact shared word plans, replay artifacts, controls, live G0 and real per-case losses rather than trusting summary flags.
- Actual result: G1 blocked; no locked-test scores, no repeated/unseen reference losses, no independent readings and no owner acceptance. All eight schema-level mappings are exact, but that does not establish correct visible historical forms. No diagnosed revision or guided integration was attempted.
- Broader legacy checks: 13 passed and one folio benchmark failed because the existing exact guided renderer lacks a guide for uppercase H. No guided code changed; baseline verification is recorded below separately.
- `arrive plan check` passed. Strict PR check was executed and hit the same installed three-part-ID parsing limitation (ids=[]). No provider CI or owner review is claimed.

### Clean-checkout and baseline verification

- Feature checkpoint `5ae8781` was cloned locally without ignored workspace files into `/tmp/td018-nominal-clean.TdwAfK`. The seven focused/regression test files passed all 74 tests in 16.89 seconds; the committed specimen independently re-evaluated to the same blocked G1 result.
- The broader legacy folio failure was checked at pre-phase checkpoint `50c163c` in `/tmp/td018-baseline-audit.a4V8eY`. That clean baseline first failed because its handsim training manifest is ignored/untracked. After supplying the existing local handsim fixture via a symlink in the temporary audit checkout only, it reproduced the identical uppercase-H missing-guide failure and deterministic_pass_rate 0.0. Neither legacy issue was introduced or fixed by this phase.
- Earlier phase integration receipts: repertoire merge `0aff3ea`; recovery merge `06b163a`. This final Advance includes only a three-field recovery-export identity addition needed to bind a future real G1 checkpoint to its initial model, dataset and contract; historical synthetic run hashes retain their original execution provenance.
- The implementation outcome is complete; unchecked real-acceptance gates above remain intentionally unmet. The next action is reference admission/calibration/target review, not guided realism.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Which evidence distinguishes novel-word generalization from repeated-word reconstruction?
2. Can an experiment be complete while G1 still blocks the next stage?
