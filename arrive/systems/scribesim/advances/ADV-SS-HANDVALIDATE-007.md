---
advance:
  id: ADV-SS-HANDVALIDATE-007
  title: Neural Promotion Gates — Style Distance, CER Bands, Anti-Font Check, A/B Bench
  system: scribesim
  primary_component: handvalidate
  components:
  - handvalidate
  - scribehand
  - metrics
  - annotate
  started_at: 2026-07-03T14:00:00Z
  implementation_completed_at: ~
  updated_by: cursor-agent
  review_time_estimate_minutes: 30
  review_time_actual_minutes: ~
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - legibility
  evidence: []
  model_usage: []
  status: in_progress
---

## Objective

Extend the TD-014 gate discipline to the neural path per
[TD-018](../../../../docs/tech-direction/TD-018-learned-scribal-hand.md) §2.7 and
the Definition of Success:

- **Style-distance gate:** writer-ID embedding distance between generated words
  and anchor exemplars within the calibrated same-writer band; FID/KID on line
  crops generated-vs-anchor.
- **CER bands:** folio-level aggregation of the ADV-SS-SCRIBEHAND-002 per-word
  scores (word CER ≤ 0.05 target).
- **Anti-font check:** no two same-text words on a folio pixel-identical;
  per-letter instance-variance floor measured across the folio.
- **Acceptance-band metrics:** existing `metrics/` suite (stroke width, slant,
  spacing CV) compared against anchor manuscript pages as acceptance ranges, not
  optimization targets.
- **A/B bench + review:** neural-vs-evo folio bench reusing the TD-014
  regression dashboard; workbench side-by-side review mode; promotion to default
  renderer requires a reviewed proof-folio set.

## Behavioral Change

After this advance:
- `scribesim bench-neural --folios ...` emits gate verdicts (JSON + visual
  sheets) covering style distance, CER bands, anti-font variance, and metric
  acceptance bands.
- Promotion of `--approach neural` to default is mechanically blocked until all
  gates pass on the reviewed proof-folio set.

## Planned Implementation Tasks

- [x] branch: cursor/learned-scribal-hand-direction-3c31
- [x] tidy: covered by pathguide.io import fix (ADV-SS-SCRIBEHAND-003)
- [x] test: gate threshold logic + anti-font NCC + HOG style distance + bench CLI — red first
- [x] feat: neural_bench with CER bands, anti-font check, HOG style-distance baseline, acceptance bands (M1-M9)
- [x] feat: bench-neural CLI writing metrics.json + diagnostic sheets; gates in shared/hands/validation/neural_gates.toml
- [ ] Mac: calibrate style/acceptance thresholds on real anchor pages (real pages must pass their own gates)
- [ ] workbench side-by-side review mode (human evaluation currently via runbook §8 rubric)
- [ ] promotion policy wiring once first real bench bundles come back

## Bug Fixes

- [ ] None yet

## Risk + Rollback

- Risk: gate thresholds calibrated too loosely make promotion meaningless, too
  tightly make it unreachable; calibrate all bands on real anchor pages first
  (real pages must pass their own gates).
- Rollback: gates are evaluation-only; disabling them cannot affect render output.

## Evidence

- [ ] tidy:preparatory
- [ ] tdd:red-green
- [ ] tests:unit
- [ ] snapshot (bench dashboard on proof folios)

## CI Evidence Notes

- CI jobs are currently disabled; run externally before merge:
  - `arrive pr check --strict --json`
  - `arrive evidence record --advance ADV-SS-HANDVALIDATE-007 --status passed`

## Changes Made

### 2026-07-03 - test: neural promotion gates
- tests/test_neural_bench.py: 12 tests incl. bench CLI end-to-end (red first)

### 2026-07-03 - feat: neural bench
- scribesim/handvalidate/neural_bench.py: gates + BenchReport
- shared/hands/validation/neural_gates.toml: thresholds (calibration pending)
- scribesim/cli.py: bench-neural command

## Bug Fixes (during red-green)

- neural_bench: cer_mean of exactly 0.0 was treated as missing via `or`-fallback, failing a perfect folio; fixed with explicit None checks
- metrics suite field is MetricResult.id, not metric_id
