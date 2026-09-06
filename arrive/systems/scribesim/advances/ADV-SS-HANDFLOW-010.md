---
advance:
  id: "ADV-SS-HANDFLOW-010"
  title: "Foundation Motion Repair — Stable Time and Lift/Re-entry"
  system: "scribesim"
  primary_component: "handflow"
  components: ["handflow","pathguide","handvalidate","gesture","tests"]
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

Diagnose and repair sampling-dependent actual contact entry before any new stroke or action fitting; provide current-code validation of the frozen primitive baseline.

**Work kind:** Investigation and implementation. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Timestamp records drafting only; implementation, experiments, CI and review are not claimed.

## Behavioral Change

The deliverable and acceptance boundary are specified in the tasks and gates below.
This record belongs to `td018-foundation-repair`; existing completed records and
failed evidence remain unchanged.

## Component Impact

- `scribesim/handflow/controller.py and planning.py (existing positional path)`
- `scribesim/handvalidate/foundation_motion.py (planned diagnostic and read-only baseline revalidator)`
- `tests/test_handflow_reentry.py (planned)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/ (planned immutable evidence)`

Existing components remain incubating. No separate renderer/controller or new component.

## Dependencies

- [ADV-SS-HANDVALIDATE-013](ADV-SS-HANDVALIDATE-013.md)
- [ADV-SS-PATHGUIDE-006](ADV-SS-PATHGUIDE-006.md)
- [ADV-SS-HANDVALIDATE-014](ADV-SS-HANDVALIDATE-014.md)

Plan dependencies order work, not runtime admission. Consume only matching,
independently validated layer/tool/code identities. Real fitting additionally
requires live G0 and accepted real lower layers; source uncertainty and locked
test isolation are not repaired by this synthetic phase.

## Planned Implementation Tasks

- [ ] branch: confirm implementation/commit/merge authorization and preserve unrelated work.
- [ ] tidy: assess narrow preparation; commit any required behavior-preserving refactor separately.
- [ ] test: commit failing behavioral tests before implementation when commits are authorized; planning-only edits do not claim TDD execution.
- [ ] Freeze the saved u / i u failures and continuous, separated-contact, coincident-overlap, word-space and exact-subdivision controls. Add red tests for first/last actual contact positions, event timing and ownership before code changes.
- [ ] Isolate segment-duration flooring, substep rounding, held desired samples and corridor projection as hypotheses. Measure planned versus executed time and state on both sides of every lift; record the demonstrated cause rather than assuming one.
- [ ] Repair the existing positional integrator through an explicit opt-in execution version if semantics change. No second simulator, contact-position teleport, ideal-trace substitution, image correction or weaker threshold.
- [ ] Preserve legacy playback, fixed-tool behavior and full contact ownership; check the physical-edge fixed-profile bridge separately. Freeze contact-event and time tolerances before comparing repaired candidates.
- [ ] Implement read-only revalidation of the six frozen primitive models against their original synthetic targets and applicable original S1 criteria under current code/tool/motion. Emit fresh baseline admission only after measured checks pass; never edit old freezes or refit baseline geometry.
- [ ] Publish before/after entry close-ups, velocity/time/contact traces and a reusable baseline revalidator. Reuse it after later compiler changes, with work charged to the consuming run.
- [ ] evidence: record commands, identities, actual budgets, sample paths and outcome before completion; keep unexecuted tasks unchecked.

## Validation Gates

- [ ] Required actual contact endpoints converge within 0.01 mm across dt 0.002/0.001 s, arc steps 0.025/0.0125 mm and equivalent segmentation; image difference <= 0.03 and contact corridor <= 0.25 mm.
- [ ] Zero extra/missing contacts or text/owner errors, no painted air, no sampling-induced accumulated time drift beyond the independently frozen timing criterion; lag is actual measured state.
- [ ] Legacy regressions remain equivalent in legacy mode; matching current baseline admission is possible only from fresh read-only proof, not a historical pass label. An unresolved cause or baseline failure blocks primitive fitting.

## Budget and Stop Rules

Use [Addendum B Section 7](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#7-budgets-and-stop-rules):
at most six fixture families, 500 diagnostic renders or 1800 seconds per attempt; zero optimization; one diagnosed revision. Baseline revalidation and replay share this cap.
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

