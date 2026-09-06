---
advance:
  id: "ADV-SS-EVOFIT-007"
  title: "Stroke Language — Shared Primitives and Layered Compilation"
  system: "scribesim"
  primary_component: "evo"
  components: ["evo","curriculum","pathguide","handvalidate","tests"]
  started_at: "2026-09-06T04:10:57Z"
  implementation_completed_at: "2026-09-06T04:36:46Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "shared/training/konrad_hand_recovery/stroke_language_v1/language/S0.json"]
  model_usage: []
  status: complete
---

## Objective

Define an explicit shared stroke language, not a character catalog whose independent curves are merely called strokes.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
Compiler implementation and synthetic S0 exercises are complete. Real handwriting, learned letter recipes and owner acceptance are not claimed.

## Behavioral Change

Define an explicit shared stroke language, not a character catalog whose independent curves are merely called strokes. The new curriculum must produce visible layer-specific
learning and transfer evidence before downstream acceptance.

## Component Impact

- `scribesim/evofit/stroke_language.py (new schema, validation and compiler)`
- `scribesim/evofit/repertoire.py and scribesim/pathguide/repertoire.py (explicit adapters)`
- `tests/test_stroke_language.py (new)`

Use tracked modules and scoped test selectors; clean-checkout imports are required.
No production renderer or component stage changes.

## Dependencies

- [ADV-SS-EVOFIT-005](ADV-SS-EVOFIT-005.md)

Completion is not acceptance. Synthetic scaffolding may execute with explicitly
unaccepted inputs. Reference-derived fitting requires live G0, and real layer
acceptance requires the matching accepted lower-layer checkpoint. Do not import
an older curriculum's pass summary as evidence of shared-stroke learning.

## Planned Implementation Tasks

- [x] branch: confirm authorization before branches or commits.
- [x] tidy: assess narrowly required preparation; preserve unrelated work.
- [x] test: commit failing behavioral tests before feature implementation when commits are authorized.
- [x] feat/evaluate: Define versioned StrokePrimitive, LetterRecipe, WordProgram and LineProgram records with immutable IDs, parameter units/bounds, source provenance and uncertainty. Keep source recipes separate from derived compiled paths.
- [x] feat/evaluate: A primitive owns shared geometry and entry/exit direction, contact, curvature and legal transform constraints. A letter references ordered primitive IDs with bounded placement/attachment parameters and explicit lifts/crossings; prohibit per-letter free cubic replacements.
- [x] feat/evaluate: Implement deterministic compilation and expansion to the existing nominal/neutral guided path. Carry primitive, occurrence, letter, word and line ownership plus shared ligature spans through sampling and actual trajectory attribution.
- [x] feat/evaluate: Separate intra-letter assembly, adjacent-letter rules and inter-word boundary rules. Use finite declared context features and bounded overlays; never arbitrary per-word geometry or target pixels at generation time.
- [x] feat/evaluate: Validate graph acyclicity, inventory, ports, transforms, exact text mapping and undeclared joins before rendering. Introduce a schema-versioned model path; existing schema-2 catalog models remain explicit diagnostic baselines, not silently promoted stroke-language models.
- [x] feat/evaluate: Freeze a starter inventory of at most eight primitive families, 12 lowercase logical characters, two recipes per character and four primitive occurrences per recipe. Increase a bound only through a diagnosed revision. Synthetic programs validate language mechanics without claiming real-source admission.
- [x] evidence: record red/green commands, actual budget use, hashes, scope and outcome before marking completion.

## Validation Gates

- [x] S0: invalid/missing primitive references, cycles, illegal ports, unbounded transforms and unmatched text spans are rejected.
- [x] Changing one shared primitive propagates to every referencing letter/word and invalidates derived hashes/caches; canonical recipes are not mutated by context.
- [x] Fresh-process compile/render replay and exact stroke-to-text ownership pass, including lifts and explicit shared spans. Legacy readers still work only through their declared model path.
- [x] Emit readable recipe listings and color-by-primitive decomposition sheets; there is no claim of learned handwriting from a seeded program.

## Invariant Impact

Exact text, source uncertainty, split isolation, shared-parameter lineage,
deterministic compilation and actual trajectory ownership remain mandatory.
Synthetic mechanics, real-source fitting and human appearance acceptance are
separate. Layer gates S0–S4 supplement, not replace, G0–G4.

## Risk + Rollback

A layer can disguise copied character geometry or memorized words as learning.
Reject unrestricted residuals and per-instance lookup; retain frozen lower-layer
checkpoints, ablations and failed evidence. Revert only the new opt-in model,
not historical snapshots or production defaults. Review estimate: 40 minutes.

## Evidence

- [x] Frozen fixtures, splits, constraints, objective/limits and model/code identities.
- [x] Before/after practice sheets, decomposition proofs and transfer results.
- [x] Replay and neutral direct/sampled/actual comparisons; real review only when performed.
- [x] `arrive plan check`, `git diff --check`, focused tests and clean-checkout validation.
- [x] Before authorized merge, run `arrive pr check --strict --json`; record installed-tool limitations separately from provider CI.

### Executed outcome

- Red commits 31317b8 and 43b1302 precede the implementation. No preparatory refactor or second controller was required. The guided/state/compiler regression set passes 28 tests.
- Implemented versioned shared primitives, bounded letter references, exact WordProgram/LineProgram compilation, layered rule overlays, ports/contact/crossing checks, sample ownership, fresh-process replay and strict model-bound bundle loading.
- Six handcrafted primitive families and two demonstration recipes (i/u) prove structure and shared-edit propagation, not learned letter construction. The primitive curriculum is the separate next Advance.
- Actual neutral trajectories retain primitive/recipe/word/line identity; fixed ink, pressure and speed only. Existing schema-2 repertoire and legacy guide readers remain unchanged and do not silently accept the new schema.
- Synthetic decomposition/nominal/actual examples are retained under stroke_language_v1/language. S0 is a compiler-mechanics pass, not G1/G2 or historical handwriting acceptance.
- Plan/diff checks pass. Strict PR check retains the installed three-part-ID parser limitation; no provider CI or owner approval occurred.

## Bug Fixes

None implemented. This planned Advance addresses the missing layered-learning
contract, not the later ink or fatigue defects.

## Changes Made

### 2026-09-06 — plan: Adopt shared-stroke layered learning

- Added to Pass 15 phase `td018-strokes`.
- Deferred expressive work until strokes, letters and both context levels are proven.

## Check for Understanding

1. What changes are learned at this layer, and which lower-layer parameters stay frozen?
2. Which visible transfer test prevents this layer from merely reproducing supplied shapes?
