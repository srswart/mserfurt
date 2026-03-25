---
advance:
  id: ADV-SS-PATHGUIDE-003
  title: Active Folio Alphabet Dataset — Exact Guides for Missing Characters, Capitals, and Diacritics
  system: scribesim
  primary_component: pathguide
  components:
  - pathguide
  - guides
  - training
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
  - new_dependency
  evidence:
  - tests:integration
  - snapshot
  status: complete
---

## Objective

Expand the dense guide inventory from the starter alphabet to the exact character set required by the proof folios, eliminating wrong-shape alias substitutions.

## Planned Implementation Tasks

- [x] Build active character inventory from the proof folio review set
- [x] Add exact lowercase guides for missing characters such as `s`, `v`, `z`
- [x] Add exact capital guides needed by proof folio lines
- [x] Add exact diacritic/umlaut guides such as `ů`
- [x] Freeze dataset as an active-folio alphabet manifest with provenance and held-out coverage

## Validation Gates

- [x] exact character coverage = 1.0 on the review folio inventory
- [x] all previously aliased review-slice characters now have exact guides in the committed dataset
- [x] all new guides validate structurally and have provenance

## Risk + Rollback

Do not promote partially covered datasets. Missing characters must stay unresolved rather than falling back to wrong glyph identities in review mode.

## Evidence

- [x] committed active-folio alphabet manifest
- [x] exact-character coverage report for review folios
- [x] snapshots for all newly added characters
