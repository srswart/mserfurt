# Contextual nu entry — bounded port audit

**Outcome: exact full-primitive reuse is incompatible with the fixed anchors
within the investigated similarity family. This does not reject derived gestures.**

[Report](report.json) SHA-256:
`8bf7cf5810a7e215a70086d2af1f5de1ad366af155ed6c09a37d3a3ac46fda99`.
[Approval](../approval.json) binds one read-only audit to the
[proposal](../../../../../../docs/tech-direction/TD-018-contextual-entry-feasibility-proposal.md).

## Results

| Necessary condition | Finding |
|---|---|
| Shared primitive ports | Lower-return→rise→upper-return ports match; smooth full-primitive reuse forces a common rotation |
| Rotation imposed by n's outgoing tangent | −2.353981470°; inside the allowed±20° range |
| Upward/right rise endpoints at that rotation | P angle89.767115°, Q angle41.452529°; endpoint-direction condition passes, not whole-curve feasibility |
| Baseline height imposed on full lower-return | Requires uniform scale0.953768823, inside[0.5,1.5] |
| Baseline horizontal position | Requires0.240296644mm travel; rotated/scaled primitive gives0.970504926mm: mismatch0.730208283mm |
| Upper-return directly to C | Directed tangent mismatch2.005750957° |
| Upper-return to unchanged canonical u prefix | Directed tangent mismatch−2.353981470° |

The baseline contradiction alone stops the exact full-primitive construction.
The receiving checks are independent necessary-condition diagnostics, not a
fallback candidate. No endpoint positions or handles for a new shape were selected.

The full lower-return's y-minimum parameter after the forced rotation is enclosed
by[0.6739452647989841,0.6739452648009840]. Fixing A determines translation and
rotation; reaching baseline determines scale, leaving a horizontal mismatch far
larger than the audit's1e-7mm accounting guard. Source extrema and input hashes
are recorded in the report. These are guarded analytic diagnostics, not a new
physical or whole-curve contact certificate.

For the rise, positive-x/positive-y endpoint angles require rotation greater
than−20° within the tested interior and below−2.121096397°. The allowed family
also includes−20°; the report's conservative open interval does not test that
endpoint and is not an exhaustive placement certificate. No choice of P/Q
positions is made from these angle conditions.

## What needs adaptation

- Preserve A and B, but derive a departure-turn shape from the lower-return
  pattern. Rotation/scale alone cannot fit it. A new primitive cut would require
  explicit review; this run did not search cuts or alter any handles.
- Retain rise/upper-return as the entry grammar. Their endpoint-direction
  compatibility does not yet establish displacement, thin-core envelope or
  curvature compatibility for an adapted entry.
- Define a crown/descent adaptation into fixed C. Neither the direct crown
  nor the unchanged canonical prefix matches under the forced reuse rotation.

Next prepare one deterministic derivation proposal with explicit adaptation
formulas, semantic P/Q ports and their mapping across fixed contact anchors.
Keep thinness, radius, A/B/D/C, source coverage and contact/length regions
unchanged. If those requirements cannot coexist, report the conflict instead
of tuning or granting a new envelope automatically.

## Execution and validation

One5.674518s invocation, under300s and10MiB; the5GiB free-space guard passed.
No retries, new geometry, images, fitting, providers/GPUs or physical runs.
Input pins verified before/after. Mu remains unstarted.

219 selected tests pass,48 exact-null cases deselected. Includes19 new audit
tests for placement exclusions, port direction, repeated roots, source identity,
contact/length partition mutation and no-retry/no-constructor behavior.
Documentation checks pass. No new geometry/contact acceptance is claimed.
CURRICULUM-016 remains in progress, not completed; changes are uncommitted.
