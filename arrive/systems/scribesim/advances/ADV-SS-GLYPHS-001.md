---
advance:
  id: ADV-SS-GLYPHS-001
  title: Glyphs — Initial Implementation
  system: scribesim
  primary_component: glyphs
  components:
  - glyphs
  started_at: 2026-03-19T17:03:04Z
  started_by: null
  implementation_completed_at: 2026-03-19T17:09:01.089082Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  - public_api
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Define the complete German Bastarda glyph catalog (~90 glyphs) as sequences of named Bezier strokes with pressure profiles, covering all letterforms required to render Brother Konrad's scribal hand in the MS Erfurt 1457 manuscript.

## Behavioral Change

After this advance:
- A glyph catalog of ~90 entries is available, each defined as an ordered sequence of named Bezier strokes (cubic curves) with per-stroke pressure profiles
- German-specific forms are fully represented: lowercase a-z, long s (U+017F), round s, esszett/sz ligature, umlauted vowels (a/o/u with superscript-e diacritic in Bastarda convention), and w
- Uppercase Bastarda capitals, Latin-specific forms (no umlauts, ae/oe digraphs), and special marks (section divider, paragraph mark) are included
- Each glyph exposes its advance width, baseline anchors, and stroke-level metadata for downstream layout and ground truth generation

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

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- The glyph catalog is a public API consumed by layout, render, and groundtruth — changes to stroke structure or advance widths will cascade through the entire rendering pipeline
- Bastarda letterform accuracy depends on paleographic reference; incorrect ductus will produce visually implausible output that undermines the simulation

**Rollback:**
- Revert the `feat/scribesim-glyphs-init` branch; the glyph catalog is a static data structure with no side effects

## Evidence

