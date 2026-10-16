---
advance:
  id: "ADV-SS-STATE-002"
  title: "Coarticulated ScribeState, Ink Cycle & CLIO-7 Folio Modifiers"
  system: "scribesim"
  primary_component: "render"
  components: ["render", "handflow", "ink", "layout", "tests"]
  started_at: "2026-10-16T04:45:00+00:00"
  implementation_completed_at: 2026-10-16T19:21:01.573218Z
  review_time_estimate_minutes: 35
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence: ["tidy:preparatory", "tdd:red-green", "tests:unit"]
  # Populated by `arrive usage import` / the LiteLLM callback — leave empty when authoring.
  model_usage: []
  status: complete
---

## Objective

Integrate temporally coherent `ScribeState` modulation (`TD-017`), continuous contact-distance ink reservoir depletion and dip surges (`TD-010`), and `CLIO-7` per-folio apparatus overrides (`f06r` lateral pressure, `f07r` multi-sitting ink reloads, `f07v` smaller working register, `f14r+` wider compensating spacing) into the kinematic via-point word and line composer.

Follows [TD-019 — Kinematic Coarticulation, Bastarda Proportions, and Hybrid Evaluation](../../../../docs/tech-direction/TD-019-kinematic-coarticulation-and-evaluation.md) (§2 Diagram Step 2, §4 Tier 1 `A5-ANTI-CLONE`, §5 Phase 16c).

## Behavioral Change

After this advance:
- Repeated letters and words across a line or folio (`und ... und`, `in ... in`) are never pixel-identical (`A5-ANTI-CLONE` passes): `ScribeState` applies a seeded, slowly drifting correlated random walk to via-point offsets ($\pm 0.05\,H$), tempo, baseline wander, and nib angle ($\pm 2.5^\circ$) before the word's minimum-jerk trajectory is solved, so variation reshapes the continuous gesture naturally rather than adding salt-and-pepper noise.
- `InkState` depletes continuously by on-surface arc length and pressure, producing realistic post-dip darkness surges, gradual tonal decay within a dip cycle, and sitting-boundary reloads on `f07r`.
- `CLIO-7` apparatus notes automatically modulate the kinematic solver and nib parameters on `f06r`, `f07r`, `f07v`, and `f14r–f17v`.

## Component Impact

Primary component: `render`. Impacted components: `render`, `handflow`, `ink`, `layout`, `tests`.

- `scribesim/render/scribe_state.py` (via-point motor memory walk and `CLIO-7` folio modifier adapter for the kinematic pipeline)
- `scribesim/handflow/coarticulate.py` (line and folio session runner carrying persistent hand state, velocity, and `InkState` across words and lines)
- `scribesim/handvalidate/kinematic_gates.py` (Tier-1 `A5-ANTI-CLONE` DTW instance-variation check)
- `tests/test_kinematic_state.py` (unit tests for determinism, anti-cloning, ink depletion, and `CLIO-7` folio overrides)

## Dependencies

- [ADV-SS-TUNING-002](ADV-SS-TUNING-002.md)
- [ADV-SS-STATE-001](ADV-SS-STATE-001.md)

## Planned Implementation Tasks

- [x] branch: create or confirm feature branch for this advance (`feat/adv-ss-state-002`)
- [x] tidy: unify `InkState` arc-length consumption interface between `scribesim/ink/cycle.py` and `scribesim/render/scribe_state.py` (no behavior change)
- [x] test: add failing unit tests for `A5-ANTI-CLONE` (positive bounded DTW distance between repeated words and word-initial letters), continuous contact-distance ink depletion without excessive fading, and measurable `CLIO-7` deltas on `f06r`, `f07r`, `f07v`, and `f14r`
- [x] feat/fix: wire `KinematicScribeSession`, word-initial attack + cross-word air momentum carryover, `InkState`, and `CLIO-7` modifiers into the kinematic line/folio composer

## Bug Fixes

- [x] Scoped `f07v` working-register compression (`x_height = 0.85 * 3.5mm`, `letter_spacing_norm = 0.92`) to `line_index >= 16` (`apply_from_line = 16`) so upper vs. lower halves of `f07v` reflect the CLIO-7 apparatus transition accurately.

## Risk + Rollback

- Risk: Excessive ink depletion caused unreadable fading in earlier Pass 15 synthetic G3 experiments (`ink-three-line.png`). Mitigate by enforcing the `TD-017` darkness floor ($\ge 0.38$) and triggering natural word-boundary dips when reservoir drops below $0.20$.
- Rollback: Disable state drift flags in `ScribeState` (`use_state=False`) to return to neutral kinematic rendering.

## Evidence

- [x] tidy:preparatory
- [x] tdd:red-green
- [x] tests:unit

## CI Evidence Notes

- If CI jobs are enabled, link pipeline evidence (`ci:passed`) from PR/MR and default-branch runs.
- If CI jobs are temporarily disabled, run checks externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-STATE-002 --status passed` (include provider/run metadata when available)
  - Optional combined flow when provider lookup is available:
    - `arrive pr check --provider-status --advance ADV-SS-STATE-002 --record-ci-evidence --json`

## Changes Made

### 2026-10-16 - docs: Draft ADV-SS-STATE-002 for TD-019 Pass 16c
- `arrive/systems/scribesim/advances/ADV-SS-STATE-002.md`: Created planned advance record for Coarticulated ScribeState, Ink Cycle, and CLIO-7 Folio Modifiers.

### 2026-10-16 - tidy: unify InkState arc-length consumption and process-stable seeding in ScribeState
- `scribesim/render/scribe_state.py`: Added `_stable_seed()` using `hashlib.sha256` and `ScribeState.consume_contact_distance()`.
- `arrive/systems/scribesim/components/tests.yaml`: Added path selectors for `tests/test_kinematic_state.py` and `tests/test_tier2_bench.py`.

### 2026-10-16 - test: add word-initial attack, cross-word momentum, ink depletion, CLIO-7, and A5-ANTI-CLONE tests
- `tests/test_kinematic_state.py`: Added unit tests covering word-initial letter variation across same-initial words (`alle`, `alleine`, `an`), Tier-1 `A5-ANTI-CLONE` gate and determinism, continuous contact-distance ink depletion + `f07r` sitting boundaries, and `CLIO-7` folio overrides (`f01r`, `f06r`, `f07v`, `f14r`).

### 2026-10-16 - feat: implement KinematicScribeSession, word-initial attack, CLIO-7 modifiers, and A5-ANTI-CLONE gate
- `scribesim/render/scribe_state.py`: Implemented `KinematicScribeSession` (correlated AR(1) motor-memory walk, word-initial entry hook + cross-word air arrival carryover, sitting boundary reloads) and `resolve_clio7_kinematic_profile()`.
- `scribesim/handflow/coarticulate.py`: Implemented `compose_line_kinematic_Stateful()` and wired `KinematicScribeSession` into `solve_word_coarticulation()` and `compose_text_kinematic()`.
- `scribesim/handvalidate/kinematic_gates.py`: Implemented `evaluate_a5_anti_clone()`.

## Check for Understanding

1. How does `KinematicScribeSession.next_letter_variation()` address the Checkpoint #2 observation that word-initial letters (`is_word_initial=True`) previously looked too similar across words starting with the same letter?
2. Why does `ScribeState` use `_stable_seed()` (`hashlib.sha256`) rather than Python's built-in `hash()` for seeding per-folio and per-occurrence random walks?
3. How does `resolve_clio7_kinematic_profile()` differentiate the upper and lower halves of `f07v` and the multi-sitting reloads of `f07r`?

