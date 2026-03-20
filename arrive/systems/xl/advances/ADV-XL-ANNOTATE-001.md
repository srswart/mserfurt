---
advance:
  id: ADV-XL-ANNOTATE-001
  title: Annotate — Initial Implementation
  system: xl
  primary_component: annotate
  components:
  - annotate
  started_at: 2026-03-19T09:00:00Z
  started_by: null
  implementation_completed_at: 2026-03-19T14:18:30.589618Z
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

Overlay CLIO-7 apparatus data onto the structured folios, mapping damage types (water damage, ink fading, physical tears, binding obscuration), lacuna markers, confidence scores, and hand-note characteristics to per-line and per-region metadata. The annotate layer transforms raw apparatus entries from ingest into positioned annotations anchored to specific folio pages and line ranges.

## Behavioral Change

After this advance:
- Each `FolioPage` carries a list of `Annotation` objects positioned at specific line ranges, with typed damage categories (water_damage, ink_fade, tear, binding_loss, lacuna)
- Folios 4r-5v are densely annotated with overlapping damage types reflecting the documented physical deterioration of those leaves
- Confidence scores (0.0-1.0) are assigned per line based on apparatus notes: clean text gets 0.95+, partially damaged text gets 0.5-0.8, lacunae get 0.0
- Hand-note annotations capture scribe characteristics (main hand vs. marginal corrections, ink color references, letter-form notes) as metadata on the relevant lines
- Folio 6r annotations reflect the resumption of clean text after the damaged section

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/xl-annotate-init`
- [ ] Tidy: Define `Annotation` data class (type, severity, line_start, line_end, confidence, description, hand_note) and `DamageType` enum (WATER_DAMAGE, INK_FADE, TEAR, BINDING_LOSS, LACUNA); define confidence scoring rules
- [ ] Test: Write tests for damage mapping — a clean folio (e.g., 1r) gets no damage annotations and high confidence; a damaged folio (4r) gets water_damage + ink_fade annotations with reduced confidence; a lacuna line gets confidence 0.0 and a LACUNA annotation; hand-note extraction produces correct scribe metadata; overlapping damage types on 5v are all captured
- [ ] Implement: Build apparatus-to-annotation mapper that matches `ApparatusEntry` folio references to `FolioPage` objects; implement confidence scorer that combines damage type and severity into a 0.0-1.0 score; implement hand-note extractor that parses scribe descriptions into structured fields; implement annotation merger that handles overlapping damage regions on the same line
- [ ] Validate: Run annotate on the full folio set and verify 4r-5v carry damage annotations, 6r+ are clean, confidence scores are monotonically higher on undamaged pages, and no apparatus entries are orphaned (all mapped to a folio)

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- Apparatus entries may reference folio positions ambiguously (e.g., "between 4v and 5r"); the mapper must handle boundary cases without dropping annotations
- Confidence scoring is a heuristic; downstream consumers (ScribeSim) may need different score ranges, requiring recalibration

**Rollback:**
- Revert the `feat/xl-annotate-init` branch; annotations are additive metadata with no destructive side effects

## Evidence

