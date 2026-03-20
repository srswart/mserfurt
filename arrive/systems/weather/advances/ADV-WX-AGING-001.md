---
advance:
  id: ADV-WX-AGING-001
  title: Aging — Initial Implementation
  system: weather
  primary_component: aging
  components:
  - aging
  started_at: 2026-03-19T20:00:00Z
  started_by: null
  implementation_completed_at: 2026-03-19T19:06:16.081374Z
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

Apply general aging effects that accumulate over 560 years of archival storage: edge darkening from oxidation and handling, foxing spots from fungal growth in a dry archive environment, and binding shadow from the codex gutter.

## Behavioral Change

After this advance:
- Edge darkening applies an 8mm-wide gradient along all four page edges with a maximum intensity of 15%, with corners receiving the strongest darkening (overlap of two edge gradients)
- Foxing generates 12 spots per page with diameters ranging from 0.3mm to 1.5mm, using a light color profile appropriate for dry archive conditions, placed with pseudo-random spatial distribution
- Binding shadow applies a 10mm-wide gradient along the gutter edge with 12% maximum darkening, simulating light falloff from the codex binding

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-aging-init`
- [ ] Tidy: define aging module interface, page dimension resolver (mm-to-pixel conversion for edge widths and spot diameters)
- [ ] Test: write tests for edge_darkening verifying 8mm gradient width, 15% max intensity, and corner accumulation (two overlapping gradients)
- [ ] Test: verify foxing generates exactly 12 spots with diameters in [0.3mm, 1.5mm] range and dry archive color profile
- [ ] Test: verify binding_shadow produces 10mm gradient on gutter side with 12% max darkening
- [ ] Test: verify recto pages have gutter shadow on left and verso pages on right
- [ ] Implement: edge_darkening — distance-from-edge gradient (8mm width, 15% max) applied to all four edges with multiplicative corner accumulation
- [ ] Implement: foxing — pseudo-random spot placement (12 spots), diameter sampling from [0.3mm, 1.5mm] uniform distribution, dry archive light brown color
- [ ] Implement: binding_shadow — gutter-side gradient (10mm width, 12% max), side determined by recto/verso folio designation
- [ ] Validate: render aging effects on f01r and f01v, confirm edge darkening visible at corners, foxing spots are subtle and dry-archive colored, binding shadow appears on correct gutter side for each

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- mm-to-pixel conversion depends on knowing the page DPI; incorrect DPI would scale all aging effects incorrectly
- Foxing spot placement must avoid clustering that looks unnatural; may need minimum separation constraint

**Rollback:**
- Revert the feat/weather-aging-init branch; compositor skips aging layer with no downstream impact on damage or optics

## Evidence

