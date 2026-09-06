# Required additional scope — feasible air braking and contact re-entry

**Proposal only; not authorized as an extra experiment, not implemented, and not
a third permitted attempt under HANDFLOW-010.** The two allowed attempts are
retained. HANDFLOW-010 remains in progress; GESTURE-002 and all later foundation
Advances remain planned. No merge should represent this as a completed repair.

## Established result

The second attempt fixes time/endpoint convergence and revalidates the old six
primitive families. It fails the repeated-contact corridor gate: actual velocity
is still about 16.6 mm/s upward when the plan requests a 12 mm/s downward stroke.
At the frozen 500 mm/s² bound, reversal takes at least about 57 ms before any
position correction. Actual lag reaches 0.795909 mm against the 0.25 mm limit.
This is a plan-feasibility issue, not evidence that the primitives need refitting.

## Proposed bounded work

1. Freeze the saved air/contact boundary states and failing traces from run-002.
   Add tests that reject a planned instantaneous velocity reversal at contact.
2. Investigate one explicit acceleration-feasible air-retiming rule in the existing
   planner. Prefer braking to a prescribed near-rest arrival before contact, or a
   geometrically justified tangent-compatible approach when necessary. Select the
   rule by physical constraints before image experiments, not by image scores.
3. Account for all added pen-up time in the plan. Preserve contact order, text,
   geometry and owners, actual velocity continuity, tool speed/pressure/angle,
   maximum acceleration and maximum speed. Do not reset state at entry, snap
   position, paint an air connector, raise limits or wait adaptively until a
   scored image happens to pass.
4. Verify planned and realized boundary positions/velocities, stopping distance,
   acceleration envelope, elapsed time and no air ink; then rerun the six frozen
   fixture families, refinements, physical-edge fixed bridge and read-only old-six
   baseline. Preserve the exact existing endpoint/image/corridor criteria.
5. If accepted, finish HANDFLOW-010 and merge it before starting GESTURE-002.
   Only then proceed through the remaining five registered foundation Advances.
   If still failing, preserve the finding without completing this Advance.

Proposed new allowance (requires explicit approval/registration): at most 500
total diagnostic/presentation/revalidation renders or 1800 seconds, zero fitting,
one predeclared motion candidate and no automatic revision. Any incompatible
contact timing contract must be revised explicitly before running. This is not
permission to widen the current experiment budget silently.

Fatigue, ink depletion, pen actions, letters, words and real-reference fitting
remain outside this additional motion work. No new component or second simulator
is needed. Existing `handflow`, `pathguide` and `handvalidate` own it.
