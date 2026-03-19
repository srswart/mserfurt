---
advance_id: ADV-GLYPHS-001
system_id: scribesim
title: "Glyphs — Initial Implementation"
status: planned
started_at: ~
implementation_completed_at: ~
review_time_estimate_minutes: 40
review_time_actual_minutes: ~
components: [glyphs]
risk_flags: [new_dependency, public_api]
evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
tech_direction: [TD-001]
pipeline_position: 2
depends_on_advances: [xl/ADV-EXPORT-001]
---

## Objective

Define the complete German Bastarda glyph catalog (~90 glyphs) as sequences of named Bezier strokes with pressure profiles, covering all letterforms required to render Brother Konrad's scribal hand in the MS Erfurt 1457 manuscript.

## Behavioral Change

After this advance:
- A glyph catalog of ~90 entries is available, each defined as an ordered sequence of named Bezier strokes (cubic curves) with per-stroke pressure profiles
- German-specific forms are fully represented: lowercase a-z, long s (U+017F), round s, esszett/sz ligature, umlauted vowels (a/o/u with superscript-e diacritic in Bastarda convention), and w
- Uppercase Bastarda capitals, Latin-specific forms (no umlauts, ae/oe digraphs), and special marks (section divider, paragraph mark) are included
- Each glyph exposes its advance width, baseline anchors, and stroke-level metadata for downstream layout and ground truth generation

## Pipeline Context

- **Position**: Phase 2 (ScribeSim — Scribal Hand Simulation)
- **Upstream**: Character sequences from per-folio JSON (XL Phase 1); hand parameters from the hand component determine scaling and pressure application
- **Downstream**: Layout engine consumes glyph advance widths for Knuth-Plass line breaking; render engine rasterizes Bezier strokes; groundtruth uses glyph bounding polygons for PAGE XML
- **Contracts**: TD-001-D (Hand parameter TOML — glyph dimensions must be compatible with hand scale factors)

## Component Impact

```yaml
components: [glyphs]
system: scribesim
```

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/scribesim-glyphs-init`
- [ ] Tidy: define `Glyph` dataclass (id, unicode_codepoint, strokes: list of `BezierStroke`, advance_width, baseline_offset); define `BezierStroke` (control_points, pressure_profile, stroke_name)
- [ ] Test: write unit tests — catalog contains expected count (~90); long s glyph differs from round s in stroke geometry; umlauted vowels contain base glyph strokes plus superscript-e strokes; esszett is composed of long-s + z stroke sequences; all glyphs have non-zero advance width
- [ ] Implement: define lowercase Bastarda letterforms (a-z) as Bezier stroke sequences with historically informed ductus (stroke order and direction)
- [ ] Implement: add German-specific forms — long s, round s, esszett ligature, umlauted vowels with superscript-e diacritic
- [ ] Implement: add uppercase Bastarda capitals with characteristic decorative strokes
- [ ] Implement: add Latin-specific forms (ae/oe digraphs without umlaut) and special marks (section divider, paragraph mark)
- [ ] Implement: glyph lookup function that resolves a Unicode character + register (German/Latin) to the correct glyph variant
- [ ] Validate: verify every glyph renders without degenerate strokes (no zero-length segments, no self-intersecting control polygons)

## Risk + Rollback

**Risks:**
- The glyph catalog is a public API consumed by layout, render, and groundtruth — changes to stroke structure or advance widths will cascade through the entire rendering pipeline
- Bastarda letterform accuracy depends on paleographic reference; incorrect ductus will produce visually implausible output that undermines the simulation

**Rollback:**
- Revert the `feat/scribesim-glyphs-init` branch; the glyph catalog is a static data structure with no side effects

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
