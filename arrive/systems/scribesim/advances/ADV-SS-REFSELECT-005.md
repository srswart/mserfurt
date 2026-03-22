---
advance:
  id: ADV-SS-REFSELECT-005
  title: Multi-Manuscript Support + TD-008 Provenance Integration (TD-009 Parts 5 + 6)
  system: scribesim
  primary_component: refselect
  components:
  - refselect
  - refextract
  - cli
  started_at: 2026-03-21T20:10:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T21:00:00Z
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

Extend the selection pipeline to handle multiple IIIF manifests in a single run (cross-manuscript analysis), and wire the provenance chain into TD-008 extraction so that every letter crop and extracted guide carries a traceable link back to its source folio and selection run.

**Part A — Multi-manuscript `select-reference`**:

Extend `scribesim select-reference` to accept multiple `--manifest` / `--manifest-label` pairs:
```
scribesim select-reference \
    --manifest <URL1> --manifest-label "Cgm 100" \
    --manifest <URL2> --manifest-label "Cgm 452" \
    --sample 10 --output reference/
```

The provenance record gains a `source_manuscripts` array (replacing the single `source_manuscript`).  Candidates are tagged with their source manuscript.  Composite ranking is cross-manuscript — the best pages from any manuscript win.

Changes to `scribesim/refselect/iiif.py`:
- `fetch_all_manifests(manifest_urls: list[str], labels: list[str]) -> list[dict]` — fetch in parallel (threadpool, max 4 workers)
- `select_candidates_multi(manifests, n_per_manuscript, strategy) -> list[dict]` — stratified sampling per manuscript, then merge

Changes to `scribesim/refselect/provenance.py`:
- `new_multi_provenance_record(manifests, sampling)` — multi-source variant
- Provenance schema: `source_manuscripts: [{institution, shelfmark, manifest_url, ...}]`; each candidate gets `source_manuscript_label` field

**Part B — TD-008 provenance integration**:

Add `--provenance` flag to the `scribesim extract-letters` CLI subcommand.  When provided, the extraction run:
1. Reads the referenced provenance JSON to get `selected_folios` and their `image_url` / full-res paths
2. Tags each letter crop with its source folio in the filename: `{shelfmark}_{folio}_{char}_{nnn}.png`
3. Writes a provenance extension file alongside the letter crops: `reference/extracted/provenance_chain.json` — maps each crop filename → `{run_id, canvas_label, canvas_id, image_url, selection_rank, composite_score}`

This creates the complete traceability chain: source manuscript → selected folio → letter crop → extracted genome.

## Behavioral Change

`select-reference` now accepts multiple manifests.  `extract-letters --provenance <path>` produces tagged crops and a provenance chain JSON.  No changes to analysis logic or existing single-manifest behavior.

## Planned Implementation Tasks

1. Extend `fetch_manifest()` error handling — timeouts (30s), HTTP errors, malformed manifests all produce informative messages and skip that manifest
2. Implement `fetch_all_manifests()` with `concurrent.futures.ThreadPoolExecutor`
3. Implement `select_candidates_multi()` — per-manuscript stratified sampling; merge + deduplicate by canvas ID
4. Update provenance schema for multi-source; backward-compatible (single-manuscript provenance records still load correctly via schema migration shim)
5. Add `--provenance` flag to `extract-letters` CLI; implement crop tagging and provenance chain writer
6. Integration test: two fixture manifests (3 canvases each); verify combined ranking has candidates from both; verify crop filenames contain shelfmark; verify provenance chain JSON links each crop to its canvas
7. Unit tests: parallel fetch returns correct count; `select_candidates_multi` respects n_per_manuscript; schema migration shim upgrades v1 (single) provenance to multi-source format

## Risk + Rollback

- **Parallel fetching**: IIIF servers may rate-limit. Use a 1s delay between requests per server (by hostname) in the threadpool. Configurable via `--request-delay` flag.
- **Schema migration**: provenance records written by ADV-SS-REFSELECT-001/002 use single `source_manuscript`. The shim wraps it in a `source_manuscripts` list on load. No rewriting of old files.
- **Provenance chain size**: if extraction produces 5000+ crops, the provenance chain JSON may be large. Store as JSON Lines (`.jsonl`) instead for streaming-friendly access.
- **Rollback**: the `--provenance` flag is additive and optional. Removing it has no effect on existing `extract-letters` behavior.

## Evidence

- [ ] **tdd:red-green**: 18 tests written before implementation; all confirmed red → green
- [ ] **tests:unit**: `test_refselect_multi.py` (11), `test_refselect_provenance_chain.py` (7) — 18 tests
- [ ] **tests:integration**: schema migration shim tested across old+new provenance formats; cross-manuscript candidate tagging integration validated
- [ ] **Full suite**: 116/116 green (2026-03-21)
