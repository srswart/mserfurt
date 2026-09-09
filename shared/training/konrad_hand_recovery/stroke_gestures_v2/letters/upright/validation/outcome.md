# HANDVALIDATE-021: partial actual results; evaluation still incomplete

The authorized continuation produced actual physical-ink n/u/m samples, then
stopped in the finer-arc translated `mu` probe. **No full protocol pass or acceptance.**
The approved candidate, original target and gates remain unchanged. Open
`index.html` for saved nominal/actual/analytic comparisons.

## Authorized continuation

- Owner: “Yes approved - go ahead.” Authorization is in
  `continuation-001/authorization.json`; runner frozen at `961f69d`.
- Immutable archive: `continuation-001/run-001/`, evidence commit `28b1b30`.
- Consumer-pinned report SHA256:
  `cc4a202e570d292ad899493e5ca53e7cad7b4f796f5e87349af5274d9e587b5c`.
- Nine saved complete four-refinement fixture records: four primitives, two
  gestures and n/u/m. Seed 7's **first process only**.
- `placed-mu` stopped with `Exact unique corner port required` in its 0.0125-mm
  arc plan. Base work began, but there is no complete saved fixture record and no
  substituted comparison. No replay, seeds 19/41 or complete control suite ran.
- 147 continuation render calls; **149 combined** with the original two calls.
  Combined seed-7 execution time: **34.57516137394123 seconds**, within the unchanged
  5,000-render/1,800-second cap. Remaining budget is not retry permission.
- Zero optimization; no further attempt after this stop.

## Independently checked partial results

`scripts/handvalidate_upright_partial.py` verifies **180 artifacts** and all nine
saved records/four refinements using original traces, metric pixels and masks.
It neither renders nor executes/fits. Receipt: `continuation-001/partial-inspection.json`.
Red `7a283bd`, green `a2c938b`; two partial-reader tests pass. The broader suite
before these two additions has 100 passes. Five unrelated old admission failures
remain independently reproduced on pre-work master, not silently repaired.
Final focused validation including the partial reader: **102 passed in 44.64 s**.

| Seed-7 letter | Per-run motion checks | Maximum port error, all refinements | Base target loss | Relative loss |
| --- | --- | ---: | ---: | ---: |
| n | pass | 0.006925 mm | 0.382013 | 0.609119 |
| u | pass | 0.019878 mm | 0.232051 | 0.279661 |
| m | pass | 0.011017 mm | 0.589663 | 0.662173 |

Each letter has one continuous contact run. Saved audits show no owner/contact/
tool/dynamics errors, projection or undeclared overlap pairs, and zero total clock
error. Maximum level residual is below 0.000603 mm. Port errors are below 0.05 mm.
These are per-run measurements, **not whole-protocol acceptance or replay**.

Image losses exceed the unchanged absolute/local **0.05** gate; relative ratios
are below 0.75. The independent semicircle yardstick is not an owner-approved
replacement for the letters. Its mismatch cannot revoke nominal KEEP or justify
silently changing targets/shapes.

Saved convergence gates also fail: first/last per-gesture integration samples
shift with resolution, producing reported event differences up to 0.008 s and a
u arc endpoint difference of 0.012086 mm (limit 0.01). Reading saved **exact corner
and terminal timestamps** instead gives zero base/arc/time difference and at most
2.10e-13 s for subdivision. This points to event-selection measurement trouble,
not total-clock drift. No saved result or threshold has been rewritten to pass.

## Placement diagnosis: no new motion or render

At 0.0125-mm arc step the frozen `placed-mu` plan has two m-corner samples:

- Index 631: incoming owner `0:2`, parameter `0.9999999999999996`, position
  `[1.0280566424274427, 10.031499999999998]`, no boundary contributors.
- Index 632: outgoing owner `0:3`, parameter `0`, exact position
  `[1.0280566424274427, 10.0315]`, both boundary contributors present.

Separation is **1.7763568394002505e-15 mm**. `_arc_samples` keeps an ordinary grid
target and exact boundary target through exact `np.unique`; the planner finds
both inside its unchanged 1e-8-mm tolerance and rejects the ambiguous port. The
base 0.025-mm plan has one match. Do not weaken the planner's uniqueness check.

## Next scope needed

1. Canonicalize near-coincident arc-grid/boundary samples while preserving the
   exact outgoing port, both contributors, geometry and caps; test translated
   continuous/retrace cases without loosening uniqueness.
2. Compare identical declared entry/corner/end events for convergence, rather
   than resolution-dependent first/last integration samples.
3. With new bounded authorization, freeze repaired code and remeasure the same
   candidate with unchanged targets/limits and both prior debits preserved.
   Image-target failure remains a separate unresolved gate.

The authorization permitted one attempt, not unlimited repairs/reruns. This
Advance remains **in progress and unmerged**. Actual-ink review is pending in
`continuation-001/actual-review.json`; S2/real/context remain false. Original
candidate/report/nominal KEEP hashes are unchanged.

## Original pre-score failure (historical snapshot)

**No numeric pass, candidate failure verdict, actual-ink sample or new acceptance.**
The first immutable attempt stopped before scoring with
`Unsupported physical contact fields`. Its nominal adapter forwarded NumPy
`float64` coordinates to the physical contact boundary, which deliberately accepts
Python `float`/`int` scalars only. This is an evaluator implementation defect, not
evidence that the owner-approved n/u/m shapes failed.

- Frozen implementation: `495c119`.
- Preserved failed archive: `run-001/`, evidence commit `c722bd1`.
- Consumer-pinned report SHA256:
  `6f4678661d6d5103311ac88040f29ad36cd0247d03c45fb9909e0145e4685421`.
- Seed 7 first process: two charged render calls, no completed scored fixture.
  No replay or seeds 19/41 ran. The second charged render raised an exception.
- Scalar-boundary regression test fails before repair (`50b5330`).
- Repair `21151c4` converts scalar types without rounding, moving points, changing
  the nib or modifying any target/threshold. It does not modify the frozen archive.
- Eight evaluator tests plus the adjacent construction/connection/action tests:
  **49 passed**. The five older curve-tangent admission failures also reproduce
  unchanged on pre-work commit `85e3b44` (22 passed, five failed in that file).
- Plan, generated-rule and whitespace checks pass. The installed strict PR
  metadata parser still returns `ids=[]` with explicit IDs. No provider CI claim.

## Historical pending request (superseded by continuation above)

The frozen protocol permits **zero automatic retries**. A request for one explicit,
bounded no-refit continuation is pending. No continuation has been run. If approved,
freeze a new continuation authorization/code identity and output directory, bind
the prior failed report hash, account for its two charged calls in the combined
seed-7 budget, and retain the same candidate, target, fixtures and numeric gates.
Do not overwrite `run-001` or pretend its failure never occurred.

Then complete seeds 7/19/41 with fresh-process replay, independent reader checks,
full-frame evidence, adversarial controls and actual-ink owner review. Until then,
HANDVALIDATE-021 remains **in progress and unmerged**, not complete or accepted.
S2, real-hand acceptance and context permission remain false.

The original nominal KEEP review and candidate/report/review hashes are unchanged.
The original approved examples remain at `../run-001/index.html`.
