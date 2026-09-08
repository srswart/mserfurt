---
advance:
  id: "ADV-SS-CURRICULUM-006"
  title: "Letter Context — Bounded Stroke Changes Within Words"
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

Learn and explain how adjacent letters alter their constituent strokes when assembled into words, without abandoning shared primitives or letter identity.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
Drafting timestamp only: no implementation, training, CI or owner approval is claimed.

## Behavioral Change

Learn and explain how adjacent letters alter their constituent strokes when assembled into words, without abandoning shared primitives or letter identity. The new curriculum must produce visible layer-specific
learning and transfer evidence before downstream acceptance.

## Component Impact

- `scribesim/curriculum/letter_context.py (new)`
- `scribesim/evofit/stroke_language.py (word compiler and rule overlays)`
- `tests/test_letter_context.py (new)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/letter_context/ (new evidence)`

Use tracked modules and scoped test selectors; clean-checkout imports are required.
No production renderer or component stage changes.

## Dependencies

- [ADV-SS-CURRICULUM-005](ADV-SS-CURRICULUM-005.md)

Per [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md),
consume matching primitive/gesture/action/letter identities and S1-gesture/
S1-action readiness inherited through CURRICULUM-005. Neutral execution retains
accepted deliberate actions while disabling fatigue and other session effects.

CURRICULUM-005's new `letters/run-001` is bounded synthetic assembly evidence,
not an accepted S2 checkpoint. Its report explicitly keeps
`context_training_allowed=false`: standalone-stem admission and letter-level
baseline/x-height/reading remain unresolved. Exact unseen two-letter strings in
that workbook are juxtaposition transfer probes, not learned context. Do not
start accepted-layer context fitting from completion status or low target loss.

HANDVALIDATE-019 resolves scoped standalone-stem admission. CURRICULUM-014 adds
level assembly, and HANDVALIDATE-020 independently passes its declared rotated-
return and whole-assembly mechanical scope. The owner now requires appearance
repair of all three letters: near-upright upward movement close to stems and
less-slanted returns. The owner confirmed that upward movements must remain
pen-down; GESTURE-003, CURRICULUM-015 and HANDVALIDATE-021 now scope this repair,
its nominal owner-review checkpoint and independent actual-contact evaluation.
HANDVALIDATE-021 completion alone is not S2 clearance. Whole-letter source subdivision is not
claimed. None releases context fitting; this Advance remains planned and unimplemented.

Completion is not acceptance. Synthetic scaffolding may execute with explicitly
unaccepted inputs. Reference-derived fitting requires live G0, and real layer
acceptance requires the matching accepted lower-layer checkpoint. Do not import
an older curriculum's pass summary as evidence of shared-stroke learning.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before branches or commits.
- [ ] tidy: assess narrowly required preparation; preserve unrelated work.
- [ ] test: commit failing behavioral tests before feature implementation when commits are authorized.
- [ ] feat/evaluate: Freeze primitive, gesture, action-profile and letter checkpoints plus tool/controller identities. Fit a bounded rule table keyed only by declared preceding/following letter or stroke class and word position; at most 16 rules, with deterministic precedence and explicit no-rule behavior. No new action tracks or mutations of shared profiles; context selects only supported frozen gesture/recipe alternatives within existing limits.
- [ ] feat/evaluate: Allow bounded entry/exit adaptation, port-compatible joins/lifts, recipe alternatives and advance changes. Preserve counters and landmark constraints, and record exactly which primitive occurrence changed and why.
- [ ] feat/evaluate: Test the same letter alone, in repeated minims and beside contrasting neighbors; show independent juxtaposition versus context-enabled composition. Include explicit shared ownership for any supported multi-character form.
- [ ] feat/evaluate: Optimize context parameters on training combinations only. Freeze a composition-disjoint development/test vocabulary before fitting; familiar letters in unseen combinations are the transfer test, not merely new random seeds.
- [ ] feat/evaluate: Run context-off, spacing-only and stroke-context ablations, each at most 5000 rendered targets or 1800 seconds per seed 7/19/41, one diagnosed revision. Unsupported or under-evidenced interactions stay disabled.
- [ ] feat/evaluate: Emit enlarged pair/triple proofs and unseen word sheets with before/after primitive deltas, rule IDs, exact text coverage and nominal/actual-neutral comparisons.
- [ ] evidence: record red/green commands, actual budget use, hashes, scope and outcome before marking completion.

## Validation Gates

- [ ] S3: measurable source-supported contextual stroke changes preserve primitive lineage, letter identity, ports/counters and declared deformation limits.
- [ ] Context effects cannot be explained solely by spacing or by per-word cached shapes; unseen combinations must be generated without reference-image access.
- [ ] Fresh-process replay, deterministic rule resolution and exact join/ligature ownership pass through every primitive/gesture/profile occurrence; context overlays never mutate shared primitive, gesture, action-profile or recipe checkpoints.
- [ ] Context-enabled output must meet frozen quality criteria on held-out combinations; numeric improvement is separate from genuine reading/appearance review.

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

- Added to Pass 15 phase `td018-letter-context`.
- Deferred expressive work until strokes, letters and both context levels are proven.

### 2026-09-06 — plan: Require gesture/action readiness

Inherited gesture/action readiness and immutable lower-layer identity now govern
context fitting; new evidence uses the v2 namespace. No execution is claimed.

## Check for Understanding

1. What changes are learned at this layer, and which lower-layer parameters stay frozen?
2. Which visible transfer test prevents this layer from merely reproducing supplied shapes?
