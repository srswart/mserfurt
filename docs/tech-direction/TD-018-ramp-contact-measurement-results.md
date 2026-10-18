# TD-018 — Saved ramp contact measurement results

Status: **measurement complete; admission remains unresolved**.

The [authorized diagnostic](TD-018-ramp-contact-measurement.md) measured the
saved J1-R1 without reconstruction, refitting, changed limits or changed
overlap policy. Historical structural/external results are reused as pinned
evidence, not represented as newly executed checks. No image was generated.

## Full-domain overlap bounds

| Measurement | Departure A→F | Receiving K→E→C |
| --- | --- | --- |
| Saved cubics / fixed cells | 1 / 64 | 2 / 128 |
| Unordered cell pairs covered, including diagonal | 2,080 | 8,256 |
| Pairs certified separated | 1,664 | 6,300 |
| Pairs not excluded by finite-footprint bounds | 416 | 1,956 |
| Possible overlap arc-separation upper bound | 0.182896mm | 0.128269mm |
| Cross-cubic possible pairs | Not applicable | 33 |
| Cross-E overlap arc-separation upper bound | Not applicable | 0.050579mm |

Display bounds are rounded upward. These are derived coverage bounds, **not
new tolerances or proof that every remaining pair overlaps**. All possible
overlap beyond the respective bound is excluded by conservative finite-nib
footprint enclosures. Each receiving cell uses the same whole-ramp arc-length
action; no reset or contact exemption is added at E.

The worst unexcluded departure pair occupies original cubic parameters
`[1/2, 33/64]` and `[51/64, 13/16]`. The receiving worst pair is wholly on
K→E, at `[1/4, 17/64]` and `[29/64, 15/32]`; the short terminal tail is not
the location of that worst bound.

## Actual departure revisit, not just a loose bound

The diagnostic certifies one paper point inside the actual departure footprint
at two ordered parameters and outside it at an intermediate parameter:

| Event | A→F cubic parameter |
| --- | --- |
| Guaranteed inside | `33/64` = 0.515625 |
| Guaranteed outside | `39/64` = 0.609375 |
| Guaranteed inside again | `25/32` = 0.781250 |

The paper point is approximately `(0.982264174, 0.169900564)`mm in the physical
y-up frame. Use the exact nib-axis coordinates and rectangles in the report,
not these rounded display coordinates, to reproduce the certificate.

An independent exact-rational containment audit of the saved witness confirms
positive inside margins at both endpoints (edge 0.001600637mm, normal
0.000261525mm), while the intermediate point is outside the enclosing normal
slab by 0.001633821mm. The certificate includes the full varying active edge,
finite nib thickness, aggregate arc-length uncertainty and accounting guard.
This is a real **disconnected paper-point membership** witness. It rules out
proving uninterrupted membership for every paper point on the saved departure.

It does **not**, by itself, resolve whether this short revisit is intended
ordinary coverage or prohibited nonlocal retrace under a broad-ramp policy.
The existing thin-core normal-window permission is not silently extended to
this ramp. No new acceptance or prohibited-contact classification is granted.

## Receiving result and remaining uncertainty

No disconnected-membership witness was found at the fixed receiving grid
parameters. That is not a continuous no-reentry proof. Both receiving cubics,
all cross-E pairs and the intervening aggregate travel are included in the
global separation bound, but overlap within that bound remains unclassified.

The earlier sufficient monotonicity proof was therefore insufficient in two
different ways: departure now has an actual point revisit; receiving still has
only an unresolved proof obligation, not an observed violation.

## Validation, budget and evidence

- **15 new diagnostic tests pass; all 248 `tests/test_nu*.py` tests pass.**
- One diagnostic batch takes **0.232758 seconds**, within 300 seconds.
- The report is **7,204 bytes**, within the 2MiB output ceiling.
- No new candidates, geometry, images, fitting, physical runs, retries or mu.
- Saved report/candidate, historical dependencies and original repair approval
  hashes verify before and after measurement. No runtime-readiness renewal.

Evidence base:
`shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/`.

- [Approval and diagnostic source pins](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/ramp-contact-measurement-approval.json).
- [Full report and exact witness](../../shared/training/konrad_hand_recovery/stroke_gestures_v2/nu-mutual-construction-v1/ramp-contact-measurement-001/report.json).

Report SHA-256:
`b713160b41bf86aa17de87d6718c2b27a1e3d523c5cd1e7600b9fec5205da79a`.
The saved candidate remains
`616526b0952f02264d772508bce4342c325cc21a4648e49abd50efdaf01845f5`.

## Recommended next gate

Review the **broad-ramp ordinary-coverage versus unwanted-retrace criterion**
against this exact departure witness before changing geometry or promising a
stronger uninterrupted-membership proof. If uninterrupted membership is the
intended requirement, saved departure cannot satisfy it and a separately
approved local geometry/action repair would be needed. If some local revisit
is intended, define and approve a bounded ramp-specific classification before
applying it; do not quietly borrow the thin-core rule or relax a numerical limit.

Receiving still needs a full-domain certificate or witness under that same
explicit ramp criterion. No such follow-up, policy revision or repair has begun.
CURRICULUM-016 remains in progress; nominal review and HANDVALIDATE-025/026
remain gated. All prior evidence stays preserved and changes are uncommitted.
