# TD-018 — Thin-connection feasibility investigation

Status: **investigation complete; construction and action admission not granted**.
Owner authorized the four-point feasibility investigation after rejecting the
thick, unnatural nm prototype. No letter or tool geometry was changed, no
connector created and no raster, fitting or physical execution started.

## Decision in plain language

We are on a more useful conceptual track: the neighbor should select a plausible
entry/exit construction and the connecting stroke should be thin. But another
full-edge connector drawn between today's endpoints is not the right next step.

**Recommend a bounded partial-edge/contact investigation coupled to the nu entry
and exit construction first; carry mu as the larger-gap comparison.** Existing
action machinery can represent this, but neither successful execution nor style
admission for these new boundaries is established. Do not generate previews yet.

The current fixed nib is nearly broadest on an up-right stroke. It is thinnest
on a down-right stroke. In addition, u starts with a descending stem, not a rising
entry like m. These are two independent issues: thinness and attachment topology.

## Evidence and scope

[Read-only report](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/thin-connection-investigation/snapshot-001/report.json),
SHA-256 `0b8b2f84474ef80cd37e94085483e5e312f52d348f46a32a07d972e83bd28aa3`.
It binds canonical candidate, prior clearance, owner feedback and source identities.
27 canonical site pairs inspected in16.497s: nine each for nu, mu and um. These
are domain/site measurements, not connector candidates or optimized parameters.
All site-admission flags remain false.

The outgoing final stem is inspected at baseline, half and full existing
lower-return entry height:0,0.434496,0.868992mm. The incoming u stem is inspected
at canonical parameters0,0.25,0.5, corresponding to3.5,2.956,2.421mm. Incoming m
rise uses the same three height levels as the departure. These finite inspection
grids are not approved replacement bounds, exhaustive searches or selected winners.

### 1. Natural departure and receiving constructions: nu and mu

| Boundary | Existing departure | Existing receiver | Finding |
|---|---|---|---|
| n→u | Final descending n stem | First descending u stem | Needs a departure turn/return and receiving turn, not the old nm receiving-rise splice |
| m→u | Final descending m stem | Same first descending u stem | Same port-level problem, with a materially larger gap |

Canonical horizontal separation is3.392–3.423mm for nu and5.210–5.240mm for mu
over these sites. Gap differences arise from frozen letter placement, not new
spacing choices. A thin connector may still look too long, especially in mu.

Starting exactly at a baseline endpoint with a downward tangent forces initial
below-baseline travel if the path remains smooth. Arriving exactly at u's
x-height start with its downward tangent requires approaching from above
x-height. Thus a smooth baseline-to-u-top bridge cannot simultaneously preserve
both endpoints and stay inside the baseline/x-height band. This follows from
the endpoint derivative signs, not from a rendering failure.

Approaching an interior u-stem site leaves room for a receiving turn, but removes
a real prefix of its first stem—about0.544mm or1.079mm vertically at the two
interior probes. That is a prospective body exception, **not** an already
approved solution. Do not skip u's first stem/underturn into its later rise:
that would change the letter's construction and cannot inherit nm permissions.

The proposed semantic family is therefore: finish the departure body, form an
explicit turning departure, carry a thin pen-down connection, and rebuild the
receiving prefix while preserving u's underturn and remaining body. The exact
geometry and permissions are still to be designed. An unchanged separated
pair is mandatory as the alternative; connecting is not the default assumption.

### 2. Can the present nib produce the desired thinness?

Physical-y-down nib angle40 degrees corresponds to−40 degrees in the geometry's
y-up frame. For travel direction phi, fixed edge length W and tip thickness T,
the rectangular contact's transverse width is:

`W × active_fraction × |sin(phi + 40°)| + T × |cos(phi + 40°)|`.

The current nominal packet uses an ideal0.45mm line edge (T=0). The repository's
opt-in `physical-edge-v1` contact uses W=0.45mm and T=0.02mm. Neither is a promise
of actual ink width. In particular, the physical rectangle has a thickness floor;
an ideal zero-width line parallel to the edge must not be called actual hairline ink.

| Travel direction, y up | Full rectangular contact | 10% active edge |
|---|---:|---:|
| Down-right, −40° | 0.0200mm | 0.0200mm |
| Horizontal right | 0.3046mm | 0.0442mm |
| Up-right, +40° | 0.4466mm | 0.0478mm |
| Up-right, +45° | 0.4500mm | 0.0466mm |

Directions of straight displacements between the inspected nu sites imply
0.415–0.450mm full-contact widths; mu implies0.386–0.438mm. These are directional
diagnostics, **not constructed straight connectors**. Curving a path does not
automatically fix the full-edge width issue: if its entire length must stay thin,
its transverse displacement requires a large total path length.

For discussion, propose thin width <=25% of a fixed-tool vertical-stem reference:
0.25×0.357576=**0.089394mm**. This is a prospective guardrail, not the owner's
confirmed definition of nib-thin, an observed learned-stem width or an accepted
threshold. Under that hypothetical whole-path limit, a full-edge path between
the investigated nu/mu endpoints needs at least4.20–5.02 times the straight-line
distance, using an optimistic integral projection bound that ignores thickness.
That makes a short, wholly thin full-edge connection implausible under this frame.
The bound does not rule out a thin core surrounded by explicitly broader splices;
such splice extents must be declared separately, not hidden in averages.

### 3. Actions, attachment limits and evaluation objective

The repository already has action tracks, active-edge fractions, a finite-contact
rectangle and a rate-limited action bridge. `gesture_guide` alone rejects dynamic
actions; `action_bundle`/`ActionController` provide the opt-in path. The present
nm nominal renderer ignores action tracks and always draws the full edge. Merely
narrowing its raster line would bypass the contact contract rather than implement it.

Compare these prospective options before choosing any new action profile:

- **Keep the full edge/orientation:** simplest preservation, but the up-right
  width and detour findings argue against another short thin connector attempt.
- **Keep orientation, use an active corner:** analytically promising. The model
  permits a minimum10% contact interval; its projected width is below0.05mm at
  representative up-right angles. This is representability, not proven realistic
  pen manipulation or admitted letter execution.
- **Rotate the full nib:** alignment could yield a thin up-right stroke, but
  moving from−40° to about+40° in y-up is an approximately80° reorientation.
  At the existing180°/s actuator ceiling, that change alone takes at least0.444s,
  before restoration. This is a rate bound, not an execution estimate. Do not
  silently change global nib orientation or the accepted body strokes.

Active-corner contact also moves the footprint relative to the nominal center:
using [0,0.1] or [0.9,1] shifts its center by0.2025mm along the nib axis. Both
corner identity and that displacement must be included in clearance and splice
placement. A centered cosmetic10%-width line is not equivalent. Existing endpoint
rate3/s implies at least0.3s to move a full edge endpoint by0.9; account for contact
ramps and restoration, without changing timing limits or launching a controller.

Recommended prospective contract requirements:

1. Use primitive/port/action state plus relative placement—not whole-word names—to
   select a construction. Declare exact departure/receiving source intervals and
   preserve all undeclared body, spacing and anchors. Nu/mu are exposed test cases.
2. Define a thin *core* and bounded transition/splice regions. Report whole-core
   maximum transverse width and contact-ramp extents, not just mean width or a
   pretty cropped image. The0.089394mm discussion limit needs owner confirmation.
3. Keep explicit pen-down ownership, chosen active corner and restored full-edge
   body contact. No pen lift disguised as a thin line; no unowned bridge.
4. Retain direction continuity, nonzero derivatives, curvature/length/excursion
   checks, and full-frame evidence. New turns and body exceptions need prospective
   bounds; neither nm's geometry nor its splice disks automatically transfer.
5. Recheck actual0.02mm-thick corner footprints, both attachment access paths and
   the entire proposed sweep, including transition phases and motion uncertainty.
   The current full-edge site audit is only an initial screen.
6. Keep separation as a negative/alternative control. Style success means a
   purposeful, readable connection preferred by the owner—not merely visible
   change or collision-free geometry. No numerical style score is fabricated.

### 4. u→m and compositional num

Full-edge site footprints for nu/mu have no detected nonowner contact in this
inspection. This does **not** prove thick-contact/corner access or connector
clearance. For um, all investigated outgoing sites still have possible contact:
baseline departure encounters u's retained lower-return0:1; the positive-height
departures encounter its retained rise0:2. Receiving m-site footprints do not add
a nonowner contact in this screen. Original overlap relationships are not new
permissions for a future boundary stroke.

Num requires two separately supported boundaries, n→u and u→m. The u must retain
one coherent body and contact lineage while its entry and exit modifications
compose; independently plausible pair patches are not automatically compatible.
Do not concatenate pair images or fit a num-specific residual. The um issue is
still a stop condition, so no num construction or evaluation is admitted.

Num was sealed in older protocols. The owner has now named it explicitly and
its canonical topology was inspected in this conversation. No target/heldout
loss, image or performance was inspected, but do not describe it as fresh unseen
evidence for a future study. This audit's executable inventory is only nu/mu/um;
num appears as a dependency analysis, with no new word candidate or target access.

## Next decision

Approve a **corner-contact capability and coupled nu entry/exit proposal**, with
mu retained as a larger-gap comparator. First resolve whether the intended
nib-thin style means partial-corner contact or a different pen orientation, and
agree on thin-core versus broader-splice limits. This is narrower and more useful
than approving another connector grid. Do not start fitting or physical runs.

Once geometry/action/ownership bounds are defined and approved, a subsequent
proposal can specify a new finite-contact nominal renderer and its image budget.
No new rendering allowance, body exception or physical budget is created here.
CURRICULUM-016 remains in progress; HANDVALIDATE-025/026 remain gated.
