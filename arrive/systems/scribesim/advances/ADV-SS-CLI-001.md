---
advance:
  id: ADV-SS-CLI-001
  title: CLI — Initial Implementation
  system: scribesim
  primary_component: cli
  components:
  - cli
  started_at: 2026-03-19T12:00:00Z
  started_by: null
  implementation_completed_at: 2026-03-19T16:37:29.938109Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: in_progress
---

## Objective

Provide the command-line driver for ScribeSim, exposing subcommands that orchestrate scribal hand rendering, batch processing, hand inspection, and ground truth generation for the MS Erfurt 1457 pipeline.

## Behavioral Change

After this advance:
- `scribesim render <folio_id>` accepts a per-folio JSON (from XL Phase 1) and produces a page PNG at 300 DPI plus a pressure heatmap PNG
- `scribesim render-batch` processes all folios listed in `manifest.json`, respecting the modifier stack for per-folio hand variation
- `scribesim hand --show` prints the resolved hand parameters for a given folio, including base parameters from `konrad_erfurt_1457.toml` and all applied modifiers
- `scribesim groundtruth` emits PAGE XML (2019 schema) with glyph-level coordinates and TextEquiv

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/scribesim-cli-init`
- [ ] Tidy: set up ScribeSim package structure, `pyproject.toml` entry points, and CLI framework (Click/Typer)
- [ ] Test: write CLI invocation tests — verify `render` exits 0 with valid folio JSON, exits non-zero on missing manifest, `hand --show` outputs TOML-formatted parameters
- [ ] Implement: wire `render` subcommand to load manifest + folio JSON, resolve hand via modifier stack, invoke layout/render pipeline, write PNG + heatmap to output directory
- [ ] Implement: wire `render-batch` to iterate manifest entries, parallelise where possible, report per-folio status
- [ ] Implement: wire `hand --show` to load `konrad_erfurt_1457.toml`, apply folio-specific modifiers (e.g., pressure_increase for f06r), and print resolved values
- [ ] Implement: wire `groundtruth` subcommand to invoke PAGE XML generation post-render
- [ ] Validate: end-to-end smoke test with a single folio (f01r) producing PNG, heatmap, and PAGE XML

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- CLI argument parsing changes may break downstream scripting in Weather phase if subcommand signatures drift
- Dependency on XL export format — if per-folio JSON schema changes, CLI input validation will reject valid data

**Rollback:**
- Revert the `feat/scribesim-cli-init` branch; no persistent state is modified by the CLI itself

## Evidence

