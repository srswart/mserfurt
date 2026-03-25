---
advance:
  id: ADV-SS-ANNOTATE-003
  title: Reviewed Exemplar Freeze — Provenance-Backed Crop Export from the Annotation Workbench
  system: scribesim
  primary_component: annotate
  components:
  - annotate
  - training
  - refextract
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

Freeze reviewed glyph and join annotations into a trusted exemplar dataset that downstream nominal-form recovery can consume.

## Planned Implementation Tasks

- [x] export reviewed annotation crops into a dedicated reviewed exemplar root
- [x] write frozen manifests with symbol, join label, quality tier, source path, and pixel bounds
- [x] generate reviewed glyph and join contact sheets for operator inspection
- [x] keep reviewed exports separate from automatic corpus tiers and repair buckets

## Validation Gates

- [x] reviewed exemplar manifests are deterministic and reproducible
- [x] reviewed glyph and join crops match the saved annotation bounds
- [x] downstream stages can consume reviewed exemplars without falling back to auto-admitted crops

## Risk + Rollback

If export semantics need to evolve, keep the reviewed annotation source manifest stable and version the crop-export format separately.

## Evidence

- [x] reviewed exemplar freeze command and manifest writer
- [x] reviewed glyph and join contact sheet generation
- [x] downstream smoke test against the reviewed exemplar root

## Implementation Notes

The new `scribesim.annotate.freeze` module freezes reviewed workbench annotations into a dedicated reviewed exemplar dataset with cropped glyph and join images, a trusted reviewed freeze manifest, a copy of the reviewed source manifest, contact sheets, and a downstream smoke test that verifies current evofit target loading against the frozen dataset. The CLI entrypoint is `scribesim freeze-reviewed-exemplars`. The actual workspace bundle remains operator-driven: until the reviewed workbench has saved real annotations, the freeze command will fail clearly rather than fabricating reviewed truth.
