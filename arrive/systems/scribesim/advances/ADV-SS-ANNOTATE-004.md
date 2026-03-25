---
advance:
  id: ADV-SS-ANNOTATE-004
  title: Reviewed Cleanup Workbench — Non-Destructive Artifact Removal for Glyph and Join Annotations
  system: scribesim
  primary_component: annotate
  components:
  - annotate
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
  - ui
  - dataset
  status: complete
---

## Objective

Let the operator clean nearby-stroke artifacts out of a reviewed glyph or join crop without overwriting the source folio image or losing the raw reviewed bounds.

## Planned Implementation Tasks

- [x] add an annotation-selected cleanup editor to the local workbench
- [x] support erase and restore operations over the reviewed crop at high zoom
- [x] persist cleanup masks or erase-stroke layers per reviewed annotation with exact source provenance
- [x] show raw vs cleaned previews in the workbench so the operator can confirm that only invalid artifacts were removed

## Validation Gates

- [x] cleanup edits are stored non-destructively and can be removed or re-edited later
- [x] raw reviewed bounds remain unchanged after cleanup
- [x] the workbench can reopen an annotation and restore its saved cleanup mask accurately

## Risk + Rollback

Do not treat cleanup as destructive image editing. If the cleanup UI is too aggressive or lossy, prefer no cleanup over irreversible source mutation.

## Evidence

- [x] cleanup-capable reviewed workbench UI
- [x] reviewed manifest entries with cleanup metadata
- [x] visual raw vs cleaned preview for at least one glyph and one join

## Implementation Notes

This advance adds the reviewed-cleanup editor to `scribesim.annotate.workbench`. Reviewed annotations now persist an optional non-destructive `cleanup_strokes` layer alongside the raw bounds, and the workbench renders side-by-side raw and cleaned previews for the selected annotation. The operator can erase or restore nearby-character artifacts at high zoom without mutating the source folio image or the raw reviewed crop.
