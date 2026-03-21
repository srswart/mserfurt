---
advance:
  id: ADV-SS-PDCONTROL-001
  title: PD Controller — Proportional-Derivative Motor Control
  system: scribesim
  primary_component: handsim
  components:
  - handsim
  - hand
  started_at: 2026-03-21T00:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T21:08:42.194106Z
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

Implement TD-006 Step 3. Replace the current attractor+damping force model with a PD (Proportional-Derivative) controller that corrects both position error and velocity error. This models how the human motor system works: the brain corrects where the hand IS (proportional) and how fast it's MOVING (derivative). Add position_gain and velocity_gain parameters to HandProfile.

## Behavioral Change



## Planned Implementation Tasks

- [ ] Add motor_planning parameters to HandProfile: position_gain (default 20.0), velocity_gain (default 8.0), max_acceleration_mm_s2 (default 500.0)
- [ ] Implement PD controller in hand_step(): correction = position_error * position_gain + velocity_error * velocity_gain
- [ ] Replace attraction_force + damping_force with PD correction (single unified force model)
- [ ] Add acceleration clamping (biomechanical limit)
- [ ] Test: damping ratio = velocity_gain / (2 * sqrt(position_gain)) ≈ 0.89 (slightly underdamped)
- [ ] Test: hand arrives at keypoints without oscillation
- [ ] Render "und der" — similar to Phase 1 but slightly smoother curves
- [ ] Snapshot: PD controller output

## Risk + Rollback

Public API change — replaces force model. Old attractor mode kept as fallback flag. Rollback by reverting hand_step().

## Evidence

