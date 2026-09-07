# Independent return-primitive evaluation

**HANDVALIDATE-015's original evaluation result is FAIL, not GO.** Its compound
subdivision failure and false S1 flags remain unchanged. The subsequently authorized
[HANDFLOW-011 repair and reevaluation](../tangent_evaluation/README.md) now pass for
the same candidates under `curve-tangent-v1`. Only that new scoped reader admits
fixed-tool shared-gesture learning; the original legacy reader does not.

## What ran

The evaluator reconstructs the frozen run-002 candidates, current original-six
baseline, independent analytic targets, supplied attachment probes, plans and
actual controller trajectories. No optimizer, candidate reselection, trainer
execution helper or saved training motion result supplies the evaluation proof.
The fixed tool, source curves, ports, compiler/controller and thresholds are unchanged.

All first/replay workers run in a clean detached checkout of `7114491`, with
hash seeds 0 and 839. Each seed uses **612 renders including replay**, well below
5000; total **1836**, zero optimization, zero diagnosed reruns. Recorded per-seed
first-plus-replay times are 18.513, 18.218 and 19.792 seconds, below 1800.
All **37 non-wall-clock artifacts per seed** replay byte-for-byte, including
the failure. Candidate files remain byte-identical to the original selection.

| Required proof | Seeds 7 / 19 / 41 |
|---|---|
| Current original-six baseline, before return evaluation | Pass |
| Both returns, unseen scales | Pass |
| Underturn and overturn attachments | Pass |
| Compound full/family-local image benefit and blank regions | Pass |
| Exact actual ownership/contact and shared-parameter propagation | Pass |
| Arc/time/image/endpoint and contact-event refinements | Pass |
| Compound desired acceleration after subdividing all cubics | **Fail: 402.432 > 250 mm/s²** |
| Seven required adversarial controls | Detected |
| S1 extension / gesture fitting | **Not admitted** |

All fifteen full-image and family-local learning benefits are reproduced. The
compound ratios remain upper **0.303233**, lower **0.327130**; this is no longer a
cropped-frame problem. Most pictures should look like the previous samples:
these are deliberately the same frozen candidates, not new learning. The new
failure concerns desired velocity direction at an artificial subdivision seam,
not a missing visible stroke or elapsed-clock drift.

## Samples and evidence

- [Seed 7 complete practice sheet](run-001/seed-7/first/practice-sheet.png)
- [Seed 19 complete practice sheet](run-001/seed-19/first/practice-sheet.png)
- [Seed 41 complete practice sheet](run-001/seed-41/first/practice-sheet.png)
- [Full-size compound actual ink](run-001/seed-7/first/compound-attachment-actual-900dpi.png)
- [Independent local adversarial guards](run-001/seed-7/first/local-controls.png)
- [S1 decision and artifact manifest](run-001/S1-primitives.json)
- [All seed-7 measurements and controls](run-001/seed-7/first/report.json)
- [Plans, owners and actual refinement traces](run-001/seed-7/first/traces.json.gz)
- [Adversarial trace evidence](run-001/seed-7/first/control-traces.json.gz)
- [First/replay budget ledger](run-001/execution.json), [verification](verification.json)
- [Pre-result criteria freeze](spec-v1.json), [diagnosis and required next fix](diagnosis.md)

The five sheet columns are initial / independent target / frozen candidate /
sampled desired / actual controller. All use the complete [-2,9,3,16] mm frame,
native 900-DPI presentation and unchanged 180-DPI evaluation. No retouching.

## Why the stronger check matters

Earlier subdivision replay split only the stem. This evaluator independently
De Casteljau-splits **every cubic**, including both returns, in a separate execution
copy. Geometry remains equivalent and the saved fitted model is never modified.
The compound's upper-return seam exposes a chord-derived tangent jump. Its desired
acceleration fails even though actual acceleration is 147.492 mm/s² and contact
event drift is only 1.78e-15 seconds. Neither improving ink nor a stable clock may
override that mandatory desired-motion gate.

Wrong ports/directions, detached geometry, hidden lifts, painted air and an
overlapping undeclared contributor are rejected by exact port/contact/owner audits.
Independent connector/terminal/counter blank guards also detect their mutations.
Original global sensitivity failures are retained: hidden connector 0.010179 and
extra terminal 0.096616 still fail the **unchanged 0.1** minimum. An exactly
overlapping extra owner has zero image disagreement. Local/structural requirements
were explicitly frozen before this run, not substituted after seeing the scores.
The counter is an analytic guard fixture, not an accepted learned counter or letter.

## Runtime boundary and next step

Eleven new tests pass. The final clean expanded suite has 190 passes and twelve
failures; a pre-change clean baseline has 179 passes and exactly the same twelve
failures (one constructor and eleven obsolete gesture-lineage expectations).
Plan/artifact/link/diff checks pass with ten unchanged doctor issues. The installed
strict PR parser still rejects this repository's ID format; no provider CI or
human appearance approval is claimed.

`require_primitive_readiness(directory, expected_report_sha256=..., required_families=...)`
requires a consumer-frozen report identity, current code/spec/source identities,
complete artifact/replay verification and recomputed numeric fixture gates.
This report's SHA is
`e779c923379db352b43fa9dc3aa8edc5c967170116404fa2c4e79b2bba2f31b9`;
the reader rejects it because it failed. A completed Advance is not admission.

The separately authorized follow-up now implements the following repair and
passes reevaluation; see the [current result](../tangent_evaluation/README.md).
The original required next step was to repair source-tangent continuity at equivalent subdivision seams,
then refresh current-code baseline/lineage and repeat the no-refit independent
evaluation. Do not change the model, drop boundary samples, relax acceleration,
edit old hashes or treat the hypothetical derivative check as an implemented fix.
Only a subsequent matching independent pass can permit bounded shared-gesture
learning. Opposite bowl, lower loop, closed-counter letter attachment, learned
letters/words, dynamic actions, fatigue and historical-hand acceptance remain absent.

```sh
.venv/bin/python -m pytest tests/test_handvalidate_foundation_primitives.py -q
.venv/bin/python -m scribesim.handvalidate.foundation_primitives --output /tmp/independent-return-evaluation-new
```

Use a new directory. The second command repeats evaluation, never fitting; its
budget includes its own fresh-process replay. Preserve this failed run unchanged.
