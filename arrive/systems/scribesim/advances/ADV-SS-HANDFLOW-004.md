---
advance:
  id: ADV-SS-HANDFLOW-004
  title: Exact-Symbol Folio Output — Render Actual Trajectory and Refuse Unresolved Text
  system: scribesim
  primary_component: handflow
  components:
  - handflow
  - render
  - cli
  started_at: 2026-03-24T00:00:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T00:00:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 3
  risk_flags:
  - public_api
  evidence:
  - tests:integration
  - snapshot
  status: complete
---

## Objective

Switch guided folio output from guide-aligned convenience rendering to the controller's actual trajectory, and add an exact-symbol review mode that refuses unresolved characters.

## Planned Implementation Tasks

- [x] Render folio pages from `result.trajectory` instead of `guide_aligned_trajectory`
- [x] Keep guide-aligned traces for evaluation only
- [x] Add exact-symbol review mode for guided folio rendering
- [x] Fail review renders when unresolved characters or aliases are present
- [x] Update folio bench and CLI reporting to show text-resolution status

## Validation Gates

- [x] guided folio output remains contract-compatible
- [x] actual-trajectory rendering remains deterministic for fixed seed
- [x] exact-symbol review mode refuses alias-based output

## Risk + Rollback

Keep the current permissive path available only for exploratory debugging. Review and promotion paths should use exact-symbol mode.

## Evidence

- [x] comparison snapshots between guide-aligned and actual-trajectory output
- [x] integration tests for exact-symbol guided render mode
- [x] folio bench output showing resolution status in reports
