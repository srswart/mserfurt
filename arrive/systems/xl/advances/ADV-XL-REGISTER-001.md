---
advance:
  id: ADV-XL-REGISTER-001
  title: Register — Initial Implementation
  system: xl
  primary_component: register
  components:
  - register
  started_at: 2026-03-19T00:00:00Z
  started_by: null
  implementation_completed_at: 2026-03-19T06:50:56.868825Z
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

Implement the hybrid register engine that parses, validates, and resolves language register hints from the ingested manuscript sections. The engine must enforce consistency rules — no orphaned {mixed} tags without clause-level resolution, no {verbatim:*} tags without a matching reference table entry, no register switches mid-word — and resolve ambiguous {mixed} sections down to clause-level {de}/{la} tags.

## Behavioral Change

After this advance:
- All register hints ({de}, {la}, {mixed}, {verbatim:augustine}, {verbatim:psalms}, {verbatim:eckhart}, {keep}) are parsed into typed `RegisterTag` objects with source location tracking
- {mixed} tags are resolved to clause-level language assignments by analyzing transitional markers (e.g., Latin incipit followed by German gloss, or German homily embedding a Latin scriptural citation)
- Consistency validation catches errors: a section tagged {la} containing clearly German morphology, a {verbatim:augustine} tag with no matching reference entry, or adjacent sections with incompatible register transitions
- The register engine emits a `RegisterMap` that translate and folio consume to determine per-clause language and translation strategy

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/xl-register-init`
- [ ] Tidy: Define `RegisterTag` enum (DE, LA, MIXED, VERBATIM_AUGUSTINE, VERBATIM_PSALMS, VERBATIM_ECKHART, KEEP) and `RegisterMap` data class mapping section/clause IDs to resolved tags; define validation error types
- [ ] Test: Write tests for tag parsing (all seven tag types), {mixed} resolution (a German homily with embedded Latin Psalm citation resolves to clause-level DE/LA), consistency checking (flag a {la} section containing German articles like "der/die/das"), verbatim tag validation (reject {verbatim:unknown} with no reference entry)
- [ ] Implement: Build tag parser that extracts register hints from section metadata; build {mixed} resolver that splits sections at clause boundaries using punctuation, Latin/German morphological markers, and transitional phrases; build consistency validator that cross-checks resolved tags against surface-level language features; emit `RegisterMap` keyed by section and clause index
- [ ] Validate: Run register engine on full ingest output and verify the Eckhart folio (7r) resolves to predominantly {de} with embedded {la} citations, the Psalm sections resolve to {verbatim:psalms}, and no validation errors are raised on well-formed input

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- Clause boundary detection for {mixed} resolution is heuristic; 14th-century macaronic text does not follow modern punctuation conventions, so the splitter may misplace boundaries
- The consistency validator may produce false positives on code-switched passages where German and Latin genuinely intermix at the sub-clause level

**Rollback:**
- Revert the `feat/xl-register-init` branch; register has no external side effects

## Evidence

