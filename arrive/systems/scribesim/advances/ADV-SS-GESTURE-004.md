---
advance:
  id: "ADV-SS-GESTURE-004"
  title: "Stroke Context — Entry Body Exit and Boundary Investigation"
  system: "scribesim"
  primary_component: "gesture"
  components: ["gesture","curriculum","handflow","pathguide","handvalidate","tests"]
  started_at: "2026-09-10T03:54:13.857346+00:00"
  implementation_completed_at: "2026-09-10T04:18:42Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: []
  evidence:
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/investigation/snapshot-001/report.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/investigation/README.md"
  model_usage: []
  status: complete
---

## Objective

Investigate the actual frozen n/u/m stroke programs and determine which entry/body/exit spans, previous/next port states and pen-down join/retrace versus genuine lift hypotheses are supportable. Preserve the validated C006 baseline; do not fit the nearly indistinguishable width/spacing grid.

Follows [TD-018 Addendum D](../../../../docs/tech-direction/TD-018-addendum-d-stroke-context-transitions.md).
Read-only implementation is complete; owner review of the proposed contract and
scope is now recorded in GESTURE-005's pinned contract. No training, new physical execution, provider CI or
acceptance is claimed. Existing components suffice.

## Behavioral Change

A pinned read-only audit replaces assumptions about connectors and letter variants with explicit supported/unsupported inventory. Upward pen-down returns remain distinct from lifts. The owner receives a bounded hypothesis proposal, not a trained or physically accepted context model.

## Component Impact

- `scripts/stroke_context_audit.py`
- `tests/test_stroke_context_audit.py`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/investigation/`

Keep new adapters opt-in and outside frozen core identity scans. Exact paths and
any required migration must be frozen before implementation, not inferred as
permission to change canonical sources or add identity-scanned spec files.

## Dependencies

- [ADV-SS-GESTURE-003](ADV-SS-GESTURE-003.md)
- [ADV-SS-CURRICULUM-015](ADV-SS-CURRICULUM-015.md)
- [ADV-SS-HANDVALIDATE-024](ADV-SS-HANDVALIDATE-024.md)

Owner scope/protocol approvals in Addendum D are independent gates, not implied
by a dependency's implementation status. C006's full completion is not a
prerequisite for consuming its specifically pinned P2 mechanical evidence.

## Planned Implementation Tasks

- [x] workflow: preserve all existing uncommitted work; no branches, commits or merges without explicit later authorization.
- [x] tidy: assess narrowly required preparation; do not refactor frozen sources or unrelated components.
- [x] Verify the candidate, original/recovery source manifests and C006 P2 independent inspection pin from Addendum D; record exact scope rather than requiring the entire in-progress C006 advance.
- [x] Map canonical primitive/gesture occurrences and cubic spans to entry/body/exit roles, including shared spans; audit body anchors, directed ports, contact runs, existing inter-letter transfers and overlap ownership.
- [x] Classify previous-exit and following-entry states, BOS/EOS and unsupported combinations; do not key rules by words, fixtures, seeds or per-instance residuals.
- [x] Audit the at-most-15-string shortlist and prior exposure/reservations before admitting diagnostic triples; preserve all existing sealed text reservations.
- [x] Use read-only geometry/trace analysis to distinguish form adaptation, join, retrace and lift requirements. No controller execution, raster generation, fitting or source mutation in this investigation.
- [x] Propose at most three transition families and four deterministic hypotheses including context-off; identify missing metrics, local parameter bounds and possible body exceptions without approving them.
- [x] Produce examples/annotation specifications, exact-null expectations, negative-control requirements and resource inventory estimates; any separately needed image generation requires an explicit bounded protocol.
- [x] Obtain owner review of the investigated port/span contract and selected scope before GESTURE-005 implementation.

## Bug Fixes

- [x] No frozen behavior fix was needed; preserve earlier fixed clock/contact/measurement behavior and failed artifacts. Only a new read-only adapter and tests were added.

## Risk + Rollback

- Risk: Mistaking existing intra-letter connections for cross-letter support, interpreting upstrokes as lifts, or introducing a hidden per-word alternate-glyph table.
- Rollback: Retain the audit as evidence and leave all proposed mappings unadmitted; do not change the baseline or unpause the old ranking exercise.
- Keep fixed tool/action, no-fatigue and no-fitting constraints. Proposed new
  geometry, frames or criteria require prospective approval; no phase-level
  reset of the old time/render debit is permitted.

## Evidence

- [x] Every investigated role and baseline transition traces to concrete canonical spans/contact events; unsupported cells and absent nu/uu identity traces are explicit. Derived exceptions remain unadmitted.
- [x] No evidence, labels or acceptance is inferred from an enlarged/difference view or inability to distinguish the old grid.
- [x] The owner approves the bounded hypothesis/contract proposal; all original bytes and budgets are preserved.
- [x] Record test-first evidence where code changes, exact commands, source/report
  pins and local results; do not fabricate tidy/test/physical success during planning.
- [x] Run plan, generated-rule, local-link and whitespace checks for the final scope.

## CI Evidence Notes

Local checks are not provider CI. Before any separately authorized merge, run
`arrive pr check --strict --json` and record provider/tool limitations honestly.
No branch, commit or merge is part of the current planning authorization.

## Changes Made

### 2026-09-10 — planned from the owner-approved stroke-context direction

- Defined a bounded deliverable and stop gates; implementation and evaluation
  remain unstarted. See Addendum D for retained baseline pins and budget limits.

### 2026-09-10 — read-only investigation implemented; owner review pending

- Template-first preparation used `arrive template render --kind advance --json`.
  No frozen refactor was required. All pre-existing changes remain uncommitted.
- Added the opt-in adapter and seven tests. Test-first run failed collection
  because the new module did not yet exist; the implemented focused suite passes
  (7 tests). The audit runtime blocks controller/raster entry points.
- `python -m scripts.stroke_context_audit snapshot` (using `.venv/bin/python`)
  verifies 12,771 original and 2,455 recovery artifacts, frozen contracts and
  independent inspection pin. Reads ten saved identity traces; compiles only
  the 12 exposed diagnostic strings, with no new physical or raster execution.
- Snapshot report SHA-256:
  `d7eb422948f7de6696221d2f026559ca603fb84a95e713e9e6cdce5aa95a6b75`.
  The independent 1,464-case measurement is reused, not remeasured by this audit.
- n/u/m have 4/4/6 canonical occurrences and one contact run each. Entry and
  exit spans overlap protected body; they are not free editable thirds. Ten
  saved traces confirm pen-down upstrokes and true inter-letter lifts.
- All previous exit directions share one class. Direct endpoint gaps are
  3.3924–6.2764 mm; no existing cross-letter join/retrace is admitted. Propose
  lift-preserving entry-only/exit-only/combined hypotheses plus exact null,
  explicit first/last handle exceptions, finite ±1-degree bounds and 0.04-mm
  displacement cap. None is owner-approved or executed.
- A 32-file metadata audit does not establish exhaustive historical absence:
  nuu/uuu/muu remain unadmitted. Sealed text images/traces remain unopened.
- Review the owner-facing proposal at
  `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/investigation/README.md`.
  GESTURE-004 stays in progress solely for required owner review; GESTURE-005
  remains planned, C006 ranking remains paused and all acceptance flags false.
- Exact read-only reinspection passes:
  `.venv/bin/python -m scripts.stroke_context_audit inspect --report-sha256 d7eb422948f7de6696221d2f026559ca603fb84a95e713e9e6cdce5aa95a6b75`.
- Regression command:
  `.venv/bin/python -m pytest -q tests/test_stroke_context_audit.py tests/test_letter_context_contract.py tests/test_letter_context_dimension_evidence.py tests/test_letter_context_recovery.py tests/test_letter_context_physical.py`
  passes **132 tests in 101.35 seconds**. This is local test evidence, not a new
  physical validation, provider CI, merge or acceptance result.
- `arrive plan check`, `arrive sync agent-rules --check`, local Markdown links
  for the changed advance/proposal, and `git diff --check` pass.

### 2026-09-10 — owner review closed

- Owner approved the proposal, then requested the next advance after discussing
  generalization limits. GESTURE-004 is complete; this approves the bounded
  contract, not new-letter/triple admission or physical execution.
- Preserve the investigated proposal/report bytes. Separate approval record:
  `stroke_context_v1/contract/contract.json`, SHA-256
  `f438dc9f8d4e9c8464dfe183346117b21c3a5f97da60e34fe5539d402b25fd3b`.
  Contrasting letter families require investigation before word-level expansion.
