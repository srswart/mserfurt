---
advance:
  id: ADV-SS-HANDFLOW-001
  title: Corridor-Following Controller Core — Planned State Tracking
  system: scribesim
  primary_component: handflow
  components:
  - handflow
  - pathguide
  - render
  started_at: 2026-03-24T13:31:03Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T13:31:03Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  - public_api
  evidence:
  - tidy:preparatory
  - tdd:red-green
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Build the new TD-014 controller that tracks planned desired state from a dense guide corridor. This is the replacement for the partially wired sparse-keypoint controller.

## Behavioral Change

After this advance:
- controller force is computed from desired plan state, not only from raw target positions
- out-of-corridor error produces strong corrective behavior
- contact, lift, speed, and pressure are planned state rather than incidental byproducts

## Planned Implementation Tasks

- [x] Define `HandStateV2` with persistent position, velocity, acceleration, nib state, ink state, fatigue/rhythm state
- [x] Define `TrackPlan` and controller input contract
- [x] Implement desired-state generation from `DensePathGuide`
- [x] Implement PD tracking toward desired position/velocity
- [x] Implement corridor correction term and out-of-corridor detection
- [x] Implement explicit contact/lift state from guide schedule
- [x] Remove raw-keypoint-only steering from the new path
- [x] Render proof primitives with the broad-edge nib sweep, not circular dots
- [x] Support configurable internal proof-render supersampling for guided runs so crispness can be tuned for fidelity-first validation

## Risk + Rollback

New controller path is isolated behind a guided-hand feature flag. Existing evo/plain renderers remain the production paths.

## Evidence

- [x] controller unit tests showing plan position/velocity actually affect acceleration
- [x] primitive render snapshots for downstroke, hairline, minim pair
- [x] proof-render comparison at baseline vs higher supersample setting
- [x] gate report showing Level 0 metrics on proof primitives
