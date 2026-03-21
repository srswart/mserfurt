---
advance:
  id: ADV-SS-FITNESS-001
  title: Fitness Function — F1-F7 Multi-Criteria Evaluation
  system: scribesim
  primary_component: evo
  components:
  - evo
  - metrics
  started_at: 2026-03-21T01:15:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T08:44:10.090303Z
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
  - tests:unit
  status: complete
---

## Objective

Implement TD-007 Part 2. Build the 7-term fitness function: F1 letter recognition (template matching + keypoint hits), F2 thick/thin contrast ratio, F3 connection flow (inter-glyph hairline detection), F4 style consistency (Bastarda proportions, slant, angles), F5 target manuscript similarity (perceptual features), F6 smoothness (curvature regularity), F7 continuity at glyph boundaries. Composite with weighted sum (F1=0.30, F3=0.15, F4=0.15, rest 0.10 each).

## Behavioral Change



## Risk + Rollback



## Evidence

