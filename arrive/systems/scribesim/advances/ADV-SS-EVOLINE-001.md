---
advance:
  id: ADV-SS-EVOLINE-001
  title: Line & Folio Composition — Context Passing, CLIO-7 Modifiers
  system: scribesim
  primary_component: evo
  components:
  - evo
  - cli
  started_at: 2026-03-21T02:30:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T09:27:26.549014Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags: []
  evidence:
  - tdd:red-green
  - tests:unit
  - tests:integration
  status: complete
---

## Objective

Implement TD-007 Part 5 + Part 7. Scale evolution from words to lines and folios. Implement evolve_line() with context passing (exit state → next word's starting condition), ink state tracking with dip cycles, and CLIO-7 contextual modifiers (fatigue, emotional state). Implement evolve_folio() with per-line progress logging. CLI: scribesim evolve-folio f01r.json --target docs/samples/33125_werbeschreiben.jpg. Warm-start optimization: cache evolved common-word genomes.

## Behavioral Change



## Risk + Rollback



## Evidence

