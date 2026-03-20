# Tech Direction: TD-002 — Physics-Informed Hand Model (Revised)

## Status
**Proposed** — intended to guide ScribeSim scribal hand development.

## Context
The current ScribeSim rendering produces letterforms that look constructed rather than written. Three fundamental problems need to be solved simultaneously:

1. **Movement at multiple scales** — the hand operates at line, word, and glyph level simultaneously, and each scale contributes visible characteristics
2. **Ink-substrate interaction** — ink on vellum is not a uniform paint fill; it wicks, pools, feathers, and depletes
3. **Cumulative imprecision** — a real scribe is precise but never exact; the deviations are structured and compound across the page

## Guiding principle
We are not rendering text. We are simulating a hand holding a quill, moving across a surface, depositing ink. Everything visible on the page should be a consequence of that physical process, not a design choice applied afterward.

---

## Part 1: Multi-Scale Movement Model

Writing is a hierarchical motor act. The scribe's body contributes movement at several nested scales simultaneously. Each scale has its own dynamics, and the final nib position is the sum of all of them.

### Scale 1: Page-level posture

```
PagePosture {
    page_rotation_degrees:   Float    // vellum not perfectly aligned, e.g. 0.3°
    page_rotation_drift:     Float    // drift over the page, e.g. 0.1° total
    vertical_reach_curve:    Fn(line_number) -> Float  // affects baseline straightness
    left_margin_drift:       Float    // mm per line, cumulative
}
```

### Scale 2: Line-level trajectory

```
LineTrajectory {
    baseline_curve:         BézierSegment  // gentle arc, not a straight line
    line_start_x:           Float    // left margin + jitter ±0.5-1.5mm
    line_start_y:           Float    // from ruling + jitter ±0.3mm
    x_height_drift:         Fn(x_position) -> Float
    speed_profile:          Fn(x_position) -> Float
}
```

### Scale 3: Word-level envelope

```
WordEnvelope {
    attack:     Float    // acceleration into the word
    sustain:    Float    // steady-state speed
    release:    Float    // deceleration at word end
    word_baseline_offset:   Float    // ±0.2mm
    spacing_from_context:   Fn(prev_exit, next_entry) -> Float
}
```

Inter-word spacing is NOT uniform — it depends on exit/entry stroke directions.

### Scale 4: Glyph-level trajectory
Each letter as a continuous path with contact and non-contact segments, entry/exit angles, and the nib model producing direction-dependent width.

### Composition

```
nib_position(t) =
    page_posture(line_number)
    + line_trajectory(x_progress)
    + word_envelope(word_progress)
    + glyph_trajectory(glyph_progress)
```

---

## Part 2: The Nib Model

The foundational primitive is a flat nib:

```
Nib {
    width_mm:       Float    // e.g. 1.8mm
    angle_degrees:  Float    // e.g. 40° for Bastarda
    flexibility:    Float    // nib spread under pressure
    cut_quality:    Float    // sharpness (affects hairline thinness)
}
```

Mark width from physics:

```
mark_width(direction, pressure) =
    nib.width * |sin(direction - nib.angle)| * pressure_factor(pressure)
    + nib.width * flexibility * pressure
```

The scribe does NOT choose thick or thin. It emerges from nib angle × stroke direction.

---

## Part 3: Ink-Substrate Interaction Model

The renderer produces two buffers — a coverage buffer and metadata buffers (pressure, speed, direction, ink_load, dwell_time per pixel). These drive post-rendering filters:

### Filter 1: Ink saturation

```
saturation(x, y) =
    base_darkness
    * ink_load(x, y)
    * (1.0 + pressure_boost * pressure(x, y))
    * (1.0 + speed_penalty * (1.0 / speed(x, y)))
```

Slower strokes are darker. Heavy pressure is denser. First words after a dip are richer.

### Filter 2: Ink pooling at stroke terminations
When the nib pauses, ink pools — producing characteristic dark dots at stroke ends.

### Filter 3: Vellum grain wicking
Ink follows the grain structure. Calfskin grain runs roughly vertical. Apply an anisotropic Gaussian blur along grain direction (sigma_along ≈ 0.4px, sigma_across ≈ 0.15px at 400 DPI).

### Filter 4: Hairline feathering
Where less ink meets more absorbent surface, edges break down. Heavy strokes have crisp edges; hairlines have soft, slightly irregular edges.

### Filter 5: Ink depletion cycle
A quill carries ink for ~30–50 words. Depletion follows:

```
ink_remaining(strokes_since_dip) =
    initial_load * (1.0 - (strokes / capacity)^1.5)
```

Visible as periodic darkness rhythm across a page — rich after dip, thinning before next dip, sudden return to richness.

---

## Part 4: Cumulative Imprecision Model

### Ruling marks (with imprecision)

```
RulingLine {
    y_position:     Float    // target
    y_jitter:       Float    // ±0.2mm
    straightness:   Float    // slight bow
    angle:          Float    // ±0.1° from horizontal
}
```

### Baseline wander around ruling

```
written_baseline(x) = ruling_line(x) + low_frequency_noise(
    amplitude = 0.3mm,
    frequency = 0.5/line_width
)
```

### Left margin alignment

```
line_start_x(line_n) =
    target_margin
    + systematic_drift * line_n
    + per_line_jitter
    + first_letter_adjustment
```

### Right margin behavior
The scribe makes real-time decisions: write normally, compress slightly, compress more, hyphenate, or extend into margin. The right margin is ragged in a structured way.

### Inter-line spacing
Follows ruling but not precisely. Slight variation ±0.3mm. Additional space where descenders from line above would collide with ascenders on line below.

---

## Part 5: Rendering Pipeline

### Target resolution
Render at 400 DPI internally, output at 300 DPI.

### Pipeline

```
Stage 1: GEOMETRY
    Page posture → ruling lines (with imprecision) → line trajectories
    → word envelopes → glyph trajectories (with connecting paths)
    Output: complete vector description of every nib position + metadata

Stage 2: RAW RENDERING (Rust)
    Rasterize all nib-contact segments to coverage buffer
    Write metadata buffers (pressure, speed, direction, ink_load, dwell_time)
    Output: coverage + metadata buffers at 400 DPI

Stage 3: INK-SUBSTRATE FILTERS (Rust)
    3a. Ink saturation
    3b. Ink pooling at pause points
    3c. Vellum grain wicking
    3d. Hairline feathering
    3e. Dip cycle visibility
    Output: final ink layer (grayscale, 400 DPI)

Stage 4: COMPOSITING
    Ink layer onto vellum substrate with appropriate blending
    (ink sinks INTO vellum, interacts with texture)
    Output: page image (400→300 DPI)

Stage 5: GROUND TRUTH EXTRACTION
    From Stage 1 geometry (not rendered image)
    Output: PAGE XML with bounding polygons + baselines

Stage 6: PRESSURE HEATMAP
    From Stage 2 pressure buffer
    Output: grayscale PNG for Weather
```

---

## Part 6: Empirical Calibration (Open Questions)

These parameters need measurement from real manuscripts:

| Parameter | Estimate | How to measure |
|---|---|---|
| Baseline wander amplitude | ±0.3mm | Fit lines to baselines on digitized folios, measure deviation |
| Left margin jitter | ±1.0mm | Measure x-coordinate of first letter per line across a page |
| Letter form variance | ~8% | Extract multiple instances of same letter, compute dimensional variance |
| Ink depletion curve exponent | 1.5 | Measure mean darkness in sliding windows across lines — dip cycle appears as periodic signal |
| Dip cycle length | 35 words | Count words between visible darkness peaks |
| Inter-word spacing variance | ~15% | Measure gaps between words across a page |
| Nib angle for German Bastarda | 40° | Reconstruct from width/direction measurements on straight strokes |

### Source manuscripts for calibration
Download 3–5 high-resolution digitized German Bastarda folios (c. 1440–1470) from:
- Bavarian State Library (BSB) via MDZ
- e-codices (Swiss/German manuscripts)
- Universitätsbibliothek Erfurt (if available)
- Gallica (BnF)

Extract measurements programmatically where possible (Kraken segmentation + OpenCV analysis), manually where needed.

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Initial draft | shawn + claude |
| 2026-03-20 | Revised — multi-scale movement, ink-substrate filters, cumulative imprecision, rendering pipeline, calibration plan | shawn + claude |
