---
advance:
  id: ADV-SS-WORDTRAIN-001
  title: Word Training — Path Extraction, CMA-ES Hand Dynamics Fitting
  system: scribesim
  primary_component: training
  components:
  - training
  - handsim
  - guides
  - metrics
  started_at: 2026-03-20T23:15:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T19:04:42.867868Z
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
  - tests:integration
  status: complete
---

## Objective

Implement TD-005 Parts 2 and 4. Extract writing path from target manuscript word (skeletonize, order, estimate speed/pressure). Fit hand dynamics to reproduce the path using CMA-ES + DTW distance. Train on "und" as proof of concept. Extend to "und der" to validate word transitions. Implement quality gates for incremental extension.

## Behavioral Change



## Planned Implementation Tasks

- [ ] Implement word image skeletonization (thin to single-pixel path)
- [ ] Implement skeleton path ordering (left-to-right with stroke detection)
- [ ] Implement speed/pressure estimation from ink density along skeleton
- [ ] Implement DTW distance metric between simulated and extracted paths
- [ ] Implement CMA-ES fitting loop: optimize hand dynamics to minimize DTW distance
- [ ] Train on "und" as proof of concept — extract target, fit, evaluate
- [ ] Extend to "und der" to validate word transition handling
- [ ] Implement quality gates for incremental vocabulary extension
- [ ] Test: fitted dynamics on "und" produce DTW distance below threshold

## Risk + Rollback

New dependency on skeletonization and DTW libraries. Training is offline — no runtime impact. Rollback by discarding trained parameters.

## Evidence

- [ ] tdd:red-green — write DTW distance and fitting convergence tests before implementation
- [ ] tests:unit — unit tests for skeletonization, path ordering, speed estimation
- [ ] tests:integration — integration test for full extract-fit-evaluate pipeline on "und"
