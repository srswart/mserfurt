# Fixed nu geometry — stopped at receiving-direction gate

Owner approved geometry implementation and checking, not rendering. The
[approval](../geometry-approval.json) binds the frozen proposal and boundary
contract report. One nu candidate was generated in5.709s; mu was not started
because the first instance failed. No parameters, sites or thresholds changed.

- [Saved nu geometry](nu-candidate.json)
- [Original check report](report.json)
- Candidate SHA-256: `7268952cd29fc7737c726838107e25f6bf0deeb4537992a8b415713150b0db97`
- Report SHA-256: `773ecfc7684284cf01354a18aed4a54a40354c8150c8a6c34ba91b883de27eaa`

## The failing requirement

S, the receiving turn into u, must match the canonical first-stem tangent at
t=0.25. That tangent has a leftward component. The fixed construction therefore
has minimum x derivative **−0.011663354102562806mm per unit parameter**, at its
receiving end, while the proposal requires S to be strictly rightward throughout.
The checker evaluates the quadratic derivative's endpoints and any interior
minimum; this is an analytic failure witness, not raster uncertainty.

This is another tangent/envelope incompatibility, now at the receiving side.
The proposal explicitly required rejection of an incompatible receiving tangent.
It should have been screened before committing to the strictly-rightward S
requirement. It is not evidence that thin nu connections are visually unsuitable:
no image exists and no visual judgment has been made.

## Checks that pass

| Check | Evidence |
|---|---|
| Exact source/action contract | Frozen contract validated; retained pieces use exact canonical restrictions and unchanged action lineage |
| Departure envelope | One allowed initial minimum/recovery; locality upper0.083590119mm <0.1125mm |
| T length | Upper0.983537565mm <1.127004407mm |
| R length | Upper4.726367506mm <5.727576502mm |
| S length | Upper0.653346740mm <0.736202725mm |
| Curvature | T/R/S upper8.806225098/2.401294093/8.212738379 per mm, below8.888888889 |
| Thin R contact | Whole-core width upper0.049244290mm <0.089393938mm |
| Attachments | Directed tangents and positions within unchanged tolerances |
| Receiver-top shift | 0.210200578mm <0.45mm |
| Vertical band / R rightward | Evaluated conditions pass |

These are conservative bounds, not curvature maxima or actual ink widths.
Finite-contact swept-overlap admission was **not evaluated**, as the earlier
structural gate failed. The checker contains conservative finite-thickness
contact-enclosure checks for future admitted structural cases; their tests
do not constitute a sweep pass for this saved candidate.

## Preserved scope and next decision

No mu candidate, images, fitting or physical runs. No corner switch, flipped
handle, altered source interval, automatic retry or relaxed constraint.
Implementation is in `scripts/nu_corner_geometry.py`, separate from all frozen
core, capability and boundary-action code. Existing geometry approvals do not
permit silently retrying after this failure.

Recommended next: a **receiving-tangent/envelope compatibility revision**, using
the saved evidence to decide between a tightly bounded tangent-following arrival
and a different compatible attachment. Preserve the thinness, curvature, body
and contact-clearance requirements. Any new criterion or site needs prospective
approval before a rerun; do not simply flip the preserved tangent to force a pass.

Validation:173 tests pass,48 exact-null cases deselected; source/approval checks
pass. No fresh exact-null planning, full sweep admission, style acceptance,
provider CI, commits or merges claimed. CURRICULUM-016 stays in progress;
HANDVALIDATE-025/026 remain gated.

```sh
.venv/bin/python -m pytest -q tests/test_nu_corner_geometry.py tests/test_nu_boundary_actions.py tests/test_nu_corner_contact.py tests/test_thin_connection_investigation.py tests/test_stroke_clearance_audit.py tests/test_stroke_attachment_audit.py tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null'
```

The attempt directory refuses overwrite. Report and candidate remain immutable.
