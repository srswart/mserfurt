# Gesture coverage investigation

**Decision: proceed with synthetic fixtures only; real G0 remains blocked.**

Audited 52 non-test records and mask exclusions; no new visual readings, source acquisition or label changes. All source/test pixels remain sealed from decoding. Zero admitted real starter characters.

[Synthetic centerline specifications](synthetic-fixtures.png) are independently authored hypotheses, not learned strokes, nib renders or actual execution. [Fixtures](fixtures.json) freeze single-gesture practice and different-scale lifted-pair transfer. Primitive roles still need v1 compatibility investigation.

| Candidate | Construction hypothesis | Real status / independent support |
|---|---|---|
| stem | i: stem plus unresolved exit | unresolved / 0 |
| rise | u: entry approach, not a complete letter | unresolved / 0 |
| underturn | u: underturn plus stem (4 primitive occurrences) | unresolved / 0 |
| overturn | n: overturn plus stem (4 primitive occurrences) | unresolved / 0 |
| compound_curve | m: alternative compound construction hypothesis, not an accepted recipe | unresolved / 0 |
| left_bowl | c: open bowl construction hypothesis | unresolved / 0 |
| upper_loop | l: loop plus stem construction hypothesis | unresolved / 0 |
| lower_loop | g: descender only; bowl/attachment unresolved | unresolved / 0 |

[Workbook/report](report.json) records native coordinates, source IDs, uncertain mappings, competing hypotheses, budget, coverage debt and a separately authorized review/acquisition request. Possible observation links use unverified text, not evidence of ductus. No candidate is historical-support accepted.

[G0](G0.json) is recomputed by the benchmark evaluator with dataset_root=None: known blockers suffice to stop. Full dataset integrity is explicitly unverified because that validator decodes locked pixels. This is not a substitute G0 pass or permission to train. No repeat calibration is possible without admitted observations.

Replay from repository root into a fresh directory:

```sh
.venv/bin/python -m scribesim.curriculum.gesture_coverage --output /tmp/td018-coverage-replay
```

No optimizer, controller, primitive checkpoint or production default was changed.
