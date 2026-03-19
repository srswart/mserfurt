---
advance:
  id: ADV-XL-EXPORT-001
  title: "Export — Initial Implementation"
  system: xl
  primary_component: export
  components: [export]
  started_at: ~
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags: [new_dependency]
  evidence:
    - tdd:red-green
    - tidy:preparatory
    - tests:unit
  status: planned
---

## Objective

Serialize annotated folios into three output formats: per-folio JSON files (one per page, e.g., `folio-001r.json`), a consolidated `manifest.json` listing all folios with metadata, and PAGE XML files (2019 schema, text-only regions with normalized grid coordinates). These outputs constitute the hand-off artifacts consumed by ScribeSim and Weather in subsequent pipeline phases.

## Behavioral Change

After this advance:
- 17 per-folio JSON files are written to the output directory, each conforming to TD-001-A schema with fields for lines, language, damage annotations, confidence scores, and hand notes
- A `manifest.json` file is written conforming to TD-001-B, listing all folios in order with summary metadata (folio_id, line_count, primary_language, damage_present, confidence_mean)
- 17 PAGE XML files are written conforming to TD-001-C (PAGE 2019 schema), each containing text-only TextRegion and TextLine elements with normalized grid coordinates (0.0-1.0 range) for downstream rendering
- A JSONL consolidation file is optionally written for bulk processing, containing one JSON object per line per folio

## Pipeline Context

- **Position**: Phase 1 (XL — Reverse Translation & Folio Structuring)
- **Upstream**: Consumes annotated `Folio` objects from folio + annotate
- **Downstream**: Emits files consumed by ScribeSim (reads folio JSON for glyph rendering) and Weather (reads PAGE XML for degradation simulation)
- **Contracts**: TD-001-A (Folio JSON), TD-001-B (Manifest JSON), TD-001-C (PAGE XML) — this component is the sole writer of all three contract artifacts

## Component Impact

```yaml
components: [export]
system: xl
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/xl-export-init`
- [ ] Tidy: Define JSON schema validators for TD-001-A and TD-001-B using jsonschema; obtain PAGE 2019 XSD for TD-001-C validation; define normalized grid coordinate system (28-35 lines mapped to 0.0-1.0 vertical range, single text column mapped to horizontal range)
- [ ] Test: Write tests for each output format — verify a clean folio (1r) produces valid TD-001-A JSON with correct line count and high confidence; verify manifest.json lists all 17 folios in order; verify PAGE XML validates against 2019 XSD and contains correct TextLine count; verify damaged folio (4v) JSON includes damage annotations; verify JSONL contains exactly 17 lines
- [ ] Implement: Build JSON serializer that maps `FolioPage` + `Annotation` objects to TD-001-A schema; build manifest generator that aggregates per-folio metadata; build PAGE XML writer using lxml with TextRegion per page and TextLine per line, computing normalized y-coordinates from line index and x-coordinates for a single-column layout; build optional JSONL writer; add `--format` flag support (json, xml, jsonl, all)
- [ ] Validate: Run export on full annotated folio set, validate all JSON files against TD-001-A schema, validate manifest against TD-001-B, validate all PAGE XML against 2019 XSD, and verify ScribeSim can parse the output (if ScribeSim stub is available)

## Risk + Rollback

**Risks:**
- PAGE XML coordinate normalization must be consistent with ScribeSim's rendering expectations; mismatched coordinate systems would produce misaligned glyphs
- The PAGE 2019 XSD is strict about element ordering and namespace declarations; lxml output must match exactly or downstream XML parsers will reject it

**Rollback:**
- Revert the `feat/xl-export-init` branch; delete any written output files from the output directory

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
