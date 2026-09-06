---
advance:
  id: "ADV-SS-HANDFLOW-010"
  title: "Foundation Motion Repair — Stable Time and Lift/Re-entry"
  system: "scribesim"
  primary_component: "handflow"
  components: ["handflow","pathguide","handvalidate","gesture","tests"]
  started_at: "2026-09-06T16:02:10Z"
  implementation_completed_at: "2026-09-06T18:25:34Z"
  review_time_estimate_minutes: 45
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api","migration"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration", "experiment:motion-gate-passed", "experiment:prior-failures-retained"]
  model_usage: []
  status: complete
---

## Objective

Diagnose and repair sampling-dependent actual contact entry before any new stroke or action fitting; provide current-code validation of the frozen primitive baseline.

**Work kind:** Investigation and implementation. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Complete after two original attempts and separately authorized braking, corner
and curve-clock follow-ups. Run-005 passes all 239 required motion gates and the
fresh original six-primitive baseline; clean replay is byte-identical. Admission
is fixed-tool synthetic motion only. No downstream training, S1-action, real-hand,
provider CI or human appearance approval is claimed. Earlier failures are retained.

## Behavioral Change

The shared planner now gives frozen source curves sampling-independent timestamps,
acceleration-feasible corner motion and lifted braking/rest entry. Source metadata
preserves cubic identity/parameter without changing guide geometry. All motion
gates pass under the existing integrator; legacy defaults remain unchanged.
This record belongs to `td018-foundation-repair`; existing completed records and
failed evidence remain unchanged.

## Component Impact

- `scribesim/handflow/controller.py and planning.py (existing positional path)`
- `scribesim/handvalidate/foundation_motion.py (diagnostic and read-only baseline revalidator)`
- `tests/test_handflow_reentry.py (temporal and arrival controls)`
- `tests/test_handflow_corner_timing.py (shared corner/curvature and independent acceptance tests)`
- `tests/test_handflow_curve_clock.py (numerical integration, provenance and repeated-stroke controls)`
- `scribesim/evofit/stroke_gestures.py, stroke_language.py and pathguide/repertoire.py, gesture_actions.py (opt-in source-parameter transport)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/ (immutable evidence)`

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
- [x] test: red tests precede behavioral changes, including braking/presentation commits `566eaa6`, `71ecbf3`, `cae63eb`, `ca9d8e1`, corner commits `a5154e5`, `2ef8393` and clock commit `e8b55fe`. Forty focused handflow repair tests pass.
- [x] Freeze the saved u / i u failures and continuous, separated-contact, coincident-overlap, word-space and exact-subdivision controls. Add red tests for first/last actual contact positions, event timing and ownership before code changes.
- [x] Isolate duration flooring arithmetically, record rounded step excess, and measure projection/held-target behavior through delegated step observation. The saved old 0.399871 mm failure is reproduced; no unmeasured causal attribution to independent ablations is claimed.
- [x] Implement explicit opt-in event-time-v1/v2 in the existing positional integrator, plus boundary-preserving gesture-arc-v3. No teleport, ideal-trace substitution, image correction or threshold relaxation. The final curve-clock follow-up completes overall motion acceptance.
- [x] User-authorized follow-up: explicit `braked-air-v1` planning, prescribed braking/rest arrival, analytic contact clock, unchanged physical limits and source-owner mapping. All arrival checks pass; the remaining failure is at a continuous-contact corner, not pen landing.
- [x] Subsequent user-authorized `corner-time-v1`: shared corner/smooth compiled ports, curvature-bounded contact speed and 125 mm/s² acceleration ramps. Planned corner rest keeps contact down; source geometry and owners remain unchanged. Independent desired acceleration, corner completeness/rest, geometry, ink and actual mechanics checks pass. The original braking failure above is historical.
- [x] Subsequent user-authorized `curve-time-v1`: bounded cubic arc integration and validated opt-in source provenance replace sampled-chord clock distances, without changing corner/air rules. All event-time refinements pass; no rounding of clocks or tolerance relaxation.
- [x] Preserve legacy playback, fixed-tool behavior and full contact ownership; separately check the physical-edge fixed-profile bridge. Frozen timing bounds are 1e-10 s duration error and 0.1 ms cross-sampling event shift.
- [x] Implement read-only revalidation of the six frozen primitive models against their original targets and original applicable S1 metrics. Run-005's six-family baseline and complete motion gate now pass; old freezes were not edited and no geometry was refitted.
- [x] Publish before/after ink panels and an enlarged re-entry path/velocity/lag plot, with actual time/contact/owner traces and a reusable baseline revalidator. Downstream compiler-triggered revalidation remains a future consuming-run obligation.
- [x] evidence: all five immutable attempts, current-code verification and cumulative budgets recorded. All required motion gates are now checked; prior failed decisions remain unchanged.

## Validation Gates

- [x] Required actual contact endpoints converge within 0.01 mm across dt 0.002/0.001 s, arc steps 0.025/0.0125 mm and equivalent segmentation; image difference <= 0.03 and contact corridor <= 0.25 mm.
- [x] Cross-sampling contact events converge within 0.0001 s. Run-005 arc-density shift is exactly zero in the recorded fixtures; maximum exact-subdivision shift is 8.881784197001252e-16 s. The old run-004 0.000437750 s failure remains immutable.
- [x] Every declared corner is accounted for at its exact port, with zero planned speed and no lift/dwell. Actual corner speed <= 0.5 mm/s, position error <= 0.05 mm; desired acceleration <= 250 mm/s² and actual acceleration <= 500 mm/s², allowing only floating-point tolerance.
- [x] Zero contact-group/owner errors and exact event-time execution on the six fixtures; pen-up samples do not paint. Actual lag remains visible and is not projected away.
- [x] Legacy rows are identical across both attempts. Fresh current-code baseline proof is required, and failed motion still blocks primitive fitting. Pre-existing stale-identity/constructor test failures are retained separately below.

## Budget and Stop Rules

Use [Addendum B Section 7](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#7-budgets-and-stop-rules):
at most six fixture families, 500 diagnostic renders or 1800 seconds per attempt; zero optimization; one diagnosed revision. Baseline revalidation and replay share this cap.
The user's subsequent “Let's do the next required fix” authorized the separately
registered spec-v3 air-braking allowance: one candidate, 500 renders or 1800 s,
zero optimization, no automatic revision. It used 303 renders in 9.426154 s.
The subsequent corner-aware request authorized spec-v4: one additional candidate,
500 renders or 1800 s, zero optimization and no automatic revision. Run-004 used
303 renders in 49.002829 s. The user then authorized spec-v5's one curve-clock
candidate: 303 renders in 22.987616 s, zero fitting/revisions, all gates passed.
Clean regression is separately labeled: 303 verification renders in 19.227469 s.
All prior attempts remain immutable. No extra candidate or downstream Advance
execution is inferred from successful motion admission.
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
- [x] Corner follow-up: 34 focused handflow tests pass; expanded local suite has 100 passes and the same pre-existing constructor failure. Run-004 has 233/239 passing checks, a passing six-primitive baseline and zero optimizer evaluations. [Results and samples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/run-004/README.md); all six failures are arc-refinement timing, not corner/ink quality.
- [x] Clean-checkout hash-seed-839 replay at `1597ed1` reproduces all measured rows/checks/decision and byte-identical freeze, baseline, traces and PNGs; 303 separately labeled verification renders in 29.342524 s. Expanded clean tests also have 100 passes and the same pre-existing failure. [Verification receipt](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/corner-verification.json).
- [x] `arrive plan check`, changed local links and `git diff --check` pass. Artifact doctor retains ten pre-existing issues; agent-rule sync has no stale output.
- [x] Clock follow-up: 40 focused tests pass; expanded local and clean-checkout suites each have 106 passes and the same pre-existing constructor failure. Run-005 passes 239/239 checks and the fresh baseline; clean hash-seed-839 replay reproduces the entire report and all artifacts byte-for-byte. [Results](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/run-005/README.md) and [verification](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/clock-verification.json).
- [x] Strict PR metadata check executed before merge but installed parser reports no recognized ID for `ADV-SS-HANDFLOW-010`; no provider CI or successful strict gate is claimed. This pre-existing tooling limitation is recorded separately from the passing motion gate.
- [x] Scope-qualified motion completion; no new learning or owner approval counted as complete.

## Bug Fixes

Sampling-dependent elapsed-time flooring, contact-event stepping and corner
chording are repaired in opt-in versions. Endpoint convergence now passes, but
the original air plan requested an infeasible velocity reversal at contact.
The authorized braking follow-up fixes landing: saved u re-entry speed is
0.001221 mm/s with 0.0000603 mm positional error. The remaining peak is at a sharp
stem-to-exit contact corner (saved u 0.370963 mm versus the unchanged 0.25 mm
limit) in retained run-003. Run-004 repairs that corner: saved-u lag is
0.007516 mm and all corner/geometry/acceleration gates pass. However, computing
the slower contact clock from sampled chord lengths accumulates up to 0.438 ms
of arc-refinement timing drift, exceeding 0.1 ms in that retained attempt.
Run-005 replaces sampled-chord clock distances with geometric arc integrals:
arc-density timing drift is zero, maximum contact lag is 0.007411 mm, and all
239 gates plus current primitive baseline pass. Foundation motion repair is complete.

## Changes Made

### 2026-09-06 — curve clock: Complete fixed-tool motion repair

- Local merge `14872ba` integrates the completed Advance into master; no remote push or provider CI is claimed. The merge retains all prior failed evidence alongside accepted run-005.
- Red test commit `e8b55fe` precedes implementation `c95a730`; no preparatory tidy needed. Existing sampler/planner paths are extended, not replaced by a second simulator.
- Added opt-in curve-position metadata, bounded 16/32-point cubic speed integration and geometry/ownership/monotonicity validation. The original sample coordinates, fixed tools, corner slowing, air braking and legacy modes are unchanged.
- Independent tests cover analytic and high-order reference lengths, exact cubic splitting, repeated saved constructions, integration exhaustion and malformed provenance. All 40 focused tests pass; local/clean expanded suites are 106 passed plus the same unrelated old failure.
- Run-005 uses 303 renders, 22.987616 s and zero optimization; all 239 motion gates and the six-family baseline pass. Clean replay is byte-identical and separately accounted for. Old run-001 through run-004 files and decisions remain immutable.
- HANDFLOW-010 is complete. GESTURE-002 is next, still planned: audit return vocabulary and ports before any new primitive learning. No action or historical-hand acceptance follows from this result.

### 2026-09-06 — authorized corner timing: Tracking passes, clock refinement fails

- `1597ed1` implements the single frozen candidate; `a5154e5` records seven red timing/gate tests and `2ef8393` adds independent completeness and smooth-join controls before implementation commit. The missing-corner guard was explicitly re-run red before restoration. No preparatory tidy was necessary; existing planner/controller paths are reused.
- Exact corners become planned zero-speed contact instants. Smooth sections use cubic curvature and conservative shared speed ceilings, not letter IDs or altered geometry. Fixed air braking and legacy defaults remain available.
- Corridor, corner rest, arrivals, endpoint/image convergence, desired/actual acceleration, ownership and old-six baseline pass. Six cumulative arc-time checks fail. Marked the newly satisfied gates, not the entire Advance.
- Retained immutable run-004, native 900-DPI samples and a saved-trace speed/lag plot. No fitting, extra candidate, merge or downstream work.
- [Next bounded proposal](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/motion/arc-clock-request.md): geometry-derived arc length/time, independent of guide sampling. Requires new authorization; thresholds stay unchanged.

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

1. Why does `curve-time-v1` integrate frozen cubic speed rather than sum sampled chords, and which provenance checks prevent confusing loops or overlaps?
2. Which run-005 gates and clean-replay identities establish fixed-tool motion acceptance without claiming new learned strokes, S1-action or a real hand?
3. How do unchanged legacy modes and immutable failed runs support rollback without granting stale evidence current admission?
