# TD-018 — n→m-only construction proposal

Status: **proposed for owner approval; not implemented or rendered**.
Date: 2026-09-10. Implements the next design decision from
[Addendum E](TD-018-addendum-e-boundary-construction.md), without modifying that
frozen input, old H0–H3, their nominal packet or the accepted upright foundation.

## 1. Owner decision in plain language

Propose one deliberately bounded **connected n→m prototype**, compared with the
unchanged separate n and m. Instead of rotating tiny handles, it would:

1. Retain the upright n body, replacing only the lower part of its final stem
   with a terminal turn that still reaches the baseline.
2. Continue through one explicit, owned pen-down transfer.
3. Enter the existing rising stroke of m above its original starting point,
   retaining the rest of m unchanged.

This is a proposed connected lettering style, not a historical-ductus claim or
a declaration that every neighboring pair should connect. The long gap may
still make it unattractive. A visible but unnecessary connector is not success.

**u→m is deferred.** Its departure footprint encounters its retained rising
stroke; no new overlap exception for u is proposed. m→m remains a larger-gap
unchanged control. n→n remains an incompatible-receiver unchanged control.

Approval requested: implement **one deterministic geometry candidate**, reject
it if any hard constraint fails, and only if it passes generate the bounded
nominal comparison packet in section 8. No parameter search, automatic second
candidate, physical simulation, fitting, changed spacing or production activation.

## 2. Evidence and why this candidate

| Frozen evidence | SHA-256 |
|---|---|
| Candidate object | `96aced30b45e5ef09eb219643c4eb068a332fcdab3a3ae466ee5fe5aa7993ca3` |
| Attachment investigation | `b555be20ccfc179be57b7ac701ded640741a4a9947a124ccbddef91550fe5a1e` |
| Finite-nib clearance investigation | `d7dd39b61b91572d1ee3e241e0583266be9dcd9e4f0f577f74e9964820033943` |

Both proposed attachment footprints in nm clear other canonical occurrences.
Own-stroke contact remains expected and must be handled explicitly. The open
central strip does not prove that a connector exists or that it will look good.

Choose the **higher matched-height attachment pair** for this single proposal:
0.868991622382580 mm above the baseline, computed from the existing lower-return
entry height ×3.5, not the rounded display value. Its purpose is to provide more
vertical turning/receiving room than the lower pair while leaving all earlier
occurrences intact. This is a design choice, not a measured optimum or selection
by largest clearance. The lower and mixed-height pairs are not fallback attempts.

The exact canonical parameters must be read from the pinned attachment report:
departure approximately0.764806878, receiving approximately0.270541392. Do not
reconstruct source geometry using these rounded values.

## 3. Explicit body and baseline exceptions

Coordinate convention for geometry below: physical millimeters, x right, y up;
baseline y=0. Fixed tool: full edge0.45 mm, physical-y-down40 degrees, pressure0.5,
existing12 mm/s cap. Physical rendering converts y consistently; no action changes.

| Site | Canonical interval retained | Proposed replacement |
|---|---|---|
| n final stem, occurrence `0:3`, cubic0 | [0, departure t] | [departure t,1] replaced by terminal-turn cubic |
| m first rise, occurrence `1:0`, cubic0 | [receiving t,1] | [0,receiving t] replaced as part of the arriving boundary construction |

Every other cubic, internal corner/join anchor, letter advance and recipe/action
definition stays exact. Retained intervals are exact canonical subcurves, not
approximated replacements. Source identities remain immutable.

This is materially more than the old handle exception:

- n's final baseline foot may move **0.225 mm to the right** of its canonical
  baseline endpoint (half the full nib width); its baseline height stays0.
  The upright retained stem is not shifted or slanted as a whole.
- The m entry's original baseline starting point is **not retained as an
  independent contact point** in the connected version. The arriving path joins
  the canonical rise at the approved higher site. Isolated m remains unchanged.
- The connected pair must retain all other baseline contacts and x-height
  landmarks. The new turn has one baseline minimum; no centerline below baseline.

These two baseline-anchor exceptions need explicit owner approval. They are not
implied by the clearance result or by calling a span “entry/exit.”

## 4. One deterministic construction rule

Proposed version: `nm-turn-rise-construction-v1`, isolated from all frozen
executing contracts. The following equations specify a candidate, not a claim
that its geometry has already been evaluated.

Let A be the canonical departure point, C the canonical receiving point, and F
the original endpoint of n's final stem. Let dA and dC be the corresponding
unit directed tangents in physical-y-up coordinates. Both attachment heights
are h. Let W=0.45 mm be the full nib width.

- B=(F.x+W/2,0): the single baseline turn point.
- Reject unless dA.y<0, dC.y>0, B.x>A.x and C.x>B.x.
- Departure-handle length a=0.9h/abs(dA.y).
- Turn-handle length b=2(B.x−A.x)/3.
- Transfer departure-handle length c=(C.x−B.x)/3.
- Receiving-handle length d=0.75h/dC.y.

Two cubic Bezier pieces, no additional degrees of freedom:

| Piece | Control points |
|---|---|
| Terminal turn T | A, A+a·dA, B−(b,0), B |
| Transfer/receiving R | B, B+(c,0), C−d·dC, C |

The ratios are explicitly proposed construction constants, **not fitted values**.
They allocate most of the terminal descent before the baseline turn and leave
a rising approach into C. Their acceptability is conditional on the independent
checks below. Do not tune these constants if the first candidate fails.

T and R have matching rightward tangent directions at B. This is geometric
direction continuity, not equality of Bezier parameter speeds or proof of
physical timing. A and C must match the retained canonical tangent directions.

## 5. Hard geometry checks before any image

All must pass. Unresolved numerical classification means stop, not approximate
acceptance. No automatic widening, repair loop or alternate site selection.

| Check | Proposed limit / requirement |
|---|---|
| Unchanged body and placement | Exact retained subcurves and all undeclared control points/anchors/advances |
| Allowed edits | Only the two declared source intervals and two new pieces |
| Attach positions | Match canonical A/C within1e-9 mm numerical accounting; no geometric allowance to move them |
| Directed tangents | Unit-vector error <=1e-8 at A, B and C; no zero-speed geometric derivatives |
| Baseline and extent | Entire new centerline in [A.x,C.x]×[0,h]; only B reaches y=0; no overshoot above h |
| Direction/retrace | x strictly increasing in the new construction; T descends and R rises; no loops, reversals or retrace |
| Length | Combined T+R arc-length upper bound <=1.25×sqrt((C.x−A.x)²+(2h)²), approximately4.7973 mm |
| Curvature | Radius >=W/4=0.1125 mm, equivalently curvature <=8.888888889/mm everywhere on T/R |
| Other-stroke clearance | Positive certified nominal finite-nib clearance outside declared splice regions; uncertainty rejects |
| Body landmarks | All unchanged landmarks exact; only n-foot shift and connected m-start removal allowed |

The length ceiling limits detours relative to the necessary baseline-touch path;
the radius floor avoids an arbitrarily sharp turn substantially smaller than the
nib. These are proposed design guardrails, not historical standards or existing
mechanical thresholds. Physical speed/acceleration feasibility is separate and
may require slowing down within the existing cap; it is not evaluated here.

Use analytic extrema or conservative subdivision bounds for whole-curve checks,
not a small point grid that might miss a loop, overshoot or curvature maximum.
Use bounded arc-length integration. Record margins and failed constraints, not
just a aggregate score. No root/constraint calculation is a license to optimize
the control points; they are fixed by section 4.

## 6. Finite-nib overlap and ownership

All new ink must have provenance and ownership before any nominal rendering.

- T belongs to the derived n departure construction, with lineage to the removed
  n stem suffix. R is a boundary-owned transfer/receiving construction with both
  n departure and m receiving contributors, including the removed m prefix.
- Retained canonical strokes keep their letter/gesture/action identities. A
  shared contact run does not erase their owners. No anonymous bridge or duplicate
  draw of a replaced interval is allowed.
- Permit nominal attachment overlap only between retained-n/T at A, T/R at B,
  and R/retained-m at C. For each pair, require the full intersection to lie
  within a **0.45-mm-radius disk** centered at its named join. Maximum permitted
  intersection area per join is therefore at most π·0.45² mm²; region containment,
  not merely total area, is mandatory. These are proposed overlap exceptions.
- All other new-to-retained and nonlocal new-to-new overlap must be absent with
  certified separation. Do not waive an entire primitive/gesture merely because
  one end participates in a splice. Adjacent original joins remain unchanged.
- Curve-flattening uncertainty must be conservatively included in both collision
  and overlap-region checks; the existing0.00001-mm geometric error is a starting
  measurement precision, not a clearance waiver. If bounds cannot decide a case,
  mark it unresolved and stop before rendering.

The old u overlap declarations grant no permission here. Nominal overlap-region
admission would still not approve ink accumulation or motion near a join.

## 7. Versioning, scope and negative controls

Planned opt-in implementation paths, outside frozen core identity scans:
`scripts/stroke_nm_construction.py`, `tests/test_stroke_nm_construction.py`,
`scripts/templates/stroke_nm_review.html`, and
`shared/training/konrad_hand_recovery/stroke_gestures_v2/nm-construction-v1/`.
Before implementation, bind the owner's approval to this proposal's exact hash
in a separate record; preserve old approval files and do not reuse the consumed
48-image rendering allowance. Existing gesture/curriculum components suffice.

Do not feed this construction into `connected-v1` or change its six-occurrence
limit. A new geometry-only document may hold at most **12 bounded pieces** for
nm: ten retained canonical occurrence pieces, one departure-turn piece, and one
boundary piece. This is an explicit new representation, not an old-cap bypass.
No new physical consumer is included in the requested approval.

Select by current n departure site, receiving m rise site, fixed relative
geometry and explicit connection-permitted policy, not by full-word/fixture/seed
keys. The demonstrator admits only the frozen exposed `nm` arrangement as an
active boundary; this narrow scope is not a generalization claim. All unsupported
layouts/sites fall back explicitly or reject, never silently connect.

Keep B0 canonical separate and B3 the joint prototype. Do not fabricate B1 by
removing R and leaving m with a truncated entry; do not claim B2 transfer-only
works with the original baseline endpoints. Both remain unsupported here.

Required adverse tests: wrong receiver (nn), oversized/unadmitted layout (mm),
deferred u departure, fake air/contact, missing boundary owner/contributor,
duplicate old suffix/prefix ink, undeclared body edit, source repinning, inverted
tangent, cusp/reversal, undetected curvature peak, overlap outside splice disks,
changed spacing and forged approval. Null compilation/planning remain exact.

## 8. Proposed nominal packet and resource approval

Only after every hard check passes, propose **10 PNGs + one review page**:
five exposed texts n/m/nm/nn/mm × B0/B3-mode. B3 changes nm only; the other four
are exact unchanged controls with matching image hashes across modes. No um,
new triples, word-heldout text or additional family enters this packet.

Use the existing nominal fixed-edge method, full frame [-3,30,2,13] mm,900 dpi,
1169×390 pixels and full-frame-first comparisons. Clearly label **NOMINAL
CONSTRUCTION — NOT ACTUAL INK**. Optional synchronized zoom/ownership overlays
reuse the same files, not additional diagnostic rasters or replacement targets.

Prospective limits: geometry/verification preparation **300 seconds**, packet
generation/verification **300 seconds**, combined output **100 MiB**, minimum
free disk **5 GiB**, no automatic retries and no controller or fitting calls.
These are explicit proposed local ceilings, not measured runtime estimates or
a reset of old physical budgets. Preserve failed outputs and stop on a cap.

Review the change at normal scale: does it still read as our upright n followed
by m; does the connection look purposeful rather than like an underline; is it
preferable to separation? “Unnecessary,” “less readable,” “too long” and “separate
letters preferred” are valid outcomes, not reasons to retune automatically.

## 9. Gates and current state

1. **Now:** review this construction, explicit body/overlap exceptions and local
   resource scope. No geometry is generated by preparing this proposal.
2. **If approved:** implement strict geometry-only version and checks, calculate
   the single candidate once, preserve failure or produce the bounded nominal
   packet only on a full structural pass. No fitting or automatic recovery.
3. **Then:** record owner usefulness judgment. Only a useful, supported candidate
   warrants a separately approved physical planner/reader/protocol and budget.

Keep CURRICULUM-016 in progress; HANDVALIDATE-025/026 remain gated. No additional
advances, components, branches, commits or merges are created by this proposal.
Existing canonical sources, reports and approval records remain untouched.

## 10. Proposal validation

ARRIVE plan, generated-rule, changed local-link and whitespace checks pass.
Exact pinned read-only reinspection of the clearance report passes, including
its attachment/design/source and original/recovery evidence checks. This is
documentation/governance work: no candidate control points were generated or
tested, no behavioral suite was rerun, and no new sample or execution is claimed.
Changes remain uncommitted.
