# Geometry-derived clock — run 005

**PASS: all 239 motion gates and the fresh six-primitive baseline.**
HANDFLOW-010 is complete for fixed-tool synthetic motion. No new learning,
S1-action, letter construction, real-hand or owner appearance acceptance.

## What changed

Contact timing now integrates the underlying cubic curves rather than summing
sample chords. Opt-in metadata carries cubic identity, parameter and source
representation; the planner validates reconstruction, monotonic order and full
endpoint coverage. No nearest-point search confuses loops or overlapping strokes.
The bounded integrator compares 16/32-point quadrature with 1e-10 mm estimated
absolute error, depth <= 12 and <= 4096 panels; exhaustion fails closed.

Corner slowing, curvature-derived speed ceilings, air braking and the controller
remain unchanged. All source positions/tangents, fixed tool state and owners are
preserved. Legacy modes remain the defaults; this is explicit `curve-time-v1`.

## Results

- Arc-density event-time drift: **0** for every recorded fixture, including the
  fixed physical-edge bridge; previously up to **0.437750 ms**.
- Exact cubic subdivision: maximum event-time shift **8.881784197001252e-16 s**,
  below the unchanged **0.0001 s** limit. Time-step refinement also passes.
- Maximum contact lag across 27 target fixture/refinement/physical runs:
  **0.007411 mm**, against **0.25 mm**.
- Endpoint refinement <= **0.005848 mm**; all image comparisons pass.
- Maximum corner speed **0.019136 mm/s**, corner position error **0.000939 mm**;
  no lift at corners, air ink, pose reset or source-geometry changes.
- Desired acceleration <= 250 mm/s² within floating-point tolerance; actual
  maximum **251.508454 mm/s²**, against the unchanged 500 mm/s² limit.
- Original six synthetic-trained primitives pass fresh nominal/actual baseline
  checks without refitting or edited historical identities.

The conservative corner policy is unchanged, not optimized rhythm: saved-u
planned duration is 3.571722 s versus run-004's 3.571327 s. The tiny duration
change corrects curve measurement, not a new slowdown strategy.

## Samples

- [Six primitives, nominal / actual](primitive-gallery.png)
- [Six controlled constructions and actual motion](comparison.png)
- [Browsable findings and history](../../index.html)

Presentation rerenders at native 900 DPI and only downsamples. Evaluation uses
its frozen 180 DPI. L-like constructions are supplied stem-terminal motion
fixtures, not learned letters. Similar-looking ink is expected for a clock-only fix.

## Evidence and verification

Red tests `e8b55fe`; implementation `c95a730`. [Freeze](freeze.json),
[report](report.json), [baseline](baseline.json), [full traces](traces.json.gz),
[wall receipt](execution.json), [ledger](../ledger.json),
[clean verification](../clock-verification.json). Prior attempts are unchanged.

One separately authorized spec-v5 candidate: 303 renders in 22.987616 s, zero
optimization and zero revisions. Hash-seed-839 clean replay uses 303 separately
labeled verification renders in 19.227469 s. Report rows/checks/decision, freeze,
baseline, traces and PNGs are byte-identical; wall time is not an identity gate.

40 focused tests pass. Expanded local and clean-checkout suites each have
106 passes and one pre-existing missing-`nib_angle_deg` constructor failure in
test_handflow.py. Older frozen-code-identity failures retain their previously
documented pre-repair status; no stale tests/hashes are weakened here.

Plan validation passes; artifact doctor retains ten pre-existing issues; generated
agent rules are not stale. Strict PR check ran, but the installed parser does not
recognize ADV-SS-HANDFLOW-010. No successful strict check or provider CI is claimed.

Replay from implementation commit c95a730 in a clean checkout and a new directory:

```sh
PYTHONHASHSEED=839 /absolute/path/to/.venv/bin/python -m scribesim.handvalidate.foundation_motion --output /tmp/curve-clock-replay-new
```

Next: GESTURE-002's return vocabulary/port and composition-limit audit. Later
learning must consume verified current evidence; motion acceptance alone does
not accept new primitives, dynamic actions, letters or real references.
