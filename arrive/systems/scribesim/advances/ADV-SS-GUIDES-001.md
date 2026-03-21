---
advance:
  id: ADV-SS-GUIDES-001
  title: Letterform Guides — Keypoint-Based Letter Definitions
  system: scribesim
  primary_component: guides
  components:
  - guides
  - handsim
  started_at: 2026-03-20T23:10:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T19:00:17.766312Z
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

Implement TD-005 Part 3. Replace the glyph catalog (complete Bezier trajectories) with letterform guides (minimal keypoint sets). Start with 5 core letters: n, u, d, e, r. Each guide defines structural keypoints (position, type, contact, direction, flexibility) that the hand simulator steers through. Add context-dependent variants. The old glyph catalog remains as fallback.

## Behavioral Change



## Planned Implementation Tasks

- [ ] Define Keypoint dataclass (position, type, contact, direction, flexibility)
- [ ] Define LetterformGuide structure (letter, keypoints, entry_angle, exit_angle, variants)
- [ ] Implement guide for 'n' (minim + arch)
- [ ] Implement guide for 'u' (inverted arch)
- [ ] Implement guide for 'd' (ascender + bowl)
- [ ] Implement guide for 'e' (bowl + crossbar)
- [ ] Implement guide for 'r' (minim + shoulder)
- [ ] Implement context-dependent variant selection (preceding/following letter)
- [ ] Keep old glyph catalog as fallback for letters without guides
- [ ] Test: each guide produces valid keypoint sequences consumable by hand simulator

## Risk + Rollback

Public API for letterform definitions consumed by hand simulator. Old glyph catalog remains for all letters not yet converted. Rollback by disabling guide pathway.

## Evidence

- [ ] tdd:red-green — write tests for keypoint structure and guide validity before implementation
- [ ] tidy:preparatory — define guide format and loader interface before writing individual guides
- [ ] tests:unit — unit tests for each letter guide, variant selection, keypoint validation
