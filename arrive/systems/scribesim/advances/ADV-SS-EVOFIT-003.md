---
advance:
  id: ADV-SS-EVOFIT-003
  title: Cleanup-Aware Reviewed Evofit — Prefer Cleaned Reviewed Exemplars while Preserving Raw Provenance
  system: scribesim
  primary_component: evo
  components:
  - evo
  - annotate
  - pathguide
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
  - data_quality
  evidence:
  - dataset
  - snapshot
  status: complete
---

## Objective

Use cleaned reviewed exemplars as the preferred fit sources for nominal-form recovery, while retaining raw reviewed provenance and the ability to compare cleaned vs raw evofit outcomes.

## Planned Implementation Tasks

- [x] teach reviewed evofit to load cleaned reviewed crops when present and fall back to raw reviewed crops otherwise
- [x] preserve raw-path, cleaned-path, and cleanup provenance in fit-source summaries
- [x] compare cleaned reviewed evofit results against raw reviewed evofit baselines for the same symbols and joins
- [x] emit candidate bundles that disclose whether each fit source was raw or cleaned

## Validation Gates

- [x] reviewed evofit never loses the raw reviewed provenance for a cleaned fit source
- [x] cleaned fit-source usage is explicit in manifests, reports, and candidate summaries
- [x] cleaned reviewed evofit does not silently mix with automatic corpus fit sources

## Risk + Rollback

If cleaned reviewed crops introduce over-erasure or structural damage, the workflow must be able to fall back to raw reviewed fit sources without losing auditability.

## Evidence

- [x] cleanup-aware reviewed evofit runner and CLI/report updates
- [x] side-by-side raw vs cleaned fit-source summaries
- [x] provenance report showing raw/cleaned lineage for each nominal proposal

## Implementation Notes

This advance extends `scribesim.evofit.workflow` so reviewed-cleaned crops become the default input for reviewed nominal recovery when available, while a raw-only reviewed baseline bundle is emitted in parallel for comparison. Reviewed fit-source manifests, summaries, and provenance reports now disclose raw path, cleaned path, source variant, and cleanup stroke count explicitly, so cleanup-aware nominal recovery remains auditable and comparable against the untouched reviewed crops.
