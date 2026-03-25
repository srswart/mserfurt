---
advance:
  id: ADV-SS-HANDVALIDATE-001
  title: Hand Validation Suite — Primitive/Glyph/Word Metrics and Promotion Gates
  system: scribesim
  primary_component: handvalidate
  components:
  - handvalidate
  - metrics
  - pathguide
  started_at: 2026-03-24T13:20:03Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T13:20:03Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - public_api
  evidence:
  - tdd:red-green
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Create the stop/go measurement suite for TD-014 before controller promotion begins. Every later advance depends on deterministic metrics and gate evaluators for primitive, glyph, word, line, and folio checkpoints.

## Behavioral Change

After this advance:
- every training run can produce a machine-readable pass/fail decision
- no later stage advances on subjective visual review alone

## Planned Implementation Tasks

- [x] Implement primitive metrics: corridor containment, self-intersection count, contact/lift accuracy, width-profile error
- [x] Implement glyph metrics: DTW centerline distance, curvature histogram distance, template/recognition score
- [x] Implement join/word metrics: continuity score, OCR proxy, exit tangent error, baseline drift within word
- [x] Implement line/folio metrics: spacing CV, x-height stability, page-level OCR proxy, downstream contract checks
- [x] Implement data-admission metrics: accepted / soft / rejected counts, held-out coverage, source-resolution summary
- [x] Define promotion gates for each curriculum level in config
- [x] Define dataset policy in config: accepted-only for promotion, soft-tier optional for exploratory runs
- [x] Implement `evaluate_gate(stage, metrics) -> pass/fail + reasons`
- [x] Emit structured JSON reports and compact markdown summaries

## Risk + Rollback

If some metrics prove noisy, keep them advisory and preserve a smaller hard-gate set. The system should still record them for trend analysis. Soft-tier data must never be promoted by accident because of an aggregate score.

## Evidence

- [x] deterministic unit tests for each metric
- [x] integration test verifying gate pass/fail decisions for known good/bad fixtures
- [x] committed gate config with explicit thresholds for primitive, glyph, word, line, and folio stages
- [x] committed dataset-policy config covering accepted / soft / rejected handling
