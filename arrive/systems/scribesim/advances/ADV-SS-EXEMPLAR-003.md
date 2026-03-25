---
advance:
  id: ADV-SS-EXEMPLAR-003
  title: Exemplar Corpus — Automatic Glyph and Join Admission Sets for Active Review Slices
  system: scribesim
  primary_component: guides
  components:
  - guides
  - refextract
  - training
  started_at: 2026-03-24T00:00:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-25T00:00:00Z
  implementation_completed_by: openai-codex
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 2
  risk_flags:
  - data_quality
  evidence:
  - dataset
  - snapshot
  - tests:integration
  status: complete
---

## Objective

Build the automatic corpus-construction pipeline for active review slices, including glyph and join candidate extraction, tiering, frozen manifests, and review bundles.

## Planned Implementation Tasks

- [x] segment and extract candidate glyph crops and join crops automatically
- [x] cluster candidates by symbol and join type with confidence tiers
- [x] quarantine low-confidence crops instead of silently promoting them
- [x] freeze automatic admission / quarantine / rejection inventories for the review slice

## Validation Gates

- [x] automatic corpus bundle is reproducible for the active review slice
- [x] automatic glyph and join inventories are frozen with machine-readable manifests
- [x] held-out exemplar splits are present for legibility checks

## Risk + Rollback

Automatic admission quality may remain poor even when the pipeline is working mechanically. Reviewable exemplar truth, stronger promotion gates, and repair-sample quarantine are handled by follow-on advances instead of being forced into this one.

## Evidence

- [x] committed exemplar manifest with automatic admission / quarantine / rejection counts
- [x] review panels for the automatic corpus sets
- [x] held-out split summary for glyphs and joins
