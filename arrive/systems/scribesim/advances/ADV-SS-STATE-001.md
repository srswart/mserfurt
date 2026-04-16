---
advance:
  id: ADV-SS-STATE-001
  title: ScribeState Machine — Temporally Coherent Scribal Variation
  system: scribesim
  primary_component: render
  components:
  - render
  - ink
  status: complete
  priority: high
  risk_flags:
  - rendering_change
  started_at: 2026-04-17T01:00:00Z
  started_by: srswart@gmail.com
  evidence: []
---

## Objective

Implement a `ScribeState` machine that evolves slowly across lines and words as
the renderer walks through a folio, producing variation that is causally grounded
and temporally coherent rather than per-glyph random noise.

The plain pipeline currently stamps every glyph identically. This advance wires
five slowly-varying state dimensions — fatigue, ink level, passage intensity,
motor memory, and nib angle drift — into `_render_at_internal_dpi` so that the
output looks like a specific person wrote it rather than a typeface.

Legibility is a hard constraint: all parameter limits are set so that every
rendered line remains readable at normal viewing distance.

## Behavioral Change

After this advance:

- Stroke darkness varies across the page as ink depletes between dips and
  refills on dip events. The first line after a dip is measurably darker than
  the last line before the next dip.
- The nib angle drifts ±0–3° across lines in a slow oscillation whose amplitude
  grows with fatigue, producing subtle but visible thick/thin variation that
  changes line to line.
- Each glyph has a personal form that drifts slowly across the folio via a
  seeded correlated random walk on interior control point offsets (±0.06
  x-height units max). The same glyph at line 8 looks slightly different from
  line 1 but is recognisably the same letter.
- Fatigue accumulates monotonically; `fatigue_rate` in the hand TOML now has
  visible effect (default 0.025 per line).
- All variation is deterministic: same folio + same hand params → same output.

## Planned Implementation Tasks

- [x] Create advance document
- [x] **Tidy**: extract `ScribeState` dataclass and `ScribeStateUpdater` into
      `scribesim/render/scribe_state.py`
- [x] **Test** (red→green): `tests/test_scribe_state.py` — 18 tests pass:
      determinism, fatigue accumulation, motor memory bounds, ink depletion,
      pipeline integration
- [x] **Implement**: wire `ScribeState` into `_render_at_internal_dpi`
- [x] **Implement**: `InkState` connected via `ScribeState`; `process_word_boundary()`
      called per word per line
- [x] **Validate** (human): f01r rendered; legible with visible variation across
      lines; not font-like

## Evidence

- [x] Determinism: two renders of f01r produce identical output
- [x] Motor bounds: 18/18 test_scribe_state.py pass including bounds tests
- [x] Human: f01r render shows visible variation across lines, legible
- [x] No regressions: 50/50 tests pass across test_scribe_state, test_render_pipeline, test_render_compositor
