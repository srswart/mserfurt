---
advance:
  id: "ADV-SS-CURRICULUM-014"
  title: "Letter Assembly — Baseline and X-height Compatible Gesture Transforms"
  system: "scribesim"
  primary_component: "curriculum"
  components: ["curriculum", "handvalidate", "gesture", "tests"]
  started_at: "2026-09-08T16:54:02Z"
  implementation_completed_at: ~
  review_time_estimate_minutes: 40
  review_time_actual_minutes: ~
  pr_links: []
  external_refs: []
  reviewability_score: 0
  risk_flags: ["public_api"]
  evidence: ["tdd:red-green", "tests:unit"]
  model_usage: []
  status: in_progress
---

## Objective

Remove the translation-only construction's 0.34 x-height staircase using whole
gesture transforms, with no context, fatigue or primitive refitting.

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

## Planned Implementation Tasks

- [x] branch: `advance/ss-curriculum-014` after the standalone-stem merge.
- [x] tidy: preserve pinned lower layers; reuse immutable replay protocol unchanged.
- [x] test: missing-module red commit `6f2c8cb`; 15 landmark/bound/lineage/target-isolation tests pass.
- [x] feat/fix: exact extrema, chord-level transforms, endpoint-compatible lifted attachment; no detached curves or macro cap bypass.
- [ ] evaluate: frozen n/u/m and unseen-pair fixtures, unchanged 0.05 absolute and 0.75 relative criteria, new explicit baseline/x-height residual gate, three seeds/replays, 5000 renders/1800 seconds per seed.
- [ ] evidence: old-vs-new ink and decompositions, no-fit receipts, live stem consumption; update and merge.

## Bug Fixes

Translation alone cannot level a gesture's nonhorizontal endpoint chord.
Independent normalization must not quietly normalize a candidate to its target
pixels, anisotropically warp a curve or introduce per-letter primitive copies.

## Risk + Rollback

Whole-gesture rotation changes shape/tool interaction and is not independently
admitted by the old unrotated return reader. Measure actual motion and image
quality for every new occurrence; retain S2/real/context flags false pending
independent new-transform acceptance and appearance review. Preserve old evidence
and remove only the new opt-in experiment to roll back.

## Evidence

- [ ] tdd:red-green
- [ ] tests:unit and clean-checkout validation
- [ ] Immutable source/target/code freeze and numeric landmark/physical evidence
- [ ] First/replay manifest equality and cumulative budgets

## CI Evidence Notes

Run local ARRIVE/PR metadata checks; do not claim provider CI from local tests.

## Changes Made

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
