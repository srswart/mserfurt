---
advance:
  id: "ADV-SS-HANDFLOW-008"
  title: "Konrad Persistent Execution — Ink, Rhythm and Stable Session State"
  system: "scribesim"
  primary_component: "handflow"
  components: ["handflow", "ink", "hand", "handvalidate", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: "2026-09-06T03:30:46Z"
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence:
    - "shared/training/konrad_hand_recovery/persistent_execution_v1/synthetic/report.json"
    - "shared/training/konrad_hand_recovery/persistent_execution_v1/neutral_bridge/G2.json"
  model_usage: []
  status: complete
---

## Objective

Execute the accepted repertoire through the existing guided controller with one stable session state across strokes, words and lines, following TD-018 section 7.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
Implementation and synthetic evaluation are complete. Real persistent execution remains blocked by matching G1/G2 acceptance. No controller defaults or recovered hand are promoted.

## Behavioral Change

After implementation: Contact consumes ink, explicit word-boundary dips refill it, and slow bounded pressure/angle/rhythm changes affect the actual guided trajectory. Identical inputs and seed reproduce across fresh processes.

## Component Impact

Primary component: `handflow`. Impacted components:
`handflow`, `ink`, `hand`, `handvalidate`, `tests`.

Implemented paths:

- scribesim/handflow/controller.py and model.py (opt-in mode and persistent state)
- scribesim/handflow/execution.py and controls.py (orchestration and bounded explicit controls)
- Existing ink cycle/profile stay unchanged; explicit repertoire ink_per_mm avoids reinterpreting the legacy time-based depletion rate.
- scribesim/handvalidate/bridge.py (explicit neutral repertoire mode and gate inputs)
- tests/test_handflow_repertoire_state.py (new); focused ARRIVE test selector coverage

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-PATHGUIDE-005](ADV-SS-PATHGUIDE-005.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [x] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [x] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [x] test: establish failing behavioral tests for the contracts below before implementation.
- [x] feat/evaluate: Require G2 pass for the selected repertoire and audit existing guided activation before adding or changing any control.
- [x] feat/evaluate: Use HandStateV2 as the state owner and stable digest-derived local RNG streams keyed by explicit session seed and immutable identities.
- [x] feat/evaluate: Preserve state across glyph/word/line transitions; model air travel, pauses, line returns and sitting breaks as explicit events.
- [x] feat/evaluate: Wire reservoir consumption to contact arc length and bounded pressure; let word boundaries check for a dip and refill without resetting motor habits.
- [x] feat/evaluate: Activate only neutral-to-ink, pressure, nib-angle and rhythm controls initially; expose consumed units, events and control values in state traces.
- [x] feat/evaluate: Keep profile defaults compatible for existing paths; do not copy the plain ScribeState implementation or add speculative keyword-emotion inference.
- [x] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [x] Ink decreases on nonzero contact travel and not during air travel; increases require a recorded refill event.
- [x] Splitting a continuous plan into glyph/word/line containers does not reset reservoir, fatigue, timing or motor habit state.
- [x] Same-seed fresh-process renders and traces match; changed seeds produce bounded permitted variation without symbol changes.
- [ ] Real reviewed G2 quality/control acceptance is blocked. Synthetic neutral equivalence and control/replay contracts are exercised; G3 supplies the separate sensitivity evaluation.

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

Local synthetic evidence follows; no real-hand review or provider CI is claimed.

- [x] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [x] `tdd:red-green`: capture focused failing and passing test commands and results.
- [x] state/event traces for continuous writing, line returns and sitting breaks
- [x] neutral bridge and ink-enabled state proof; individual/combined control panels are produced by the dependent G3 Advance
- [x] fresh-process replay hashes and contact-consumption invariants
- [x] Record local integration checks separately from provider CI and owner review.
- [x] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

The new opt-in mode fixes the repertoire bridge’s major-width/nominal-pressure
contract and prevents time-based or duplicate ink consumption. Neutral continuous
plan partitions do not introduce hidden settling steps. Legacy defaults remain
unchanged; broader production renderer defects are not claimed as fixed.

### Execution outcome

- Authorized branch `feat/td018-persistent-execution`; no broad refactor or new motor controller. HandStateV2 owns reservoir, fatigue, time, habit phase, cumulative contact/consumption/refill, events and step traces. The existing GuidedHandFlowController receives a default-disabled repertoire_controls option; legacy behavior remains selected when omitted.
- Red: missing-module/state contracts failed before implementation (`fb2c001`). Green: 6 persistent-state tests and the combined guided/nominal set passed 48 tests in 13.59 seconds. Local digest-seeded streams replay under PYTHONHASHSEED 1 and 839; changing explicit seed changes permitted active output/state without changing model/text.
- Activation audit: legacy guided depletion was pressure-times-time, legacy nominal pressure added direction/rhythm/attack priors, and direction-dependent mark width was then used as a broad nib major width. The new opt-in contract uses declared nominal pressure and actual broad-nib major width. It does not change the legacy renderer or profile defaults.
- Ink has exactly one owner/consumption point in controller.step: actual contact distance times explicit units/mm times bounded pressure relative to 0.5. Air and stationary samples consume zero; only recorded dip events increase ink. Pauses/line returns/sitting breaks preserve state identity; dips do not reset motor habits. Continuous plans split into containers replay identically in neutral/ink mode without hidden settling steps.
- The synthetic three-line state run travelled 161.179944 mm in contact and consumed 0.475218516 reservoir units, with zero refills. Explicit sitting-break and word-boundary events remain in the trace. Forced-dip invariants are exercised separately in tests.
- `neutral_bridge/` reruns the three synthetic bridge cases with the opt-in nib contract: all synthetic numeric bounds now pass, but G2 remains blocked by G1 and synthetic scope. The earlier width-failure evidence is retained, not overwritten.
- Actual execution requires revalidated real G2 artifacts and live G1 identity; a hand-written pass summary cannot authorize execution. G2 must explicitly validate this neutral repertoire execution mode. `real_attempt/report.json` records refusal without execution.
- `arrive plan check` passes. Strict PR check was executed and hit the known installed three-part-ID parser limitation. No provider CI or human appearance approval has occurred.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Where is ink consumed, and what separate responsibility does a word boundary have?
2. How is state retained when layout starts a new line or a sitting resumes?
