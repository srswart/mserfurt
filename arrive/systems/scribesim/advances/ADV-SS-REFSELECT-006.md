---
advance:
  id: ADV-SS-REFSELECT-006
  title: Fix analyze-reference / download-selected Canvas ID Round-Trip
  system: scribesim
  primary_component: refselect
  components:
  - refselect
  - cli
  started_at: 2026-03-21T22:30:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T17:30:03.144512Z
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

Fix the broken `analyze-reference` → `download-selected` workflow.  Currently `analyze-reference` clears the `candidates` array in provenance and re-populates it with synthetic stubs (id = jpg stem, image_url = ""), discarding the real IIIF canvas IDs that `select-reference` stored.  Downstream `download-selected` then fails to match any canvas in the manifest.

**Approach — in-place update (Option A):**

Instead of clearing and re-adding candidates, `analyze-reference` should *update* existing candidate records in-place by matching on `canvas_label` (derived from the JPG filename stem).  Analysis scores are merged into the existing record; all original IIIF fields (`id`, `image_url`, `service_url`) are preserved.

If no existing provenance is found (scores-only mode), behaviour is unchanged — synthetic stubs are written as before, with a warning that `download-selected` will not work.

## Behavioral Change

`analyze-reference` with an existing `provenance.json` no longer clears and rewrites candidates.  After the fix:

```
select-reference  →  provenance.json with real canvas IDs
analyze-reference →  scores merged into same records, canvas IDs intact
download-selected →  resolves canvas IDs → full-res download works
```

All existing `analyze-reference` CLI flags (`--input`, `--report`, `--selection-threshold`) unchanged.

## Planned Implementation Tasks

1. In `analyze_reference` CLI handler: after loading provenance, build a lookup `{canvas_label: candidate_record}` from existing candidates
2. After scoring each JPG, derive `canvas_label` from `jpg.stem` (same logic used when writing) and update the matching record's score fields in-place
3. If no match found (e.g. extra JPG not in provenance), append a synthetic stub with a `"warn_no_canvas_id": true` flag
4. Update `rank_candidates` call path — still runs after all scores are merged
5. Update `add_candidate` usage: only called for the no-provenance (scores-only) path
6. Tests:
   - `test_analyze_reference_preserves_canvas_ids` — provenance with real canvas IDs survives an analyze-reference pass
   - `test_analyze_reference_scores_merged` — composite/criterion scores appear on existing candidate records
   - `test_analyze_reference_unmatched_appended_with_flag` — extra JPG not in provenance gets synthetic stub with warn flag

## Risk + Rollback

- **Backward compat**: if no provenance.json is present, behaviour is identical to current. Zero risk to scores-only workflows.
- **Label matching**: relies on `jpg.stem == canvas_label` convention established in `select-reference`. If a user renames the JPG, the match will fail and a stub is appended. Acceptable — the warning flag makes this visible.
- **Rollback**: revert the in-place update logic; restore the clear+re-add path. One function change.

## Evidence

