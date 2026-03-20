# Tech Direction: TD-003 — Parameter Tuning & Manuscript Fitting

## Status
**Proposed** — guides ScribeSim parameter exposure, comparison metrics, and optimization loop.

## Context
TD-002 defines a multi-scale hand model with dozens of parameters across five scales (folio, line, word, glyph, stroke) plus ink and material properties. These parameters need to be:
1. **Exposed** — visible and adjustable at appropriate granularity
2. **Measured** — compared quantitatively against real manuscript samples
3. **Optimizable** — tunable both manually (human eye) and programmatically (fitting algorithm)

The goal is a feedback loop: render → compare against historical sample → adjust → re-render, converging toward output that matches real 15th-century Bastarda as closely as possible.

---

## Part 1: Parameter Architecture

### Parameter hierarchy

Every parameter in the hand model lives at a specific scale and has a defined range, default, and semantic meaning:

```
Parameter {
    id:          String       // e.g. "folio.ruling.slope_variance"
    scale:       Scale        // folio | line | word | glyph | stroke | ink | material
    type:        ParamType    // float | int | angle | mm | ratio
    range:       (min, max)   // valid bounds
    default:     Value        // starting value
    current:     Value        // current value (mutable)
    unit:        String       // "degrees", "mm", "ratio", "strokes", etc.
    description: String       // human-readable
    sensitivity: Float        // how much visual change per unit change (for optimizer step size)
}
```

### Parameter groups (by scale)

**Folio-level** (~8 parameters)
```toml
[folio]
page_rotation_deg = { default = 0.0, range = [-1.0, 1.0], unit = "degrees" }
ruling_slope_variance = { default = 0.003, range = [0.0, 0.01], unit = "radians" }
ruling_spacing_variance_mm = { default = 0.5, range = [0.0, 2.0], unit = "mm" }
margin_left_variance_mm = { default = 0.3, range = [0.0, 1.0], unit = "mm" }
base_pressure = { default = 0.8, range = [0.3, 1.0], unit = "ratio" }
base_tempo = { default = 3.0, range = [1.0, 6.0], unit = "strokes/sec" }
tremor_amplitude = { default = 0.0, range = [0.0, 0.02], unit = "mm" }
lines_per_page = { default = 30, range = [24, 38], unit = "count" }
```

**Line-level** (~6 parameters)
```toml
[line]
start_x_variance_mm = { default = 0.3, range = [0.0, 1.5], unit = "mm" }
baseline_undulation_amplitude_mm = { default = 0.2, range = [0.0, 0.8], unit = "mm" }
baseline_undulation_period_ratio = { default = 0.5, range = [0.2, 1.0], unit = "line_widths" }
margin_compression_zone_ratio = { default = 0.85, range = [0.7, 0.95], unit = "ratio" }
line_spacing_mean_mm = { default = 8.0, range = [5.0, 12.0], unit = "mm" }
line_spacing_variance_mm = { default = 0.3, range = [0.0, 1.0], unit = "mm" }
```

**Word-level** (~6 parameters)
```toml
[word]
spacing_mean_ratio = { default = 1.2, range = [0.6, 2.0], unit = "x_heights" }
spacing_variance_ratio = { default = 0.15, range = [0.0, 0.5], unit = "x_heights" }
slant_drift_per_word_deg = { default = 0.3, range = [0.0, 1.5], unit = "degrees" }
speed_variance = { default = 0.1, range = [0.0, 0.3], unit = "ratio" }
post_punctuation_space_multiplier = { default = 1.4, range = [1.0, 2.5], unit = "ratio" }
slant_reset_at_line_start = { default = true, range = [true, false], unit = "bool" }
```

**Glyph-level** (~8 parameters)
```toml
[glyph]
size_variance = { default = 0.02, range = [0.0, 0.08], unit = "ratio" }
warp_amplitude_mm = { default = 0.1, range = [0.0, 0.4], unit = "mm" }
warp_correlation = { default = 0.7, range = [0.0, 1.0], unit = "ratio" }
ascender_extra_variance = { default = 1.5, range = [1.0, 3.0], unit = "multiplier" }
descender_extra_variance = { default = 1.5, range = [1.0, 3.0], unit = "multiplier" }
baseline_jitter_mm = { default = 0.05, range = [0.0, 0.2], unit = "mm" }
connection_lift_height_mm = { default = 1.5, range = [0.5, 4.0], unit = "mm" }
entry_angle_adaptation = { default = 0.7, range = [0.0, 1.0], unit = "ratio" }
```

**Nib + stroke-level** (~6 parameters)
```toml
[nib]
width_mm = { default = 1.8, range = [0.8, 3.0], unit = "mm" }
angle_deg = { default = 40.0, range = [25.0, 55.0], unit = "degrees" }
flexibility = { default = 0.15, range = [0.0, 0.5], unit = "ratio" }
cut_quality = { default = 0.9, range = [0.5, 1.0], unit = "ratio" }
attack_pressure_multiplier = { default = 1.15, range = [1.0, 1.5], unit = "ratio" }
release_taper_length = { default = 0.3, range = [0.0, 0.8], unit = "ratio" }
```

**Ink-level** (~6 parameters)
```toml
[ink]
reservoir_capacity = { default = 1.0, range = [0.5, 1.5], unit = "ratio" }
depletion_rate = { default = 0.02, range = [0.005, 0.05], unit = "per_stroke" }
fresh_dip_darkness_boost = { default = 0.15, range = [0.0, 0.4], unit = "ratio" }
dry_threshold = { default = 0.15, range = [0.05, 0.3], unit = "ratio" }
raking_threshold = { default = 0.08, range = [0.02, 0.15], unit = "ratio" }
base_color_rgb = { default = [45, 35, 25], range = [[0,0,0], [80,60,40]], unit = "rgb" }
```

**Material-level** (~5 parameters)
```toml
[material]
edge_feather_mm = { default = 0.05, range = [0.0, 0.2], unit = "mm" }
grain_spread_factor = { default = 0.1, range = [0.0, 0.4], unit = "ratio" }
pooling_at_direction_change = { default = 0.2, range = [0.0, 0.6], unit = "ratio" }
overlap_darkening_factor = { default = 0.7, range = [0.3, 1.0], unit = "ratio" }
stroke_start_blob_size = { default = 0.1, range = [0.0, 0.3], unit = "mm" }
```

**Total: ~45 parameters**, organized by scale, all with ranges and defaults.

### Parameter file format

All parameters are stored as a single TOML file (the "hand profile"):

```
shared/hands/konrad_erfurt_1457.toml
```

This file is version-controlled. The optimizer writes candidate profiles to a working directory; the human approves and copies to the canonical location.

---

## Part 2: Comparison Metrics

To tune parameters programmatically, we need to measure the distance between a rendered folio and a real manuscript sample. No single metric captures "looks like a real manuscript," so we use a suite of metrics at different scales.

### Metric suite

**M1: Stroke width distribution**
- Extract stroke widths from both images (rendered and real) using ridge detection
- Compare the distributions (histogram distance or Wasserstein distance)
- Captures: nib angle behavior, pressure variation, thick/thin contrast
- Scale: glyph/stroke level

**M2: Baseline regularity**
- Extract baselines from both images using Kraken or custom line detection
- Measure: per-line slope variance, inter-line spacing variance, left-margin position variance
- Compare distributions
- Captures: ruling imperfection, baseline undulation, line-start drift
- Scale: folio/line level

**M3: Letter spacing rhythm**
- Measure inter-glyph spacing along baselines (using connected-component gaps)
- Compare the autocorrelation function (rhythmic writing has characteristic periodicity)
- Captures: writing rhythm, word spacing consistency
- Scale: line/word level

**M4: Ink density variation**
- Measure mean ink darkness in sliding windows across the page
- Compare the spatial pattern (should show dip cycles — periodic darkening every 30-50 words)
- Captures: ink depletion and reload cycle
- Scale: line/word level

**M5: Glyph shape consistency (within-class variance)**
- For a given letter (e.g., all instances of 'e' on the page), extract bounding boxes
- Compute pairwise shape distance (e.g., Hausdorff distance on skeletonized forms)
- The variance should be nonzero but structured — too low = synthetic, too high = sloppy
- Captures: per-glyph variation, trajectory warping
- Scale: glyph level

**M6: Ascender/descender proportion**
- Measure the ratio of ascender height to x-height across all tall letters
- Compare mean and variance against the real sample
- Captures: letterform proportions specific to Bastarda
- Scale: glyph level

**M7: Connection angle distribution**
- At letter junctions within words, measure the angle of the connecting stroke
- Compare the distribution (Bastarda has characteristic connection angles)
- Captures: inter-letter trajectory quality
- Scale: glyph/word level

**M8: Overall texture (frequency domain)**
- Compute the 2D FFT of a text block from both images
- Compare the power spectra (real manuscripts have characteristic frequency signatures from the interplay of stroke width, letter spacing, and line spacing)
- Captures: holistic "texture" of the page, the thing your eye responds to at a distance
- Scale: folio level

**M9: Perceptual similarity (learned metric)**
- Use a pretrained image feature extractor (e.g., CLIP, DINO, or a VGG perceptual loss network)
- Compute feature distance between rendered and real manuscript crops
- Captures: the "feel" that no single hand-crafted metric covers
- Scale: folio/line level

### Composite score

```
distance(rendered, real) = 
    w1 * M1(rendered, real) +    // stroke width distribution
    w2 * M2(rendered, real) +    // baseline regularity
    w3 * M3(rendered, real) +    // spacing rhythm
    w4 * M4(rendered, real) +    // ink density variation
    w5 * M5(rendered, real) +    // glyph consistency
    w6 * M6(rendered, real) +    // ascender/descender proportion
    w7 * M7(rendered, real) +    // connection angles
    w8 * M8(rendered, real) +    // frequency domain texture
    w9 * M9(rendered, real)      // perceptual similarity
```

Weights are initially equal, then tuned based on which metrics best correlate with human judgment.

---

## Part 3: Manual Tuning Interface

For human-in-the-loop adjustment, ScribeSim provides:

### CLI parameter overrides

```bash
# Render with modified parameters
scribesim render f01r.json -o f01r.png \
    --set folio.ruling_slope_variance=0.005 \
    --set nib.angle_deg=38 \
    --set ink.depletion_rate=0.03

# Render a quick preview (lower DPI, faster)
scribesim preview f01r.json \
    --set line.baseline_undulation_amplitude_mm=0.4

# Diff two renders visually
scribesim diff f01r_v1.png f01r_v2.png -o diff.png
```

### Interactive parameter exploration (React artifact or HTML)

A browser-based tool that renders a representative text block and provides:
- Sliders for each parameter, grouped by scale
- Real-time re-render on parameter change (at reduced resolution for speed)
- Side-by-side: rendered output | real manuscript sample
- Overlay mode: rendered output semi-transparently over real sample
- Metric dashboard: live display of M1-M9 scores as parameters change
- Snapshot: save current parameter state as a named profile
- A/B comparison: toggle between two parameter profiles

### Parameter presets

```bash
# Load a preset, then adjust from there
scribesim render f01r.json --preset bastarda_formal
scribesim render f01r.json --preset bastarda_hasty
scribesim render f01r.json --preset bastarda_fatigued
```

Presets are just named TOML profiles in `shared/hands/presets/`.

---

## Part 4: Automated Optimization (Manuscript Fitting)

The optimizer adjusts parameters to minimize the composite distance metric against a real manuscript target.

### Target preparation

1. **Select reference folios** — 3-5 folios from a real mid-15th-century German Bastarda manuscript, downloaded via IIIF at high resolution
2. **Segment** — extract text blocks, lines, and baselines using Kraken
3. **Extract measurements** — compute M1-M9 metric values for the real folios
4. **Store as target profile** — JSON file with per-metric target values and distributions

### Optimization loop

```
initialize: load default parameter profile
repeat:
    1. render a representative text block using current parameters
    2. compute M1-M9 metrics on the rendered output
    3. compute composite distance to the target profile
    4. if distance < threshold: stop (converged)
    5. compute gradient estimate:
       for each parameter p:
           render with p + epsilon
           compute distance_plus
           render with p - epsilon  
           compute distance_minus
           gradient[p] = (distance_plus - distance_minus) / (2 * epsilon)
    6. update parameters: p = p - learning_rate * gradient[p]
    7. clamp parameters to valid ranges
    8. log iteration: parameters, distance, per-metric scores
```

### Optimization strategy

**Not full gradient descent on all 45 parameters at once.** That's too expensive (each gradient evaluation requires ~90 renders) and the surface is likely non-convex.

Instead, a staged approach:

**Stage 1: Coarse fitting (folio + line level, ~14 parameters)**
- Fix glyph/stroke/ink/material parameters at defaults
- Optimize folio and line parameters against M2 (baseline regularity) and M8 (frequency texture)
- This sets the overall page geometry: line spacing, baseline undulation, margin drift
- Fast: ~28 renders per gradient step, low-resolution preview sufficient

**Stage 2: Nib fitting (~6 parameters)**
- Fix folio/line parameters from Stage 1
- Optimize nib parameters against M1 (stroke width distribution) and M6 (ascender/descender proportion)
- This sets the thick/thin character and letterform proportions
- Medium: ~12 renders per gradient step

**Stage 3: Rhythm fitting (word + glyph, ~14 parameters)**
- Fix folio/line/nib from Stages 1-2
- Optimize word and glyph parameters against M3 (spacing rhythm), M5 (glyph consistency), M7 (connection angles)
- This sets the writing rhythm, variation level, and connection quality
- Medium: ~28 renders per gradient step

**Stage 4: Ink and material fitting (~11 parameters)**
- Fix all geometric parameters from Stages 1-3
- Optimize ink and material parameters against M4 (ink density variation) and per-pixel darkness distribution
- This sets the ink cycle and material interaction quality
- Medium: ~22 renders per gradient step

**Stage 5: Perceptual fine-tuning (all parameters, small steps)**
- Unfreeze all parameters
- Optimize against M9 (perceptual similarity) with very small learning rate
- This is the final polish — adjusting everything together for overall feel
- Expensive but small adjustments: few iterations needed

### Bayesian alternative

For efficiency, replace the numerical gradient with Bayesian optimization (e.g., Gaussian process surrogate):
- Build a surrogate model of the distance function
- Use acquisition function (Expected Improvement) to choose next parameter set to evaluate
- Much more sample-efficient than gradient descent for expensive render evaluations
- Libraries: `botorch` (PyTorch), `scikit-optimize`, or `optuna`

### Human-in-the-loop optimization

The optimizer proposes parameter changes; the human approves or overrides:

```
Optimizer: "Adjusting nib.angle_deg from 40.0 to 37.5 (M1 improved by 12%)"
Human: "Approved"

Optimizer: "Adjusting glyph.warp_amplitude from 0.1 to 0.35 (M5 improved but glyphs look wobbly)"
Human: "Override: set to 0.2"
```

The optimizer logs human overrides and adjusts its model accordingly — if the human consistently overrides a parameter in one direction, the optimizer learns that this parameter has an implicit constraint not captured by the metrics.

---

## Part 5: Comparison Workflow

### Per-folio comparison

```bash
# Compare rendered folio against a real manuscript sample
scribesim compare f01r.png --target samples/bsb_cod_germ_1450_f12r.png --metrics all

# Output:
# M1 stroke_width_dist:    0.12  (good: < 0.15)
# M2 baseline_regularity:  0.34  (needs work: > 0.20)
# M3 spacing_rhythm:       0.08  (good: < 0.10)
# M4 ink_density:          0.45  (needs work: > 0.20)
# M5 glyph_consistency:    0.15  (okay: < 0.20)
# M6 ascender_proportion:  0.09  (good: < 0.10)
# M7 connection_angles:    0.22  (okay: < 0.25)
# M8 frequency_texture:    0.18  (okay: < 0.20)
# M9 perceptual:           0.31  (needs work: > 0.20)
# COMPOSITE:               0.216
```

### Side-by-side visual report

```bash
scribesim report f01r.png --target samples/bsb_cod_germ_1450_f12r.png -o comparison.html
```

Produces an HTML report with:
- Side-by-side images (rendered vs. real) at full and cropped views
- Per-metric scores with visual indicators (green/yellow/red)
- Histogram overlays for distributional metrics (M1, M3, M5)
- Heatmaps showing where the rendered output differs most from the target
- Parameter values used and suggested adjustments

### Run the optimizer

```bash
# Automated fitting against a target manuscript
scribesim fit --target samples/bsb_cod_germ_1450_f12r.png \
    --profile shared/hands/konrad_erfurt_1457.toml \
    --output shared/hands/konrad_fitted_v1.toml \
    --stages coarse,nib,rhythm \
    --max-iterations 50 \
    --log fitting_log.json

# Human-in-the-loop mode
scribesim fit --target samples/bsb_cod_germ_1450_f12r.png \
    --profile shared/hands/konrad_erfurt_1457.toml \
    --interactive \
    --preview-dpi 150
```

---

## Part 6: Integration with ARRIVE

Parameter tuning runs produce advances:

```
ADV-HAND-001: Initial parameter fitting against BSB Cod.germ.XXX
  Objective: Fit folio and line parameters to match baseline regularity of target
  Behavioral change: baseline_undulation_amplitude adjusted 0.2 → 0.35mm
  Evidence: M2 improved from 0.34 to 0.12; visual comparison attached
  
ADV-HAND-002: Nib angle fitting
  Objective: Match thick/thin contrast of target manuscript
  Behavioral change: nib.angle_deg adjusted 40.0 → 37.5
  Evidence: M1 improved from 0.23 to 0.11
```

Each fitting run that produces an accepted parameter change gets an advance recording what changed, why, and the metric evidence.

---

## Implementation priority

1. **Parameter file + CLI overrides** — expose all TD-002 parameters in a TOML file with `--set` overrides. This enables manual tuning immediately.

2. **Metric M2 (baseline regularity)** — the single most impactful metric for the current rendering. Implement line detection on both rendered and real images, compare regularity distributions. This gives us an objective measure of the "lines all start at the same point" problem.

3. **Metric M1 (stroke width distribution)** — second most impactful. Ridge detection + width measurement. Tells us whether the nib model is producing realistic thick/thin.

4. **Comparison CLI** — `scribesim compare` that runs available metrics and produces a score + report.

5. **Staged optimizer (Stages 1-2)** — coarse + nib fitting. Gets the page geometry and thick/thin right.

6. **Interactive tuning UI** — browser-based parameter explorer for human-in-the-loop work.

7. **Full metric suite (M3-M9)** — remaining metrics for rhythm, ink, glyph shape, perceptual.

8. **Bayesian optimizer** — sample-efficient optimization for the full parameter space.

9. **Per-folio CLIO-7 fitting** — separate parameter profiles for emotionally distinct folios (f06r, f07r, f14r).

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Initial draft — parameter architecture, metrics, optimization loop | shawn + claude |
