# TD-018 — Local footprint overlap versus nonlocal return contact

Status: **classification proposal prepared at owner request; not yet applied**.

## 1. Meaning and scope

A finite nib normally covers some of the same paper at neighboring positions
while moving through one stroke. That is not, by itself, a retrace or collision.
The prohibited case is contact with a separate or returning portion of the
path, rather than the local neighborhood currently being drawn.

This document proposes an explicit, conservative sufficient rule for **ordinary
neighboring-path overlap inside the constant-contact R run only**. It does not
permit other letters, T/S, separate strokes or lifted runs to overlap. Those
retain their existing separation tests and four named splice permissions.

This fills a previously unresolved acceptance definition. It is a proposed
classification/permission change, not proof that the old rule already passed.
Thinness, curvature, geometry and all existing numerical limits stay unchanged.
The frozen unresolved reports must remain unchanged after any future approval.

## 2. Definitions

Let c(s) be the centerline of aggregate R, parameterized by cumulative arc length
across all three cubics. Let F(s) be its actual fixed-orientation finite rectangle
at the negative10% corner. It has normal thickness h=0.02mm and active edge
length0.045mm. The constant corner offset is retained; pairwise offsets cancel.

Use the fixed nib-normal direction n=(sin40°,cos40°) in physical y-up coordinates.
Let z(s)=n·c(s). For a paper point x, its **normal contact window** is the set of
path parameters for which x lies within the footprint's normal-coordinate slab.
This is only a necessary condition for full rectangle membership.

When z is strictly increasing through one continuous run, that normal contact
window is a single interval. The path cannot leave it and later re-enter it.
Membership along the rectangle's edge direction can change within that window;
that alone does not mean the pen has returned from a remote part of the path.

## 3. Proposed ordinary-overlap certificate

Classify possible R-to-R overlap as ordinary neighboring-path coverage only if
all of the following are certified over the complete applicable run:

1. **Same run and footprint:** continuous position and directed tangent through
   P/Q; no hidden lift, action reset, contact-size change or nib rotation. No
   coincidence between different owners is admitted under this rule.
2. **One-way progress:** z'(s) has a certified strictly positive lower bound m.
   For the current positive-x/nonnegative-y family, m can be bounded by sin40°,
   with the existing numerical accounting guard. Do not infer this from samples.
3. **Finite normal window:** every overlapping pair lies within one normal
   contact window. Its entire intervening arc has length at most h/m, with
   outward numeric guards. Derive this bound from footprint and motion geometry;
   do not hard-code the current0.031114480mm result as a new tolerance.
4. **No local fold-back:** the integral of absolute curvature over that entire
   intervening arc is strictly less than pi/2. A sufficient bound is the
   unchanged curvature ceiling times the guarded h/m bound. Tangent continuity
   must be checked separately: a cubic-join corner cannot evade the integral.
5. **All external gates pass:** existing geometry, source coverage, thinness,
   length, envelopes and external-contact/splice checks remain mandatory.

The pi/2 condition is a **new proposed conservative classification guard**:
directions within the overlap window cannot turn through a right angle. It is
not a relaxed curvature limit, a physical guarantee or an established historical
scribal standard. A boundary-equality or uncertain certificate is unresolved.

Under this rule, even leave-and-reenter *edge-coordinate membership* can be
ordinary if confined to that one forward, non-folding normal window. This is
an explicit distinction from requiring each paper point to have one uninterrupted
full-rectangle membership interval. That stronger rule would be a different
contact policy; it must not be silently substituted during implementation.

## 4. Prohibited and unresolved cases

| Situation | Classification/action |
|---|---|
| Same continuous R run, all ordinary-overlap certificates pass | Ordinary neighboring-path coverage; no extra overlap disk needed |
| Certified overlapping disconnected/lifted runs or other owners outside existing named permissions | Prohibited contact |
| Certified return to earlier path after leaving its forward normal window, or a loop/retrace forbidden by geometry rules | Prohibited nonlocal return contact |
| Positive progress, curvature integral or contact membership cannot be certified | Unresolved, not automatically prohibited or accepted |
| Sufficient ordinary certificate fails without a collision/return witness | Unresolved; preserve evidence, no automatic relaxation |

Nearness in Euclidean distance, being in the same cubic/owner, or sharing a
numerical endpoint is never enough to authorize overlap. Conversely, splitting
one stroke into more cubics must not make ordinary local overlap a collision.
Length and locality accounting continue across P/Q without resets.

## 5. What saved evidence suggests, without granting a pass

The [saved measurement](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/self-contact-review-001/README.md)
bounds possible R self-overlap to0.031114480mm arc separation and total turning
to0.276573153 radians, below pi/2. It also records exact unchanged structural
results and external-contact reinspection. These values suggest the proposed
sufficient classification may resolve the remaining gate.

That is an inference from saved evidence, not a newly executed classifier or
retroactive acceptance. A versioned implementation must check every premise,
including constant footprint, chain continuity and the curvature bound, against
the pinned candidate before reporting a result.

Pins for a future approval manifest:

- Candidate: `16872e32eb44d15c2b226a4327a75851bf6a286ba08568930f856c554e97c433`.
- Original derived report: `8123f6684aaf0dd01ea384defa97e8547ddcaa259ba0ec149ce00bf8c759f30c`.
- Stronger measurement report: `6bd3453b1ff86f7e6461ff77cecc4026f23a6cd0097a3284271b12e39dc20278`.

## 6. Implementation and evaluation boundary

Proposed classifier identity: `nu-local-contact-classification-v1`. Keep both
previous checkers/reports frozen. Implement a separate saved-candidate consumer
that verifies this document's approval/hash and the three evidence pins above.
No constructor, refitting, new geometry or altered thinness/curvature limits.

Test ordinary adjacent sweeps across cubic joins, within-window edge-membership
changes, nonlocal return/disconnected paths, contact/action mutation, zero or
reversed normal progress, uncounted tangent corners, ambiguous pi/2 bounds and
attempts to apply this R-only permission to T/S or other letters.

After explicit approval: one300s saved-candidate classification/reinspection,
10MiB new evidence maximum, minimum5GiB free space, zero automatic retries,
images, physical runs or fitting. Save under
`nu-contextual-entry-v1/local-contact-review-001/` and report classification
separately from geometric, nominal visual and physical acceptance.

No execution in this documentation turn. Mu and nominal rendering remain gated.
If the classifier passes, the next separately approved work is the planned
same-scale canonical/old-bridge/derived-entry nominal comparison for owner review.
