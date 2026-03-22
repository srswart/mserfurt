---
advance:
  id: ADV-SS-CENTERLINE-001
  title: Centerline Tracing — Skeletonize + Bézier Fitting (TD-008 Step 5)
  system: scribesim
  primary_component: refextract
  components:
  - refextract
  started_at: 2026-03-21T11:30:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T11:11:39.993791Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence:
  - tdd:red-green
  - tests:unit
  status: complete
---

## Objective

Implement `scribesim/refextract/centerline.py` for TD-008 Step 5: extract the writing path from each letter exemplar as a sequence of cubic Bézier segments.

**Pipeline per letter**:
1. `binarize(image)` — threshold at 0.7
2. `skeletonize(binary)` — Zhang-Suen (via `skimage.morphology.skeletonize`); produces 1-pixel-wide skeleton
3. `order_skeleton_pixels(skeleton)` — traverse skeleton graph left-to-right; handle branch points (multi-stroke letters like 'd', 'b') by detecting degree-3+ nodes and emitting sub-paths
4. `detect_gaps(skeleton)` — gaps in skeleton = pen-lift points; mark as `contact=False` segments
5. `fit_bezier_to_path(points, max_error=0.5)` — Philip Schneider's algorithm: iterative Bézier fitting, split at max-error points. Output: `list[BezierSegment]` (reuses `scribesim/evo/genome.BezierSegment`)
6. `trace_centerline(letter_image) -> list[BezierSegment]` — full pipeline; sets `.contact` on each segment

**Output format**: Per-letter trace files as TOML or numpy arrays in `reference/traces/{char}/werbeschreiben_{nnn}.toml`. Each file contains a list of Bézier control points and `contact` flags.

**Debug output**: `scribesim extract-preview` overlays the fitted centerlines on the original image in red.

**CLI**: `scribesim trace-centerlines --exemplars reference/exemplars/ -o reference/traces/`

## Behavioral Change

New module only. No changes to existing code. The `BezierSegment` struct from `scribesim.evo.genome` is reused (no duplication).

## Planned Implementation Tasks

1. `scribesim/refextract/centerline.py`: `binarize()`, `skeletonize_letter()`, `order_skeleton_pixels()`, `detect_gaps()`, `fit_bezier_to_path()`, `trace_centerline()`
2. TOML serialization for trace output (`reference/traces/{char}/`)
3. `extract-preview` CLI subcommand: draw control points and skeleton on original image
4. `trace-centerlines` CLI subcommand
5. Unit tests: skeleton of a simple stroke produces a single ordered path; Bézier fit to a known cubic returns control points within tolerance; gap detection marks correct segments as non-contact

## Risk + Rollback

- **New dependency**: `scikit-image` for `skeletonize`. Already used elsewhere in the project (metrics). No new install required.
- Skeleton ordering on complex letters (d, b, h) may produce wrong path ordering. The debug preview (`extract-preview`) is the primary validation tool.
- Rollback: module is additive. Removing it does not affect any existing code path.

## Evidence

