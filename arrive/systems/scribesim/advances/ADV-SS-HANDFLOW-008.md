---
advance:
  id: "ADV-SS-HANDFLOW-008"
  title: "Konrad Persistent Execution — Ink, Rhythm and Stable Session State"
  system: "scribesim"
  primary_component: "handflow"
  components: ["handflow", "ink", "hand", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
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

Execute the accepted repertoire through the existing guided controller with one stable session state across strokes, words and lines, following TD-018 section 7.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
This is a planned outcome record. The timestamp records drafting; implementation
has not started and no execution, CI or owner approval is claimed.

## Behavioral Change

After implementation: Contact consumes ink, explicit word-boundary dips refill it, and slow bounded pressure/angle/rhythm changes affect the actual guided trajectory. Identical inputs and seed reproduce across fresh processes.

## Component Impact

Primary component: `handflow`. Impacted components:
`handflow`, `ink`, `hand`, `tests`.

Planned paths (new modules and commands are not available yet):

- scribesim/handflow/session.py, controller.py, planning.py and model.py
- scribesim/ink/cycle.py and scribesim/hand/profile.py (minimal compatible state integration)
- tests/test_handflow_repertoire_state.py (new); focused ARRIVE test selector coverage

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-PATHGUIDE-005](ADV-SS-PATHGUIDE-005.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [ ] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [ ] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [ ] test: establish failing behavioral tests for the contracts below before implementation.
- [ ] feat/evaluate: Require G2 pass for the selected repertoire and audit existing guided activation before adding or changing any control.
- [ ] feat/evaluate: Use HandStateV2 as the state owner and stable digest-derived local RNG streams keyed by explicit session seed and immutable identities.
- [ ] feat/evaluate: Preserve state across glyph/word/line transitions; model air travel, pauses, line returns and sitting breaks as explicit events.
- [ ] feat/evaluate: Wire reservoir consumption to contact arc length and bounded pressure; let word boundaries check for a dip and refill without resetting motor habits.
- [ ] feat/evaluate: Activate only neutral-to-ink, pressure, nib-angle and rhythm controls initially; expose consumed units, events and control values in state traces.
- [ ] feat/evaluate: Keep profile defaults compatible for existing paths; do not copy the plain ScribeState implementation or add speculative keyword-emotion inference.
- [ ] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] Ink decreases on nonzero contact travel and not during air travel; increases require a recorded refill event.
- [ ] Splitting a continuous plan into glyph/word/line containers does not reset reservoir, fatigue, timing or motor habit state.
- [ ] Same-seed fresh-process renders and traces match; changed seeds produce bounded permitted variation without symbol changes.
- [ ] Neutral output retains G2 quality, and every claimed active control affects the reviewed guided path.

Focused validation: Exercise known-length strokes, zero-length events, air travel, forced/preferred dips, pause/resume and multi-line carryover. Run subprocesses with different Python hash seeds and verify stable replay.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: State can be reset or consumed twice across controller/render boundaries, and variation can damage legibility. Assign one owner and one consumption point, trace every transition, and bound each activated control.

Rollback: Select the neutral accepted guided profile and disable the new opt-in activation bundle; retain model and trace evidence.

Review estimate: 35 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Pending implementation; none of these evidence types is claimed as completed.

- [ ] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [ ] `tdd:red-green`: capture focused failing and passing test commands and results.
- [ ] state/event traces for continuous writing, line returns and sitting breaks
- [ ] neutral and single-control proof panels
- [ ] fresh-process replay hashes and contact-consumption invariants
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

1. Where is ink consumed, and what separate responsibility does a word boundary have?
2. How is state retained when layout starts a new line or a sitting resumes?

