---
advance:
  id: ADV-SS-INK-002
  title: Ink Reservoir Model — InkState, Depletion, and Dip Timing
  system: scribesim
  primary_component: ink
  components:
  - ink
  - evo
  started_at: 2026-03-22T00:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-22T12:14:32.709Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence:
  - tidy:preparatory
  - tdd:red-green
  - tests:unit
  status: in_progress
---

## Objective

Implement the core `InkState` class (TD-010 Part 1) in `scribesim/ink/cycle.py`.
This is the state machine that drives the ink cycle: reservoir level decreases as
strokes are rendered, and the scribe dips between words when the reservoir runs low.
All downstream effects (darkness, width, hairline quality) depend on this model being
correct first.

## Behavioral Change

After this advance:
- `InkState` tracks `reservoir` (0.0–1.0), `strokes_since_dip`, `words_since_dip`,
  `total_dips`, and configurable physical properties (`capacity`, `base_depletion`,
  `viscosity`)
- `deplete_for_stroke(length_mm, avg_pressure, avg_width_mm)` reduces the reservoir
  using the formula from TD-010 §Part 1: `consumption = length * pressure * (width/2.0)
  * base_depletion / viscosity`
- `process_word_boundary()` checks `should_dip()` (reservoir < 0.15) and
  `wants_to_dip()` (reservoir < 0.22), performs the dip, and returns a `DipEvent`
  enum (`NoDip`, `PreferredDip`, `ForcedDip`)
- `dip()` restores reservoir to capacity and resets `strokes_since_dip` and
  `words_since_dip`
- The evo renderer's `render_word_from_genome()` accepts an `InkState` parameter;
  `render_line()` in `compose.py` creates a single `InkState` at the start and
  passes it through all words left to right, calling `process_word_boundary()` after
  each word
- At 300 DPI, a typical line render of 7 words should deplete the reservoir to
  roughly 0.55–0.70, and a full folio page (8–10 words × 28–32 lines) should
  produce 6–8 dips — matching the observed cycle in real manuscripts

## Planned Implementation Tasks

- [ ] Tidy: create `scribesim/ink/cycle.py` with `DipEvent` enum and `InkState` class
- [ ] Test: `test_ink_cycle.py` — verify depletion per stroke at known length/pressure/width; verify `should_dip()` triggers at reservoir ≤ 0.15; verify `wants_to_dip()` triggers at reservoir ≤ 0.22; verify `dip()` resets correctly; verify `process_word_boundary()` returns the right `DipEvent` at each threshold
- [ ] Implement: `InkState` class per TD-010 Part 1 spec
- [ ] Integrate: thread `InkState` through `render_word_from_genome()` — replace the current
  `ink_reservoir` local variable with the shared state object; call `deplete_for_stroke()`
  after each segment; call `process_word_boundary()` at each word boundary in `render_line()`
- [ ] Validate: add `verbose` logging of reservoir level and dip events to `render_line()`
  output; render the two Konrad test lines and confirm dip count and timing look plausible

## Risk + Rollback

**Risks:**
- The `base_depletion` rate (0.0008 per mm) is calibrated from TD-010 against
  reference manuscripts — may need tuning once darkness modulation (ADV-SS-INK-003)
  is in place and the visual effect is observable
- Threading `InkState` across words changes the signature of `render_word_from_genome()`;
  callers that pass no ink state should default to a fresh full reservoir

**Rollback:**
- `InkState` is a new module with no reverse dependencies; removing it restores prior
  behavior. The renderer falls back to the current `ink_reservoir` local variable.

## Evidence

- [ ] Tests in `tests/test_ink_cycle.py` covering depletion, dip thresholds, and word boundary events
- [ ] `render_line()` verbose output shows reservoir level and dip events per word
- [ ] Full 7-word Konrad line depletes reservoir to expected range (0.55–0.70)
