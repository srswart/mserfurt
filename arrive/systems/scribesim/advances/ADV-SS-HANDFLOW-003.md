---
advance:
  id: ADV-SS-HANDFLOW-003
  title: Folio Integration Adapter — Guided Hand Rendering Behind a Feature Flag
  system: scribesim
  primary_component: handflow
  components:
  - handflow
  - render
  - layout
  - groundtruth
  started_at: 2026-03-24T16:20:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T16:20:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - breaking_change
  - public_api
  evidence:
  - tidy:preparatory
  - tests:integration
  status: complete
---

## Objective

Integrate the guided-hand path into folio rendering while preserving the existing contracts and keeping rollout guarded behind a feature flag.

## Behavioral Change

After this advance:
- `scribesim render --approach guided` becomes available experimentally
- page PNG, pressure heatmap, and PAGE XML contracts remain unchanged
- evo/plain remain the default and fallback renderers
- guided rendering may use a higher internal supersample setting than the current default path when needed for stroke fidelity, while still emitting contract-compatible outputs

## Planned Implementation Tasks

- [x] Add guided-hand approach to the CLI and render report
- [x] Adapt line and folio composition to consume guided checkpoints
- [x] Reuse the existing broad-edge render pipeline for page output and heatmaps
- [x] Add configurable internal guided-render resolution / supersample setting for fidelity-first proof and folio runs
- [x] Preserve PAGE XML and Weather-facing output contracts
- [x] Add representative folio fixtures for clean, pressure-heavy, multi-sitting, and fatigue pages

## Validation Gates

- [x] deterministic folio render for fixed seed
- [x] PAGE XML remains valid and aligned
- [x] Weather pipeline accepts guided folio outputs unchanged
- [x] representative folios render without controller blow-up
- [x] higher supersample setting produces a measurable crispness or fidelity benefit before becoming the guided default

## Risk + Rollback

Feature-flagged rollout only. Rollback is to disable the guided approach in the CLI and keep evo/plain untouched.

## Evidence

- [x] integration tests for guided folio rendering
- [x] representative folio snapshots
- [x] comparison snapshots at baseline and higher internal guided render resolution
- [x] render report showing approach=`guided`
