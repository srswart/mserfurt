---
advance:
  id: ADV-SS-RUSTEVO-001
  title: Rust Crate — Genome Structs, Bézier Rendering, PyO3 Bindings
  system: scribesim
  primary_component: evo-rust
  components:
  - evo-rust
  started_at: 2026-03-21T01:50:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-21T09:09:59.960866Z
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

Implement TD-007 Addendum A items 1-2. Create the scribesim-evo Rust crate with PyO3 bindings. Port genome data structures (WordGenome, GlyphGenome, BézierSegment) to Rust. Implement render_word() in Rust with nib-angle width equation, stroke foot/attack, ink depletion at configurable DPI. Verify: Rust rendering matches Python rendering for the same genome.

## Behavioral Change



## Risk + Rollback



## Evidence

