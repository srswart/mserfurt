---
advance:
  id: ADV-SS-NIB-002
  title: Physics-Based Nib Model — Direction-Dependent Width
  system: scribesim
  primary_component: render
  components:
  - render
  started_at: 2026-03-20T13:50:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T10:17:36.015214Z
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

Replace the current simplified nib model (elliptical, fixed pressure-to-width mapping) with the physics-based nib from TD-002 Part 2: `mark_width = nib_width * |sin(direction - nib_angle)| * pressure_factor + nib_width * flexibility * pressure`. Stroke width emerges from the interaction of nib angle and stroke direction, not from a design choice.

## Behavioral Change

After this advance:
- The `Nib` model has four physical properties: `width_mm`, `angle_deg`, `flexibility`, `cut_quality`
- Mark width at any point is computed from stroke direction and pressure: `nib.width * |sin(direction - nib.angle)| * pressure_factor(pressure) + nib.width * flexibility * pressure`
- Hairline strokes (direction parallel to nib angle) are genuinely thin — their thinness is governed by `cut_quality` (sharp nib = thinner hairlines)
- Full-width strokes (direction perpendicular to nib angle) show pressure-dependent spread via `flexibility`
- Attack pressure multiplier (1.15×) produces characteristic stroke-start thickening
- Release taper length controls how strokes thin at termination
- The thick/thin contrast of Bastarda letterforms emerges naturally from the 40° nib angle interacting with stroke directions, rather than being encoded in the glyph definitions

## Planned Implementation Tasks

- [ ] Tidy: extract nib model from `render/nib.py` into a standalone module with clear input/output interface
- [ ] Test: write tests — horizontal stroke at 40° nib produces expected width; vertical stroke produces different width; 45° stroke produces intermediate width; flexibility increases width under high pressure; cut_quality affects minimum hairline width
- [ ] Implement: `Nib` dataclass with `width_mm`, `angle_deg`, `flexibility`, `cut_quality`
- [ ] Implement: `mark_width(direction, pressure)` using the TD-002 formula
- [ ] Implement: `attack_pressure_multiplier` — applies pressure boost at stroke onset (first 15% of stroke length)
- [ ] Implement: `release_taper` — stroke width tapers over the final `release_taper_length` fraction of the stroke
- [ ] Integrate: update the rasterizer to call `mark_width(direction, pressure)` at each sample point instead of the current fixed pressure-to-width mapping
- [ ] Integrate: wire physics nib into the rasterizer so it is ACTIVE — all stroke rendering uses `mark_width(direction, pressure)` instead of the fixed mapping
- [ ] Validate: render f01r with physics nib; verify thick/thin contrast matches Bastarda characteristics; compare against v1
- [ ] Checkpoint: run `./snapshot.sh nib-002` — VISUAL DIFF vs movement-001 snapshot: thick/thin contrast should change character (emerges from nib angle × stroke direction, not pressure alone)

## Risk + Rollback

**Risks:**
- The nib model interacts tightly with existing glyph stroke definitions — pressure profiles in the glyph catalog may need rebalancing after the nib formula changes
- Performance: computing direction at every sample point adds overhead to rasterization

**Rollback:**
- Revert the branch; restore the previous `nib.py`

## Evidence

- [ ] 21 tests in `tests/test_physics_nib.py` covering direction-dependent width, flexibility, cut_quality, attack/release, stroke_direction
- [ ] 218 total tests pass (0 failures)
- [ ] Snapshot `nib-002` visually differs from `movement-001` — physics nib produces direction-dependent thick/thin contrast
