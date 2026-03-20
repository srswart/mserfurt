---
advance:
  id: ADV-SS-RENDER-001
  title: Render — Initial Implementation
  system: scribesim
  primary_component: render
  components:
  - render
  started_at: 2026-03-19T17:20:56Z
  started_by: null
  implementation_completed_at: 2026-03-19T17:25:10.484424Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  - public_api
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Implement the Bezier stroke rasterization engine as a Rust crate (`scribesim_render`) exposed to Python via PyO3, producing 300 DPI page images and simultaneous pressure heatmaps using a virtual nib model calibrated to Brother Konrad's 40-degree Bastarda nib angle.

## Behavioral Change

After this advance:
- The `scribesim_render` Rust crate accepts a sequence of positioned glyphs (from layout) and resolved hand parameters, and rasterizes all Bezier strokes into a pixel buffer at 300 DPI
- The virtual nib model computes stroke width as `nib_width * pressure(t)` and darkness as `ink_flow(t)`, with nib angle fixed at 40 degrees for Bastarda thick/thin contrast
- Pressure heatmaps are produced simultaneously during rasterization, encoding per-pixel pressure values as a grayscale PNG (`{folio_id}_pressure.png`)
- Ink flow simulation handles sitting boundaries (f07r): ink density shifts at the boundary where Konrad resumed writing in a different session, producing visible but subtle density variation
- Rendering is deterministic — the same input with the same seed produces bitwise-identical PNG output

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/scribesim-render-init`
- [ ] Tidy: set up `scribesim_render` Rust crate with PyO3 bindings; define FFI interface for accepting positioned glyph data and hand parameters from Python
- [ ] Test: write unit tests — single stroke rasterizes to non-empty pixel buffer; nib angle 40 degrees produces expected thick/thin ratio on horizontal vs vertical strokes; pressure heatmap values correlate with input pressure profiles; determinism test (render twice, compare buffers byte-for-byte)
- [ ] Implement: cubic Bezier curve evaluation with adaptive subdivision for smooth rasterization at 300 DPI
- [ ] Implement: virtual nib model — elliptical nib at 40 degrees, width modulated by `pressure(t)`, opacity modulated by `ink_flow(t)`
- [ ] Implement: pressure heatmap generation — record pressure value at each rendered pixel, output as grayscale PNG alongside the page image
- [ ] Implement: ink flow sitting boundary handling — detect f07r sitting boundary annotation, apply `ink_density_shift` to ink_flow for strokes after the boundary point
- [ ] Implement: tremor application — for folios f14r onward, add controlled randomness (seeded) to stroke control points based on tremor_amplitude from hand parameters
- [ ] Validate: render f01r (clean baseline), f06r (increased pressure), f07r (sitting boundary density shift), f14r (tremor + fatigue); visually inspect and compare against expected output

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- The Rust/PyO3 boundary is a public API that Weather depends on indirectly (via the PNG output contract); changes to pixel buffer format or resolution will break downstream consumers
- Adaptive subdivision parameters may need tuning to balance rendering quality against performance for full-page rasterization at 300 DPI
- Determinism requires careful handling of floating-point operations across platforms; Rust compiler flags and SIMD usage must be controlled

**Rollback:**
- Revert the `feat/scribesim-render-init` branch; the Rust crate is self-contained and the PyO3 bindings have no persistent state

## Evidence

