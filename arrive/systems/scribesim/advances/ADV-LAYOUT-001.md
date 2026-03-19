---
advance_id: ADV-LAYOUT-001
system_id: scribesim
title: "Layout — Initial Implementation"
status: planned
started_at: ~
implementation_completed_at: ~
review_time_estimate_minutes: 35
review_time_actual_minutes: ~
components: [layout]
risk_flags: [new_dependency]
evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
tech_direction: [TD-001]
pipeline_position: 2
depends_on_advances: [scribesim/ADV-GLYPHS-001, scribesim/ADV-HAND-001]
---

## Objective

Implement the page layout engine that positions text within historically accurate ruling patterns and margins, applying Knuth-Plass line breaking adapted for variable Bastarda glyph widths and handling lacuna regions (water damage, missing corners) on affected folios.

## Behavioral Change

After this advance:
- Pages are laid out on a 280x400mm page with correct margins (top 25mm, bottom 70mm, inner 25mm, outer 50mm) for standard folios, and 240x340mm for final folios (f14-f17)
- Dry-point ruling lines are generated at the correct vertical pitch, yielding 30-32 lines per page on standard folios and 26-28 lines on final folios
- Knuth-Plass line breaking operates on variable glyph advance widths from the glyph catalog, scaled by the resolved hand parameters, producing justified text blocks
- Lacuna rendering is supported: `water_damage` regions cause text to fade according to a damage mask; `missing_corner` regions constrain text placement to the surviving page area only

## Pipeline Context

- **Position**: Phase 2 (ScribeSim — Scribal Hand Simulation)
- **Upstream**: Glyph catalog (advance widths, baseline anchors) from glyphs component; resolved hand parameters (x-height, spacing, scale) from hand component; text content and lacuna annotations from per-folio JSON
- **Downstream**: Produces a positioned glyph sequence (glyph ID + page coordinates + baseline) consumed by render for rasterization and by groundtruth for PAGE XML coordinate generation
- **Contracts**: TD-001-D (Hand parameter TOML — layout must respect hand_scale modifiers for folios like f07v)

## Component Impact

```yaml
components: [layout]
system: scribesim
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/scribesim-layout-init`
- [ ] Tidy: define `PageLayout` (page_width, page_height, margins, ruling_lines), `PositionedGlyph` (glyph_id, x, y, baseline_y, folio_id), and `TextBlock` (lines of positioned glyphs)
- [ ] Test: write unit tests — standard folio produces 30-32 ruling lines within correct margins; final folio (f14r) produces 26-28 lines at reduced page size; Knuth-Plass breaking does not overflow text block width; lacuna regions exclude glyphs from damaged areas
- [ ] Implement: page geometry for standard (280x400mm) and final (240x340mm) folio formats, with margin definitions and dry-point ruling line generation
- [ ] Implement: Knuth-Plass line breaking algorithm adapted for variable-width Bastarda glyphs, consuming advance widths from the glyph catalog scaled by hand parameters
- [ ] Implement: lacuna handler — `water_damage` applies a fade mask to glyph positions within the affected region; `missing_corner` clips the text block to the surviving area polygon
- [ ] Validate: layout a representative folio (f01r standard, f07v with hand_scale modifier, f14r with reduced page size) and verify line counts and margin compliance

## Risk + Rollback

**Risks:**
- Knuth-Plass parameterisation (penalty weights, tolerance) may need tuning per folio type to avoid overly loose or tight lines, especially on final folios with fewer lines and narrower text blocks
- Lacuna region definitions from XL may use coordinate systems that require transformation to match layout page coordinates

**Rollback:**
- Revert the `feat/scribesim-layout-init` branch; layout is a pure computation with no persistent state

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
