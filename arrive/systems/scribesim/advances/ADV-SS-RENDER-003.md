---
advance:
  id: ADV-SS-RENDER-003
  title: Natural Inter-Glyph Connections — Entry/Exit Geometry Fix
  system: scribesim
  status: proposed
  priority: medium
---

## Problem

Curved hairline connections between glyphs are now drawn using exit/entry tangents
(Bézier with tangent-derived control points), which looks organic. However the
connection arcs descend from the top of one letter to the baseline of the next,
rather than staying near the x-height level.

Root cause: several GLYPH_CATALOG letters ('n', 'i', 'h', 'm', etc.) define their
first stroke starting from the baseline (y_norm=0) rather than the x-height top
(y_norm=1.0). Gothic Bastarda downstrokes begin at the top; the catalog has them
reversed so the Bézier's p0 (the connection entry point) sits at the bottom.

## Options

### Option A — Reorder GLYPH_CATALOG strokes
For each affected letter, flip the first stroke so it starts at the top
(y_norm=1.0) and descends. This fixes entry points and tangents for all letters
that begin with a downstroke ('n', 'h', 'm', 'u', 'r', etc.).

*Pro*: Correct calligraphic direction for the whole genome.
*Con*: Changes all existing segment coordinates; may affect F1 NCC scoring.

### Option B — Override connection entry point per letter
Annotate each letter in GLYPH_CATALOG with an explicit `connection_entry` point
in normalised coordinates (typically the top of the first stroke). The renderer
uses this instead of p0 when drawing the hairline connection.

*Pro*: Non-invasive — leaves stroke geometry intact.
*Con*: Requires per-letter annotation of ~20 characters.

### Option C — Auto-detect top of first stroke
In the renderer, scan the first segment at t=0..1 and find the point with the
minimum y_mm (highest on page). Use that as the connection entry, with the
tangent at that t value.

*Pro*: Automatic, no manual annotation.
*Con*: May pick the wrong point for letters with multiple strokes at x-height.

### Option D — Route connection via x-height rail
Always route the hairline to/from a point at y = baseline − x_height on the
appropriate side of the glyph bounding box, ignoring the actual segment endpoints.

*Pro*: Consistent x-height level connections regardless of catalog ordering.
*Con*: May look artificial if the actual stroke doesn't reach the x-height point.

## Recommended path
Option A (reorder strokes) combined with Option B (explicit connection annotation)
for letters where reordering alone is ambiguous (e.g., 'd', 'g').

## Future enhancement (noted separately)
Fade the hairline connection slightly as it approaches the entry point (darkness
decreasing from 0.75 → 0.45 over the last 30% of the arc) to mimic the
characteristic ink-thinning as the nib lifts toward the next stroke.
