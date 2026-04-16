---
advance:
  id: ADV-SS-RENDER-005
  title: Render — Fix Page Compositor Coordinate Bug
  system: scribesim
  primary_component: render
  components:
  - render
  - layout
  status: complete
  priority: high
  risk_flags:
  - breaking_change
  started_at: 2026-04-17T00:00:00Z
  started_by: srswart@gmail.com
  implementation_completed_at: 2026-04-17T00:30:00Z
  implementation_completed_by: srswart@gmail.com
  evidence:
  - tdd:green
  - tests:unit
  - human-verified:coordinate-placement
---

## Objective

Fix the coordinate composition bug that places all rendered text in the top-left corner of the page canvas. After ADV-SS-RENDER-004 (polygon sweep renderer) the individual glyph and word rendering will be correct; this advance ensures words are correctly positioned when assembled into lines and lines into pages.

The symptom: `scribesim-evo/debug/evolved_3lines.png` shows text only in the top-left corner of an otherwise blank parchment page, regardless of folio geometry settings.

## Behavioral Change

After this advance:

- A rendered folio page shows text distributed across the full text block, not clustered in any corner.
- Words are spaced horizontally according to the layout geometry (left margin, inter-word spacing).
- Baselines are positioned vertically at the correct y coordinates (top margin + line number × line height).
- A test line `"und das waz gut"` rendered as a standalone diagnostic shows four words spread across the text measure with correct inter-word gaps.
- `scribesim render --folio f01r` produces a page image where text begins near the top-left text block corner and extends across the full width.

## Pipeline Context

- **Upstream**: ADV-SS-RENDER-004 must be complete — there is no value in fixing the compositor if the renderer itself is still producing blobs.
- **Downstream**: This advance unblocks all layout quality work (ADV-SS-LAYOUT-001 justification requires the compositor to correctly place words before stretching their gaps).
- **Contracts**: Output PNG dimensions and format unchanged. Content will change significantly (text now fills the page instead of the corner).

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/ss-render-005-compositor-coords`
- [ ] **Tidy**: add a `scribesim render-line <text>` diagnostic subcommand (extending ADV-SS-DIAG-001's CLI module) that renders a single line of text onto a full-width canvas at the correct page-width, saves PNG — this is the isolated test harness for the compositor
- [ ] **Diagnose**: run `scribesim render-word und` and `scribesim render-line und das waz gut` with logging; print `x_offset_px` values passed to `_world_to_px` for each word; confirm whether words are receiving page-absolute or word-local x offsets
- [ ] **Test** (red): write `tests/test_render_compositor.py` — render the line `"und das waz gut"` at 150 DPI; segment the result into word columns by finding vertical bands with no ink; assert there are exactly 4 such segments (4 words); assert the leftmost word starts within 5mm of the left margin; assert the rightmost word ends within 10mm of the right margin
- [ ] **Test** (red): render the f01r folio JSON at 75 DPI (low-res for speed); assert that ink pixels exist in all four quadrants of the text block (not only top-left)
- [ ] **Implement**: trace the coordinate path from `PageLayout.lines[n].glyphs[m].x_mm` through to the pixel coordinate passed to the draw call; find where the page-absolute x_mm is not being converted to page-absolute pixels
- [ ] **Implement**: fix the coordinate transformation; the correct formula for each glyph's pixel position is `x_px = glyph.x_mm * px_per_mm` (page-absolute) not `(glyph.x_mm - line.start_x_mm) * px_per_mm` (line-relative)
- [ ] **Implement**: apply the same fix to baseline y: `y_px = glyph.baseline_y_mm * px_per_mm` from the page top (y=0 at top of page)
- [ ] **Validate** (human): run `scribesim render-line "und das waz gut"` and inspect — four words spread across the line with natural spacing
- [ ] **Validate** (human): run `scribesim render --folio f01r --output debug/f01r.png`; open the output; confirm text fills the page from top to bottom left to right
- [ ] Run full test suite; confirm compositor tests pass; no regressions

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- The coordinate bug may be in the `PageLayout` construction (layout stage) rather than in the render stage. If `glyph.x_mm` values themselves are wrong (all near zero), the fix is in `layout/placer.py`, not `render/pipeline.py`. The diagnostic step (printing x_offset_px values) will distinguish these cases.
- Fixing the coordinates may reveal a second problem: the page geometry (margin widths, text block width) may be configured incorrectly for the MS Erfurt folio dimensions, causing correctly-placed text to fall outside the page boundaries. Check page width from `ms_erfurt_standard.toml` against the `PageLayout.geometry` values.
- If the y coordinate is also wrong, text may appear at the correct x position but at the wrong vertical position (e.g., all text on line 1 regardless of line number). Address in the same fix pass.

**Rollback:**
- Revert the `feat/ss-render-005-compositor-coords` branch. The rendering algorithm (ADV-SS-RENDER-004) is in a separate branch and is unaffected by rollback.

## Check for Understanding

The coordinate bug was resolved as part of ADV-SS-RENDER-004. The complete rewrite of `render/pipeline.py` from ellipse-stamp to polygon-sweep used page-absolute mm coordinates throughout: `pg.x_mm + pt[0] * x_height_mm` correctly places each glyph at the configured margin. Diagnostic confirms: leftmost ink at 19.2mm on a 20mm left-margin page.

The render-line diagnostic command already existed from ADV-SS-DIAG-001. Tests confirm 4 correctly spaced word segments for "und das waz gut".

## Evidence

- [x] `render-line "und das waz gut"` produces 4 visually separated word segments (word-segmentation test passes)
- [x] Plain pipeline diagnostic: leftmost ink at 19.2mm on 20mm-margin page — margin correctly applied
- [x] `tests/test_render_compositor.py` — 8 tests pass: left-margin, top-margin, origin-guard, multi-line vertical span, per-line baseline bands, 4-word segmentation, word spacing, line ink presence
- [x] No regressions: 59/59 render-related tests pass (test_render_compositor, test_render_pipeline, test_diagnostic)
