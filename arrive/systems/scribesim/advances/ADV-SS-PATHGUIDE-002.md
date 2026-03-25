---
advance:
  id: ADV-SS-PATHGUIDE-002
  title: Alphabet and Join Guide Dataset — Dense Guides for Common Letters and Bigrams
  system: scribesim
  primary_component: pathguide
  components:
  - pathguide
  - guides
  - training
  started_at: 2026-03-24T13:47:51Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T13:47:51Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence:
  - tests:unit
  - tests:integration
  - snapshot
  status: complete
---

## Objective

Expand dense guide coverage from proof primitives to a practical starter alphabet and join inventory suitable for word-level training. This advance is automatic-first: extracted traces and automatic transcription are the default source, with hand correction reserved for high-value failures.

## Planned Implementation Tasks

- [x] Create dense guides for starter letters: `u`, `n`, `d`, `e`, `r`, `i`, `m`, `a`, `o`, `t`, `h`
- [x] Create dense guides for common joins: `u→n`, `n→d`, `d→e`, `e→r`, `i→n`, `m→i`, `r→space`, `space→d`
- [x] Build starter dataset automatically from segmentation + transcription + trace extraction outputs where available
- [x] Import from extracted trace assets where available; hand-correct only where automatic extraction repeatedly fails on important glyphs or joins
- [x] Quarantine low-confidence automatic samples into soft/rejected tiers rather than mixing them into promoted guide assets
- [x] Version and freeze dataset as `starter-alphabet-v1`
- [x] Create held-out validation split for starter glyphs, joins, and proof words
- [x] Validate that every guide meets density, corridor, and entry/exit constraints

## Validation Gates

- [x] all starter guides validate structurally
- [x] no accidental self-intersections in starter guides
- [x] every starter join has explicit contact/lift schedule
- [x] every promoted guide is backed by accepted-tier source samples only

## Risk + Rollback

Dataset-only change. If some guides are poor, keep them excluded and do not use them in promotion sets.

## Evidence

- [x] committed dataset manifest
- [x] confidence-tier manifest with accepted / soft / rejected counts per glyph and join
- [x] overlay snapshots for each starter glyph and join
- [x] validation report for `starter-alphabet-v1`
