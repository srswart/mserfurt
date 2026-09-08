---
advance:
  id: "ADV-SS-CURRICULUM-005"
  title: "Letter Construction — Recipes Built from Learned Strokes"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","evo","gesture","handvalidate","tests"]
  started_at: "2026-09-06T04:10:57Z"
  implementation_completed_at: "2026-09-08T16:41:10Z"
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 110
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit", "tests:integration", "local:synthetic-letter-assembly", "local:fresh-process-replay"]
  model_usage: []
  status: complete
---

## Objective

Construct and fit letters as constrained compositions of frozen learned gestures and their shared primitives/action profiles, proving each lower layer is used rather than replaced.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
Implementation and the bounded synthetic experiment are complete. This does not
grant S2, historical reading, context-training or provider CI approval.

## Behavioral Change

Construct and fit letters from accepted gesture instances, with deliberate pen actions preserved and session effects disabled. The new curriculum must produce visible layer-specific
learning and transfer evidence before downstream acceptance.

## Component Impact

- `scribesim/curriculum/letter_recipes.py (new)`
- `scribesim/curriculum/letter_recipe_evidence.py (read-only receipts)`
- Existing `stroke_language.py` and `stroke_gestures.py` are reused unchanged.
- `tests/test_letter_recipes.py (new)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/ (new evidence)`

Use tracked modules and scoped test selectors; clean-checkout imports are required.
No production renderer or component stage changes.

## Dependencies

- [ADV-SS-CURRICULUM-004](ADV-SS-CURRICULUM-004.md)
- [ADV-SS-HANDVALIDATE-014](ADV-SS-HANDVALIDATE-014.md)
- [ADV-SS-HANDVALIDATE-016](ADV-SS-HANDVALIDATE-016.md)
- [ADV-SS-HANDVALIDATE-017](ADV-SS-HANDVALIDATE-017.md)
- [ADV-SS-HANDVALIDATE-018](ADV-SS-HANDVALIDATE-018.md)

[TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md)
requires matching accepted primitive, S1-gesture and S1-action/readiness records
for the intended scope. A fixed/null profile is valid only for its declared
coverage; a required unresolved action blocks the affected inventory.

[Addendum B](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md)
inserts foundation repair before this work. A matching foundation pass and a
newly scoped accepted action/null candidate evaluation are runtime prerequisites;
HANDVALIDATE-014's completed early-stop record is not S1-action acceptance.
HANDVALIDATE-017 admits only underturn for its frozen candidates. The revised
path is CURRICULUM-013's finer shared-scale experiment, then HANDVALIDATE-018's
independent acceptance of the replacement bytes. Neither a foundation gesture
pass nor a complete learning experiment releases this Advance for letter fitting.

HANDVALIDATE-018 now supplies independent scoped fixed-null acceptance of the
frozen finer-scale underturn, overturn and compound constructions. Consume
`scribesim.handvalidate.finer_scales.require_readiness` with its exact report hash
and an explicit inventory; do not relax old candidate-specific readers. This
closes that declared null prerequisite, not this Advance's unexecuted recipe,
letter/reference coverage or real-hand requirements.

Completion is not acceptance. Synthetic scaffolding may execute with explicitly
unaccepted inputs. Reference-derived fitting requires live G0, and real layer
acceptance requires the matching accepted lower-layer checkpoint. Do not import
an older curriculum's pass summary as evidence of shared-stroke learning.

## Planned Implementation Tasks

- [x] branch: `advance/ss-curriculum-005` under the standing implement/update/merge authorization.
- [x] tidy: no preparatory refactor needed; preserve pinned lower-layer source and reports.
- [x] test: `d7bbf58` records missing-module failure before implementation; 27 behavioral tests now pass.
- [x] feat/evaluate: Freeze audited synthetic `n/u/m` scaffolds, one topology each, before training; unsupported text fails. Retain the admitted contract's six-reference cap. Underturn/overturn are admitted in scope; standalone stem remains explicitly unresolved. Accepted-inventory/real letter training is not claimed.
- [x] feat/evaluate: Represent sequence, lifted ports, bounded translation, fixed scale/rotation, forbidden crossings and proportion envelopes. Counter-bearing letters are unsupported. No independent cubic fallback. Level baseline/x-height compatibility remains a diagnosed letter-shape issue, not a passed reading criterion.
- [x] feat/evaluate: Freeze lower-layer and tool/controller identities; development selects bounded placements against explicitly synthetic training observations. Live real G0/native allocations are not supplied and real mode fails closed. No new action tracks, finishing passes or session controls.
- [x] feat/evaluate: Compare shared placement, frozen prior and geometry-only legacy diagnostics with matched physical frame/tool/layout and equal 5000-render/1800-second ceilings including replay. Seeds 7/19/41 complete; zero revisions. Actual expenditure differs explicitly; legacy has no fabricated controller proof.
- [x] feat/evaluate: Emit recipe listings, numbered/color-coded strokes, assembly stages, native 900-DPI nominal/actual-neutral panels and shared-primitive propagation proofs.
- [x] feat/evaluate: Freeze selected checkpoints before opening transformed repeat and unseen-pair pixels; report those groups separately. No human reading/appearance acceptance is inferred from template loss.
- [x] evidence: Record red/green tests, budgets, identities, scope and outcomes in the linked report and verification receipt.

## Validation Gates

- [ ] S2: letters compile entirely from frozen learned gestures over shared primitives and accepted action profiles, respecting contacts, ports, overlaps, proportions, counters and exact visible/logical mappings.
- [x] A shared-primitive substitution/change propagates predictably across multiple letters; detached per-letter curve copies cannot pass the reuse check.
- [x] Recipe fitting improves predeclared synthetic held-out image quality over initialization without changing scale/aspect, adding residual geometry or introducing text aliases. This does not resolve the target's pre-existing unequal letter heights.
- [x] Publish a letter construction workbook and checkpoint with synthetic versus reference-grounded status; missing support produces unresolved characters, not guessed promotions.

## Invariant Impact

Exact text, source uncertainty, split isolation, shared-parameter lineage,
deterministic compilation and actual trajectory ownership remain mandatory.
Synthetic mechanics, real-source fitting and human appearance acceptance are
separate. Layer gates S0–S4 supplement, not replace, G0–G4.

## Risk + Rollback

A layer can disguise copied character geometry or memorized words as learning.
Reject unrestricted residuals and per-instance lookup; retain frozen lower-layer
checkpoints, ablations and failed evidence. Revert only the new opt-in model,
not historical snapshots or production defaults. Review estimate: 40 minutes.

## Evidence

- [x] Frozen fixtures, splits, constraints, objective/limits and model/code identities.
- [x] Before/after practice sheets, decomposition proofs and transfer results.
- [x] Replay and neutral direct/sampled/actual comparisons; no real review claimed.
- [x] `arrive plan check`, `git diff --check`, focused tests and clean-checkout validation.
- [x] Strict PR check executed with explicit title/body/label; installed parser returns `ids=[]` and exit 1. No provider CI claim.
- [x] Local merge and post-merge evidence receipt.

See [results and commands](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/README.md),
[samples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/index.html)
and [immutable report](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/run-001/report.json).

## Bug Fixes

Pre-render tests exposed an omitted letter-local gate and missing attachment
proofs; `b4ba8a5` records those failures before `e00ed7c` repairs them. No ink,
clock, fatigue, historical compiler or primitive code changed.

## Changes Made

### 2026-09-08 — feat: complete synthetic assembly experiment

Completion commit `3c26f5d` merged locally into `master` as `47db8b1`.
Post-merge read-only reconstruction verifies all 968 artifacts and the published
report hash, with synthetic pass and S2/real/context flags still false. Plan,
generated-agent-rule freshness and whitespace checks pass. No push, provider CI
or human appearance/reading approval is claimed.

All three seeds select the same bounded placement deltas: `n=[0.08,0]`,
`u=[0.02,0.34]`, `m=[0.02,0.34]`. Worst letter-local actual/target losses are
0.013008 / 0.016607 / 0.019452, below unchanged 0.05. Repeat nominal/prior ratios
are 0.02908 / 0.11206 / 0.04633, below unchanged 0.75; unseen pairs also pass.
All measured physical, lifted-port, frame and ownership checks pass.

2652 renders total, including separate first/replay processes for every arm and
seed: shared 476, prior 300, legacy 108 per seed. Maximum cumulative arm/seed
time is 582.531 seconds. All nine arm/seed pairs replay exactly, with 63 / 61 /
34 non-clock artifacts per shared/prior/legacy worker. No lower-layer fitting,
attempt revision or retry occurred. All 968 artifacts verify through the new
read-only inspector, which reconstructs saved selection and compiled provenance
without calling the fitter, selector or renderer.

Execution code is frozen at `e00ed7c`; the later read-only inspector is
`58fc4ed`, following missing-module red tests in `08f18e8`. Initial runner red
tests are `d7bbf58`, with implementation `7701028`; guard red/fix is
`b4ba8a5` / `e00ed7c`. Validation: 127 initial focused tests pass; the expanded
new-module selection has 40 passing tests (13.88 seconds, and 12.66 seconds in a
clean committed checkout). The broader physical/foundation selection has 287
passing tests in 340.77 seconds. These are local tests, not provider CI.

The experiment report SHA is
`a587f212aa62c2a4742e4d7601a814d3932a5a903e5e993947c9116c4ebe0c12`;
all three selected candidate files have SHA
`d522b14f3470101603d957332016c257d2c8a1a1d7f41d0d66d542acf5644734`.
The native seed-7 workbook was visually inspected. It exposes diagonal rises
and a stair-stepped `m`: both return gestures have endpoint displacement
`[1.02,0.34]`, which translation cannot level. Approximate -18.435-degree
rotation is a geometric investigation only, not a rendered or accepted fix.
Retain these targets; next scope baseline/x-height-compatible assembly and
standalone-stem admission before independent S2 or context work.

Reviewability is Red 110, dominated by 968 inseparable manifest-backed generated
artifacts (mechanical review estimate 566.6 minutes, not human review performed).
Test, implementation, guard and reader changes are already separated
into reviewable commits. Only two new opt-in runtime modules are added; no
pinned historical runtime changes. Future shape/rotation and acceptance work
remain separate, rather than hiding a protocol revision in this evidence commit.
Artifact doctor retains ten inherited issues; generated rules remain current.

### 2026-09-08 — feat: freeze bounded synthetic letter scaffolding

Implementation began at 11:48:16 UTC from `51061a1`. The initial opt-in runner,
tests and specification use existing incubating components, without editing
the pinned compiler, primitives, gesture/action checkpoint or renderer.

Freeze `n`, `u`, `m` from GESTURE-002's audited construction vocabulary: four,
four and six expanded references, respectively. One topology per character,
two explicit lifted gestures; only the second gesture's bounded x/y placement
may fit. Rotation, scale, advances, crossings, context and all lower layers stay
fixed. A uniform -0.2 local-x origin is applied to every arm and analytic target
before rendering so `m` stays within the existing +/-2 reference-offset bound;
no cap or compiler bound is increased.

HANDVALIDATE-018's live reader verifies the exact underturn/overturn checkpoint.
Its coverage does not independently admit the standalone stem needed by `n/u`.
Therefore this is explicitly permitted **synthetic scaffolding with unresolved
inputs**, not accepted-inventory letter fitting. `m` also needs letter-level
evaluation even though its two overturn references have scoped null evidence.
Real-reference mode fails before source pixels: reviewed live G0, real lower
layers and native letter allocations are not provided.

The frozen experiment has seeds 7/19/41; shared-placement fitting, frozen prior
recipes, and frozen exact-Unicode catalog independent-form diagnostics. Each
arm gets the same 5000-render/1800-second ceiling including separate-process
replay, not padded equal expenditure. The legacy arm is geometry-only, with
matched tool/frame/layout and no fabricated shared-ownership/controller proof.
Training/development use isolated observations; transformed repeats and exact
unseen `nu`, `um`, `mn` strings open only after checkpoint freeze. These are
transfer probes, not word/context training. Three actual timing/arc refinements
are measured; no new source-subdivision or counter acceptance is claimed.
Targets reuse unchanged independent analytic families; 0.05 absolute loss and
0.75 held-out ratio remain fixed. One separately diagnosed revision is allowed,
with zero automatic retry. Publish failures and keep S2/real/context flags false.

### 2026-09-06 — plan: Adopt shared-stroke layered learning

- Added to Pass 15 phase `td018-letters`.
- Deferred expressive work until strokes, letters and both context levels are proven.

### 2026-09-06 — plan: Require gesture/action readiness

Gesture/action readiness is now a prerequisite; new evidence uses the v2
namespace and preserves v1 snapshots. No implementation or gate result changed.

## Check for Understanding

1. What changes are learned at this layer, and which lower-layer parameters stay frozen?
2. Which visible transfer test prevents this layer from merely reproducing supplied shapes?
3. Why do the low synthetic losses not resolve the climbing `m` or grant S2?
