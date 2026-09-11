# TD-018 — Bounded contextual-entry port/envelope feasibility

Status: **proposal prepared; execution not started**.

This is the next step after the [gesture audit](TD-018-contextual-u-entry-audit.md).
It asks what adaptation is necessary to derive a natural entry program from
existing gestures, without turning that question into an unconstrained search.
Approval of this document's preparation is not execution or geometry approval.

## 1. Decision to obtain

For nu only, distinguish:

1. **Exact geometric reuse:** existing primitive subcurves with an explicitly
   allowed similarity transform can satisfy the required directed ports.
2. **Derived adaptation required:** reuse the stroke grammar, but one or more
   endpoint directions, handles or envelopes must change. Quantify and name the
   required change before selecting a construction.
3. **Conflict or unresolved:** current source cuts, contact phases or envelopes
   cannot be certified compatible within the investigated family. Stop; do not
   broaden that family or treat this as proof that all contextual entries fail.

A necessary-condition pass is not geometric feasibility or owner acceptance.
An empty or unresolved bounded analysis is a valid outcome, not a reason to fit.

## 2. Frozen control and immutable requirements

Read canonical model `letters/upright/run-001/candidate.json`, the saved nu
candidate and the existing boundary-action/receiving-envelope evidence under
`shared/training/konrad_hand_recovery/stroke_gestures_v2/`. Verify their existing
hash pins before and after the investigation. Preserve all old reports and samples.

- Canonical model file: `01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd`.
- Saved nu file: `7268952cd29fc7737c726838107e25f6bf0deeb4537992a8b415713150b0db97`.
- Gesture-audit document: `f86601c164429ae1b7022b281c7303d9ed2da6b4129e0839e7e9b4427e12b377`.

Keep A at canonical n final-stem parameter0.7648068784772746 and C at canonical
u first-stem parameter0.25. Retain exactly the source coverage in the audit.
No global letter movement, advance/gap change, added lift or body redraw.

Keep physical W=0.45mm, thickness0.02mm, fixed physical-y-down40 degrees,
pressure0.5 and speed cap12mm/s. Preserve exact-decimal negative10% corner
contact and full/corner/full action semantics; no centered thin-line substitute.

Hard limits remain:

- Thin core: `0.25*(0.45*cos40° + 0.02*sin40°)` ≈0.089393938mm maximum,
  everywhere on the core, never a mean or cropped measurement.
- Radius≥0.1125mm; curvature≤8.888888889/mm on every adapted span.
- Aggregate path length on each existing A→B, B→D, D→C evaluation region
  ≤1.25 times that region's endpoint distance. Extra semantic pieces cannot
  reset this length allowance.
- Directed tangent error≤1e-8 and attachment position error≤1e-9mm.
- Existing baseline/x-height band, departure allowance, revised receiving
  allowance, and four radius0.45mm contact-splice disks remain unchanged.

Do not repurpose a contact-splice disk as a centerline envelope or blanket owner
overlap exemption. No additional contact permission at a new semantic joint.

## 3. Separate semantic ports from contact anchors

The semantic program is:

`n departure-turn → u entry-rise → u entry-crown → u descent-prefix → retained u`

A/B/D/C keep their current geometric, action and evaluation roles for this
investigation. New semantic ports P (departure-turn to entry-rise) and Q
(entry-rise to crown) are **requirements to characterize**, not points to select
by fitting. Inspect their necessary position/tangent domains without constructing
a new curve. Candidate coordinates are outside this package.

| Port | Necessary role and initial domain |
|---|---|
| A | Exact retained n exit and tangent; full contact |
| B | Existing baseline extremum and end of full→corner transition |
| P | After B and before Q on the ascending thin-core region; upward tangent |
| Q | After P and before D on that region; upward/right approach into crown |
| D | Existing x-height extremum and start of corner→full transition |
| C | Exact retained u receiving site/tangent; full contact restored |

Thus the semantic departure-turn can cross B and the crown can cross D without
moving either action boundary. The core B→D stays wholly thin, including any
parts semantically called departure or crown. P/Q cannot enlarge broad contact.
On B→D retain strictly increasing x/y in the open region and the existing box
[B.x,D.x]×[0,H]. If a reused port needs negative x travel there, report the
conflict rather than silently adding a new backward allowance.

Outside that core, retain the exact documented A/B and D/C envelopes and
allowances. A gesture spanning an extremum must be checked on both applicable
regions; its semantic ownership does not replace these bounds.

## 4. Finite read-only investigation inventory

Use only full `lower-return`, full `rise`, full `upper-return`, and the already
retained/replaced canonical stem intervals. Do not sweep arbitrary primitive
cut parameters. A newly proposed cut must become a separate reviewed choice.

### Pass A — exact-reuse necessary conditions

For each of the three full primitives, report source endpoint directions,
displacement, y-extrema and how its semantic role would straddle B or D.
Use exact polynomial roots or guarded conservative bounds; a sparse polyline
picture is not admission evidence.

Test only the existing placement family: translation, positive uniform scale
in[0.5,1.5] and rotation in[−20°,20°]. These are inherited placement bounds,
not a license to use every transform. No shear, anisotropic stretch, reflection,
free control handles or rotation of the physical nib.

Solve necessary directed-port constraints analytically where possible; report
intervals or a contradiction, not a numerically optimized best candidate.
Internal joins must share a directed tangent, while A/C are fixed. Distinguish
these tests from whether the complete displacement and envelope can also fit.
If an interval proof is unresolved, record it and stop that case.

### Pass B — adaptation requirements, not adapted curves

For requirements that exact reuse cannot satisfy, report:

- The conflicting source/required tangent or displacement and its cause.
- Whether the affected handle belongs to departure, rise, crown or descent.
- Whether endpoint-handle adaptation alone could address the port mismatch as
  a necessary condition, or whether a new source cut/envelope would be required.
- Which unchanged limits must still be proved; no inferred curvature pass from
  a tangent match and no inherited thin-contact admission from a full-edge gesture.

In particular, rise's current upward entry has a slightly negative x component,
while P lies in a strictly-rightward region. Investigate that conflict explicitly.
Do not claim the original rise can be used unchanged just because it points up.

This pass may produce a table of required adaptation types and unresolved bounds.
It must not choose handle lengths, generate control points, rank visual variants,
minimize a loss or progressively relax a bound. The result is a construction
specification input, not a hidden fitting run.

## 5. Stop rules and evidence contract

Stop on any changed input pin, invalid topology, ambiguous root classification,
budget exhaustion or need for an unapproved family extension. Preserve partial
evidence and distinguish `incompatible`, `unresolved` and `necessary_conditions_pass`.
Never emit `geometry_accepted` or `physical_accepted` from this investigation.

Evidence must include input hashes, primitive identities, tested family bounds,
port interval/sign certificates, unchanged source coverage, contact/semantic
mapping and a list of unsolved requirements. No candidate file or image output.

Adverse tests must cover altered pins, backwards/zero port directions, repeated
roots, unmatched tangent signs, reflected/sheared/out-of-range transforms,
relabeling T/R/S without primitive derivation, duplicate source coverage, broad
contact crossing into B→D and resetting length budgets at semantic joints.

## 6. Proposed execution budget and output

One nu-only read-only invocation,300 seconds total,10MiB new evidence maximum,
minimum5GiB free disk. One fixed inventory, zero automatic retries, zero random
seeds, no provider/GPU, no renderer/controller, no fitting or geometry generation.
This is a new proposed investigation budget, not a reset of any consumed run.

Proposed isolated script/test names: `scripts/nu_entry_port_audit.py` and
`tests/test_nu_entry_port_audit.py`; proposed output directory:
`shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/port-audit-001/`.
Do not modify frozen core or introduce a training spec. Existing gesture and
curriculum components and CURRICULUM-016 cover this work.

After reviewing that report, prepare **one deterministic derivation proposal**
with explicit primitive cuts, adaptation formulas, semantic ports and action
mapping, plus its own geometry budget. Only separate approval permits generating
and checking that candidate. Failure does not authorize a second construction.

Mu, other words, fatigue and unspecified fine-tuning remain deferred. No execution
has started in this proposal-preparation turn.
