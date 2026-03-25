---
advance:
  id: ADV-SS-HANDVALIDATE-002
  title: Folio Regression Bench — A/B Validation, Dashboard, and Rollout Gates
  system: scribesim
  primary_component: handvalidate
  components:
  - handvalidate
  - metrics
  - render
  - tests
  started_at: 2026-03-24T00:00:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T00:00:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 4
  risk_flags:
  - public_api
  evidence:
  - tests:integration
  - snapshot
  status: complete
---

## Objective

Build the final folio-level regression bench and stop/go dashboard for promoting or rejecting the guided-hand path.

## Behavioral Change

After this advance:
- the repo has an explicit decision point for whether guided hand stays experimental or is promoted
- folio rollout uses evidence, not intuition

## Planned Implementation Tasks

- [x] Define representative folio set for A/B evaluation against evo/plain
- [x] Measure folio-level readability, spacing stability, baseline stability, and join continuity
- [x] Run downstream contract checks: PAGE XML validity, Weather compatibility
- [x] Build dashboard/report summarizing pass/fail gates and regression deltas
- [x] Define hard rollback thresholds and promotion rule

## Promotion Rule

Guided hand is promotable only if:
- [x] all folio hard gates pass
- [x] readability-critical metrics are not materially worse than evo baseline
- [x] at least one representative folio is better on continuity/organicness metrics without failing legibility

## Risk + Rollback

If folio gates fail, the guided path remains experimental. No default renderer change is allowed.

## Evidence

- [x] A/B dashboard or summary report committed
- [x] representative folio diffs and snapshots
- [x] explicit promotion decision recorded in evidence output
