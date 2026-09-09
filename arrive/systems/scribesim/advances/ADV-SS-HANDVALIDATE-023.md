---
advance:
  id: "ADV-SS-HANDVALIDATE-023"
  title: "Approved Appearance — Versioned Reference Contract"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate", "tests"]
  started_at: "2026-09-09T08:34:53Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 0
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  model_usage: []
  status: in_progress
---

## Objective

Implement the owner-approved TD-018 Addendum B section 14 reference contract.
Keep candidate-derived approved appearance, independent style provenance and
mechanical evidence distinct without changing historical numerical decisions.

## Behavioral Change

Version and pin approved actual-ink regression references and their fixture/tool
scope. Expose separate construction, motion, appearance, style and regression
results. Exact deterministic replay is an identity check, never new quality,
generalization or layer admission. Prepare a held-out placement protocol without
starting an unbudgeted physical experiment or borrowing old render allowances.

## Planned Implementation Tasks

- [x] branch: `advance/ss-handvalidate-023`.
- [x] tidy: new opt-in script API preserves all frozen evaluator source identities.
- [ ] test: provenance/identity, scope, frame/tool, corruption, fail-closed decisions and independent report verification.
- [ ] feat/fix: registry, replay comparison, five-channel report, immutable build and consumer-pinned read-only inspector.
- [ ] protocol: freeze current zero-execution validation and prepare held-out placements, controls and explicit execution-authorization boundary.
- [ ] evidence: validate saved first/replay samples and adversarial mutations; no re-render or fitting.
- [ ] docs/merge: publish contract state, update plan and merge locally.

## Bug Fixes

- [ ] Prevent derived reference relabeling, out-of-scope owner approval and mechanical success laundering a failed style gate into overall acceptance.

## Risk + Rollback

- Risk: dropping a failed gate by renaming it, treating self-comparison as transfer, or using candidate-derived pixels as independent ground truth.
- Rollback: withhold the new contract output; never mutate old archives, targets, numerical limits or source hashes. All S2/real/context flags remain false.
- Budget: this implementation validation performs zero controller executions, raster renders and optimization evaluations. New held-out physical runs require their own concrete authorization and execution freeze.
- Existing handvalidate component is incubating; no new component or dependency is necessary.

## Evidence

- [x] tidy:preparatory unnecessary; new script API deliberately avoids old source drift.
- [ ] tdd:red-green; tests:unit; tests:integration.
- [ ] Consumer-pinned registry/report inspection and original artifact integrity.
- [ ] Separate first/replay baseline identity and non-admitting held-out protocol state.

## CI Evidence Notes

Run focused tests, plan/rules/whitespace and strict PR metadata checks. Record
installed parser limitations separately from provider CI. Implementation
completion is not a held-out experiment, owner approval of unseen output or S2.

## Changes Made

### 2026-09-09 - implementation scope

Owner says “Okay go ahead with implemetation.” The approved design record is
immutable and remains an at-review snapshot. Implement versioned reference roles,
fail-closed consumers and a concrete next-protocol boundary; do not refit shapes,
invent aesthetic tolerances or silently move 0.05 to a new reference. Registry
and evidence live outside old run directories. ARRIVE template 0.1.24.

## Check for Understanding

1. Why does an exact approved-reference match establish replay identity but not independent style accuracy?
2. Which reference, candidate, fixture, frame and tool bindings must a consumer verify?
3. Why does a prepared held-out protocol not authorize execution or inherit owner approval for unseen combinations?
