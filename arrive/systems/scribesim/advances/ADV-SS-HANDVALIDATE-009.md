---
advance:
  id: "ADV-SS-HANDVALIDATE-009"
  title: "Konrad Expressive Specimen — Controlled Variation and G3 Evaluation"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "handflow", "tests"]
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

Establish whether coherent state improves the accepted three-line specimen while preserving its letterforms, text and nominal quality.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
This is a planned outcome record. The timestamp records drafting; implementation
has not started and no execution, CI or owner approval is claimed.

## Behavioral Change

After implementation: Each expressive control is classified as inactive, active-safe or active-unsafe using its actual output and state trace. G3 combines deterministic checks, bounded variation and concrete appearance review.

## Component Impact

Primary component: `handvalidate`. Impacted components:
`handvalidate`, `handflow`, `tests`.

Planned paths (new modules and commands are not available yet):

- scribesim/handvalidate/specimen.py (G3 and sensitivity evaluation)
- tests/test_handvalidate_specimen.py and tests/test_handflow_repertoire_state.py
- shared/training/konrad_hand_recovery/expressive_specimen_v1/

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-HANDFLOW-008](ADV-SS-HANDFLOW-008.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [ ] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [ ] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [ ] test: establish failing behavioral tests for the contracts below before implementation.
- [ ] feat/evaluate: Reuse the accepted G1/G2 proof inventory and freeze control bounds before evaluating expressive candidates.
- [ ] feat/evaluate: Render neutral, one-control-at-a-time and combined variants over three explicit seeds at equal scale.
- [ ] feat/evaluate: Measure contact/dip consistency, pressure/width/angle/spacing deltas, corridor deviation and text coverage separately from appearance.
- [ ] feat/evaluate: Compare same-seed fresh-process replays and changed-seed variants; flag inert knobs and unsafe combinations.
- [ ] feat/evaluate: Record owner rubric decisions for the expressive specimen and issue G3 with offending controls and rollback recommendations.
- [ ] feat/evaluate: Reuse useful sensitivity concepts from HANDVALIDATE-006 without claiming that its broader deferred scope is complete.
- [ ] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] G1 text/appearance and G2 trajectory requirements remain satisfied on required proof cases.
- [ ] Claimed controls produce the intended measurable trace and visible output changes within frozen bounds; inert controls cannot count as success.
- [ ] Three seeds preserve one coherent hand; all same-seed fresh-process replays match.
- [ ] Every rubric category is acceptable before G3 passes; pressure range alone never determines the appearance verdict.

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

Pending implementation; none of these evidence types is claimed as completed.

- [ ] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [ ] `tdd:red-green`: capture focused failing and passing test commands and results.
- [ ] neutral/individual/combined three-line comparison bundle
- [ ] per-control sensitivity matrix and multi-seed state reports
- [ ] G3 reviewer record, replay evidence and stop/proceed decision
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

1. How is an active but harmful control distinguished from an inactive one?
2. What evidence makes coherent variation different from a larger pixel difference?

