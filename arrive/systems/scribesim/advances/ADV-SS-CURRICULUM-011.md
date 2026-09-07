---
advance:
  id: "ADV-SS-CURRICULUM-011"
  title: "Foundation Gesture Learning — Underturn, Overturn and Compound Transfer"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","gesture","evo","handflow","handvalidate","tests"]
  started_at: "2026-09-07T15:53:11Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  model_usage: []
  status: in_progress
---

## Objective

Actually learn reusable fixed-tool continuous return constructions, then demonstrate unseen combinations without fitting letters or copying independent curves.

**Work kind:** Learning implementation and bounded experiment. Follows [TD-018 Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md).
Implementation started after live matching primitive admission. Seed-7 fitting ran,
but visual review invalidated paired nominal/target diagnostics. This Advance stays
**in_progress, unmerged**. The user explicitly approved diagnostic lift repair,
no-refit seed-7 remeasurement and finishing untouched seeds 19/41 on 2026-09-07.
The continuation is running under unchanged targets, splits, search and criteria;
completion and acceptance are not yet claimed.

## Behavioral Change

The deliverable and acceptance boundary are specified in the tasks and gates below.
This record belongs to `td018-foundation-repair`; existing completed records and
failed evidence remain unchanged.

## Component Impact

- `scribesim/curriculum/foundation_gestures.py` — bounded shared-scale fitting and frozen evidence runner; paired diagnostic lift handling still needs repair.
- `scribesim/curriculum/gesture_targets.py` — independent analytic target definitions.
- `scribesim/curriculum/gesture_refinements.py` — exact subdivision of validated compiled sources without legacy-cap fallback.
- `tests/test_foundation_gestures.py` — 18 passing checks plus eight deliberately failing reproductions of the remaining lift bug.
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
- [x] test: red commits `d20e17e`, `7e5af73`, `7a2b083` precede implementation/revision; the newly discovered remaining defect has eight red reproductions in `f4f2504`, not a green claim.
- [x] Require the live matching HANDFLOW-011 no-refit reevaluation pass, repaired execution and audited grammar. Freeze report SHA `e17be78e54d91b73076f17ece07cb6c530f0088ac32bc0e2db76a32ac12ebb89` through `scribesim.handvalidate.tangent_evaluation.require_readiness`, explicitly declare required families and execute `curve-tangent-v1`. The retained HANDVALIDATE-015/legacy reader cannot admit this mode. Freeze every primitive curve and fixed action/tool parameter before gesture optimization.
- [x] Predeclare required underturn, overturn and compound constructions with independent synthetic targets and train/development/held-out topology or attachment pairings. Do not treat the old supplied i/u recipes as learned letters.
- [x] Fit only shared audited attachment/placement transforms: seed 7 selects stem/rise/return scales `[0.85,1.15,0.85]`; reference topology stays fixed by the audited grammar. No primitive refitting, per-letter residuals, profile activation, hidden finishing pass, context learning or expanded-cap bypass. This is partial execution, not all-seed completion.
- [ ] Run seeds 7/19/41 and at most three ablations within fixed budgets. Include fixed and placement-only controls; development selects before held-out scoring. A representable exact-grid target or scale-only transfer is insufficient evidence.
- [x] Publish native 900-DPI initial/target/fitted/sampled/actual sheets and constituent/direction/port overlays, with an explicit quarantine warning: paired initial/target/fitted columns contain false connectors; sampled/actual columns preserve the lifts. These are retained failures, not accepted comparison evidence.
- [ ] Freeze selected candidates for HANDVALIDATE-016. Remain in progress if only tooling or blocked admission is delivered; do not finish this learning Advance without its actual bounded experiment.
- [x] evidence: commands, identities, cumulative interrupted-worker accounting and scope are recorded in the gesture README and `validation-stop.json`; remaining work stays unchecked.

## Validation Gates

- [ ] Every required construction and seed achieves frozen held-out benefit with shared lower-layer identities unchanged; topology-disjoint transfer is present.
- [ ] Actual execution preserves continuous contact within a gesture, explicit lifted separation and exact overlap owners; stable endpoint/refinement checks remain mandatory.
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

- [x] Frozen inputs, independent targets/controls, criteria and scope-specific identities; paired trajectory encoding is explicitly invalidated rather than silently repaired.
- [x] Actual work/budget ledger, equal-scale samples, failures and recorded replay commands; further execution is blocked pending approval.
- [x] Focused red/green tests and clean-checkout execution at `a56908a`; seed-7 first/replay manifests match for every ablation. Eight later red bug reproductions remain unresolved.
- [x] `arrive plan check`, 22 changed local links and `git diff --check` pass. All 398 saved artifact hashes and current code identities verify. Doctor retains exactly ten inherited issues; generated rules are not stale.
- [ ] Before an authorized merge run `arrive pr check --strict --json`; report installed ID-parser limitations separately from provider CI.
- [x] Scope-qualified partial result; no unperformed learning, valid all-seed transfer evaluation, merge or human review counted as complete. Strict PR/provider checks are deferred because no merge is attempted.

## Bug Fixes

- Fixed the legacy-schema subdivision adapter's four-occurrence failure by subdividing validated compiled sources; the foundation grammar cap and admitted lower-layer code are unchanged. Nonsubdivided binding matches the old runtime's complete plan, trace, groups and metrics in regression tests.
- **Remaining:** `nominal()` and `target()` flatten every primitive segment into one all-contact trajectory. The shared painter consequently sweeps ink between explicitly lifted gesture instances. Isolated training/development is unaffected, but paired held-out ratios and three presentation columns are invalid. The actual controller still executes the lifts correctly. Eight no-render tests reproduce this for all four held-out fixtures.

## Execution Outcome and Stop

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

Next requires explicit approval: repair diagnostic contact-run encoding,
remeasure the already frozen seed-7 candidates **without refitting**, preserve
targets/splits/criteria and every failed artifact, then finish untouched seeds
19/41 under the original search. Do not start HANDVALIDATE-016 or merge this
learning Advance before valid all-seed proofs. A second diagnostic repair/rerun
is not silently inferred from the original one-revision allowance.

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

## Check for Understanding

1. Which exact evidence and identities permit this Advance's experiment to run?
2. What visible learned or independently evaluated result distinguishes completion from scaffolding?
