---
advance:
  id: ADV-SS-CONNECTIONS-001
  title: Cursive Connections — Inter-Glyph Pen Strokes Within Words
  system: scribesim
  primary_component: glyphs
  components:
  - glyphs
  - layout
  - render
  started_at: 2026-03-20T20:45:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T16:49:24.749792Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - public_api
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Implement cursive connections between letters within a word. Currently each glyph is rendered independently — the pen "lifts" between every letter, producing a disconnected typewriter-like appearance. Real Bastarda is semi-cursive: the pen stays on the vellum within words, with connecting strokes linking each letter's exit point to the next letter's entry point. The pen lifts only at word boundaries.

## Behavioral Change

After this advance:
- Each `Glyph` in the catalog has `entry_point` and `exit_point` — the (x, y) coordinates where the pen arrives and departs (in x-height units)
- The layout placer generates a `ConnectionStroke` (cubic Bezier) from the previous glyph's exit point to the next glyph's entry point for consecutive glyphs within a word
- Connection strokes are hairline upstrokes (low pressure, thin) — matching the `_UP` pressure profile
- The connection lift height (how high the pen arcs between glyphs) is parameterized by `glyph.connection_lift_height_mm` from HandProfile
- At word boundaries (spaces), no connection stroke is generated — the pen lifts
- The rasteriser renders connection strokes the same as glyph strokes (they're just additional BezierStrokes in the layout)
- Visual output matches the Werbeschreiben reference: flowing cursive within words, breaks at word boundaries

## Planned Implementation Tasks

- [ ] Tidy: add `entry_point` and `exit_point` fields to `Glyph` dataclass (default to (0.0, 0.0) and (advance_width, 0.0) for backward compat)
- [ ] Tidy: define `ConnectionStroke` — a BezierStroke generated between consecutive glyphs
- [ ] Test: connection strokes generated between consecutive glyphs within a word
- [ ] Test: no connection stroke at word boundaries (spaces)
- [ ] Test: connection stroke arc height matches `connection_lift_height_mm` parameter
- [ ] Test: rendered connection strokes are visible (hairline upstrokes between letters)
- [ ] Implement: add entry/exit points to all ~90 glyphs in the catalog — each letter's natural pen arrival and departure point
- [ ] Implement: `generate_connection()` — produce a cubic Bezier from exit to entry with an upward arc
- [ ] Implement: update placer to insert ConnectionStrokes between consecutive glyphs in a word
- [ ] Implement: update PositionedGlyph or LineLayout to carry connection strokes for rendering
- [ ] Validate: render f01r — flowing cursive within words, clean breaks at word boundaries
- [ ] Checkpoint: `./snapshot.sh connections-001` — VISUAL DIFF: connected letterforms within words

## Risk + Rollback

**Risks:**
- Adding entry/exit points to all 90 glyphs is a large manual task requiring calligraphic knowledge — initial values will be approximate and need tuning
- Connection strokes may collide with glyph strokes if entry/exit points are poorly placed
- The connection arc height needs careful calibration — too high looks artificial, too low overlaps with x-height letterforms

**Rollback:**
- Revert the branch; connection generation is additive (glyphs render unchanged without connections)

## Evidence

