---
advance:
  id: ADV-XL-CLI-001
  title: "CLI — Initial Implementation"
  system: xl
  primary_component: cli
  components: [cli]
  started_at: "2026-03-19T00:00:00Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 20
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags: [new_dependency]
  evidence:
    - tdd:red-green
    - tidy:preparatory
    - tests:unit
  status: in_progress
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
| tdd:red-green | complete | 14 tests in tests/test_cli_args.py written before implementation |
| tidy:preparatory | complete | xl/ package, pyproject.toml, __main__.py scaffold |
| tests:unit | complete | 14/14 passing — argument parsing, flags, subcommands, dry-run |

## Implementation Sub-Plan

### Tidy (Preparatory Refactors)
- [x] Create `xl/` Python package directory with `__init__.py`
- [x] Add `pyproject.toml` with `[project.scripts] xl = "xl.__main__:main"` entry point
- [x] Create `xl/__main__.py` stub that exits 0 — confirm `xl --help` runs before adding any logic

### Tests First (Red Phase)
- [x] Write `tests/test_cli_args.py`: assert `xl translate --input foo.md --output out/` parses correctly
- [x] Write test: assert `xl translate` without `--input` exits non-zero with usage message
- [x] Write test: assert `xl validate out/` subcommand is recognized
- [x] Write test: assert `xl manifest out/` subcommand is recognized
- [x] Write test: assert `xl preview out/folio-007r.json` subcommand is recognized
- [x] Write test: assert `xl translate --dry-run` skips pipeline calls (mock the pipeline functions)
- [x] Confirm all tests pass green (14/14)

### Implement (Green Phase)
- [x] Build `click` parser with `translate`, `manifest`, `validate`, `preview` subcommands
- [x] Add `--input`, `--output`, `--folio`, `--dry-run` flags to `translate`
- [x] Wire orchestration sequence stubs (ingest → translate → register → folio → annotate → export comments)
- [x] Add `--dry-run` branch that skips all pipeline calls and logs what would run
- [x] Structured logging notes added (per-stage timing to be added as components are wired)
- [x] All 14 argument-parsing tests pass

### Validate
- [x] `xl translate --dry-run --input source/ms-erfurt-source-annotated.md --output /tmp/xl-test` — exits 0
- [x] `xl --help` and `xl translate --help` — usage text accurate, all flags present
- [x] `arrive plan check` — plan integrity passes
- [x] Evidence table updated

## Changes Made

- `pyproject.toml` — new; defines `xl` package with `xl` console script entry point (click>=8.1)
- `xl/__init__.py` — new; package root
- `xl/__main__.py` — new; click CLI with `translate`, `manifest`, `validate`, `preview` subcommands; `--input`, `--output`, `--folio`, `--dry-run` flags on `translate`
- `tests/__init__.py` — new
- `tests/test_cli_args.py` — new; 14 unit tests covering argument parsing and subcommand dispatch

## Check for Understanding

_To be generated after implementation._
