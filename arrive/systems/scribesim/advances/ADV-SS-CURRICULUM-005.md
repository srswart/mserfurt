---
advance:
  id: "ADV-SS-CURRICULUM-005"
  title: "Letter Construction — Recipes Built from Learned Strokes"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","evo","gesture","handvalidate","tests"]
  started_at: "2026-09-06T04:10:57Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: []
  model_usage: []
  status: planned
---

## Objective

Construct and fit letters as constrained compositions of frozen learned gestures and their shared primitives/action profiles, proving each lower layer is used rather than replaced.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
Drafting timestamp only: no implementation, training, CI or owner approval is claimed.

## Behavioral Change

Construct and fit letters from accepted gesture instances, with deliberate pen actions preserved and session effects disabled. The new curriculum must produce visible layer-specific
learning and transfer evidence before downstream acceptance.

## Component Impact

- `scribesim/curriculum/letter_recipes.py (new)`
- `scribesim/evofit/stroke_language.py (recipe constraints)`
- `scribesim/evofit/stroke_gestures.py (versioned gesture recipe compilation)`
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

Completion is not acceptance. Synthetic scaffolding may execute with explicitly
unaccepted inputs. Reference-derived fitting requires live G0, and real layer
acceptance requires the matching accepted lower-layer checkpoint. Do not import
an older curriculum's pass summary as evidence of shared-stroke learning.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before branches or commits.
- [ ] tidy: assess narrowly required preparation; preserve unrelated work.
- [ ] test: commit failing behavioral tests before feature implementation when commits are authorized.
- [ ] feat/evaluate: Freeze up to 12 starter lowercase characters from admitted coverage before training; unsupported requested characters fail explicitly. Fit at most two recipes per character from the accepted shared gesture inventory, retaining the matching contract's audited expansion limit. The legacy cap remains four; only an accepted explicit GESTURE-002 contract can introduce a justified cap up to eight. Macros cannot bypass either version's limit.
- [ ] feat/evaluate: Represent sequence, attachment ports, bounded translation/scale/rotation, lifts, permitted crossings and baseline/x-height/counter constraints explicitly. Do not add independent cubic geometry as a fallback.
- [ ] feat/evaluate: Keep accepted primitive, gesture and action-profile checkpoints plus tool/controller identities frozen while fitting bounded recipe choices and placements. Optimize from admitted training word/letter evidence with uncertain allocations recorded; development selects the recipe checkpoint. Do not learn new action tracks, hidden finishing passes or session controls at this layer.
- [ ] feat/evaluate: Compare shared-stroke recipes against frozen prior recipes and the legacy independent-form diagnostic under matched render/time budgets. Cap each ablation/seed at 5000 target renders or 1800 seconds, seeds 7/19/41; one diagnosed revision.
- [ ] feat/evaluate: Emit each letter as a recipe listing, numbered/color-coded constituent strokes, assembly stages and clean nominal/actual-neutral outputs. Include multiple letters sharing the same primitive and traceable parameter identity.
- [ ] feat/evaluate: Freeze recipe evaluation before opening held-out examples; repeat observations and genuinely unseen combinations are reported separately. Obtain real appearance/reading review when available rather than equating a template score with legibility.
- [ ] evidence: record red/green commands, actual budget use, hashes, scope and outcome before marking completion.

## Validation Gates

- [ ] S2: letters compile entirely from frozen learned gestures over shared primitives and accepted action profiles, respecting contacts, ports, overlaps, proportions, counters and exact visible/logical mappings.
- [ ] A shared-primitive substitution/change propagates predictably across multiple letters; detached per-letter curve copies cannot pass the reuse check.
- [ ] Recipe fitting improves predeclared held-out quality over initialization without unbounded residual geometry, distorted aspect or unauthorized text aliases.
- [ ] Publish a letter construction workbook and checkpoint with synthetic versus reference-grounded status; missing support produces unresolved characters, not guessed promotions.

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

- [ ] Frozen fixtures, splits, constraints, objective/limits and model/code identities.
- [ ] Before/after practice sheets, decomposition proofs and transfer results.
- [ ] Replay and neutral direct/sampled/actual comparisons; real review only when performed.
- [ ] `arrive plan check`, `git diff --check`, focused tests and clean-checkout validation.
- [ ] Before authorized merge, run `arrive pr check --strict --json`; record installed-tool limitations separately from provider CI.

## Bug Fixes

None implemented. This planned Advance addresses the missing layered-learning
contract, not the later ink or fatigue defects.

## Changes Made

### 2026-09-06 — plan: Adopt shared-stroke layered learning

- Added to Pass 15 phase `td018-letters`.
- Deferred expressive work until strokes, letters and both context levels are proven.

### 2026-09-06 — plan: Require gesture/action readiness

Gesture/action readiness is now a prerequisite; new evidence uses the v2
namespace and preserves v1 snapshots. No implementation or gate result changed.

## Check for Understanding

1. What changes are learned at this layer, and which lower-layer parameters stay frozen?
2. Which visible transfer test prevents this layer from merely reproducing supplied shapes?
