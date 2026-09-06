# TD-018 reference repair v3: still blocked, not training data

One frozen strong-seed mask revision was applied to the 52 non-test candidates.
Compared with v2, non-test crops with no target ink decrease from 32 to 10;
excess-unknown exclusions decrease from 44 to 36. The eight locked-test crops,
masks, labels and split reservations remain unchanged and absent from previews.

**Zero observations are admitted.** All 52 non-test candidates still need exact
verified mappings; 30 also have missing/uncertain readings. No human review was
performed or invented. Source calibration and genuine target review remain
blocked, and real stroke fitting must not run. See `G0.json`, `coverage.json`
and `repair_report.json` for overlapping reasons and symbol/context debt.

## Review and reproduction

`review.json` contains only non-test rows, initially pending, bound to source
coordinates/raw hashes and the immutable v2 manifest. A supplied confirmation
requires exact logical/visible mapping, reviewer, timezone timestamp and a
separate approval map of entry digest to reviewer. That map is an explicit
external trust input, not cryptographic authentication or automatic verification
of a human's identity. Do not generate it on the owner's behalf. Multi-character
identity spans and long-s are supported; other abbreviations remain quarantined.

The lineage and complete review inputs are retained in the manifest and checked
by normal dataset validation, not only by this command's summary. Future reviews
must write a new version, never alter this snapshot. The raw source JPEG is
unchanged; three-state masks still exclude unknown pixels from fitting.

```sh
.venv/bin/python -m scribesim.evofit.reference_repair --output /tmp/new-repair
```

Inspect `contact_sheet_01.png` through `contact_sheet_06.png`. Orange is unknown,
not background truth. Strong components touching multiple line cores remain
unknown. Local pale growth is bounded to three pixels and does not cross strong
ambiguous ink. This automatic segmentation is not verified stroke decomposition.

Stop decision: obtain real non-test readings/mappings and target review, then
recompute admission/calibration. Any additional source acquisition or extraction
revision needs a named support shortfall and a new budget. Synthetic stroke
language exercises can proceed independently, with no historical acceptance claim.
