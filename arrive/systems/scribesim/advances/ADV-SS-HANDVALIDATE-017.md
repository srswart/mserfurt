---
advance:
  id: "ADV-SS-HANDVALIDATE-017"
  title: "Foundation Action or Null — Independent Selected-Candidate Acceptance"
  system: "scribesim"
  primary_component: "handvalidate"
  components: ["handvalidate","curriculum","gesture","handflow","pathguide","nibcontact","tests"]
  started_at: "2026-09-08T06:01:40Z"
  implementation_completed_at: "2026-09-08T06:44:10Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api","migration"]
  evidence: ["tdd:red-green","tests:unit","local:independent-evaluation","local:fresh-process-replay"]
  model_usage: []
  status: complete
---

## Objective

Independently evaluate the newly frozen action or null candidates that the historical action phase never executed. Issue a matching scoped S1-action decision rather than promoting a fixed profile or copying learning pass flags.

Implementation authorized 2026-09-08, with standing update/merge instruction.
No preparatory refactor: isolate the evaluator and preserve all pinned modules.
Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).

## Behavioral Change

Independent current-code numeric proofs and complete scoped action/null evidence are required. Any required unresolved action blocks affected letter inventory. Real G0/G1/G2 and owner appearance review remain separate.

## Component Impact

`scribesim/handvalidate/foundation_actions.py`, explicit opt-in scoped-null admission with separate letter prerequisites, focused tests and `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/action_evaluation/`.
Existing components remain incubating; no separate controller or renderer.

## Dependencies

- [ADV-SS-CURRICULUM-012](ADV-SS-CURRICULUM-012.md)
- [ADV-SS-HANDVALIDATE-016](ADV-SS-HANDVALIDATE-016.md)
- [ADV-SS-HANDVALIDATE-014](ADV-SS-HANDVALIDATE-014.md)

## Planned Implementation Tasks

### Frozen CURRICULUM-012 input — 2026-09-08

The bounded null experiment is measured for every seed with exact replay, but
the whole-candidate null is **unsupported**, not S1-action. Pin report SHA
`ba2d46377b59787065486738e861aaea00c042cf0be2704072821aed3ac0fa3a` at
`shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/actions/run-001/report.json`.
Candidate files under `seed-{7,19,41}/first/candidate.json` retain SHA
`d8b26fba2655b0bba961865fb74b543829cb1b11ac850afd672dd02ba0822e5a`.
The new `foundation_actions.require_candidates` reader permits independent
review of this completed negative experiment, never action/letter admission.

Underturn has scoped null support; overturn/compound exceed absolute target
loss 0.05 already in nominal geometry. Preserve those findings and evaluate
scope/diagnosis independently before contemplating new shared-geometry work.
Do not fit actions to conceal geometry error or run letter fitting. Existing
full-edge rejection controls are not asymmetric physical-edge or closed-letter
counter evidence. This input note does not start or complete HANDVALIDATE-017.

- [x] branch: confirm implementation/update/merge authorization and preserve unrelated work.
- [x] tidy: assess minimal behavior-preserving preparation separately.
- [x] test: commit observed failing behavioral tests before implementation.
- [x] Pin CURRICULUM-012 selected candidate reports and current lower-layer/code/tool/split identities before fresh proofs. Reconstruct live HANDVALIDATE-016 admission for the exact requested inventory; reject unsupported gestures or real scope.
- [x] Freeze independent held-out geometry/action targets and numerical gates before rendering. No refit, optimizer invocation, test leakage, changed reference geometry or post-hoc local regions.
- [x] Evaluate every selected action/null candidate on actual versus desired traces and target benefit, including every contact entry/exit, local blank/counter guards, exact contributors, physical footprint, spaces, overlaps and dt/arc/all-cubic subdivision convergence.
- [x] Execute all six previously unexecuted selected-action adversarial classes required by the old action evaluation, plus relevant frozen local guards. Preserve global 0.1 misses and independent local detection; missing controls block acceptance.
- [x] Require first/replay agreement for seeds 7, 19 and 41, with 5000 renders or 1800 seconds per seed including controls/refinement/replay and at most one diagnosed revision. Preserve failures and cumulative ledgers.
- [x] Implement a new explicit S1-action/null manifest reader with consumer-pinned report SHA and current evidence reconstruction. Preserve historical blocked reports and default legacy readers. Reject status-only, stale, incomplete or cross-tool admission.
- [x] Publish action-by-action active/null/unresolved dispositions, native-resolution examples and missing inventory. A null pass covers only the frozen experiment and requested constructions; it is not universal evidence that pen manipulation is unnecessary.
- [x] Keep CURRICULUM-005 blocked unless matching S1-action/null and every required primitive/gesture/reference prerequisite pass. No letter fitting, historical appearance approval, fatigue or default-mode promotion in this evaluation.

## Validation Gates

- [x] Independent current-code numeric proofs and complete scoped action/null evidence are required. Any required unresolved action blocks affected letter inventory. Real G0/G1/G2 and owner appearance review remain separate.
- [x] Fresh-process results match current pinned source, target, compiler, tool, controller and metric identities.
- [x] Missing or failed evidence blocks the affected scope; completion is not promotion.

## Bug Fixes

One diagnosed fixture-schema repair and a subsequent explicitly user-approved
scalar-type/constant-angle diagnostic repair are implemented. Each completed
control is journaled. All failed evidence is retained; no candidate, target,
compiler, controller, renderer or physical threshold changes.

## Risk + Rollback

A global image score can hide malformed contact, lost counters or copied geometry.
Use exact source/owner checks and frozen local guards. Revert only new opt-in behavior;
keep historical evidence, controllers and defaults unchanged. Review time is an estimate.

## Evidence

- [x] tdd:red-green and actual focused/expanded test results.
- [x] Frozen candidate/target/metric manifests, visible samples and cumulative budgets.
- [x] Clean-checkout fresh-process replay and current strict admission reconstruction.
- [x] `arrive plan check`, changed local-link checks and `git diff --check`.
- [x] `arrive pr check --strict --json` before an authorized merge; report local parser limitations separately from provider CI.
- [x] No unexecuted learning, owner review or provider CI counted as complete.

Pre-approval validation: 65 focused tests pass in 64.19 seconds. Expanded selection:
305 pass, 18 existing failures (12 previously recorded plus six folio-resolution
failures reproduced in clean pre-task `ac08daf`). Plan, 132 local links and diff
checks pass. Artifact doctor retains ten identical issues; no stale agent rules.
Both experiment attempts ran from clean committed-code worktrees. No provider
CI or merge is claimed; remaining acceptance work and repair approval are open.

## Changes Made

### 2026-09-08 — complete: Approved measurement repair, mixed scoped acceptance

- Final local focused tests: 73 pass in 110.49 seconds, including scoped-reader,
  forged-flag and exact prior-output regressions. Expanded selection: 310 pass,
  same 18 inherited failures in 162.07 seconds before three added evidence tests.
- Plan/diff/link checks pass; artifact doctor retains ten identical issues and
  agent rules have no stale outputs. Strict PR check executes but the installed
  parser returns `ids=[]` despite the ID in title/body/label; no provider CI or
  human review is claimed. Merge and clean-checkout receipts follow separately.
- Run-003 at frozen code `9100977` completes all nine heldouts, three contexts,
  closed-counter checks, four refinements and nine controls for seeds 7/19/41
  with exact fresh-process replay. No further repair or candidate search.
- Independent scoped null acceptance: underturn local maximum 0.044704.
  Overturn 0.099430 and compound 0.093600 exceed unchanged 0.05; their nominal
  geometry already misses targets. No dynamic action is inferred as necessary.
- The explicit reader admits underturn-only synthetic fixed-null scope, rejects
  required full inventory and keeps letter/real permissions false. Completion
  is not whole-inventory acceptance: `evaluation_complete=true`, `status=fail`.
- Swapped physical edge is now detected (endpoint displacement 0.2475 mm).
  All eight other controls evade global 0.1 but fail exact/local guards. The
  erased-counter control operates on an actual closed diagnostic enclosure;
  none of this admits active physical actions or learned letters.
- New 1086 + retained 1650 =2736 renders, 912/5000 per seed, cumulative time
  <260/1800 seconds each. Zero fitting; all frozen candidates unchanged.
- Manifest SHA `90f26d501d8860717bf8c40d394c7a25df679c8e63d4b58995ecba3e61fba2ef`;
  530 manifest artifacts. Prior actual images/traces and target/motion metrics
  remain byte/numerically identical; only measurement diagnostics change.
- [Completed results, samples and exact scope](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/action_evaluation/README.md).

### 2026-09-08 — authorized: Additional measurement-only repair and replay

- User approves the proposed diagnostic repair and remeasurement. Continue on
  the existing Advance branch; no preparatory refactor is required.
- Observed RED `2e79204`: five failures expose native-scalar rejection, constant
  angle classification, missing control checkpoints and incomplete prior costs.
- Normalize diagnostic scalars without changing their values; retain raw
  angular rates while enforcing the existing 1e-12 fixed-sample field checks.
  No physical validation or target threshold is loosened.
- Journal each completed control and preserve its evidence on interruption.
- Pin both failed reports in `continuation-v2.json`; retain 1650 renders,
  550 per seed, and their cumulative elapsed times. Freeze the unchanged
  `spec-v2.json`, all candidates/targets/controls and existing 5000/1800 limits.
  One explicitly authorized run-003, zero refitting, no further automatic retry.

### 2026-09-08 — stop: Additional measurement-only repair requires approval

- Run-002 at `8e578f8` measures nine heldouts, three contexts and a closed
  diagnostic counter for every seed, then fails at the physical-edge adapter.
  Actual NumPy scalar coordinates violate the strict physical sample type
  contract; no-render controller replay reproduces the type difference hidden
  by JSON serialization. Candidate/tool/renderer changes are not indicated.
- Review also finds exact-zero comparison of derived angular rate, while all
  actual angles pass the frozen 1e-12-degree check. Raw rounding-rate maxima
  reach 2.50748e-10 deg/s. Fix diagnostic classification, not physical limits.
- All existing motion/refinement/individual-contact and context checks pass;
  the target, nominal and every actual counter refinement are enclosed and
  blank. The new composite guard still fails, and missing controls prevent
  any independent null acceptance. No optimistic underturn approval.
- Fresh local loss maxima: underturn 0.044704, overturn 0.099430, compound
  0.093600. These partial target findings do not complete S1-action.
- Each seed replays 80 non-clock artifacts exactly; 488 run-002 artifacts
  verify. New 1062 + retained 588 = 1650 renders, 550 per seed, cumulative
  time <=148.318 seconds each. Zero optimization. All six candidate files
  remain byte-identical. The one automatic revision is exhausted.
- Stop report SHA `f7a6d96dccb418e058f7a5daf96bde8af754e76f3868e2d0a609f8b7afb51933`.
  Swapped-edge rendering, erased-counter/open-pocket negatives and persisted
  complete control numeric evidence remain missing; no final workbook.
- Request one additional scalar/constant-angle diagnostic repair, incremental
  control journaling and measurement-only replay within the same cumulative
  budgets. Do not execute another attempt without approval. Advance remains
  in progress, not merged; letters, real scope and default promotion are blocked.
- [Preserved evidence, diagnosis and samples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/action_evaluation/README.md).

### 2026-09-08 — fix: Preflight diagnostic grammar and retain cumulative costs

- Preserve run-001's 588 renders (196 per seed) and exact replay at `8151001`.
  Two seven-stroke pairings cannot fit the unchanged six-stroke carrier; the
  unexecuted counter placement also exceeds the lowered transform bound.
- Observed revision RED `55afb87` covers grammar preflight, retained budgets
  and support-terminal inventory. No source/controller/compiler repair needed.
- One diagnosed `spec-v2` protocol replaces only the two invalid carriers with
  capped compound/terminal and reverse-return probes; the seven executed cases
  remain identical. Seven-stroke transfer stays missing inventory. Translate
  the complete counter and its region together, preserving relative geometry.
- No fit, metric relaxation or target-quality selection. All failed files and
  time remain pinned in continuation accounting; no further revision allowed.

### 2026-09-08 — scope: Independent frozen-null evaluation

- TDD observed import failure committed at `6787023` before implementation.
- Freeze nine new same-family heldouts, unchanged absolute 0.05 and mechanical
  gates, plus three overlap/space contexts. No candidate fitting or selection.
- Execute six historical adversarial classes and three additional guards.
  Swapped-edge uses an explicit asymmetric physical-render diagnostic on the
  selected actual path, not a learned action or a candidate tool-mode change.
- A predeclared underturn/overturn enclosure tests actual closed blank topology;
  no open pocket substitution and no learned-letter claim. Any failed control,
  enclosure or refinement prevents affected acceptance, without revising limits.
- A new opt-in reader will reconstruct scoped null evidence. Existing readers,
  current foundation identities and letter/default behavior stay unchanged.

### 2026-09-08 — plan: Register the previously unexecuted action/null work

- HANDVALIDATE-016 registers this explicit follow-up instead of promoting old blocked action evidence.
