---
advance:
  id: ADV-SS-REFSELECT-001
  title: IIIF Manifest Fetch + Candidate Sampling + Analysis-Resolution Download (TD-009 Part 1)
  system: scribesim
  primary_component: refselect
  components:
  - refselect
  - cli
  started_at: 2026-03-21T16:10:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T17:00:00Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  - external_api
  evidence:
  - tdd:red-green
  - tests:unit
  status: complete
---

## Objective

Implement the IIIF download and candidate sampling stage of TD-009: given a IIIF manifest URL, fetch the manifest, sample candidate pages using a configurable strategy, and download them at analysis resolution (1500px).  A provenance skeleton JSON is written alongside every download operation so that provenance is never retrofitted.

**Module**: `scribesim/refselect/iiif.py`

Functions:
- `fetch_manifest(manifest_url: str) -> dict` — GET and parse a IIIF Presentation v2/v3 manifest; return normalised dict with `title`, `attribution`, `license`, `canvases` (list of `{id, label, image_url, service_url}`)
- `select_candidate_pages(manifest: dict, n_candidates: int = 15, strategy: str = "stratified", seed: int = 42) -> list[dict]` — four strategies: `random`, `stratified`, `text_pages_only`, `focused`
- `download_folio(canvas: dict, output_dir: Path, resolution: str = "analysis") -> Path` — downloads via IIIF Image API (`/full/1500,/0/default.jpg` for analysis; `/full/max/0/default.jpg` for extraction); falls back to direct URL if no service; returns local path
- `sanitize_filename(label: str) -> str` — strip unsafe chars, normalise Unicode, max 64 chars

**Module**: `scribesim/refselect/provenance.py` (skeleton only — full record in ADV-SS-REFSELECT-002)
- `new_provenance_record(manifest: dict, sampling: dict) -> dict` — creates the top-level provenance skeleton with `run_id`, `timestamp`, `operator`, `source_manuscript`, `sampling`, `candidates: []`
- `save_provenance(record: dict, output_path: Path)` — writes JSON

**CLI** (`scribesim/cli.py`):
- `scribesim download-folios --manifest <URL> --pages 5,8,12 --resolution max --output reference/selected/` — download specific pages at full resolution; writes provenance stub
- `scribesim select-reference --manifest <URL> --manifest-label "..." --sample 15 --strategy stratified --output reference/ --no-analyze` — download-only mode of the master pipeline command

## Behavioral Change

New module `scribesim/refselect/`. No changes to any existing rendering, extraction, or evolution code. Creates `reference/provenance/` and `reference/candidates/` directory trees.

## Planned Implementation Tasks

1. Create `scribesim/refselect/__init__.py`, `scribesim/refselect/iiif.py`, `scribesim/refselect/provenance.py`
2. Implement `fetch_manifest()` — handle both IIIF v2 (`sequences[0].canvases`) and v3 (`items`) structure; normalise to common dict
3. Implement `select_candidate_pages()` with all four strategies; validate `n_candidates ≤ total pages`
4. Implement `download_folio()` with IIIF Image API URL construction and direct-URL fallback; respect `resolution` parameter
5. Implement provenance skeleton: `run_id = f"ref-select-{timestamp}"`, write alongside every download
6. Add `download-folios` and download-only `select-reference` CLI subcommands
7. Unit tests: manifest parsing (synthetic fixture), sampling strategies (correct count, no out-of-bounds), filename sanitization, provenance JSON structure

## Risk + Rollback

- **New dependency**: `requests` — add to `pyproject.toml`. Available transitively but should be declared explicitly. No other new deps.
- **External API**: IIIF servers are external. Tests use a recorded fixture manifest (no live network calls in CI). Integration tests marked `@pytest.mark.network` and skipped by default.
- **IIIF v3 support**: Many newer manifests use v3 format (`items` not `sequences`). Both must be handled to avoid brittle pipeline.
- **Rollback**: entirely new module; removing it is safe with no downstream effects (ADV-SS-REFSELECT-002+ depend on it but none exist yet).

## Evidence

- [ ] **tdd:red-green**: Tests written before implementation; all 35 failed before `iiif.py` / `provenance.py` existed
- [ ] **tests:unit**: `tests/test_refselect_iiif.py` (25 tests), `tests/test_refselect_provenance.py` (10 tests) — 35 total, all green
- [ ] **tidy**: `requests>=2.28` declared in `pyproject.toml`; `scribesim/refselect/` package created as clean new module
