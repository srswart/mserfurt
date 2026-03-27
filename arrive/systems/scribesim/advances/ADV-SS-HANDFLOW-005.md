---
advance:
  id: ADV-SS-HANDFLOW-005
  title: Reviewed Exemplar-Fit Flow Recovery — Handflow Training on Cleanup-Aware Promoted Nominal Guides
  system: scribesim
  primary_component: handflow
  components:
  - handflow
  - curriculum
  - render
  started_at: 2026-03-25T00:00:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-25T00:00:00Z
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

Wire handflow to the reviewed cleanup-aware promoted guide catalog so exact-symbol review-slice rendering and proof runs consume readable nominal guides backed by reviewed exemplar truth, while preserving enough raw-vs-cleaned evidence to debug controller behavior honestly.

## Planned Implementation Tasks

- [x] point guided proof and folio render paths at the reviewed cleanup-aware guide catalog frozen by `ADV-SS-PATHGUIDE-004`
- [x] preserve guide-catalog provenance and raw-vs-cleaned nominal evidence in handflow metadata for debugging
- [x] expose an explicit reviewed guide catalog override for guided render commands
- [x] preserve exact-symbol refusal behavior for unresolved text

## Validation Gates

- [x] guided exact-symbol review renders can consume the reviewed promoted guide catalog or an explicit override catalog
- [x] guided render metadata reports which nominal guide lane was used, including reviewed raw/cleaned source counts when available
- [x] exact-symbol refusal remains active for unresolved text even when a reviewed override catalog is used
- [x] controller-vs-nominal comparisons still use the actual trajectory mode and aligned reference outputs

## Risk + Rollback

If controller dynamics degrade a readable reviewed cleanup-aware nominal guide set into illegible output, the problem is now correctly isolated to handflow and must be fixed there rather than hidden by guide changes or by falling back to weaker automatic corpus inputs.

## Evidence

- [x] reviewed-guide catalog support in handflow session and folio render paths
- [x] guided folio metadata showing reviewed or override guide-lane provenance
- [x] integration tests covering reviewed promoted catalog loading and exact-symbol guided rendering

## Implementation Notes

This advance updates `scribesim.handflow.session`, `scribesim.handflow.folio`, and the guided render CLI so handflow can consume the reviewed promoted guide catalog from `ADV-SS-PATHGUIDE-004` or an explicit override path. Guided render metadata now records the nominal guide lane, catalog path, and reviewed raw/cleaned source counts, which gives `HANDVALIDATE-004` the evidence it needs to compare controller output against the correct nominal source instead of the earlier clone/toy guide lane.
