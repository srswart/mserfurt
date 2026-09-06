---
advance:
  id: "ADV-SS-HANDFLOW-009"
  title: "Konrad Ink Repair — Separate Contact Pressure from Optical Ink Load"
  system: "scribesim"
  primary_component: "handflow"
  components: ["handflow","ink","handvalidate","tests"]
  started_at: "2026-09-06T03:57:59Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
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

Diagnose and revise the opt-in ink behavior that erased much of the synthetic three-line specimen while preserving deterministic, distance-owned consumption and neutral geometry.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
This is a planned outcome record. The timestamp records drafting only;
implementation, experimental execution, CI and owner approval are not claimed.

**Deferred:** Not part of the immediate stroke-language curriculum. Start only
after real S0–S4/G1/G2 acceptance for the layered neutral candidate and an
explicit later owner go-ahead. Synthetic diagnostics in this record do not
make it a competing immediate training priority. Fatigue remains separate.

## Behavioral Change

After implementation: Mechanical nib pressure, reservoir mass and optical deposition have distinct explicit contracts. Bounded ink variation remains visible without accidental pressure/width collapse; genuinely empty ink still cannot paint a normal mark.

## Component Impact

Primary component: `handflow`. Planned paths and artifacts:

- `scribesim/handflow/controls.py, controller.py, model.py and execution.py`
- `scribesim/handvalidate/bridge.py and expressive.py (actual-trajectory rendering and audits)`
- `tests/test_handflow_repertoire_state.py and tests/test_handvalidate_expressive.py`
- `shared/training/konrad_hand_recovery/ink_repair_v1/ (new diagnostics)`

No component stage changes. Add narrow ownership/test selectors only if required.

## Dependencies

- [ADV-SS-HANDFLOW-008](ADV-SS-HANDFLOW-008.md)
- [ADV-SS-HANDVALIDATE-009](ADV-SS-HANDVALIDATE-009.md)
- [ADV-SS-HANDVALIDATE-011](ADV-SS-HANDVALIDATE-011.md): real layered neutral acceptance before activation.

Dependencies order implementation; live identity-bound gate records separately
authorize real candidate execution. Completed blocked experiments do not pass gates.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before creating a branch or committing.
- [ ] tidy: assess preparatory changes; avoid unrelated refactoring.
- [ ] test: establish and record failing behavioral tests before implementation.
- [ ] feat/evaluate: Preserve the frozen v1 failure and trace reservoir, pressure, nib width and painted opacity across full proof lines and dips. Test the current multiplication of mechanical pressure by normalized reservoir as a causal hypothesis, not a proven sole cause.
- [ ] feat/evaluate: Define bounded, unit-labeled consumption/deposition behavior with exactly one state owner and one contact-distance consumption point. Separate reservoir-driven optical changes from intended mechanical pressure modulation; carry any optical field through saved actual trajectories and render audits.
- [ ] feat/evaluate: Retain zero consumption during air/stationary steps, finite nonnegative reservoirs and explicit refills. An empty reservoir must produce no ink; do not clamp opacity to hide depletion or reset ink at layout boundaries.
- [ ] feat/evaluate: Revise boundary dip settings using explicit load/depletion diagnostics. If an upcoming word requires a conservative reserve estimate, use its declared guide and configured bounds, not reference pixels. Record refill decisions; reject unsupported long-word demand or expose dry-out honestly rather than inserting a hidden midword dip.
- [ ] feat/evaluate: Freeze at most 12 candidate setting bundles before synthetic trials. Evaluate seeds 7/19/41 with independent replay (at most 72 sessions), including complete three-line proofs and bounded stress fixtures. Select on declared development diagnostics; preserve all attempts and stop after one diagnosed revision.
- [ ] feat/evaluate: Keep ink visibly active: report load/opacity evolution, consumption and dip events. Disabling ink, setting consumption to zero or matching neutral exactly is not an ink-repair success.
- [ ] feat/evaluate: Leave legacy controller/profile defaults unchanged. Preserve exact neutral behavior or document the change and require fresh neutral G2 evidence; extend artifact schema/version checks if optical state is added.
- [ ] evidence: record red/green commands, artifact identities and the actual outcome before marking implementation complete.

## Validation Gates

- [ ] Known-length contact, zero-length/air travel, empty reservoir, full refill, long word, line return, repeated lines and sitting break tests verify conservation and no hidden state resets.
- [ ] Pressure-only geometry is independent of reservoir load; optical deposition is finite/bounded and trace-derived, with zero deposition at empty load.
- [ ] Plan partitioning does not double-consume ink; timestep refinement has a predeclared convergence tolerance and fresh-process replay is exact for a fixed timestep.
- [ ] Neutral remains equivalent; active ink and combined settings must meet the existing synthetic image bound 0.35, corridor/angle/pressure limits and meaningful activation checks. Numeric safety is not human appearance approval.

## Invariant Impact

Preserve exact text, source provenance, native geometry, leakage-resistant
splits, deterministic replay and the separation of implementation completion
from model acceptance. Production defaults and prior evidence remain unchanged.

## Risk + Rollback

A cosmetic opacity floor or aggressive refill can conceal a broken mass/state model. Retain explicit depletion/empty behavior, evaluate full lines and roll back to neutral with ink disabled when unsafe.

Review estimate: 40 minutes, not a measured reviewability score.

## Evidence

Planned evidence: Causal old/new trace comparison, frozen settings and bounded search ledger, conservation and dip diagnostics, actual rendered proofs, replay hashes and candidate configuration. Final real/synthetic acceptance remains HANDVALIDATE-012.

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

1. Which state describes mechanical pressure, and which determines optical deposition?
2. How do the tests distinguish safe active ink from a control that was silently disabled?
