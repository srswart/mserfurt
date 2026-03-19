---
advance_id: ADV-CLI-001
system_id: xl
title: "CLI — Initial Implementation"
status: planned
started_at: ~
implementation_completed_at: ~
review_time_estimate_minutes: 20
review_time_actual_minutes: ~
components: [cli]
risk_flags: [new_dependency]
evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
tech_direction: [TD-001]
pipeline_position: 1
depends_on_advances: []
---

## Objective

Build the command-line driver that orchestrates all XL pipeline stages, providing `xl translate`, `xl manifest`, `xl validate`, and `xl preview` commands. The CLI must accept `source/ms-erfurt-source-annotated.md` as input and coordinate the ingest-translate-register-folio-annotate-export sequence, emitting per-folio JSON, manifest.json, and PAGE XML to the output directory.

## Behavioral Change

After this advance:
- Running `xl translate --input source/ms-erfurt-source-annotated.md --output out/` executes the full pipeline and writes 17 folio JSON files plus manifest.json
- Running `xl validate out/` checks all emitted artifacts against TD-001-A (Folio JSON), TD-001-B (Manifest JSON), and TD-001-C (PAGE XML) contracts
- Running `xl preview out/folio-007r.json` renders a terminal preview of a single folio for quick inspection
- Running `xl manifest out/` regenerates the manifest from existing folio outputs without re-translating

## Pipeline Context

- **Position**: Phase 1 (XL — Reverse Translation & Folio Structuring)
- **Upstream**: Raw annotated manuscript at `source/ms-erfurt-source-annotated.md`
- **Downstream**: Coordinates all XL components; final outputs consumed by ScribeSim (Phase 2) and Weather (Phase 3)
- **Contracts**: TD-001-A (Folio JSON), TD-001-B (Manifest JSON), TD-001-C (PAGE XML) — the CLI invokes validation against all three

## Component Impact

```yaml
components: [cli]
system: xl
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/xl-cli-init`
- [ ] Tidy: Set up Python package structure under `arrive/systems/xl/`, create `__main__.py` entry point, configure `pyproject.toml` with `xl` console script
- [ ] Test: Write CLI invocation tests — verify argument parsing for all four commands, verify `--input` path validation, verify `--output` directory creation, verify `--dry-run` flag skips API calls
- [ ] Implement: Build argument parser with subcommands (translate, manifest, validate, preview); wire up pipeline orchestration that calls ingest -> translate -> register -> folio -> annotate -> export in sequence; add `--folio` flag to restrict processing to a single folio (e.g., `--folio 7r` for the Eckhart folio); add `--dry-run` for testing without API calls; add structured logging with per-stage timing
- [ ] Validate: Run `xl translate --dry-run --input source/ms-erfurt-source-annotated.md` end-to-end and confirm it completes without error

## Risk + Rollback

**Risks:**
- Package structure decisions made here constrain all downstream components; incorrect module layout would require broad refactoring
- Orchestration order must match the dependency graph (ingest before translate, translate+register before folio, etc.) — misordering produces silent data errors

**Rollback:**
- Revert the `feat/xl-cli-init` branch; no persisted state or external dependencies to clean up

## Evidence

| Type | Status | Notes |
|------|--------|-------|
| tdd:red-green | pending | |
| tidy:preparatory | pending | |
| tests:unit | pending | |

## Changes Made

_No changes yet._

## Check for Understanding

_To be generated after implementation._
