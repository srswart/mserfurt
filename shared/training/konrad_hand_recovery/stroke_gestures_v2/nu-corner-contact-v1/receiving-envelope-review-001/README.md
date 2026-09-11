# Saved nu — revised receiving-envelope reinspection

**Pass under the revised structural/contact criteria; nominal and physical
acceptance remain gated.** No refitting, replacement candidate or control-point
change. The [original rejection](../geometry-001/report.json) remains unchanged
and valid under its original strictly-rightward receiving requirement.

## Evidence

- [Machine report](report.json), SHA-256
  `053aff33d2b767c622ea63614fd4727a394c1c6bce365740d007915c7e163b8f`.
- [Owner approval and frozen pins](../receiving-envelope-approval.json).
- [Approved receiving revision](../../../../../../docs/tech-direction/TD-018-nu-receiving-envelope-revision.md).
- [Saved candidate](../geometry-001/nu-candidate.json), SHA-256
  `7268952cd29fc7737c726838107e25f6bf0deeb4537992a8b415713150b0db97`.
- Checker: `scripts/nu_receiving_envelope.py`; evaluation identity
  `nu-receiving-envelope-evaluation-v2`. Code/tests hashes are in the report.

## Measurements

| Gate | Result |
|---|---|
| Receiving crossing before maximum | t≈0.952928151110, then t≈0.976477127487; each enclosed ±1e-12 |
| Canonical arrival | Original endpoint dx=−0.011663354103 retained; leftward arrival preserved |
| Handle-derived allowance | 0.003887784701mm, below unchanged0.0045mm cap |
| Curve right-of-C excursion | Guarded upper0.000137102893mm, below derived allowance |
| Entire overshoot locality | Upper0.055851813044mm, below unchanged0.1125mm radius |
| Thin-core width | Upper0.049244290009mm, below unchanged0.089393937899mm limit |
| T/R/S curvature upper | 8.806225098 / 2.401294093 / 8.212738379 per mm, below unchanged8.888888889/mm |
| Length, departure, vertical band, attachments, body/action identity | All pass |
| Finite-contact sweep | All27 new/retained and new/new pairs pass |

The receiving proof factors the exact endpoint crossing, isolates the interior
quadratic roots, checks their order and signs, and bounds the entire overshoot
interval with a restricted Bezier control hull. The locality disk grants no new
contact permission. The finite-contact proof uses conservative full-rectangle
supersets for every T/S ramp phase and the exact negative corner on R, certifying
separation or confinement to the existing four named splice disks. This is not
a rendered-ink, accumulation, timing or physical-performance measurement.

## Scope and validation

One saved-nu review completed in5.227679s of300s, with5GiB minimum-free guard and
10MiB output ceiling. No retries, constructor calls, new geometry, images,
controller executions or fitting evaluations. All frozen input pins verified
before and after inspection. The previous failure was not relabeled.

195 selected tests pass,48 exact-null cases deselected:

```sh
.venv/bin/python -m pytest -q tests/test_nu_receiving_envelope.py tests/test_nu_corner_geometry.py tests/test_nu_boundary_actions.py tests/test_nu_corner_contact.py tests/test_thin_connection_investigation.py tests/test_stroke_clearance_audit.py tests/test_stroke_attachment_audit.py tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null'
```

Tests include frozen identity mutation, tangent forgery, degenerate/additional
roots, missing crossing, cusp/retrace, excessive allowance, locality escape,
unchanged legacy gate results and no-constructor/contact-gating behavior.
ARRIVE plan/rule checks, local evidence links and whitespace checks pass.

Next: review these results before separately authorizing pending mu geometry
under the same receiving policy. Mu remains unstarted; no implicit approval for
nominal rendering, um/num, fitting or physical execution. CURRICULUM-016 remains
in progress; HANDVALIDATE-025/026 remain gated. Changes are uncommitted.
