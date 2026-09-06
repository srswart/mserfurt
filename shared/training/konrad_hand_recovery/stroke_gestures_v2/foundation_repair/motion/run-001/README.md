# Motion attempt 0 — timing repair exposes a failed physical baseline

This is a failed, immutable diagnostic attempt, not an accepted repair or training.
The experiment used 266 renders in 17.10 seconds, zero optimization, six fixture
families, and the original frozen gesture candidate. `report.json` records all
checks; `baseline.json` separates historical provenance from current acceptance.

## Findings

- Saved `u` reproduces the old 0.399871 mm arc-refinement endpoint shift.
- In saved `i u`, the legacy 0.141244 s excess execution time exactly equals the
  sum of per-segment duration floors. Refinement changes that unintended time.
- Legacy rounding can exceed the requested 0.002 s integration step. Next-sample
  holding advances contact events early; zero-length lift/re-entry adds time.
- Event-time-v1 uses a global time grid, exact contact-event instants, interpolated
  desired states and the existing acceleration-limited integrator. It performs no
  corridor projection, pose reset, image correction or change to legacy mode.
- Planned/executed time now agrees and every contact owner is retained. However,
  the original low-bandwidth position/velocity controller has 1.29–1.95 mm maximum
  contact lag on these gestures, not the required <=0.25 mm. Old positional
  projection concealed that failure. All six frozen primitive actual checks fail.
- V1 timestep refinement still moves endpoints by up to 0.025516 mm. The inherited
  first-order integration error is measurable rather than averaged away.
- Saved candidate arc refinement still changes planned contact duration by
  0.592049 ms per gesture. The sampler chords across the stem/terminal corner;
  exact corner vertices are absent from the uniform arc grid. That is separate
  from the now-fixed execution-time flooring.

## Bounded diagnosed revision

Use the single permitted revision, with unchanged acceptance limits and no search:
an explicit event-time-v2 bounded velocity servo in the same integrator, with
trapezoidal position integration; explicit gesture-arc-v3 sampling retaining
primitive/cubic boundaries. The target velocity is desired velocity plus the
existing position-gain correction; actual velocity change remains acceleration
limited and speed capped. No contact entry reset or unconstrained acceleration.
Keep V1 and legacy replay. Freeze this revision before measuring it. If the
current baseline still fails, stop and scope further motion work; do not fit
return primitives or mark HANDFLOW-010 complete.

## Samples

- [Equal-frame before/after and timestep comparison](comparison.png)
- [Frozen nominal primitives versus unprojected actual motion](baseline.png)
- `traces.json.gz`: desired plans, event times, positions, velocities, owners and
  independently observed pre-projection states. Observation delegates to the
  existing controller step and supplies no forces.

Replay this exact attempt from its implementation commit. Later revisions have
different explicit execution/sampling versions and code identities.
