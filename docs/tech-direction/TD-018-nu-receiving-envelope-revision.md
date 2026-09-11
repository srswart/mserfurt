# TD-018 — Canonical-tangent-compatible receiving envelope

Status: **requirement revision prepared at owner request; checker/reinspection not started**.

The owner requested a receiving envelope that respects the canonical tangent,
without changing thinness or curvature limits. Keep the saved nu geometry and
all attachment sites, body exceptions and contact profiles unchanged. Revise
only the receiving piece S's horizontal envelope and direction requirement.

## 1. Frozen evidence and meaning of the change

| Frozen input | SHA-256 |
|---|---|
| Original corner-contact proposal | `7f8aff72c7769e5c28eb8eaec4ec3d41251d97320a6ac997c5fdaf6c7a74821c` |
| Saved nu candidate | `7268952cd29fc7737c726838107e25f6bf0deeb4537992a8b415713150b0db97` |
| Original rejected report | `773ecfc7684284cf01354a18aed4a54a40354c8150c8a6c34ba91b883de27eaa` |
| Boundary-action contract report | `f02c6105d8990616d7c74cb53ebc00030025728c6f1d90d809a65e0e649f1c14` |

The [original proposal](TD-018-nu-corner-contact-proposal.md) required S to be
strictly rightward while matching u's canonical tangent at t=0.25. The preserved
candidate has an endpoint x derivative of−0.011663354102562806mm per unit
parameter, so the two requirements conflict. The saved rejection remains valid
under that original rule and must not be overwritten or relabeled as a pass.

This is an explicit design-criterion revision, not a measurement-only correction
under unchanged criteria. It is the receiving-side counterpart of the already
bounded departure allowance, not a general permission for backward connections.

## 2. Replacement receiving requirement

Use the same physical-mm/y-up coordinates and original D, C, H=3.5mm,
W=0.45mm and exact canonical directed receiving tangent dC. The fixed receiving
handle length remains c=0.75(H−C.y)/|dC.y|. Do not move a control point.

Define **delta_C = max(0, −c·dC.x)**, the rightward projection of the existing
penultimate handle C−c·dC beyond C. Require **delta_C <= W/100=0.0045mm**.
Reject if this derived allowance exceeds the cap; do not clamp the handle or
increase the cap automatically.

For the saved candidate, the endpoint derivative implies a handle projection
of approximately0.003887785mm. This is a conservative handle-based allowance,
**not** the curve's measured maximum excursion or a fitted threshold. No new
curve-extremum or contact evaluation was performed to prepare this revision.

Replace only the original S horizontal rule with:

| Requirement | Revised whole-curve condition |
|---|---|
| Envelope | S lies in [D.x, C.x+delta_C]×[C.y,H] |
| Vertical progress | S descends strictly for 0<t<=1; y'(0)=0 at D |
| Horizontal progress | Exactly one interior horizontal maximum t_max; x'>0 before it, x'=0 there, x'<0 after it through C |
| Crossing | Exactly one interior crossing of x=C.x, before t_max; thereafter S approaches C from the right and ends exactly at C |
| Locality | Every S point with x>C.x lies inside the disk of radius W/4=0.1125mm centered on C |
| Attachment | Exact canonical C and directed dC preserved; no zero geometric derivative |
| No extra detours | No additional horizontal stationary points/crossings, loop, path retrace or nonlocal crossing |

The final endpoint x=C.x is not counted as a second *interior* crossing.
The single permitted horizontal sign change is not a reversal along the drawn
path: strict descent maintains forward geometric progression into u. A cusp or
retraced path still fails. The current candidate's dC.x is negative; this does
not admit other sites or generalize a receiving allowance to unrelated letters.

T retains its existing bounded departure rule. R remains strictly rightward;
there is no horizontal allowance in the thin core. All contact and nonlocal
intersection conditions remain separate gates: the locality disk is a
centerline constraint, **not** a new contact-overlap permission.

## 3. Explicitly unchanged limits

- **Thinness:** all of R stays at the selected negative10% corner. Whole-core
  maximum transverse width limit remains exactly
  `0.25 × (0.45 cos40° + 0.02 sin40°)` ≈0.089393938mm. No change to the
 0.049244289mm theoretical rectangular support bound or full-core measurement.
- **Curvature:** radius>=0.1125mm, equivalently curvature<=8.888888889/mm,
  everywhere on T/R/S. No special curvature exception near C.
- Each piece's arc-length upper bound remains <=1.25 times its endpoint distance.
  Broad transitions stay confined to T/S; no enlarged transition or mean-width test.
- Positions within1e-9mm numerical accounting; unit tangent error<=1e-8. Same
  baseline/x-height band, foot shift, receiving-top exception and all undeclared
  body/spacing/source/action identities exact.
- Same finite0.45×0.02mm contact rectangle, physical-y-down40 degrees, pressure0.5,
  speed cap12mm/s, negative-corner choice, exact decimal interval handling and
  full/corner/full ramps. Full contact restored at C.
- Same four named contact splice permissions, each confined to its radius0.45mm
  disk; certified separation elsewhere. No whole-owner exemption or inherited
  um permission. Continuous ramp envelopes and corner offsets remain required.

No fitting, site change, global slant correction, pen lift, body redraw or
pressure adjustment is authorized by this requirement change.

## 4. Checker and reinspection work package

Proposed new evaluation identity: `nu-receiving-envelope-evaluation-v2`. Preserve
the saved `nu-coupled-corner-geometry-v1` candidate bytes and prior contract.
Record this revision's hash and the frozen input pins in a separate approval;
do not repin or edit the original proposal, rejected report or checker.

1. Implement analytic root isolation or conservative whole-curve bounds for S's
   quadratic x' and its x−C.x crossings, including exact endpoint accounting.
   Record enclosed root intervals, root order, signs, guarded maximum x and
   delta_C/cap margin. Do not rely on the signs of control-polygon edges alone.
2. Certify the entire x>C.x interval's distance from C, including the crossing
   neighborhood and endpoint. Unresolved boundary classification stops admission.
   Record the original negative endpoint derivative alongside the new criterion.
3. Add adverse tests for extra/double roots, late or missing crossing, excessive
   overshoot, locality escape, cusp/retrace, forged tangents and mutation of
   thinness/curvature limits. Assert frozen geometry/body/contact identities.
4. After approval, load the saved nu candidate directly for one no-refit
   reinspection. Do not call the constructor or generate a replacement. Recheck
   all unchanged gates and, only if structural gates pass, evaluate the previously
   unrun full finite-contact sweep/splice gates. Preserve failures and stop.
5. Save new evidence separately under
   `nu-corner-contact-v1/receiving-envelope-review-001/`. Report success only under
   this revised criterion, never as a retroactive original pass.

Prospective next execution scope: checker implementation and one saved-nu
reinspection,300s verification,10MiB new output, minimum free5GiB, zero automatic
retries, no images, physical runs or fitting. This is a fresh bounded review
proposal, not a reset of the consumed geometry attempt. **No reinspection starts
in this documentation turn.**

Mu remains unstarted. If nu passes all revised structural and contact gates,
review that evidence before authorizing mu's pending geometry under the same
receiving policy. The nominal packet remains separately gated. CURRICULUM-016
stays in progress; HANDVALIDATE-025/026 remain gated; um/num remain excluded.
