# TD-018 — Tangent-compatible n→m attachment envelope

Date: 2026-09-10. Status: **requirement revision prepared at owner request;
implementation and saved-candidate remeasurement not started**.

Owner request: “Please revise the conflicting attachment/envelope requirement”.
This records the revised design, not permission to retry the exhausted attempt,
change geometry or accept the saved candidate under different criteria.

## 1. Decision and evidence boundary

Keep the existing attachment sites, exact canonical tangent directions and
both fixed construction cubics. Replace the blanket strictly-rightward rule
with a **local, tangent-following departure allowance** on T only. Preserve the
strictly-rightward transfer R and every other guardrail.

The canonical n stem has a slight leftward component at A. A smooth attachment
must initially follow it. Treating any negative horizontal component as a loop
was inconsistent with requiring that tangent. A brief sideways component while
descending is not a pen lift or a retraced stroke. This revision does not change
the accepted upright letter bodies or introduce general slant variation.

The [original proposal](TD-018-nm-construction-proposal.md), approval and stopped
attempt remain immutable. This document supersedes only section5's horizontal
extent/direction requirements for a future, separately recorded evaluation.
It is an explicit design-constraint change informed by the stopped result,
**not** a claim that the original requirements passed or a measurement-only bug
fix under unchanged thresholds. It does not prove visual usefulness.

| Frozen input | SHA-256 |
|---|---|
| Original proposal | `a2a47b91654d7a3d6d5347d67c61f46ae44e158c32523c0b32d2463adf7f932f` |
| Saved candidate file | `5b570b3df83e88dea38c4faf3b3c4badc121bf2055b0a0631efebf1b515b434c` |
| Original stopped report | `1f5cb5b87bb4aa6a264c09bc8a9bf0fccf6efacc24935f8b1327a3277d8f2a80` |

All canonical/attachment/clearance pins in the original approval remain binding.
The saved report remains unresolved at the extent/direction gate, with finite-nib
intersection admission not evaluated. Its saved controls establish the negative
initial x derivative; no new extrema, intersection or candidate evaluation is
claimed by this document.

## 2. Replacement requirement

Coordinates remain physical millimeters, x right and y up. Retain A, B, C, h,
the canonical unit departure tangent dA and full nib width W=0.45mm from the
original proposal. The existing departure handle length is a=0.9h/|dA.y|.

Define the permitted horizontal departure envelope from that fixed tangent:

**delta = max(0, −a·dA.x).**

For the saved construction this is the first handle's leftward displacement,
approximately0.003179mm. It is a conservative control-hull allowance, **not**
the curve's measured maximum excursion. Do not fit delta to a measured extremum.

The allowance also has an independent proposed scale cap: **delta <= W/100 =
0.0045mm**. Reject if the derived allowance exceeds this cap; do not clamp it,
rotate the tangent or enlarge the cap automatically. This cap is a prospective
locality guardrail, not a historical standard or a physical accuracy claim.

| Part | Revised whole-curve requirement |
|---|---|
| T envelope | x in [A.x−delta, B.x], y in [0,h] |
| T vertical progress | y'(t)<0 for 0<=t<1; y'(1)=0 at B |
| Initial horizontal departure | If dA.x<0, exactly one interior stationary x point t_min: x'<0 before it, x'=0 there, x'>0 after it through B |
| Locality | Every point of T with x<A.x lies inside the disk of radius W/4=0.1125mm centered on A |
| Recovery | Exactly one subsequent crossing of x=A.x before B; no later leftward excursion |
| R | x'(t)>0 throughout; y'(0)=0 and y'(t)>0 for 0<t<=1; centerline in [B.x,C.x]×[0,h] |
| Entire construction | Nonzero geometric derivative, sole baseline point B, no overshoot, cusp, self-intersection or path retracing |

The current pinned dA.x is negative. The nonnegative-departure case is not an
additional candidate: if a future independently admitted site has dA.x>=0,
delta=0 and the original strictly-rightward requirement applies without a new
departure allowance. This revision admits no new site or layout.

“No reversal” now means no reversal along the drawn path and no additional
horizontal sign changes beyond the single declared initial turn. It must not
be implemented as the contradictory blanket x'>0 test on T. Strict descent
keeps T injective despite its one horizontal minimum; R stays strictly rightward
of B. The narrow leftward allowance grants **no finite-nib overlap permission**.

## 3. Unchanged constraints

- Same A/C canonical parameters, body slices, fixed equations and twelve-piece
  representation. No new handles, alternate sites, spacing or baseline changes.
- Same position tolerance1e-9mm and directed-tangent tolerance1e-8; no zero-speed
  derivatives. Tangent continuity remains geometric, not physical timing proof.
- Same length ceiling1.25×hypot(C.x−A.x,2h) and radius floor0.1125mm.
- Same fixed nib0.45mm at physical-y-down40 degrees, pressure0.5 and12mm/s cap.
- Same ownership, contact and three splice permissions: retained-n/T at A,
  T/R at B, R/retained-m at C. Full intersection containment inside the respective
  radius0.45mm disk; certified separation everywhere else. No whole-owner waiver.
- Same active nm arrangement; n/m/nn/mm unchanged controls, um deferred, B1/B2
  unsupported. No default compiler activation, fitting or physical consumer.

## 4. Evaluation implementation work package

Use a new evaluation contract identity, `nm-tangent-envelope-evaluation-v2`,
while preserving the saved `nm-turn-rise-construction-v1` geometry bytes.
Record this document's exact hash, the three pins above, canonical source pins,
owner approval and checker/test identities separately. Do not overwrite the
v1 approval, report or attempt directory, or claim v1 acceptance retrospectively.

1. Implement the revised tests using analytic polynomial extrema/root isolation
   or conservative interval subdivision. The derivative x' is quadratic; isolate
   all roots, classify signs between roots, and account for numerical uncertainty.
   Check extrema of x/y and the whole x<A.x interval's squared distance from A.
   Sparse sampling and the control-hull sign test alone cannot certify the gate.
2. Keep fail/unresolved distinct. Record the original negative endpoint derivative
   as an analytic witness, delta/cap margin, enclosed extrema, stationary-point
   count, crossing count, locality margin and all other existing checks. Report
   the new criterion alongside the preserved old outcome, not as a corrected pass.
3. Test zero/extra/double stationary roots, excess excursion, late recovery,
   locality escape, cusp/retrace, mismatched tangents and uncertain boundaries.
   Also retain body/lineage/spacing/approval tamper tests and null controls.
4. Complete the still-missing finite-nib intersection admission before any image.
   Include flattening error and numerical guards in separation and full splice
   containment; adverse tests must reject overlap outside a splice disk even
   when total overlap area is small. Any unresolved result stops admission.
5. Once approved, load and hash-check the saved candidate directly for one bounded
   reinspection; do not construct, refit or select another candidate. Save new
   results separately under `nm-construction-v1/envelope-review-001/`.
6. Only if every revised geometry and finite-nib gate passes, finish the conditional
   nominal renderer/page and produce the original ten-image full-frame comparison.
   Four unchanged controls must have matching B0/B3 pixel hashes. Owner usefulness
   review remains required; passing geometry is not useful-style acceptance.

## 5. Execution and resource gate

This turn is documentation-only. Proposed follow-up approval would cover checker
implementation and one saved-candidate reinspection, not a new geometry attempt:
300s verification, conditional300s nominal generation, combined100MiB new output,
minimum5GiB free disk and zero automatic retries. The prior geometry attempt stays
consumed. The ten-image allowance is unspent but cannot bypass the revised
contract/approval binding. No old physical budget is reset or used.

Preserve failed/unresolved evidence and stop before rendering on any failed gate.
CURRICULUM-016 remains in progress; HANDVALIDATE-025/026 remain gated. No new
advances, components, commits or merges are required by this revision.
