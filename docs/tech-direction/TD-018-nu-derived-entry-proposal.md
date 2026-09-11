# TD-018 — One deterministic derived entry for nu

Status: **construction proposal prepared; geometry execution awaits approval**.

## 1. Decision and evidence

The [port audit](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/port-audit-001/README.md)
rules out full lower-return/rise/upper-return reuse by similarity placement at
the fixed anchors. In particular, the lower-return would miss B horizontally
by0.730208mm. Its failure does not require changing thinness or curvature limits.

Propose a new, explicitly **derived-handle** construction family, not another
attempt within the rejected exact-reuse family. Reuse the accepted T and S
curves exactly; replace only the thin B→D curve by a three-cubic entry program.
This avoids forcing the full canonical lower-return into the narrow A→B region.
It also avoids forcing an unchanged upper-return to meet C directly.

The semantic departure is T plus a derived upward recovery. The semantic crown
is a derived approach to D plus existing S. Thus the new internal primitive
ports change the geometry within the thin span rather than merely renaming R.
Whether that change looks more natural remains a separate owner decision.

Frozen inputs:

- Port report SHA-256 `8bf7cf5810a7e215a70086d2af1f5de1ad366af155ed6c09a37d3a3ac46fda99`.
- Nu candidate SHA-256 `7268952cd29fc7737c726838107e25f6bf0deeb4537992a8b415713150b0db97`.
- Canonical model file SHA-256 `01f892299fff5b069f1559c3ae7c22bfc1a185a40633a424b670b3a6cfbdd8cd`.
- Revised-envelope pass SHA-256 `053aff33d2b767c622ea63614fd4727a394c1c6bce365740d007915c7e163b8f`.

No control points, root solves or new curve checks were executed to prepare
this document. Formulas below are proposed choices, not discovered optima.

## 2. Fixed anchors and semantic ports

Use physical mm, y upward, H=3.5mm. Load exact A/B/D/C, T/R/S and canonical
source cuts from the frozen candidate. T and S, all retained curves and actions,
letter placement and source cuts remain byte-identical.

Let theta be the audited rotation mapping canonical lower-return entry to dA:
approximately−2.353981470 degrees, computed from the same pinned unit vectors.
Use the existing shared rise entry/exit vectors rotated by theta as proposed
directed semantic tangents p and q. Their expected endpoint directions are
upward/right, approximately89.767115° and41.452529°. Reject if their x or y
components are nonpositive; do not clamp or substitute a direction.

Define P/Q heights from canonical vocabulary, not tunable fractions:

- P.y = H times canonical lower-return's final local y coordinate.
- Q.y = H times canonical rise's final local y coordinate.

Locate P and Q on the **old frozen R** at those heights by unique certified
roots of R.y(t)−height. Require0<tP<tQ<1 and B.x<P.x<Q.x<D.x.
These locations are a fixed placement scaffold; the old R interior is not
the new geometry. Do not choose alternate roots or adjust heights on failure.

This keeps existing placement as the control while giving the entry explicit
upward ports inherited from rise. It is a bounded first hypothesis, not a claim
that these are the only or stylistically ideal semantic-port locations.

## 3. Primitive-derived handle rule

Use these source curves only, in local coordinates, with an explicit theta
rotation for finding extrema and directions:

| New thin segment | Source for dimensionless handle proportions | Required endpoint tangents |
|---|---|---|
| recovery B→P | Canonical lower-return suffix from its unique rotated y-minimum to its end | rightward, p |
| entry-rise P→Q | Full canonical rise | p, q |
| crown-approach Q→D | Canonical upper-return prefix from its start to its unique rotated y-maximum | q, rightward |

The audit pins the lower-return minimum near0.673945264800. Recompute and
certify it from the pinned primitive during the approved construction. Solve
the rotated upper-return maximum analytically then; no arbitrary cut sweep.
Reject multiple, boundary-ambiguous or wrong-sign extrema. These two
**extremum-defined subspans are new proposed cuts**, not cuts authorized by the
earlier full-primitive audit. Record exact source root brackets and de Casteljau
provenance. No numerical minimization or fitting is permitted.

For each source cubic subspan K with controls K0..K3, define:

`rho_in = distance(K1,K0) / distance(K3,K0)`

`rho_out = distance(K3,K2) / distance(K3,K0)`

For its new endpoints U,V and prescribed unit tangents u,v, let L=distance(U,V).
The single derived cubic is:

`[ U, U + L*rho_in*u, V - L*rho_out*v, V ]`

Reject zero/nonfinite chords or ratios. Do not cap ratios, adjust handles,
choose alternate cuts or rerun with different fractions if a check fails.
Tangent magnitudes need not match parameter speeds; no motion timing is inferred.

This preserves a source gesture's dimensionless handle proportions and directed
entry/crown pattern, but **does not preserve its exact shape or similarity scale**.
The earlier[0.5,1.5] similarity-scale bounds cannot describe this new family;
there is no new adjustable scale variable. This family change requires explicit
approval. All spatial, thinness and curvature limits below remain unchanged.

## 4. Geometry, ownership and contact representation

Store eight exact retained occurrences, unchanged T, three new thin cubics, and
unchanged S: thirteen cubics total for nu. Do not call the original constructor
or alter the canonical model. Use a separately versioned candidate manifest.

Preserve the audit's exact retained/replaced source-interval coverage. Added
entry-rise geometry is owned by contextual u with n as predecessor contributor;
it is not a fabricated canonical u interval. Record each new segment's shared
primitive hash, extremum cut if any, ratios, semantic ports and contributor map.
Mark the new curves derived, never exact primitive reuse.

Semantic mapping:

- n departure-turn = T plus B→P recovery, with u-entry compatibility contributor.
- u entry-rise = P→Q, with n predecessor contributor.
- u entry-crown/descent = Q→D plus S; restore the retained u body at C.

Contact/evaluation mapping remains independent:

- A→B: old T, unchanged full→negative10% corner ramp.
- B→D: all three new cubics, constant negative10% corner contact.
- D→C: old S, unchanged corner→full ramp.

P/Q are numerical/semantic joins inside one thin run. No extra splice disks,
new overlap permissions, action resets or pen lifts. For pairwise contact checks,
the three cubics are one aggregate R region, not three independent owners.
The aggregate's self-contact must be checked for nonlocal overlap; adjacency
at a shared endpoint does not authorize remote self-overlap.

## 5. Mandatory gates before any rendering

1. Verify all frozen pins and exact retained/T/S/source/action identities.
2. Certify unique P/Q and source-extremum roots with correct order and signs.
   Establish nonzero derivatives and directed-tangent error≤1e-8 at B/P/Q/D;
   retain attachment position tolerance1e-9mm at A/C.
3. Entire new aggregate R remains inside[B.x,D.x]×[0,H], strictly rightward
   and strictly ascending on its open span, with horizontal endpoint tangents
   only at B/D. Reject loops, retrace, cusps or ambiguous classification.
4. Curvature≤8.888888889/mm, radius≥0.1125mm on every cubic. No special
   exception at P/Q or any control-handle junction.
5. Sum the certified lengths of all three thin cubics: require
   `sum(lengths) <= 1.25*distance(B,D)`. Do not reset allowance per semantic
   piece. Existing T/S length limits and envelopes also remain unchanged.
6. Entire B→D stays below the existing exact thinness limit
   `0.25*(0.45*cos40° + 0.02*sin40°)` ≈0.089393938mm. Preserve the finite
   0.45×0.02mm tool, orientation40° y-down, pressure0.5 and speed cap12mm/s.
7. Recheck finite contact against retained bodies, T/S and nonlocal parts of R,
   using only existing A/B/D/C splice permissions. Geometry success does not
   inherit contact success from the frozen candidate.

The original departure and revised receiving allowances remain unchanged,
including their0.0045mm caps and0.1125mm locality radii. No silent enlargement
of body exceptions, top/foot shift, broad transition coverage or spacing.

## 6. Tests, execution budget and review

Implement new opt-in script/tests only; leave pinned checkers and training core
unchanged. Test frozen mutation, incorrect primitive/cut lineage, root ambiguity,
backward/zero tangents, fake T/R/S relabeling, per-piece length-budget evasion,
contact resets at P/Q, thinness/curvature relaxation and unauthorized retries.
Assertions must compare the generated formulas/provenance, not just role names.

Proposed execution: **one nu candidate, one300s construction-and-check invocation,
10MiB output maximum, minimum5GiB free disk, zero retries**, no provider/GPU,
fitting, images or physical execution. Preserve a candidate once generated even
if it fails; save the first failure or unresolved result and stop. Never reset
the prior audit or geometry budgets.

Proposed outputs under
`shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-contextual-entry-v1/derived-entry-001/`:
approval bindings, one candidate, provenance and check report. Use evaluation
identity `nu-derived-entry-geometry-v1`. Existing components/CURRICULUM-016 cover
this work; no new advance or core schema migration is required to propose it.

Only after a complete geometry/contact pass should a separately approved nominal
comparison show canonical unconnected nu, old bridge and new derived entry at
identical scale, with semantic/contact annotations. Owner review should decide
whether the rise genuinely participates in forming u. A numerical pass alone
cannot establish naturalness. No automatic mu, fitting or physical follow-on.

This proposal is ready for review, not evidence that the construction will pass.
