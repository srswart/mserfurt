---
advance:
  id: ADV-SS-REFSELECT-007
  title: Percentage-Based Top-N Candidate Selection with Minimum Floor
  system: scribesim
  primary_component: refselect
  components:
  - refselect
  - cli
  started_at: 2026-03-21T23:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T17:40:47.135337Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence: []
  status: complete
---

## Objective

Replace the hardcoded absolute threshold (0.75) with a percentage-based top-N selection strategy that works reliably across any manuscript regardless of absolute score distribution.

The core problem: real manuscript pages score 0.59–0.65 composite; the 0.75 threshold selects nothing.  Absolute thresholds require per-manuscript calibration.  A percentage-based approach ("select the top 25% of candidates") is self-calibrating and always produces a useful result.

**Design:**

- `--top-pct FLOAT` (default: 0.25) — select the top N% of ranked candidates by composite score
- `--min-candidates INT` (default: 15) — hard floor: always select at least this many even if top-pct produces fewer
- `--selection-threshold FLOAT` (kept for backward compat, lower priority than top-pct when both provided)

When a batch has fewer than `--min-candidates` total pages, all pages are selected.  When `top-pct` would produce fewer than `min-candidates`, the floor takes precedence.

This means a user running against a 387-page manuscript with `--n-candidates 60 --top-pct 0.25` gets the top 15 pages selected (25% of 60 = 15, which equals the floor).  Against a small 20-page sample: `--top-pct 0.25 --min-candidates 15` → 15 selected (floor kicks in since 25% of 20 = 5 < 15).

## Behavioral Change

`analyze-reference` and `rank_candidates()` gain percentage-based selection.  Old `--selection-threshold` still accepted; when provided alongside `--top-pct`, threshold acts as an additional gate (candidate must be in top-pct AND above threshold).  Default invocation with no flags behaves as before except the default is now top-25% with a 15-candidate floor rather than 0.75 absolute.

`rank_candidates(record, selection_threshold, top_pct, min_candidates)` — new signature, all optional with backward-compatible defaults.

## Planned Implementation Tasks

1. Update `rank_candidates()` in `scribesim/refselect/provenance.py`:
   - Sort candidates by composite descending (already done)
   - Compute `n_select = max(min_candidates, ceil(len(candidates) * top_pct))`
   - Cap at `len(candidates)`
   - Mark top `n_select` as selected (subject to threshold gate if provided)
   - Update `selection_reason` / `rejection_reason` strings to reflect new logic
2. Update `analyze-reference` CLI: add `--top-pct` and `--min-candidates` flags; thread through to `rank_candidates`
3. Update `select-reference` CLI: add same flags (it calls `rank_candidates` in its own flow)
4. Update `__init__.py` exports if signature changes
5. Tests:
   - `test_rank_candidates_top_pct_basic` — top 25% of 20 candidates = 5 selected
   - `test_rank_candidates_min_floor` — top 25% of 8 candidates (=2) but floor=15 → all 8 selected (capped at total)
   - `test_rank_candidates_floor_respected` — 60 candidates, 25% = 15, floor = 15 → exactly 15
   - `test_rank_candidates_threshold_gate` — top-pct selects 10, but 3 are below threshold → 7 selected
   - `test_rank_candidates_backward_compat` — old threshold-only call still works

## Risk + Rollback

- **Backward compat**: `--selection-threshold` still accepted. Existing test calls pass threshold only → behaviour unchanged.
- **Rollback**: revert `rank_candidates` signature; remove new CLI flags. One function + two CLI decorators.
- **Min floor edge case**: if total candidates < min_candidates, all are selected. Logged clearly.

## Evidence

