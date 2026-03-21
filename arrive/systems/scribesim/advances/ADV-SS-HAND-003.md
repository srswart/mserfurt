---
advance:
  id: ADV-SS-HAND-003
  title: Hand Profile v3 — Dynamics, Letterform, Stroke Parameters
  system: scribesim
  primary_component: hand
  components:
  - hand
  started_at: 2026-03-20T22:30:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T18:36:37.142352Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - breaking_change
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Implement TD-003-A S1. Extend HandProfile with ~12 new parameters: dynamics group (attraction_strength, damping_coefficient, lookahead_strength, max_speed, rhythm_strength, target_radius_mm, contact_threshold, word_lift_height_mm), letterform group (keypoint_flexibility_mm, ascender_height_ratio, descender_depth_ratio, x_height_mm), and stroke group (foot_width_boost, foot_ink_boost, foot_zone_start, attack_width_boost, attack_zone_end, pressure_modulation_range). Update TOML format, ranges, validation.

## Behavioral Change



## Planned Implementation Tasks

- [ ] Add dynamics parameters to HandProfile dataclass
- [ ] Add letterform parameters to HandProfile dataclass
- [ ] Add stroke parameters to HandProfile dataclass
- [ ] Update TOML serialization/deserialization for new fields
- [ ] Define valid ranges and defaults for all new parameters
- [ ] Add validation for parameter constraints and cross-parameter consistency
- [ ] Update existing presets with sensible defaults for new parameters
- [ ] Migration path: old TOML files load with defaults for missing fields

## Risk + Rollback

Breaking change to HandProfile schema. Mitigated by default values for all new fields so old TOML files remain loadable. Rollback by removing new fields and reverting dataclass.

## Evidence

- [ ] tdd:red-green — write tests for new parameter validation and TOML round-trip before implementation
- [ ] tidy:preparatory — refactor HandProfile into parameter groups before adding fields
- [ ] tests:unit — unit tests for ranges, defaults, validation, TOML serialization
