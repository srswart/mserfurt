---
advance:
  id: ADV-SS-HANDFLOW-005
  title: Exemplar-Fit Flow Recovery — Handflow Training on Promoted Nominal Guides
  system: scribesim
  primary_component: handflow
  components:
  - handflow
  - curriculum
  - render
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

Retrain and retune handflow on exemplar-fit nominal guides so the controller learns the intended stroke approach and cross-character flow from readable templates.

## Planned Implementation Tasks

- [ ] point the review-slice curriculum at the exemplar-fit guide catalog
- [ ] infer or tune stroke approach, entry/exit, and join behavior from the promoted guides
- [ ] rerun word and line curriculum on the real review slice
- [ ] preserve exact-symbol refusal behavior for unresolved text

## Validation Gates

- [ ] guided review-slice words become nominally legible before folio claims are made
- [ ] join continuity remains inside TD-014 gates on the exemplar-fit guide set
- [ ] actual trajectory remains close to the exemplar-fit nominal path without collapsing readability

## Risk + Rollback

If controller dynamics degrade a readable nominal guide set into illegible output, the problem is now correctly isolated to handflow and must be fixed there rather than hidden by guide changes.

## Evidence

- [ ] updated word/line checkpoint on exemplar-fit guides
- [ ] review snapshots for proof words and proof lines
- [ ] comparison against the previous unreadable guide set
