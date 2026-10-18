---
advance:
  id: "ADV-SITE-DATA-001"
  title: "Manuscript & Edition Asset Pipeline — 34-Folio Web Dataset, Full 7-Section Edition Corpus, and Design Bundle Extraction"
  system: "site"
  primary_component: "data-assets"
  components: ["data-assets"]
  started_at: "2026-10-17T11:40:00Z"
  implementation_completed_at: 2026-10-17T13:04:36.983629Z
  review_time_estimate_minutes: 15
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 18
  risk_flags: []
  evidence: ["tests:unit"]
  model_usage: []
  status: complete
---

## Objective

Extract all embedded typographic and visual assets (`mobius.jpg`, `EB Garamond` normal/italic WOFF2 fonts) from `docs/site/MS Erfurt Aug. 12°47 — Edition & Manuscript.html`, optimize all 34 folio images (`f01r–f17v`), 16 bound bifolium spreads, and diagnostic callout sheets for web delivery, and compile `site/dist/data/site_data.json` containing the complete 7-section English critical edition + 34-folio CLIO-7 apparatus coordinates (`Lacunae & losses`, `Line confidence`, `Pressure analysis`, `Quill re-dips`, and FNHD transcriptions).

## Behavioral Change

After this advance:
- Running `python -m site_app.build_site_data` populates `site/dist/assets/` (Möbius vellum hero image, self-hosted WOFF2 fonts, 34 folio web images + thumbnails, 16 bound spreads, callout graphics) and `site/dist/data/site_data.json`.
- Every folio `f01r–f17v` has normalized percentage coordinates for damage/lacuna boxes, per-line confidence bars, emotional/pressure lines, and quill re-dip markers ready for the interactive Folio Viewer.

## Planned Implementation Tasks

- [x] branch: confirmed on the current working branch
- [ ] tidy: no preparatory refactor; this is a new pipeline
- [x] test: `tests/test_site.py` verifies asset extraction and `site_data.json` across all 34 folios and 7 sections
- [x] feat: implemented `site_app/build_site_data.py`

## Bug Fixes

- [x] None yet

## Risk + Rollback

- Risk: Large PNG folio images could slow initial page load if served unoptimized.
- Rollback: Remove `site/dist/` and `site_app/build_site_data.py`.

## Evidence

- [ ] tidy:preparatory
- [x] tdd:red-green
- [x] tests:unit

## CI Evidence Notes

- `python3 -m pytest tests/test_site.py -q` — 3 passed (2026-10-17).

## Changes Made

### 2026-10-17 - feat: initial advance scaffold
- `arrive/systems/site/advances/ADV-SITE-DATA-001.md`: authored advance specification.

### 2026-10-17 - feat: compile the web dataset and edition corpus
- `site_app/build_site_data.py`: extracts the Möbius hero and EB Garamond WOFF2 from the design bundle, converts 34 folios, clean plates, thumbs, 16 spreads, and callouts to JPEG, and writes `site/dist/data/site_data.json`. Existing JPEGs are left in place.
- Overlay boxes, confidence bars, hand lines, and quill dips are stored as percentages of the folio so the viewer can scale them with the image.
- Corpus counts written into the manuscript record are 34 pages, 88 damage spans, 254 emotional lines, and 180 quill re-dips.

## Check for Understanding

1. Why are damage boxes and confidence bars stored as percentages of the folio, and what misaligns in the viewer if those percentages are applied to a thumbnail instead of the full plate?
2. `build_site_data` skips a JPEG that already exists. After a folio is re-rendered, what has to be removed before the site shows the new plate?
3. The colophon prints 88, 254, and 180. Which catalogue lists do those counts come from, and what would a mismatch with the per-folio overlay arrays mean?
