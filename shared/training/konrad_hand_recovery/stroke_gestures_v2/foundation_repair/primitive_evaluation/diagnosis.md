# Required next fix: subdivision-invariant source tangents

**Follow-up completed:** [HANDFLOW-011](../tangent_evaluation/README.md) implements
the opt-in repair and passes independent reevaluation of the same candidates.
This document retains the original failure and pre-repair proposal for provenance.

## Observed failure, not a threshold change

All seeds and clean fresh-process replays reproduce the same compound failure.
Read `seed-7/first/compound-attachment-metrics.json` and the corresponding plan in
[traces.json.gz](run-001/seed-7/first/traces.json.gz), refinement `subdivision`.
Plan samples **48 → 49** straddle the artificial midpoint of the upper return:

| Quantity | Before | After |
|---|---:|---:|
| Time, s | 0.2364483094643398 | 0.2365217713231412 |
| x, mm | 0.9277791789347298 | 0.9281904619688863 |
| y, mm | 9.321053212339491 | 9.321030652450768 |
| Desired vx, mm/s | 5.5951313543235 | 5.5966726700054545 |
| Desired vy, mm/s | -0.30690675342269147 | -0.27738358322799556 |
| Source cubic / parameter | 0 / 0.9995855627384663 | 1 / 0.0 |

The desired speed is unchanged at 5.603542328512419 mm/s. The direction change
over **0.000073461858801388 s** produces **402.43164304831953 mm/s²**,
above the frozen 250 mm/s² limit. Unsplit/base desired acceleration is 126.432562;
arc-refined is 127.940442. Actual subdivision acceleration is 147.491782 and has
zero ownership, geometry, projection, air-ink and zero-time discontinuity errors.

## Evidence-backed diagnosis

`scribesim/evofit/stroke_gestures.py::_arc_samples` derives tangent direction from
a 256-chord approximation independently for each cubic. `build_track_plan` uses
that tangent for desired velocity. `retime_curve_timing` measures elapsed distance
from source curves but retains those chord directions. Adding an equivalent cubic
seam changes the chord on each side; two nearby samples can inherit an artificial
direction jump even when exact cubic endpoint tangents match.

An offline, zero-render diagnostic evaluated analytic cubic derivatives at the
two recorded source parameters, using the same speed and timestamps. Its pairwise
acceleration is **42.68845659587813 mm/s²**. This supports the tangent explanation;
it is not a complete repaired trajectory, a production change or acceptance.

The old `gestures._subdivide` helper only subdivides `stem`. Its passing prior
results therefore did not establish invariance of either new return. The new
independent evaluator retains all those historical results and closes this
coverage gap rather than relabeling them.

## Bounded repair proposal

1. Freeze a separate regression/repair Advance using this selected candidate and
   failing seam. Keep endpoints, ports, target splits, tool, renderer and the
   250 mm/s² limit fixed; zero fitting and no candidate reselection.
2. Use validated source cubic identity/parameter to derive opt-in physical
   velocity directions from analytic derivatives. Preserve sampled positions,
   source ownership, exact text, contact events and elapsed curve-derived clock.
   Specify stationary-derivative and corner behavior; do not guess a nearest curve.
3. Test equivalent subdivision of both returns and every original family,
   density/time refinements, lifted re-entry, corners, overlapping contributors
   and zero-time events. Do not hide failures by dropping seam samples, clamping
   measured acceleration or making a controller pose reset.
4. Refresh the original-six baseline and full motion acceptance under the new
   execution identity. Explicitly audit compatibility with frozen candidates;
   old source code hashes remain immutable and must not be silently rewritten.
5. Replay all three frozen candidates and all mandatory independent proofs with
   an explicitly frozen no-refit protocol/current-code admission. Keep run-001 and
   its false S1 flags intact. Stop if any required family/refinement/control fails.

This diagnosis itself did not implement a repair or additional attempt. The
subsequent linked follow-up now provides matching new-mode admission; CURRICULUM-011
remains planned, but can freeze that admission before its separate experiment.
