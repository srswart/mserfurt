# Proposed next scope — geometry-derived contact arc clock

**Authorized by the user's request to incorporate the fix and rerun.**
[Spec-v5](spec-v5.json) freezes one additional candidate, without an automatic
revision. Run-004 remains immutable. HANDFLOW-010 stays in progress until the
full new evaluation and verification pass; only then may it complete and merge.

## Evidence and diagnosis

Corner tracking succeeds: saved-u contact lag falls from 0.370963 to 0.007516 mm.
Every corner, arrival, desired/actual acceleration, ownership, image and endpoint
check passes, as does the read-only original six-primitive baseline.

Six arc-refinement convergence checks fail only their event-time component.
The worst saved-i-u shift is 0.000437749916 s versus 0.0001 s allowed. Its coarse
contact chord total is 16.53007698569722 mm; the refined total is
16.530786621897473 mm. The current planner feeds these sampled chord lengths
into its analytic clock. Conservative curvature slowing magnifies their small
length difference into a cumulative time shift. Exact cubic subdivision and
time-step refinement pass. This diagnosis follows the code and saved traces;
no alternate clock candidate has been tried.

## Bounded implementation proposal

Compute each smooth section's arc length and corner/event clock from the frozen
source cubics, with a deterministic bounded integration/inversion tolerance,
not from the guide's resampled chord sum. Map source samples monotonically into
that geometric clock while retaining every sample, exact corner, owner and
air-contact event. Integrate the existing planner/compiler metadata rather than
adding a second simulator or silently replacing the evaluated path.

Keep corner-time-v1's shared curvature policy, fixed tool/geometry, 12 mm/s speed
ceiling, 250 mm/s² desired and 500 mm/s² actual acceleration limits. Preserve
accepted air braking. Freeze numerical tolerances, convergence and negative
controls before results: repeated joins must not accumulate more than 0.1 ms
event-time drift under arc refinement or exact subdivision. Retain every other
existing corridor, endpoint, image, ink, ownership and corner requirement.

Proposed new allowance: one candidate, at most 500 total fixture/baseline/
presentation renders or 1800 s, zero optimization and no automatic revision.
Recheck the same six fixtures, separate fixed physical-edge bridge and original
six-primitives baseline. Clean-checkout regression is separately accounted for,
not permission for another candidate. Complete and merge HANDFLOW-010 only on
full acceptance; otherwise preserve the failure. No new primitive/letter/action
fitting, fatigue or ink-depletion work belongs to this proposal.
