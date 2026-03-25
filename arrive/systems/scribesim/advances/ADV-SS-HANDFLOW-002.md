---
advance:
  id: ADV-SS-HANDFLOW-002
  title: Stateful Word Controller — Cross-Glyph Continuity, Joins, and Ink Carryover
  system: scribesim
  primary_component: handflow
  components:
  - handflow
  - pathguide
  - render
  - ink
  started_at: 2026-03-24T14:25:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-24T14:25:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  - public_api
  evidence:
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Promote the controller from isolated glyph execution to persistent stateful writing across glyphs and words. This is where the hand starts behaving like one hand rather than many restarts.

## Planned Implementation Tasks

- [x] Carry velocity, pressure, rhythm, and ink state across glyph boundaries
- [x] Carry state across word boundaries unless a planned dip or deliberate pause occurs
- [x] Implement planned joins as contact segments when guide data marks them so
- [x] Implement explicit air transitions for true lifts only
- [x] Integrate ink carryover and dip-cycle state into the guided path
- [x] Prevent per-word simulator resets in the guided path

## Validation Gates

- [x] no forced lift inside contact joins
- [x] word continuity score >= 0.90 on proof words
- [x] ink-state transitions are monotonic and deterministic for fixed seed
- [x] baseline drift within a word <= 0.15 x-height

## Risk + Rollback

If persistent state destabilizes output, keep checkpointed state carryover optional and do not promote to line training.

## Evidence

- [x] proof-word snapshots for `und`, `der`, `wir`, `in`, `mir`
- [x] state trace log showing continuity across glyphs and words
- [x] gate report for proof vocabulary
