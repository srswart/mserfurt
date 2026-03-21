---
advance:
  id: ADV-SS-CLAMP-001
  title: Clamped Dynamics — Precise, Legible Hand Output
  system: scribesim
  primary_component: handsim
  components:
  - handsim
  started_at: 2026-03-20T23:30:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T19:36:36.762572Z
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

Implement TD-006 Phase 1. Fix chaotic hand simulator output by clamping dynamics to critically damped values (attraction=25, damping=12), adding a velocity gate at keypoint transitions (must decelerate to 30% max speed before advancing), and adding bounding box constraints per letter (clamp hand position within letter bounds + 0.5mm tolerance). The output should be precise and legible — letters recognizable, no tangling, no overshoot, clean lifts.

## Behavioral Change



## Planned Implementation Tasks

- [ ] Update dynamics defaults: attraction=25, damping=12, lookahead=0.5, max_speed=40, rhythm=0.1, target_radius=0.15, contact_threshold=0.08, word_lift=5.0
- [ ] Add velocity gate to should_advance_target(): distance < radius AND speed < max_speed * 0.3
- [ ] Add bounding box constraint per letter: clamp hand position within guide bounds + 0.5mm
- [ ] Add nib height tracking: contact only when nib_height < contact_threshold (prevents ink during lifts)
- [ ] Render "und der" and verify: letters recognizable, no tangling, clean word separation
- [ ] Snapshot: legible hand simulator output

## Risk + Rollback

Low risk — parameter changes + guard functions. Existing dynamics code unchanged structurally. Rollback by restoring old defaults.

## Evidence

