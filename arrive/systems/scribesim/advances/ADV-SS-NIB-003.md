---
advance:
  id: ADV-SS-NIB-003
  title: Nib Physics Fixes — Thick/Thin Contrast, Stroke Foot, Attack
  system: scribesim
  primary_component: render
  components:
  - render
  started_at: 2026-03-20T22:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T18:03:17.720050Z
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

Implement TD-004 Part 1 fixes A-E. Fix the mark_width formula to produce real thick/thin contrast (target 3-5x ratio). Add stroke-foot thickening at direction changes (diamond feet on downstrokes). Add stroke-start attack thickening. Separate pressure from direction (pressure +/-20% modulation, direction is primary driver). Verify rendering scale produces correct pixel widths.

## Behavioral Change



## Planned Implementation Tasks

- [ ] Fix A: min_hairline_ratio parameter (8% of nib width, ~2px at 300 DPI)
- [ ] Fix B: pressure modulation +/-20% range (not 0-100% multiplier)
- [ ] Fix C: stroke_foot_effect — width +20% and ink +25% in last 15% of downstrokes
- [ ] Fix D: stroke_attack_effect — width +10% in first 10% of strokes
- [ ] Fix E: verify pixel-level rendering scale (21px full width, 2px hairline at 300 DPI)
- [ ] Add stroke parameters to HandProfile (foot_width_boost, foot_ink_boost, foot_zone_start, attack_width_boost, attack_zone_end, pressure_modulation_range)
- [ ] Snapshot: thick/thin ratio should be >=3:1 in rendered output

## Risk + Rollback

Low risk. Changes are additive parameters with defaults that preserve current behavior. Rollback by reverting parameter additions.

## Evidence

- [ ] tdd:red-green — write tests for thick/thin ratio, foot effect, attack effect before implementation
- [ ] tests:unit — unit tests for mark_width formula, stroke effects, pressure modulation
