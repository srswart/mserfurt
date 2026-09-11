# TD-018 — Reusable gesture audit for contextual u entry

Status: **read-only audit complete; proposed construction contract, no new geometry**.

## 1. Sources and scope

Inspected the current frozen upright model, canonical nu expansion, boundary
action manifest and saved T/R/S candidate. Computed only existing endpoint
displacements and directed unit tangents; no candidate construction, fitting,
rendering, physical execution or new geometric admission test.

- Canonical model: `shared/training/konrad_hand_recovery/stroke_gestures_v2/letters/upright/run-001/candidate.json`
  SHA-256 `01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd`.
- Saved nu SHA-256 `7268952cd29fc7737c726838107e25f6bf0deeb4537992a8b415713150b0db97`.
- [Receiving-envelope review](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/receiving-envelope-review-001/README.md)
  remains valid for that candidate only; all its pinned inputs were verified.
- Compiler: `scribesim/evofit/stroke_gestures.py`, especially `_lower` and
  `validate_gestures`. Current gestures are flat primitive sequences; context
  overlays are rejected, and action ownership is per gesture. The new semantic
  contract is not already executable through this API.

Coordinates below are physical mm, y upward; tangents are directed unit vectors.
Numbers are rounded descriptions of frozen values, not new tolerances.

## 2. What is actually reusable

| Existing vocabulary | Existing purpose | Reuse decision |
|---|---|---|
| `lower-return` | Turns a descending stem into an upward rise within `underturn` | Reuse the descent→bottom turn→upward-exit construction pattern for n's departure; not its entire placed curve without compatibility checks |
| `rise` | Near-upright rising stroke used in `overturn` and `underturn` | Primary entry-rise vocabulary: explicit upward entry and upward/right exit into a crown |
| `upper-return` | Continues that rise through a top turn into a descending stem | Primary entry-turn vocabulary; already direction-matched to `rise` |
| `overturn` | `rise → upper-return → stem` | Best reusable semantic template for contextual u entry; use a declared descent prefix, not a second complete stem over u |
| `underturn` | `stem → lower-return → rise` | Preserve u's existing body; use its departure-turn pattern as evidence, not a wholesale replacement of u |
| `stem` | Canonical descending stroke | Retain the existing u continuation and n body; do not redraw them globally |

These are existing canonical building blocks, not newly proven thin-contact
gestures. Their current `fixed` action is full-edge contact. Geometric vocabulary
reuse does **not** transfer physical or partial-contact acceptance. The model's
primitive provenance also explicitly disclaims historical/physical admission.

### Directed ports and scale mismatch

| Primitive at unit gesture scale, x-height3.5mm | Displacement (dx,dy) mm | Entry tangent | Exit tangent |
|---|---|---|---|
| lower-return | (1.378902,−0.459634) | (0.037012,−0.999315) | (−0.037012,0.999315) |
| rise | (0.280000,3.143661) | (−0.037012,0.999315) | (0.721682,0.692225) |
| upper-return | (1.402557,−0.467519) | (0.721682,0.692225) | (0.066519,−0.997785) |

The lower-return exit matches the rise entry; the rise exit matches the
upper-return entry. This supplies an existing **bottom turn→rise→crown** grammar.
The top turn is not an arbitrary horizontal endpoint: it begins while the pen
is still traveling upward/right and ends directed downward into the stem.

But canonical lower-return entry does not equal saved n's attachment tangent
(−0.004065,−0.999992); upper-return exit does not equal saved u's receiving
tangent (−0.009523,−0.999955). Therefore simple translation of these primitives
cannot join the current sites exactly. Their width/height envelopes also differ.
This audit does not test whether a permitted transformed/subspan construction
can satisfy every constraint; that remains a bounded feasibility question.

## 3. Why the existing bridge cannot just be relabeled

| Saved piece | Displacement mm | Directed ports | What is missing for vocabulary reuse |
|---|---|---|---|
| T | (0.240297,−0.868992) | n tangent→horizontal right | It stops at the bottom before developing the upward exit of a lower-return |
| R | (2.957243,3.500000) | horizontal right→horizontal right | It includes both departure recovery and arrival flattening; not the existing rise's upward-entry/upward-right-exit contract |
| S | (0.225000,−0.544290) | horizontal right→u tangent | It starts at the apex after the rising crown approach; not the whole `upper-return` gesture |

The current construction already provides pen-down continuity, a thin core,
declared source replacement and compatible end attachments. Keep those useful
contracts. What it lacks is a derivation from a receiving entry gesture whose
internal ports determine the rise/crown construction.

The proposed semantic boundaries need not coincide with old B and D. A departure
turn may include the beginning of old R; a receiving crown may include its end.
This is not permission to enlarge broad contact spans: the current thin-core
coverage stays required unless an explicit reviewed contract changes it.
Semantic partition and contact-profile partition are separate axes.

## 4. Proposed program and exact source coverage

Working semantic family: **`contextual-u-entry-v1`**, not a released schema.

`n retained body → n departure-turn → u entry-rise → u entry-crown → u descent-prefix → u retained body`

- Departure-turn derives from the lower-return pattern, constrained by n's
  actual outgoing tangent. It owns the change to n's terminal stem.
- Entry-rise derives from `rise`, owned by u with n as contributing predecessor.
- Entry-crown derives from `upper-return`, with a compatible upward incoming
  port and downward outgoing port. It is not simply an endpoint cap.
- Descent-prefix joins the retained u first stem without a duplicated stem.
  A prefix may be zero-length only if the crown itself reaches the receiving
  site with the required tangent; such a topology must be explicitly proposed.

Keep current source cuts as the initial feasibility boundary, not newly approved
coordinates. Canonical occurrence IDs are those of compiled nu:

| Source occurrence | Retained interval | Replaced interval / responsibility |
|---|---|---|
| n0: `0:0`, `0:1`, `0:2` | [0,1] each | None |
| n final stem `0:3` | [0,0.7648068784772746] | [0.7648068784772746,1], departure-turn |
| u first stem `1:0` | [0.25,1] | [0,0.25], entry-crown/descent-prefix replacement program |
| u lower-return `1:1`, rise `1:2`, final stem `1:3` | [0,1] each | None |

Entry-rise is contextual added geometry, not a fictitious source interval from
standalone u. Its lineage references the shared `rise` primitive separately
from the canonical u occurrence being edited. Crown derivation likewise records
the shared upper-return reference separately from replaced-source coverage.
Shared cut endpoints are geometric joins, not double traversal. Replaced spans
are consumed once by the program, not once per generated piece.

Each semantic span needs: receiving/departing owner, contributors, primitive
reference and hash, source subinterval if used, allowed transformation or
adaptation rule, directed ports, generated-piece mapping and contact mapping.
An adapted curve must be labeled derived, not byte-identical primitive reuse.

### Contact and execution boundaries

Keep full contact on retained bodies; preserve exact-decimal negative10% corner
contact through the thin core and full/corner/full boundary behavior. A semantic
gesture boundary cannot reset the action track or create a hidden pen lift.
Existing boundary-local action lineage is useful, but its T/R/S manifest cannot
be silently relabeled: a new version must map contact phases to semantic spans.

Keep thinness≤0.089393938mm using the unchanged exact formula, radius≥0.1125mm,
per-piece length≤1.25 endpoint distance under the existing evaluation partition,
and current site/envelope/overlap permissions. Do not split pieces merely to
evade a length limit. No automatic whole-owner overlap exception, pressure or
orientation change. Any new port, phase partition or envelope needs explicit
review before candidate construction.

## 5. Required tests and decision gates

1. Context off reproduces canonical model/compiled/action identities exactly;
   standalone u and all undeclared bodies/spacing remain unchanged.
2. Source coverage partitions the declared stem intervals once, with no omitted
   or duplicated canonical span, fabricated primitive provenance or hidden lift.
3. Primitive-derived ports agree at departure/rise/crown/descent joins; original
   canonical attachment position/tangent tolerances remain unchanged.
4. A manifest that only relabels saved T/R/S fails the claimed primitive-derived
   port/provenance contract. Test actual geometry and derivation, not name strings.
5. Contact continuity survives semantic boundaries; thin-core coverage and all
   limits are checked over the whole applicable interval, not averaged widths.
6. After separate construction approval, evaluate full-frame curvature, length,
   envelope and finite-contact gates before nominal visual review. A geometry
   pass cannot prove the owner's intended naturalness.

## 6. Recommendation and unresolved choices

Use **the overturn grammar for u's contextual entry, preceded by a lower-return
derived departure**, rather than another arbitrary bridge. Preserve the old
candidate as the control. Do not transplant an entire overturn at unit scale:
its ports, body descent and full-edge action do not match this context unchanged.

Next prepare a bounded port/envelope feasibility proposal: which primitive
subspans are reused exactly, which adaptations are necessary, whether the current
A/C cuts can stay, and where the semantic joints fall relative to fixed contact
phases. Specify one deterministic construction rule and evidence budget before
generating coordinates. If no solution satisfies the existing constraints,
report that conflict rather than stretching primitives or relaxing limits.

No specific new control points, new sampling/fitting budget, physical allowance,
or mu authorization follows from this audit. Fine-tuning, mu and other letters
remain deferred; CURRICULUM-016 remains in progress.
