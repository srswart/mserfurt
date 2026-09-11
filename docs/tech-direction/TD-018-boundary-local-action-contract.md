# TD-018 — Boundary-local action contract and exact edge handling

Status: **implemented and checked in a new opt-in contract; geometry gated**.
Owner request: “Let's address that contract and numeric handlin”. This work
addresses contract isolation and numeric semantics only. It does not activate
the proposed nu/mu curves, change corner choice or grant nominal/physical runs.

## 1. Preserve the old contract; add a separate one

`nu-boundary-actions-v1` lives in `scripts/nu_boundary_actions.py`, outside frozen
core identity scans. It does not mutate connected-v1, bypass its six-occurrence
limit or modify the shared `fixed` action. The canonical candidate remains
`96aced30b45e5ef09eb219643c4eb068a332fcdab3a3ae466ee5fe5aa7993ca3`.

The geometry-free nu/mu manifests record:

- Exact canonical compilation identity, owner metadata, geometry hashes and
  original action definitions for every retained occurrence.
- Declared source subintervals at the higher departure site and receiver t=0.25,
  as contract metadata only. No replacement curves or new subcurves are built.
- Three boundary slots T/R/S with separate action-profile references, contributor
  identities, source-removal lineage and explicit pen-down state.
- A proposed shared contact-run reference that does not erase canonical owners.
- Full contact on retained pieces; shrinking on T, negative-corner hold on R,
  restoration on S. A/B/D/C joins explicitly declare matching contact states;
  geometric continuity remains unevaluated until geometry exists.
- A13-piece cap, nu/mu exposed scope, and false geometry/nominal/physical approval
  flags. um/num and automatic opposite-corner substitution remain unsupported.

Validation rebuilds the expected *contract metadata* from pinned canonical inputs
and rejects altered bodies/actions, missing contributors, extra geometry, moved
source scope, duplicate pieces, changed contact state or forged execution flags.
The exposed text is fixture admission, not a fitted full-word construction rule;
selection records canonical port roles, policy and frozen relative layout.

There is intentionally no geometry, renderer or controller consumer in this
module. Its consumer gate raises rather than converting these manifests to a
legacy plan. Future consumers must validate the manifest and receive separate
geometry/execution approval, not merely accept a version label.

## 2. Exact10% semantics, without widening

The new contact type is `boundary-contact-decimal-v1`, separate from the legacy
`physical-edge-v1` object. Authority for edge endpoints and track progress is
bounded decimal strings in the JSON contract, converted to exact rational values.
Binary floats, booleans, NaN/infinity, exponent strings and out-of-domain values
are rejected as authoritative edge input. Fractions are retained internally.

Validate `0 <= start < end <= 1` and `end−start >= 1/10` exactly:

| Input | New behavior |
|---|---|
| ["0", "0.1"] | Accept exact negative10% corner |
| ["0.9", "1"] | Accept exact positive10% corner |
| ["0", "0.09999999999999999"] | Reject genuinely subminimum interval |
| ["0.90000000000000001", "1"] | Reject genuinely subminimum interval |
| Binary float endpoints | Reject; no automatic rounding/stringification repair |

Tracks contain two to four strictly ordered knots spanning exactly[0,1]. Linear
interpolation uses exact rational arithmetic, including exact endpoint returns.
Each segment's bounds and minimum width are preserved throughout by convexity
of its valid endpoint intervals, not by testing a few progress samples.

Float conversion occurs only after validation, when projecting the finite
rectangle into geometric coordinates. There is no epsilon-based admission,
clamping, wider contact or changed tool width. The new type preserves the fixed
0.45mm edge,0.02mm thickness and40-degree y-down orientation. Y/angle reflection
preserves directed interval labels and reflected contact corners.

Full and negative-corner coordinates agree with supported legacy contact geometry
within1e-12mm. Positive contact now works in this separate type. **The legacy
validator's positive-corner rejection is unchanged**, deliberately preserving old
source identities and replay behavior. This is a versioned correction, not a
claim that the old API or all physical consumers have been repaired.

## 3. Evidence and tests

[Saved manifests and report](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-corner-contact-v1/boundary-action-001/README.md)
record a10.874s contract snapshot with unchanged canonical inputs. Both corner
types and full contact pass reflection checks; nu retains eight source pieces,
mu ten. No path or image was generated.

163 regression tests pass;48 exact-null cases are deselected. Tests cover:
exact10% symmetry, just-below-limit rejection, invalid numeric forms, interpolation
endpoints, malformed tracks, frame reflection, supported legacy coordinate
equivalence, preserved legacy rejection, exact retained actions, contact/profile
isolation, contributor/source/body mutations and execution gates. Frozen-source
verification passes separately; no new physical replay or exact-null planning
is claimed by this contract snapshot.

## 4. Next approval

The contract/numeric blockers are addressed for the new isolated route. Next
is explicit approval to implement and check the fixed nu/mu geometry family in
the [corner-contact proposal](TD-018-nu-corner-contact-proposal.md), binding this
contract report and proposal hashes. That stage must still verify all declared
body exceptions, tangents, curvature, length, thin-core contact ramps and full
finite-contact overlap. Contract validity does not prove any of those properties.

No automatic retry, nib-corner change, geometry approval, rendering allowance,
physical validation or fitting is inferred here. CURRICULUM-016 remains in
progress; HANDVALIDATE-025/026 remain gated. Changes remain uncommitted.
