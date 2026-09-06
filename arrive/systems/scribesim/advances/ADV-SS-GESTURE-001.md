---
advance:
  id: "ADV-SS-GESTURE-001"
  title: "Stroke Gestures — Versioned Composition, Actions and Legacy Migration"
  system: "scribesim"
  primary_component: "gesture"
  components: ["gesture","evo","pathguide","handvalidate","tests"]
  started_at: "2026-09-06T12:03:29Z"
  implementation_completed_at: "2026-09-06T13:15:31Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api","migration"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration", "shared/training/konrad_hand_recovery/stroke_gestures_v2/language/run-001/report.json"]
  model_usage: []
  status: complete
---

## Objective

Introduce first-class continuous gesture and intentional action-profile identities without duplicating primitive geometry or reinterpreting frozen v1 bundles.

**Work kind:** Implementation. Follows [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md), including its [delivery and budget contract](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md#10-planned-advances-and-delivery-contract).
Compiler implementation and clean-checkout replay complete; no learned gesture,
dynamic action execution or real-hand acceptance is claimed.

## Behavioral Change

After this Advance: An opt-in versioned compiler expands primitive → gesture → letter → word → line ownership. Continuous multi-segment strokes retain contact, while lifts and overlapping finishing gestures remain explicit.

## Component Impact

- `scribesim/evofit/stroke_gestures.py (planned schema/compiler sibling)`
- `scribesim/evofit/stroke_language.py (explicit version dispatch only as needed)`
- `tests/test_stroke_gestures.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/language/ (planned fixtures)`

These are planned implementation/evidence locations, not existing APIs.
Components remain incubating; production defaults and frozen v1 evidence stay unchanged.

## Dependencies

- [ADV-SS-EVOFIT-007](ADV-SS-EVOFIT-007.md)
- [ADV-SS-EXEMPLAR-009](ADV-SS-EXEMPLAR-009.md)
- [ADV-SS-NIBCONTACT-001](ADV-SS-NIBCONTACT-001.md)

Dependencies order work, not acceptance. Investigation completion can conclude
blocked. Live scope-qualified gate identities separately authorize fitting and
downstream execution; synthetic demonstrations never authorize real fitting.

## Planned Implementation Tasks

- [x] branch: confirm authorization before creating branches or commits.
- [x] tidy: assess narrow preparation; record any required behavior-preserving refactor separately.
- [x] test: add failing tests before any new or changed tooling; record red/green evidence. For investigation-only runs, record why code changes and TDD are not applicable rather than fabricating test evidence.
- [x] Implement versioned StrokeGesture and PenActionProfile records over shared primitive IDs. Enforce flat nonrecursive gesture references, ports, declared smooth/corner topology and explicit separate lift/overlap occurrences.
- [x] Validate finite ordered normalized-arc-length knots, endpoint coverage, units/frame, active-edge intervals and frozen action/rate envelopes. Reject required unsupported actions, stationary dabs and nonconstant pressure/speed in the initial contract.
- [x] Enforce at most eight gestures, four primitive references per gesture and four knots per active track, plus all existing expanded-letter/character/context budgets. Macro expansion must not multiply the four-primitive-per-letter allowance.
- [x] Compile globally by gesture arc length so repartitioning a continuous path introduces no settling pause, lift or pressure reset. Preserve primitive, gesture, action-profile and exact letter/word/line spans, including overlap contributors.
- [x] Hash all shared records and dependencies, invalidate compiled caches after changes and reject stale summaries or hidden per-letter residual geometry.
- [x] Provide explicit v1 fixed-action migration with lifts splitting gestures. Preserve legacy rendered pixels, contact schedules and logical/occurrence lineage with a recorded ID mapping, or refuse unsupported migration. Old readers fail on required new fields; no silent fallback.
- [x] Publish decomposition and segmentation-equivalence fixtures with the fixed-tool path; dynamic actions remain execution-unsupported until the contact/bridge Advances land.
- [x] evidence: append actual commands, identities, budgets, sample paths and outcome before marking completion.

## Validation Gates

- [x] Tests reject cycles, missing identities, malformed tracks, illegal contacts/crossings, expansion bypasses, unsupported actions and stale caches.
- [x] Repartitioning equivalent continuous geometry preserves contact and output within frozen tolerances; separate finishing passes retain explicit lifts and multiple owners.
- [x] Legacy bundle replay remains unchanged or migration is explicitly rejected. No completed v1 S1 record is relabeled as a new gesture-learning pass.

## Invariant Impact

Exact text and source uncertainty, locked-test isolation, shared lower-layer
lineage, deterministic replay and realized-contact ownership remain mandatory.
No fatigue, depletion/dips, random rhythm, tremor, warp or semantic state effects.
S1-gesture/S1-action supplement rather than replace S0–S4 and real G0–G4.

## Risk + Rollback

Macros can hide copied character curves or bypass budgets. Keep v1 loaders/evidence unchanged and the new schema opt-in; rollback removes only new version dispatch and dependent bundles.

Review estimate: 40 minutes, not a measured reviewability score.

## Evidence

- [x] Frozen inputs, criteria and identities; complete render/time and revision ledger.
- [x] Readable equal-scale evidence and a reproducible command/sample index under the planned bundle.
- [x] Scope-qualified decision with negative/null/unresolved outcomes and genuine review only when performed.
- [x] Tidy assessment and TDD red/green evidence for code changes; focused tests and clean-checkout replay where applicable.
- [x] `arrive plan check`, changed-link checks and `git diff --check`.
- [x] Before authorized merge, run `arrive pr check --strict --json`; report installed-tool limitations separately from provider CI. Never claim unobserved CI or owner approval.

## Bug Fixes

None implemented. Defects discovered during execution require a recorded
diagnosis and bounded repair; unrelated changes and threshold relaxation are excluded.

## Changes Made

### 2026-09-06 — plan: Scope TD-018 gesture and intentional-action work

- Added to Pass 15 phase `td018-gestures`.
- Implementation, experiments and acceptance remain pending.

### 2026-09-06 — complete: Versioned gesture compiler

- Red commits: `defc6e9` (missing module), `786c95c` (falsely smooth join).
  Green: `6e22531`. No preparatory refactor or legacy-source edit.
- Added flat shared gestures, finite bounded profiles, explicit lift/overlap
  occurrences, expanded-letter limits, exact text/layer identities and strict
  reconstructed bundle loading. Physical-y-down action frame is explicit.
- Lossless legacy migration retains full guide samples, pixels and ownership
  mappings. Ambiguous contexts/crossings are refused, not guessed. New
  gesture-global arc sampling is a separate opt-in mode; old readers reject it.
- Continuous primitive boundaries do not insert contact resets or pauses.
  Repartitioned cubic sample geometry differs by less than 0.001mm in the test.
  Dynamic/nonbaseline actions remain execution-unsupported until PATHGUIDE-006.
- 36 focused/regression tests pass locally (3.82s) and in clean clone
  `/tmp/td018-gesture-clean.EBja3v` at `6e22531` (3.92s).
  Hash-seed 839 replay reproduces every generated artifact byte-for-byte.
- Strict PR metadata check ran; installed parser returned `ids: []` for the
  repository ID format. No provider CI or human appearance approval claimed.
- [Compiler evidence](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/language/README.md).

## Check for Understanding

1. How can three primitive segments remain one pen-down gesture without losing their individual ownership?
2. Which changes invalidate a compiled model, and when must legacy migration fail?
