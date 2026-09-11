---
advance:
  id: "ADV-SS-CURRICULUM-007"
  title: "Word Context — Boundary Effects on Stroke Programs"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum","evo","gesture","layout","handvalidate","tests"]
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

Model how placing words together affects their boundary strokes and layout, keeping this distinct from fatigue, ink depletion or emotional/motor simulation.

Follows [TD-018 section 12](../../../../docs/tech-direction/TD-018-reference-grounded-hand-recovery.md#12-stroke-language-and-layered-learning-revised-direction).
Drafting timestamp only: no implementation, training, CI or owner approval is claimed.

## Behavioral Change

Model how placing words together affects their boundary strokes and layout, keeping this distinct from fatigue, ink depletion or emotional/motor simulation. The new curriculum must produce visible layer-specific
learning and transfer evidence before downstream acceptance.

## Component Impact

- `scribesim/curriculum/word_context.py (new)`
- `scribesim/evofit/stroke_language.py (line compiler and boundary rules)`
- `tests/test_word_context.py (new)`
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/word_context/ (new evidence)`

Use tracked modules and scoped test selectors; clean-checkout imports are required.
No production renderer or component stage changes.

## Dependencies

- [ADV-SS-CURRICULUM-006](ADV-SS-CURRICULUM-006.md)
- [ADV-SS-HANDVALIDATE-026](ADV-SS-HANDVALIDATE-026.md)

Per [TD-018 Addendum D](../../../../docs/tech-direction/TD-018-addendum-d-stroke-context-transitions.md),
word-context work now waits for the new neighbor-aware stroke-context phase and
an explicit scope-qualified owner/checkpoint decision. The old affine mechanical
pass or completion of these planning documents is not contextual acceptance.

Per [TD-018 Addendum A](../../../../docs/tech-direction/TD-018-addendum-a-stroke-gestures.md),
retain the matching primitive/gesture/action/recipe/context identities and
scope-qualified readiness inherited through the letter curriculum.

Completion is not acceptance. Synthetic scaffolding may execute with explicitly
unaccepted inputs. Reference-derived fitting requires live G0, and real layer
acceptance requires the matching accepted lower-layer checkpoint. Do not import
an older curriculum's pass summary as evidence of shared-stroke learning.

## Planned Implementation Tasks

- [ ] branch: confirm authorization before branches or commits.
- [ ] tidy: assess narrowly required preparation; preserve unrelated work.
- [ ] test: commit failing behavioral tests before feature implementation when commits are authorized.
- [ ] feat/evaluate: Freeze primitive, gesture, action-profile, recipe and within-word context checkpoints plus tool/controller identities. Add at most eight inter-word rules keyed by declared word-edge stroke/letter classes, gap and line position, not arbitrary word identities or semantic/emotional keywords. Context may select supported frozen alternatives but cannot learn or override pen-action tracks.
- [ ] feat/evaluate: Permit only evidence-supported bounded terminal/entry adaptation, pen-lift/air-transition planning and spacing. A space breaks ink contact unless an explicit reviewed convention allows otherwise; interior word strokes remain unchanged unless a predeclared supported rule names them.
- [ ] feat/evaluate: Preserve the accepted deliberate gesture actions, constant pressure/speed and no reservoir depletion, fatigue, stochastic rhythm, tremor or warp. Neutral means no session effects, not erasing accepted orientation/contact actions. Normal geometric carryover cannot introduce hidden session effects.
- [ ] feat/evaluate: Compare a fixed word alone, before and after different words, at different legal gaps and at line boundaries. Freeze new word-sequence evaluation cases before fitting, separate from the within-word training vocabulary.
- [ ] feat/evaluate: Use no-context, spacing-only and boundary-stroke-context ablations; cap each at 5000 rendered targets or 1800 seconds per seed 7/19/41, one diagnosed revision. If the source does not support boundary shape changes, retain the null shape rule and report that result.
- [ ] feat/evaluate: Emit word/line decomposition sheets with primitive occurrence lineage and highlighted boundary deltas. Unsupported text/overflow must fail clearly; preserve the original three-line benchmark and report inventory debt rather than rewriting it to pass.
- [ ] evidence: record red/green commands, actual budget use, hashes, scope and outcome before marking completion.

## Validation Gates

- [ ] S4: word grouping has explicit, bounded and reproducible effects; no cross-space ink, hidden stretching, arbitrary word lookup or global fatigue surrogate appears.
- [ ] The same word retains identity across held-out sequences; spacing-only changes and actual stroke changes are reported separately.
- [ ] All five abstraction levels and their action profiles remain traceable in actual session-neutral trajectories. Missing or unsupported context evidence yields a disabled/null rule, not invented historical behavior.
- [ ] Publish an unseen-word-sequence specimen and stop/revise/proceed decision; real G1/G2 and expressive acceptance remain separate downstream requirements.

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

- Added to Pass 15 phase `td018-word-context`.
- Deferred expressive work until strokes, letters and both context levels are proven.

### 2026-09-06 — plan: Require gesture/action readiness

Word context preserves accepted deliberate gesture actions rather than forcing
fixed nib orientation; session effects stay deferred. New evidence uses v2.

## Check for Understanding

1. What changes are learned at this layer, and which lower-layer parameters stay frozen?
2. Which visible transfer test prevents this layer from merely reproducing supplied shapes?
