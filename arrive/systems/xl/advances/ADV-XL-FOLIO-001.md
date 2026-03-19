---
advance:
  id: ADV-XL-FOLIO-001
  title: "Folio — Initial Implementation"
  system: xl
  primary_component: folio
  components: [folio]
  started_at: ~
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
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

Distribute the translated manuscript text across 17 folios with recto/verso structure, targeting 28-35 lines per page. The distribution must respect CLIO-7 folio references — folios 4r-5v are damaged (reduced line counts, lacunae), 6r resumes clean text, 7r contains the Eckhart *Reden der Unterweisung* passage, and 14r begins the final section — while preserving sentence and clause integrity at page boundaries.

## Behavioral Change

After this advance:
- Translated text is distributed across 17 folios (1r/1v through 9r, accounting for recto/verso), each page containing 28-35 lines of text
- Folio 4r-5v pages carry reduced line counts and lacuna placeholders reflecting the documented physical damage
- Folio 7r is structurally isolated to contain the Eckhart passage without splitting it across a page boundary
- Folio 14r marks the beginning of the final section (*finis* material) and its content is not mixed with earlier homiletic text
- Each `FolioPage` object carries its lines, language metadata from the register map, and references to apparatus entries that apply to that page

## Pipeline Context

- **Position**: Phase 1 (XL — Reverse Translation & Folio Structuring)
- **Upstream**: Consumes `TranslatedSection` objects from translate and `RegisterMap` from register
- **Downstream**: Produces `Folio` objects (each with recto/verso `FolioPage`s) consumed by annotate (for damage/confidence overlay) and export (for JSON/XML serialization)
- **Contracts**: TD-001-A (Folio JSON) — the folio component defines the structural skeleton that the JSON schema describes

## Component Impact

```yaml
components: [folio]
system: xl
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/xl-folio-init`
- [ ] Tidy: Define `FolioPage` (folio_id, side, lines, line_count, language_per_line, apparatus_refs) and `Folio` (number, recto, verso) data classes; define line-breaking strategy interface
- [ ] Test: Write tests for line distribution — a clean page gets 28-35 lines, a damaged page (4r-5v range) gets fewer lines with lacuna markers, the Eckhart passage (7r) stays on a single page, sentence boundaries are not broken mid-sentence, the final section starts at 14r
- [ ] Implement: Build line-breaking algorithm that fills pages to target line count while respecting sentence boundaries; implement folio reference constraints (hard-pin sections to their CLIO-7 folio references); implement damage-aware line reduction for 4r-5v; implement register metadata passthrough from `RegisterMap` to per-line language tags; generate sequential folio IDs (001r, 001v, 002r, ... 009r)
- [ ] Validate: Run folio structuring on full translated output and verify 17 pages are emitted, line counts fall within 28-35 for clean pages, 4r-5v have reduced counts, 7r contains the Eckhart text, and 14r begins the final section

## Risk + Rollback

**Risks:**
- Text volume may not divide evenly into 17 folios at 28-35 lines/page; the algorithm may need to flex line counts or accept slightly over/under-filled pages
- Hard-pinning sections to specific folios (7r for Eckhart, 14r for finis) may conflict with natural text flow if the translated text is longer or shorter than expected

**Rollback:**
- Revert the `feat/xl-folio-init` branch; folio structuring is pure computation with no external effects

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
