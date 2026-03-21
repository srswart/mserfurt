---
advance:
  id: ADV-SS-CMAES-001
  title: CMA-ES Group Optimizer — Multi-Parameter Fitting
  system: scribesim
  primary_component: tuning
  components:
  - tuning
  - metrics
  started_at: 2026-03-20T22:20:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T18:24:57.572927Z
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
  - tidy:preparatory
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Implement TD-004 Part 3 and TD-003-A S2. Replace single-parameter optimizer with CMA-ES group optimization. Define parameter groups (nib_physics, baseline_geometry, hand_dynamics, letterform_proportion, ink_material) each targeting specific metrics. Implement staged execution with quality gates.

## Behavioral Change



## Planned Implementation Tasks

- [ ] Install cma package (pip install cma)
- [ ] Define parameter group config format (parameters, target_metrics, method, priority)
- [ ] Implement CMAESGroupOptimizer using python-cma library
- [ ] Implement staged execution pipeline with quality gates (M1<0.15, M2<0.15, etc.)
- [ ] Update scribesim fit CLI with --staged and --gate flags
- [ ] Test: CMA-ES on nib_physics group reduces M1 better than single-parameter

## Risk + Rollback

New dependency on python-cma. Existing single-parameter optimizer remains as fallback. Rollback by reverting to current optimizer.

## Evidence

- [ ] tdd:red-green — write optimizer comparison tests before implementation
- [ ] tidy:preparatory — extract optimizer interface for swappable backends
- [ ] tests:unit — unit tests for parameter group config, staged pipeline
- [ ] tests:integration — integration test comparing CMA-ES vs single-parameter on nib_physics group
