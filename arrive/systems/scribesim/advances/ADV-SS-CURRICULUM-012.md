---
advance:
  id: "ADV-SS-CURRICULUM-012"
  title: "Foundation Action or Null — Bounded Experiment on Accepted Shared Gestures"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","handflow","pathguide","nibcontact","handvalidate","tests"]
  started_at: "2026-09-08T03:50:00Z"
  implementation_completed_at: "2026-09-08T04:50:00Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api","migration"]
  evidence: ["tdd:red-green","tests:unit","local:bounded-null-experiment","local:fresh-process-replay"]
  model_usage: []
  status: complete
---

## Objective

Scope and execute the previously unexecuted selected-action/null experiment only after matching independent foundation admission. Prefer an explicit fixed-tool null hypothesis for the three accepted constructions unless a named local defect justifies one bounded physical pen action.

Implementation starts 2026-09-08 under the user's implementation and standing
update/merge instruction. Tidy assessment: no refactor is needed; new isolated
code preserves every pinned foundation and legacy module.
Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).

## Behavioral Change

Matching foundation admission, complete scoped candidate evidence and deterministic replay are required. Missing action coverage stays unresolved. Real fitting additionally requires live G0 and accepted real lower layers.

## Component Impact

`scribesim/curriculum/foundation_actions.py`, existing explicit foundation admission APIs, focused tests and `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/actions/`.
Existing components remain incubating; no separate controller or renderer.

## Dependencies

- [ADV-SS-HANDVALIDATE-016](ADV-SS-HANDVALIDATE-016.md)
- [ADV-SS-CURRICULUM-004](ADV-SS-CURRICULUM-004.md)

## Planned Implementation Tasks

- [x] branch: confirm implementation/update/merge authorization and preserve unrelated work.
- [x] tidy: assess minimal behavior-preserving preparation separately.
- [x] test: commit observed failing behavioral tests before implementation.
- [x] Require a consumer-pinned HANDVALIDATE-016 report, live primitive/gesture/tool/controller identities and an explicit required inventory. A completed Advance or historical HANDVALIDATE-014 stop is not admission.
- [x] Investigate and freeze the smallest useful action/null scope before any target access. Name the local failure if testing rotation, edge release or finishing; do not invent dynamic work when the fixed tool already satisfies the scoped construction.
- [x] Freeze independent project-authored targets, train/development/held-out splits, controls, metrics and numerical limits. A null candidate needs affirmative scoped target/transfer/contact evidence, not merely a constant action dictionary or absence of selected proposals.
- [x] Keep primitive curves and shared gesture attachments immutable. The foundation schema rejects dynamic tools: any necessary explicit versioned action extension must preserve old replay and pass physical bridge/ownership/refinement tests first. No bypass of the legacy or foundation grammar.
- [x] For a justified action, fit only the predeclared bounded profile and select on development, never held-out pixels. Otherwise evaluate the predeclared null without optimization. Report active/null/unresolved separately for each required action and construction.
- [x] Execute seeds 7, 19 and 41 with first/replay/control/refinement costs charged: at most 5000 renders or 1800 seconds per seed, one diagnosed revision. Preserve failed attempts and cumulative accounting; no open-ended search or threshold relaxation.
- [x] Publish equal-scale native-resolution target/nominal/desired/actual examples, selected candidate bytes, source/compiled ownership and local counter/blank evidence. Complete actual work or record an explicit stop; scaffolding does not complete a learning task.
- [x] Freeze selected candidate manifests for HANDVALIDATE-017. No S1-action, letters, words, fatigue, default switch or real-hand approval is granted here.

## Validation Gates

- [x] Matching foundation admission, complete scoped candidate evidence and deterministic replay are required. Missing action coverage stays unresolved. Real fitting additionally requires live G0 and accepted real lower layers.
- [x] Fresh-process results match current pinned source, target, compiler, tool, controller and metric identities.
- [x] Missing or failed evidence blocks the affected scope; completion is not promotion.

## Bug Fixes

No existing runtime behavior is repaired or changed. The new opt-in experiment
separates complete negative evidence from null acceptance; no refitting or retries.

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

## Changes Made

### 2026-09-08 — merge: Local completion receipt

- Completion commit `087be8c` passes all 48 focused tests in a clean detached
  checkout (66.79 seconds), including the three saved-evidence regressions.
- Locally merged into `master` with `--no-ff` as `6edc81d` under the standing
  update/merge instruction. Plan validation passes after merge. No push,
  provider CI or human acceptance is implied; the strict parser limitation
  remains recorded. Temporary validation worktree removed after cache cleanup.
- Post-merge pinned selected-evidence reconstruction passes with review allowed,
  whole null unsupported and both action/letter acceptance false. The existing
  foundation readiness gate still passes unchanged.

### 2026-09-08 — complete: Mixed fixed-null result, no action acceptance

- Executed eleven frozen train/development/held-out fixtures, three mechanical
  contexts, four refinements and six declared controls for seeds 7, 19 and 41.
  All candidate bytes and pinned lower-layer identities remain unchanged.
- Underturn supports the scoped null hypothesis (worst local loss 0.045681).
  Overturn (0.100653) and compound curve (0.097080) exceed the unchanged absolute
  0.05 cap. Whole-model `null_supported=false`; completion is not acceptance.
- Overturn/compound target mismatch is already present in frozen nominal
  geometry. Investigate shared-geometry/target fidelity before prescribing
  dynamic actions. No added rotation, partial-edge or finishing fit is justified
  by this experiment alone. Independent HANDVALIDATE-017 remains planned.
- All motion/contact/refinement and declared local controls pass. All five
  measured negative images evade the global 0.1 detector; exact guards catch
  them. Partial-edge rejection is a schema test, not physical edge validation;
  open pockets are not closed-letter counters.
- Actual clean-code execution at `623a687` uses 1140 renders, 380 per seed
  including replay, each below 1800 seconds; zero optimization and retries.
  Each seed replays 88 non-clock artifacts exactly. All 536 manifest artifacts
  verify, including immutable report SHA
  `ba2d46377b59787065486738e861aaea00c042cf0be2704072821aed3ac0fa3a`.
- Observed RED was committed at `77ff696` before implementation. Focused tests:
  48 pass; expanded: 284 pass with the same 12 inherited failures. Clean
  committed-code focus passed 45 before three saved-evidence regressions were
  added. Detailed logs, budget receipts and disposition tables are preserved.
- `arrive plan check`, local links and diff checks pass. Artifact doctor has
  the same 10 inherited issues; no stale agent rules. Strict PR metadata check
  was executed but the installed parser returns `ids=[]` despite the Advance
  ID in title, body and label. No provider CI, push or owner review is claimed.
- [Results and samples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/actions/README.md),
  [verification](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/actions/verification.json),
  [layered sample index](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/index.html).
- The selected-evidence reader reconstructs current source admission, numeric
  evidence and exact replay but returns `S1_action_accepted=false` and
  `letter_training_allowed=false`. No letter, word, fatigue, real-hand or
  default-runtime promotion occurs.

### 2026-09-08 — scope: Predeclared fixed-tool null, no geometry or action fitting

- Live HANDVALIDATE-016 admission verifies before new target access. Prior
  nominal target losses around 0.099 for overturn/compound exceed the existing
  absolute null cap 0.05 despite passing relative foundation improvement.
- Freeze the same independent target family with eleven train/development/
  held-out cases, including new transforms and pairings. Keep the absolute 0.05
  cap and apply it locally as well; do not substitute actual/desired tracking
  loss or relative improvement. New target pixels are not used to choose a
  candidate, actions or revised thresholds.
- One fixed null candidate per seed is selected before any target render.
  A negative result is a completed experiment, not evidence for a particular
  dynamic pen action. Diagnose target/nominal and nominal/actual separately.
- Partial-edge requests are outside this full-edge mode and rejected by the
  unchanged grammar. Active edge sensitivity, closed-letter counters and
  independent S1-action remain unexecuted; no physical renderer extension.

### 2026-09-08 — plan: Register the previously unexecuted action/null work

- HANDVALIDATE-016 registers this explicit follow-up instead of promoting old blocked action evidence.
