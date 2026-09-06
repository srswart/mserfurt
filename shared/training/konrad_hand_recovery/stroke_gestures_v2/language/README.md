# Continuous gesture compiler

[Legacy-equivalent output](run-001/legacy-equivalent.png) preserves the original
fixed-tool sample stream and pixels. [Continuous-gesture output](run-001/continuous-gestures.png)
uses gesture-global arc sampling without lifts at primitive boundaries.
These are supplied i/u constructions, not learned letters or new historical forms.

The migrated two-primitive stem/exit gesture is shared across i and u; u has two
explicitly lifted occurrences. Each sampled/actual mark carries primitive,
gesture, action-profile, letter, word and line lineage. Declared overlap
contributors are occurrence-level metadata, not a per-pixel segmentation claim.

Use [model](run-001/model.json), [guide](run-001/guide.json) and
[report](run-001/report.json). Dynamic tracks have bounded representation but
execution rejects them until the realized-action bridge. Context overlays and
unqualified old crossings require explicit future migration; no silent fallback.

Replay into a fresh directory:

    .venv/bin/python -m scribesim.evofit.stroke_gestures --output /tmp/gesture-compiler-replay

36 tests cover invalid profiles, rates, ports, exact smoothness, expansion,
stale bundles, migration equivalence, subdivision and explicit lifted overlaps.
The canonical v1 implementation and all frozen primitive evidence are unchanged.
