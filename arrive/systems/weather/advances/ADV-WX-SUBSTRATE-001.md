---
advance:
  id: ADV-WX-SUBSTRATE-001
  title: Substrate — Initial Implementation
  system: weather
  primary_component: substrate
  components:
  - substrate
  started_at: 2026-03-19T18:35:00Z
  started_by: null
  implementation_completed_at: 2026-03-19T18:40:51.738679Z
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
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Generate realistic vellum texture layers using multi-octave Perlin noise and Poisson-distributed follicle marks, supporting two distinct vellum stocks (standard warm cream for f01-f13, irregular slightly yellow for f14-f17) with optional tiled photograph blending and verso bleed-through simulation.

## Behavioral Change

After this advance:
- Substrate generation produces a vellum texture using 3-octave Perlin noise with follicle marks elongated along the grain direction, distinguishing standard stock (f01r-f13v, warm cream base) from irregular stock (f14r-f17v, shifted yellow, different noise seed)
- Vellum translucency produces verso bleed-through at 0.06 opacity, allowing faint show-through of the opposite page's ink
- Optional tiled vellum photograph blend composites a photographic vellum texture with the procedural layer for enhanced realism

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-substrate-init`
- [ ] Tidy: define substrate module interface, vellum stock enum (standard, irregular), and texture buffer format
- [ ] Test: write tests for Perlin noise generation (3 octaves, verify frequency doubling per octave), follicle mark distribution (Poisson spacing, elongation ratio along grain axis)
- [ ] Test: verify standard stock (f01r-f13v) produces warm cream base color distinct from irregular stock (f14r-f17v) yellow-shifted base
- [ ] Test: verify different noise seeds for standard vs irregular stock produce visually distinct textures
- [ ] Implement: multi-octave Perlin noise generator (3 octaves) with configurable persistence and lacunarity
- [ ] Implement: follicle mark renderer using Poisson disk sampling with elongated marks along vellum grain direction
- [ ] Implement: vellum stock selector that maps folio ranges to stock type (f01-f13 standard, f14-f17 irregular)
- [ ] Implement: vellum_color application with stock-specific base color values from ms-erfurt-560yr.toml
- [ ] Implement: vellum_translucency verso bleed-through at 0.06 opacity compositing
- [ ] Implement: optional tiled vellum photograph blend with alpha-weighted overlay
- [ ] Validate: render substrate for f01r (standard) and f14r (irregular), confirm visually distinct textures with correct color cast; verify bleed-through opacity measures at 0.06

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- Perlin noise seeding inconsistency across runs could break determinism requirements for reproducible manuscript generation
- Follicle mark density may need tuning per stock type to avoid visual artifacts at high DPI

**Rollback:**
- Revert the feat/weather-substrate-init branch; compositor falls back to flat color background if substrate is unavailable

## Evidence

