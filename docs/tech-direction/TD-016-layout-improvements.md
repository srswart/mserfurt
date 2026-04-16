# Tech Direction: TD-016 — Layout Improvements: Justification, Line Quality, and Spatial Realism

## Status
**Proposed** — depends on TD-015 (renderer working correctly). Start implementation only after ADV-SS-RENDER-005 is complete.

## Context

Once the renderer produces readable output (TD-015), the next visible quality gap will be in layout. The current `layout/linebreak.py` uses a greedy first-fit algorithm with no justification. Bastarda manuscript text is always justified — lines fill the full measure. The absence of justification is immediately recognizable and makes the output look like computer text rather than a manuscript page.

Secondary layout issues (baseline undulation, inter-word spacing variation, margin irregularity) matter less than justification and should follow after.

---

## Part 1: Justification

### Problem

Every rendered line is ragged-right. In the reference manuscript, lines uniformly reach the right margin. This is the single most recognizable marker that the output is synthetic.

### Approach: Post-fit proportional stretch

The Knuth-Plass algorithm mentioned in the solution intent is a full paragraph optimizer requiring hyphenation dictionaries and a penalty system. For Phase 1, a simpler approach produces 90% of the visual improvement:

**After first-fit line-breaking**, distribute the remaining whitespace proportionally across the inter-word gaps:

```python
def justify_line(words: list[PlacedWord], text_right_mm: float) -> list[PlacedWord]:
    if len(words) <= 1:
        return words  # single-word lines are never justified
    
    last_word_right = words[-1].x_mm + words[-1].width_mm
    remaining = text_right_mm - last_word_right
    
    if remaining <= 0:
        return words  # already fits
    
    n_gaps = len(words) - 1
    extra_per_gap = remaining / n_gaps
    
    result = [words[0]]
    cumulative_shift = 0.0
    for i, word in enumerate(words[1:], 1):
        cumulative_shift += extra_per_gap
        result.append(word.shifted_x(cumulative_shift))
    return result
```

Apply this after line-breaking, before rendering. The last line of a paragraph should **not** be justified (left-aligned only), matching historical convention.

### Constraint: minimum and maximum stretch

Impose a limit on how much justification can stretch a line:
- **Minimum stretch**: If `remaining / text_width < 0.01`, skip (the line is already nearly full).
- **Maximum stretch**: If `remaining / text_width > 0.30`, the line is too short to justify attractively. Apply the same left-alignment used for paragraph-final lines. (This can happen at section boundaries or when lacuna truncates a line.)

### Future: Knuth-Plass

Knuth-Plass would allow global paragraph optimization — choosing line breaks to minimize total badness rather than filling lines greedily. This is the right long-term approach (medieval scribes did optimize globally, adjusting word spacing across lines). Defer until the greedy approach is validated and Konrad's actual spacing preferences are better characterized from the reference manuscript.

---

## Part 2: Hyphenation at Line Ends

When a word is too long to fit on the remaining line, the greedy algorithm starts a new line. Medieval German scribes instead hyphenated, breaking the word at a syllable boundary and marking the break with `=` at the line end.

### Minimal implementation

For Phase 1, a syllable-boundary detector for Frühneuhochdeutsch is not required. Use a fallback heuristic:
- If a word is more than 1.5× the remaining space on the line, do not hyphenate — start a new line.
- If the word is between 1.0× and 1.5× remaining, attempt to hyphenate at the last consonant-vowel boundary before the overflow point.
- If no syllable boundary is found, start a new line without hyphenation.

The hyphenation marker `=` is rendered as two short diagonal strokes, not a keyboard hyphen. A dedicated glyph entry `=` should be added to `GLYPH_CATALOG` for this purpose.

### Latin text

Latin text (register `la`) uses different hyphenation conventions. For Phase 1, apply the same heuristic — Latin syllabification is complex enough to defer.

---

## Part 3: Baseline Undulation

The reference manuscript shows slight baseline waviness — not tremor (random noise at high frequency) but gentle line-level undulation (long-period sinusoidal variation within a single line). This is distinct from the folio-f14r tremor modifier.

### Model

Each line gets an independent, seeded undulation:
```python
def baseline_undulation(x_mm: float, line_seed: int,
                        amplitude_mm: float = 0.3,
                        period_mm: float = 80.0) -> float:
    """Return y offset in mm at horizontal position x_mm."""
    import math, random
    rng = random.Random(line_seed)
    phase = rng.uniform(0, 2 * math.pi)
    return amplitude_mm * math.sin(2 * math.pi * x_mm / period_mm + phase)
```

Apply the y offset to each glyph's `baseline_y_mm` as a function of its x position. Default amplitude is 0.3mm (about 3–4 pixels at 300 DPI — subtle but visible).

This is separate from the line-position imprecision already implemented in the movement model. That handles where the scribe *started* the line; undulation handles how the pen *drifted* during the line.

---

## Part 4: Inter-Word Spacing Variation

The hand profile defines `word_spacing_mean` and `word_spacing_stddev`. These are applied per-word at layout time. Currently the mean is applied uniformly after justification overrides everything anyway.

The correct order:
1. Draw word spacings from the normal distribution (seeded per line).
2. Run first-fit line-breaking using these variable spacings.
3. Apply justification stretch to the *residual* after variable spacing, not to the nominal spacing.

This ensures variable spacing survives into the final layout rather than being nulled out by justification.

### Target distribution (from reference manuscript measurement)

From visual inspection of the reference samples in `docs/samples/`:
- Median inter-word gap: approximately 1.0–1.2× x-height
- Standard deviation: approximately ±0.15× x-height
- Occasional tight words (0.7× x-height) where Konrad compressed to fit a line
- Rare wide words (1.5× x-height) at line ends before justification

The `word_spacing_mean = 1.1` and `word_spacing_stddev = 0.10` in the base hand TOML are reasonable starting points. Do not change them until the renderer is producing readable output and the spacing can be perceptually compared.

---

## Part 5: Margin Irregularity

The left margin in historical manuscripts is not perfectly straight. Scribes used dry-point ruling lines as guides, but the actual letter starts (especially tall capitals and ascenders) could overhang the margin slightly or retreat from it.

### Model

Add a small random left-margin offset per line, drawn from a tight normal distribution:
- `left_margin_jitter_mm`: mean=0, stddev=0.5mm
- Clamp to [-1.5mm, +1.5mm]

Apply before line layout. This is a very small effect — its primary purpose is eliminating the unnaturally straight left margin that reads as computer-generated even when the text content is realistic.

### Right margin

The right margin irregularity is produced naturally by justification constraints (some lines can't fully justify) and is not separately modeled.

---

## Implementation Order

1. **ADV-SS-LAYOUT-001** — Justification (proportional inter-word stretch). Depends on: ADV-SS-RENDER-005 complete.
2. **ADV-SS-LAYOUT-002** — Baseline undulation. Depends on: ADV-SS-LAYOUT-001.
3. **ADV-SS-LAYOUT-003** — Hyphenation heuristic + `=` glyph. Depends on: ADV-SS-LAYOUT-001.
4. **ADV-SS-LAYOUT-004** — Inter-word spacing variation + margin jitter. Depends on: ADV-SS-LAYOUT-001.

Items 2, 3, and 4 are independent of each other once item 1 is in place.

---

## Dependency Chain

```
TD-015 (renderer consolidation)
  ↓
TD-016 (layout improvements) ← YOU ARE HERE
  ↓
TD-003 (full parameter tuning — now can tune against readable output)
TD-004 Part 1 calibration (stroke width ratios, now perceptually verifiable)
```

---

## Revision History

| Date | Change | Author |
|---|---|---|
| 2026-04-16 | Initial — layout quality improvements following renderer consolidation | shawn + claude |
