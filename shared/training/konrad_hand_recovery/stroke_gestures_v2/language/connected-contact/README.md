# Connected gesture contract — GESTURE-003

This implements contact mechanics, **not the repaired n/u/m shapes**. Shared
upright geometry and owner-review samples remain CURRICULUM-015. No fitting,
new target, alphabet expansion, pressure reduction, S2, context or fatigue is
introduced. All touched components remain incubating.

## Explicit opt-in

Use `shared-stroke-gestures-connected-v1` with `gesture-arc-v3` sampling. The
lowered schema is `shared-stroke-language-connected-v1`. Legacy schemas retain
their original semantics and guide bytes; there is no automatic conversion.
Construct a new explicitly versioned model with truthful cubic endpoint tangent
ports; do not simply relabel a frozen old model or rewrite its provenance.

- Keep up to eight primitives and eight gestures, at most four primitives per
  gesture, four gesture instances per recipe and six expanded references. Legacy
  four-reference and foundation six-reference limits are unchanged.
- Inventory is limited to diagnostic i and the planned n/u/m constructions.
- Tool/scale are fixed at 3.5 mm x-height, 0.45 mm nib and 40 degrees. Only the
  full-edge constant `fixed` action at pressure 0.5 and speed 12 mm/s is supported.
- First instance uses `start`; later instances explicitly use `smooth`, `corner`
  or `lift`. Connected endpoints must coincide within 1e-10 x-height; smooth
  tangent alignment uses the existing 1e-6 dot-product tolerance. These are
  numerical continuity guards, not appearance/slant tolerances.
- Internal cubic joins must be smooth. Expose intentional reversals as primitive
  or gesture `corner` boundaries so the clock can stop without raising the pen.

## Ownership, overlap and timing

Each compiled primitive keeps its gesture/action identity and also receives a
`contact_run_id`. Sampling groups by contact run, not gesture occurrence. A
connected port has one sample, owned by the outgoing primitive. Its
`boundary_contributors` records the last incoming primitive/action at gesture
progress 1 and the outgoing primitive/action at progress 0. There is no duplicated
zero-distance dwell, hidden air sample or pressure reset. Inter-letter travel
remains lifted; this is not word-context behavior.

Overlap admission uses conservative circular nib envelopes around 257-point
cubic samples with a derivative-based interpolation allowance. This catches
retracing and close parallel paths that proper-crossing tests miss. It is **not
an exact physical overlap-area measurement**. Adjacent smooth joins have a local
two-envelope-width shared-port allowance; corners/reversals and lifted overlaps
require an explicit earlier `overlap_with` contributor, including short retraces.
Conservative false positives may require extra declarations; physical ink
accumulation remains an independent HANDVALIDATE-021 evaluation obligation.

`gesture_guide` includes curve provenance automatically for this version.
`action_bundle` is still an unretimed desired plan. `execute_actions` (also used
by `execute_gestures` for this schema) applies `curve-tangent-v1` corner timing and
the existing `event-time-v2` controller with no artificial settle time. Results
include clock/corner evidence and contact/ownership checks. A tracking pass is
not shape, overlap-quality or hand acceptance. New bundles additionally pin the
connected contract and curve-tangent implementation. Missing/stale identity fails
closed; legacy bundles are not silently refreshed.

## Bounded evidence

`proof.json` binds the final `aa5feed` implementation and test fixture source.
It records 12 configurations: straight smooth continuation, exact corner retrace,
genuine lift, and a two-letter lifted separator; each uses base, finer-arc and
finer-time settings. Each configuration replays exactly in the same process.
There are 48 metric renders at 72 DPI, no optimization and no fresh-seed or
independent-admission claim. These straight diagnostic fixtures are not new
letter samples. Full executable fixtures are in `tests/test_connected_gestures.py`.

Maximum actual corner speed is 0.031478 mm/s (existing limit 0.5); corner position
error is 0.001548 mm (limit 0.05); contact corridor error is 0.025034 mm (limit
0.25). Time error, contact errors and owner errors are zero. No target/image-loss
acceptance is inferred from the diagnostic renders.

`pre-overlap-hardening.json` preserves the earlier c95d694 proof, before the
short-retrace negative control exposed a shared-port allowance bug. The final
implementation removes that allowance for corners. The final proof was rerun,
not re-stamped; metrics match, with new source/result hashes.

Run the new contract tests with:

```sh
.venv/bin/python -m pytest tests/test_connected_gestures.py -q
```

## Historical compatibility versus live admission

The HANDVALIDATE-020 report and candidates are unchanged. Its report remains
`bd3def56ffb24c9541815d3234cceddb31d21453331f2a6764f95c009026b28e`.
Legacy guide serialization matches hashes measured before implementation.
However, shared compiler/action-bridge **source identities have changed**. Old
live admission correctly fails with `Stale, incomplete or overstated independent
evidence`; do not rewrite the old receipt hashes to bypass this.

Five historical-admission tests in `test_curve_tangents.py` fail against the new
source tree and all five pass in the pinned pre-change `fc562b8` checkout. They
are not claimed as passing current admission. Historical sources remain in git;
fresh matching-source validation is required before reusing those admissions.
The new geometry preview may be explicitly unaccepted; it must not inherit an
old lower-layer pass. HANDVALIDATE-021 must evaluate the exact new identities.
