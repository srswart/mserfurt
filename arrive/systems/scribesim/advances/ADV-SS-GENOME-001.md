---
advance:
  id: ADV-SS-GENOME-001
  title: Genome Representation — Three-Layer Word/Glyph/Stroke Genomes
  system: scribesim
  primary_component: evo
  components:
  - evo
  - render
  started_at: 2026-03-21T01:00:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T08:39:19.524980Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  - public_api
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Implement TD-007 Part 1 + Part 4. Define the three-layer genome (WordGenome, GlyphGenome, StrokeGenome with BézierSegment) and implement rendering from genomes using existing nib physics (TD-002/004). The genome provides paths; nib angle width equation, stroke foot/attack, and ink depletion render those paths as marks.

## Behavioral Change



## Risk + Rollback



## Evidence

