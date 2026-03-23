---
advance:
  id: ADV-SS-EVOLINE-002
  title: Evo Folio Rendering Default, Deep Quality, and Render Observability
  system: scribesim
  primary_component: evo
  components:
  - evo
  - cli
  - ink
  started_at: 2026-03-23T00:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-23T08:30:00Z
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

Make the `evo` folio renderer the default public path while keeping the legacy
plain renderer available for comparison and compatibility. Add explicit runtime
observability so a user can tell which rendering approach ran, whether the
render is still making progress, and whether the pressure heatmap actually
matches the page image. Add a natural-first `deep` quality mode that re-evolves
every word occurrence instead of reusing cached word genomes.

## Behavioral Change

After this advance:
- `scribesim render` defaults to `--approach evo`; `--approach plain` keeps the
  old raster path available
- `evo` folio renders now support `--evo-quality balanced|deep`
- `balanced` mode reuses evolved word genomes and records that reuse in the
  render report
- `deep` mode disables word-genome reuse and re-evolves each word occurrence,
  favoring natural variation over runtime
- every folio render writes `{folio_id}_render_report.json`, recording:
  - requested approach
  - page renderer
  - heatmap renderer
  - evolution settings
  - ink model mode
  - effective page nib width and angle
- every `evo` folio render writes `{folio_id}_render_progress.json`
- progress output is line-level in `balanced` mode and word-level in `deep`
  mode
- when `page_renderer = "evo"`, the pressure heatmap is now generated from the
  same evolved stroke sweep as the page image rather than from the legacy
  layout reconstruction path
- the public renderer contract is auditable from the report instead of requiring
  code inspection to determine whether GA, cache reuse, or the legacy heatmap
  path were used

## Planned Implementation Tasks

- [x] Add `--approach evo|plain` and keep `evo` as the default page renderer
- [x] Add `--evo-quality balanced|deep` to single-folio and batch render flows
- [x] Write a render report capturing renderer choice, GA settings, cache policy,
  ink model mode, and effective page parameters
- [x] Write a progress sidecar during folio rendering and print progress to the
  console
- [x] Emit per-line progress in balanced mode and per-word progress in deep mode
- [x] Route `evo` pressure heatmap generation through the same evolved stroke
  render pass as the page image
- [x] Test: CLI accepts deep mode and reports progress path
- [x] Test: `evo` report records `heatmap_renderer = "evo"`
- [x] Validate: render `f01r` in `balanced` and `deep` modes and inspect report
  and progress sidecars

## Risk + Rollback

**Risks:**
- `deep` mode is materially slower than cached balanced mode
- the render report becomes part of the operator workflow, so field drift will
  be confusing if not kept stable
- `evo` heatmap generation must remain faithful to the same stroke samples as
  the page render or downstream Weather targeting will become inconsistent again

**Rollback:**
- switch the CLI default back to `plain`
- force `--evo-quality balanced` and re-enable cache reuse for all public renders
- fall back to the legacy pressure heatmap path if the evolved heatmap path
  proves unstable

## Evidence

- [x] `uv run pytest tests/test_evo_heatmap.py tests/test_evo_progress.py tests/test_scribesim_cli.py`
- [x] `f01r_render_report.json` records `page_renderer = "evo"` and
  `heatmap_renderer = "evo"`
- [x] `f01r_render_progress.json` reaches `stage = "completed"` for real folio
  renders in both balanced and deep modes
