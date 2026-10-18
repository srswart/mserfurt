# TD-018 — J1 receiving repair results

Status: **local repair passes all structural checks; ramp self-contact unresolved**.

The owner approved implementation of the
[bounded proposal](TD-018-j1-receiving-local-tail-proposal.md):
“Okay let's proceed with implementation.” One J1-R1 was constructed and saved
before checking. No refitting, alternate handles, retries, other candidate,
physical run, mu or nib rotation. No nominal image was admitted.

## Results

All **31 structural checks pass**, including the unchanged departure/core,
protected geometry, source coverage, aggregate length, thinness and attachments.
Only the receiving cubic list and its explicit revision metadata change.

| Receiving measurement | Certified bound | Unchanged limit |
| --- | --- | --- |
| Whole terminal-tail radius about C | 0.056250mm | 0.112500mm |
| Tail rightward control-hull extent | 0.000515mm | 0.004500mm |
| K→E curvature | 7.811856/mm | 8.888889/mm |
| E→C curvature | 1.955224/mm | 8.888889/mm |
| Whole K→E→C length | 0.892192mm | 1.007894mm |
| E positional / unit-tangent error | 0 / 0 | 1e-9mm / 1e-8 |
| C positional / unit-tangent error | 0 / 5.324e-15 | 1e-9mm / 1e-8 |

Values are rounded for display; the JSON contains full-precision bounds.
Exact-rational control hulls certify that the whole prefix stays at or left of
C and the whole tail stays inside the original locality disk. This resolves
the original receiving-locality defect for **this new candidate**, not for J1.
The original failed J1 and J2 remain unchanged.

All **27 external owner-pair checks (59 cubic pairs)** pass. Both receiving
cubics participate; there is no E splice permission. Ramp supersets use the
full finite nib, so this is not a centerline-only contact check.

However, **neither broad ramp has a complete self-contact certificate**:

- Departure: the sufficient monotonicity test cannot certify that the moving
  active-edge endpoint always progresses. The departure geometry is unchanged.
- Receiving: its nib-normal derivative projection changes sign, with range
  approximately `[-1.199299, 0.373812]` on the prefix. Thus this global
  monotonicity proof cannot certify the whole two-cubic footprint sweep.

These are **unresolved proof obligations, not demonstrated prohibited-contact
witnesses**. The checker stops conservatively. The thin core's separate
window-local self-contact certificate passes, but does not admit either ramp.

## Implementation and validation

- `scripts/nu_j1_receiving_repair.py` is a separate opt-in adapter; all
  historical construction, measurement and readiness code stays byte-identical.
- Receiving K→E→C retains one owner/source interval and one arc-length contact
  profile. Length, contact, nominal drawing and lineage consume both cubics.
- The whole-ramp sufficient certificate requires continuous footprint-boundary
  monotonicity with a common sign across cubics and uses total ramp arc length
  for its active-edge rate. It covers cross-cubic pairs only when proven; it
  does not concatenate independently admitted self-contact results.
- A new authority record freezes the proposal and current dependencies. The
  historical receipt is verified as historical evidence, not rewritten into
  current clearance. Only the prior isolated diagnostic and new adapter/tests
  are allowed additions. A fresh isolated current-runtime check and exact
  context-off n/u/nu fingerprints match the historical canonical outputs.
- **23 new tests pass; 233 tests across `tests/test_nu*.py` pass.** Regression
  coverage includes both receiving cubics, protected-state mutation, action
  domain resets, shared length, cross-cubic return, contact pair coverage,
  curvature/cusp failure, context-off, save-before-check and no retry/render.
- Construction/readiness/checking: **2.216139 seconds**. Text-only finalization:
  **0.330103 seconds**. The output directory is **115,671 bytes** before any
  later external archive metadata; zero new SVG/PNG files. Both 300-second
  phase budgets and the 25MiB ceiling are respected.

## Evidence and next gate

Evidence base:
`shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/`.

- [Approval and new source snapshot](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/j1-receiving-repair-approval.json).
- [Saved candidate, readiness and full checks](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/j1-receiving-repair-001/report.json).
- [Text-only status board](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/j1-receiving-repair-001/index.html).

Candidate object SHA-256:
`616526b0952f02264d772508bce4342c325cc21a4648e49abd50efdaf01845f5`.
Report SHA-256:
`03979c687c1fb027b383e07d0b9c176b8c7e782b08f9df351905dba43f0deda6`.

**Recommended next: propose bounded measurement-only self-contact diagnosis
of the saved departure and receiving ramps.** Distinguish an actual prohibited
contact witness from failure of the sufficient global monotonicity proof.
Keep geometry, active-edge action, limits and overlap policy unchanged; inspect
the whole receiving aggregate including cross-E pairs. If stronger measurement
cannot classify contact under the existing policy, report unresolved rather
than silently broaden ordinary-overlap permissions.

No follow-up diagnostic or new geometry is authorized by this results note.
The one-candidate allowance is exhausted. CURRICULUM-016 remains in progress;
owner visual review, HANDVALIDATE-025/026 and physical/fitting work remain gated.
