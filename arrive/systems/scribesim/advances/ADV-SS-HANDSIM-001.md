---
advance:
  id: ADV-SS-HANDSIM-001
  title: Hand State Machine — Continuous Dynamics Simulation
  system: scribesim
  primary_component: handsim
  components:
  - handsim
  - render
  started_at: 2026-03-20T23:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T18:54:59.395841Z
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

Implement TD-005 Part 1. Build the hand as a continuous state machine with position, velocity, nib state, ink state, motor program state, and rhythmic state. Implement hand_step() with attraction force, lookahead smoothing, velocity damping, tremor, rhythm force, and biomechanical speed limits. Mark emission when nib is in contact. Validate: render a line of minims (nnnnnn) using the hand simulator.

## Behavioral Change



## Planned Implementation Tasks

- [ ] Define HandState dataclass (position, velocity, nib_state, ink_state, motor_program_state, rhythmic_state)
- [ ] Implement hand_step() core loop with configurable dt
- [ ] Implement attraction force toward next target keypoint
- [ ] Implement lookahead smoothing across upcoming keypoints
- [ ] Implement velocity damping and biomechanical speed limits
- [ ] Implement tremor model (low-frequency physiological noise)
- [ ] Implement rhythm force (periodic acceleration/deceleration)
- [ ] Implement nib contact state and mark emission logic
- [ ] Wire hand simulator output into existing rendering pipeline
- [ ] Validation: render a line of minims (nnnnnn) and verify visual quality

## Risk + Rollback

New dependency and public API. This is the core architectural change from glyph placement to dynamics simulation. Old renderer remains as fallback. Rollback by disabling hand simulator pathway.

## Evidence

- [ ] tdd:red-green — write tests for hand_step physics (force, damping, limits) before implementation
- [ ] tidy:preparatory — define clean interfaces between hand simulator and rendering pipeline
- [ ] tests:unit — unit tests for each force component, state transitions, contact logic
- [ ] tests:integration — integration test rendering minims through full pipeline
