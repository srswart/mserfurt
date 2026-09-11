---
advance:
  id: "ADV-SS-GESTURE-005"
  title: "Stroke Context — Versioned Contextual Span and Transition Contract"
  system: "scribesim"
  primary_component: "gesture"
  components: ["gesture","pathguide","handflow","handvalidate","tests"]
  started_at: "2026-09-10T03:54:13.857346+00:00"
  implementation_completed_at: "2026-09-10T04:41:18Z"
  review_time_estimate_minutes: 65
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence:
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/contract/contract.json"
    - "shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/contract/snapshot-001/report.json"
    - "tests/test_stroke_context_contract.py"
  model_usage: []
  status: complete
---

## Objective

Implement the owner-reviewed contextual-span, port-state and transition representation from GESTURE-004 as a separately versioned opt-in contract, with exact context-off preservation.

Follows [TD-018 Addendum D](../../../../docs/tech-direction/TD-018-addendum-d-stroke-context-transitions.md).
Owner-reviewed script-level implementation and local regression checks are
complete. No training, new physical execution, provider CI or
acceptance is claimed. Existing components suffice.

## Behavioral Change

Neighbor-conditioned occurrence derivation can describe entry/body/exit effects and explicit join/retrace/lift intent without silently reinterpreting legacy connected-v1 semantics. Contract support alone grants no geometry, physical or training acceptance.

## Component Impact

- `scripts/stroke_context_contract.py`
- `tests/test_stroke_context_contract.py`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/contract/`

Keep new adapters opt-in and outside frozen core identity scans. Exact paths and
any required migration must be frozen before implementation, not inferred as
permission to change canonical sources or add identity-scanned spec files.

## Dependencies

- [ADV-SS-GESTURE-004](ADV-SS-GESTURE-004.md)

Owner scope/protocol approvals in Addendum D are independent gates, not implied
by a dependency's implementation status. C006's full completion is not a
prerequisite for consuming its specifically pinned P2 mechanical evidence.

## Planned Implementation Tasks

- [x] workflow: preserve all existing uncommitted work; no branches, commits or merges without explicit later authorization.
- [x] tidy: assess narrowly required preparation; do not refactor frozen sources or unrelated components.
- [x] Require the externally pinned investigation and owner-reviewed schema/bounds before accepting any nonidentity request.
- [x] Add failing tests for previous/next/BOS/EOS selectors, canonical span lineage, explicit cross-letter ownership, invalid ports, false smooth reversals, implicit lifts, undeclared body edits and forbidden word/fixture keys.
- [x] Implement an opt-in script-level adapter with immutable canonical programs, bounded derived span edits, explicit body invariants and no recursive expansion or old-cap bypass.
- [x] Represent contact-run identity separately from letter/gesture/action ownership. Under the reviewed narrowed scope, air has no ink owners/overlap allowance; pen-down joins/retraces reject rather than being admitted without finite-width evidence.
- [x] Keep smooth geometry, intentional corners/reversals and lift/landing events distinct, retaining exact-event requirements and fixed action values.
- [x] Prove null canonical compilation, derived geometry, plans and action/timing bundles match the baseline exactly; reject unsupported transitions rather than synthesizing a connector.
- [x] Preserve all frozen source files. If core changes become unavoidable, stop for an explicit version migration and fresh-baseline plan; do not silently refresh source hashes.
- [x] Document schema, invariants, consumer pins and remaining unsupported cells; no physical runs, optimizer calls or production-default activation.

## Bug Fixes

- [x] No frozen behavior fix was needed; preserve earlier fixed clock/contact/measurement behavior and failed artifacts.

## Risk + Rollback

- Risk: A flexible context API could bypass canonical identity, permit uncontrolled body changes or hide contact/ownership defects.
- Rollback: Disable the new opt-in version; retain legacy rejection behavior and all failed contract probes. Never weaken old validators to make the adapter pass.
- Keep fixed tool/action, no-fatigue and no-fitting constraints. Proposed new
  geometry, frames or criteria require prospective approval; no phase-level
  reset of the old time/render debit is permitted.

## Evidence

- [x] Positive and adverse structural tests pass with exact null outputs and unchanged old evidence.
- [x] No transformation reaches execution from an unverified occurrence/transition request; H1–H3 have no execution/planner adapter.
- [x] Owner-reviewed contract scope is frozen independently of later geometry and physical acceptance.
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

### 2026-09-10 — approved bounded contract implemented

- Owner approval closes GESTURE-004. `contract/contract.json` freezes the exact
  investigation/proposal, H0–H3, ±1-degree bounds, 0.04-mm cap and lift-only scope:
  `f438dc9f8d4e9c8464dfe183346117b21c3a5f97da60e34fe5539d402b25fd3b`.
- Template-first preparation: `arrive template render --kind advance --json`.
  No frozen refactor/migration required. Changes remain uncommitted.
- Test-first `tests/test_stroke_context_contract.py` failed collection before
  the adapter existed. Initial implemented suite passed 124 tests; expanded
  non-null/adverse suite passed 81 tests (48 exact-null tests deselected).
- Strict opt-in request validation and occurrence derivation, exact H0 planner
  reuse, explicit lift/air/landing ownership, protected-body exceptions and
  nonidentity geometry-only schema are implemented. Document reconstruction
  shares the derivation algorithm; it is not independent physical measurement.
- Canonical-origin geometry covers only 12 exposed strings. Triples and other
  letter families remain unadmitted. Preserve old cap/validators; investigate
  contrasting letter families before word-level expansion.
- Non-null subdivision splits derived cubics with source parameter ranges; H0
  uses frozen subdivision exactly. No physical execution, raster generation,
  fitting, new numeric acceptance or budget reset.
- Immutable evidence command:
  `.venv/bin/python -m scripts.stroke_context_contract snapshot --contract-sha256 f438dc9f8d4e9c8464dfe183346117b21c3a5f97da60e34fe5539d402b25fd3b`.
  **192** structural documents and **36** exact saved seed-7 null bindings pass.
  nu/uu missing identity traces and placed mu are not relabeled as origin cases.
  Source verification preserves original/recovery manifests and inspection pins.
- Report SHA-256:
  `8af42ea3bcec6ac97546856798f1aec970dd96a6cd59a01a1822ef45761f42e4`.
- Consumer documentation: `shared/training/konrad_hand_recovery/stroke_gestures_v2/stroke_context_v1/contract/README.md`.
- Final local regression command:
  `.venv/bin/python -m pytest -q tests/test_stroke_context_contract.py tests/test_stroke_context_audit.py tests/test_letter_context_contract.py tests/test_letter_context_dimension_evidence.py tests/test_letter_context_recovery.py tests/test_letter_context_physical.py`
  passes **261 tests in 223.39 seconds**, including all 129 new contract tests.
- Current adapter/test/report hashes match. `arrive plan check`,
  `arrive sync agent-rules --check`, changed local links and `git diff --check`
  pass. Plan uses `done`, advance frontmatter uses `complete`; an initial plan
  enum mismatch was corrected before final validation.
- This is contract implementation completion, not provider CI, merge, physical
  validity or appearance acceptance. CURRICULUM-016 remains next and unstarted.
