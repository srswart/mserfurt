---
advance:
  id: "ADV-SS-GESTURE-002"
  title: "Foundation Vocabulary — Return Ports and Audited Composition Limits"
  system: "scribesim"
  primary_component: "gesture"
  components: ["gesture","evo","curriculum","handvalidate","pathguide","tests"]
  started_at: "2026-09-06T18:37:24Z"
  implementation_completed_at: "2026-09-06T18:50:38Z"
  review_time_estimate_minutes: 45
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api","migration"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration", "audit:synthetic-contract", "replay:clean-checkout"]
  model_usage: []
  status: complete
---

## Objective

Determine the smallest reusable return vocabulary and bounded composition contract that can support ordinary starter constructions without letter-specific curves.

**Work kind:** Investigation and bounded contract implementation. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Complete: eight gesture hypotheses and twelve feasibility characters audited;
two untrained return families and their exact actual-tangent interfaces frozen.
The opt-in six-expanded-occurrence contract passes; old readers retain four.
Only i/n/u/m/h have supplied constructions. r/l remain partial; o/a/d/e/g and
opposite-bowl/lower-loop inventory remain debt. No fitting, actual extension
acceptance, source-pixel access, provider CI or human appearance approval.
After compiler changes, current motion/baseline revalidation is mandatory before training.

## Behavioral Change

New explicit foundation gesture/lowered-language readers admit at most six
expanded primitive occurrences per recipe, preserve exact ownership, and reject
unsupported or malformed constructions. Lower/upper returns have fixed endpoints
and tangent rays with only two bounded handle lengths per family. Old-six geometry,
legacy caps, transform limits and fixed tool semantics remain unchanged.
This record belongs to `td018-foundation-repair`; existing completed records and
failed evidence remain unchanged.

## Component Impact

- `scribesim/evofit/foundation_contract.py (versioned contract/audit)`
- `scribesim/evofit/stroke_gestures.py (explicit version integration only)`
- `tests/test_foundation_contract.py (implemented)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/contract/ (immutable evidence)`

Existing components remain incubating. No separate renderer/controller or new component.

## Dependencies

- [ADV-SS-HANDFLOW-010](ADV-SS-HANDFLOW-010.md)
- [ADV-SS-GESTURE-001](ADV-SS-GESTURE-001.md)
- [ADV-SS-EXEMPLAR-009](ADV-SS-EXEMPLAR-009.md)

Plan dependencies order work, not runtime admission. Consume only matching,
independently validated layer/tool/code identities. Real fitting additionally
requires live G0 and accepted real lower layers; source uncertainty and locked
test isolation are not repaired by this synthetic phase.

## Planned Implementation Tasks

- [x] branch: confirm implementation/commit/merge authorization and preserve unrelated work.
- [x] tidy: assessed the existing compiler; reused its lowering/validation and renderer with narrowly opt-in branches. No separate preparatory refactor was necessary or claimed.
- [x] test: `10b7b84` records 14 red tests, `f1db548` adds two red version/tool checks; `633dabc` implements them. Sixteen new tests and the 59-test focused suite pass.
- [x] Audit six existing primitives against eight gesture hypotheses and the twelve-letter feasibility checklist in Addendum B. Publish direction/port, topology/counter, attachment and expanded-count tables, distinguishing synthetic hypotheses from historical admission.
- [x] Specify at most two new shared lower-return/upper-return families, with explicit ports, independent target provenance and bounded interior-control-point freedoms. Do not silently relabel existing turn/loop geometry.
- [x] Test the four-primitive letter cap against the checklist. Select the smallest evidenced sufficient new cap, at most eight expanded occurrences per letter, retaining four references per gesture, eight families/gestures and two recipes per character.
- [x] Freeze the audit and contract before implementation/training. If more families, larger caps, new reflection/rotation freedoms or incompatible ports are required, stop and revise the design explicitly.
- [x] Implement only justified opt-in contract/compiler changes and new-family schema support. Preserve old readers/caps, acyclic expansion, finite transforms, exact owners and fail-closed unsupported forms; do not add per-letter cubics or a grammar that hides expansion.
- [x] Declare supported and missing inventory plus train/development/topology-held-out fixture specifications. Supply untrained initial models, not fitted or accepted return primitives.
- [x] evidence: record commands, identities, actual budgets, sample paths and outcome before completion; keep unexecuted tasks unchecked.

## Validation Gates

- [x] Every claimed construction has visible primitive expansion and compatible ports; unsupported loops/opposite bowls remain debt, not aliases or extra hidden gestures.
- [x] New reader/version enforces the audited cap and refuses malformed, cyclic, nonfinite, unsupported or detached geometry; legacy behavior remains explicit.
- [x] No source/locked-test pixels or new training renders are used for the coverage audit. Contract completion does not claim learned strokes or authorize fitting without fresh matching motion/baseline validation.

## Budget and Stop Rules

Use [Addendum B Section 7](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#7-budgets-and-stop-rules):
eight gesture hypotheses, twelve feasibility characters, two proposed families; at most 100 diagnostic renders or 900 seconds per attempt; zero optimization; one diagnosed revision.
Keep immutable attempts and a cumulative ledger. Stop on unmet prerequisites or
budget exhaustion; no threshold relaxation, hidden extra search or guessed approval.

## Invariant Impact

Exact text, source/test isolation, shared lower-layer lineage, deterministic
replay and realized-contact ownership remain mandatory. Old freezes are immutable.
No fatigue, ink depletion/dips, stochastic rhythm, tremor, warp, historical
calibration claims or default renderer promotion.

## Risk + Rollback

A visually similar image can conceal contact instability, missing vocabulary or
copied geometry. Preserve failed cases and explicit execution/contract versions;
rollback to the prior mode without treating historical acceptance as current.
Review estimate is 45 minutes, not measured review or approval.

## Evidence

- [x] Frozen inputs, independent targets/controls, criteria and scope-specific identities.
- [x] Actual work/budget ledger, equal-scale samples, failures and executable replay commands.
- [x] Focused red/green regression tests and clean-checkout replay when code changes.
- [x] `arrive plan check`, changed local-link checks and `git diff --check`.
- [x] Before an authorized merge run `arrive pr check --strict --json`; report installed ID-parser limitations separately from provider CI.
- [x] Scope-qualified result; no unperformed learning, candidate evaluation or human review counted as complete.

## Bug Fixes

The original four-occurrence cap could not represent the frozen two-arch m
construction without hiding expansion. A new explicit reader admits six; the
old reader remains unchanged. Actual endpoint tangents, not stale declaration
vectors, now define the new return interfaces; the old parameters are not edited.
Returned compiler and guide metadata retain the foundation schema rather than
silently labeling a six-occurrence result as v2.

## Changes Made

### 2026-09-06 — 0b94dfc: Local merge receipt

- Merged `advance/ss-gesture-002` into `master` with `--no-ff` after audit, clean replay and documented governance checks. Full merge: `0b94dfc66e46f2c9a28b000c5d3ae8f5dd9422ad`; no remote push.
- The implementation and frozen evidence identities are unchanged by the documentation and merge. Strict parser and pre-existing test limitations remain disclosed; this receipt does not imply provider CI or owner review.

### 2026-09-06 — 633dabc: Complete the bounded return contract audit

- Frozen spec-v1 precedes implementation; old run-005 motion and original primitive provenance are verified independently of current compiler identities. Original evidence remains immutable.
- Added `foundation_contract.py`, opt-in readers in `stroke_language.py` / `stroke_gestures.py`, and contract/module identities in `gesture_actions.py`. No new component or renderer.
- Eight hypotheses and twelve characters are reported with directions, topology/counters, explicit joins, expanded counts and debt. Six named hypothesis constructions have valid ports; the opposite bowl and lower loop remain unsupported.
- The m scaffold uses two three-piece lifted overturns: caps four/five fail its explicit count; six suffices for this frozen subset. This is not a universal calligraphic minimum or alphabet acceptance.
- Two return families freeze endpoints, port rays and handle bounds 0.12–0.40. Independent analytic targets and single-versus-attachment topology splits are specified, not rendered, scored or fitted.
- Immutable run-001 passes with 22 nominal diagnostic renders in 1.168160 s, zero optimization/training/target renders and no revision. Clean hash-seed-839 replay is byte-identical; verification separately uses 22 renders in 1.244628 s.
- Focused suite: 59 passes. Expanded local/clean suites each have 138 passes and the same pre-existing missing-nib-angle constructor failure. ARRIVE plan passes, artifact doctor retains ten old issues, and generated rules are not stale.
- Strict PR check executed; installed parser reports no recognized ADV-SS-GESTURE-002 ID. No successful strict gate, provider CI or owner review is claimed.
- [Audit and samples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/contract/README.md), [ledger](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/contract/ledger.json), [verification](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/contract/verification.json).
- Next is CURRICULUM-010: refresh matching motion/baseline evidence under changed compiler identities before fitting only the new returns. That learning Advance remains planned; audit completion does not bypass its prerequisites.

### 2026-09-06 — plan: Prioritize reliable learned stroke foundations

- Added the bounded work to Pass 15 `td018-foundation-repair`.
- Implementation and acceptance remain pending under Addendum B.

## Check for Understanding

1. Why are new return ports tied to actual frozen stem/rise tangents instead of rewriting the old declared vectors?
2. Why does the six-occurrence cap fit the supplied m scaffold without admitting the seven unresolved checklist characters or weakening legacy readers?
3. Which current-code motion/baseline checks must CURRICULUM-010 rerun, and why do these nominal untrained diagrams not constitute learned-stroke acceptance?
