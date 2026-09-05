---
advance:
  id: "ADV-SS-HANDVALIDATE-010"
  title: "Konrad Folio Evaluation — Four-Case Evidence and Rollout Decision"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "render", "groundtruth", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
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

Evaluate the opt-in candidate against G4 on clean, pressure-heavy, multi-sitting and late/failing-eyes folios, producing a concrete rollout recommendation.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
This is a planned outcome record. The timestamp records drafting; implementation
has not started and no execution, CI or owner approval is claimed.

## Behavioral Change

After implementation: The project receives a complete candidate-versus-baseline evidence bundle with exact text, geometry, state, appearance and downstream acceptance results. A default-renderer change remains a separate explicit release decision.

## Component Impact

Primary component: `handvalidate`. Impacted components:
`handvalidate`, `render`, `groundtruth`, `tests`.

Planned paths (new modules and commands are not available yet):

- scribesim/handvalidate/folio_bench.py (TD-018 gate/report integration)
- tests/test_repertoire_folio.py and focused handvalidate bench tests
- shared/training/konrad_hand_recovery/folio_candidate_v1/

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-RENDER-006](ADV-SS-RENDER-006.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [ ] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [ ] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [ ] test: establish failing behavioral tests for the contracts below before implementation.
- [ ] feat/evaluate: Freeze candidate/model/configuration and case mapping for f01r/f06r/f07r/f14r after inventory/hand-note validation.
- [ ] feat/evaluate: Render candidate and declared baseline on all four cases; inspect full pages and equal-scale crops, including worst-case joins and final lines.
- [ ] feat/evaluate: Check fresh-process deterministic replay, complete transcription, geometry/ink ownership, pressure maps, overflow and runtime.
- [ ] feat/evaluate: Run local Weather input/compositing acceptance without external image generation; report available downstream checks precisely.
- [ ] feat/evaluate: Record owner appearance review and G4 pass/fail/blocked with per-case reasons and unresolved limitations.
- [ ] feat/evaluate: Write the opt-in candidate recommendation, reproduction/rollback instructions and explicit statement that no default switch or expert historical approval is implied.
- [ ] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] All four required cases have exact text coverage, zero aliases/undeclared normalization and no silently clipped or omitted content.
- [ ] Actual image/XML/pressure agreement and local downstream contract checks pass for every case.
- [ ] Folio-specific effects have traceable configured causes and preserve the accepted hand; current XL case mapping is recorded.
- [ ] Owner review and all required evidence exist before G4 passes; missing external expertise is not replaced by a fabricated scholarly claim.
- [ ] The report recommends a release decision but does not change the CLI default or mark unrelated Advances complete.

Focused validation: Reject incomplete case bundles, omitted final lines, stale asset hashes, mismatched XML geometry and missing review. Run representative folio/groundtruth/Weather contract integration checks and report all actual failures.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: A pleasing page can conceal incorrect text, coverage gaps or broken downstream artifacts. Require complete case accounting and independent contract checks alongside the visual review.

Rollback: Retain evo and existing artifacts as the default; keep the candidate opt-in or unpromoted according to the gate decision.

Review estimate: 30 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Pending implementation; none of these evidence types is claimed as completed.

- [ ] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [ ] `tdd:red-green`: capture focused failing and passing test commands and results.
- [ ] four-folio source/baseline/candidate panels with PNG/XML/pressure sidecars
- [ ] G4 per-case report, actual downstream checks and reviewer record
- [ ] runtime/replay summary and opt-in release/rollback recommendation
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

1. Why does a G4 pass not itself switch the production renderer?
2. Which evidence prevents a visually pleasing but incomplete folio from passing?

