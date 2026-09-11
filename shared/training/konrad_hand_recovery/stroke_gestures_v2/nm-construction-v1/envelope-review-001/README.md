# Saved n→m candidate — revised checker passes

The owner approved implementation and reinspection of the saved candidate.
The [separate approval](../envelope-approval.json) binds the immutable revision,
candidate, original report and helper identities. The
[new report](report.json) records one reinspection in9.172 seconds, within300s.

## Results

- **All evaluated gates pass**, including finite-nib clearance/splice containment.
- Exact saved candidate SHA-256 remains
  `5b570b3df83e88dea38c4faf3b3c4badc121bf2055b0a0631efebf1b515b434c`.
  The checker loads it directly; no construction, refit or selection is called.
- Leftward excursion upper bound0.000087725mm; allowed departure envelope
  0.003178919368mm, below the0.0045mm scale cap.
- One horizontal minimum at parameter0.018403134150; one recovery at
  0.036818754825. Each simple root is enclosed and checked with exact-rational
  polynomial signs. These are geometric parameters, not clock times.
- The entire left-of-A portion lies within a0.083590119mm radius enclosure
  around A, below the0.1125mm locality limit.
- Length upper bound4.432965778mm versus4.797308244mm ceiling. Curvature upper
  bounds8.806225098/mm and5.518955270/mm versus8.888888889/mm ceiling.
- Attachments and frozen body/ownership/placement remain intact. All21 new/retained
  or T/R pair checks pass. Only the three named splice disks allow intersection.

Finite-nib checks recursively bound exact Bezier control hulls swept by the fixed
nib, using separating-axis projections and conservative intersection boxes.
No flattening approximation is needed. Any possible intersection is either
enclosed wholly inside its permitted0.45mm splice disk or remains unresolved;
an entire primitive is never exempted. A1e-9mm coordinate guard and bounded
subdivision are explicit. This is nominal fixed-nib geometry, not actual ink or
physical motion validation.

## Evidence boundary and next step

The original proposal, approval, candidate and unresolved report are preserved.
This is a pass under the **revised** envelope, not a retroactive original pass.
`accepted` remains false: style usefulness and physical behavior are unreviewed.
No new geometry, PNGs, fitting or physical runs were produced. The current task
implements the checker and reinspection; the conditional nominal packet is next.
Its allowance remains unspent and every image must be bound to this passing
report and the unchanged candidate before the owner usefulness review.

CURRICULUM-016 remains in progress; HANDVALIDATE-025/026 remain gated. No previous
physical budget is reset. Changes remain uncommitted; no merge or provider CI.

Local validation:146 tests passed,48 exact-null cases deselected. New tests cover
simple/multiple/double/boundary roots, progress, excessive excursion, locality,
cusp/retrace, approval/source tampering, diagonal nib separation and tiny overlaps
outside allowed splice disks. Existing geometry/ownership/context regressions
remain included; no fresh exact-null planning claim is made.

```sh
.venv/bin/python -m pytest -q tests/test_stroke_nm_envelope.py tests/test_stroke_nm_construction.py tests/test_stroke_clearance_audit.py tests/test_stroke_attachment_audit.py tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null'
```

Do not rerun the reinspection command: its single output directory refuses
overwrite, and the approved reinspection is consumed. Read the saved report.
