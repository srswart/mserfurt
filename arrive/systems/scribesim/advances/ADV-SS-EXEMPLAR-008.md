---
advance:
  id: "ADV-SS-EXEMPLAR-008"
  title: "Konrad Admission Repair — Verified Mappings and Native Line Masks"
  system: "scribesim"
  primary_component: "refextract"
  components: ["refextract","evo","handvalidate","tests"]
  started_at: "2026-09-06T03:57:59Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 45
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Repair the specific exclusions in the v2 reference observations without turning machine guesses into verified labels or using locked-test pixels for development.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
This is a planned outcome record. The timestamp records drafting only;
implementation, experimental execution, CI and owner approval are not claimed.

## Behavioral Change

After implementation: A new immutable corpus carries auditable readings, exact visible-form mappings and improved native masks. Each candidate is admitted only by recomputed evidence; unresolved words remain quarantined.

## Component Impact

Primary component: `refextract`. Planned paths and artifacts:

- `scribesim/evofit/reference_dataset.py`
- `tests/test_reference_dataset.py`
- `reference/konrad_hand_recovery_v3/ (new immutable corpus and review/import artifacts)`
- `.gitignore (narrow v3 exception only)`

No component stage changes. Add narrow ownership/test selectors only if required.

## Dependencies

- [ADV-SS-EXEMPLAR-007](ADV-SS-EXEMPLAR-007.md)
- [ADV-SS-HANDVALIDATE-009](ADV-SS-HANDVALIDATE-009.md)

Dependencies order implementation; live identity-bound gate records separately
authorize real candidate execution. Completed blocked experiments do not pass gates.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before creating a branch or committing.
- [ ] tidy: assess preparatory changes; avoid unrelated refactoring.
- [ ] test: establish and record failing behavioral tests before implementation.
- [ ] feat/evaluate: Freeze v2 lineage and report overlapping exclusion reasons per non-test candidate. Begin with the seven legacy crops excluded only for exact mapping; do not assume their readings are verified.
- [ ] feat/evaluate: Provide an auditable review/import path for logical text, visible forms, abbreviation/ligature spans, uncertainty, reviewer or machine identity and source coordinates. Reject incomplete mappings, unverifiable approval assertions and changes to reserved split membership.
- [ ] feat/evaluate: Improve line assignment using strong-ink seeds and local line evidence; preserve ambiguous touching strokes as unknown. Do not whiten unknown ink for fitting or reduce the admission thresholds simply to increase counts.
- [ ] feat/evaluate: Preserve native source bytes, reversible crop coordinates, aspect ratio and mask semantics. Record extraction configuration, code identity and every annotation or mask intervention.
- [ ] feat/evaluate: Limit the first repair pass to the 41 training and 11 development reservations. Keep the eight locked-test reservations sealed and preserve source-line/overlap grouping; previously inspected data never becomes test data.
- [ ] feat/evaluate: Write v3 to a new directory with before/after non-test contact sheets, exclusion deltas, coverage and independent instance/context counts. Retain v2 unchanged.
- [ ] feat/evaluate: Stop after one diagnosed extraction revision and one non-test annotation pass. If support remains inadequate, report the missing symbols/contexts and propose a separately approved source-acquisition or annotation budget; do not silently expand scope.
- [ ] feat/evaluate: Calibrate source losses using independent admitted train/development repeats and negative controls; obtain genuine target review bound to frozen source/benchmark identities. Recompute G0 before any reference-derived stroke fitting. Missing support, calibration or review remains blocked; this must not wait for the downstream layer evaluation.
- [ ] feat/evaluate: Record primitive/letter support and uncertain stroke assignments without treating repeated slices of a single word as independent observations. Freeze a supported starter inventory; source images alone do not verify pen order or force.
- [ ] evidence: record red/green commands, artifact identities and the actual outcome before marking implementation complete.

## Validation Gates

- [ ] Regression fixtures cover adjacent-line contamination, pale connected strokes, genuine touching ambiguity, empty masks and exact multi-character visible mappings.
- [ ] Tampered hashes, invented review status, incomplete mappings and split leakage are rejected; artifact reconstruction recomputes admission.
- [ ] At least 30 usable observations and existing per-symbol independent support requirements are measured, not inferred from candidate count. Failure produces a blocked corpus report, not a lowered target.
- [ ] No locked-test image or statistic enters repair previews, threshold selection or source calibration.

## Invariant Impact

Preserve exact text, source provenance, native geometry, leakage-resistant
splits, deterministic replay and the separation of implementation completion
from model acceptance. Production defaults and prior evidence remain unchanged.

## Risk + Rollback

Overconfident readings or masks can poison the recovered hand. Preserve uncertainty, isolate test data and retain v2 as the reproducible rollback dataset.

Review estimate: 45 minutes, not a measured reviewability score.

## Evidence

Planned evidence: Versioned non-test review ledger; before/after masks and contact sheets; admitted/excluded counts with reasons; native source, split and intervention hashes. Initial live G0 readiness belongs here before reference-grounded stroke fitting; HANDVALIDATE-011 later revalidates it alongside the layer and nominal/neutral gates.

- [ ] Record focused tests and reproducibility checks.
- [ ] Run `arrive plan check` and `git diff --check`.
- [ ] Before an authorized merge, run `arrive pr check --strict --json` and record any installed-tool limitation separately from provider CI.
- [ ] Do not claim provider CI or human approval without actual evidence.

## Bug Fixes

No implementation changes yet; this record scopes the diagnosed repair/evaluation.

## Changes Made

### 2026-09-06 — plan: Scope the post-guided repair

- Added to Pass 15, phase `td018-repair`, ahead of folio work.
- Existing benchmark/nominal/guided completion records and negative evidence remain unchanged.

### 2026-09-06 — revision: Shared stroke-language curriculum first

- Moved to phase `td018-strokes`; supersedes the earlier `td018-repair` ordering.
- Strokes, letter recipes, within-word context and inter-word context are separate learned layers.
- Ink, fatigue and other expressive work are deferred; no implementation or acceptance is claimed.

## Check for Understanding

1. What evidence changes a mapping from a machine hypothesis into an admissible observation?
2. How can an improved mask remain uncertain without treating unknown pixels as white training targets?
