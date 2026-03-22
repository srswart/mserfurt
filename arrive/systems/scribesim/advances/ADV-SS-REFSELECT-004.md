---
advance:
  id: ADV-SS-REFSELECT-004
  title: Visual HTML Report + Human Approval + Full-Resolution Download (TD-009 Parts 4 + 6)
  system: scribesim
  primary_component: refselect
  components:
  - refselect
  - cli
  started_at: 2026-03-21T19:10:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T20:00:00Z
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

Produce the HTML visual report for human review, close the human-approval loop (operator confirms or overrides the automatic selection, adds notes), and trigger full-resolution download of the approved folios.  Also adds the provenance CLI subcommands (`provenance show`, `provenance cite`).

**Module**: `scribesim/refselect/report.py`

- `generate_html_report(record: dict, candidate_image_dir: Path, output_path: Path) -> Path` — produces a self-contained HTML file (no external CDN) with:
  - One card per candidate, sorted by rank
  - Thumbnail (scaled from the analysis-resolution download)
  - Horizontal bar chart per criterion (ASCII-style using HTML/CSS, no JS required)
  - SELECTED / REJECTED badge with reason
  - Composite score and rank

**Module**: extend `scribesim/refselect/provenance.py`

- `apply_human_approval(record: dict, approved: list[str], notes: str) -> None` — sets `selected: true/false` on the specified canvas labels; records `human_approved: true`, `human_notes`, updates `selection_summary`
- `cite_provenance(record: dict, fmt: str = "bibtex") -> str` — formats the source manuscript as a citation; supports `bibtex` and `chicago` formats

**CLI** (extend `scribesim/cli.py`):
- `scribesim select-reference ... --analyze --report reference/analysis/report.html` — full pipeline including report; opens report in browser if `--open` flag
- `scribesim download-selected --provenance <path> --resolution max --output reference/selected/` — re-downloads human-approved folios at full resolution; updates provenance with full-res paths
- `scribesim provenance show <path>` — pretty-print summary table to terminal
- `scribesim provenance cite <path> --format bibtex` — emit citation string

## Behavioral Change

Completes the TD-009 selection loop from download → analysis → human review → full-res download.  After this advance, a user can run the full `select-reference` pipeline end-to-end and hand selected folios to TD-008 extraction.

## Planned Implementation Tasks

1. Implement `generate_html_report()` — pure Python string template; thumbnail = base64-encoded resize of analysis image; bar chart = CSS width percentage on a colored div; no external assets
2. Add `apply_human_approval()` and `cite_provenance()` to provenance module
3. Add `download-selected` CLI subcommand — reads `selection_summary.selected_folios` from provenance JSON, re-downloads at full res, writes new paths back to provenance
4. Add `provenance show` and `provenance cite` CLI subcommands
5. Wire `--report` flag into `analyze-reference` and `select-reference`
6. Integration test: full pipeline on a fixture manifest (2 canvases, synthetic images); verify report HTML is valid, provenance round-trips, download-selected writes correct files
7. Unit tests: `generate_html_report` produces non-empty HTML with candidate count; `cite_provenance` bibtex output contains shelfmark; `apply_human_approval` toggles selected flags

## Risk + Rollback

- **Self-contained HTML**: the report must be viewable offline (manuscripts are often researched without connectivity). No CDN dependencies. All styles inline; thumbnails base64-embedded.
- **Browser open**: `--open` uses `webbrowser.open()` which is safe cross-platform and silently no-ops if no browser is configured.
- **Full-res download size**: BSB Cgm 100 pages at full resolution are 20–40 MB each. The CLI warns if total download will exceed 500 MB and asks for confirmation.
- **Citation accuracy**: `cite_provenance` formats attribution and license fields from the IIIF manifest verbatim. If the manifest has poor metadata, the citation will be poor too — this is expected and noted in the output.

## Evidence

- [ ] **tdd:red-green**: 19 tests written and confirmed red before report.py / provenance extensions existed
- [ ] **tests:unit**: `tests/test_refselect_report.py` (8), `tests/test_refselect_provenance3.py` (11) — 98 total refselect tests pass
- [ ] **tests:integration**: `test_report_is_self_contained` verifies no external CDN dependencies; `test_missing_image_handled_gracefully` verifies resilience
