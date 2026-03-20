---
advance:
  id: ADV-WX-GROUNDTRUTH-001
  title: Groundtruth — Initial Implementation
  system: weather
  primary_component: groundtruth
  components:
  - groundtruth
  started_at: 2026-03-19T21:30:00Z
  started_by: null
  implementation_completed_at: 2026-03-19T19:25:49.959245Z
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

Update PAGE XML ground truth coordinates to account for spatial distortions introduced by weathering effects (primarily page_curl), and annotate glyph legibility for glyphs occluded or degraded by physical damage (missing corner on f04v, water damage on f04r-f05v).

## Behavioral Change

After this advance:
- PAGE XML glyph coordinates are transformed using the composed coordinate transform from the compositor, correcting for page_curl sinusoidal displacement so that bounding boxes align with the weathered image
- Glyphs falling within the f04v missing corner region (bottom-right, 35mm x 28mm) are marked with legibility 0.0 (completely illegible)
- Glyphs in water-damaged zones (f04r-f05v) receive graduated legibility scores from 0.0 to 1.0 based on their position relative to the water damage gradient (strongest damage at top, diminishing downward)
- All coordinate and legibility updates are performed in a single pass after all weathering effects are finalized, producing `{folio_id}_weathered.xml`

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-groundtruth-init`
- [ ] Tidy: define groundtruth module interface, PAGE XML parser/writer, coordinate transform applicator
- [ ] Test: write tests verifying coordinate transform application produces glyph positions within 2px of expected post-curl locations
- [ ] Test: verify glyphs inside f04v missing corner polygon (bottom-right 35mm x 28mm) receive legibility 0.0
- [ ] Test: verify glyphs outside f04v missing corner retain their original legibility
- [ ] Test: verify glyphs on f04r in the upper (heavily water-damaged) zone receive lower legibility scores than glyphs in the lower (lightly damaged) zone
- [ ] Test: verify glyphs on non-damaged folios (e.g., f01r) receive no legibility modification
- [ ] Implement: PAGE XML reader — parse ScribeSim PAGE XML to extract glyph bounding box coordinates
- [ ] Implement: coordinate transform applicator — apply composed displacement map from compositor to all glyph coordinates
- [ ] Implement: missing corner legibility marker — test each glyph centroid against the f04v corner polygon, set legibility 0.0 for contained glyphs
- [ ] Implement: water damage legibility scorer — compute per-glyph legibility based on position within the water damage gradient (top = 0.0, bottom = 1.0, interpolated between)
- [ ] Implement: PAGE XML writer — output `{folio_id}_weathered.xml` with updated coordinates and legibility attributes
- [ ] Validate: process f04v PAGE XML, confirm corner glyphs marked legibility 0.0, water-damaged glyphs scored on gradient, all coordinates shifted by page_curl transform within 2px tolerance

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- Coordinate precision loss from floating-point rounding during transform composition could exceed the 2px drift tolerance
- PAGE XML schema must match eScriptorium's expected import format; legibility attribute naming must be verified against TD-001-C

**Rollback:**
- Revert the feat/weather-groundtruth-init branch; original ScribeSim PAGE XML can be used with weathered images (coordinates will be slightly misaligned due to page curl but usable)

## Evidence

