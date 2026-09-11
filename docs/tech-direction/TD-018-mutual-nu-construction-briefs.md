# TD-018 F1 — Two reciprocal nu construction briefs

Status: **F1 documentation prepared; numeric construction choices and F2 execution
await owner approval**. These are testable design hypotheses, not successful
geometry, samples, historical ductus claims or accepted handwriting.

Parent: [Addendum F — mutual letter flow](TD-018-addendum-f-mutual-letter-flow.md).
The owner finds the derived entry wrong and the old bridge better but still
wrong. Neither is the target to optimize against. Preserve both and the
[review evidence](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/nominal-001/index.html).

## 1. Decision requested

Review these two **fixed stroke programs**, their replacement regions and the
measurement contract before constructing either. J1 gives u a distinct upright
entry rise; J2 distributes the rise into a departing n and a rising u crown.
Both replace part of n and part of u. Neither keeps the old T/S curves or uses
the old bridge to locate internal points. All travel described here is pen-down.

Recommendation: compare these two shape hypotheses at fixed nib angle first;
do not add rotation, tighten spacing or introduce more candidates to rescue one.
If neither looks natural, use that result to revisit the construction or spacing,
not to begin fitting. A future rotation study requires its own approval.

## 2. Frozen reference and coordinate contract

Canonical model:
[upright candidate](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/upright/run-001/candidate.json),
file SHA-256 `01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd`.
Compile the existing canonical `nu` placement without context. Let H=3.5mm;
coordinates below are divided by H, with baseline y=0 and positive y upward.
Occurrence IDs refer to that compiled pair, not standalone primitive indices.

- `N(t)` is n's final stem, occurrence `0:3`, directed downward.
- `U(t)` is u's initial stem, occurrence `1:0`, directed downward.
- `foot_x = N(1).x = 0.2807304692649836`.
- `stem_x = U(0).x = 1.25` in the fixed pair placement.
- `t` is the source cubic parameter, **not** arc progress or time.

The reference supplies exact coordinates/tangents, not a fitting target. Protect
n occurrences `0:0`–`0:2` and u occurrences `1:1`–`1:3`, their actions and
placement. Protect the retained portions in the tables below by exact de Casteljau
restriction. Standalone n/u, every other pair and context-off output remain exact.
No changes to letter advance, the canonical gap, baseline, H or slant parameters.

## 3. Brief J1 — receiving-rise-led

**Intent:** n rolls out at its foot toward a distinct ascent belonging to u.
That ascent runs upright beside u's first downstroke, then turns over and descends.
This tests a recognizable receiving stroke rather than one long rising bridge.

| Port | Fixed location in H units | Directed tangent | Responsibility |
|---|---|---|---|
| A | `N(0.7648068784772746)` | canonical unit `N'` | End of retained n stem |
| F | `(foot_x + 0.08, 0)` | `(1,0)` | Contextual n foot/departure |
| P | `(stem_x - 0.16, 0.45)` | `(0,1)` | Arrival at u's distinct entry rise |
| Q | `(stem_x - 0.16, 0.88)` | `(0,1)` | End of upright entry rise |
| K | `(stem_x - 0.08, 1.00)` | `(1,0)` | u entry crown summit |
| C | `U(0.35)` | canonical unit `U'` | Restore canonical u descent |

Program: **terminal turn A→F; approach F→P; upright rise P→Q; crown Q→K;
receiving descent K→C**, followed by retained u. P→Q is a genuine straight
upright segment, not a relabeled portion of the old diagonal R. Its nominal
horizontal offset from the original u stem is 0.16H=0.56mm; this is a proposed
spacing of the entry stroke, not permission for ink overlap.

Replace n `0:3[tA,1]` and u `1:0[0,0.35]`. The neighbor u sets F's outward
departure and the approach into P; the preceding n supplies the incoming foot
and tangent from which u's added ascent is reached. u's old top is replaced by
the leftward crown and return to C. Nothing above n's cut is reshaped.

**Expected visible distinction:** a separate, nearly parallel entry/upstroke
and downstroke at u, with a slightly extended n foot. **Failure to watch for:**
the fixed gap still demands an obvious transport stroke F→P, or P creates a
new shoulder despite tangent continuity. This is not assumed to solve either.

## 4. Brief J2 — shared accommodation

**Intent:** n begins accommodating the next letter earlier in its final descent;
the departure becomes a continuous rising follow-through into u's rising crown.
There is no separate upright entry run. u accepts a wider, slightly higher entry
and settles into its canonical descent farther down than J1.

| Port | Fixed location in H units | Directed tangent | Responsibility |
|---|---|---|---|
| A | `N(0.65)` | canonical unit `N'` | Earlier start of n accommodation |
| F | `(foot_x + 0.12, 0)` | `(1,0)` | Contextual n foot/departure |
| P | `(stem_x - 0.22, 0.62)` | `(0.4,sqrt(0.84))` | Handoff from n follow-through to u rising crown |
| K | `(stem_x - 0.10, 1.02)` | `(1,0)` | u crown summit |
| C | `U(0.45)` | canonical unit `U'` | Later restoration of u descent |

Program: **terminal turn A→F; rising follow-through F→P; rising crown P→K;
receiving descent K→C**, followed by retained u. Unlike J1 there is no Q,
no vertical P→Q interval, and no discrete approach-to-u-rise transition.

Replace n `0:3[0.65,1]` and u `1:0[0,0.45]`. u's receiving direction causes
an earlier/larger n terminal response; n's outgoing direction becomes the entry
direction of u's new crown. The added n follow-through and u crown meet at a
shared directed port, not an independent bridge with frozen endpoints.

**Expected visible distinction:** more change within n's final descent and u's
upper receiving form, with the ascent distributed across them. **Failure to
watch for:** the wider n foot looks like a flourish, the u crown loses identity,
or this reads as the same bridge with new labels. If the two programs produce
indistinguishable behavior, record that failure rather than adding variants.

## 5. One deterministic construction rule; zero search

Convert all locations to mm before computing controls and measurements. Ports,
cuts and constants above are fixed proposed design choices, not tunable domains.
Require nonzero finite chords, ordered source intervals and downward canonical
join tangents. One evaluation per brief, no handle grids or root-selected ports.

For A→F, let `departure = unit(N'(tA))`, `drop = A.y`, and
`reach = F.x-A.x`. Require positive drop/reach and negative departure.y.
Use exactly:

`[A, A + (0.9*drop/abs(departure.y))*departure, F-(2*reach/3,0), F]`.

For K→C, let `receiving = unit(U'(tC))`, `drop = K.y-C.y`, and
`reach = C.x-K.x`. Require positive drop/reach and negative receiving.y.
Use exactly:

`[K, K+(2*reach/3,0), C-(0.75*drop/abs(receiving.y))*receiving, C]`.

These reuse the old terminal/receiving **rule**, not its geometry or anchors.
For every other adjacent port pair Start→End with unit directions start_dir
and end_dir, let `handle = distance(Start,End)/3` and use exactly:

`[Start, Start+handle*start_dir, End-handle*end_dir, End]`.

This is a new bounded Hermite-derived grammar, not exact canonical primitive
reuse. Store rule name/version, port values, source intervals, canonical hash,
units and contributors. No clamping, extra handles, fallback directions or
candidate generation is authorized by writing these formulas.

## 6. Replacement envelopes and directed joins

The following are **proposed new spatial contracts**, not measurement-only
repairs to the old candidate. Each is a bound on the entire curve, not controls
or sampled points. In this table A/F/K/C denote the converted mm ports, while
foot_x remains the dimensionless reference in section 2. Canonical protected
curves are exempt from new-region boxes.

| Region | Proposed permitted centerline envelope in H units |
|---|---|
| n terminal A→F | `[foot_x-0.02, foot_x+0.15] × [0,A.y/H]` (A.y converted back to H units) |
| Approach/follow-through and u ascent, F→K | `[F.x/H,K.x/H] × [0,K.y/H]` |
| u receiving K→C | `[K.x/H,C.x/H+0.0045/H] × [C.y/H,K.y/H]` |

A→F may make a canonical-tangent-driven initial left excursion of at most
0.0045mm from A, confined to a 0.1125mm disk around A; otherwise it moves
right/down. F→K moves monotonically right/up, allowing a vertical interval
only in J1 and the prescribed horizontal endpoint tangents. K→C moves down,
allowing at most one rightmost extremum followed by its canonical leftward
arrival; every point right of C lies in its 0.1125mm disk and within 0.0045mm.
Reject extra extrema, loops, cusps or uncertain classifications. No retrace
permission is proposed in this first test, even though intended travel stays
pen-down. A future retracing entry needs a different explicit contact contract.

All joins must match position within 1e-9mm and directed unit tangent within
1e-8. This is geometric tangent continuity, not equal parameter speed or
physical acceleration continuity. Require nonzero derivatives everywhere.

Ownership is separate from evaluation partition: A→F is contextual n; in J1
F→P is n departure toward u and P→K is contextual u entry; in J2 F→P is n
follow-through and P→K is contextual u rising crown. K→C is contextual u.
Every new piece records both pair contributors and whether it replaces a
source interval or adds entry travel. Added travel must not claim canonical
source coverage; the replaced/retained source intervals partition exactly once.

## 7. Contact, action and length contract

Use fixed 40° orientation in the physical y-down frame, reflected correctly
from the y-up geometry; tool 0.45×0.02mm, pressure 0.5. No lift, rotation,
pressure adjustment or random variation. Speed cap 12mm/s is not a schedule.

Both programs share one action policy, parameterized by each aggregate's own
arc length: A→F linearly changes active edge interval `[0,1]` to `[0,0.1]`;
F→K holds `[0,0.1]`; K→C reverses that ramp. No action resets at P or Q.
These are directed negative-corner intervals, not centered narrow rectangles.
Exact endpoint arithmetic and contact-center offsets are mandatory.

- F→K is the **entire thin-core domain**, regardless of letter ownership or
  subdivisions. Its maximum finite-nib width stays at or below
  `0.25*(0.45*cos40°+0.02*sin40°)` ≈0.089393938mm. Ramps are reported
  separately, never counted as thin-core passes by trimming their broad ends.
- Radius stays at least 0.1125mm (curvature at most `1/0.1125` per mm)
  everywhere, including ramps; no exceptions at semantic joins.
- Length partitions are A→F, aggregate F→K and K→C. Each length must be
  at most 1.25 times **that aggregate's endpoint distance**. Splitting at P/Q
  does not create additional allowances. These changed anchors/partitions need
  approval; report absolute lengths alongside the frozen old partitions and
  never compare their normalized ratios as an unchanged-target improvement.
- Proposed contact permissions are only adjacent aggregate/body joins at
  A/F/K/C, each with the existing 0.45mm splice-disk radius but **new named
  centers and explicit adjacent owners**. Approval of old centers does not
  approve these. No extra disk at P/Q, and no disk-union permission for
  nonadjacent owners or remote parts of an adjacent aggregate.
- Measure the full finite nib against all retained geometry and new aggregates,
  including each aggregate's nonlocal self-contact. Do not transplant a saved
  self-contact certificate to this topology, broad ramps or receiving descent.
  Uncertified contact remains unresolved, not visually excused or discarded.

**Explicit new local-contact proposal for F→K:** both programs turn toward
upward travel and then back toward rightward travel. The old R-wide total-turn
guard is therefore not an appropriate automatic admission route. Propose a
window-local version of the [ordinary-overlap rule](TD-018-local-contact-classification.md),
requiring separate approval and checker tests:

1. Certify a strictly positive lower bound `normal_progress` on unit tangent
   projection onto the fixed nib normal throughout the complete thin aggregate.
   No sign reversal or repeated normal-coordinate window is permitted.
2. Any shared ink point's contacting centerline positions must lie in a single
   contiguous arc window of length at most `0.02/normal_progress` mm, derived
   from the unchanged physical nib thickness. Certify this for the finite
   corner footprint, not a zero-width line or sampled approximation.
3. Bound total turning in every such window, including joins, by
   `curvature_upper_bound * 0.02/normal_progress < pi/2`. The curvature limit
   itself stays unchanged. Classify only that contiguous local overlap as
   ordinary; any possible overlap outside the certified window is prohibited
   or unresolved. There is no permission for a later return into an earlier
   window, or for contact with n's/u's neighboring broad strokes.

This changes the **domain of the turn guard from the whole thin aggregate to
each possible overlap window**; it is not an already-approved measurement-only
repair. No claim is made here that either unevaluated curve passes. Tests must
include reversed normal progress, nonlocal returns and uncertain bounds. If
this rule is not approved or cannot be certified, stop before nominal rendering;
do not weaken the guard implicitly. Broad ramps still need their own complete
finite-nib self-contact measurement and the explicit adjacent-owner permissions.

## 8. Proposed F2 execution and review gates

Approval must name **both brief versions, new cuts/envelopes/ports, contact
permissions and window-local turn guard, action/length partition and budget**. Existing approvals cover
neither these geometries nor their new contact domains. Freeze the approved
document hash before implementing the opt-in constructor/checker. No core
curriculum, trained model, renderer or pinned evidence script is overwritten.

1. Verify frozen reference/evidence hashes and checker prerequisites. Add tests
   for exact source coverage, context-off identity, directed joins, reflected
   corner contact, aggregate accounting, and deliberate out-of-envelope,
   curvature/contact failures. Implement without rendering new candidates yet.
2. Construct at most one J1 and one J2 using the specified rules. Record controls,
   lineage, action map and all checks, including unresolved results. A technical
   prerequisite failure stops the batch; an ordinary candidate rejection is
   preserved and does not authorize a retry or a new parameter choice.
3. Render only admitted geometry. A failed candidate gets a textual status
   panel, not a misleading ink sample. Use one common full frame containing
   the union of all displayed finite-ink bounds plus one nib width padding;
   keep identical baseline, x-height, placement, scale and detail crop.
4. Deliver canonical unconnected and frozen old bridge controls plus admitted
   J1/J2; old is labeled **owner-rejected, relative reference only**. Link the
   rejected derived entry without altering its evidence. Show individual
   canonical/contextual n and u overlays and the complete pair. Label added
   travel and protected bodies; do not invent unilateral connected ablations.
5. Show direction/sequence at normalized arc progress, explicitly **not physical
   timing**. Ask separately about n/u identity, flow, entry/downstroke relation,
   thinness, shelves/bulges and whether both letters respond. Preserve ties,
   uncertainty and exact owner feedback; no scalar reward or fitting objective.

Also report `stem_x-foot_x` (0.9692695307350164H, approximately 3.39244mm),
the unchanged canonical origin spacing and actual F→K horizontal span. This
large centerline distance is not a nib-clearance measurement. If the nominal
approach still looks like a long bridge, explicitly ask whether fixed placement
is the problem; do not quietly move u or widen the editable regions.

Proposed ceiling: two new fixed candidates, one batch, zero automatic retries;
300s total construction/check wall time and 300s total rendering wall time;
25MiB new evidence and at least 5GiB free before starting. Budget exhaustion
preserves partial results and stops; no physical runs or fitting. Output ceiling:
one versioned manifest/report, one HTML board, at most three SVG/PNG pairs
(plain board, ownership overlays, sequence/detail), and one review record.
Persist failure records within the same allowance; do not generate trajectories
or frame sequences. Implementation/tests precede the separately timed batch.

Success is an owner-understood construction worth pursuing, not a mandatory
winner. If selected, prepare one separate fixed-versus-variable nib-angle
proposal on that exact path. Mu, physical budgets, fitting, fatigue, alphabet
expansion and general contextual-program integration remain gated.

## 9. F1 evidence boundary

This delivery contains specifications only. No new control points have been
evaluated, candidates constructed, samples rendered, contact certificates claimed
or fitting/physical runs started. Proposed numeric choices have not been shown
feasible. Existing candidates and all previous passing/failing evidence remain
untouched. CURRICULUM-016 stays in progress; F1 readiness is not F2 approval.
