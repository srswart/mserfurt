---
advance:
  id: ADV-SS-SPACING-001
  title: Line Spacing Fix — Ruling Pitch From line_height_norm
  system: scribesim
  primary_component: layout
  components:
  - layout
  started_at: 2026-03-20T19:50:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T15:57:32.800850Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence:
  - tdd:red-green
  - tests:unit
  status: complete
---

## Objective

Fix the line spacing bug: ruling pitch is currently `x_height_px * 0.250mm` (~9.5mm) which only accounts for the x-height, not ascenders or descenders. Bastarda glyphs extend to 1.8× x-height (ascenders) and -0.5× x-height (descenders), causing overlap between adjacent lines. The `line_height_norm` parameter (currently 4.2 x-heights, ~40mm) exists but is ignored by `make_geometry()`.

## Behavioral Change

After this advance:
- `make_geometry()` uses `line_height_norm * x_height_mm` for ruling pitch instead of raw `x_height_px * _PX_TO_MM`
- Lines are well-separated: ascenders of one line never overlap descenders of the line above
- The number of lines that fit on a page is reduced (fewer lines per page, more spacing between them)
- `line_spacing_mean_mm` from `HandProfile.line` is used when the v2 profile is available
- Visual output matches the Werbeschreiben reference: clean, generous line spacing

## Planned Implementation Tasks

- [ ] Tidy: understand the relationship between ruling_pitch_mm, x_height, and line_height_norm
- [ ] Test: ruling pitch with line_height_norm=4.2 produces ~40mm spacing (no overlap for 1.8× ascenders)
- [ ] Test: adjacent lines' ascenders and descenders do not vertically overlap in rendered output
- [ ] Implement: update `make_geometry()` to use `line_height_norm * x_height_mm` for pitch
- [ ] Implement: when HandProfile is available, use `line.line_spacing_mean_mm` directly
- [ ] Validate: render f01r — lines clearly separated, no overlap
- [ ] Checkpoint: `./snapshot.sh spacing-001` — VISUAL DIFF vs render-002: lines should be well-separated

## Risk + Rollback

**Risks:**
- Wider spacing means fewer lines per page — some folios may not fit all their text in the available space
- Existing test fixtures may assume the old line count

**Rollback:**
- Revert the branch; layout geometry is isolated

## Evidence

