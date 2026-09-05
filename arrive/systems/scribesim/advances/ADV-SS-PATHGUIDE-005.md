---
advance:
  id: "ADV-SS-PATHGUIDE-005"
  title: "Konrad Guided Bridge — Preserve Forms, Contact and Text Ownership"
  system: "scribesim"
  primary_component: "pathguide"
  components: ["pathguide", "handflow", "handvalidate", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 30
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

Convert a G1-passing repertoire into DensePathGuide inputs without losing contextual choices, stroke structure, physical scale or text ownership; establish G2.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
This is a planned outcome record. The timestamp records drafting; implementation
has not started and no execution, CI or owner approval is claimed.

## Behavioral Change

After implementation: The selected WordPlan is sampled into physical trajectories with explicit lifts and an ownership sidecar. Direct nominal, sampled playback and neutral guided output can be compared independently.

## Component Impact

Primary component: `pathguide`. Impacted components:
`pathguide`, `handflow`, `handvalidate`, `tests`.

Planned paths (new modules and commands are not available yet):

- scribesim/pathguide/repertoire.py (new adapter and ownership sidecar)
- scribesim/handflow/planning.py and scribesim/handvalidate/specimen.py (bridge bench)
- tests/test_repertoire_pathguide.py (new); focused ARRIVE test selector coverage

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-HANDVALIDATE-008](ADV-SS-HANDVALIDATE-008.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [ ] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [ ] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [ ] test: establish failing behavioral tests for the contracts below before implementation.
- [ ] feat/evaluate: Require a matching G1-pass model/configuration record before candidate integration.
- [ ] feat/evaluate: Sample cubics by arc length in physical millimetres, preserving baseline orientation, nib/pressure priors, entry/exit tangents and explicit air travel.
- [ ] feat/evaluate: Resolve contextual forms before composing the dense word guide; preserve form/stroke/text-span ownership in a versioned sidecar.
- [ ] feat/evaluate: Keep existing DensePathGuide loading compatible and reject adapters that drop unknown metadata required for exact attribution.
- [ ] feat/evaluate: Compare nominal sweep, sampled playback and actual neutral-controller trajectory at matching scale, nib and development-frozen tolerances.
- [ ] feat/evaluate: Emit G2 metrics and panels; retain guide-aligned trajectories solely for diagnostics.
- [ ] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] The exact selected forms, contact schedule, intended intersections and logical spans survive conversion.
- [ ] Direct-to-sampled and nominal-to-neutral-guided deviations remain within predeclared contour/width/corridor bounds.
- [ ] The evaluated image is rendered from actual controller trajectory, not aligned or substituted guide geometry.
- [ ] G1 coverage and appearance remain acceptable; missing bridge evidence blocks G2.

Focused validation: Use asymmetric orientation fixtures, contextual variants, lifts, loops, shared ligature attribution and round-trip physical units. Inject an aligned-versus-actual discrepancy and verify the bench detects actual output degradation.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: A converter can make a good hand fail through coordinate or contact errors while aligned diagnostics conceal the loss. Compare each stage separately and keep actual output authoritative.

Rollback: Remove the opt-in repertoire adapter selection; keep existing guide catalogs and the accepted nominal specimen available.

Review estimate: 30 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Pending implementation; none of these evidence types is claimed as completed.

- [ ] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [ ] `tdd:red-green`: capture focused failing and passing test commands and results.
- [ ] nominal/playback/neutral-guided comparison panels
- [ ] ownership sidecar, conversion invariants and G2 report
- [ ] sampling convergence and coordinate-transform regression results
- [ ] Record local integration checks separately from provider CI and owner review.
- [ ] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

None implemented in this planning change. Record scoped defects and their
regressions here during execution; do not imply unrelated renderer defects are fixed.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Why must allograph selection precede conversion to a word guide?
2. Which trajectory is allowed to paint the reviewed image, and why?

