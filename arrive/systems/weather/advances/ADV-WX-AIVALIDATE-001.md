---
advance:
  id: ADV-WX-AIVALIDATE-001
  title: AI Weathering Validation — Text Integrity and Damage Consistency
  system: weather
  primary_component: aivalidation
  components:
  - aivalidation
  started_at: 2026-03-22T17:45:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-22T17:50:03.487981Z
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

Implement the three-check validation pipeline (TD-011 Part 5 and Addendum A) that runs after AI weathering to verify: (V1) text positions have not shifted beyond 5px drift, (V2-A) pre-degraded lacunae and traces were not restored by the AI model, and (V3) water stain regions are spatially consistent between recto and verso of the same leaf. Validation results are appended to the folio's provenance JSON.

## Behavioral Change

After this advance:
- `validate_text_positions(clean_image, weathered_image, page_xml)` binarizes both images, extracts connected components in text regions per PAGE XML, computes centroid distances, returns `passed=True` if `max_drift_px < 5`
- `validate_pre_degradation_preserved(pre_degraded_image, weathered_image, degradation_mask, word_damage_map)` checks that:
  - Lacuna pixels (mask=255): mean brightness in weathered image is within 15% of local background (the AI did not restore ink)
  - Trace pixels (mask proportional): mean weathered brightness does not exceed mean pre-degraded brightness by more than 20% (the AI did not brighten faded text)
- `validate_damage_consistency(weathered_images, weathering_map)` finds all folio pairs sharing a leaf, detects stain regions via Otsu thresholding of the darkened zones, mirrors one image horizontally, computes IoU; reports pairs below 0.50
- `validate_folio(...)` runs all three checks and returns a `ValidationSummary` matching the provenance JSON `validation` block schema from TD-011 Part 6
- `validate_codex(weathered_dir, clean_dir, pre_degraded_dir, mask_dir, word_damage_dir, weathering_map, page_xml_dir)` runs `validate_folio` for all 34 pages and writes a summary report to `weather/validation_report.json`
- Validation failures are logged as warnings but do not abort the pipeline — the provenance JSON records the failure for human review

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/weather-aivalidate`
- [ ] Tidy: create `weather/aivalidation.py`; define `ValidationResult` and `ValidationSummary` dataclasses; no existing code modified
- [ ] Test: V1 — synthetic test where weathered image is a copy of clean: drift=0px, passed=True
- [ ] Test: V1 — synthetic test where weathered image is shifted 10px right: max_drift >= 10px, passed=False
- [ ] Test: V2-A — lacuna region in weathered image has same brightness as pre-degraded (AI didn't restore): passed=True
- [ ] Test: V2-A — lacuna region in weathered image is darkened (AI added ink): passed=False
- [ ] Test: V3 — two synthetic images with matching water stain regions, one horizontally flipped: IoU >= 0.50, passed=True
- [ ] Test: V3 — two synthetic images with non-overlapping stain regions: IoU < 0.50, issues list non-empty
- [ ] Test: `validate_folio` — returns ValidationSummary with all three check results
- [ ] Test: ValidationSummary serializes to JSON matching the provenance schema in TD-011 Part 6
- [ ] Implement: `_binarize_text_regions(image, page_xml)` — Otsu threshold within PAGE XML word bboxes
- [ ] Implement: `validate_text_positions(clean_image, weathered_image, page_xml)`
- [ ] Implement: `_detect_stain_region(image, weathering_map_entry)` — Otsu-based stain detection in expected water damage zone
- [ ] Implement: `validate_pre_degradation_preserved(pre_degraded_image, weathered_image, degradation_mask, word_damage_map)`
- [ ] Implement: `validate_damage_consistency(weathered_images, weathering_map)`
- [ ] Implement: `validate_folio(...)` — runs all three validators, returns ValidationSummary
- [ ] Implement: `validate_codex(...)` — batch validation across all 34 pages, writes report JSON
- [ ] Validate: run validate_folio on a dry_run result (pre-degraded image = weathered image); V1 should pass, V2-A should pass (no restoration), V3 is only meaningful with real AI output

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- V1 text position check depends on binarization quality: if the weathered image is very dark (heavy aging), Otsu may not separate ink from background, producing false centroid positions. May need adaptive thresholding
- V3 stain detection requires visible darkening in the water-damaged zone; if the AI applies very subtle staining, Otsu may not detect it, causing false "no stain found" rather than a proper IoU check
- Validation failures are expected on the first few AI weathering runs — the pipeline is designed to record and report them, not block output

**Rollback:**
- Revert the feat/weather-aivalidate branch; weathering proceeds without validation; provenance JSON lacks the validation block

## Evidence

