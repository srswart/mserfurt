# Pen-action learning runner

**Runner implemented; fitting BLOCKED and not performed.** No action is labeled
supported or unnecessary from zero renders. The unexecuted learning/transfer
tasks remain unchecked in CURRICULUM-009 despite runner completion.

[Synthetic admission attempt](run-002/report.json) and
[real admission attempt](real-attempt-002/report.json) stop before candidate
enumeration, target pixels or controller rendering:

- Matching S1-gesture is not passed and required gesture coverage is missing.
- Old whole-file gesture acceptance identities are stale after opt-in renderer
  and bridge changes. Legacy pixel compatibility is not new acceptance.
- The realized bridge retains the 0.40 mm contact-entry convergence failure.
- Real mode additionally lacks live reviewed G0 and accepted real lower layers.

The [frozen runner contract](spec-v1.json) defines seeds 7/19/41, at most three
isolated ablations (rotation, edge release, separate lifted finishing), at most
four knots, constant geometry/tool/pressure/speed, 5000 renders or 1800 seconds
per ablation/seed and one diagnosed revision. Fixed profiles win development
ties. Held-out scores can reject an activation but never select a replacement.
Pure proposal/selection tests do not constitute fitted action evidence.

The fitting core and manifest reader are implemented but **not exercised on
accepted rendered lessons**. There is no approved named-failure train/dev/test
lesson yet. A fresh scope-matching accepted baseline and lesson must be
registered before running it; editing an old status or replacing a checkpoint
cannot satisfy the pinned evidence, model, tool and current-code checks.

Both attempts use **zero renders and zero optimization**. Run-002 tightens
explicit baseline/model binding; [run-001](run-001/report.json) is retained.
The unit-only null-selection test uses a fitness stub, not simulated training.

    .venv/bin/python -m scribesim.curriculum.pen_actions --revision 1 --output /tmp/td018-actions
    .venv/bin/python -m scribesim.curriculum.pen_actions --real --revision 1 --output /tmp/td018-actions-real

Use new empty output directories. Admission reports replay exactly; wall-time
receipts vary. No source image, review, mask or locked-test reservation changed.

For actual visible implementation diagnostics, see the
[contact geometry](../contact/README.md) and [realized action bridge](../action_bridge/README.md).
These are deliberately not mislabeled as newly learned actions. Repair and
revalidate fixed-tool foundations before starting a fitted action experiment.
