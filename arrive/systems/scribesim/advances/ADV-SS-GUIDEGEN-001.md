---
advance:
  id: ADV-SS-GUIDEGEN-001
  title: Extracted Letterform Guides — DTW Averaging + Genome Seeding (TD-008 Steps 7 + integration)
  system: scribesim
  primary_component: guides
  components:
  - guides
  - refextract
  - evo
  started_at: 2026-03-21T14:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T11:42:49.988532Z
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
  - tests:integration
  status: complete
---

## Objective

Two parts:

**Part A — Build extracted guides** (`scribesim/refextract/guidegen.py`):
- `normalize_trace(segments, x_height_px)` — map to normalized coordinate system: baseline at y=0, x-height at y=1, start at x=0.
- `dtw_align(trace, reference)` — Dynamic Time Warping alignment of two normalized point sequences. Return aligned version of `trace` that matches `reference`'s time steps.
- `average_traces(traces)` — iterative averaging (3 iterations): align all traces to running mean, recompute mean.
- `build_letterform_guide(letter, exemplar_traces) -> LetterformGuide` — normalize, DTW-average, fit Bézier to averaged path, extract keypoints (start, end, direction reversals, extrema), compute `x_advance`.
- Output: `shared/hands/guides_extracted.toml` — one guide per letter, all 20+ letters covered from `reference/traces/`.

**CLI**: `scribesim build-guides --traces reference/traces/ -o shared/hands/guides_extracted.toml`

**Part B — Wire into genome seeding**:
- Update `scribesim/guides/__init__.py` or `scribesim/evo/genome.py` `genome_from_guides()` to prefer loading from `guides_extracted.toml` when present, falling back to the hand-defined guides.
- This means evolution seeds immediately from extracted Bastarda geometry rather than guessed keypoints.
- Add `guides_path` parameter to `genome_from_guides()` for explicit override in tests and CLI.

## Behavioral Change

- `genome_from_guides()` will produce different (better) seed genomes once `guides_extracted.toml` is present. Evolution convergence speed should improve noticeably.
- The hand-defined guides in `scribesim/guides/` remain unchanged as fallback — no breaking change.
- Letters not yet in `guides_extracted.toml` continue using the hand-defined fallback.

## Planned Implementation Tasks

1. `scribesim/refextract/guidegen.py`: `normalize_trace()`, `dtw_align()`, `average_traces()`, `build_letterform_guide()`, `extract_keypoints()`
2. TOML output for `guides_extracted.toml` — matching the format of existing `scribesim/guides/` TOML files
3. `build-guides` CLI subcommand
4. Update `genome_from_guides()`: load `guides_extracted.toml` if `SCRIBESIM_GUIDES` env var or `guides_path` param points to it; otherwise auto-detect `shared/hands/guides_extracted.toml`; final fallback to hand-defined
5. Update `run_evolution.sh` to pass `guides_path` once `guides_extracted.toml` is available
6. Integration test: evolve "und" with extracted guides; confirm F4 (style consistency) ≥ 0.70 (vs ~0.55 with hand-defined guides)
7. Unit tests: `normalize_trace` maps known coords correctly; `dtw_align` produces lower L2 distance than unaligned; `build_letterform_guide` produces valid `LetterformGuide` with correct `x_advance`

## Risk + Rollback

- DTW averaging quality depends on having 3+ good traces per letter. Letters with <3 traces will fall back to the hand-defined guide.
- Rollback: delete `guides_extracted.toml`. `genome_from_guides()` falls back to hand-defined guides automatically.
- F1/F4 fitness scores will shift once new guides are seeding the population — expected improvement.

## Evidence

