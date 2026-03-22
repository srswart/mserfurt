---
advance:
  id: ADV-SS-NIBCAL-001
  title: Stroke Width Measurement + Nib Calibration (TD-008 Steps 6 + 8)
  system: scribesim
  primary_component: refextract
  components:
  - refextract
  - hand
  started_at: 2026-03-21T12:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T11:32:35.802063Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence:
  - tdd:red-green
  - tests:unit
  status: complete
---

## Objective

Implement stroke width measurement and nib parameter calibration in `scribesim/refextract/nibcal.py`. This takes the centerline traces from ADV-SS-CENTERLINE-001 and the letter images, measures the physical width of each stroke, and fits the `PhysicsNib` model parameters to match the real manuscript.

**Step 6 — Stroke width measurement** (`measure_stroke_width()`):
- For each sampled point along a centerline, cast perpendicular rays into the ink mask to find the left and right ink boundaries.
- Output: `(widths: list[float], directions: list[float])` per letter — width and stroke direction at each sample point.
- Aggregate across all letters: `reference/widths/all_strokes.npz`

**Step 8 — Nib calibration** (`calibrate_nib()`):
- `estimate_nib_angle()`: fit `width ∝ |sin(direction - nib_angle)|` model; search over 25°–55° range (Bastarda typical). Use `scipy.optimize.minimize_scalar`.
- `estimate_nib_width()`: 95th percentile of all measured stroke widths; convert px → mm using image DPI.
- `estimate_pressure_modulation()`: within-direction variance of widths; high variance = large pressure effect.
- Output: calibrated nib params as TOML → `shared/hands/nib_calibrated.toml` and print summary.

**CLI**: `scribesim measure-widths --letters reference/letters/ --traces reference/traces/ -o reference/widths/` and `scribesim calibrate-nib --widths reference/widths/ -o shared/hands/nib_calibrated.toml`

## Behavioral Change

- Produces `shared/hands/nib_calibrated.toml` with fitted `nib.angle_deg`, `nib.width_mm`, `nib.min_hairline_ratio`, `stroke.pressure_modulation_range`.
- The existing `konrad_erfurt_1457.toml` hand profile is **not automatically updated** — the operator reviews and merges the calibrated values manually. This avoids breaking the existing hand model without review.

## Planned Implementation Tasks

1. `scribesim/refextract/nibcal.py`: `measure_stroke_width()`, `cast_ray()`, `estimate_nib_angle()`, `estimate_nib_width()`, `estimate_pressure_modulation()`, `calibrate_nib()`
2. `measure-widths` + `calibrate-nib` CLI subcommands
3. Aggregate across all letter/trace pairs; save to `reference/widths/all_strokes.npz`
4. Write `nib_calibrated.toml` with fitting summary comment block
5. Unit tests: `cast_ray` on synthetic binary image returns correct distance; nib angle estimator recovers known angle from synthetic width/direction data; calibration pipeline runs end-to-end on test fixtures

## Risk + Rollback

- Calibration output is advisory (a TOML file). No existing code is modified automatically.
- Rollback: delete `nib_calibrated.toml`. No other code is affected.
- Image DPI must be correctly set for mm conversion to be accurate — expose as a CLI parameter.

## Evidence

