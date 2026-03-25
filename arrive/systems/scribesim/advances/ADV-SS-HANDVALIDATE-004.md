---
advance:
  id: ADV-SS-HANDVALIDATE-004
  title: Nominal Legibility Gates — Exemplar-Fit Review Slice Validation
  system: scribesim
  primary_component: handvalidate
  components:
  - handvalidate
  - pathguide
  - handflow
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

Add explicit nominal-guide and exemplar-backed legibility gates so TD-014 cannot claim progress when the guide set itself is unreadable.

## Planned Implementation Tasks

- [ ] add nominal-render legibility metrics against held-out exemplar crops
- [ ] separate nominal-guide gates from controller-following gates
- [ ] update review benches to report nominal legibility, controller legibility, and folio legibility distinctly
- [ ] block promotion if nominal guide renders are unreadable even when exact-symbol coverage is 1.0

## Validation Gates

- [ ] nominal guide legibility passes before handflow folio review is considered
- [ ] review dashboards distinguish guide failure from controller failure
- [ ] exemplar-fit review slice can only pass when both nominal and guided renders are legible

## Risk + Rollback

This may make current review outputs fail more clearly. That is intended: unreadable nominal guides should fail fast instead of contaminating controller evaluation.

## Evidence

- [ ] updated review dashboard with nominal legibility section
- [ ] held-out exemplar metric reports
- [ ] promotion gates that explicitly separate guide and controller failure modes
