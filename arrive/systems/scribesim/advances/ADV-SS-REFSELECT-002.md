---
advance:
  id: ADV-SS-REFSELECT-002
  title: Core Analysis A1+A2 (Ink Contrast, Line Regularity) + Full Provenance Record (TD-009 Part 2)
  system: scribesim
  primary_component: refselect
  components:
  - refselect
  - cli
  started_at: 2026-03-21T17:05:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T17:45:00Z
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

Implement the two highest-priority analysis criteria from TD-009 (A1 ink contrast, A2 line regularity) and the complete provenance record structure.  These two criteria alone are sufficient for a usable ranking.  All implementations use numpy/scipy only — no opencv.

**Module**: `scribesim/refselect/analysis.py`

- `analyze_ink_contrast(image: np.ndarray) -> float` — Otsu valley depth + peak distance score; reuse `_otsu_threshold` from `scribesim/refextract/segment.py` rather than duplicating it; returns 0.0–1.0
- `analyze_line_regularity(image: np.ndarray) -> float` — horizontal projection profile; `scipy.signal.find_peaks` to locate text-line peaks; coefficient of variation of inter-line spacing + line count score; returns 0.0–1.0
- `analyze_folio(image_path: Path) -> dict` — runs all available criteria (A1+A2 in this advance), returns score dict with `composite` computed from available weights

**Module**: `scribesim/refselect/provenance.py` (extend from ADV-SS-REFSELECT-001)

- `add_candidate(record: dict, canvas: dict, image_path: Path, scores: dict) -> None` — append a fully scored candidate entry to `record["candidates"]`
- `rank_candidates(record: dict) -> None` — sort candidates by composite score descending; set `rank` field on each; set `selected` to `true` for those above `selection_threshold` (default 0.75)
- `update_provenance(record: dict, output_path: Path)` — rewrite the JSON file in place
- `load_provenance(path: Path) -> dict` — read an existing provenance record

**CLI**:
- `scribesim analyze-reference --input reference/candidates/ --output reference/analysis/ --report reference/analysis/report.html` — analyzes all JPGs in input dir, writes `scores.csv` and updated provenance JSON; report deferred to ADV-SS-REFSELECT-004

## Behavioral Change

Extends `scribesim/refselect/` with analysis and full provenance support.  The provenance JSON schema is now stable: all later advances (A3-A7, report, multi-manuscript) extend it without breaking changes.

## Planned Implementation Tasks

1. Implement `analyze_ink_contrast()` — reuse `_otsu_threshold` from segment.py (import directly; do not copy); add histogram valley depth and peak-distance sub-scores
2. Implement `analyze_line_regularity()` — same projection approach as in `segment_lines()` but scored rather than sliced; `find_peaks` on smoothed row-ink profile; return regularity + line-count composite
3. Implement `analyze_folio()` — load image (PIL → grayscale numpy), run A1+A2, return `{ink_contrast, line_regularity, composite}` dict; partial composite uses only available criteria weights renormalized to 1.0
4. Implement full provenance candidate schema — `canvas_label`, `canvas_id`, `image_url`, `download_resolution`, `scores`, `rank`, `selected`, `selection_reason` / `rejection_reason`
5. Implement `rank_candidates()` and `update_provenance()`
6. Add `analyze-reference` CLI subcommand; write `scores.csv` alongside provenance JSON
7. Unit tests: `analyze_ink_contrast` returns higher score for high-contrast synthetic image; `analyze_line_regularity` returns higher score for regular-spaced rows vs. irregular; provenance JSON round-trips correctly; `rank_candidates` orders by composite

## Risk + Rollback

- **Otsu reuse**: importing `_otsu_threshold` from `segment.py` (private function) creates a coupling. If that function moves, this breaks. Mitigation: move it to `scribesim/refextract/utils.py` as a public function during tidy phase.
- **No opencv**: TD-009 spec uses `cv2.threshold` for Otsu — replaced with the existing pure-numpy implementation. All other A1/A2 logic uses scipy only.
- **Provenance schema stability**: the JSON schema defined here is the canonical contract for all downstream advances. Changes after this point require a migration note.

## Evidence

- [ ] **tdd:red-green**: 22 tests written and confirmed failing before `analysis.py` / provenance extensions existed
- [ ] **tidy:preparatory**: `_otsu_threshold` moved to `scribesim/refextract/utils.py` as public `otsu_threshold`; segment.py updated
- [ ] **tests:unit**: `tests/test_refselect_analysis.py` (13 tests), `tests/test_refselect_provenance2.py` (9 tests) — 22 total, all green
