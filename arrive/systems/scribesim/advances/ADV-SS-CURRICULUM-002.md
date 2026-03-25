---
advance:
  id: ADV-SS-CURRICULUM-002
  title: Glyph and Join Curriculum — Legible Single Letters and Connected Bigrams
  system: scribesim
  primary_component: curriculum
  components:
  - curriculum
  - handflow
  - handvalidate
  - pathguide
  started_at: 2026-03-24T14:05:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T14:05:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence:
  - tests:integration
  - snapshot
  status: complete
---

## Objective

Train the guided hand path on single letters and joins using the frozen primitive checkpoint and starter guide dataset.

## Planned Implementation Tasks

- [x] Build glyph curriculum manifests for the starter alphabet
- [x] Build join curriculum manifests for the starter bigrams
- [x] Train/tune against recognition-critical metrics rather than aesthetics alone
- [x] Use accepted-tier held-out glyph/join samples for promotion metrics; keep soft-tier runs exploratory only
- [x] Freeze checkpoint `glyph-join-v1` only on gate pass

## Validation Gates

- [x] glyph recognition/template score >= 0.90 on starter set
- [x] DTW centerline distance <= 0.20 x-height
- [x] join continuity score >= 0.90
- [x] zero uncontrolled exits outside corridor

## Risk + Rollback

No promotion to word training until all starter glyphs and joins pass. Failed runs remain experimental.

## Evidence

- [x] confusion matrix or recognition summary for starter glyphs
- [x] join continuity report for starter bigrams
- [x] report showing promotion metrics were computed on accepted-tier held-out data
- [x] snapshots for good/bad examples with gate decisions
