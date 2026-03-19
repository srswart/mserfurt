---
advance:
  id: ADV-XL-INGEST-001
  title: "Ingest — Initial Implementation"
  system: xl
  primary_component: ingest
  components: [ingest]
  started_at: "2026-03-19T00:00:00Z"
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
  status: in_progress
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

## Implementation Sub-Plan

### Tidy (Preparatory Refactors)
- [ ] Create `xl/models.py` with shared data classes: `Passage`, `Section`, `ApparatusEntry`, `ManuscriptMeta`, `IngestResult`
- [ ] Create `xl/ingest/` package with `__init__.py` and `parser.py`
- [ ] Confirm `xl/ingest` is importable before writing any parsing logic

### Tests First (Red Phase)
- [ ] Write `tests/test_ingest.py` using the real source file as fixture
- [ ] Test: frontmatter YAML is parsed — shelfmark, author, date, gathering count
- [ ] Test: folio_map is extracted — all 11 folio range entries present
- [ ] Test: all section titles are captured (Opening Declaration, Press Meditation, Peter Narrative, Workshop Visits, Eckhart Confession, Psalter Return, Final Gathering)
- [ ] Test: folio references correctly extracted per section (f01r, f04r-f05v, f06r, f07r-f07v, f07v, f14r-f17v)
- [ ] Test: register hints parsed — de, la, mixed, mhg all appear in output
- [ ] Test: damage apparatus captured — f04r-f05v sections have damage entries
- [ ] Test: hand notes captured — f06r section has lateral-pressure hand note
- [ ] Test: lacunae captured — f04r-f05v passages have lacuna entries
- [ ] Test: verbatim markers captured — Augustine and MHG passages flagged as verbatim
- [ ] Confirm tests fail (red) before implementing

### Implement (Green Phase)
- [ ] Parse YAML frontmatter using `yaml.safe_load` → `ManuscriptMeta`
- [ ] Split document body on section comment blocks (`<!-- SECTION N: ... -->`)
- [ ] For each section: extract folio ref, hand notes, damage notes from header block
- [ ] Within each section: split on `<!-- register: X -->` markers → list of `Passage`
- [ ] For each passage: capture text (strip HTML comments), register, verbatim flag + source, lacunae list
- [ ] Collect all apparatus entries (damage, lacuna, hand_note, gap_note, damage_note) into `ApparatusEntry` objects
- [ ] Return `IngestResult(metadata, sections)`

### Validate
- [ ] Run ingest against real source file, confirm 7 sections returned
- [ ] Confirm all 17 folio positions represented across folio_map
- [ ] Confirm f07r section is correctly isolated (Eckhart confession)
- [ ] Confirm f04r-f05v damage apparatus entries present
- [ ] Run `arrive plan check`
- [ ] Update evidence table

## Changes Made

_No changes yet._

## Check for Understanding

_To be generated after implementation._
