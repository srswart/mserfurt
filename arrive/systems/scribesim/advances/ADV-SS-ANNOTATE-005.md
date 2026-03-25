---
advance:
  id: ADV-SS-ANNOTATE-005
  title: Cleanup-Aware Reviewed Freeze — Export Raw and Cleaned Reviewed Exemplars with Mask Provenance
  system: scribesim
  primary_component: annotate
  components:
  - annotate
  - evo
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

Freeze reviewed annotations with cleanup edits into a provenance-backed dataset that preserves raw crops, cleaned crops, and cleanup metadata separately.

## Planned Implementation Tasks

- [x] extend reviewed freeze to export both raw reviewed crops and cleaned reviewed crops when a cleanup mask exists
- [x] emit cleanup metadata and source-mask provenance in the reviewed freeze manifest
- [x] generate contact sheets for raw vs cleaned reviewed exemplars
- [x] keep reviewed-cleaned exports distinct from automatic corpus tiers and ordinary promoted exemplar bundles

## Validation Gates

- [x] every cleaned reviewed export has a matching raw reviewed export
- [x] cleanup metadata is sufficient to trace a cleaned crop back to its reviewed annotation and source folio
- [x] freeze fails clearly if cleanup references are corrupt or incomplete

## Risk + Rollback

Never collapse raw and cleaned reviewed crops into one ambiguous artifact. If cleanup export is incomplete, preserve the raw reviewed crop and fail the cleaned branch.

## Evidence

- [x] reviewed freeze manifest with raw and cleaned reviewed paths
- [x] raw vs cleaned contact sheets
- [x] downstream smoke test covering cleaned reviewed export loading

## Implementation Notes

This advance extends `scribesim.annotate.freeze` so reviewed cleanup becomes a first-class frozen artifact instead of transient UI state. The reviewed freeze now emits raw and cleaned reviewed crops side by side, records cleanup stroke counts and cleanup-aware path fields in the manifest, preserves cleanup metadata in the copied reviewed source manifest, and keeps `reviewed_exemplar_paths` pointed at the cleaned crop when one exists so downstream evofit can consume the cleaned reviewed version without losing raw provenance.
