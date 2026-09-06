# Authorized scope — shared acceleration-aware contact timing

**Authorized by the user's corner-aware motion timing request.** One candidate
is frozen in [spec-v4.json](spec-v4.json), with no automatic revision. The prior air-braking
follow-up has executed and its arrival checks pass. Its complete motion gate
fails at sharp continuous-contact corners; no automatic revision is permitted.
HANDFLOW-010 stays in progress until all required fixtures pass, then may merge.

## Executed outcome

[Run-004](run-004/README.md) executes this one candidate. Saved-u contact lag
falls from 0.370963 to 0.007516 mm; corner, arrival, geometry, acceleration,
endpoint/image and old-six baseline checks pass. The complete gate still fails:
arc-refinement event-time drift reaches 0.438 ms against the unchanged 0.1 ms
bound. This is a sampled-chord contact-clock issue, not remaining corner lag.
No automatic revision, completion or merge follows this result. The
[next proposed scope](arc-clock-request.md) needs new authorization.

## Evidence boundary

Run-003 saved u lands essentially at rest with 0.0000603 mm position error, but
later reaches 0.370963 mm lag while changing from stem to exit through a sharp
declared corner. The bound is still 0.25 mm. This is not a remaining air-arrival
problem, a missing-primitive diagnosis, or permission to refit the frozen shape.

## Proposed implementation

Replace constant-speed treatment of sharp contact joins with one shared,
acceleration-aware timing policy in the existing planner. Use explicit primitive
ports and `corner`/`smooth` declarations, not letter IDs or per-example delays.
For an exact tangent discontinuity, investigate a planned zero-speed instant at
the corner with bounded deceleration and reacceleration while contact remains
down. For smooth curves, derive speed bounds from curvature and acceleration.
Preserve accepted air braking, primitive geometry, text/owners, nib angle,
pressure and physical limits. No hidden lift, image correction or pose reset.

Freeze the policy and independent desired-acceleration, time, ownership and ink
checks before evaluating it. Retain the 12 mm/s nominal ceiling and all existing
0.25 mm corridor / 0.01 mm endpoint / 0.03 image-refinement bounds. Account for
planned slowing explicitly rather than relaxing these criteria after results.
This addresses the shared motion plan, not another special-case landing patch.

Proposed separately authorized allowance: one candidate, at most 500 total
diagnostic/presentation/baseline renders or 1800 seconds, zero optimization,
no automatic revision. Reuse the six frozen fixture families, exact subdivision,
arc/timestep refinements, separate physical-edge fixed bridge and old-six baseline.
If passed, complete and merge HANDFLOW-010 before beginning GESTURE-002. If failed,
retain the result without promoting the pipeline. No new learning, pen actions,
letters, context, fatigue or ink-depletion fitting belongs to this work.
