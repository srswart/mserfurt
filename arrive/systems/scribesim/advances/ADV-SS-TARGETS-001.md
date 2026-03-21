---
advance:
  id: ADV-SS-TARGETS-001
  title: Target Generation Module — Hand Simulator Interface
  system: scribesim
  primary_component: layout
  components:
  - layout
  - movement
  - handsim
  started_at: 2026-03-20T22:50:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T18:46:57.074528Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - public_api
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Implement TD-002-C action items. Extract baseline undulation and ruling imprecision from current line-positioning code into a target_generation module. Extract word-level parameter adjustments into a plan_word() interface. These become the input to the TD-005 hand simulator — targets the hand steers through rather than positions glyphs are placed at. Keep the old glyph-based renderer as fallback.

## Behavioral Change



## Planned Implementation Tasks

- [ ] Extract baseline undulation logic from placer into target_generation module
- [ ] Extract ruling imprecision logic into target_generation module
- [ ] Implement plan_word() interface returning target sequence for hand simulator
- [ ] Define target point data structure (position, type, constraints)
- [ ] Wire target_generation as optional input to rendering pipeline
- [ ] Keep glyph-based placer as fallback when hand simulator is not active
- [ ] Test: plan_word() produces valid target sequences for known words

## Risk + Rollback

Public API change — new module consumed by hand simulator. Old glyph-based renderer remains as fallback. Rollback by disabling target_generation pathway.

## Evidence

- [ ] tdd:red-green — write tests for target sequence structure and plan_word() before implementation
- [ ] tidy:preparatory — extract existing undulation/imprecision logic before building new module
- [ ] tests:unit — unit tests for target generation, plan_word interface
