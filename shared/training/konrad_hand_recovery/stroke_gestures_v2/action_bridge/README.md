# Realized intentional-action bridge

**Implementation complete; convergence acceptance FAILS. No learned action or
letter readiness is claimed.**

[Comparison sheet](run-002/action-comparison.png): dense desired, sampled
desired, bounded actual and deliberately slowed actual. Five declared profiles
use identical supplied i/u centerlines: fixed, rotation, negative/positive edge
release and an unwrapped 179→181 degree transition. These are synthetic adapter
fixtures, not learned gestures or newly admitted reference observations.

The versioned adapter subclasses the existing handflow controller and overrides
only action-state initialization/update. Its planner and positional integrator
are unchanged; there is no second motion simulator. Desired action samples use
gesture-local physical arc progress. Actual angle/edge endpoints approach those
requests at at most 180 degrees/s and 3 edge fractions/s, including during lifts.
Air travel requests the next contact-entry action; it does not teleport state.
Pressure is constant, session effects are disabled, and lifted samples paint no ink.

Strict bundles bind model, tool, code and exact primitive/gesture/action/text
owners. Actual painting consumes realized fields, never substituted desired
tracks. Forcing limits to 1 degree/s and 0.01 fraction/s visibly fails orientation
and edge tracking, proving the adapter is not simply ideal playback.

## Results

- Normal angle/edge tracking and exact contact checks pass on these fixtures.
- Sampling refinement produces a **0.399742 mm** contact-entry shift; timestep
  refinement produces **0.399462 mm**. Both exceed the unchanged **0.01 mm** bound.
- Image changes remain below 0.03, but cannot override endpoint failure. This
  retains the known lift/re-entry positional defect rather than hiding it with
  actuator control or looser thresholds.
- [Metrics and identities](run-002/report.json), [actual/desired traces](run-002/actual-traces.json.gz),
  [frozen inputs](run-002/freeze.json), [criteria](spec-v1.json).
- 51 renders per attempt; two attempts total 102, zero optimization. One bounded
  export/presentation revision adds strict hash envelopes and readable enlargement;
  controller traces and measured outcomes are unchanged. [Run-001](run-001/report.json)
  remains immutable and its diagnostic bundle files intentionally fail strict import.

    .venv/bin/python -m scribesim.handvalidate.action_bridge --revision 1 --output /tmp/td018-action-bridge

Use a new empty directory. Reports, images and gzip traces replay exactly;
wall-time receipts vary. Controller/legacy dataclasses are unchanged, and legacy
pixels still pass. Older whole-file renderer/bridge gates remain stale, not
silently refreshed. Fix and revalidate geometry/gesture coverage and lift/re-entry
before enabling CURRICULUM-009 fitting; no real G0 or owner review is inferred.
