---
advance_id: ADV-OPTICS-001
system_id: weather
title: "Optics — Initial Implementation"
status: planned
started_at: ~
implementation_completed_at: ~
review_time_estimate_minutes: 25
review_time_actual_minutes: ~
components: [optics]
risk_flags: [new_dependency]
evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
tech_direction: [TD-001]
pipeline_position: 3
depends_on_advances: [weather/ADV-SUBSTRATE-001]
---

## Objective

Simulate digitization artifacts introduced by the scanning/photography process: page curl displacement from codex binding, camera lens vignetting, and uneven studio lighting, producing output that mimics real-world manuscript digitization rather than a flat synthetic render.

## Behavioral Change

After this advance:
- Page curl applies a sinusoidal displacement up to 1.0mm maximum on the gutter side of each page, warping the image and generating a coordinate transform map consumed by groundtruth for PAGE XML correction
- Camera vignette applies radial intensity falloff from center to corners at 0.08 strength, darkening page periphery
- Lighting gradient applies a directional intensity ramp at 150 degrees with an intensity range of 0.95 to 1.02, simulating off-axis studio illumination

## Pipeline Context

- **Position**: Phase 3 (Weather — Manuscript Aging & Weathering)
- **Upstream**: Substrate textures (page curl displaces the substrate base layer), ms-erfurt-560yr.toml for optics parameters
- **Downstream**: Optics output consumed by compositor (optics is the final effect layer); page curl coordinate transforms consumed by groundtruth for PAGE XML update
- **Contracts**: TD-001-E (Weathering profile TOML — optics section)

## Component Impact

```yaml
components: [optics]
system: weather
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-optics-init`
- [ ] Tidy: define optics module interface, coordinate transform format for page curl (displacement map or affine chain)
- [ ] Test: write tests for page_curl verifying sinusoidal displacement profile with 1.0mm max at gutter edge decaying to zero at fore-edge
- [ ] Test: verify page curl produces an invertible coordinate transform map suitable for groundtruth correction
- [ ] Test: verify camera_vignette at 0.08 strength produces measurable darkening at corners relative to center
- [ ] Test: verify lighting_gradient at 150 degrees direction produces intensity values within [0.95, 1.02] range across the page
- [ ] Implement: page_curl — sinusoidal x-displacement field (max 1.0mm at gutter), gutter side determined by recto/verso, with coordinate transform export
- [ ] Implement: camera_vignette — radial falloff from page center, strength 0.08, applied as multiplicative intensity modifier
- [ ] Implement: lighting_gradient — directional ramp at 150 degrees, intensity range [0.95, 1.02], applied as multiplicative intensity modifier
- [ ] Validate: render optics effects on f01r, confirm visible but subtle page curl at gutter, slight corner darkening from vignette, and directional brightness variation from lighting

## Risk + Rollback

**Risks:**
- Page curl coordinate transform must be precise enough for groundtruth to maintain 2px or better glyph position accuracy after correction
- Sinusoidal displacement may introduce interpolation artifacts at sub-pixel level; bicubic resampling recommended

**Rollback:**
- Revert the feat/weather-optics-init branch; compositor skips optics layer, groundtruth receives identity transform

## Evidence

| Type | Status | Notes |
|------|--------|-------|
| tdd:red-green | pending | |
| tidy:preparatory | pending | |
| tests:unit | pending | |

## Changes Made

_No changes yet._

## Check for Understanding

_To be generated after implementation._
