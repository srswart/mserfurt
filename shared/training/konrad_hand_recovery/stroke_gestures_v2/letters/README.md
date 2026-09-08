# CURRICULUM-005 — bounded letter assembly

This opt-in experiment fits **where frozen gestures are assembled**, not new
curves. It starts with the audited synthetic `n`, `u`, `m` constructions.
Supplied letter labels are hypotheses, not verified historical readings.

## What can change

| Letter | Frozen gesture sequence | Expanded primitives |
|---|---|---:|
| n | stem, lift, overturn | 4 |
| u | underturn, lift, stem | 4 |
| m | overturn, lift, overturn | 6 |

There is one recipe topology per letter. Only the second gesture's x/y placement
is selected from the frozen 30-point grid. The first gesture, all internal
primitive controls and gesture attachment scales, action tracks, tool, advance,
uniform scale, rotation and logical/visible mappings remain frozen. No independent
per-letter curve, macro, finishing pass, ink change, fatigue or context overlay
is permitted. The accepted contract's six-reference cap is not increased.

The letters share the **same stem primitive**, including the stem inside both
return gestures. The negative substitution proof changes one shared stem control
and demonstrates propagation across all three expanded recipes; that mutant is
rejected by lineage, never rendered, fitted or admitted.

## Evidence boundary

The live HANDVALIDATE-018 reader verifies the literal report SHA and requested
underturn/overturn inventory. It does **not** independently admit the standalone
stem used by `n/u`, nor does a gesture pass certify a letter. This is synthetic
scaffolding with that unresolved input, as explicitly permitted by the Advance.
No S2, real-hand, context-training or production-default promotion is issued.

`--real` fails before opening source pixels: no live reviewed G0/native letter
allocations or accepted real lower-layer checkpoint is supplied to this runner.
The other audited starter characters remain unresolved here, not aliased to
`n/u/m`. Counter-bearing letters and continuous seven-reference alternatives are
excluded. These open synthetic constructions do not prove closed counters.

## Frozen protocol

- [Specification](spec-v1.json): all inventory, transforms, targets, splits,
  losses, budget ceilings and source identities precede rendering.
- Three arms: learned shared placement, unchanged prior assembly, frozen catalog
  independent-form diagnostic. The catalog arm uses its exact Unicode cubic
  paths with matched physical frame/tool/layout, not its original ink renderer.
  It is geometry-only: no fabricated shared ownership or actual-controller claim.
- Seeds 7, 19 and 41 each have separate first/replay processes with distinct
  Python hash seeds. Each arm/seed has a cumulative ceiling of 5000 renders and
  1800 seconds including replay. Equal ceilings do not imply padded equal work.
- Train/development use isolated synthetic observations. Development selects
  from the four best training placements plus initialization. Checkpoint and
  evaluation freeze are written **before** transformed repeats and unseen exact
  pairs `nu`, `um`, `mn` are measured. Pairs are transfer probes, not learned words.
- Independent analytic target families are unchanged from the foundation work.
  New synthetic letter placements are declared separately; no target function
  receives a candidate model. These are same-family observations, not new hands.
- Global and per-letter actual/target loss must be at most **0.05**, and repeat/
  unseen nominal loss must be less than **0.75** of initialization. Lifted ports
  must be within the predeclared **0.13 x-height** attachment gap. Actual execution
  retains inherited motion, ownership, contact-boundary and frame guards at base,
  finer arc and finer time steps. No new source-subdivision proof is claimed.
- The common **[-2, 20, 2, 13] mm** frame is checked before image comparisons.
  A uniform **-0.2 x-height horizontal origin**, shared by every arm and target,
  keeps the wider `m` below the existing +/-2 primitive-reference offset limit.
  It changes no target/candidate relative placement or compiler bound.
- One separately diagnosed revision is allowed. There are no automatic retries;
  existing output paths are immutable and failed evidence must be retained.

## Reproduce

From the repository root, on an unused run path:

```sh
.venv/bin/python -m pytest tests/test_letter_recipes.py -q
.venv/bin/python -m scribesim.curriculum.letter_recipes
```

The second command refuses to overwrite the published `run-001`; it is not a
rerun command for an already completed checkout. A new attempt requires a
separately frozen protocol and must preserve the previous bundle.

## Samples and results

**COMPLETE — synthetic assembly/transfer pass, not S2 acceptance.** All three
seeds select `n: [0.08, 0]`, `u: [0.02, 0.34]`, `m: [0.02, 0.34]` second-gesture
translation deltas. The three candidates have identical bytes.

| Letter | Worst local actual/target loss | Repeat nominal loss / initialization |
|---|---:|---:|
| n | 0.013008 | 0.02908 |
| u | 0.016607 | 0.11206 |
| m | 0.019452 | 0.04633 |

All global and letter-local losses satisfy 0.05; repeat and unseen-pair benefit
ratios satisfy 0.75. All declared attachment, exact ownership, contact-boundary,
full-frame, base/arc/time execution and convergence checks pass. These are
condition-specific synthetic metrics, not confidence in reading the letters.

The frozen prior's repeat nominal losses are 0.41898 / 0.10794 / 0.40100 for
`n/u/m`; catalog diagnostics are 0.79596 / 0.79530 / 0.83459. This comparison
does not rank historical authenticity or appearance: the catalog is not the
source of these independent synthetic targets.

**2652 renders total**, including all first/replay workers: shared **476**,
prior **300**, legacy **108** per seed. The largest cumulative arm/seed time is
**582.531 seconds**, below 1800. All nine arm/seed pairs replay exactly.
Each shared worker scores 105 proposals (90 training, 15 development), including
13 compiler-invalid proposals retained with the frozen failure score rather than
rendered. These are bounded search rejections, not retries or experiment revisions.
Each prior worker scores only its six unchanged train/development observations.
No lower-layer fitting, attempt revision or automatic retry occurs.

- [Interactive sample index](index.html)
- [Seed 7 full workbook](run-001/seed-7/shared/first/workbook.png)
- [Seed 19 workbook](run-001/seed-19/shared/first/workbook.png) / [seed 41 workbook](run-001/seed-41/shared/first/workbook.png)
- [Numbered stroke assembly](run-001/seed-7/shared/first/construction.svg)
- [Candidate and recipe listing](run-001/seed-7/shared/first/candidate.json)
- [Selection](run-001/seed-7/shared/first/selection.json) / [shared-parameter propagation proof](run-001/seed-7/shared/first/reuse.json)
- [Experiment report](run-001/report.json) / [cumulative ledger](run-001/execution.json)

The workbook keeps native **900 DPI** panels. The vector construction diagram
shows first gesture, two-gesture assembly, and numbered primitive contributions;
it is a structural path diagram, not a substitute for the actual ink panels.

The report SHA-256 is
`a587f212aa62c2a4742e4d7601a814d3932a5a903e5e993947c9116c4ebe0c12`.
Selected candidate file SHA-256:
`d522b14f3470101603d957332016c257d2c8a1a1d7f41d0d66d542acf5644734`.

Validation: **287 broader tests pass**; **40 new-module tests pass**, also in a
clean committed checkout. The native seed-7 workbook was visually inspected;
no human reading approval or provider CI is claimed. The installed strict PR
parser still fails to recognize explicit `ADV-SS-*` metadata; artifact doctor
retains ten inherited issues. Read-only provenance inspection (no fitting or
rendering) is available with:

```sh
.venv/bin/python -m scribesim.curriculum.letter_recipe_evidence
```

## Remaining letter-shape issue

The workbook visibly retains diagonal rises and unequal heights. This is not
an ink or clock defect: the frozen underturn and overturn both have entry-to-
exit displacement **[1.02, 0.34] x-height**. Translation cannot remove that
internal 0.34 height difference. Aligning a second overturn to the first one's
exit therefore makes the synthetic `m` climb. The low image loss measures
faithful assembly of that target, not a satisfactory letterform.

As a geometric investigation only, rotating that displacement by approximately
**-18.435 degrees** would make its endpoints level. No such rotation has been
fitted, rendered or accepted here; its tool/shape/placement bounds and fresh
evaluation would need to be frozen separately. The next useful experiment is
baseline/x-height-compatible gesture placement/rotation, rather than new cubic
handles or fatigue. Preserve this target and evidence, and resolve the standalone
stem's independent admission before treating a new result as S2 readiness.
