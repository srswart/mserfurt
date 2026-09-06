---
advance:
  id: "ADV-SS-HANDVALIDATE-012"
  title: "Konrad Repair Evaluation — Ink Sensitivity and G3 Readiness Decision"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","handflow","tests"]
  started_at: "2026-09-06T03:57:59Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 35
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

Independently evaluate the revised ink configuration, then decide whether the reference-grounded candidate can proceed to opt-in folios without weakening the existing evidence boundary.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
This is a planned outcome record. The timestamp records drafting only;
implementation, experimental execution, CI and owner approval are not claimed.

**Deferred:** Not part of the immediate stroke-language curriculum. Start only
after real S0–S4/G1/G2 acceptance for the layered neutral candidate and an
explicit later owner go-ahead. Synthetic diagnostics in this record do not
make it a competing immediate training priority. Fatigue remains separate.

## Behavioral Change

After implementation: A frozen, replayable repair matrix reports neutral/ink/pressure/angle/rhythm/combined behavior and gives an explicit real G3 pass, fail or blocked result. Failed historical artifacts remain available for comparison.

## Component Impact

Primary component: `handvalidate`. Planned paths and artifacts:

- `scribesim/handvalidate/expressive.py and bridge.py`
- `tests/test_handvalidate_expressive.py`
- `shared/training/konrad_hand_recovery/expressive_specimen_v2/ (new immutable evaluation bundle)`
- `docs/tech-direction/TD-018-reference-grounded-hand-recovery.md and arrive/implementation-plan.yaml (outcome records)`

No component stage changes. Add narrow ownership/test selectors only if required.

## Dependencies

- [ADV-SS-HANDVALIDATE-011](ADV-SS-HANDVALIDATE-011.md)
- [ADV-SS-HANDFLOW-009](ADV-SS-HANDFLOW-009.md)

Dependencies order implementation; live identity-bound gate records separately
authorize real candidate execution. Completed blocked experiments do not pass gates.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before creating a branch or committing.
- [ ] tidy: assess preparatory changes; avoid unrelated refactoring.
- [ ] test: establish and record failing behavioral tests before implementation.
- [ ] feat/evaluate: Freeze the selected ink settings, code/model identities, unchanged proof texts, seeds 7/19/41, timestep, DPI and limits before evaluation. Keep v1 failure artifacts unchanged; do not rescore them as if produced by revised code.
- [ ] feat/evaluate: Run all six configurations and three seeds with two fresh workers (36 sessions). Compare unchanged nominal/reference panels with actual revised trajectories; include matched old/new neutral, ink and combined overview sheets.
- [ ] feat/evaluate: Retain the synthetic image limit 0.35 and existing corridor/angle/pressure bounds. Audit optical state-to-pixel agreement as well as distance, consumed/refilled ink, continuity, exact text, replay and measurable activation.
- [ ] feat/evaluate: Keep tuning results separate from acceptance: the familiar three-line proofs are regression evidence, not an unseen generalization test. Add a predeclared stress set covering multiple dips, low/empty load, long words, returns and sitting breaks without test-reference pixels.
- [ ] feat/evaluate: After the deferred phase is explicitly activated, synthetic regression evaluation remains labeled unaccepted engineering evidence. Real trials require the accepted layered stroke-language candidate, current matching G0/G1/G2 for revised code/configuration, calibrated frozen limits and genuine G3 owner review. Catalog-prior replays cannot substitute for the learned candidate.
- [ ] feat/evaluate: Publish a concise sample index and stop/revise/proceed report. If either ink mode remains unsafe, retain neutral and disable that mode; do not proceed to folios or repeat tuning without a newly scoped budget.
- [ ] feat/evaluate: Update each Advance's implementation outcome separately from runtime gate acceptance. RENDER-006 remains blocked unless the actual candidate passes G3; no default renderer switch.
- [ ] evidence: record red/green commands, artifact identities and the actual outcome before marking implementation complete.

## Validation Gates

- [ ] All 18 configuration/seed rows replay from frozen inputs with actual image/state audits; missing rows, inactive claimed controls, stale hashes or altered reviews cannot pass.
- [ ] Safe synthetic behavior does not generate a real G3 pass; missing upstream evidence or owner review is explicitly blocked.
- [ ] Real G3 requires source-grounded nominal quality plus matching guided and expressive acceptance, not merely similarity to an unaccepted font-like prior.
- [ ] Evidence includes the negative v1 comparison and all repaired outcomes; reviewers can locate the three-line samples without running the pipeline.

## Invariant Impact

Preserve exact text, source provenance, native geometry, leakage-resistant
splits, deterministic replay and the separation of implementation completion
from model acceptance. Production defaults and prior evidence remain unchanged.

## Risk + Rollback

Overfitting settings to familiar proof lines can look like progress without recovering the hand. Preserve independent reference/reading gates and keep synthetic regression results clearly labeled; neutral remains the fallback.

Review estimate: 35 minutes, not a measured reviewability score.

## Evidence

Planned evidence: Frozen matrix, stress contracts, first/replay artifacts, state audits, v1/v2 comparison panels, G3 record and owner review only when performed; a readable sample index and explicit folio readiness decision.

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

- Moved to phase `td018-expressive-later`; supersedes the earlier `td018-repair` ordering.
- Strokes, letter recipes, within-word context and inter-word context are separate learned layers.
- Ink, fatigue and other expressive work are deferred; no implementation or acceptance is claimed.

## Check for Understanding

1. Why can all synthetic ink checks pass while real G3 remains blocked?
2. What exact evidence authorizes folio execution after this phase?
