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
  started_at: null
  started_by: null
  implementation_completed_at: null
  implementation_completed_by: null
  updated_by: openai-codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - public_api
  evidence:
  - tests:integration
  - snapshot
  status: proposed
---

## Objective

Use evo only to fit nominal glyph and short-join forms against manuscript-derived crops, never to write promoted folio pages for TD-014. Exploratory fitting may begin from the automatic corpus, but promoted guide freeze must consume only `promoted_exemplars`.

## Planned Implementation Tasks

- [ ] add a glyph/short-join evofit workflow that consumes exemplar crops
- [ ] reuse exemplar-aware fitness and contextual allograph logic where relevant
- [ ] emit best candidates, fitness traces, and frozen nominal-form proposals
- [ ] ensure evofit outputs can be converted into `DensePathGuide` assets

## Validation Gates

- [ ] evofit candidates beat the previous nominal guide set on exemplar-backed recognition
- [ ] evofit outputs remain bounded and structurally convertible into guides
- [ ] no evofit stage writes promoted folio pages for TD-014

## Risk + Rollback

If evofit fails to produce readable nominal forms for a symbol, that symbol remains unpromoted. The fallback is to improve the exemplar corpus, not to let evo take over folio rendering.

## Evidence

- [ ] frozen evofit candidate set for the active review alphabet
- [ ] per-symbol fitness or similarity reports
- [ ] comparison snapshots against previous nominal guides
