# HANDVALIDATE-022 — why approved letters fail the analytic yardstick

**The approved shapes do not need an automatic repair.** Saved evidence supports
a mismatch between two style constructions, not a large physical tracking error.
This investigation changes no shape, target, threshold or historical decision.

## Measured comparison

All values below use the same saved 180-DPI full-frame image metric. Small loss
means closer ink agreement; the new nominal-to-actual diagnostic is not an added
acceptance gate. This metric is normalized/nonlinear: do not subtract its values
to claim a percentage of error caused by the controller or by width.

| Fixture | Analytic vs approved nominal | Analytic vs actual | Approved nominal vs actual | Desired-plan ink vs actual |
| --- | ---: | ---: | ---: | ---: |
| n | 0.382013 | 0.382013 | 0.000000 | 0.002051 |
| u | 0.232303 | 0.232051 | 0.000302 | 0.003137 |
| m | 0.590033 | 0.589663 | 0.000957 | 0.005898 |
| placed mu | 0.444511 | 0.444487 | 0.000674 | 0.003867 |

The large mismatch already exists in the approved nominal design, before physical
execution. Actual output stays close to that nominal design; its maximum
nominal-to-actual difference over all ten fixtures/four refinements is 0.00665819.
The corresponding desired-to-actual maximum is 0.00796460. Zero loss at this pixel
resolution does not mean continuous geometry is identical.

### What differs geometrically?

| Letter | Approved entry/exit horizontal span | Analytic span | Difference |
| --- | ---: | ---: | ---: |
| n | 1.682557 mm | 1.400000 mm | +20.18% |
| u | 1.654180 mm | 1.400000 mm | +18.16% |
| m | 3.365113 mm | 2.800000 mm | +20.18% |

These spans describe centerline ports, not ink bounding boxes, spacing or new
design requirements. The approved rise has 0.28 mm lateral travel and a higher
return attachment than the ideal vertical rise. Approved upper/lower returns have
asymmetric entry/exit heights; the ideal semicircles do not. n/m include the shared
rise's lateral travel, which the analytic recipes omit. Stem ports match, but its
small curvature is not the perfect analytic line. Existing baseline/x-height,
motion, overlap and convergence gates remain satisfied in the frozen evaluation.

**Inference:** the large residual is predominantly a style/construction mismatch.
No controlled width-only intervention or new render was performed, so this does
not quantify the contribution of each geometric difference.

## Reconciliation decision

- Keep actual n/u/m and placed-mu owner KEEP. No automatic narrowing or semicircle replacement.
- Preserve HANDVALIDATE-021's numeric FAIL and its unchanged 0.05/0.75 gates.
- Treat its analytic target as evidence about that declared style, not an owner verdict.
- Approved specimens can anchor regression tests, but must be labeled candidate-derived, not independent targets.
- Document a prospective reference contract before new scoring; do not unlock context, S2 or real-hand admission by changing a label.

The proposal is in [TD-018 Addendum B section 14](../../../../../../../../docs/tech-direction/TD-018-addendum-b-foundation-repair.md#14-reconcile-approved-appearance-and-independent-target-provenance).
Its preferred direction is approved-style regression plus separate mechanical
checks and explicit style diagnostics. It is **not activated**: target roles,
required gates and any new independent exemplar/style specification still need
review and a fresh protocol freeze. Appearance itself is already approved.

## Evidence and reproduction

- [Read-only report](report.json), [pre-measurement protocol](protocol.json).
- [Original approved comparison gallery](../index.html).
- [Bound actual-ink approval](../continuation-002/actual-review.json).
- [Original independent verification receipt](../continuation-002/inspection.json).
- Report SHA256: `f56d560e345b686e8dc06d2a5cef55ea4a8956d7b3f608e0069c330462ce3eae`.

From the repository root, recompute the diagnostic JSON to stdout:

```sh
.venv/bin/python -m scripts.handvalidate_upright_targets
```

The script verifies all 1,256 original artifact hashes, frozen code/source pins,
approval and existing reader receipt; then recomputes saved target/global/local
losses and new diagnostic comparisons. Motion/replay findings come from the
previous pinned independent verification, not a new controller run. Seed 7 first
is the diagnostic representative; the original deterministic seeds/replays are
not claimed as new models or new statistical evidence.

Zero controller executions, zero raster renders, zero optimization. Files in old
archives are never written. `--output` refuses to overwrite an existing report.
