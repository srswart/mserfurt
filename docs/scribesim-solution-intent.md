# Solution Intent — ScribeSim (Phase 1)

This document captures **how we intend to solve** Phase 1 (architecture + constraints). It is not a task plan and not an outcome record.

## Phase 1 intent
Produce a `scribesim` tool that takes XL folio JSON for *MS Erfurt Aug. 12°47* and renders Brother Konrad's scribal hand — a mid-fifteenth-century German Bastarda with per-folio emotional and physical variation — onto page images with pixel-accurate ground truth.

## Core decisions
### Implementation language (Stage 0)
- **Python** for orchestration: CLI, layout engine, hand parameter management, per-folio CLIO-7 override computation, ground truth export.
- **Rust** (via PyO3/maturin) for the stroke renderer: Bézier rasterization, pressure-to-width computation, ink flow simulation, image compositing.
- The Rust crate (`scribesim_render`) exposes a minimal API: accept a list of stroke commands with per-stroke pressure/ink parameters, return a pixel buffer and glyph bounding box list.

### Rendering approach
- **Stroke-based, not font-based.** Each glyph is a sequence of named Bézier strokes with pressure profiles. This is non-negotiable: Brother Konrad himself describes the difference between his hand and the press in terms of stroke pressure variation ("the slight thickening of a stroke when my attention deepened"). The rendering must model exactly what he describes.
- The "virtual nib" model: at each sample point along a Bézier curve, stroke width = `nib_width × pressure(t)` and darkness = `ink_flow(t)`. The nib is held at a fixed angle (40° for Bastarda), producing characteristic thick/thin variation by stroke direction.

Rationale:
- Font rendering cannot produce within-glyph pressure variation.
- Stroke decomposition enables the per-folio hand modulation that CLIO-7 describes.
- The pressure heatmap (a byproduct of stroke rendering) drives Weather's ink degradation model.

### Hand variation architecture
Rather than separate hand models per folio, ScribeSim uses a **base hand + modifier stack**:

```
final_hand(folio) = base_hand + Σ modifiers(folio.hand_notes)
```

Each modifier is a function that adjusts specific parameters:
- `pressure_increase(factor)` — scales pressure curve (f06r: agitation)
- `ink_density_shift(boundaries)` — inserts sitting breaks with ink reload (f07r: multi-sitting)
- `hand_scale(factor)` — reduces overall glyph size (f07v lower: smaller working hand)
- `spacing_drift(rate)` — widens letter/word spacing progressively (f14r: compensating)
- `tremor(amplitude, frequency)` — adds low-frequency noise to stroke paths (f14r: physical difficulty)

This stack is computed from XL's `hand_notes` field automatically. Custom modifiers can be added per folio.

## Scribal hand model — Brother Konrad
### Base hand parameters (TOML)
```toml
[identity]
name = "Konrad_Erfurt_1457"
script_family = "Bastarda"
period = "mid_15th_century"
region = "Thuringia"
character = "professional_scriptorium"

[nib]
angle_degrees = 40
width_min = 0.8
width_max = 2.0

[letterform]
slant_degrees = 5
x_height = 1.0
ascender_ratio = 1.6
descender_ratio = 0.5
# Bastarda-specific: moderate contrast between thick and thin strokes
# less angular than Textualis, more formal than pure Cursiva

[spacing]
letter_spacing_mean = 0.28
letter_spacing_stddev = 0.04
word_spacing_mean = 1.1
word_spacing_stddev = 0.10

[pressure]
# Konrad's base pressure: controlled professional hand
attack_duration = 0.12
sustain_level = 0.80
release_duration = 0.18
# Downstroke emphasis (characteristic of trained scribe)
downstroke_multiplier = 1.3

[ink]
flow_initial = 1.0
flow_decay_rate = 0.015
dip_cycle_strokes = 45

[fatigue]
enabled = false   # base hand has no fatigue; f14r modifier enables it
```

### Per-folio modifier mapping (from CLIO-7 apparatus)
```toml
# f06r: "increased lateral pressure on downstrokes, consistent with
#        either agitation or fatigue at time of writing"
[folio_overrides.f06r]
modifiers = ["pressure_increase"]
pressure_increase_factor = 1.25
pressure_increase_target = "downstrokes"

# f07r: "written across multiple sittings — ink density varies in ways
#        consistent with the pen being set down and resumed several times"
[folio_overrides.f07r]
modifiers = ["ink_density_shift"]
sitting_boundaries = [8, 17, 25]   # line numbers where sittings break
ink_reload_boost = 0.15

# f07v_lower: "Hand returns to the author's standard scriptorium register
#             — smaller, more economical"
[folio_overrides.f07v]
modifiers = ["hand_scale"]
scale_factor = 0.85
apply_from_line = 16   # lower half of folio

# f14r onward: "slower than in earlier sections — letterforms remain precise
#              but are more widely spaced, consistent with a writer
#              compensating for some physical difficulty"
[folio_overrides.f14r]
modifiers = ["spacing_drift", "tremor"]
spacing_drift_rate = 0.008    # per-line increase
tremor_amplitude = 0.003
tremor_frequency = 0.4

[folio_overrides.f15r]
modifiers = ["spacing_drift", "tremor"]
spacing_drift_rate = 0.010
tremor_amplitude = 0.004
tremor_frequency = 0.4

# ... similar for f15v through f17v, progressively increasing
```

## Glyph catalog — German Bastarda (Phase 1)
### Lowercase
Standard Latin a–z plus:
- Long s (ſ) — used word-initially and word-medially
- Round s — used word-finally
- ß or ſz ligature
- Umlauted vowels: ä, ö, ü rendered as base vowel + superscript e (the fifteenth-century convention, not modern diacritics)
- w — the double-v form characteristic of German scripts

### Uppercase
Simplified Bastarda capitals A–Z. These are less elaborate than Textualis capitals — Konrad is writing a private manuscript, not a presentation copy.

### Latin-specific
When register = `la`, use:
- No umlaut forms (no ä/ö/ü)
- Classical ae/oe digraphs where appropriate
- Different abbreviation conventions (see below)

### Abbreviation marks (Phase 1 minimum)
- Nasal bar (macron over m/n omission)
- Tironian et (⁊) for "und"/"et"
- Common suspensions: q; → que, p̄ → per/pre
- Superscript vowels for Latin abbreviations
- Note: XL Phase 1 produces expanded text. Phase 2 will add abbreviation compression, and ScribeSim will render compressed forms then. For now, full letterforms only.

### Special characters
- ✦ section divider — rendered as a simple three-dot pen flourish
- Paragraph mark (¶) — optional, for section starts
- Cross (✝) — if used in devotional passages

## Layout model
### Page dimensions
- Standard folios (f01–f13): ~280 × 400 mm (matching a typical large-quarto gathering)
- Final folios (f14–f17): ~240 × 340 mm ("smaller, cut unevenly, as though taken from a sheet intended for something else")
- DPI: 300 (configurable)

### Ruling
- Dry-point ruling (invisible in the final image but guides line placement)
- Standard folios: 30–32 lines per page
- Final folios: 26–28 lines (wider spacing per CLIO-7)
- Margins: top ~25mm, bottom ~70mm, inner ~25mm, outer ~50mm (standard for a private manuscript of this period)

### Line breaking
- Knuth-Plass algorithm adapted for variable glyph widths
- Prefer breaking at word boundaries
- Respect XL's line assignments as soft constraints
- Hyphenation follows fifteenth-century German conventions (break at syllable boundaries, mark with `=` at line end)

### Lacuna rendering
- Where XL marks a lacuna with type "water_damage": render partial text that fades/trails off, as though ink was dissolved
- Where XL marks "missing_corner": render text only within the surviving area (ScribeSim computes the text boundary; Weather will actually remove the corner)
- Where XL marks "reconstructed" or "speculative": render normally (these are CLIO-7's interpretive categories, not physical damage)

## Rendering pipeline (Phase 1)
### Stages
1. **Load + configure**: parse folio JSON, load base hand, compute per-folio modifier stack
2. **Line breaking**: distribute folio text into lines at target density
3. **Glyph placement**: decompose characters into stroke sequences, position along baselines with spacing from (modified) hand parameters
4. **Stroke rendering** (Rust): evaluate Bézier curves, apply pressure/ink models, rasterize to pixel buffer + pressure heatmap
5. **Sitting-boundary rendering** (f07r): at sitting boundaries, simulate ink reload (slight density increase) and possible baseline drift
6. **Ground truth extraction**: compute glyph bounding polygons, baselines, emit PAGE XML
7. **Export**: PNG + PAGE XML + pressure heatmap

## Determinism + reproducibility
- All stochastic processes (spacing jitter, tremor noise) use seeded PRNG.
- Default seed: hash of folio ID, so each folio is distinct but reproducible.
- Explicit `--seed` flag for testing.

## eScriptorium integration
### Image import
- PNG at 300 DPI with DPI metadata
- Naming: `{folio_id}.png`

### Ground truth
- PAGE XML 2019 schema
- Hierarchy: `Page > TextRegion > TextLine > Word > Glyph`
- `<Baseline>` elements on each `<TextLine>` (Kraken-compatible)
- `<TextEquiv>` at TextLine level: full line text in German/Latin
- `<TextEquiv>` at Glyph level: single Unicode character
- Register tag as custom attribute on `<TextLine>`: `@register="de|la|mixed"`

### Kraken compatibility
- Baselines match Kraken's expected format
- Glyph segmentation enables character-level training data
- ScribeSim output can serve as synthetic training data for Bastarda HTR models

## Testing strategy (Phase 1)
- **Stroke tests:** known Bézier input → expected pixel coverage
- **Glyph catalog tests:** every glyph → valid stroke sequence → renders cleanly
- **German-specific glyph tests:** ſ, ß, ä/ö/ü-with-superscript-e render correctly
- **Hand modifier tests:** base hand + pressure_increase → measurably thicker downstrokes; base + tremor → path deviation within bounds
- **Sitting boundary tests (f07r):** ink density shift visible at specified line boundaries
- **Layout tests:** text fits within page margins, no overflow
- **Ground truth IoU tests:** rendered glyph bounding polygon IoU ≥ 0.95 against actual pixels
- **Determinism tests:** same input + seed → bitwise identical PNG
- **Integration test:** XL folio JSON → ScribeSim render → eScriptorium import without error

Development discipline:
- default commit sequence: tidy → test → implement

## Repository layout (suggested)
- `scribesim/` (Python package)
  - `cli.py`
  - `hand/` — base hand loading, modifier stack computation
  - `glyphs/` — glyph decomposition (German Bastarda, Latin, special chars)
  - `layout/` — page layout, ruling, line breaking
  - `groundtruth/` — PAGE XML generation
  - `models/` — data classes
- `scribesim-render/` (Rust crate, PyO3)
  - `src/bezier.rs`, `src/rasterize.rs`, `src/pressure.rs`, `src/ink.rs`, `src/compositor.rs`
- `hands/`
  - `konrad_erfurt_1457.toml` — Brother Konrad's base hand
  - `folio_overrides.toml` — CLIO-7-derived per-folio modifiers
- `layouts/`
  - `ms_erfurt_standard.toml` — standard folio layout
  - `ms_erfurt_final.toml` — smaller final folios
- `glyphs/`
  - `bastarda_german.toml` — glyph decomposition definitions
- `examples/`, `tests/`, `docs/`

## Out of scope (Phase 1)
- Color rendering (Konrad's private manuscript is monochrome)
- Illustrations (there are none)
- Rubrication (this is not a commissioned work)
- Abbreviation-compressed forms (Phase 2, after XL Phase 2)
- Vellum texture or aging (Weather's domain)
- GPU rendering
