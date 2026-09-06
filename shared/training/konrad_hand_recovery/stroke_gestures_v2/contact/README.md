# Physical contact geometry

**Implemented opt-in geometry, not S1-action acceptance.**

[Comparison sheet](run-001/contact-comparison.png) shows eight independent
analytic expectations, the canonical physical sweep and refined sampling at
equal physical scale. Rotation, wrap, left/right release and lifted finishing
are declared fixtures, not learned movements or historical calibration.

The `physical-edge-v1` path uses a 0.45 mm directed edge and 0.02 mm thickness.
Releasing one side translates the surviving footprint instead of shrinking it
around the center. Pressure is 0.5, optical deposition is constant and speed
learning/deformation/dabs are unsupported. The existing canonical sweep draws
both legacy and explicitly versioned contact; there is no separate brush engine.

[Results](run-001/report.json): eight geometry checks pass the unchanged 0.05
oracle and 0.03 refinement bounds. 25 diagnostic renders, zero optimization.
The legacy pixel hash is unchanged; new fields require the explicit reader mode.

Whole-file identities of the renderer and bridge have changed. Frozen older
S1 evidence is retained but **stale for current-code admission**, even where
legacy pixels match. Revalidate rather than rewriting hashes or treating an old
pass as permission for new fitting. The earlier gesture gate was already blocked
by coverage and contact-entry convergence; this geometry work does not repair it.

    .venv/bin/python -m scribesim.handvalidate.nib_contact --output /tmp/td018-contact-proof

Use a new empty output directory. Semantic report and image replay identically;
`execution.json` records variable wall time. No default renderer switch.
