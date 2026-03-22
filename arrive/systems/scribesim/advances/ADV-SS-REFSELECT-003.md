---
advance:
  id: ADV-SS-REFSELECT-003
  title: Full Analysis A3-A7 + Composite Scoring + Candidate Ranking (TD-009 Part 3)
  system: scribesim
  primary_component: refselect
  components:
  - refselect
  started_at: 2026-03-21T18:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T19:00:00Z
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

Implement the remaining five analysis criteria (A3-A7) and the weighted composite scoring function from TD-009 Part 2.  All implementations are scipy/numpy only — the TD-009 spec references opencv (`cv2.distanceTransform`, `cv2.connectedComponentsWithStats`) but we replace these with pure-numpy equivalents consistent with the existing codebase.

**Module**: extend `scribesim/refselect/analysis.py`

- `analyze_script_consistency(image: np.ndarray) -> float` (A3) — divide binary image into 8 horizontal strips; per strip compute ink density (fraction dark pixels) and approximate stroke width via `scipy.ndimage.distance_transform_edt`; CV of width and density across strips → consistency score
- `analyze_text_density(image: np.ndarray) -> float` (A4) — locate text block via row/column projection bounding box; ink ratio within block (ideal 15–35%); page coverage fraction → density score
- `analyze_damage(image: np.ndarray) -> float` (A5) — stain detection: `scipy.ndimage.uniform_filter` (large kernel) on text block → low-freq background variation; foxing: std of non-ink pixels → high-freq noise score
- `analyze_thick_thin(image: np.ndarray) -> float` (A6) — `scipy.ndimage.distance_transform_edt` on binary image; 10th/90th percentile of ink-pixel distances → thick/thin ratio; score peaks at 3:1–5:1 (Bastarda ideal)
- `analyze_letter_variety(image: np.ndarray) -> float` (A7) — `scipy.ndimage.label` for connected components; filter to letter-sized blobs (0.3–3× median height); component count + aspect-ratio std → variety score
- `composite_suitability(scores: dict) -> float` — weighted average using TD-009 weights: ink_contrast 0.20, line_regularity 0.15, script_consistency 0.15, text_density 0.10, damage 0.15, thick_thin 0.15, letter_variety 0.10; handles missing criteria by renormalizing weights

Update `analyze_folio()` to run all seven criteria.  Update `rank_candidates()` to populate `selection_reason` / `rejection_reason` with the lowest-scoring criterion for rejected candidates.

## Behavioral Change

`analyze-reference` now produces a full 7-criterion score for each candidate.  Composite scores and rankings become meaningful.  Provenance JSON is enriched with per-criterion scores.

## Planned Implementation Tasks

1. **Tidy**: move `_otsu_threshold` from `segment.py` to `scribesim/refextract/utils.py` as `otsu_threshold(gray)`; update all callers (segment.py, analysis.py)
2. Implement A3 `analyze_script_consistency()` using `distance_transform_edt` + strip CV
3. Implement A4 `analyze_text_density()` — text block from projection bounding box; ink ratio + coverage
4. Implement A5 `analyze_damage()` — `uniform_filter` stain score + background pixel std for foxing
5. Implement A6 `analyze_thick_thin()` — `distance_transform_edt` percentile ratio; Bastarda score curve
6. Implement A7 `analyze_letter_variety()` — `scipy.ndimage.label` CC analysis; count + aspect ratio diversity
7. Implement `composite_suitability()` with renormalized weights for missing criteria
8. Update `analyze_folio()` and `rank_candidates()` with reason generation
9. Unit tests: each criterion returns higher score for the "good" synthetic case vs. the "bad" case; composite weights sum to 1.0; rejection reasons name the weakest criterion

## Risk + Rollback

- **No opencv**: `cv2.distanceTransform` → `scipy.ndimage.distance_transform_edt` (same algorithm, different API). `cv2.connectedComponentsWithStats` → `scipy.ndimage.label` + `np.where` for bounding boxes. Both are exact equivalents.
- **A3 strip width measurement**: `distance_transform_edt` on strips may be slow for large images. Downsample to 800px height before analysis if image is larger.
- **A7 letter-size threshold**: the `median_height * 0.3–3.0` filter is resolution-dependent. Compute threshold from the image's estimated x-height (from A2 line spacing) rather than absolute pixels.
- **Tidy risk**: moving `_otsu_threshold` is a rename-refactor. All callers are in the same repo; grep + replace is safe. Tag this as `tidy:preparatory` evidence.

## Evidence

- [ ] **tdd:red-green**: 21 tests written and confirmed failing before any A3-A7 code existed
- [ ] **tests:unit**: `tests/test_refselect_analysis_a3a7.py` — 22 tests, all green (79 total refselect suite)
