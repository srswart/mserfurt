# Tech Direction: TD-015 — Renderer Consolidation: Polygon Sweep as Canonical Approach

## Status
**Active** — prerequisite for any further scribesim quality work. All rendering work should target the approach defined here.

## Context

The current codebase contains two independent rendering implementations that were never reconciled:

- **`render/pipeline.py`** — "standard" pipeline using `PIL.ImageDraw.ellipse()` stamps at each Bézier sample point
- **`evo/renderer.py`** — evolutionary renderer using filled polygon sweeps between adjacent nib positions

The standard pipeline is architecturally broken and must be replaced. The evolutionary renderer has the correct core approach but a coordinate composition bug that puts all text in the top-left corner of the page. This TD defines the canonical approach, the coordinate fix, and a diagnostic tooling requirement that must gate all further rendering work.

---

## Part 1: Why Ellipse Stamping Fails

`PIL.ImageDraw.ellipse()` draws only axis-aligned ellipses. The bounding-box argument is `[x0, y0, x1, y1]` — there is no rotation parameter. The nib-angle math in `render/pipeline.py:111–114` computes `cos_a`, `sin_a`, `dx`, `dy` and then discards the rotation by constructing an axis-aligned bounding box:

```python
cos_a = math.cos(nib_angle_rad)
sin_a = math.sin(nib_angle_rad)
dx = math.sqrt((semi_maj * cos_a) ** 2 + (semi_min * sin_a) ** 2)
dy = math.sqrt((semi_maj * sin_a) ** 2 + (semi_min * cos_a) ** 2)
bbox = [x_px - dx, y_px - dy, x_px + dx, y_px + dy]
draw.ellipse(bbox, fill=...)
```

The result is a circle-ish blob at each sample point, oriented identically regardless of stroke direction or nib angle. No thick/thin contrast is possible with this approach. The physics are correct; the drawing primitive cannot express them.

**This path is a dead end. Ellipse stamping must be replaced.**

---

## Part 2: The Canonical Approach — Polygon Sweep

A calligraphic broad-edge nib is geometrically a line segment of fixed length (`nib_width_mm`) held at a fixed angle (`nib_angle_deg`). As the pen moves, this edge sweeps through space and deposits ink everywhere it touches. The correct rendering model:

1. At each sample point along a Bézier stroke, compute the nib edge as a half-vector:
   ```python
   half = nib_width_mm / 2.0
   hx = half * math.cos(nib_angle_rad)   # horizontal half-extent of nib edge
   hy = half * math.sin(nib_angle_rad)   # vertical half-extent of nib edge
   ```

2. The nib occupies a line segment from `(x - hx, y - hy)` to `(x + hx, y + hy)`.

3. Between two consecutive positions `(x0,y0)` and `(x1,y1)`, the swept area is a quadrilateral:
   ```
   (x0 - hx, y0 - hy) → (x0 + hx, y0 + hy)
   (x1 + hx, y1 + hy) → (x1 - hx, y1 - hy)
   ```

4. Fill this quadrilateral with the ink color at the average darkness of the two endpoints.

This model **naturally produces thick downstrokes and thin crossstrokes** without any direction-dependent width calculation. When the stroke direction is parallel to the nib angle, the swept quadrilateral is thin (the nib moves along its own edge). When the stroke direction is perpendicular to the nib angle, the quadrilateral is wide (the nib moves broadside). This is exactly how a real broad-edge pen works.

### Supersampling

Render at `N×` resolution (N=3 recommended) then downsample with Lanczos. This provides smooth anti-aliased edges without requiring sub-pixel polygon math. The evo renderer already does this correctly (`_SUPERSAMPLE = 3` in `evo/renderer.py`).

### Darkness computation

Darkness at each sample point is a function of pressure and ink state. Keep the existing `ink_darkness()` function from `evo/renderer.py` — it correctly models:
- base darkness from reservoir state
- fresh-dip boost
- depletion decay

Do **not** use the `stroke_opacity()` function from `render/nib.py`. It multiplies four factors and can produce near-zero values for hairline strokes, causing them to be filtered out at the `darkness < 4` threshold.

### Width modulation

The polygon sweep produces width purely from nib geometry. The optional pressure-modulated width scaling in `mark_width()` (a ±20% factor) is not needed for the canonical renderer — direction does all the work. Retain it only as a minor ink-volume signal for the heatmap.

---

## Part 3: Page Compositor Coordinate Bug

The evo renderer's `render_word_from_genome()` correctly renders individual words. The page-level compositor that assembles words into lines and lines onto the full page canvas has a coordinate error: all text is placed at the top-left corner instead of being distributed across the page.

The bug is in how `x_offset_px` is passed to `_world_to_px()`. The function signature is:
```python
def _world_to_px(x_mm, y_mm, baseline_y, slant_rad, baseline_offset, px_per_mm, x_offset_px)
```

`x_offset_px` should be the absolute horizontal position of the word on the page canvas in pixels (i.e., `word.x_mm * px_per_mm`). The compositor is likely passing the word-local x offset (typically 0 or a small number) instead.

### Diagnosis protocol

Run `scribesim render-glyph n` (the diagnostic command defined in TD-015 Part 4). If the glyph renders correctly in isolation, the renderer itself is correct and the bug is only in the compositor. If the glyph is still illegible in isolation, the renderer has additional problems.

### Fix target

After the fix, a rendered test line `"und das waz gut"` at 150 DPI should show:
- Words distributed across the line at appropriate inter-word spacing
- No text clustering in any corner
- Baselines horizontal (before slant is applied)

---

## Part 4: Diagnostic Tooling Requirements

**No further rendering work should proceed without a functional single-glyph and single-word diagnostic CLI.** This is not optional infrastructure — it is the feedback loop that makes all other fixes verifiable.

### Required CLI commands

```
scribesim render-glyph <char> [--dpi N] [--output path]
scribesim render-word <text> [--dpi N] [--output path]
scribesim glyph-sheet [--output path]
```

**`render-glyph`**: Renders a single character from `GLYPH_CATALOG` on a small canvas (canvas size = 3× x_height at the requested DPI). Saves to `--output` (default: `debug/<char>.png`). No layout, no compositor — just the glyph strokes.

**`render-word`**: Renders a short word (≤12 characters) using the evo renderer's word-level compositor. Canvas sized to fit the word with 2× x_height margins. Saves to `--output` (default: `debug/<text>.png`). This isolates the word compositor from page-level bugs.

**`glyph-sheet`**: Renders every glyph in the catalog as a grid (10 per row). Saves a single PNG to `--output` (default: `debug/glyph-sheet.png`). Used to visually verify the complete catalog after any renderer change.

### Acceptance criterion

Before ADV-SS-RENDER-004 is marked complete:
1. `scribesim render-glyph n` must produce a visible 'n' shape with a thick leftward downstroke and a thin rightward connection stroke
2. `scribesim render-word und` must show three connected letterforms with natural inter-letter hairlines
3. `glyph-sheet` must show all catalog glyphs without any missing or corrupted entries

These are human-inspected criteria. The advance is not complete until they pass visual review.

---

## Part 5: Unified Pipeline Architecture

After implementing Parts 1–4, the rendering architecture should be:

```
Bézier stroke sequence
    ↓
Arc-length sampled points (N samples, uniform spacing in mm)
    ↓
Per-point: (x, y, pressure, ink_state) → darkness scalar
    ↓
Polygon sweep: quadrilateral fill between adjacent points
    at 3× supersample resolution
    ↓
Lanczos downsample to target DPI
```

The existing `render/pipeline.py` 6-stage structure (geometry → raw render → ink filters → composite → ground truth → heatmap) is correct at the macro level and should be preserved. Only Stage 2 (raw rendering) changes: the ellipse stamp loop is replaced with the polygon sweep loop.

**The evolutionary engine** (`evo/engine.py`, `evo/fitness.py`) is not part of the rendering pipeline. It remains as an optional parameter-tuning tool. The base renderer is deterministic; evolution is not required for standard folio rendering.

### Dead code notice

`scribesim/handflow/` (~5000 lines) and `scribesim/handsim/` are not wired into any CLI path. They should not be modified as part of this consolidation. Whether to retain or remove them is a separate decision.

---

## Implementation Order

1. **ADV-SS-DIAG-001** — Diagnostic CLI (`render-glyph`, `render-word`, `glyph-sheet`). No renderer changes; uses existing evo renderer. Establishes visual baseline.
2. **ADV-SS-RENDER-004** — Replace ellipse stamps with polygon sweep in `render/pipeline.py`. Validated against diagnostic output.
3. **ADV-SS-RENDER-005** — Fix page compositor coordinate bug. Validated by rendering a test line spanning the full page width.

All three advances must complete before any further rendering-quality work (thick/thin calibration, ink filters, justification) makes sense.

---

## Dependency Chain

```
TD-002 (hand model, nib physics)
TD-004 (nib fixes, metrics)
  ↓
TD-015 (renderer consolidation) ← YOU ARE HERE
  ↓
TD-004 Part 1 calibration (now effective, renderer was previously broken)
TD-016 (layout improvements — justification, line-breaking)
```

---

## Revision History

| Date | Change | Author |
|---|---|---|
| 2026-04-16 | Initial — renderer consolidation plan following quality review | shawn + claude |
