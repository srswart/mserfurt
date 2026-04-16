# TD-017 — ScribeState Machine: Temporally Coherent Scribal Variation

**Status**: proposed  
**Author**: srswart@gmail.com  
**Date**: 2026-04-17  
**Depends on**: TD-015 (polygon sweep renderer), TD-010 (ink cycle)

---

## Problem Statement

The current plain pipeline renders every occurrence of a glyph identically: same control points, same pressure curve, same nib angle. The output is legible but reads as a typeface. Random per-glyph jitter (tremor, Gaussian noise on sample points) was tried and makes the output look noisy and degraded rather than handwritten — a scribe's hand does not shake randomly.

What distinguishes a real manuscript from a stamped font is not noise but **temporal coherence**: the scribe's state drifts slowly across the page in physically motivated ways, and that drift imprints on every mark they make. A tired scribe at line 18 writes differently than the same scribe at line 1 — but consistently so, in a way traceable to cause (fatigue, ink level, emotional register of the text, speed under time pressure).

The goal is a `ScribeState` machine that generates smooth, causally grounded variation. Legibility must be preserved: the constraint is that every rendered line remains readable at normal viewing distance.

---

## Key Design Principle: Slow Variables, Not Random Noise

Random per-glyph noise produces salt-and-pepper variation with no coherent structure. Real scribal variation operates on three timescales:

| Timescale | What changes | Driven by |
|---|---|---|
| **Per-session** (across the whole folio) | Fatigue accumulation, ink dip cycle rhythm | Lines written, time at desk |
| **Per-passage** (across a text block) | Pressure intensity, writing speed | Emotional register of the Latin/German text |
| **Per-word** (word to word) | Baseline position, slight angle drift | Line rhythm, pen lift and re-engagement |

Individual glyph shape does vary — but within a stable **motor habit** for that letter. The scribe draws 'n' slightly differently each time, but the variation samples from a consistent personal distribution, not random jitter. This is modeled as slowly-drifting offsets to the canonical Bézier control points, not per-point noise.

---

## ScribeState Parameters

The state machine maintains a `ScribeState` dataclass that is updated as the renderer walks through lines and glyphs. All parameters are normalized to [0, 1] unless noted.

### 1. Fatigue (`fatigue: float`)

Accumulates monotonically from 0.0 (fresh) toward 1.0 (exhausted) across the session. A realistic value for a full folio page of ~25 lines is `fatigue_rate ≈ 0.025 per line`, reaching ~0.5 by page end. Already present as `fatigue_rate` in HandParams but not currently consumed by the renderer.

**Effect on rendering**:
- Increases baseline drift amplitude (lines sag slightly toward page bottom)
- Reduces nib angle precision (±1–2° drift grows to ±3–4°)
- Slightly increases stroke-start pressure (tired scribes press harder, compensating for shaking)
- Does NOT increase random noise — effects are smooth and line-correlated

### 2. Ink Level (`ink_level: float`)

Fraction of current reservoir (1.0 = just dipped, 0.0 = dry). Already modeled in `ink/cycle.py` for the evo renderer. The plain pipeline currently ignores this.

**Effect on rendering**:
- Stroke darkness scales with ink level (dark at 1.0, fading toward 0.15 as reservoir depletes)
- Below ~0.25: hairlines show split-nib gaps (rendered as occasional skipped quads)
- Dip events: brief darkness and width surge for the first 2–3 strokes after re-dipping

### 3. Passage Intensity (`intensity: float`)

The emotional weight of the text being written. This is the most novel dimension. A scribe copying a Psalter passage writes differently than copying a property list; theological climaxes in the Erfurt text (e.g., descriptions of divine union) show tighter spacing and heavier pressure.

This can be approximated from text features without NLP:
- Exclamation / rhetorical markers in the transcription annotations
- Sentence length (long sentences → sustained concentration → darker, steadier ink)
- Repeated key words flagged in the XL folio annotations

**Effect on rendering**:
- High intensity (>0.7): pressure ceiling rises, downstrokes are 10–15% darker, letter spacing tightens 5–8%
- Low intensity (<0.3): pressure loosens, strokes are lighter, baseline more relaxed

### 4. Writing Speed (`speed: float`)

How fast the scribe is moving through the text. Controlled by the `writing_speed` parameter in HandParams, but currently static across a folio.

**Effect on rendering**:
- Fast (>0.8): curves are slightly shallower (less time on curves), hairline entry strokes are shorter
- Slow (<0.5): more deliberate curves, thicker entry attacks, more precise nib angle

### 5. Motor Memory (`motor_memory: dict[str, ControlPointDrift]`)

The most important dimension for avoiding the "font" look. Each letter has a **personal form** for this scribe on this page — a slight lean, a preferred loop size, a characteristic entry angle. This form drifts very slowly across the page (one full drift cycle might take 30–40 lines).

Implementation: for each glyph ID, maintain a small vector of control point offsets (in x-height units, bounded to ±0.06). These offsets evolve via a correlated random walk with very small step size per line (σ ≈ 0.008 per line). The result is that the scribe's 'n' leans slightly more upright at line 5 than at line 1, reaches maximum lean at line 15, then gradually returns — a natural motor pattern, not noise.

The walk is seeded from `(folio_id, glyph_id)` so it is deterministic: the same folio always produces the same drift trajectory for the same letter.

---

## What This Is NOT

- **Not random jitter**: Every parameter evolves smoothly. The scribe at line N is a predictable function of the scribe at line N-1.
- **Not per-glyph noise**: Variation operates on timescales of lines and passages, not individual letters (except motor memory, which changes across dozens of lines).
- **Not illegibility**: Every parameter has a legibility ceiling. Fatigue maxes out at a level that still produces readable Bastarda. The system cannot produce output that looks damaged — that is the job of the Weather pipeline.
- **Not character substitution**: Allograph selection (which 'r' form, which 's' form) is a separate concern handled by the evo allograph system (TD-012). ScribeState modulates the *rendering* of whatever form is selected.

---

## Architecture

```
ScribeState
├── fatigue: float          # 0.0–1.0, monotonic, per-line update
├── ink_level: float        # 0.0–1.0, managed by InkState (ink/cycle.py)
├── intensity: float        # 0.0–1.0, per-passage, from text annotations
├── speed: float            # from HandParams, potentially dynamic
└── motor_memory: dict      # per-glyph control point drift, correlated walk

ScribeStateUpdater
├── update_for_line(line_index, line_text) → ScribeState
│   ├── increment fatigue by fatigue_rate
│   ├── advance motor_memory walk (per-glyph, tiny σ)
│   └── recompute intensity from line annotations if available
└── update_for_word_boundary() → ScribeState
    └── advance ink_level via InkState.process_word_boundary()

RenderingParams (derived from ScribeState + HandParams)
├── darkness_scale: float      # ink_level × intensity × stroke_weight
├── nib_angle_jitter_deg: float # grows with fatigue
├── baseline_offset_mm: float  # drifts with motor_memory, fatigue
└── control_point_offsets: dict # motor_memory → per-glyph Bézier deltas
```

The `ScribeState` is passed into `_render_at_internal_dpi` and used to parameterize each call to `_polygon_sweep_stroke`. The existing darkness formula:

```
dark = pressure × stroke_weight × ink_density × glyph_opacity
```

becomes:

```
dark = pressure × stroke_weight × ink_level × intensity_scale × glyph_opacity
```

And control points are offset before `sample_bezier`:

```
p0_actual = (p0[0] + motor_memory[glyph_id].dx0,
             p0[1] + motor_memory[glyph_id].dy0)
```

---

## Legibility Constraints

These are hard limits enforced regardless of state:

| Parameter | Floor | Ceiling |
|---|---|---|
| Darkness | 0.35 (still dark enough to read) | 1.0 |
| Baseline drift | −0.4mm | +0.4mm |
| Control point offset | −0.06 x-height | +0.06 x-height |
| Nib angle drift | −4° | +4° |

---

## Implementation Order

This TD is intended to be implemented as a single advance (ADV-SS-STATE-001) with the following sequence:

1. **Tidy**: extract `ScribeState` dataclass and `ScribeStateUpdater` into `scribesim/render/scribe_state.py`
2. **Test (red)**: assert that two renders of the same folio with a fresh `ScribeState` produce identical output (determinism); assert that rendering with `fatigue_rate=0.05` produces measurably different darkness on line 1 vs line 8
3. **Implement**: wire `ScribeState` into `_render_at_internal_dpi`; implement motor memory correlated walk
4. **Implement**: connect `InkState` from `ink/cycle.py` into the plain pipeline (it is currently only used in the evo renderer)
5. **Validate**: render f01r and f07r side-by-side; f07r has a known two-sitting structure (line 1–12 fresh ink, line 13+ re-dipped) — the tonal break should be visible without Weather processing

## Success Criteria

- Two consecutive renders of f01r with ScribeState are NOT pixel-identical (variation is present)
- But: any single line of the output is readable at 150 DPI without magnification
- The first line of a folio is measurably darker than the last (ink depletion visible)
- The letter 'n' at line 1 and line 8 have measurably different control point offsets, but both are recognisably 'n'
- No individual glyph has a control point offset exceeding 0.06 x-height units in any direction
