---
advance:
  id: ADV-SS-GUIDEGEN-002
  title: Ink Bounding-Box x_advance + Recalibrated Analysis Test Coverage
  system: scribesim
  primary_component: refextract
  components:
  - refextract
  - refselect
  - cli
  started_at: 2026-03-21T23:15:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T17:50:25.224276Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  status: complete
---

## Objective

Two related fixes shipped as one advance:

**Part A — Correct `x_advance` from ink bounding box:**

`build_letterform_guide` currently derives `x_advance` from the maximum x-coordinate of the DTW-averaged Bézier trace.  This is unreliable for wide multi-stroke letters (`m`, `w`, `v`) where the trace geometry overestimates the advance, and for narrow letters where the trace underestimates.

The correct approach: measure `x_advance` from the pixel bounding box of the exemplar images themselves — specifically, the median of `(ink_right_col - ink_left_col) / x_height_px` across all exemplars for a given letter.  This is the actual ink footprint in x-height units and is independent of tracing quality.

This requires passing exemplar image paths (or their precomputed bounding boxes) into `build_letterform_guide`.  The `build-guides` CLI already has the exemplar directory; it will compute bounding boxes there and pass them through.

**Part B — Update analysis test coverage for recalibrated `thick_thin`:**

`analyze_thick_thin` was rewritten today (interior EDT distribution, p25/p75) but `tests/test_refselect_analysis_a3a7.py` still has assertions written against the old p10/p90 logic and synthetic images that don't exercise the interior-pixel path.  These tests need updating, and a real-crop fixture (one of the BSB 95r letter crops) should be added as a regression guard.

## Behavioral Change

**Part A:** `x_advance` values for `m`, `w`, `v` will decrease from the current 2.0 cap toward more realistic values (~0.9–1.3 x-heights for wide Bastarda letters).  Narrow letters (`i`, `l`, `r`) will also get more accurate values.  The TOML output format is unchanged.

**Part B:** No behavioral change to analysis functions.  Test file updated to match current implementation.  New fixture added.

## Planned Implementation Tasks

### Part A — x_advance from ink bounding box

1. Add `measure_ink_x_advance(image_paths: list[Path], x_height_px: float) -> float` to `scribesim/refextract/guidegen.py`:
   - Load each exemplar, convert to grayscale, Otsu binarize
   - Find leftmost and rightmost ink column
   - Compute `(right - left) / x_height_px` per image
   - Return median across all images (robust to a bad crop)
   - Return `None` if no ink found in any image

2. Update `build_letterform_guide(letter, exemplar_traces, x_height_px, exemplar_paths=None)`:
   - If `exemplar_paths` provided and non-empty, call `measure_ink_x_advance`; use result if valid
   - Fall back to current max-trace-x approach if no paths provided (backward compat)
   - Clip result to [0.3, 2.0] as before

3. Update `build-guides` CLI handler:
   - Accept `--exemplars PATH` alongside existing `--traces PATH` (optional; enables ink bounding box)
   - When provided, collect `{char: [exemplar_paths]}` and pass to `build_letterform_guide`
   - Document that `--exemplars` gives more accurate `x_advance`

4. Tests:
   - `test_measure_ink_x_advance_wide` — wide synthetic image (full-width ink block) returns ~1.0
   - `test_measure_ink_x_advance_narrow` — narrow central strip returns ~0.3
   - `test_measure_ink_x_advance_median` — 3 images with different widths; returns median not mean
   - `test_build_letterform_guide_uses_bounding_box` — when exemplar_paths provided, x_advance matches ink extent not trace endpoint

### Part B — Recalibrated analysis tests

5. Update `tests/test_refselect_analysis_a3a7.py`:
   - `test_thick_thin_uniform` — update expectation: uniform image has no interior pixels → returns 0.0 (unchanged)
   - `test_thick_thin_bastarda_strokes` — rewrite fixture: alternating wide/narrow ink strips; interior EDT has genuine p25/p75 variation → score > 0.5
   - `test_thick_thin_real_crop` — add fixture using one saved BSB 95r letter crop (stored in `tests/fixtures/`); assert score in [0.4, 0.8]
   - Remove any assertions that were calibrated to old p10/p90 ratio thresholds

## Risk + Rollback

- **Backward compat**: `exemplar_paths` is optional in `build_letterform_guide`. Existing callers without `--exemplars` flag get current behaviour.
- **Bounding box accuracy**: depends on Otsu binarization quality on 256px exemplars — these are well-controlled inputs so failure rate should be very low. Median across exemplars further smooths any bad crops.
- **Test fixture storage**: one real crop PNG (~15KB) committed to `tests/fixtures/`. Small, stable, unambiguous.
- **Rollback**: remove `exemplar_paths` parameter; revert to max-trace-x. One function change.

## Evidence

