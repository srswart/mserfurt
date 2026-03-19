---
advance_id: ADV-INGEST-001
system_id: xl
title: "Ingest — Initial Implementation"
status: planned
started_at: ~
implementation_completed_at: ~
review_time_estimate_minutes: 30
review_time_actual_minutes: ~
components: [ingest]
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

Parse `source/ms-erfurt-source-annotated.md` into structured segments, separating Konrad von Erfurt's main text from the CLIO-7 editorial apparatus. Extract structural markers (folio references like 4r-5v, 6r, 7r, 14r), damage descriptions, hand notes, and register hints ({de}, {la}, {mixed}, {verbatim:*}, {keep}) so downstream components receive clean, typed data.

## Behavioral Change

After this advance:
- The ingest module parses the annotated manuscript and emits a list of `Section` objects, each carrying its text content, folio reference range, apparatus entries, and register hints
- CLIO-7 apparatus lines (damage notes, lacuna markers, hand descriptions, confidence annotations) are extracted into structured `ApparatusEntry` objects rather than left inline
- Folio boundary markers (4r through 14r) are recognized and attached to their respective sections, preserving the 17-folio structure implied by the source
- Register hint tags ({de}, {la}, {mixed}, {verbatim:augustine}, {verbatim:psalms}, {verbatim:eckhart}, {keep}) are parsed and validated at the section level

## Pipeline Context

- **Position**: Phase 1 (XL — Reverse Translation & Folio Structuring)
- **Upstream**: Raw annotated manuscript file (`source/ms-erfurt-source-annotated.md`)
- **Downstream**: Produces `IngestResult` consumed by translate (for text content), register (for register hints), and annotate (for apparatus entries)
- **Contracts**: No direct contract output, but shapes data for TD-001-A folio fields

## Component Impact

```yaml
components: [ingest]
system: xl
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/xl-ingest-init`
- [ ] Tidy: Define data classes — `Section` (text, folio_ref, apparatus, register_hints), `ApparatusEntry` (type, description, folio_ref, confidence), `IngestResult` (sections list, metadata); establish the internal data model that all downstream XL components share
- [ ] Test: Write parser tests for each structural element — folio references (verify `4r`, `5v`, `6r`, `7r`, `14r` are all captured), apparatus extraction (damage, lacuna, hand notes), register hint parsing ({de}, {la}, {mixed}, {verbatim:augustine}), edge case where apparatus and text interleave within a folio
- [ ] Implement: Build Markdown parser that walks the source document line-by-line; detect section boundaries via heading markers and folio references; extract inline apparatus using CLIO-7 notation patterns; collect register hints from curly-brace tags; emit `IngestResult` with ordered sections
- [ ] Validate: Run ingest against the real source file and verify all 17 folios are represented, the Eckhart section (7r) is correctly isolated, and the damage range (4r-5v) is captured as apparatus entries

## Risk + Rollback

**Risks:**
- The CLIO-7 apparatus notation in the source file may have inconsistent formatting; the parser must handle both strict and loose variants
- Folio references may appear as ranges (4r-5v) or single references (6r); the parser must normalize both forms

**Rollback:**
- Revert the `feat/xl-ingest-init` branch; ingest has no external side effects

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
