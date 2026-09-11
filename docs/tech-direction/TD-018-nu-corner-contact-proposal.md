# TD-018 — Corner-contact capability and coupled nu construction proposal

Status: **proposal prepared; capability work, geometry and rendering await approval**.
The owner's “okay let's do the recommended next” authorizes preparing this
proposal. It does not activate new pen actions, body changes or experiments.

## 1. What should change, and why

For a following u, propose three owned, continuous pen-down motions:

1. Finish the preceding n's final stem with a small departure turn, narrowing
   from full-edge to corner contact while still reaching the baseline.
2. Carry a thin rising connection toward the following u—not a broad horizontal
   band across the gap.
3. Turn into u's descending first stem, restoring its full contact before the
   retained stem continues into the unchanged underturn and remaining body.

**mu is the larger-gap comparator**, using the same port-level construction and
action profile, not independently tuned geometry. Separation is always an
explicit alternative. Neither a geometrically possible join nor a thin one
automatically counts as a good writing construction.

Partial corner contact is a hypothesis about how to represent the desired thin
stroke in this model, not a claim that it is the owner's intended historical
pen technique. Choosing this route must be reviewed explicitly. No global nib
rotation, pressure reduction, narrower raster brush or pen lift substitutes for it.

## 2. Frozen inputs and scope

| Input | SHA-256 |
|---|---|
| Canonical candidate object | `96aced30b45e5ef09eb219643c4eb068a332fcdab3a3ae466ee5fe5aa7993ca3` |
| Thin-connection investigation | `0b8b2f84474ef80cd37e94085483e5e312f52d348f46a32a07d972e83bd28aa3` |
| Investigation design | `84ac53d4d97b78f60905fe6cff8617d1724955308176e4e8b313c5ae4fb339c1` |
| Existing tool contract | `f267680ed6313862ab4bd8771fb52c4937a7f20c3b711988b5d746cc6ca924b7` |

Keep all prior candidates, reports, approvals, targets, code identities and
budgets unchanged. The rejected nm packet remains negative style evidence.
um and num are not admitted here; their retained-stroke/composition issue is
still unresolved. No new claim of unseen holdout evidence.

Planned isolated paths: `scripts/nu_corner_contact.py`,
`tests/test_nu_corner_contact.py`, `scripts/templates/nu_corner_review.html`, and
`shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/`.
Do not modify identity-scanned core files or add training spec files. Existing
gesture/curriculum components suffice; no new advance or component is needed.

## 3. Capability package comes first

Proposed identity: `nu-corner-capability-v1`. This package performs read-only
contact geometry and contract tests, **not a controller run or connector build**.

- Use the existing physical contact rectangle: full edge W=0.45mm, thickness
  0.02mm, physical-y-down40 degrees, pressure0.5 and speed cap12mm/s.
- Compare the two actual corner intervals [0,0.1] and [0.9,1], plus full-edge
  [0,1] as a control. A centered [0.45,0.55] interval is not a corner substitute.
- Preserve directed edge labels under y/angle reflection. Confirm that interval
  endpoints, rectangle corners and the0.2025mm corner-center displacement are
  represented consistently by contact geometry and the action bridge.
- Check complete full-to-corner/corner-to-full interval ramps at fixed canonical
  sites analytically or with conservative interval bounds. No sparse sampled
  contact proof. Report penetration possibilities and uncertainty rather than
  converting existing overlap declarations into permission.
- Audit schema/ownership mapping for an independent boundary action while
  retaining canonical letter and action identities. A shared contact run must
  not silently replace the body action for every occurrence of its gesture.
- Retain the existing endpoint-rate limit3/s and angular-rate limit180°/s.
  Each full-to10% corner transition requires at least0.3s; restoration requires
  another0.3s. These are necessary rate bounds, not a ready motion schedule.

**Proposed first corner is [0,0.1]**, the negative directed endpoint. This is an
explicit deterministic design choice for the first prototype, not a discovered
optimum. The opposite corner is capability evidence only, not an automatic
fallback. If the proposed corner fails or remains unresolved, stop and review.

Capability completion establishes representability and local contact evidence
only. The existing action bridge is not itself admission for these new boundaries.
Actual realization, transition rates, tracking and ink accumulation remain a
separate physical-validation work package and budget.

## 4. Coupled geometry: one fixed construction family

Proposed identity: `nu-coupled-corner-geometry-v1`. Prepare it only after a
capability report and explicit geometry approval. Coordinates below are mm,
x right/y up, baseline0, x-height H=3.5. No control points are evaluated by
writing this proposal, and no pass or pleasant appearance is predicted.

Select the outgoing final descending stem and incoming u's first descending
stem by their canonical port/recipe roles and relative geometry. Active exposed
inventory is nu/mu only; not full-word rules, seed keys or per-case residuals.

### Proposed source intervals and body exceptions

- Departure A: existing higher site at h=0.86899162238258mm, read from the pinned
  report at its exact canonical parameter. Retain the preceding final stem's
  [0,tA] subcurve; replace only its suffix. This applies to n or m's final stem.
- Receiver C: canonical parameter tC=0.25 on u's first stem. Retain [tC,1]
  exactly; replace [0,tC]. This removes about0.544mm of vertical prefix, rather
  than skipping the entire stem or jumping to u's later rise.
- Let F be the original outgoing stem endpoint. Baseline turn B=(F.x+W/2,0):
  proposed outgoing foot shift0.225mm right, as an explicit new body exception.
- Let D=(C.x−W/2,H) be the proposed receiving apex. This replaces u's original
  initial top anchor, preserving its height but moving it horizontally. Require
  its displacement from the original top anchor <=W; otherwise reject. Do not
  hide this as exact body preservation. The owner's original upright letter
  acceptance does not automatically approve this connected-prefix change.
- Retain every other cubic, anchor, letter advance, internal join, underturn
  and canonical action definition exactly. Isolated n/m/u and separated pairs
  are unchanged inputs. No spacing change or baseline/x-height overshoot.

Let dA and dC be the exact canonical directed unit tangents at A and C. Reject
unless both point downward, A.x<B.x<D.x<C.x and0<C.y<H. Proposed control points:

| Piece | Four Bezier control points |
|---|---|
| T, departure turn | A; A+a·dA; B−(b,0); B |
| R, thin rising connection | B; B+(r,0); D−(r,0); D |
| S, receiving turn | D; D+(s,0); C−c·dC; C |

Fixed constants: a=0.9h/|dA.y|; b=2(B.x−A.x)/3; r=(D.x−B.x)/3;
s=2(C.x−D.x)/3; c=0.75(H−C.y)/|dC.y|. These define at most two exposed
instances of one family, not a search. Do not tune them, change corner, move a
site or retry automatically if either instance fails.

T descends to B, R rises to D, S descends to C. At B/D the directed tangent is
rightward; A/C match retained canonical tangent directions. The construction
therefore explicitly turns into u's descending stem rather than attaching an
upstroke to the top with incompatible direction. Direction continuity does not
prove physical timing or equal parameter speeds.

Representation permits at most13 geometry pieces: nu has eight retained
occurrences plus T/R/S; mu has ten plus T/R/S. This is a new isolated document,
not a bypass of connected-v1's six-occurrence cap and not a physical consumer.

## 5. Thin core, transitions and hard gates

Contact state is explicit: T ramps linearly in its own arc progress from [0,1]
to [0,0.1]; R holds [0,0.1]; S ramps back to [0,1]. Orientation stays fixed.
Full contact must be restored exactly at C; retained bodies use their unchanged
full-edge state. No paint is duplicated over replaced source intervals.

- **Thin core:** all of R, not a selected crop or average. Proposed maximum
  transverse rectangular width is25% of the fixed vertical full-contact reference,
  exactly0.25×(0.45cos40°+0.02sin40°), approximately0.089394mm. At10% contact,
  the direction-independent geometric upper bound is sqrt(0.045²+0.02²), below
  0.05mm. This is a contact-model bound, not actual ink or motion acceptance.
- **Broader transitions:** only T and S may exceed that thin-core limit, never
  more than the full rectangle's directional support. Each piece must have
  certified arc length <=1.25 times its endpoint distance. This includes R,
  so broad transition spans cannot be stretched across the gap. Do not use
  an average thinness score to conceal a thick central segment.
- **Geometry:** nonzero derivatives, directed tangent error<=1e-8 and attachment
  position error<=1e-9mm. Radius>=W/4=0.1125mm on all three pieces. T reaches
  baseline only at B, R reaches x-height only at D, and S stays inside the band.
  Require monotone y on each open piece and no loop, retrace or nonlocal crossing.
- **Horizontal bounds:** T may use the same *explicitly reproposed* tangent-derived
  departure allowance delta=max(0,−a·dA.x), capped atW/100=0.0045mm, with one
  initial minimum/recovery and the left-of-A part confined to radiusW/4 about A.
  R must be strictly rightward inside [B.x,D.x]. S stays in [D.x,C.x] and must
  be strictly rightward; an incompatible canonical dC is a rejection, not a
  license to flip its tangent or add an undeclared receiving allowance.
- **Contact/clearance:** measure full finite-thickness rectangles, corner offsets
  and every ramp phase. Proposed attachment permissions apply only to retained
  departure/T at A, T/R at B, R/S at D, S/retained receiver at C. For each pair,
  the full intersection must be confined to a radiusW disk at that join. All
  other new-to-retained/nonlocal intersections require certified separation.
  No full-primitive waiver, old um overlap exception or zero-thickness proof.
- **Ownership:** T belongs to the derived departure with removed-suffix lineage;
  R is boundary-owned with both contributors; S belongs to the receiving prefix
  with incoming-boundary provenance. Preserve source identities and action/contact
  lineage separately. Own-stroke contact and nonlocal self-overlap must be reported.
- **Measurement:** analytic extrema or conservative whole-curve/contact bounds,
  explicit margins, no sparse-grid admission. Unresolved means stop. Two corner
  sweeps and continuous action ramps must not be replaced with a static-width
  approximation. Source/null checks and adverse mutation tests precede rendering.

The position, shape and rate constraints may conflict; that is precisely what
the staged checks must expose. No threshold is automatically relaxed. Geometry
admission is not physical readiness: each T/S needs at least0.3s for its ramp,
and local time allocation must respect the instantaneous endpoint rate, not just
the total duration. Slowing is possible under the cap but not implemented here.

## 6. Comparison and resource gates

1. **Next requested approval:** capability implementation and read-only inspection
   only. Proposed local ceiling300s, output<=10MiB, minimum free5GiB; no images,
   connector construction, controller, fitting or automatic retry. Preserve the
   capability report and review its implications before geometry activation.
2. **Later geometry approval:** bind this proposal, capability output, canonical
   inputs, global corner choice and source/test identities to a fresh record.
   At most one nu and one mu instance;300s total verification, no fitting/retry.
   If either fails or is unresolved, stop before the comparison packet.
3. **Later conditional nominal approval:** at most ten PNGs plus one page,
   n/m/u/nu/mu × separated/connected-mode,300s and100MiB combined new artifacts,
   minimum free5GiB. n/m/u are pixel-identical controls. Use the SAME finite
   rectangle renderer for both modes; do not compare old line-edge B0 with a
   finite-thickness B3 or claim old nominal pixel identity. Frame remains
   [-3,30,2,13]mm,900dpi,1169×390. Every contact state and width is inspectable.
4. **Owner review:** are nu/mu recognizable, is the connector genuinely thin and
   purposeful, are the departure foot and u's changed top acceptable, and is mu
   too long? Agent appraisal does not fill in owner preferences. Rejection and
   preference for separation are valid. Physical validation remains separate.

The current turn prepares this proposal only. None of these prospective resource
allowances is consumed or enabled by documentation. Old attempts/budgets remain
consumed and preserved. CURRICULUM-016 stays in progress; HANDVALIDATE-025/026
remain gated. No commits, merges, new components or advances are requested.
