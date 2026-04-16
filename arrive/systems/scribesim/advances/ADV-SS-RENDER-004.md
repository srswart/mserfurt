---
advance:
  id: ADV-SS-RENDER-004
  title: Render — Replace Ellipse Stamps with Polygon Sweep (TD-015 Part 2)
  system: scribesim
  primary_component: render
  components:
  - render
  status: complete
  priority: critical
  risk_flags:
  - breaking_change
  started_at: 2026-04-16T22:10:00Z
  started_by: srswart@gmail.com
  implementation_completed_at: 2026-04-16T23:00:00Z
  implementation_completed_by: srswart@gmail.com
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  - human-verified:render-pipeline
---

## Objective

Replace the broken ellipse-stamp rendering loop in `render/pipeline.py` Stage 2 with a polygon-sweep approach consistent with the evo renderer in `evo/renderer.py`. This is the core fix identified in TD-015: `PIL.ImageDraw.ellipse()` cannot be rotated, so the nib angle and direction-dependent width calculations in the current pipeline are silently discarded, producing illegible blob-stamp output instead of calligraphic strokes.

## Behavioral Change

After this advance:

- Stage 2 of `render/pipeline.py` (`_render_at_internal_dpi`) draws filled quadrilaterals between consecutive Bézier sample points instead of ellipses at each point. The quadrilateral vertices are derived from the nib edge half-vector `(hx, hy) = (half × cos θ, half × sin θ)` where θ is `nib_angle_deg`.
- Downstrokes (stroke direction ≈ perpendicular to nib angle) produce wide marks. Crossstrokes (stroke direction ≈ parallel to nib angle) produce narrow hairline marks. The thick/thin ratio at 300 DPI for a 1.8mm nib at 40° should be at least 4:1 between a vertical downstroke and a horizontal crossstroke.
- Connection strokes (hairline upstrokes between glyphs) also switch to polygon sweep. Their width is a fraction of the nib width (configured as `hairline_ratio ≈ 0.065`), drawn as narrow quads.
- The `stroke_opacity()` function from `nib.py` is **not** used in the new path. Darkness is computed directly as `pressure × ink_density × base_darkness`, clamped to [0, 1], without the four-factor multiply that was producing near-zero values for hairline strokes.
- The `darkness < 4` skip threshold is removed. Instead, skip only when `darkness < 0.02` (i.e., effectively invisible). Hairline strokes that were being filtered out are now visible.
- All other pipeline stages (Stage 1 geometry, Stage 3 ink filters, Stage 4 downsample, Stage 5 ground truth, Stage 6 heatmap) are unchanged.
- Output contract is unchanged: same filenames, same DPI, same formats.

## Pipeline Context

- **Upstream**: ADV-SS-DIAG-001 must be complete. Use `scribesim render-glyph` to verify the new renderer produces visible thick/thin contrast before integrating into the full pipeline.
- **Downstream**: ADV-SS-RENDER-005 (compositor coordinate fix) depends on the renderer being correct first. ADV-SS-LAYOUT-001 (justification) depends on both.
- **Contracts**: Output PNG and heatmap contracts are unchanged. The rendered appearance will change — this is intentional. The Weather pipeline requires no changes.

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/ss-render-004-polygon-sweep`
- [ ] **Tidy**: extract the nib edge half-vector computation into a helper `_nib_half_vec(nib_angle_deg: float, nib_width_mm: float, px_per_mm: float) -> tuple[float, float]` in `render/pipeline.py`; extract `_polygon_sweep_stroke(draw, samples, darkness_fn, hx, hy)` as a standalone function
- [ ] **Test** (red): add tests to `tests/test_render_pipeline.py` — render a single vertical stroke (Bézier from top to bottom) and a single horizontal stroke; measure the width of the resulting mark in pixels; assert `vertical_width / horizontal_width >= 3.0`; assert no single-pixel-wide output for the vertical stroke at 300 DPI with 1.8mm nib
- [ ] **Test** (red): render 'n' at 300 DPI; assert the image is not all-parchment (some pixels darker than background threshold); assert maximum darkness in the image is above 0.6 (strokes are actually dark, not washed out)
- [ ] **Implement**: replace the `draw.ellipse(bbox, fill=...)` loop in `_render_at_internal_dpi` with `draw.polygon(quad, fill=...)` where `quad` is the four-vertex quadrilateral between consecutive sample points
- [ ] **Implement**: replace the darkness computation — remove the `stroke_opacity()` call, compute `darkness = pressure * hand.ink_density * hand.stroke_weight` directly, skip only if `darkness < 0.02`
- [ ] **Implement**: apply the same polygon sweep to connection strokes (hairlines), using `hairline_width_mm = nib_width_mm * 0.065` for `hx`/`hy` computation
- [ ] **Implement**: add stroke-end caps: at the start and end of each stroke, draw a short line segment at the nib angle to close the polygon ends cleanly (prevents open gaps at stroke terminations)
- [ ] **Validate** (human): run `scribesim render-glyph n --dpi 150` with the new renderer; confirm a visible 'n' with a thick left downstroke and a thinner curved connection; compare against the reference sample in `docs/samples/v2_bsb00052961_00005_full_full_0_default.jpg`
- [ ] **Validate** (human): run `scribesim glyph-sheet`; confirm all glyphs have clear thick/thin contrast and no glyphs are blobs
- [ ] Run full test suite; confirm the thick/thin ratio tests pass; confirm no regressions in other pipeline stages

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- The polygon sweep may produce harder edges than the ellipse stamps. If edges look too crisp/digital, the ink filter in Stage 3 should be relied upon for softening rather than reverting to ellipses. Resist the temptation to add blur to the renderer itself.
- Sample density along Bézier curves: if sample points are spaced too far apart, the quadrilaterals will have gaps (dashed appearance). At 400 DPI internal, points should be spaced ≤0.3mm apart (≤4.7px). Check the `sample_bezier()` adaptive subdivision parameters if gaps appear.
- The stroke-end cap approach may cause double-thickness at stroke junctions if two strokes share an endpoint. Visual inspection will reveal this; fix by shortening the cap to 50% of nib width at shared endpoints.

**Rollback:**
- Revert the `feat/ss-render-004-polygon-sweep` branch. The output contract is unchanged, so Weather and downstream consumers are unaffected by rollback.

## Evidence

- [ ] Thick/thin ratio test passes: `vertical_width / horizontal_width >= 3.0` at 300 DPI, 1.8mm nib
- [ ] 'n' glyph maximum darkness test passes: max pixel darkness > 0.6
- [ ] `scribesim render-glyph n` output shows visible thick/thin contrast (human verified)
- [ ] `scribesim glyph-sheet` output shows all catalog glyphs with clear letterforms (human verified)
- [ ] Full test suite passes with no regressions
