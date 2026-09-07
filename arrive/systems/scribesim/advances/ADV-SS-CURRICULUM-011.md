---
advance:
  id: "ADV-SS-CURRICULUM-011"
  title: "Foundation Gesture Learning — Underturn, Overturn and Compound Transfer"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","evo","handflow","handvalidate","tests"]
  started_at: "2026-09-07T15:53:11Z"
  implementation_completed_at: "2026-09-07T19:21:25Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  model_usage: []
  status: complete
---

## Objective

Actually learn reusable fixed-tool continuous return constructions, then demonstrate unseen combinations without fitting letters or copying independent curves.

**Work kind:** Learning implementation and bounded experiment. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
**COMPLETE as learning, not S1-gesture acceptance.** The explicitly approved
diagnostic lift repair remeasures seed 7 without refitting and finishes the
unchanged seeds 19/41. All required held-out/local/motion/control/replay proofs
pass. Independent HANDVALIDATE-016 remains next.

## Behavioral Change

The deliverable and acceptance boundary are specified in the tasks and gates below.
This record belongs to `td018-foundation-repair`; existing completed records and
failed evidence remain unchanged.

## Component Impact

- `scribesim/curriculum/foundation_gestures.py` — bounded shared-scale fitting, frozen no-refit continuation and explicit diagnostic lift preservation.
- `scribesim/curriculum/gesture_targets.py` — independent analytic target definitions.
- `scribesim/curriculum/gesture_refinements.py` — exact subdivision of validated compiled sources without legacy-cap fallback.
- `tests/test_foundation_gestures.py` — 32 passing checks, including all eight former lift reproductions and no-refit/source-integrity guards.
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/gestures/` — immutable attempts, candidates, samples and explicit stop decision.

Existing components remain incubating. No separate renderer/controller or new component.

## Dependencies

- [ADV-SS-HANDVALIDATE-015](ADV-SS-HANDVALIDATE-015.md)
- [ADV-SS-GESTURE-002](ADV-SS-GESTURE-002.md)
- [ADV-SS-HANDFLOW-011](ADV-SS-HANDFLOW-011.md)

Plan dependencies order work, not runtime admission. Consume only matching,
independently validated layer/tool/code identities. Real fitting additionally
requires live G0 and accepted real lower layers; source uncertainty and locked
test isolation are not repaired by this synthetic phase.

## Planned Implementation Tasks

- [x] branch: continuing the authorized update-and-merge workflow on `advance/ss-curriculum-011`; initial worktree clean.
- [x] tidy: no preparatory refactor needed; isolated new modules preserve every pinned lower-layer identity.
- [x] test: red commits `d20e17e`, `7e5af73`, `7a2b083` precede implementation/revision; `f4f2504` adds eight red lift reproductions, and `8e5d258` adds no-refit continuation guards; `ba2c16c` makes all 32 checks pass.
- [x] Require the live matching HANDFLOW-011 no-refit reevaluation pass, repaired execution and audited grammar. Freeze report SHA `e17be78e54d91b73076f17ece07cb6c530f0088ac32bc0e2db76a32ac12ebb89` through `scribesim.handvalidate.tangent_evaluation.require_readiness`, explicitly declare required families and execute `curve-tangent-v1`. The retained HANDVALIDATE-015/legacy reader cannot admit this mode. Freeze every primitive curve and fixed action/tool parameter before gesture optimization.
- [x] Predeclare required underturn, overturn and compound constructions with independent synthetic targets and train/development/held-out topology or attachment pairings. Do not treat the old supplied i/u recipes as learned letters.
- [x] Fit only shared audited attachment/placement transforms: seed 7 selects stem/rise/return scales `[0.85,1.15,0.85]`; reference topology stays fixed by the audited grammar. No primitive refitting, per-letter residuals, profile activation, hidden finishing pass, context learning or expanded-cap bypass. Seeds 19/41 now select the same parameters under the unchanged protocol; seed 7 is not refitted.
- [x] Run seeds 7/19/41 and at most three ablations within fixed budgets. Include fixed and placement-only controls; development selects before held-out scoring. A representable exact-grid target or scale-only transfer is insufficient evidence.
- [x] Publish corrected native 900-DPI initial/target/fitted/sampled/actual sheets and constituent/direction/port overlays for every seed. All paired columns now preserve explicit lifts. Earlier false-connector evidence stays quarantined and linked, not overwritten.
- [x] Freeze selected candidates for HANDVALIDATE-016. Remain in progress if only tooling or blocked admission is delivered; do not finish this learning Advance without its actual bounded experiment.
- [x] evidence: commands, identities, no-refit checks, cumulative budgets and scope are recorded in the gesture README, run-003 report and `continuation-verification.json`; the historical stop remains immutable.

## Validation Gates

- [x] Every required construction and seed achieves frozen held-out benefit with shared lower-layer identities unchanged; topology-disjoint transfer is present.
- [x] Actual execution preserves continuous contact within a gesture, explicit lifted separation and exact overlap owners; stable endpoint/refinement checks remain mandatory.
- [x] No learned alphabet, historical hand or S1-action claim is inferred. Missing required gesture coverage blocks the corresponding inventory and final acceptance.

## Budget and Stop Rules

Use [Addendum B Section 7](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#7-budgets-and-stop-rules):
seeds 7/19/41; at most three ablations; 5000 total renders or 1800 seconds per ablation/seed per attempt; one diagnosed revision, all setup and direct/sampled/actual/presentation work charged.
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
Review estimate is 40 minutes, not measured review or approval.

## Evidence

- [x] Frozen inputs, independent targets/controls, criteria and identities; `continuation-v1.json` pins explicit user approval, original candidates and unchanged search/criterion functions.
- [x] Actual work/budget ledger, corrected equal-scale samples, retained failures and recorded replay commands. New work uses 6594 renders; retained work adds 3121.
- [x] Focused red/green tests and clean-checkout execution at `ba2c16c`: 32 focused passes; local and clean expanded suites both have 249 passes and exactly 12 inherited failures. All nine seed/ablation first/replay pairs match 54 artifacts exactly.
- [x] `arrive plan check`, changed local links and `git diff --check` pass. All 398 historical artifacts and 992 current manifest entries, current code identities and no-refit byte comparisons verify. Doctor retains exactly ten inherited issues; generated rules are not stale.
- [x] Before an authorized merge run `arrive pr check --strict --json`; report installed ID-parser limitations separately from provider CI.
- [x] Scope-qualified learning result; no independent S1-gesture, human review or provider CI counted as complete. Strict PR check was invoked before local merge but the installed parser returns `ids=[]` for the repository’s ADV-SS-* IDs; this limitation is not a provider CI pass.

## Bug Fixes

- Fixed the legacy-schema subdivision adapter's four-occurrence failure by subdividing validated compiled sources; the foundation grammar cap and admitted lower-layer code are unchanged. Nonsubdivided binding matches the old runtime's complete plan, trace, groups and metrics in regression tests.
- **Fixed in the approved continuation:** `nominal()` and `target()` previously flattened every primitive segment into one all-contact trajectory. The shared painter consequently sweeps ink between explicitly lifted gesture instances. Isolated training/development is unaffected, but paired held-out ratios and three presentation columns are invalid. The actual controller still executes the lifts correctly. Eight no-render tests reproduced this for all four held-out fixtures and now pass. Explicit pen-up samples are inserted only between gesture owners; every existing contact point and continuous primitive join is preserved. Per-fixture contact-run gates reject a return to flattened paired diagnostics.

## Historical Execution Stop (Superseded by Approved Continuation)

Run-001 (`f63e1f6`) stops at the subdivision adapter after 69 renders.
The one permitted diagnosed revision (`a56908a`) runs seed-7 fixed,
placement-only and primary attachment first/replay processes. Primary selection
is `[0.85,1.15,0.85]`; its 54 non-wall artifacts replay byte-identically. All
primitive and action dictionaries remain unchanged. Visual inspection then
finds false diagnostic connectors. The per-worker automatic `pass` is **not
accepted evidence**: the containing attempt has no completion report or S1.
Seed-19 fixed execution is interrupted and its final 106-render counter retained;
seed-19 learning and all seed-41 work are unexecuted.

Total retained usage is **3121 renders / 229.715709 worker-seconds**, including
both attempts, replays and interruption. Seed-7 primary used 2358/5000 renders;
the stop is an invalid proof and exhausted revision allowance, not budget exhaustion.

The following continuation required and subsequently received explicit approval: repair diagnostic contact-run encoding,
remeasure the already frozen seed-7 candidates **without refitting**, preserve
targets/splits/criteria and every failed artifact, then finish untouched seeds
19/41 under the original search. Do not start HANDVALIDATE-016 or merge this
learning Advance before valid all-seed proofs. The second diagnostic repair/rerun
was explicitly approved by the user rather than inferred from the original allowance.

## Changes Made

### 2026-09-06 — plan: Prioritize reliable learned stroke foundations

- Added the bounded work to Pass 15 `td018-foundation-repair`.
- Implementation and acceptance remain pending under Addendum B.

### 2026-09-07 — partial implementation and quarantined experiment

- `d20e17e` / `7e5af73`: initial failing contract/selection/proof/CLI tests.
- `f63e1f6`: frozen protocol and runner, then retained run-001 stop.
- `7a2b083` / `a56908a`: red/green cap-preserving source subdivision revision.
- `f4f2504`: preserve interrupted run-002 and frozen candidates; eight new red lift-schedule reproductions.
- Local and clean-checkout expanded suites at `a56908a`: 235 passed, the same 12 pre-existing failures as HANDFLOW-011. Eighteen new tests passed then; eight later failing reproductions are deliberately separate and unresolved.
- No merge, push, provider CI, completed review, S1-gesture or learned-letter claim.

## Approved Continuation — Complete

- User authorization: repair diagnostic lift handling, remeasure frozen seed 7 without refitting, then finish seeds 19/41. Frozen in `continuation-v1.json`.
- `8e5d258` / `ba2c16c`: red/green continuation tests and repair. No preparatory refactor or lower-layer modification was necessary.
- Run-003 passes all required constructions/occurrences at seeds 7/19/41. Shared scales are [0.85,1.15,0.85]; fixed and placement-only controls do not meet all learning gates.
- Held-out pair ratios are 0.157574 / 0.157807 / 0.132465 / 0.066255; maximum occurrence-local ratio is 0.408835 (<0.75).
- Actual/desired loss <=0.010016; corridor <=0.007936 mm; refinement endpoint difference <=0.005718 mm. All ownership, blank-pocket and eight adversarial guards pass; historical global-negative misses remain reported.
- All six seed-7 candidate/selection files are byte-identical to run-002, with zero selection/training scoring. Its 42 sampled/actual PNGs, 21 trace archives and 27 isolated diagnostic PNGs are unchanged.
- Every seed/ablation replays 54 artifacts byte-for-byte. 6594 new + 3121 retained = 9715 renders across nine budgets; largest individual use is 2592/5000 renders. Old interruptions and failures are retained.
- Current report SHA: `7dbec24cd0bf82e9f45d55c5417cf2c36551ee7dfe6294bd7b0c409219066911`.
- [Current samples and verification](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/gestures/README.md). Independent HANDVALIDATE-016 is next, not automatically completed by these results.
- Local merge follows the user’s standing update-and-merge instruction. No push, provider CI, human review, learned alphabet/actions/words or historical-hand acceptance is claimed.

## Check for Understanding

1. Which exact evidence and identities permit this Advance's experiment to run?
2. What visible learned or independently evaluated result distinguishes completion from scaffolding?
