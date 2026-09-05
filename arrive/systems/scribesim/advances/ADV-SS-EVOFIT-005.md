---
advance:
  id: "ADV-SS-EVOFIT-005"
  title: "Konrad Stroke Repertoire — Alternative Forms and Exact Word Plans"
  system: "scribesim"
  primary_component: "evo"
  components: ["evo", "tests"]
  started_at: "2026-09-05T17:30:14Z"
  implementation_completed_at: "2026-09-05T18:33:33Z"
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence:
    - "shared/training/konrad_hand_recovery/repertoire_v2/ownership.json"
  model_usage: []
  status: complete
---

## Objective

Implement the shared HandRepertoire and WordPlan contracts that can represent alternative stroke structures, contextual allographs and explicit joins without storing a separate drawing for each word.

Follows [TD-018 — Reference-Grounded Recovery of Konrad's Hand](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md).
Implementation is complete. These are unaccepted catalog/synthetic priors, not a recovered Konrad hand. G0 remains blocked; production defaults are unchanged.

## Behavioral Change

After implementation: The nominal renderer composes new text from stable form IDs, ordered contact chains, air transitions and exact logical spans. Missing forms fail visibly, and structural alternatives can differ in loops, branches and lifts.

## Component Impact

Primary component: `evo`. Impacted components:
`evo`, `tests`.

Implemented paths (existing genome/allograph modules are reused without modification):

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

- [x] branch: confirm the existing working branch; do not create a branch or commit without explicit authorization.
- [x] tidy: assess preparatory refactoring; perform only what the implementation requires and record when none is necessary.
- [x] test: establish failing behavioral tests for the contracts below before implementation.
- [x] feat/evaluate: Define versioned repertoire/form/word-plan schemas with x-height coordinates, landmarks, tangents, topology, provenance and bounds.
- [x] feat/evaluate: Add explicit logical-to-visible mappings, per-occurrence ownership and legal context/transition choices, including declared multi-character spans.
- [x] feat/evaluate: Seed catalog and existing allograph families as unaccepted candidate structures; allow different chain counts and permitted intersections.
- [x] feat/evaluate: Implement exact composition and direct broad-edge nominal playback with stable local RNG/configuration hashes and complete render-cache keys.
- [x] feat/evaluate: Validate proposed limits of three forms per symbol, eight contact chains and 32 cubics per form; expose limit-hit diagnostics rather than silent truncation.
- [x] evidence: record actual red/green commands, outputs and artifact identities; update the outcome and implementation timestamp only when work is complete.

## Validation Gates

- [x] Round trips preserve topology, pen lifts, visible-symbol identity, units and ownership.
- [x] Unseen strings render using shared form parameters and text-only selection; absent symbols and undeclared normalization are errors.
- [x] A looped and an open form can represent the same logical character without being collapsed to one fixed topology.
- [x] Changing one shared form updates all its occurrences; no per-word raster or unconstrained drawing enters the learned model.

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

Local implementation evidence follows; provider CI and owner review have not occurred.

- [x] `tidy:preparatory`: record the actual preparation or why it was unnecessary.
- [x] `tdd:red-green`: capture focused failing and passing test commands and results.
- [x] schema examples and replayable repertoire fixtures
- [x] nominal alternative-form and novel-word panels
- [x] coverage/ownership reports and deterministic serialization tests
- [x] Record local integration checks separately from provider CI and owner review.
- [x] Before merge, run `arrive pr check --strict --json`; record provider metadata only for an actual CI run.

## Bug Fixes

Exact composition rejects unsupported Unicode rather than falling back to another letter. No unrelated production renderer changes.

### Actual execution

- Tidy assessment: no preparatory refactor necessary; opt-in module reuses existing cubic and broad-edge primitives.
- Red: `.venv/bin/python -m pytest tests/test_hand_repertoire.py -q` failed collection with missing repertoire module; committed as `79b9704` before implementation.
- Green: the same focused command passed 13 tests; combined repertoire, dataset, specimen, word-recovery and nominal-review suite passed 51 tests in 10.68 seconds.
- Evidence: `shared/training/konrad_hand_recovery/repertoire_v2/` contains serialized seed/alternative topology, exact ownership plans, code-aware cache keys and equal-scale panels. The novel seed panel was visually inspected; its font-like prior is explicitly not accepted as historical handwriting.
- Representation uses one to three-symbol spans (ligatures explicitly declared), at most three forms per span, eight continuous contact chains and 32 cubics; every gap between chains is an air transition. Optional bounded inter-form contact joins are declared separately. No word-specific geometry or raster fields are accepted.
- Text-only bounded dynamic programming uses stable content-hash tie breaks, not process hashes or global RNG. The catalog allograph families are structural priors, not verified visible readings.
- `arrive plan check` passed. `arrive pr check --strict --json --title "Complete reusable repertoire [ADV-SS-EVOFIT-005]"` ran but failed: installed ID parser returned no IDs for the repository’s three-part identifier. No provider CI or human approval is claimed.

## Changes Made

### 2026-09-05 — plan: Define the TD-018 implementation and evaluation outcome

- Drafted this Advance and linked it into Pass 15.
- Implementation, experimental execution and promotion remain pending.

## Check for Understanding

1. Which representation change allows a missing loop or lift to be explored?
2. How are a logical character, its visible allograph and an occurrence in a word distinguished?
