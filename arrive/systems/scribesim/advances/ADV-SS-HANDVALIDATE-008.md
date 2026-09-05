---
advance:
  id: "ADV-SS-HANDVALIDATE-008"
  title: "Konrad Nominal Specimen — Unseen Words and Three-Line Acceptance"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "evo", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 25
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Evaluate the frozen repertoire against G1 and deliver the first concrete three-line specimen before any new controller realism work.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
This is a planned outcome record. The timestamp records drafting; implementation
has not started and no execution, CI or owner approval is claimed.

## Behavioral Change

After implementation: The project can inspect reconstruction, unseen combinations and manuscript text side by side, with exact coverage, per-word evidence and a recorded pass/fail/blocked decision that scalar loss cannot override.

## Component Impact

Primary component: `handvalidate`. Impacted components:
`handvalidate`, `evo`, `tests`.

Planned paths (new modules and commands are not available yet):

- scribesim/handvalidate/specimen.py (G1 evaluator and panels)
- tests/test_handvalidate_specimen.py
- shared/training/konrad_hand_recovery/nominal_specimen_v1/ (proofs, test report and review record)

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-EVOFIT-006](ADV-SS-EVOFIT-006.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [ ] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [ ] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [ ] test: establish failing behavioral tests for the contracts below before implementation.
- [ ] feat/evaluate: Freeze selected checkpoint/configuration and confirm G0 split/coverage artifacts before opening locked test inputs.
- [ ] feat/evaluate: Render the three proof lines plus at least five unseen strings, separating real referenced unseen words from unscored synthetic combinations.
- [ ] feat/evaluate: Report repeated-word and unseen-word losses, worst cases, mapping coverage, exclusions and fresh-process deterministic replay.
- [ ] feat/evaluate: Generate equal-scale randomized baseline/candidate panels with the fixed reference sheet and per-category appearance rubric.
- [ ] feat/evaluate: Capture owner appearance review and independent-reading status honestly; leave missing readings/review blocked without inventing approval.
- [ ] feat/evaluate: Issue G1 and a stop/revise/proceed recommendation after the initial run and at most one diagnosed revision; disclose test reuse and reserve a new test set for a subsequent version.
- [ ] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] Exact logical-to-visible coverage is 1.0 with zero aliases or undeclared normalization on the frozen proof inventory.
- [ ] All required G1 controls and fresh-process replay checks pass; metric tolerances were frozen before test inspection.
- [ ] The three-line appearance review records acceptable in all rubric categories and an overall preference to baseline before G1 passes.
- [ ] Unavailable independent readings are explicit; image agreement is never labeled OCR accuracy or paleographic approval.

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

Pending implementation; none of these evidence types is claimed as completed.

- [ ] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [ ] `tdd:red-green`: capture focused failing and passing test commands and results.
- [ ] nominal three-line PNG and equal-scale source/baseline/candidate proof bundle
- [ ] locked evaluation report, reviewer record and G1 decision
- [ ] fresh-process replay hashes and diagnosed revision/stop decision
- [ ] Record local integration checks separately from provider CI and owner review.
- [ ] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

None implemented in this planning change. Record scoped defects and their
regressions here during execution; do not imply unrelated renderer defects are fixed.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Which evidence distinguishes novel-word generalization from repeated-word reconstruction?
2. Can an experiment be complete while G1 still blocks the next stage?

