# Saved derived nu — stronger self-contact measurement

**Measurement bound certified; overall admission remains unresolved.**

[Report](report.json) · [Approval](../self-contact-approval.json) ·
[Unchanged candidate](../derived-entry-001/candidate.json)

Report SHA-256 `6bd3453b1ff86f7e6461ff77cecc4026f23a6cd0097a3284271b12e39dc20278`.
Candidate SHA-256 `16872e32eb44d15c2b226a4327a75851bf6a286ba08568930f856c554e97c433`.

## What the stronger measurement proves

Across the whole three-cubic thin entry, including P/Q joins, any overlapping
finite footprints must belong to path positions separated by at most
**0.031114480mm of arc length**. Overlap between more widely separated positions
is excluded. This is a bound for all parameter pairs, not sampled pixels.

The path has dx>0 and dy>=0. Along its unit tangent, progress in the nib-normal
direction n=(sin40°,cos40°) is therefore at least sin40°≈0.642787610 per unit
arc length. Identical fixed-orientation rectangles can overlap only when their
n-coordinate separation is at most their0.02mm thickness. Integration gives
arc separation≤0.020000002/0.6427876096855393, with conservative numeric guards.
The constant negative-corner offset cancels in the difference; it is not omitted
from the contact model. No replacement with a zero-thickness line is used.

Under the unchanged curvature ceiling, this arc interval has total turning
bounded by0.276573153 radians. This too is a measurement, not an acceptance rule.

## What remains unresolved

The previous checker required both nib-axis projections to be monotone. The
new bound works even when the along-edge projection turns, so it supplies
stronger spatial evidence without changing the curve.

However, the existing contract does not quantify how to distinguish allowable
neighboring-path footprint overlap from prohibited nonlocal overlap inside this
short interval. Neither the bound nor the absence of a monotonicity certificate
proves that every residual overlap is permissible or that a collision occurred.
We have not silently introduced a0.031115mm locality threshold or any P/Q disk.

Next: make the local-versus-nonlocal contact definition explicit, distinguishing
continuous neighboring-path coverage from leave-and-reenter contact. Any proposed
permission change requires review. Alternatively, prove the residual contact
classification directly under the existing rule. Preserve this candidate and
both unresolved reports; do not refit or retry automatically.

## Scope and checks

One10.255061s no-refit reinspection under300s. Existing structural measurements
recomputed and exactly equal to the prior report; external contacts rechecked.
Thinness, curvature, length, geometry, source/action identity and overlap
permissions unchanged. Candidate constructor never called; formula checks
recompute expected controls only to verify provenance, not to replace a candidate.
All frozen pins verified before/after. No images, physical runs, fitting or mu.

107 focused tests pass, including seven new measurement tests for the all-pairs
bound, projection reversal, disconnected/reversing paths and no reconstruction
or retry. Documentation checks pass. Evidence below10MiB;5GiB free-space guard
passed. CURRICULUM-016 remains in progress; changes uncommitted.
