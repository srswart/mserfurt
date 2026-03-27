---
advance:
  id: ADV-SS-ANNOTATE-006
  title: Glyph Status Inspector — Per-Symbol Processing History and Selection Guidance in the Annotation Workbench
  system: scribesim
  primary_component: annotate
  components:
  - annotate
  - refextract
  - handvalidate
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
  - workflow_change
  - data_quality
  evidence:
  - ui
  - dataset
  - tests:integration
  status: proposed
---

## Objective

Let the operator click an individual glyph or join in the workbench debt list and see what processing has already happened for that symbol, why existing automatic candidates were not accepted into the reviewable catalog, and what kind of manual reference selection is most likely to produce an includable reviewed exemplar.

## Planned Implementation Tasks

- [ ] define a per-symbol status payload that summarizes the current tier state across `auto_admitted`, `quarantined`, `rejected`, `repair_only`, `promoted`, and `reviewed`
- [ ] carry forward structured blocker reasons from automatic corpus and promotion stages instead of collapsing everything to counts only
- [ ] add a workbench detail panel or modal for symbols selected from the "Needs Reviewed Samples" list
- [ ] show concrete processing history for the symbol, including representative source folios, candidate outcomes, and any recorded rejection or quarantine reasons
- [ ] generate operator guidance that explains what to select manually so the reviewed sample can enter the catalog cleanly, such as isolation, label certainty, join completeness, and artifact avoidance
- [ ] fail honestly when a blocker reason is unknown by showing "no structured reason recorded" rather than inventing an explanation

## Validation Gates

- [ ] selecting any debt symbol in the workbench opens a detail view with tier status, prior processing outcomes, and source provenance
- [ ] symbols that were blocked upstream show at least one concrete recorded blocker when one exists
- [ ] operator guidance is specific enough to distinguish a merely visible glyph from a catalog-eligible exemplar
- [ ] the UI makes clear whether a symbol is missing because no candidate existed, because candidates stayed quarantined or rejected, or because promotion evidence remained insufficient

## Risk + Rollback

This view must report pipeline truth, not a comforting story. If upstream stages do not yet emit structured reasons, surface that gap explicitly and keep the UI diagnostic rather than speculative.

## Evidence

- [ ] workbench symbol-status detail panel with blocker explanations and guidance
- [ ] machine-readable symbol-status report or API payload
- [ ] tests covering missing-reason, quarantined, rejected, and promoted-vs-reviewed cases
