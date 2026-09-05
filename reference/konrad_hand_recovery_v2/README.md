# Konrad observations v2 — benchmark evidence, not a learned hand

This immutable dataset contains 60 automatic word-region candidates from the
same apparent right-column hand used in the v1 experiment. It preserves native
source pixels and explicit uncertainty. **Zero candidates are currently
admitted; G0 is blocked.** The 30–60 usable-instance target has not been met.

## Results

- Candidate reservations: 41 training, 11 development, 8 locked test.
- All 26 legacy word labels remain machine hypotheses with unverified visible
  forms. Previously inspected held-out words, their source-line peers, and
  overlapping regions are development only.
- Another 34 lower-column regions were proposed automatically. They are
  unlabeled and quarantined; the final two new line groups reserve the 8 test
  candidates. No test images are displayed in the review sheets.
- All 60 candidates lack declared exact logical-to-visible mappings; 38 also
  have missing/uncertain readings, 52 exceed the unknown-ink limit, and 38 have
  no confidently assigned target ink. Exclusion categories overlap.
- Five synthetic image-objective controls pass. Source calibration remains
  blocked because there are no admitted non-test independent repeated words.

These results identify a data problem. They are not a claim of recovered
handwriting, verified transcription, or source-hand attribution.

## Inspect and reproduce

Start with `contact_sheet_01.png` through `contact_sheet_06.png`. Each row shows
raw crop, mask overlay and cleaned preview at the same isotropic scale. Orange
means unknown ink; pink marks detected neighbouring ink removed from the target.
The full contact sheet is also available. Locked-test rows show a placeholder.

```sh
.venv/bin/python -m scribesim.evofit.reference_dataset \
  --input reference/konrad_hand_recovery_v2/input_manifest.json \
  --output /tmp/konrad-observation-replay
```

The repository's default benchmark is `shared/training/konrad_hand_recovery/benchmark_v1`.
Use a new empty output directory for each run. This module and its dependencies
are tracked; it does not import the ignored local extraction/transcription helpers.

`manifest.json` contains source/crop/mask hashes, extraction-code and configuration
identity, native bounds, reversible translations, estimated baselines/x-heights,
label hypotheses, split assignment, exclusions and coverage. `coverage.json`,
`calibration.json`, and `G0.json` give the separate evaluation results. The
source JPEG is copied byte-for-byte under `sources/`.

## Mask contract

Mask values are 0 = known background, 128 = unknown, 255 = target ink. Assignments
use connected weak ink with strong support, line cores and explicit ambiguity
when a component touches multiple line cores. A weak flood without sufficient
strong support stays unknown. Pale strokes attached to a strong target survive;
isolated pale marks and touching-line components remain uncertain.

**Use raw pixels plus the mask for fitting.** The cleaned PNG is a preview:
unknown pixels are displayed white there and must not be interpreted as known
background by a training loss. The conservative masks can leave only fragments
of difficult words; those cases are quarantined, not presented as cleaned truth.

The thresholds are frozen engineering admission rules. Synthetic controls and
development repeat statistics are not handwriting/readability validation.

## Work required before G0 can pass

Resolve the actual visible-form mappings and reading hypotheses on usable
training/development crops, improve ambiguous masks or acquire cleaner source
observations, and meet per-symbol instance/context coverage. Preserve the
reserved test boundary; do not inspect or tune on its images while revising the
model or extraction rules. Record target appearance review against the frozen
benchmark contract. Run source calibration once independent admitted repeats
exist. Newly versioned data must retain the prior exclusions and intervention
history rather than relabeling this snapshot as a successful corpus.
