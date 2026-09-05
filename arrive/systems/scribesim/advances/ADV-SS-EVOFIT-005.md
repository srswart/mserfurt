---
advance:
  id: "ADV-SS-EVOFIT-005"
  title: "Konrad Stroke Repertoire — Alternative Forms and Exact Word Plans"
  system: "scribesim"
  primary_component: "evo"
  components: ["evo", "tests"]
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

Implement the shared HandRepertoire and WordPlan contracts that can represent alternative stroke structures, contextual allographs and explicit joins without storing a separate drawing for each word.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
This is a planned outcome record. The timestamp records drafting; implementation
has not started and no execution, CI or owner approval is claimed.

## Behavioral Change

After implementation: The nominal renderer composes new text from stable form IDs, ordered contact chains, air transitions and exact logical spans. Missing forms fail visibly, and structural alternatives can differ in loops, branches and lifts.

## Component Impact

Primary component: `evo`. Impacted components:
`evo`, `tests`.

Planned paths (new modules and commands are not available yet):

- scribesim/evofit/repertoire.py (new)
- scribesim/evo/genome.py and scribesim/evo/allograph.py (reuse or minimal compatible adaptation)
- tests/test_hand_repertoire.py (new); focused ARRIVE test selector coverage

No component stage is changed. Add narrow ownership selectors for new files
where the current selectors do not cover them.

## Dependencies

- [ADV-SS-EXEMPLAR-007](ADV-SS-EXEMPLAR-007.md)

Plan completion and model acceptance are separate: dependent candidate execution
requires the applicable TD-018 gate record to pass for the same model and
configuration. A completed unsuccessful experiment does not satisfy that gate.

## Planned Implementation Tasks

- [ ] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [ ] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [ ] test: establish failing behavioral tests for the contracts below before implementation.
- [ ] feat/evaluate: Define versioned repertoire/form/word-plan schemas with x-height coordinates, landmarks, tangents, topology, provenance and bounds.
- [ ] feat/evaluate: Add explicit logical-to-visible mappings, per-occurrence ownership and legal context/transition choices, including declared multi-character spans.
- [ ] feat/evaluate: Seed catalog and existing allograph families as unaccepted candidate structures; allow different chain counts and permitted intersections.
- [ ] feat/evaluate: Implement exact composition and direct broad-edge nominal playback with stable local RNG/configuration hashes and complete render-cache keys.
- [ ] feat/evaluate: Validate proposed limits of three forms per symbol, eight contact chains and 32 cubics per form; expose limit-hit diagnostics rather than silent truncation.
- [ ] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [ ] Round trips preserve topology, pen lifts, visible-symbol identity, units and ownership.
- [ ] Unseen strings render using shared form parameters and text-only selection; absent symbols and undeclared normalization are errors.
- [ ] A looped and an open form can represent the same logical character without being collapsed to one fixed topology.
- [ ] Changing one shared form updates all its occurrences; no per-word raster or unconstrained drawing enters the learned model.

Focused validation: Exercise alternate topology, explicit long-s mapping, unsupported diacritics, shared ligature ownership, intentional crossings, contact-to-air transitions and unseen composition. Fresh-process nominal renders must match for fixed inputs.

## Invariant Impact

Preserve exact requested text, declared backend/asset identity, source provenance,
deterministic replay and separation of model promotion from implementation
completion. Production defaults remain unchanged. Record any contract deviation
explicitly before considering the candidate promotable.

## Risk + Rollback

Risk: A flexible schema can introduce wrong symbols or accidental per-word memorization. Enforce exact spans, shared IDs and topology validation at load and composition boundaries.

Rollback: Keep repertoire v2 opt-in and continue using the existing v1 shared-hand representation or catalog assets.

Review estimate: 30 minutes. Reassess against the actual diff and split
work if necessary; do not treat this estimate as a measured reviewability score.

## Evidence

Pending implementation; none of these evidence types is claimed as completed.

- [ ] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [ ] `tdd:red-green`: capture focused failing and passing test commands and results.
- [ ] schema examples and replayable repertoire fixtures
- [ ] nominal alternative-form and novel-word panels
- [ ] coverage/ownership reports and deterministic serialization tests
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

1. Which representation change allows a missing loop or lift to be explored?
2. How are a logical character, its visible allograph and an occurrence in a word distinguished?

