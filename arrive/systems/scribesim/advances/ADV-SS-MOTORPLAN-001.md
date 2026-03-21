---
advance:
  id: ADV-SS-MOTORPLAN-001
  title: Sliding Window Motor Planning — Anticipatory Path Splines
  system: scribesim
  primary_component: handsim
  components:
  - handsim
  - guides
  - hand
  started_at: 2026-03-21T00:15:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T21:19:11.859382Z
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
  - tests:integration
  status: complete
---

## Objective

Implement TD-006 Steps 4-5. Add sliding window motor planning: the hand holds a window of 6-8 upcoming keypoints and computes a smooth Hermite spline path through them. The PD controller follows this planned path instead of aiming at individual keypoints. Add context-dependent keypoint adjustment: letters adapt based on preceding/following letters (entry/exit angles, word-initial/final size). Add diagnostic rendering (--show-keypoints, --show-plan-path).

## Behavioral Change



## Planned Implementation Tasks

- [ ] Add motor_planning parameters to HandProfile: window_size (6), replan_interval (8), speed_reduction_at_turns (0.6), air_speed_multiplier (1.5)
- [ ] Implement SlidingWindow: holds keypoints, plan, cursor, replan counter
- [ ] Implement plan_path(): fit Hermite spline through window keypoints with velocity estimates
- [ ] Implement speed_profile(): slow at turns, fast on straights, decelerate at keypoints
- [ ] Implement hand_step_with_plan(): PD controller follows plan cursor instead of raw keypoint
- [ ] Implement advance_window(): when keypoint passed, pop front, push next, replan
- [ ] Implement context-dependent keypoint adjustment: preceding letter affects entry, following affects exit
- [ ] Add --show-keypoints and --show-plan-path diagnostic rendering flags
- [ ] Test: the end of 'n' in "und" tilts toward 'd' ascender (anticipation measurable)
- [ ] Test: word-initial letters are slightly larger than mid-word instances
- [ ] Render "und der strom" — letters anticipate what's coming, word-level coherence
- [ ] Snapshot: anticipatory motor planning output

## Risk + Rollback

Complex addition. The sliding window replaces point-to-point steering. Old PD controller mode kept as fallback. Rollback by disabling the planner.

## Evidence

