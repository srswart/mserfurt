# Corner-contact capability — review required before geometry

**Owner feedback received:** [Nominal is acceptable; contextual entry is next](owner-feedback-001.json).
Continue [u-entry contract preparation](../../../../../docs/tech-direction/TD-018-contextual-u-entry.md),
not final acceptance or mu generation. Fine-tuning remains deferred. The frozen
visual packet below is preserved as reviewed evidence, not relabeled or rerendered.

**Visual comparison ready:** [Open frozen-nu review](nominal-001/index.html).
Unconnected n/u above connected nu, followed by enlarged color-keyed detail.
Vectors stay sharp when zoomed; this is nominal contact geometry, not actual ink.
No fitting or geometry changes. Owner visual review pending; mu unstarted.

**Current result:** [Saved-nu no-refit reinspection passes](receiving-envelope-review-001/README.md)
under [the revised receiving envelope](../../../../../docs/tech-direction/TD-018-nu-receiving-envelope-revision.md).
All structural and 27 finite-contact pair checks pass. Thinness/curvature and
saved geometry are unchanged. No images, mu, fitting or physical runs started.

**Historical geometry outcome:** [The fixed nu candidate stopped at its receiving-direction gate](geometry-001/README.md).
Canonical tangent matching conflicts with strictly-rightward S. Length, curvature,
attachments and thin-core checks pass; swept-contact admission and mu were not
started. No images, fitting or physical execution. Earlier findings stay preserved.

**Latest follow-up:** [Boundary-local contract and exact numeric handling](boundary-action-001/README.md)
now pass in a new opt-in type. Retained body actions and old APIs remain unchanged;
the capability findings below are historical evidence. Geometry is still gated.

The owner approved the read-only capability package only. See
[approval](capability-approval.json), [report](capability-001/report.json), and
[technical findings](../../../../../docs/tech-direction/TD-018-nu-corner-capability-findings.md).

Completed in13.638s, under300s; the directory was32KiB before this note, under10MiB.
The5GiB free-space guard passed. No connector geometry, images, controller runs
or fitting evaluations. No automatic retry or source repair performed.

## Findings

- Proposed negative corner [0,0.1] is accepted by contact geometry; its rectangle
  and directed labels reflect correctly. Contact-center displacement0.2025mm;
  transverse-width upper bound0.049244289mm at any travel angle.
- Full-to-corner and reverse fixed-site ramps have an exact full-rectangle union.
  The four nu/mu attachment sites have certified positive clearance to nonowner
  canonical strokes: at least1.279776951mm departing and1.118760702mm receiving.
  Own retained/replaced spans remain explicit possible contacts, not waived.
- The canonical connected-letter schema rejects BOTH partial-corner actions:
  it intentionally requires fixed actions. The shared `fixed` action affects all
  eight nu or ten mu occurrences; mutating it is not boundary-local execution.
- Opposite corner [0.9,1] also exposes a numerical contract bug: `1 - 0.9` is
  0.09999999999999998 in the current validator, so exact decimal10% is rejected.
  Neither widening that interval nor changing corner was attempted as a workaround.
- Existing interpolation reaches the negative endpoint0.1 exactly. Each ramp
  requires at least0.3s under the3/s endpoint rate; moving ramps remain unvalidated.

This is **not** a capability pass for connected execution or construction admission.
Static ramp envelopes are a geometric query, not a recommendation to hold the
pen still, a dab simulation or an ink-accumulation model. No new path was built.

Next: define an opt-in boundary-local action contract and numerically consistent
10%-edge validation, preserving canonical body actions and old source identities.
Geometry remains gated until that contract is reviewed and checked. The opposite
corner bug is not evidence that the chosen negative corner is geometrically bad.

Validation:125 tests pass,48 exact-null cases deselected; frozen source checks,
ARRIVE plan/rules, links and whitespace checks pass. Tests explicitly capture the
current positive-corner rejection; passing tests do not mean that bug is repaired.

```sh
.venv/bin/python -m pytest -q tests/test_nu_corner_contact.py tests/test_thin_connection_investigation.py tests/test_stroke_clearance_audit.py tests/test_stroke_attachment_audit.py tests/test_stroke_context_audit.py tests/test_stroke_context_contract.py -k 'not exact_null'
```

The capability snapshot refuses overwrite. Report SHA-256:
`b42bf1a70a0d52d4fde0a19a4fb7a52aab9ec81da342fbb959f59a796da231d6`.
CURRICULUM-016 stays in progress; HANDVALIDATE-025/026 remain gated. No budgets
reset, new core source identity, provider CI, commits or merges are claimed.
