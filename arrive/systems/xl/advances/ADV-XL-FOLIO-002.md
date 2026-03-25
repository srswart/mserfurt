---
advance:
  id: ADV-XL-FOLIO-002
  title: Folio — Private Manuscript Layout Recalibration
  system: xl
  primary_component: folio
  components:
  - folio
  started_at: 2026-03-23T00:00:00Z
  started_by: null
  implementation_completed_at: 2026-03-23T00:00:00Z
  implementation_completed_by: Codex
  updated_by: Codex
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - contract_change
  evidence:
  - tests:unit
  - docs:td-013
  status: in_progress
---

## Objective

Recalibrate XL folio structuring for a smaller private manuscript. The text
block should feel comfortable rather than maximally dense, with standard folios
targeting 22-24 lines and the smaller irregular stock from f14 onward
targeting 16-18 lines.

## Behavioral Change

After this advance:
- XL structures the manuscript against the smaller private-manuscript budgets
- The folio run may extend beyond `f17v` when the text volume requires it
- `f14` remains the start of the smaller irregular vellum stock, but later
  section starts are treated as earliest-start constraints rather than rigid
  fixed-slot boundaries

## Evidence

- `tests/test_folio.py`
- `docs/tech-direction/TD-013-private-manuscript-layout.md`
