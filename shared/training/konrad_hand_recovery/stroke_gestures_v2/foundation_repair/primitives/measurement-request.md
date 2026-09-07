# Measurement-only follow-up — approved 2026-09-07

User authorization: “Yes please widen the measurement frame. You have approval.”
Execution is bounded by [measurement-spec-v1](measurement-spec-v1.json). Approval
does not alter any historical result or grant independent primitive acceptance.

The frozen comparison frame in spec-v1/v2 is `[-2, 9, 3, 13]` mm. Static
compilation of the unchanged compound scaffold at scale 0.9 exposes a framing
error, independently of target scores or selected handles:

- Upper return spans its fixed endpoint level y=10 mm.
- The attached stem descends from y=10 to y=13.15 mm.
- The lower return starts and ends at y=13.15 mm; initial control points extend
  to y=14.031396 mm. It is therefore outside the frame's y=13 mm lower edge.
- The final rise returns upward from y=13.15 mm.

This is a measurement/presentation defect, not evidence that this missing ink
is absent from the model or actual trajectory. The current run must retain its
frozen frame and report failures honestly; no old target, loss or artifact is edited.

The one automatic diagnosed revision already fixes numeric handle representation.
An additional follow-up therefore requires explicit user authorization.

## Bounded proposal

After all three seeds freeze their candidates, reuse those exact candidates and
saved actual/refinement trajectories. Widen only the common physical frame to
`[-2, 9, 3, 16]` mm and recompute initial/independent-target/nominal/sampled/actual,
per-family regions and convergence images at the unchanged 180 DPI. Regenerate
900-DPI sheets at that same full frame. No optimizer, candidate fallback, new seed,
new geometry or relaxed criterion is allowed. Preserve the old results alongside
the new frame-qualified result. Verify complete footprint containment explicitly.

Allow at most 500 measurement/presentation renders and 900 seconds across all
three seeds, zero optimization and no further automatic revision. Report every
failure. Reusing a frozen candidate for this measurement repair is not permission
to self-certify S1 or begin gesture fitting; HANDVALIDATE-015 remains independent.
