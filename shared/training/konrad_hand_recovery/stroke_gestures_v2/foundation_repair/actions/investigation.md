# CURRICULUM-012 — Scope investigation before target rendering

## Decision

Test exactly one fixed-tool null hypothesis for underturn, overturn and
compound_curve, using the matching HANDVALIDATE-016 candidates. Do not fit a
rotation, partial edge or extra finishing stroke merely because the previous
action phase did not run. No demonstrated action-specific failure currently
justifies such a change, and the foundation schema deliberately forbids it.

## Existing evidence inspected

The live foundation report is pinned at
`b564aa11e5752b5d0af0a6cb6ced5671b38b78d1cee62bcca0e07bf29de66f75`.
Every candidate file is pinned at
`d8b26fba2655b0bba961865fb74b543829cb1b11ac850afd672dd02ba0822e5a`.
That admission covers the three constructions under curve-tangent-v1 and the
legacy full-edge tool, not actions, null sufficiency, letters or historical ink.

Its saved nominal/independent-target losses are approximately 0.044376 for
isolated underturn, 0.099454 for overturn and 0.098227 for compound. Foundation
acceptance checks relative improvement (<0.75) and motion, while the existing
action contract uses an absolute null actual/target limit of **0.05**. A relative
pass does not establish that stricter absolute condition. Actual/desired tracking
is a different measurement and cannot be substituted for target accuracy.

Thus the remaining gap may already exist in the frozen nominal geometry.
This is a hypothesis to measure, not proof that pen manipulation is necessary
or that a new action profile will repair it. Do not tune the threshold or target
to make the current candidate pass.

## Frozen experiment

- One hypothesis per seed; source bytes, all geometry, reference scales, recipes,
  controller, tool and profile remain unchanged. Selection happens before any
  target access. No optimizer or legacy action fitter is called.
- The independently authored Hermite-plus-sine target family and local regions
  stay frozen. Eleven fixtures cover three diagnostic train cases, three new
  development transforms, three new held-out transforms and two held-out lifted
  pairings. There is no development selection in this null experiment and no
  held-out substitution. This is same-target-family generalization, not a new
  source hand or external artistic-quality validation.
- Retain the absolute 0.05 null cap. Apply the same cap to each occurrence, on
  all four actual refinements, so a good aggregate cannot hide one poor gesture.
  Keep all prior motion/contact/refinement and blank-pocket bounds unchanged.
- Measure nominal/target as well as actual/target and actual/desired, with
  separate per-gesture and rotation/edge/finishing null/unresolved dispositions.
  Shared failure does not identify which, if any, action should be activated.
- Replay overlap, adjacent and spaced diagnostic carriers as mechanical controls.
  Wrong angle, partial-edge requests, undeclared lifts, overbuilt contributors,
  filled open pockets and desired-only substituted actual traces must be rejected.
- Partial-edge model rejection is not physical edge sensitivity. Open pockets
  are not closed letter counters. Those unsupported scopes and independent
  selected-action acceptance remain explicitly unexecuted.
- Seeds 7, 19 and 41 each have 5000 renders or 1800 seconds including first/replay,
  controls and all refinements; zero optimization and at most one diagnosed
  revision. Existing attempts cannot be overwritten or silently restarted.

## Handoff

Publish the exact selected candidate bytes and immutable measurements even if
the null hypothesis is unresolved. HANDVALIDATE-017 must independently review
the frozen candidates and scope before S1-action/null acceptance. If target
error is already present in nominal geometry, preserve it and investigate the
shared-geometry/target contract before proposing dynamic actions. Do not refit
geometry or open letter training in CURRICULUM-012.
