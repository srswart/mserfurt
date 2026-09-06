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
  evidence: ["tdd:red-green", "tests:unit", "tests:integration", "experiment:failed-motion-gate"]
  model_usage: []
  status: in_progress
---

## Objective

Diagnose and repair sampling-dependent actual contact entry before any new stroke or action fitting; provide current-code validation of the frozen primitive baseline.

**Work kind:** Investigation and implementation. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Implementation, two original attempts and the separately authorized braking
follow-up have executed. Re-entry now passes; the Advance remains in progress
because sharp stem-to-exit corner tracking fails. No implementation merge,
downstream training, provider CI or human approval is claimed.

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

- [x] branch: user authorized implementation/update/merge; preserved planning in master commit `64f818f`, then used `advance/ss-handflow-010`.
- [x] tidy: assessed narrow preparation; reused the existing controller step without a second simulator. No separate preparatory refactor was necessary or claimed.
- [x] test: red tests precede behavioral changes, including braking/presentation commits `566eaa6`, `71ecbf3`, `cae63eb`, `ca9d8e1`. Twenty-four handflow repair tests pass.
- [x] Freeze the saved u / i u failures and continuous, separated-contact, coincident-overlap, word-space and exact-subdivision controls. Add red tests for first/last actual contact positions, event timing and ownership before code changes.
- [x] Isolate duration flooring arithmetically, record rounded step excess, and measure projection/held-target behavior through delegated step observation. The saved old 0.399871 mm failure is reproduced; no unmeasured causal attribution to independent ablations is claimed.
- [x] Implement explicit opt-in event-time-v1/v2 in the existing positional integrator, plus boundary-preserving gesture-arc-v3. No teleport, ideal-trace substitution, image correction or threshold relaxation. Overall motion repair remains incomplete because the corridor gate fails.
- [x] User-authorized follow-up: explicit `braked-air-v1` planning, prescribed braking/rest arrival, analytic contact clock, unchanged physical limits and source-owner mapping. All arrival checks pass; the remaining failure is at a continuous-contact corner, not pen landing.
- [x] Preserve legacy playback, fixed-tool behavior and full contact ownership; separately check the physical-edge fixed-profile bridge. Frozen timing bounds are 1e-10 s duration error and 0.1 ms cross-sampling event shift.
- [x] Implement read-only revalidation of the six frozen primitive models against their original targets and original applicable S1 metrics. The revised six-family baseline checks pass, but global motion admission stays false; old freezes were not edited and no geometry was refitted.
- [x] Publish before/after ink panels and an enlarged re-entry path/velocity/lag plot, with actual time/contact/owner traces and a reusable baseline revalidator. Downstream compiler-triggered revalidation remains a future consuming-run obligation.
- [x] evidence: immutable attempts, current-code verification and cumulative budget recorded; the failed acceptance gate remains unchecked.

## Validation Gates

- [ ] Required actual contact endpoints converge within 0.01 mm across dt 0.002/0.001 s, arc steps 0.025/0.0125 mm and equivalent segmentation; image difference <= 0.03 and contact corridor <= 0.25 mm.
- [x] Zero contact-group/owner errors and exact event-time execution on the six fixtures; pen-up samples do not paint. Actual lag remains visible and is not projected away.
- [x] Legacy rows are identical across both attempts. Fresh current-code baseline proof is required, and failed motion still blocks primitive fitting. Pre-existing stale-identity/constructor test failures are retained separately below.

## Budget and Stop Rules

Use [Addendum B Section 7](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#7-budgets-and-stop-rules):
at most six fixture families, 500 diagnostic renders or 1800 seconds per attempt; zero optimization; one diagnosed revision. Baseline revalidation and replay share this cap.
The user's subsequent “Let's do the next required fix” authorized the separately
registered spec-v3 air-braking allowance: one candidate, 500 renders or 1800 s,
zero optimization, no automatic revision. It used 303 renders in 9.426154 s;
the original two attempts remain immutable. No further candidate is authorized.
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

- [x] Frozen inputs, original independent primitive targets, criteria and code/model/tool identities in both motion attempts.
- [x] [Samples and actual-lag explanation](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/index.html), [ledger](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/ledger.json), [replay instructions](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/run-002/README.md).
- [x] Eighteen new tests pass; expanded local and clean-checkout runs each yield 84 passed and one pre-existing missing-`nib_angle_deg` failure, reproduced at `64f818f`. Eleven additional stale-frozen-identity failures in old gesture-learning/evaluation tests also reproduce before this work; no old hashes or tests were weakened.
- [x] Braking follow-up: 24 handflow tests pass; expanded clean-checkout suite has 90 passes and the same pre-existing constructor failure. Hash-seed-839 replay reproduces the measured rows, checks, baseline traces and images. [New samples and results](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/run-003/README.md).
- [x] `arrive plan check`, changed local links and `git diff --check` pass. Artifact doctor retains ten pre-existing issues; agent-rule sync has no stale output.
- [x] Strict PR metadata check executed but installed parser reports no recognized ID for `ADV-SS-HANDFLOW-010`; no provider CI or successful strict gate is claimed. No implementation merge performed because the Advance is incomplete.
- [x] Scope-qualified failed outcome; no new learning or owner approval counted as complete.

## Bug Fixes

Sampling-dependent elapsed-time flooring, contact-event stepping and corner
chording are repaired in opt-in versions. Endpoint convergence now passes, but
the original air plan requested an infeasible velocity reversal at contact.
The authorized braking follow-up fixes landing: saved u re-entry speed is
0.001221 mm/s with 0.0000603 mm positional error. The remaining peak is at a sharp
stem-to-exit contact corner (saved u 0.370963 mm versus the unchanged 0.25 mm
limit). This is not yet a completed foundation motion repair.

## Changes Made

### 2026-09-06 — authorized follow-up: Fix landing and clarify the samples

- `eb10004` implements the single frozen air-braking candidate and native 900-DPI presentation; `f222169` adds fixed-input validation and preserves run-003. No optimization or further motion revision.
- Landing, time, endpoint, mechanics and old-six baseline checks pass; required sharp-corner corridor checks still fail. Advance stays in progress and unmerged; no later foundation training runs.
- Replaced pixel-enlarged previews with actual high-resolution geometric rendering and smooth downsampling. Added a separate six-primitive gallery; comparison labels now describe repeated stem-terminal fixtures, not learned letters.
- [Next proposed scope](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/corner-timing-request.md): shared acceleration-aware contact/corner timing, not additional air-arrival patches. Requires separate authorization.

### 2026-09-06 — implement and stop: Re-entry feasibility still fails

- `dfac9c9`: first immutable attempt, 266 renders, 17.091055 s; unprojected baseline failed.
- `c66e9f5`: single permitted revision, 266 renders, 14.706725 s. All fixture endpoint/image/time refinements pass; fresh old-six baseline passes; repeated-contact corridor checks fail.
- `ca08732`: fail-closed completeness/current-identity checks and a bounded time-grid guard; no additional motion candidate. Clean-checkout verification reproduces all measured rows, baseline traces and failed checks with 266 separately labeled verification renders.
- Zero optimizer evaluations, no source/reference access or later Advance execution. Remaining five records stay planned. This branch is not merged as a completed Advance.
- [Required next scope](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/revision-request.md): acceleration-feasible pen-up braking and tangent-compatible re-entry. The allowed revision is spent; another motion experiment needs explicit new scope.

### 2026-09-06 — plan: Prioritize reliable learned stroke foundations

- Added the bounded work to Pass 15 `td018-foundation-repair`.
- Implementation and acceptance remain pending under Addendum B.

## Check for Understanding

1. Which exact evidence and identities permit this Advance's experiment to run?
2. What visible learned or independently evaluated result distinguishes completion from scaffolding?
