---
advance:
  id: "ADV-SS-CURRICULUM-014"
  title: "Letter Assembly — Baseline and X-height Compatible Gesture Transforms"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum", "handvalidate", "gesture", "tests"]
  started_at: "2026-09-08T16:54:02Z"
  implementation_completed_at: "2026-09-08T17:38:15Z"
  review_time_estimate_minutes: 348.2
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 110
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit"]
  model_usage: []
  status: complete
---

## Objective

Remove the translation-only construction's 0.34 x-height staircase using whole
gesture transforms, with no context, fatigue or primitive refitting.
Follows [TD-018 Addendum B section 11](../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#11-level-assembly-and-standalone-stem-admission).

## Behavioral Change

Derive bounded rotation from each return gesture's endpoint chord, and uniform
scale/translation from exact cubic extrema, so each open construction spans
baseline 0 to x-height 1. Attach repeated arches at level ports. Keep n/u/m's
4/4/6 references, two lifts, exact text and fixed nib actions. Independently
normalize the existing analytic target families in a NEW target version; never
edit CURRICULUM-005's old targets/results. This is a constrained assembly solve,
not new stroke learning or evidence of historical legibility.

## Dependencies

- [ADV-SS-CURRICULUM-005](ADV-SS-CURRICULUM-005.md)
- [ADV-SS-HANDVALIDATE-019](ADV-SS-HANDVALIDATE-019.md)

## Component Impact

- `scribesim/curriculum/letter_alignment.py`: deterministic bounded assembly and frozen physical evaluation.
- `scribesim/curriculum/letter_alignment_evidence.py`: no-render receipt reconstruction and numeric adjudication.
- `tests/test_letter_alignment*.py`: source/target isolation, geometry, bounds and decision regression tests.
- `shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/alignment/`: versioned protocol, immutable bundle, separate adjudication and full-frame samples.
- ARRIVE plan/component interfaces and sample links; no new component, stage or production-default changes.

## Planned Implementation Tasks

- [x] branch: `advance/ss-curriculum-014` after the standalone-stem merge.
- [x] tidy: preserve pinned lower layers; reuse immutable replay protocol unchanged.
- [x] test: missing-module red commit `6f2c8cb`; 15 landmark/bound/lineage/target-isolation tests pass.
- [x] feat/fix: exact extrema, chord-level transforms, endpoint-compatible lifted attachment; no detached curves or macro cap bypass.
- [x] evaluate: all numeric/physical gates pass for nine fixtures and three seeds/replays; 768 renders, 256 per seed, maximum 243.501 seconds, zero fitting/retries.
- [x] evidence: old-vs-new ink, full-frame decompositions, no-fit adjudication and live stem consumption; local merge receipt follows.

## Bug Fixes

Translation alone cannot level a gesture's nonhorizontal endpoint chord.
Independent normalization must not quietly normalize a candidate to its target
pixels, anisotropically warp a curve or introduce per-letter primitive copies.

The frozen checker rejects a finite NumPy float64 ratio before serialization,
while accepting its identical JSON-restored float. Workers therefore retain
`passed=false` while the post-reload root says `pass`. Both original receipts
remain immutable. The separate read-only evidence reader reconstructs both
decisions and normalizes only the finite scalar type before applying every
unchanged gate. It does not rerender, refit, replace targets or rewrite receipts.

## Risk + Rollback

Whole-gesture rotation changes shape/tool interaction and is not independently
admitted by the old unrotated return reader. Measure actual motion and image
quality for every new occurrence; retain S2/real/context flags false pending
independent new-transform acceptance and appearance review. Preserve old evidence
and remove only the new opt-in experiment to roll back.

## Evidence

- [x] tdd:red-green: assembly and both diagnosed reader corrections have separate red/green commits.
- [x] 112 broader tests pass in 56.64 seconds; 31 new-module tests pass in clean `beece9b` checkout (4.39 seconds).
- [x] [Frozen specification, numeric adjudication and samples](../../../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/alignment/README.md).
- [x] Live read-only audit verifies all 422 artifacts, six worker proofs and cumulative budgets; all three seeds replay 69 non-clock artifacts exactly.
- [x] Original strict reader rejects the preserved worker/root discrepancy with `Worker decision differs from measured evidence`.
- [x] Plan, generated rules, whitespace, sample links and unchanged diagram paths pass; workbook and padded SVG are visually inspected.

## CI Evidence Notes

Run local ARRIVE/PR metadata checks; do not claim provider CI from local tests.

## Changes Made

### 2026-09-08 — merge: local completion receipt

Completion `756f0ee` merged into `master` as `8a49a71`, following the separate
HANDVALIDATE-019 merge `99b58c4`. Post-merge verification confirms both report
pins, current frozen code identities, exact manifests (140 stem / 422 assembly
artifacts), and byte identity of the live-audited adjudication and reader.
Plan, generated rules and whitespace checks pass; the worktree is clean before
this documentation-only receipt. No push, provider CI or acceptance promotion.

### 2026-09-08 — feat: complete bounded compatibility repair

The worst nominal baseline/x-height/attachment residual is 2.483e-16 x-height;
worst actual centerline-extrema residual is 0.000108295 mm (limit 0.05 mm).
Worst local actual/target loss is 0.02624499, local nominal loss 0.02633647,
and new/prior nominal loss ratio 0.03797615 (limits 0.05 / 0.75 unchanged).
The new m no longer climbs, but the shared strokes remain slanted; no historical
legibility or S2 approval is inferred. Nine fixtures, including fresh un/mu/nm,
pass exact lineage/contact/tool/motion/convergence and full-frame guards.

The live reader returns numeric `pass`, verifies 422 artifacts and consumes the
literal HANDVALIDATE-019 admission. It adds zero renders or optimization calls.
Original report SHA-256:
`bd9cf281cb28fbc5bb31dcdaf0646c3cf4b9d7a7d58edad19aa303d4ea11a34c`.
S2, real and context-training flags stay false. Context/fatigue code is untouched;
CURRICULUM-006's notes now identify independent rotated-return evaluation and
appearance/reading review as the remaining gates.

### 2026-09-08 — fix: preserve and adjudicate the serialization discrepancy

Red commits `1b1dee8` and `82d9e5c` precede reader repairs `e13bb58` and `beece9b`.
The second red test captures the final root/worker distinction rather than
incorrectly assuming the root also fails. Execution code/specification remain
frozen at `350dfc6`. Separate reader tests prove numeric round-trip invariance,
invalid-value rejection, unchanged physical/image gates, pinned-source failure,
and no rendering or evidence mutation. The ordinary strict reader is not used
to silently bless inconsistent historical decisions.

Reviewability Red 110 / 348.2 estimated minutes is dominated by the complete
generated six-worker manifest. Test, implementation, diagnosed reader repair and
evidence commits are split; the immutable replay bundle is kept inseparable.
No actual human review time or provider CI is claimed. The installed strict PR
metadata parser still returns `ids=[]` for explicit ADV-SS-CURRICULUM-014
title/body/label metadata; existing component-schema warnings remain unrelated.

### 2026-09-08 — feat: freeze exact level assembly before rendering

No optimizer or candidate search is required. Endpoint chords give approximately
-18.435 degrees, with uniform source-derived scales 0.9546734 (underturn) and
0.9710506 (overturn). Each transform is shared across every occurrence of that
gesture; all underlying primitives/actions remain identical. Nominal baseline,
x-height and attachment residual limit is 1e-8 x-height; actual extrema use the
existing 0.05 mm physical endpoint tolerance, separately from 0.05 image loss.

Pre-render containment tests caught the rotated underturn's left overhang.
The NEW common frame is [-3,20,2,13] mm, with explicit 0.5/0.25 x-height local
window padding. Old frames, images, specifications and thresholds are unchanged.
All initial/target/nominal/actual panels use the new full frame; no cropped pass.
Nine fixtures distinguish isolated repeats, old-pair regressions and genuinely
new `un/mu/nm` juxtaposition probes. None learns letter context or word spacing.

### 2026-09-08 — plan: register bounded alignment repair

User explicitly requests baseline/x-height-compatible assembly and standalone-
stem admission, excluding context and fatigue. No experiment is executed by
creating this record. Completion of this work will not silently release S2.

## Check for Understanding

1. Why do translation-only ports produce a climbing m?
2. How do exact extrema and uniform transforms preserve shared primitives?
3. Why are the new target version and rotated-gesture acceptance separate from the old pass?
4. Why can identical numeric evidence yield false worker and true root decisions, and how does the reader correct that without rewriting history?
