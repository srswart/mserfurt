# TD-018 nominal specimen: blocked acceptance, implemented evaluation

**G1: blocked. This is an unaccepted seed diagnostic, not recovered Konrad handwriting.**

The three-line image deliberately shows what the exact repertoire pipeline can
currently produce without inventing trained forms. It remains upright/font-like;
its successful text ownership and replay are not evidence of correct letterform
appearance. Production rendering and the guided controller are unchanged.

## What to inspect

- `three-line.png`: exact reconstruction, synthetic unseen and project-text lines.
- `comparison.png`: equal-physical-x-height A/B panels for all three lines and five
  strings; neutral catalog adapter versus contextual catalog priors. These are not
  mislabeled production CLI baselines. `unblinding.json` identifies A/B.
- `reference-sheet.png`: unchanged frozen benchmark sheet; source x-height estimates
  and target appearance remain unreviewed.
- `freeze.json`: checkpoint/configuration/contract/source/code identities, exact
  text inventory, held-out reservation/exclusions and G0, written before scoring.
- `report.json`: eight exact ownership plans, actual two-process PNG replay hashes,
  synthetic adverse controls and explicit absence of real locked-test scores.
- `review-template.json`: pending owner rubric and independent readings, bound to
  this exact freeze and report. No approval or transcription has been invented.
- `G1.json`: stop and repair prerequisites; no production promotion.

There are **zero usable locked test cases** in this corpus version. No test pixels
are used for fitting; integrity checks may verify source/crop bytes, but the locked
evaluation routine is not called while G0, a real checkpoint or calibrated
tolerances are missing. Empty repeated/unseen groups cannot pass. Synthetic new
strings are unscored combinations, not novel-word manuscript references.

## Reproduce and evaluate

```sh
python -m scribesim.handvalidate.nominal build --output /tmp/new-nominal-specimen
python -m scribesim.handvalidate.nominal evaluate --output shared/training/konrad_hand_recovery/nominal_specimen_v1
```

Use a new directory; existing evidence is never overwritten. Evaluation refuses
changed renderer/evaluator code, models, rasters or frozen identities. Reproduce
older bundles at the recorded source revision rather than relabeling old evidence
as current. `report.json` records the actual local commands and environment; their
absolute output paths are execution provenance, not required portable paths.

For a future admitted real corpus, run the recovery CLI, then build with
`--recovery-root <run> --criteria <json> --target-review <json>`. Criteria fields are
`status: frozen_train_development`, `per_case_max_loss`,
`per_case_max_regression`, `unseen_mean_min_gain`, and the canonical
`source_calibration_sha256`. Do not choose thresholds after inspecting locked
scores. The run's model, initial baseline, configuration and dataset identities
must match; synthetic checkpoints are rejected by this path.

Complete a copy of the review template only after actual human review and an
independent reading, then pass it with `evaluate --review <json>`. G1 requires all
five rubric categories acceptable, candidate preference, exact transcriptions,
coverage, replay, controls and per-case thresholds. An aggregate improvement
cannot conceal a failed required word. Real results re-score the same frozen
checkpoint for integrity; they do not refit it.

## Stop decision

No diagnosed model revision was made and no locked test was scored. The next
useful work is corpus repair: exact visible labels/mappings, cleaner masks,
sufficient repeated/context support, train/development source calibration and
target review. Then perform real fitting and reserve/evaluate the G1 specimen.
Do not proceed to guided realism while G1 is blocked. A subsequent model revision
must disclose reuse and reserve a new locked test set beyond the allowed initial
evaluation and one diagnosed revision.
