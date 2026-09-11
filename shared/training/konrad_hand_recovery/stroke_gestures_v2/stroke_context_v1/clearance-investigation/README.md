# Finite-nib clearance at the candidate attachment sites

**Read-only geometric audit complete; no construction admitted.** No new
connector, raster sample, fitting or physical run was generated.

[Report](snapshot-001/report.json) SHA-256:
`d7dd39b61b91572d1ee3e241e0583266be9dcd9e4f0f577f74e9964820033943`.
Consumes attachment report
`b555be20ccfc179be57b7ac701ded640741a4a9947a124ccbddef91550fe5a1e`.

## Findings

All 12 positive-height site combinations were examined: four combinations each
for nm, um and mm. These represent 12 distinct endpoint footprints (two heights
per role per pair), reused across the mixed-height combinations. The 15 earlier
baseline-obstructed combinations remain excluded, not rehabilitated by clearance.

| Boundary | Departure footprint versus other canonical occurrences | Receiving footprint versus other canonical occurrences | Conservative open central strip for a moving fixed nib |
|---|---|---|---|
| nm | Clear; nearest lower clearance bound 1.2917–1.3167 mm | Clear; nearest lower bound 1.3095–1.3329 mm | 2.6546–2.6761 mm wide |
| um | Possible contact/overlap with u's retained rising occurrence `0:2` at both departure heights | Clear; same receiving bounds as nm | 2.6664–2.6875 mm wide |
| mm | Clear; nearest lower bound 1.2917–1.3167 mm | Clear; same receiving bounds as nm | 4.4720–4.4935 mm wide |

Own-primitive attachment contact is excluded only from this table's phrase
“other occurrences”; **it remains explicitly measured in every report row**.
We did not discard the entire parent stroke to manufacture clearance.

### n→m is the cleaner initial case

The candidate departure on n's last stem and receiving site on m's first rise
are separated from other existing strokes by positive finite-nib clearance.
The retained portions of their own primitives still meet the site footprint,
as expected for an attachment. That local self-contact is not authorization for
arbitrary new retracing or ink thickening.

This supports narrowing the first proposed construction to **nm**, rather than
handling every pair together. It does not select one of the four height pairs
or prove that a smooth, baseline-preserving turn can connect them.

### u→m has an ownership/overlap complication

At both departure heights (0.434496 and 0.868992 mm), the fixed nib segment has
zero approximate distance to the swept region of u's existing rising stroke
`0:2`, a retained occurrence in the underturn gesture. The distance interval
is [0, approximately0.000010001] mm: **possible contact/overlap**, not a certified
positive overlap area or a physical ink measurement.

The source metadata already declares this gesture as an overlap contributor.
That makes the relationship explainable, not automatically permitted for a new
connector. Rebuilding u's terminal stem must account for the retained rising
stroke beneath/alongside it. Simply deleting the terminal suffix from a collision
test would miss this dependency. The nearby lower return is clear at the sites,
with lower bounds approximately0.1878/0.5164 mm at the lower/higher departure.

**Keep um out of the first construction until its overlap policy is explicit.**
This is not a defect in the accepted u and does not invalidate its original
pen-down return construction.

### m→m has space, but still a long boundary

mm has an even wider open strip and no other-stroke endpoint collision in this
audit. More open space does not make a long connector aesthetically restrained
or physically feasible. Retain mm as a larger-gap control, rather than assuming
one construction should span it.

## What was measured

The model is the frozen **0.45-mm fixed broad edge at physical-y-down40 degrees**.
Analysis is in physical millimeters with y upward, so the edge vector's y sign
is inverted consistently. This is a line-segment nib footprint, not a circular
brush approximation or a centerline-only clearance test.

For each site pair:

1. Partition only the existing canonical cubic domain into retained and proposed
   replacement intervals using de Casteljau. This is measurement of the same
   curve, not a replacement stroke program or newly constructed connector.
2. Flatten those existing intervals with a maximum curve-to-chord displacement
   of0.00001 mm. Sweep the fixed edge along each chord to obtain convex polygons.
   No image or rasterizer is used.
3. Measure the site's nib segment against every swept canonical region, including
   its own retained and proposed-replacement intervals. Record primitive,
   gesture, contact-run ownership and existing contributor relationship.
4. Report distance bounds using the flattening bound plus a1e-9-mm floating-point
   allowance. A positive lower bound is labeled `certified_clear` under this
   nominal approximation model. Zero/near-zero means possible contact/overlap;
   no overlap area or arbitrary collision threshold is invented.

The error interval is geometric approximation accounting with a numerical guard,
not formal interval-arithmetic verification, a new acceptance threshold or a
physical tracking allowance. It does not include pressure/ink spread or motion
deviation. The nib angle, width, targets and previous thresholds stay unchanged.

## Meaning of the open central strip

For retained canonical regions, take conservative control-hull x bounds and
expand them by **both** the existing-ink and moving-nib horizontal half extents.
The strict interior between these expanded bounds is an open vertical strip
for a center carrying this fixed nib. This accounts for finite nib width on
both sides, rather than calling an empty centerline gap a clear ink corridor.

This strip excludes proposed replacement ink, because that geometry does not
exist. It proves neither access from the departure site into the strip nor exit
from it into the receiving site. It also says nothing about baseline extrema,
tangent matching, curvature, speed or self-overlap of a future connecting path.
**Open middle space is not a connector-feasibility result.**

## Next decision

The requested proposal is now documented in
`docs/tech-direction/TD-018-nm-construction-proposal.md`. It proposes a single
higher-site nm construction with explicit stem-foot/receiving-entry exceptions
and conditional10-image review, while deferring um. This remains a proposal,
not an approved geometry, completed feasibility check or new rendering allowance.

Recommend a bounded **nm-only construction proposal**, retaining nn as the
incompatible-receiver control and mm as the larger-gap control. Keep the four
positive-height nm site combinations unselected until a construction requirement
justifies a choice; do not choose the one with the largest clearance by default.

Before any new geometry, freeze the stem-foot and rise-prefix replacements,
protected body/anchor requirements, permitted turn extent/length/curvature,
finite-nib overlap ownership at the splices and baseline policy. Then obtain
owner approval for that construction scope and a separate nominal-preview
protocol. um needs additional retained-rise overlap handling before inclusion.

No new body exception, overlap allowance, contact transition, spacing change,
geometry bounds, physical budget or execution is granted by this audit.

## Reproduction

Subsequent approved nm-only construction stopped before rendering; see
[saved outcome](../../nm-construction-v1/README.md). The original clearance
snapshot below remains unchanged and does not admit that construction.

```sh
.venv/bin/python -m pytest -q tests/test_stroke_clearance_audit.py
.venv/bin/python -m scripts.stroke_clearance_audit inspect --report-sha256 d7dd39b61b91572d1ee3e241e0583266be9dcd9e4f0f577f74e9964820033943
```

Snapshots refuse overwrite. Pinned reinspection re-derives the report from the
same algorithm; this is reproducibility evidence, not an independent physical
reader. Frozen attachment/design/source and original/recovery artifact checks
remain in force. Changes are uncommitted; no merge or acceptance is claimed.

Local checks:105 tests pass,48 unchanged exact-null tests deselected; exact pinned
reinspection passes. All12 cases retain explicit own-primitive attachment
contacts and false admission flags. Report/code/test pins, ARRIVE plan,
generated-rule, local-link and whitespace checks pass.
