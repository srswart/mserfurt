---
advance:
  id: ADV-SS-CURRICULUM-003
  title: Word and Line Curriculum — Frequent Words, Phrases, and Baseline Stability
  system: scribesim
  primary_component: curriculum
  components:
  - curriculum
  - handflow
  - handvalidate
  - layout
  started_at: 2026-03-24T15:10:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T15:10:00Z
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

Train and validate the guided hand model on full words and then short lines, while preserving legibility and continuity.

## Planned Implementation Tasks

- [x] Build proof vocabulary manifests: `und`, `der`, `wir`, `in`, `mir`, `und der`
- [x] Build short-line manifests: 3-word, 5-word, and 8-word lines
- [x] Measure OCR proxy, spacing stability, baseline drift, and join continuity
- [x] Keep promotion evaluation on accepted-tier held-out words and lines; report any exploratory soft-tier runs separately
- [x] Freeze checkpoint `line-v1` only after line-level gates pass

## Validation Gates

- [x] word recognition score >= 0.88 on proof vocabulary
- [x] line OCR proxy >= 0.85
- [x] spacing CV within calibrated script band
- [x] no catastrophic slant/x-height drift across a line

## Risk + Rollback

Line instability blocks folio integration. The guided path remains experimental until `line-v1` exists.

## Evidence

- [x] proof-line snapshots
- [x] JSON report comparing proof-line metrics to the current evo baseline
- [x] dataset admission report for proof vocabulary and held-out lines
- [x] checkpoint metadata for `line-v1`
