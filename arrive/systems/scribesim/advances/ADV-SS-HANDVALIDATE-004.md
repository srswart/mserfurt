---
advance:
  id: ADV-SS-HANDVALIDATE-004
  title: Nominal Legibility Gates — Reviewed Raw vs Cleaned Exemplar-Fit Review Slice Validation
  system: scribesim
  primary_component: handvalidate
  components:
  - handvalidate
  - pathguide
  - handflow
  started_at: 2026-03-26T00:00:00Z
  started_by: openai-codex
  implementation_completed_at: 2026-03-26T00:00:00Z
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

Add explicit nominal-guide and exemplar-backed legibility gates so TD-014 cannot claim progress when the guide set itself is unreadable, and so raw-reviewed, cleaned-reviewed, and guided/controller outputs are evaluated separately.

## Planned Implementation Tasks

- [x] add nominal-render legibility metrics against held-out exemplar crops for both raw-reviewed and cleaned-reviewed nominal proposals
- [x] separate nominal-guide gates from controller-following gates
- [x] update review benches to report raw nominal legibility, cleaned nominal legibility, and controller legibility distinctly
- [x] block promotion if nominal guide renders are unreadable even when exact-symbol coverage is 1.0

## Validation Gates

- [x] nominal guide legibility passes before handflow folio review is considered
- [x] review dashboards distinguish raw nominal failure, cleaned nominal failure, and controller failure
- [x] exemplar-fit review slice can only pass when cleaned nominal and guided renders are legible, while raw nominal remains available as audit evidence

## Risk + Rollback

This may make current review outputs fail more clearly. That is intended: unreadable nominal guides should fail fast instead of contaminating controller evaluation, and cleanup should not be allowed to hide regressions without a raw-reviewed baseline.

## Evidence

- [x] updated review dashboard with raw nominal, cleaned nominal, and guided sections
- [x] held-out exemplar metric reports
- [x] promotion gates that explicitly separate guide and controller failure modes

## Implementation Notes

This advance adds `scribesim.handvalidate.nominal_review.run_reviewed_nominal_validation` plus the CLI command `validate-reviewed-nominal-guides`. The new bench loads the reviewed evofit cleaned run, the raw reviewed baseline run, and the promoted reviewed guide catalog, then scores raw nominal, cleaned nominal, and guided/controller renders separately on the reviewed slice. The new `reviewed_nominal` gate in `shared/hands/validation/gates.toml` enforces exact-symbol coverage and explicit raw-vs-cleaned-vs-guided legibility deltas so unreadable nominal guides fail before folio-level controller claims are made.
