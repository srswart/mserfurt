---
advance:
  id: ADV-SS-EVOFIT-001
  title: Evofit Nominal Forms — Exemplar-Driven Glyph and Short-Join Recovery
  system: scribesim
  primary_component: evo
  components:
  - evo
  - guides
  - training
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

Use evo only to fit nominal glyph and short-join forms against manuscript-derived crops, never to write promoted folio pages for TD-014. Exploratory fitting may begin from the automatic corpus, but promoted guide freeze must consume only `promoted_exemplars`.

## Planned Implementation Tasks

- [x] add a glyph/short-join evofit workflow that consumes exemplar crops
- [x] reuse exemplar-aware fitness and contextual allograph logic where relevant
- [x] emit best candidates, fitness traces, and frozen nominal-form proposals
- [x] ensure evofit outputs can be converted into `DensePathGuide` assets

## Validation Gates

- [ ] evofit candidates beat the previous nominal guide set on exemplar-backed recognition
- [x] evofit outputs remain bounded and structurally convertible into guides
- [x] no evofit stage writes promoted folio pages for TD-014

## Risk + Rollback

If evofit fails to produce readable nominal forms for a symbol, that symbol remains unpromoted. The fallback is to improve the exemplar corpus, not to let evo take over folio rendering.

## Evidence

- [x] frozen evofit candidate set for the active review alphabet
- [x] per-symbol fitness or similarity reports
- [x] comparison snapshots against previous nominal guides

## Implementation Notes

The exploratory evofit workflow is implemented in `scribesim.evofit`, exposed via `scribesim evofit-corpus`, and exercised against the current automatic active-review corpus at `shared/training/handsim/evofit_active_review_v1`. The current exploratory bundle converts 14 of 18 targets into guides and beats the previous nominal guide on 5 of 18 targets, so promoted guide freeze remains correctly gated on the downstream exemplar-hardening and guide-freeze advances rather than this exploratory pass alone.
