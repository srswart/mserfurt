---
advance:
  id: ADV-SS-METRICS-001
  title: Comparison Metrics M1-M9 — Quantitative Manuscript Distance
  system: scribesim
  primary_component: metrics
  components:
  - metrics
  started_at: 2026-03-20T15:40:00Z
  started_by: srswart@mac.com
  implementation_completed_at: 2026-03-20T12:18:04.472832Z
  implementation_completed_by: srswart@mac.com
  updated_by: srswart@mac.com
  archived_at: null
  archived_by: null
  pr_links: []
  reviewability_score: 0
  risk_flags:
  - new_dependency
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  status: complete
---

## Objective

Implement the nine comparison metrics from TD-003 Part 2 that measure the distance between a rendered folio and a real manuscript sample. These metrics enable both objective evaluation of rendering quality and programmatic parameter optimization.

## Behavioral Change

After this advance:
- **M1 — Stroke width distribution**: ridge detection on both images, histogram distance (Wasserstein) of stroke widths. Captures nib angle behavior, thick/thin contrast.
- **M2 — Baseline regularity**: line detection (Kraken or custom), measure per-line slope variance, inter-line spacing variance, left-margin position variance. Captures ruling imperfection, baseline undulation.
- **M3 — Letter spacing rhythm**: measure inter-glyph spacing along baselines (connected-component gaps), compare autocorrelation functions. Captures writing rhythm.
- **M4 — Ink density variation**: mean ink darkness in sliding windows across the page, compare spatial pattern. Captures dip cycle visibility.
- **M5 — Glyph shape consistency**: extract all instances of a letter class, compute pairwise Hausdorff distance on skeletonized forms, compare within-class variance. Captures per-glyph variation quality.
- **M6 — Ascender/descender proportion**: measure ascender-height/x-height ratio across tall letters, compare mean and variance. Captures Bastarda-specific letterform proportions.
- **M7 — Connection angle distribution**: measure angles at letter junctions within words, compare distributions. Captures inter-letter trajectory quality.
- **M8 — Overall texture (frequency domain)**: 2D FFT of text blocks, compare power spectra. Captures holistic page texture.
- **M9 — Perceptual similarity**: pretrained feature extractor (CLIP or DINO), compute feature distance between crops. Captures overall "feel."
- **Composite score**: weighted sum of all metrics, initially equal weights.
- Each metric returns a normalized distance in [0, 1] and qualitative rating (good/okay/needs work) based on empirically-determined thresholds.

## Planned Implementation Tasks

- [ ] Tidy: define `MetricResult` dataclass (name, distance, rating, detail) and `MetricSuite` interface for running all metrics
- [ ] Test: write tests using synthetic image pairs with known properties — identical images score 0.0; images with different stroke widths show high M1; images with different baselines show high M2
- [ ] Implement: M2 — baseline regularity (highest priority per TD-003). Line detection, slope/spacing/margin variance measurement.
- [ ] Implement: M1 — stroke width distribution. Ridge detection, width histogram, Wasserstein distance.
- [ ] Implement: M4 — ink density variation. Sliding window mean darkness, spatial pattern comparison.
- [ ] Implement: M8 — frequency domain texture. 2D FFT on text blocks, power spectrum comparison.
- [ ] Implement: M3 — letter spacing rhythm. Connected-component gap measurement, autocorrelation comparison.
- [ ] Implement: M5 — glyph shape consistency. Glyph extraction, skeletonization, within-class Hausdorff variance.
- [ ] Implement: M6 — ascender/descender proportion. Tall letter detection, height ratio measurement.
- [ ] Implement: M7 — connection angle distribution. Junction detection, angle measurement.
- [ ] Implement: M9 — perceptual similarity. CLIP/DINO feature extraction, cosine distance. (Optional dependency on torch; falls back gracefully if unavailable.)
- [ ] Implement: composite score with configurable weights.
- [ ] Validate: run full metric suite against a known rendered folio and a real manuscript sample; verify all 9 metrics return plausible values
- [ ] Checkpoint: run `scribesim compare` on the render-002 snapshot f01r vs a real manuscript sample; copy the metric report to `./snapshot.sh metrics-001` output. This is the first QUANTITATIVE assessment of how close we are.

## Risk + Rollback

**Risks:**
- M9 introduces a heavy dependency (torch + pretrained model). Should be optional — metrics work without it, M9 just returns None.
- Some metrics (M5, M7) require reliable glyph segmentation, which may not work well on degraded manuscript images.
- Metric thresholds need empirical calibration against human judgment — initial thresholds are guesses.

**Rollback:**
- Revert the branch; metrics are a new independent module.

## Evidence

- [ ] 25 tests in `tests/test_metrics.py` covering identical/different images, all 9 metrics, rating, composite score
- [ ] 284 total ScribeSim tests pass (0 failures)
- [ ] Metrics validated on render-002 snapshot: composite=0.221 (v2 vs v1 baseline — expected divergence from movement/nib/ink changes)
