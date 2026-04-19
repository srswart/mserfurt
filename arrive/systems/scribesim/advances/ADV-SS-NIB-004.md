---
advance:
  id: ADV-SS-NIB-004
  title: Direction-Coupled Nib Angle — Within-Stroke Thick/Thin Variation
  system: scribesim
  primary_component: render
  components:
  - render
  status: complete
  priority: high
  risk_flags:
  - rendering_change
  started_at: 2026-04-17T02:00:00Z
  started_by: srswart@gmail.com
  evidence: []
---

## Objective

Make the nib angle track stroke direction locally at each segment, producing
natural calligraphic thick/thin variation within individual strokes.

The current model fixes `(hx, hy)` for an entire line based on the hand's nib
angle. A real broad-edged quill produces its thickest mark when the stroke is
perpendicular to the nib edge and its thinnest when parallel. Without tracking,
all strokes look the same regardless of direction.

## Approach

For each consecutive sample pair in `_polygon_sweep_stroke`, compute the local
stroke direction angle `θ = atan2(dy, dx)`. The effective nib angle is:

```
effective_angle(t) = base_angle + coupling × θ(t)
```

where `coupling ∈ [0, 1]` controls how strongly the nib tracks the stroke.
At `coupling=0` the current model is preserved. At `coupling≈0.25` the nib
tracks the stroke direction at 25% — enough to produce measurable variation
without the exaggerated effect of full tracking.

Diagnostic confirms the 'n' arch stroke spans 115° of direction change. At
coupling=0.25 that produces ~29° of nib angle change through the arch —
creating genuine thick/thin variation without requiring new glyph data.

## Planned Implementation Tasks

- [x] Create advance document
- [x] **Implement**: modify `_polygon_sweep_stroke` to accept `nib_angle_deg`,
      `nib_width_mm`, `nib_coupling=0.0` and recompute `(hx, hy)` per segment
- [x] **Update calls**: glyph strokes pass `nib_coupling=0.25`; connection
      strokes keep `nib_coupling=0.0` (hairlines stay fixed)
- [x] **Test**: 9/9 tests pass in test_nib_coupling.py including arch span,
      length preservation, zero-coupling fallback, TOML loading
- [x] **Validate**: f01r rendered; legible Bastarda with visible thick/thin
      variation — downstrokes thin, arch crossings thick

## Evidence

- [x] Test: 9/9 test_nib_coupling.py pass; arch spans 28°+ nib angle range
- [x] Human: f01r render shows natural calligraphic thick/thin, legible
