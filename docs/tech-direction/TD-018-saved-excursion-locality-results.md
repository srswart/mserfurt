# TD-018 — Saved excursion locality: three proven violations

Status: **measurement complete; J1/J2 not admitted**. No reconstruction, refit,
new samples, changed limits or physical execution.

The owner authorized measuring the saved excursion spans more precisely without
refitting or changing limits. The [approval](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/locality-approval.json)
pins the prior continuation and readiness reports. The independent diagnostic
`scripts/nu_excursion_locality.py` reads the saved controls directly; it imports
no constructor, renderer or training code. Previously recorded dependency bytes
remain checked, without pretending the old readiness receipt certifies a new
execution inventory. All old evidence and checkers remain unchanged.

## Result

All three formerly unresolved spans contain actual outside-disk points.
The fixed disk radius is **0.1125mm**.

| Candidate / span | Proven interior-point distance, at least | Excess over radius, at least | Whole-span supremum, approximately |
|---|---:|---:|---:|
| J1 receiving K→C | 0.146453mm | 0.033953mm | 0.191386mm |
| J2 departure A→F | 0.279206mm | 0.166706mm | 0.362183mm |
| J2 receiving K→C | 0.258969mm | 0.146469mm | 0.336362mm |

The table rounds distances for readability; exact rational inequalities in the
report establish the violations. Each witness lies strictly on the excursion
side of the anchor, not merely at a crossing boundary or outside the measured
span. Horizontal excursions at these witnesses are only 0.001063mm, 0.001629mm
and 0.002409mm respectively. The problem is distance from the attachment in
two dimensions, not exceeding the separate 0.0045mm horizontal cap.

The earlier hull bounds were already close to the true suprema. Tightening the
measurement does not turn any of these cases into a pass. Thinness and curvature
were not changed or reevaluated; their earlier results remain intact. External
finite-nib/ramp-contact gates are still not executed and no visual acceptance
is inferred.

## Proof and evidence boundary

The diagnostic interprets saved floating-point controls as exact rational
numbers. Exact de Casteljau restriction/subdivision measures the same curves;
it does not create or fit replacement geometry. Sign-changing rational root
brackets and the factored crossing polynomial verify the full excursion domains,
including exclusion of additional interior crossings.

On each complete covering interval, convex-hull radius upper bounds are refined
against lower bounds from actual points strictly inside the excursion. Final
radius intervals are narrower than 2e-10mm. Independently recorded, well-inside
points prove the violations using exact squared-distance comparisons, not sampled
acceptance or rounded decimal displays. No interval is cropped to fit its disk.

The [measurement report](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/locality-001/report.json)
contains candidate hashes, full covering intervals, root brackets, rational
distance bounds, witness parameters/positions and preserved prior measurements.
It completes in 0.428065 seconds. Eight focused diagnostic tests cover exact
restriction, conservative-bound refinement, actual witnesses, outward rounding,
ambiguous roots, nonfinite input, exhausted refinement and pin/limit guards.

There are zero new study candidates, images, fitting evaluations or physical
runs. The diagnostic has a 300-second/1MiB ceiling and no automatic retries.
The saved report and candidate hashes are checked before and after measurement.
The original unresolved report is preserved; this new report supplies the
stronger, proven-failure classification rather than overwriting history.

## Next proposal, not execution

Prepare a bounded **local terminal/receiving construction revision**, beginning
with J1's receiving span because J1 has only that demonstrated locality failure.
This is prioritization by repair scope, not a visual preference or guarantee.
The small canonical-tangent accommodation must stay close to its attachment;
do not enlarge the disk, change the horizontal cap or truncate its domain.

Preserve the rest of J1 wherever feasible, and retain all thinness, curvature,
source identity and contact gates. If the local revision cannot satisfy those
constraints together, report the incompatibility before broadening the design.
J2 additionally needs departure repair and is not an automatic next trial.
Any new geometry requires a separately specified and authorized construction;
this measurement does not authorize additional candidates or refitting.
