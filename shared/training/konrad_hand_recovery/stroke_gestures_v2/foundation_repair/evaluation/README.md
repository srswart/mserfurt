# HANDVALIDATE-016 — Independent frozen-gesture evaluation

## Result — scoped PASS, 2026-09-08

All three frozen seeds pass the independent gesture gate in `run-002`, including
fresh lower-layer proofs, all eight gesture fixtures, three overlap/space
contexts, four refinements and all nine gesture adversaries. Each first/replay
pair matches **115 non-wall-clock artifacts** exactly. Every candidate remains
byte-identical to CURRICULUM-011; no optimization or refitting occurs.

Report SHA: `b564aa11e5752b5d0af0a6cb6ced5671b38b78d1cee62bcca0e07bf29de66f75`.
The strict current-code reader and both explicit pen-action consumers verify it.
They permit only next-experiment scoping; action fitting and letters stay blocked.

| Held-out pairing | Learned / initial full loss, every seed |
|---|---:|
| Underturn / overturn | 0.157574 |
| Overturn / underturn | 0.157807 |
| Compound / terminal | 0.132465 |
| Repeated underturn | 0.066255 |
| Independent scaled/offset attachment | 0.154040 |

Maximum occurrence-local ratio is 0.408835 (<0.75). Across gesture/context
proofs, actual/desired loss <=0.010409, corridor <=0.007936 mm and refinement
endpoint difference <=0.005718 mm. All **912 individual contact-boundary
measurements**, including replay, meet position and prescribed-velocity gates.
No aggregate image score substitutes for those individual checks.

The continuation uses **3546 new +3528 retained =7074 renders**, or **2358/5000
per seed**. Cumulative seed times remain below 1800 seconds. All 109 pre-existing
non-report/non-clock worker artifacts are unchanged in each of six workers.
The failed attempt's 668 manifest artifacts and current attempt's 698 manifest
artifacts verify. The global 0.1 guard still misses all six measured small
gesture defects: four are pixel-identical owner/contact errors, painted air
scores 0.001109 and a filled pocket scores 0.010768. Exact/local guards catch them.

- [Layered sample index](../index.html)
- [Seed 7 native 900-DPI comparison workbook](run-002/seed-7/first/practice-sheet.png)
- [Seed 19 workbook](run-002/seed-19/first/practice-sheet.png)
- [Seed 41 workbook](run-002/seed-41/first/practice-sheet.png)
- [Declared-overlap actual](run-002/seed-7/first/declared-overlap-actual.png)
- [Adjacent-carrier actual](run-002/seed-7/first/adjacent-carriers-actual.png)
- [Spaced-carrier actual](run-002/seed-7/first/spaced-carriers-actual.png)
- [Original-six fresh gallery](run-002/seed-7/first/primitives/original-six-gallery.png)
- [Current report](run-002/S1-gestures.json), [retained failed report](run-001/S1-gestures.json), [verification](verification.json)

**Validation:** 33 focused tests pass locally and in the final clean committed
checkout (the earlier clean check passed 27 before six evidence regressions). Expanded
tests: 269 pass, with the same 12 pre-existing failures recorded by CURRICULUM-011.
Plan/link/diff checks pass; artifact doctor retains its same 10 inherited issues.
The installed strict PR parser still returns `ids=[]` despite the Advance ID in
title, body and label. No provider CI, push or human appearance review is claimed.

Initial code: `6fbff6a`. Diagnosed continuation code: `5799ebf`. Both experiments
run from clean committed worktrees with the existing environment's interpreter.
Native PNGs were visually inspected; no browser validation is claimed.

Completion commit `ffd3ef4` is merged locally into `master` as
`9af3a7b238353891dd11b9b57eb61972bcc3eaec`. Post-merge plan and strict live
foundation admission verify. Final clean-checkout focused tests: 33 passed.
No push or provider CI was performed; the installed PR parser limitation remains.

## Acceptance boundary

This evaluates the three frozen CURRICULUM-011 candidates, without fitting or
calling the learning evaluator. The independently admitted primitive curves,
shared attachment scales, tool, compiler and controller stay unchanged.
The diagnostic `i`, `ii` and `i i` carriers are not learned letters or words.

A passing report permits **scoping a new bounded action/null experiment**, not
running the old action fitter. It is not S1-action, accepted null behavior,
letter readiness, real G0/G1/G2 or owner appearance approval. Existing historical
reports remain immutable. Missing inventory and local/global failures are explicit.

## Independent implementation

- `scribesim/handvalidate/foundation_gestures.py` reconstructs the frozen candidate
  lineage independently, loads the matching live primitive gate, and requires
  exact candidate bytes for seeds 7, 19 and 41.
- Before any new target render, `spec-v1.json` freezes independent analytic
  endpoint/derivative targets, full frames, held-outs, controls, criteria and
  budgets. The evaluator uses its own Hermite basis implementation and local
  regions; it does not call the learning target, scoring, control or search code.
- Every worker freshly reconstructs the original six and current-mode motion
  baseline, then reevaluates all five frozen primitive fixtures and their seven
  adversarial controls before measuring gestures.
- Gesture proofs cover three continuous constructions, four frozen held-out
  pairings and a separately authored scaled/offset attachment pair. All four
  refinements run: base, half arc step, half timestep and exact subdivision of
  every cubic. Paired probes use the existing cap-preserving compiled adapter;
  repeated/spaced text uses the existing legacy diagnostic subdivision adapter
  with three occurrences per recipe, not a relaxed grammar limit.
- Context proofs include declared coincident overlap, adjacent carriers and a
  word-space carrier. Exact owner/contributor/span/air checks reconstruct the
  timed source plan and inspect each actual trace row. Every contact group has
  separately saved entry/exit position, velocity and event-time measurements.
- Arrival speed remains <=0.5 mm/s; an exit follows its frozen plan velocity
  within 0.5 mm/s, not an invented zero-speed stop for a prescribed moving lift.
  This interpretation was finalized before new acceptance renders. Position
  error is <=0.05 mm at each boundary, refinement endpoint difference <=0.01 mm
  and event difference <=0.0001 seconds. No old threshold is relaxed.
- Full and occurrence-local held-out loss ratios must each be <0.75. Blank
  fractions stay <=0.01. Actual/desired image loss <=0.35, corridor <=0.25 mm
  and refinement image loss <=0.03 remain unchanged.
- Nine gesture controls cover wrong ports/directions, detached copies, hidden
  lifts, extra contributors, wrong owners, painted air, missing declared overlap
  and filled open-return pockets. Whole-image 0.1 misses remain visible. The
  inherited primitive counter controls run freshly too; an open pocket is not
  proof of a closed learned letter counter.

## Immutable attempts

Run-001 reaches all eight gesture fixtures and three contexts, then its
painted-air adversary exposes a reporter defect: an air owner has no occurrence
ID, and mixing `None` with string IDs crashes the sorted diagnostic list.
The runner records a blocked worker, not a successful control. All first/replay
artifacts and render/time charges are retained. The negative trace must be
reported as an undeclared contributor rather than crashing.

The one diagnosed continuation changes that missing-ID representation only in
the audit and adds explicit retained-attempt accounting. The frozen target,
geometry, control mutations, candidate/primitive/tool/controller and all metric
functions remain unchanged. `continuation-v1.json` pins the failed report,
ledger, spec and unchanged function hashes; every failed render and second is
charged against the same seed's 5000-render / 1800-second allowance. No refit.
Another rerun or relaxed criterion requires a new explicit decision.

## Reproduction and consumers

Use an appropriate clean checkout of the committed evaluator. Initial execution:

```sh
.venv/bin/python -m scribesim.handvalidate.foundation_gestures \
  --output shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/evaluation/run-001
```

The diagnosed continuation uses its retained original evidence:

```sh
.venv/bin/python -m scribesim.handvalidate.foundation_gestures --continuation \
  --output shared/training/konrad_hand_recovery/stroke_gestures_v2/foundation_repair/evaluation/run-002
```

Existing output directories are immutable; these commands intentionally refuse
to overwrite them or silently begin another attempt. First/replay subprocesses
use `PYTHONHASHSEED=0` and `839`. Wall-clock receipts are excluded only from
deterministic byte comparison, never from the artifact manifest or budget.

The explicit admission API is:

```python
from scribesim.handvalidate.foundation_gestures import require_readiness

require_readiness(report_directory, expected_report_sha256=consumer_pinned_sha256,
                  required_gestures=['underturn', 'overturn', 'compound_curve'])
```

Both pen-action modules expose `foundation_prerequisites(...)` with the same
manifest/SHA/inventory arguments. The curriculum CLI adds
`--foundation-manifest`, `--foundation-sha256` and repeated `--required-gesture`;
the independent pen-action CLI offers the separate `foundation` command. These
return an explicit **blocked action status** even when foundation eligibility
passes. They cannot send a new foundation pass into the old learning routine.
Real scope remains blocked without live G0 and real lower layers.

## Next work

[CURRICULUM-012](../../../../../../arrive/systems/scribesim/advances/ADV-SS-CURRICULUM-012.md)
must freeze and execute a bounded action/null experiment on admitted inventory.
Prefer an affirmative fixed-tool null hypothesis unless a named local defect
justifies a physical pen action; the existing fixed dictionary is not itself
null acceptance. [HANDVALIDATE-017](../../../../../../arrive/systems/scribesim/advances/ADV-SS-HANDVALIDATE-017.md)
then independently evaluates the actual selected candidates and the previously
unexecuted action controls. CURRICULUM-005 stays blocked until that new matching
S1-action/null and its other prerequisites pass. No alphabet fitting is run here.
