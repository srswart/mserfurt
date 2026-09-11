---
advance:
  id: "ADV-SS-CURRICULUM-006"
  title: "Letter Context — Bounded Stroke Changes Within Words"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","evo","gesture","handvalidate","tests"]
  started_at: "2026-09-06T04:10:57Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 60
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration"]
  model_usage: []
  status: in_progress
---

## Objective

**Current direction, 2026-09-10:** retain the validated affine pilot as foundation
evidence and pause its P3 rankings/P4–P5 preference selection. Follow
[TD-018 Addendum D](../../../../docs/tech-direction/TD-018-addendum-d-stroke-context-transitions.md)
and the planned `td018-stroke-context` phase for previous/next-conditioned
entry/body/exit forms and explicit join/retrace/lift transitions. No new
implementation, wider bounds, physical budget or fitting is authorized here.

Determine whether small following-neighbor-conditioned stroke changes improve
synthetic n/u/m composition beyond spacing alone, preserving shared primitives
and letter identity. Unchanged strokes or spacing-only sufficiency are valid outcomes.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
Prepared design: [TD-018 Addendum C](../../../../docs/tech-direction/TD-018-addendum-c-letter-context.md).
Owner authorizes P1/P2a and P2b's bounded width/advance geometry and wider frame,
leaving changes uncommitted. Geometric and desired-plan preflight is implemented;
the owner now approves the 45-minute combined per-seed physical-validation budget.
The opt-in physical runner, independent reader, controls and ledger are implemented.
The authorized three-seed attempt stops on disk exhaustion during seed 41's
replay. Its separately authorized recovery now passes all 244 replay worker
checks and exact artifact equality within the original cumulative budget.
The separately approved measurement-only reader correction now completes full
independent inspection: 1464 cases and 324 presentations pass, with exact replay
equality for all three seeds. The bounded P2b mechanical gate is cleared without
changing saved evidence, frozen readers, targets, frames, thresholds or budgets.
P3's pinned 54-image page, export/validator and proposed objective/budget remain
preserved, but the owner pauses this exercise because the narrow affine choices
are not meaningfully distinguishable. No rankings are inferred from that feedback
or overwritten in browser drafts. The old P3/P4/P5 route and fitting stay paused;
new work starts with GESTURE-004's read-only span/contact investigation. Existing
budget shortfalls remain unresolved; a phase name does not reset their debits.
The approved derived-only corner repair clears all six preflight rejections in
snapshot-003: 244/244 desired plans pass on the unchanged grid. Appearance review
and fitting remain subject to their separate prerequisites.

## Behavioral Change

The proposed first pilot compares context-off, spacing-only and stroke-context
arms using six shared rule cells and composition-disjoint test triples. It must
show exactly which constituent strokes change and why, without interpreting
placement alone as stroke learning. Preparation does not confer S2/S3/real admission.

## Component Impact

- `docs/tech-direction/TD-018-addendum-c-letter-context.md` (prepared design).
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/preparation-001/` (read-only audit and non-executable proposal).
- `scripts/current_foundation_readiness.py`, its focused tests and `letter_context/readiness-v1/` (P1 pinned baseline-only consumption contract).
- `scripts/letter_context_contract.py`, `scripts/letter_context_evidence.py`, `tests/test_letter_context_contract.py` and `letter_context/null-contract-v1/` (P2a null contract, independent sidecar verification and archived-output binding).
- `scripts/letter_context_variants.py`, `scripts/letter_context_variant_evidence.py`, `tests/test_letter_context_variants.py` and `letter_context/bounded-geometry-v1/` (P2b approved geometric envelope, derived planning, frozen frame/windows and physical budget preflight).
- `scripts/letter_context_dimension_evidence.py`, `tests/test_letter_context_dimension_evidence.py` and `physical-validation-v1/dimension-check-v1/` (separately pinned, measurement-only correction and complete composite inspection; frozen prior readers unchanged).
- `scripts/letter_context_review.py`, `scripts/templates/letter_context_review.html`, `tests/test_letter_context_review.py` and `letter_context/owner-review-v1/` (training-only saved-image review, ordinal-label validation and proposed objective/budget packet; no fitting).
- Future opt-in compiler/learning/independent-reader adapters and focused tests,
  owned by existing curriculum/gesture/handvalidate components; no nonidentity context runtime yet.

Use tracked modules and scoped test selectors; clean-checkout imports are required.
No production renderer, frozen core source, old readiness reader or component
stage changes. Do not add spec-*.json to the old identity-scanned training tree.

## Dependencies

- [ADV-SS-CURRICULUM-005](ADV-SS-CURRICULUM-005.md)
- [ADV-SS-GESTURE-003](ADV-SS-GESTURE-003.md)
- [ADV-SS-CURRICULUM-015](ADV-SS-CURRICULUM-015.md)
- [ADV-SS-HANDVALIDATE-024](ADV-SS-HANDVALIDATE-024.md)

Current approved input is CURRICULUM-015's connected-v1 n/u/m candidate, physically
verified in HANDVALIDATE-024, including whole-primitive internal subdivision and
all three seed/replay pairs. Actual appearance of known and six held-out pairs is
approved. These are fixed placements, not learned context or historical style truth.

The preparation audit rechecks 1,808 artifact hashes, 206 current core identities
and owner/source pins. Both old finer-scale and standalone-stem readiness calls
reject their original pinned manifests; three compiler/action sources changed.
The current schema also explicitly rejects nonempty context rules. Only one
canonical recipe per letter exists; there are no admitted contextual alternatives.

First establish a versioned current-source primitive/gesture/fixed-action/letter
clearance contract using applicable H024 evidence and an explicit gap inventory.
Do not repair these blocks by updating old reader hashes or treating owner KEEP
as permission to fit. New variant/lineage semantics, targets and budget need
approval and independent evidence. Synthetic scaffold work with explicitly
unaccepted inputs is not accepted-layer training; real-source fitting still
requires live G0 and matching accepted lower layers. Existing flags remain false.

## Planned Implementation Tasks

Current next work is the planned [GESTURE-004](ADV-SS-GESTURE-004.md) →
[GESTURE-005](ADV-SS-GESTURE-005.md) → [CURRICULUM-016](ADV-SS-CURRICULUM-016.md) →
[HANDVALIDATE-025](ADV-SS-HANDVALIDATE-025.md) →
[HANDVALIDATE-026](ADV-SS-HANDVALIDATE-026.md) sequence. The old unchecked P3–P5
tasks below are historical paused work, not permission to resume selection.

- [x] workflow: owner explicitly requests leaving P2a changes uncommitted; preserve prior dirty work, no branch/commit/merge.
- [x] prepare: current-source read-only audit and explicit gate/coverage debt.
- [x] prepare: exact proposed rule grid, text partitions, controls, frames and bounded execution contract in Addendum C.
- [x] tidy P1: preserve unrelated work, frozen core, source reports and old readers; add an opt-in script only.
- [x] test P1: fail-closed current-source readiness, raw occurrence lineage, explicit consumer scope and immutable snapshot before feature implementation.
- [x] test P2a: exact null compilation/planning, independent lineage reconstruction, archived binding and fail-closed scope tests before implementation.
- [ ] test P2b–P5: nonidentity derivation/ownership, physical null/variant replay, text isolation, frame and budget tests before their implementation.
- [x] feat/fix P1: implement current-source consumption clearance and inventory only genuinely missing lower-layer proofs; no old-reader repinning.
- [x] feat/fix P2a: identity-only six-cell following-entry contract, canonical/derived occurrence sidecars, independent reader and exact unchanged compile/plan/timing interface; old connected-v1 context rejection intact.
- [x] feat/fix P2b geometry: approved width choices 0.97/1/1.03, independent advance deltas -0.05/0/+0.05 and wider frame; derived occurrence/port contract and verified planning adapter. No canonical mutation, joins, new actions or word keys.
- [x] test P2b preflight: strict bounds/lineage, null equivalence, shared-cell enumeration, sealed-text exclusion, full-nib frame/window checks and fail-closed physical budget gate.
- [x] fix P2b derived sampling: remove only ordinary roundoff duplicates at explicitly owned corners for 0.97-width m under subdivision; snapshot-003 passes the same 860 geometry/244 plan inventory, with all 238 prior passing timings and 52 null bundles exact. Canonical geometry, grid, windows and thresholds remain unchanged.
- [x] approve P2 physical budget: owner approves 2700 seconds per seed (7/19/41), including first/replay, with 5000 renders and zero automatic retries/revisions; carry P2b debits into the combined C006 seed accounting.
- [x] implement P2 physical preparation: opt-in derived-plan runner, immutable contract, supervisor permits/deadlines, persistent reservations, independent raw/saved-pixel reader and fifteen negative controls. Archived/stub software tests do not count as new physical runs.
- [x] execute the one approved P2 physical attempt: run-001 starts all three seeds; preserve the ENOSPC failure during seed-41 replay without retrying or changing frozen inputs.
- [x] evaluate P2 physical: original/recovery contracts, controls and combined budgets remain frozen; dimension-check-v1 independently verifies all 1464 saved cases, 324 presentations and exact replays after the authorized storage recovery. Known-base regressions keep their frame; no further controller, raster or fitting calls.
- [x] prepare P3 review packet: owner authorizes read-only reuse of 54 training-pair previews; pin grid/source images and preserve full equal-scale frames; rank/tie/exclude/notes export and fail-closed validator; proposed objective and carried-forward budgets.
- [ ] complete P3: receive and confirm actual owner rankings/approval; freeze labels/objective/exclusions/ties and a feasible exact staged evaluation/reuse inventory with authorized remaining or revised budgets. No preference labels or objective approval are invented by the packet.
- [ ] feat/evaluate P4: at most 54 separable training grid rows, deterministic shared-rule selection, identity allowed. Development is safety-only with no retuning; freeze one selected table before opening six sealed triples.
- [ ] evaluate P5: context-off, best spacing-only and stroke-context arms plus matched-advance shape comparisons; unseen-triple reading/appearance and raw independent verification. No new S3/real acceptance inferred.
- [ ] budget P3–P5: reconcile the remaining approved 5000-render/2700-second combined seed allowances after physical validation and recovery; authorize and freeze a feasible preview/selection/evaluation inventory before spending. No reset or automatic retries/revisions.
- [ ] evidence: enlarged pair/triple actual and nominal proofs, canonical primitive deltas, rule IDs, exact coverage and all negative outcomes; no word sheets or fatigue in this pilot.
- [ ] evidence: record red/green commands, actual budget use, hashes, scope and outcome before marking completion.

## Validation Gates

- [ ] First-pilot support requires preferred contextual stroke changes beyond spacing alone, preserving primitive lineage, letter identity, ports/counters and approved bounds; this is not automatic S3.
- [ ] Context effects cannot be explained solely by spacing or by per-word cached shapes; unseen combinations must be generated without reference-image access.
- [ ] Fresh-process replay, deterministic rule resolution and exact derived-geometry/contact ownership pass through every primitive/gesture/profile occurrence; canonical checkpoints stay byte-frozen. No joins/ligatures are introduced.
- [ ] Context-enabled output meets pre-approved criteria and unseen-triple reading/preference review; spacing-only sufficiency, identity selection or no preference is reported honestly, not relabeled successful context learning.

## Invariant Impact

Exact text, source uncertainty, split isolation, shared-parameter lineage,
deterministic compilation and actual trajectory ownership remain mandatory.
Synthetic mechanics, real-source fitting and human appearance acceptance are
separate. Layer gates S0–S4 supplement, not replace, G0–G4.

## Risk + Rollback

A layer can disguise copied character geometry or memorized words as learning.
Reject unrestricted residuals and per-instance lookup; retain frozen lower-layer
checkpoints, ablations and failed evidence. Revert only the new opt-in model,
not historical snapshots or production defaults. Proposed transforms and widened
frame require approval before use. Preparation does not release context training.

## Evidence

- [x] P2a: 80 exact context-off/six-identity compile/plan/timing comparisons; 240 archived run bindings, 480 original image bindings and 24 exact known-base reference matches. No fresh physical null replay is claimed.
- [x] P1: externally pinned snapshot and read-only reinspection; 240 archived-run occurrence audits, complete four-primitive/three-gesture/fixed-action/n-u-m inventory, no baseline inventory gaps. No arbitrary primitive, transformed-context or S1/S2 admission.
- [x] Read-only preparation audit: current artifact/source/owner pins, expected old-reader rejection and compiler refusal of context; zero controller/raster/optimizer calls.
- [x] Baseline compile-only topology for 21 strings; nominal containment for twelve triples. Only mmm fails the old frame; all fit proposed wider frame. No variant or actual-motion preflight claimed.
- [ ] Frozen fixtures, splits, constraints, objective/limits and model/code identities.
- [ ] Before/after practice sheets, decomposition proofs and transfer results.
- [ ] Replay and neutral direct/sampled/actual comparisons; real review only when performed.
- [x] P1: `arrive plan check`, generated-rule check, `git diff --check`, local links and 47 focused tests.
- [x] P2a: 97 focused tests, plan/generated-rule/whitespace checks and isolated HEAD-code import smoke with the three new modules and shared evidence symlink.
- [x] P2b preflight and sampler repair: 167 focused tests (70 bounded-variant plus 97 prior tests); independent derivation, null preservation, shared-cell coverage, geometry/frame, roundoff event preservation, pinned unchanged-grid comparison and budget-gate tests. No actual mechanical result is inferred.
- [x] P2b physical: separately pinned read-only inspection verifies 1464 cases, 324 presentations, all controls, carried-forward budgets and exact three-seed replays. Seventy-five focused physical/recovery/dimension tests and local governance/links/whitespace checks pass. No appearance or fitting acceptance.
- [ ] Clean-checkout validation before authorized merge; current P1 evidence uses the working checkout with preserved prior preparation/owner-review changes.
- [ ] Before authorized merge, run `arrive pr check --strict --json`; record installed-tool limitations separately from provider CI.

## Bug Fixes

P1 replaces the missing current-foundation consumption path with a separately
versioned baseline-only reader. It does not repair or repin rejected historical
readers, change primitive geometry, or address later ink/fatigue defects.

## Changes Made

### 2026-09-10 — pause affine preference exercise and plan stroke-context revision

The owner agrees to preserve the precise baseline and investigate entry/body/exit
relationships influenced by both neighbors, including deliberate connections,
retracing and genuine lifts. Addendum D specifies a bounded initial n/u/m scope,
fixed body/tool guardrails, explicit transition ownership, exact null behavior,
causal comparisons and separate mechanical/usefulness/transfer gates. A join is
not presumed desirable at every boundary; meaningful no-change is a valid outcome.

Five template-authored planned advances are registered in `td018-stroke-context`.
Existing components suffice. Word context now explicitly waits for the new
scope-qualified owner/transfer checkpoint. No execution, rendering, fitting,
source/candidate/threshold change or budget reset is performed. Original P2
mechanical evidence and old P3 packet remain unchanged; the pause is recorded
outside immutable packets. No human ranks, aesthetic rejection, natural variation
or fatigue implementation are invented. C006 remains in progress and all changes
remain uncommitted.

### 2026-09-10 — P3 training review packet and pre-fitting proposal prepared

The owner authorizes P3 preparation and preference collection before any fitting.
The [review packet](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/owner-review-v1/README.md)
indexes 54 existing seed-7/base actual images for nn/nm/un/um/mn/mm only, with
complete 3×3 width/advance grids and matching source/document pins. The browser
shows equal full-frame tiles and larger chosen/baseline/matched-advance controls;
no image is cropped, repainted, contrast-adjusted or used as a historical target.
All original/recovery evidence and frozen sources remain unchanged. Read-only
packaging takes 8.358s; controller/raster/optimizer counts remain zero.

Ranks are blank by default; ties, appearance exclusions and uncertainty are
explicit. Exported owner JSON binds the packet; validation rejects incomplete or
malformed records, unknown rows and changed pins and never releases fitting.
The proposed objective is the equal-weight six-cell mean of normalized strictly
preferred-alternative counts, with identity-favoring simplicity/deformation/ID
tie rules. Labels and objective remain unapproved until actual owner input.

Budgets carry all failed/recovery costs forward: remaining seconds/renders are
582.185/3426, 988.416/3426 and 579.067/3259 for seeds7/19/41. A proposed four-arm,
development/probe/sealed/control/regression inventory without reuse needs536
executions/1744 renders per seed, roughly31–39 additional minutes before safety
margin. Time feasibility is not cleared and no cap increase is assumed. Exact
selected-program reuse/inventory and explicit budget approval remain prerequisites.

Packet object SHA-256:
`a928389737c6e6c0ff0c2598dc66b625e9b8e13a3dfd6ee63c61423d438a4331`.
Eighty-eight focused tests pass in45.72s; JavaScript syntax and native Chrome
visual checks pass. No full browser export round trip, owner appearance approval,
provider CI, fitting, commit or merge is claimed. P3 awaits owner review and
budget resolution; C006 remains in progress and all changes uncommitted.

### 2026-09-10 — measurement-only correction clears complete mechanical inspection

The independently pinned dimension reader passes all 1464 cases across seeds
7/19/41 first/replay, including the recovered seed-41 replay, and all 324 saved
presentations. Exact replay equality, raw finite-ink containment, local windows,
known-base regressions, fifteen controls and numerical criteria are rechecked,
not inferred from stored passing flags. Runtime guards enforce zero controller
executions and raster renders; no refitting or new physical run occurs.

Dimension contract SHA-256:
`56e3ed722e086ec1415ea54c179070985c8d4841c19368a7c666db56d4f31f11`.
[Inspection report](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/dimension-check-v1/inspection-001/report.json)
SHA-256: `251d4fd3ff6a9c11ea0162b2b73108d679e22fa6ea7fd2a82756e103fdaddb5b`.
All original/recovery source and artifact pins are checked before and after;
the storage failure and failed-inspection audit remain preserved. Physical
debits stay 2117.815s/1574 renders, 1711.584s/1574 and 2120.933s/1741 respectively.

The bounded P2b mechanical gate is cleared, not appearance, S2, real-hand,
context-training or fitting acceptance. Next is P3 owner-review/preference,
objective and remaining-budget preparation. The 20 new dimension tests plus
55 original physical/recovery tests pass (75 in 37.67s), as do local plan,
generated-rule, whitespace and link checks. C006 remains in progress and all
changes uncommitted; no provider-CI, clean-checkout or merge claim is made.

### 2026-09-09 — owner-authorized measurement-only dimension correction

The owner approves correcting the checker and reinspecting saved files.
A [separate versioned reader](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/dimension-check-v1/README.md)
uses the pinned renderer's exact supersampling/downsize dimensions and decodes
the full presentation image. It does not allow a one-pixel tolerance or change
raw containment, metric dimensions, masks, controls, exact replays or budgets.
Structural tests require the worker to differ only in its presentation check,
and the composite reader only in worker dispatch. Runtime guards prohibit
controller execution and raster rendering. Both frozen readers, all existing
artifacts and the previous failed-inspection audit remain unchanged. No
physical run, rerender, fitting, commit or merge is authorized by this repair.

### 2026-09-09 — seed-41 replay recovered; presentation reader mismatch isolated

The one owner-authorized recovery completes 244/244 passing worker checks and
all controls, with exact artifact equality against the preserved seed-41 first
run. Recovery costs 955.023s/787 renders; all prior failed-replay costs remain
charged, yielding a seed-41 total of 2120.933s/1741 renders, within 2700s/5000.
Recovery report SHA-256 is
`e294db3edc76d2d22f28548e8a5f54834c61e9c3d543b6102410a274ce20dc98`.
The original attempt's 12771 files and original/recovery source pins are
reverified unchanged. Saved recovery output is 272 MiB, peak resident worker
memory about 448 MiB, and minimum observed free space 6.13 GiB (guard: 5 GiB).

Independent composite inspection exits 1 with `Incomplete presentation frame`.
The frozen renderer downsamples its full supersampled canvas to 1169×390;
the frozen reader's separate rounding formula expects 1170×390. A read-only
audit of all 324 saved presentation images confirms every image matches the
renderer and disagrees with the reader. Audit SHA-256:
`90d6287394d1feec8cdf40a141a5678dc602c77eba382a5d5fee070d8d947463`.
This metadata audit is not full raw mechanical inspection or acceptance.

No frozen reader, saved image, frame, target or threshold is altered to bypass
the failure. Next is approval for a separately versioned dimension-contract
reader correction and reinspection of existing files, with no further physical
run or fitting. Overall physical clearance and appearance review remain pending;
C006 remains in progress, with changes uncommitted. Plan, generated-rule,
whitespace and local-link checks pass; software validation remains 55 tests.

### 2026-09-09 — owner authorizes guarded seed-41 storage recovery

The owner approves a separate bounded recovery path with disk monitoring.
The [recovery protocol](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/RECOVERY.md)
preserves the original failed attempt and frozen source pins. One fresh full
seed-41 replay avoids assuming resumable RNG state, carries forward the entire
1165.910s/954-render debit, and must fit the remaining 1534.090s/4046 renders.
It requires 10 GiB free at launch and stops below 5 GiB. The new opt-in runner
collects unreachable objects between cases and records memory/storage telemetry;
it does not change controller dynamics or claim the storage cause is repaired.
A separate composite reader must verify all six complete raw datasets and exact
replays without fabricating a successful original root report. Preparation is
not execution or clearance; 55 recovery/original-physical tests pass. No fitting,
automatic retry, source repinning, deletion, commit or merge is authorized.

### 2026-09-09 — approved physical attempt blocked by disk exhaustion

The owner explicitly authorizes execution of the frozen three-seed contract.
Seeds 7 and 19 complete 244 first-pass and 244 replay cases each, with all worker
checks passing and byte-identical first/replay artifacts (excluding receipts).
Their combined ledgers are 2117.815s/1574 renders and 1711.584s/1574 renders,
within the approved 2700s/5000 per-seed caps. Seed 41's first 244 cases pass;
its replay records 52 passing measurements before case 53 is interrupted by
`[Errno 28] No space left on device`. Its cumulative debit is 1165.910s/954 renders.

There are 1272 completed measured cases, 1273 controller reservations and 4102
charged render calls. The supervisor exits 120 without writing a root report.
The interrupted case retains its reservation/document and zero-byte trace;
no partial artifact is treated as a successful measurement. A separate
[failure manifest](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/failed-run-001-manifest.json)
pins all 12771 retained files and the six worker reports, and independently
confirms completed seed replay artifact equality. Manifest SHA-256:
`adec239210591bf83b37abbe22543012e89ed5912fea2aea359be4e958fd086e`.

Full independent root inspection is not complete: no synthetic replacement
root report, retry, cleanup or source fix is performed. No overall physical,
S2, real-hand, context-training or fitting acceptance is granted. Next is storage
headroom investigation and an explicitly approved no-refit recovery plan for the
unfinished seed-41 replay, carrying forward every debit. The remaining recorded
allowance is 1534.09s/4046 render calls, not a reset. Frozen sources, geometry,
targets, frames, thresholds and prior dirty work remain intact and uncommitted.

### 2026-09-09 — physical runner, evidence reader and budget safeguards

The next work package implements `scripts/letter_context_physical.py`,
`scripts/letter_context_physical_evidence.py` and their focused tests under existing
curriculum/handvalidate components. Preparation is separate from execution; no
controller run, raster render, fitting or holdout access occurs during this step.
The [physical preparation guide](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/physical-validation-v1/README.md)
records the unchanged 244-case process inventory, 488 runs/seed, 1574 scheduled
render calls/seed inside the original 1588 bound, and explicit first/replay permits.
Atomic pre-render reservations, process deadlines, controller-attempt journals,
final-sealing accounting and immutable attempts preserve failures without retries
or budget resets. All future P2b spending must carry these seed debits forward.

The raw reader retains the frozen H024 formulas while supplying independently
verified derived plans, geometry and ports. It reconstructs ownership, dynamics,
clocks, exact contact events, finite-nib/local containment, overlap and saved-image
metrics, with old thresholds and scoped known-base comparisons unchanged.
Fifteen adversarial controls include desired-as-actual substitution and spacing
misclassification. Software tests use archived H024 traces/pixels and stubbed
controller routing; they do not grant actual-motion or fitting acceptance.
Frozen core, candidate, approval, P1/P2a and snapshot-003 identities stay unchanged.
C006 remains in progress; changes remain uncommitted.

Prepared contract pin:
`db909d00cd3d7c26cff021e2c9ff9ad19a6ebb8ca08bfd873bd41dd13d443eb5`.
Preparation rechecks live foundation readiness and fresh-process contract/source
identity. No actual attempt directory exists; controller/raster/optimizer counts
remain zero. The next action is the separately started bounded physical run.

Red: collection fails before the new modules exist. Final green: **205 tests pass
in 228.38s**, including 38 new physical-preparation tests and all 167 prior scoped
regressions. The exact command and evidence limits are in the physical guide's
software-validation receipt. Plan, generated-rule, local-link and whitespace
checks pass; strict PR metadata remains blocked by the installed `ids=[]` parser
behavior despite explicit title/body/label IDs. No provider CI or merge is claimed.

### 2026-09-09 — owner approves physical-validation budget

Recorded the explicit [budget approval](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/bounded-geometry-v1/budget-approval-001.json)
for 45 minutes (2700 seconds) per seed 7/19/41, including first/replay. The
5000-render ceiling and zero automatic retries/revisions remain unchanged;
P2b preview/validation costs carry into the combined C006 seed ledger without
resetting per arm or stage. Geometry, targets, frames and acceptance thresholds
remain unchanged. This clears the budget-approval prerequisite, not the physical
runner/reader/control freeze or fitting gates. No physical run starts in this
approval-only update. Preserve all historical snapshots and their code identities;
the new execution contract must bind this separate approval, not repin old reports.
Changes remain uncommitted; C006 remains in progress.

### 2026-09-09 — approved corner repair and unchanged-grid rerun

Owner explicitly requests repairing corner sampling and rerunning the same grid
without changing geometry or thresholds. The derived-only adapter retains exact
corner sample 318 and its boundary contributors, removing roundoff duplicate
319. Only ordinary adjacent interior samples on the relevant source cubic can
coalesce; meaningful nearby points, endpoints, protected boundaries, unrelated
owners and missing/ambiguous anchors remain untouched. Frozen core and the
identity short-circuit are not edited. The arithmetic suppression is 16 coordinate
ULPs, capped at the unchanged exact-corner tolerance, not a new acceptance limit.

Snapshot-003 passes **860/860 geometry/frame checks and 244/244 desired plans**
over the same 430 assignments. The pinned before/after reader verifies exact
geometry records and local windows, unchanged criteria/grid/source foundation,
all **238 prior passing timing hashes/metrics**, and **52 exact null bundles**.
All six earlier mn/mm subdivision rejections are retained in the old report and
cleared only in the new report. Snapshot-002's sampler/reader source archives
match its original frozen hashes. Report pin:
`190cc9975bfb307ebd60b293cb7e62bef49a137bbaf5fe5a217b9f9b88c02cfb`.
Fresh-process read-only reinspection reconstructs the full pinned report exactly,
including all 860 geometry checks and 244 passing desired plans. Plan,
generated-rule, local-link and whitespace checks pass. The installed strict PR
parser still reports `ids=[]` despite explicit title/body/label IDs; no provider
CI, commit or merge is claimed.

Thirteen sampler regression cases fail before the repair and pass afterwards;
additional incoming/ambiguous boundary and pinned-comparison negative controls
cover preservation and fail-closed behavior. Final focused suite: **167 pass in
190.87s**, using the five-module command recorded below. Controller executions, raster
renders and optimizer calls remain zero. Physical validation still needs the
45-minute combined seed budget approval and frozen runner/reader/controls;
P2b and C006 remain in progress, with no fitting or new acceptance permission.
Changes remain uncommitted; historical failures and prior dirty work are preserved.

### 2026-09-09 — P2b approved geometry/frame and budget preflight

Owner authorizes the bounded stroke changes and measurement frame. A separately
versioned compiler and reader preserve frozen P1/P2a/core identities while
deriving only horizontal width and independent placement effects. Shared-rule
enumeration covers all unsealed geometric combinations without opening sealed
triples. Conservative full-nib control hulls and union-frozen local windows
prevent the earlier crop problem from being accepted as evidence. New desired
plans use derived cubics and recomputed timing, not old plans with shifted pixels.

The [bounded preflight](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/bounded-geometry-v1/README.md)
separates geometric and planned checks from missing actual mechanics. Its physical
inventory has 488 runs including replay and an estimated 1588 render calls per
seed. Historical wall-time extrapolation gives 35.78 minutes before reserve;
45 minutes per seed is proposed with 25% headroom, not silently authorized.
This is not an actual timeout or a claim that stroke variants failed. Physical
runner/reader/control freeze and owner budget approval remain required; no
controller, raster or optimizer call is made. P2b and C006 remain incomplete.
Old reports, targets, thresholds, approval history and all uncommitted work are
preserved. No branch, commit or merge is made.

Red collection fails before the new modules exist. Green: 138 tests pass in
182.26s using `.venv/bin/python -m pytest -q tests/test_letter_context_variants.py tests/test_letter_context_contract.py tests/test_current_foundation_readiness.py tests/test_upright_reference_contract.py tests/test_upright_event_replay.py`.
Plan, generated-rule and whitespace checks pass. These local checks are not
provider CI or a completed physical experiment.

The first full preflight aborts during planning with `Exact unique corner port
required`. Its freeze and exact reader source remain in bounded-geometry-v1.
A red/green collector-only repair retains rejected plans and continues the same
inventory in snapshot-002. Geometry, sampler and thresholds are not revised;
there are still zero physical executions. Plan rejection is an additional
blocking finding, not permission to advance or widen tolerances.

Snapshot-002: all 860 geometric/frame checks pass; 238 of 244 desired plans pass.
Six subdivision plans fail for mn/mm at width 0.97, independent of advance.
At the first m corner, plan indices 318/319 are only 1.42e-14 mm apart and both
match the unchanged 1e-8 mm port tolerance. The sampler has not been repaired.
Report pin: `a58c673514efc2bd89a23e04b644caa50150a0e21b9864a1c747955f844c7671`.
Final focused suite: 139 tests pass in 170.37s, including rejected-plan collection.
Fresh-process read-only reinspection reproduces the pinned complete inventory
and all six planning failures; no physical or fitting gate is promoted.
Next is the bounded sampler repair and same-grid recheck, not fitting or physical
execution. The 45-minute budget proposal remains pending behind this prerequisite.

### 2026-09-09 — P2a context/lineage and exact null checks

The owner requests the next contract/null-check work package and explicitly
leaves changes uncommitted. No preparatory refactor or core edit is necessary;
red tests precede two new opt-in modules and scoped component selectors.

The compiler preserves canonical geometry byte-for-byte under context-off and
six shared identity rules. Separate occurrence sidecars bind canonical and
execution primitive hashes, gesture/action/recipe lineage, spans, contact
ownership, rule resolution and identity derivations. An independent reader
reconstructs this sidecar without trusting the new compiler. The planning
adapter checks the sidecar before invoking unchanged action planning and
curve-tangent timing; it cannot execute or accept nonidentity geometry.

Evidence is [null-contract-v1](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/null-contract-v1/README.md).
The immutable snapshot passes all 80 mode/fixture/refinement comparisons and
binds 240 archived runs plus 480 actual/desired images; all 24 known-base actual
reference comparisons match exactly. Report pin is
`7d8030f9818238a6e7d1252d4b152c844c0e423f9d2909df4400f52e428700ac`.
A fresh-process read-only reinspection reconstructs and matches the entire
externally pinned snapshot. P2a is complete; no new physical replay was performed.
Exact null input equivalence plus pinned archived-output bindings are distinct
from fresh physical replay. Old evidence, P1 pins, preparation authority flags,
targets and thresholds remain unchanged. The contract's six cells do not imply
six-cell physical coverage: n-to-rise has no H024 archived fixture. No new
simulation, render, fitting, unseen-triple inspection or acceptance is claimed.
P2b variant/frame mechanics and P3–P5 remain pending; C006 stays in progress.

Validation: the new module fails test collection before implementation; then
all 97 focused tests pass (50 new plus the P1/reference/event regressions) in
139.24s. Command: `.venv/bin/python -m pytest -q tests/test_letter_context_contract.py tests/test_current_foundation_readiness.py tests/test_upright_reference_contract.py tests/test_upright_event_replay.py`.
This includes real archived-pixel integration without a new renderer call.
Isolated imports resolve only to an exported HEAD code tree plus the three new
modules, with shared evidence linked from this checkout; this is not a full
clean-checkout experiment. Plan, generated-rule and whitespace checks pass.
The installed strict PR parser still yields `ids=[]` despite explicit IDs in
title/body/label; no successful strict check, provider CI or merge is claimed.

### 2026-09-09 — P1 current-foundation readiness clearance

Owner authorizes the first work package only. The new reader verifies all 1,808
pinned H024 artifacts and current source identities, reuses the pinned independent
physical-inspection receipt, and newly scans every contact occurrence across
240 archived runs. Canonical geometry and exact internal subdivision are distinguished;
primitive/gesture/action/recipe hashes, placement ownership, fixed action and
contact coverage remain bound to the approved candidate. This is not another
physical reconstruction or a new experiment.

The [readiness snapshot and usage guide](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/readiness-v1/README.md)
clear exact baseline reuse only. Consumers must supply the external report hash,
exact candidate, explicit n/u/m letter scope, physical-edge-v1 tool and
frozen-baseline-reuse purpose. Inspection recomputes coverage; edited pass flags,
repinned authority, stale source, missing artifacts and changed candidates fail
closed. There are no missing baseline inventory entries, but five named gaps
still block contextual geometry, new text/frame coverage, preferences/objective,
execution authorization and broader layer admission. Neither old S1 reader is
repaired. S2, real-hand and context-training flags remain false.

Red: the new test module fails collection before the readiness module exists.
Green: `python -m pytest -q tests/test_current_foundation_readiness.py tests/test_upright_reference_contract.py tests/test_upright_event_replay.py`
passes all 47 tests using `.venv/bin/python` (159.61s). Tests cover raw lineage,
fixed actions, missing occurrences, subdivision provenance, artifact corruption,
scope/authority expansion and retained legacy rejection. No new controller calls,
renders or optimizer evaluations. No core changes, branches, commits, merge or
provider CI are claimed. Existing uncommitted preparation/owner-review work is
preserved. P1 is complete; the Advance stays in progress for P2–P5.

### 2026-09-09 — prepared bounded neighbor-context pilot

Owner authorizes preparation after H024 appearance approval. Addendum C and
preparation-001 pin the audit and propose six following-neighbor rule cells,
three arms, exact train/development/test strings and new-frame safeguards.
This supersedes the broader initial 16-rule/join/word implementation proposal.
Readiness, transform bounds, preference targets and execution authorization
remain unresolved; Advance status stays planned. ARRIVE scaffold 0.1.24 used.

### 2026-09-06 — plan: Adopt shared-stroke layered learning

- Added to Pass 15 phase `td018-letter-context`.
- Deferred expressive work until strokes, letters and both context levels are proven.

### 2026-09-06 — plan: Require gesture/action readiness

Inherited gesture/action readiness and immutable lower-layer identity now govern
context fitting; new evidence uses the v2 namespace. No execution is claimed.

## Check for Understanding

1. What changes are learned at this layer, and which lower-layer parameters stay frozen?
2. Which visible transfer test prevents this layer from merely reproducing supplied shapes?
3. Why can H024 appearance approval and mechanical PASS coexist with blocked context fitting?
4. Why does mmm need a new frame while old exact-reference comparisons retain theirs?

## CI Evidence Notes

P1 readiness and P2a null context are tested read-only implementations, not a
physical experiment or nonidentity learner. Validate source/artifact pins, unchanged preparation
partitions/bounds/authority flags, plan, generated rules, links and whitespace.
No controller run, fitting, provider CI, branch or merge is claimed. P2b–P5 still
require their own authorization, red/green tests and matching-scope evidence.

Preparation checks pass: pinned audit/source/review/inspection files, unchanged
H024 code identities, non-executable authority flags, 24 distinct text-role entries,
complete six-cell training coverage, 54-row proposed grid cap and local document
links. Plan, generated-rule and whitespace checks pass. The installed strict PR
parser still returns ids=[] with explicit title/body/label IDs; provider CI is
not claimed. Prior uncommitted H024 owner-review updates are preserved.
