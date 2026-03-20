---
advance:
  id: ADV-SS-GROUNDTRUTH-001
  title: Groundtruth — Initial Implementation
  system: scribesim
  primary_component: groundtruth
  components:
  - groundtruth
  started_at: 2026-03-19T17:34:54Z
  started_by: null
  implementation_completed_at: 2026-03-19T17:38:50.628509Z
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

Generate PAGE XML ground truth files (2019 schema) with full glyph-level coordinate polygons and text equivalents, producing Kraken-compatible baseline polylines and achieving a target glyph IoU of at least 0.95 against rendered pixel positions.

## Behavioral Change

After this advance:
- Each rendered folio produces a corresponding PAGE XML file with the full hierarchy: Page > TextRegion > TextLine > Word > Glyph
- Glyph-level `Coords` elements contain pixel-coordinate polygons that tightly bound each rendered glyph, derived from the positioned glyph data and actual rasterized extents
- `TextEquiv` elements at the Glyph level provide the Unicode character, with a custom `@register` attribute distinguishing German and Latin text
- `Baseline` elements on each `TextLine` are Kraken-compatible polylines, targeting at least 90% line detection rate when evaluated by Kraken's line finder
- Ground truth coordinates match the 300 DPI page image pixel space exactly

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/scribesim-groundtruth-init`
- [ ] Tidy: set up PAGE XML 2019 schema validation; define data structures for the Page > TextRegion > TextLine > Word > Glyph hierarchy
- [ ] Test: write unit tests — output validates against PAGE XML 2019 XSD; all glyphs have non-empty Coords polygons; TextEquiv values match input text; Baseline polylines are present on every TextLine; @register attribute is set correctly for German vs Latin text
- [ ] Implement: construct PAGE XML document from positioned glyph data — group glyphs into Words (by whitespace), Words into TextLines (by layout lines), TextLines into TextRegions (by text block)
- [ ] Implement: generate Coords polygons from glyph bounding boxes, with convex hull tightening to achieve glyph IoU >= 0.95 against rendered pixels
- [ ] Implement: generate Baseline polylines from layout ruling lines, interpolated through actual glyph baseline positions for Kraken compatibility
- [ ] Implement: attach TextEquiv with Unicode content and custom @register attribute (German/Latin) at the Glyph level
- [ ] Validate: validate output against PAGE XML 2019 XSD; compute glyph IoU against rendered page image; run Kraken line detection on output and measure detection rate

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- PAGE XML 2019 schema compliance is strict; custom attributes like @register must be handled via schema extension or namespace to avoid validation failures
- Glyph IoU target (>= 0.95) depends on tight coordination between render pixel output and groundtruth polygon generation; any drift in coordinate systems will degrade IoU

**Rollback:**
- Revert the `feat/scribesim-groundtruth-init` branch; PAGE XML files are generated output with no side effects on other components

## Evidence

