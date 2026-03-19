---
advance:
  id: ADV-XL-CLI-001
  title: CLI — Initial Implementation
  system: xl
  primary_component: cli
  components:
  - cli
  started_at: 2026-03-19T00:00:00Z
  started_by: null
  implementation_completed_at: 2026-03-19T05:50:32.806181Z
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
  status: complete
---

## Objective

Build the command-line driver that orchestrates all XL pipeline stages, providing `xl translate`, `xl manifest`, `xl validate`, and `xl preview` commands. The CLI must accept `source/ms-erfurt-source-annotated.md` as input and coordinate the ingest-translate-register-folio-annotate-export sequence, emitting per-folio JSON, manifest.json, and PAGE XML to the output directory.

## Behavioral Change

After this advance:
- Running `xl translate --input source/ms-erfurt-source-annotated.md --output out/` executes the full pipeline and writes 17 folio JSON files plus manifest.json
- Running `xl validate out/` checks all emitted artifacts against TD-001-A (Folio JSON), TD-001-B (Manifest JSON), and TD-001-C (PAGE XML) contracts
- Running `xl preview out/folio-007r.json` renders a terminal preview of a single folio for quick inspection
- Running `xl manifest out/` regenerates the manifest from existing folio outputs without re-translating

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/xl-cli-init`
- [ ] Tidy: Set up Python package structure under `arrive/systems/xl/`, create `__main__.py` entry point, configure `pyproject.toml` with `xl` console script
- [ ] Test: Write CLI invocation tests — verify argument parsing for all four commands, verify `--input` path validation, verify `--output` directory creation, verify `--dry-run` flag skips API calls
- [ ] Implement: Build argument parser with subcommands (translate, manifest, validate, preview); wire up pipeline orchestration that calls ingest -> translate -> register -> folio -> annotate -> export in sequence; add `--folio` flag to restrict processing to a single folio (e.g., `--folio 7r` for the Eckhart folio); add `--dry-run` for testing without API calls; add structured logging with per-stage timing
- [ ] Validate: Run `xl translate --dry-run --input source/ms-erfurt-source-annotated.md` end-to-end and confirm it completes without error

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- Package structure decisions made here constrain all downstream components; incorrect module layout would require broad refactoring
- Orchestration order must match the dependency graph (ingest before translate, translate+register before folio, etc.) — misordering produces silent data errors

**Rollback:**
- Revert the `feat/xl-cli-init` branch; no persisted state or external dependencies to clean up

## Evidence

