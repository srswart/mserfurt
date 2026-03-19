---
advance:
  id: ADV-SS-TESTS-001
  title: "Tests — Initial Implementation"
  system: scribesim
  primary_component: tests
  components: [tests]
  started_at: ~
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags: [new_dependency]
  evidence:
    - tdd:red-green
    - tidy:preparatory
    - tests:unit
  status: planned
---

## Objective

Implement the integration and validation test suite for ScribeSim, covering golden image comparison, ground truth IoU validation, hand variation distinguishability, deterministic rendering, sitting boundary ink effects, and German-specific glyph correctness.

## Behavioral Change

After this advance:
- Golden image tests compare rendered folio PNGs against reference images using perceptual hashing (pHash), catching visual regressions while tolerating minor anti-aliasing differences
- Ground truth IoU validation tests confirm that PAGE XML glyph polygons achieve IoU >= 0.95 against the corresponding rendered pixel regions
- Hand variation tests verify that f01r (baseline hand) and f14r (fatigue/tremor hand) produce visually distinguishable output, measured by perceptual hash distance exceeding a minimum threshold
- Determinism tests render the same folio with the same seed twice and assert bitwise-identical PNG output
- Sitting boundary tests verify that f07r exhibits a measurable ink density shift at the multi-sitting boundary point
- German-specific glyph tests confirm correct rendering of long s, esszett ligature, and umlauted vowels (a/o/u with superscript-e)

## Pipeline Context

- **Position**: Phase 2 (ScribeSim — Scribal Hand Simulation)
- **Upstream**: Rendered page PNGs and pressure heatmaps from render; PAGE XML from groundtruth; glyph catalog from glyphs; hand parameters from hand
- **Downstream**: Test pass/fail gates the release of ScribeSim outputs to Weather (Phase 3); golden images serve as regression baselines for future changes
- **Contracts**: TD-001-F (Pressure heatmap PNG — tests validate heatmap format and value ranges), TD-001-C (PAGE XML — tests validate schema compliance and IoU targets)

## Component Impact

```yaml
components: [tests]
system: scribesim
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/scribesim-tests-init`
- [ ] Tidy: set up test infrastructure — golden image storage directory, pHash comparison utility, IoU computation helper, test fixtures for representative folios (f01r, f06r, f07r, f07v, f14r)
- [ ] Test: golden image tests — render each fixture folio, compare pHash against stored reference, fail if hamming distance exceeds threshold
- [ ] Test: ground truth IoU — for each fixture folio, load PAGE XML glyph polygons, rasterize polygons to a mask, compute IoU against rendered glyph pixels, assert >= 0.95
- [ ] Test: hand variation — render f01r and f14r, compute pHash distance, assert distance exceeds minimum distinguishability threshold (confirming tremor and spacing drift produce visible differences)
- [ ] Test: determinism — render f01r twice with seed=42, assert byte-for-byte PNG identity
- [ ] Test: sitting boundary — render f07r, extract pixel intensity samples before and after the sitting boundary, assert statistically significant density shift
- [ ] Test: German glyphs — render text containing long s, round s, esszett, and umlauted vowels; verify each glyph occupies a distinct bounding box and renders with correct stroke count
- [ ] Validate: run full test suite, generate initial golden images for baseline, document pHash thresholds and IoU margins

## Risk + Rollback

**Risks:**
- Golden image baselines are fragile across platform/compiler changes; pHash thresholds must be calibrated to tolerate acceptable rendering differences without masking real regressions
- IoU computation depends on accurate polygon rasterization matching the render engine's anti-aliasing behaviour; mismatched rasterization will produce artificially low IoU scores

**Rollback:**
- Revert the `feat/scribesim-tests-init` branch; tests are read-only and do not modify production outputs

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
