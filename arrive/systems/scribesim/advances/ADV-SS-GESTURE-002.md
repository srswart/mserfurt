---
advance:
  id: "ADV-SS-GESTURE-002"
  title: "Foundation Vocabulary — Return Ports and Audited Composition Limits"
  system: "scribesim"
  primary_component: "gesture"
  components: ["gesture","evo","curriculum","handvalidate","tests"]
  started_at: "2026-09-06T16:02:10Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 45
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api","migration"]
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Determine the smallest reusable return vocabulary and bounded composition contract that can support ordinary starter constructions without letter-specific curves.

**Work kind:** Investigation and bounded contract implementation. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Timestamp records drafting only; implementation, experiments, CI and review are not claimed.

## Behavioral Change

The deliverable and acceptance boundary are specified in the tasks and gates below.
This record belongs to `td018-foundation-repair`; existing completed records and
failed evidence remain unchanged.

## Component Impact

- `scribesim/evofit/foundation_contract.py (planned versioned contract/audit)`
- `scribesim/evofit/stroke_gestures.py (explicit version integration only)`
- `tests/test_foundation_contract.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/contract/ (planned immutable evidence)`

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

- [ ] branch: confirm implementation/commit/merge authorization and preserve unrelated work.
- [ ] tidy: assess narrow preparation; commit any required behavior-preserving refactor separately.
- [ ] test: commit failing behavioral tests before implementation when commits are authorized; planning-only edits do not claim TDD execution.
- [ ] Audit six existing primitives against eight gesture hypotheses and the twelve-letter feasibility checklist in Addendum B. Publish direction/port, topology/counter, attachment and expanded-count tables, distinguishing synthetic hypotheses from historical admission.
- [ ] Specify at most two new shared lower-return/upper-return families, with explicit ports, independent target provenance and bounded interior-control-point freedoms. Do not silently relabel existing turn/loop geometry.
- [ ] Test the four-primitive letter cap against the checklist. Select the smallest evidenced sufficient new cap, at most eight expanded occurrences per letter, retaining four references per gesture, eight families/gestures and two recipes per character.
- [ ] Freeze the audit and contract before implementation/training. If more families, larger caps, new reflection/rotation freedoms or incompatible ports are required, stop and revise the design explicitly.
- [ ] Implement only justified opt-in contract/compiler changes and new-family schema support. Preserve old readers/caps, acyclic expansion, finite transforms, exact owners and fail-closed unsupported forms; do not add per-letter cubics or a grammar that hides expansion.
- [ ] Declare supported and missing inventory plus train/development/topology-held-out fixture specifications. Supply untrained initial models, not fitted or accepted return primitives.
- [ ] evidence: record commands, identities, actual budgets, sample paths and outcome before completion; keep unexecuted tasks unchecked.

## Validation Gates

- [ ] Every claimed construction has visible primitive expansion and compatible ports; unsupported loops/opposite bowls remain debt, not aliases or extra hidden gestures.
- [ ] New reader/version enforces the audited cap and refuses malformed, cyclic, nonfinite, unsupported or detached geometry; legacy behavior remains explicit.
- [ ] No source/locked-test pixels or new training renders are used for the coverage audit. Contract completion does not claim learned strokes or authorize fitting without fresh matching motion/baseline validation.

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

- [ ] Frozen inputs, independent targets/controls, criteria and scope-specific identities.
- [ ] Actual work/budget ledger, equal-scale samples, failures and executable replay commands.
- [ ] Focused red/green regression tests and clean-checkout replay when code changes.
- [ ] `arrive plan check`, changed local-link checks and `git diff --check`.
- [ ] Before an authorized merge run `arrive pr check --strict --json`; report installed ID-parser limitations separately from provider CI.
- [ ] Scope-qualified result; no unperformed learning, candidate evaluation or human review counted as complete.

## Bug Fixes

None yet. The planned diagnosis/repair is not an implemented or validated fix.

## Changes Made

### 2026-09-06 — plan: Prioritize reliable learned stroke foundations

- Added the bounded work to Pass 15 `td018-foundation-repair`.
- Implementation and acceptance remain pending under Addendum B.

## Check for Understanding

1. Which exact evidence and identities permit this Advance's experiment to run?
2. What visible learned or independently evaluated result distinguishes completion from scaffolding?

