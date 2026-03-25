---
advance:
  id: ADV-SS-HANDVALIDATE-003
  title: Exact Character Coverage Gates — Alias Detection and Text-Fidelity Metrics
  system: scribesim
  primary_component: handvalidate
  components:
  - handvalidate
  - handflow
  - tests
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
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Make folio review and rollout benches measure text fidelity explicitly instead of silently accepting wrong-symbol fallback aliases.

## Behavioral Change

After this advance:
- glyph resolution records whether a character was resolved exactly, through normalization, or through alias substitution
- folio review benches emit exact character coverage and alias counts
- review/rollout gates fail when alias substitutions are present

## Planned Implementation Tasks

- [x] Record glyph resolution mode in `SessionGuide`
- [x] Add validation metrics for exact character coverage, alias substitutions, and normalized substitutions
- [x] Feed those metrics into the folio review bench and dashboard outputs
- [x] Tighten folio rollout gates so alias use blocks promotion
- [x] Add unit/integration tests covering alias detection on real benchmark text

## Validation Gates

- [x] benchmark cases report exact character coverage
- [x] benchmark cases report alias substitution count
- [x] review bench fails if aliases are used in promoted folio text

## Risk + Rollback

This can make previously “passing” benches fail, but that is the intended correction. Rollback is to relax the new gates for exploratory-only runs, not to hide alias use.

## Evidence

- [x] tests covering glyph resolution tracking
- [x] folio bench summary includes exact coverage and alias counts
- [x] folio gate config includes text-fidelity gates
