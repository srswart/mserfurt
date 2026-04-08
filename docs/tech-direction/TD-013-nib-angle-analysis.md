# Tech Direction: TD-013 — Nib Angle Analysis in the Annotation Workbench

## Status
**Active** — extends the Annotation Workbench glyph decomposition (TD-012 Addendum B).

## Context
The current nib model assumes a fixed angle (40°) throughout all strokes. But a real scribe's nib angle drifts during writing — the wrist rolls slightly during curved strokes, the hand adjusts between different stroke types, and there's a subtle but measurable difference between the nib angle on a downstroke versus a horizontal connector.

This drift is visible in the ink. At every point along a stroke, the width encodes the relationship between stroke direction and nib angle. Where the width doesn't match what a fixed angle would predict, the angle must have changed. We can solve for the angle at every point and present it to the operator as an editable track alongside the Bézier path and pressure profile.

This produces per-stroke nib angle profiles that, when fed into the rendering pipeline, reproduce the exact thick/thin pattern of the original manuscript — not an approximation from a fixed angle, but the actual angle variation the scribe's hand produced.

---

## Part 1: The Physics

### The nib-angle-width equation (from TD-002/004)

```
mark_width = nib_width × |sin(stroke_direction - nib_angle)| × pressure
```

At any point along a stroke, we know or can measure:
- **mark_width**: measured from the glyph crop (distance transform of the ink)
- **stroke_direction**: computed from the Bézier tangent at that point
- **pressure**: estimated from TD-012 Addendum B decomposition (or assumed ~0.7 for initial analysis)

The **nib_angle** is the unknown. Solving:

```
|sin(stroke_direction - nib_angle)| = mark_width / (nib_width × pressure)

nib_angle = stroke_direction - arcsin(mark_width / (nib_width × pressure))
```

There are two solutions (the arcsin has two branches) — we pick the one closest to the expected baseline nib angle (~40° for Bastarda).

### Why this works on curves

On a straight downstroke, the direction is constant (~270° or -90°) so the width is constant and reveals one nib angle. Not very informative.

On a **curved stroke** like the 'd' bowl, the direction rotates continuously through a wide range of angles. At each point, the width changes because the direction-vs-nib relationship changes. This continuous variation provides many independent measurements of the nib angle. If the nib angle is truly fixed, all measurements agree. If the nib angle drifts during the stroke, the measurements show the drift.

Curved strokes are the most informative — they sweep through enough directional range to fully constrain the nib angle. Straight strokes provide less information but still contribute to the overall estimate.

---

## Part 2: The Analysis Algorithm

### Per-point nib angle estimation

```rust
fn estimate_nib_angles(
    bezier_segments: &[BezierSegment],
    measured_widths: &[f64],         // from distance transform
    nib_width_mm: f64,               // estimated or calibrated
    assumed_pressure: &[f64],        // from Addendum B or uniform
    baseline_angle_deg: f64,         // expected angle (~40° for Bastarda)
) -> NibAngleProfile {
    let n_samples = measured_widths.len();
    let mut angles = Vec::with_capacity(n_samples);
    let mut confidences = Vec::with_capacity(n_samples);
    
    for i in 0..n_samples {
        let t = i as f64 / (n_samples - 1) as f64;
        
        // Stroke direction at this point (tangent to Bézier)
        let tangent = evaluate_tangent(bezier_segments, t);
        let direction = tangent.angle();  // radians
        
        // Measured width at this point
        let width = measured_widths[i];
        let pressure = assumed_pressure[i];
        
        // Solve for nib angle
        let sin_value = width / (nib_width_mm * pressure);
        
        if sin_value > 1.0 {
            // Width exceeds what the nib model can produce — 
            // either pressure is underestimated or there's ink pooling
            angles.push(baseline_angle_deg.to_radians());
            confidences.push(0.2);  // low confidence
            continue;
        }
        
        if sin_value < 0.05 {
            // Very thin stroke — near-parallel to nib
            // Angle is well-determined (it's close to the direction)
            angles.push(direction);
            confidences.push(0.7);
            continue;
        }
        
        let arcsin_val = sin_value.asin();
        
        // Two candidate angles
        let candidate_a = direction - arcsin_val;
        let candidate_b = direction - (std::f64::consts::PI - arcsin_val);
        
        // Pick the one closest to the baseline expectation
        let baseline_rad = baseline_angle_deg.to_radians();
        let angle = if angle_distance(candidate_a, baseline_rad) 
                     < angle_distance(candidate_b, baseline_rad) {
            candidate_a
        } else {
            candidate_b
        };
        
        // Confidence based on how much information this measurement provides
        // High confidence when sin_value is in the mid-range (0.3-0.7)
        // Low confidence at extremes (near 0 or near 1)
        let info_content = 1.0 - (2.0 * sin_value - 1.0).powi(2);  // peaks at 0.5
        confidences.push(info_content);
        
        angles.push(angle);
    }
    
    // Smooth the angle profile to remove noise
    let smoothed = gaussian_smooth(&angles, &confidences, sigma: 3.0);
    
    NibAngleProfile {
        raw_angles: angles,
        smoothed_angles: smoothed,
        confidences,
        baseline_angle: baseline_angle_deg,
    }
}
```

### Confidence weighting

Not all points along a stroke are equally informative about the nib angle:

- **High confidence:** where the stroke direction is at a moderate angle to the nib (~20-70° from the nib angle). The width varies rapidly with small angle changes, so the measurement is precise.
- **Low confidence:** where the stroke is nearly parallel to the nib (thin hairline) or nearly perpendicular (maximum width). At these extremes, small width measurement errors produce large angle errors.
- **Very low confidence:** where the measured width exceeds the theoretical maximum (ink pooling, measurement artifact) or is at the minimum hairline floor.

The Workbench uses confidence to determine visual prominence — high-confidence angle estimates are shown as solid indicators, low-confidence ones are faded.

---

## Part 3: Global Scribe Angle Estimation

### Across all strokes in the library

After analyzing many strokes from the same scribe, compute the global baseline nib angle:

```rust
fn estimate_global_nib_angle(
    all_stroke_profiles: &[NibAngleProfile],
) -> GlobalNibAngle {
    // Collect all high-confidence angle measurements
    let mut weighted_angles = Vec::new();
    
    for profile in all_stroke_profiles {
        for (angle, confidence) in profile.smoothed_angles.iter()
            .zip(profile.confidences.iter()) 
        {
            if *confidence > 0.5 {
                weighted_angles.push((*angle, *confidence));
            }
        }
    }
    
    // Weighted circular mean (angles wrap around)
    let global_angle = circular_weighted_mean(&weighted_angles);
    
    // Variance — how much does the angle drift?
    let variance = circular_weighted_variance(&weighted_angles, global_angle);
    
    // Per-stroke-type breakdown
    let downstroke_angles = collect_angles_by_type(all_stroke_profiles, StrokeType::Down);
    let curve_angles = collect_angles_by_type(all_stroke_profiles, StrokeType::Curve);
    let horizontal_angles = collect_angles_by_type(all_stroke_profiles, StrokeType::Horizontal);
    
    GlobalNibAngle {
        baseline_deg: global_angle.to_degrees(),
        variance_deg: variance.to_degrees(),
        
        // Per stroke type (reveals systematic angle changes)
        downstroke_mean_deg: circular_mean(&downstroke_angles).to_degrees(),
        curve_mean_deg: circular_mean(&curve_angles).to_degrees(),
        horizontal_mean_deg: circular_mean(&horizontal_angles).to_degrees(),
        
        n_measurements: weighted_angles.len(),
    }
}
```

### What the global analysis reveals

For a typical Bastarda scribe:

```
Global baseline:      40.2°  (±2.1°)
On downstrokes:       39.8°  (the hand is most controlled — closest to baseline)
On curves:            41.5°  (slight roll during curved strokes)
On horizontals:       38.0°  (hand flattens slightly for crossbars)
```

This tells us the scribe's nib angle isn't truly fixed — it shifts systematically by stroke type. The rendering pipeline can model this: instead of a single `nib_angle = 40°`, use a per-stroke-type angle that matches the scribe's actual behavior.

---

## Part 4: Nib Width Estimation

### Solving for nib width simultaneously

If we don't know the nib width precisely, we can estimate it alongside the angle. Across all measurements:

```rust
fn estimate_nib_width(
    all_widths: &[f64],           // measured mark widths
    all_directions: &[f64],       // stroke directions
    all_pressures: &[f64],        // estimated pressures
    initial_angle_estimate: f64,  // from global analysis
) -> f64 {
    // At the thickest points (where direction ⊥ nib angle),
    // width ≈ nib_width × pressure
    // So nib_width ≈ max_width / max_pressure (approximately)
    
    // More precisely: find the measurements where |sin(dir - angle)| is highest
    let perpendicular_measurements: Vec<f64> = all_widths.iter()
        .zip(all_directions.iter())
        .zip(all_pressures.iter())
        .filter(|((_, dir), _)| {
            (*dir - initial_angle_estimate).sin().abs() > 0.85
        })
        .map(|((width, _), pressure)| {
            width / pressure  // nib_width estimate from this measurement
        })
        .collect();
    
    if perpendicular_measurements.is_empty() {
        return 1.5;  // fallback default (mm)
    }
    
    // Use the 90th percentile rather than max (more robust to outliers)
    percentile(&perpendicular_measurements, 90.0)
}
```

---

## Part 5: Workbench UI

### Nib angle track in the stroke editor

The nib angle analysis adds a new track below the pressure track in the stroke decomposition view:

```
┌──────────────────────────────────────────────────────────────────┐
│  Glyph: 'd' from "der" (Cgm 597, f85v)                         │
│                                                                  │
│  ┌────────────────────────┐   ┌────────────────────────┐        │
│  │                        │   │                        │        │
│  │    [glyph crop]        │   │  [strokes + angle      │        │
│  │                        │   │   indicators overlaid]  │        │
│  └────────────────────────┘   └────────────────────────┘        │
│                                                                  │
│  Stroke 1: bowl_curve                                            │
│  ┌──────────────────────────────────────────────────────┐        │
│  │ Pressure: ▃▅▇██▇▅▃▂                                 │        │
│  │           0.3 → 0.85 → 0.35                          │        │
│  ├──────────────────────────────────────────────────────┤        │
│  │ Nib angle: ▅▅▅▆▆▇▇▆▅                                │        │
│  │            38° → 43° → 40°                           │        │
│  │            [confidence: ░░▓▓████▓▓░░]                │        │
│  ├──────────────────────────────────────────────────────┤        │
│  │ Width:    ▂▃▅▇██▇▅▃                                  │        │
│  │           measured from ink                           │        │
│  └──────────────────────────────────────────────────────┘        │
│                                                                  │
│  Stroke 2: ascender                                              │
│  ┌──────────────────────────────────────────────────────┐        │
│  │ Pressure: ▅▇██▇▅▃▂                                   │        │
│  │           0.5 → 0.9 → 0.3                             │        │
│  ├──────────────────────────────────────────────────────┤        │
│  │ Nib angle: ▅▅▅▅▅▅▅▅                                   │        │
│  │            39° → 40° → 39°  (stable — straight stroke)│        │
│  │            [confidence: ░░░▓▓▓░░░]                     │        │
│  └──────────────────────────────────────────────────────┘        │
│                                                                  │
│  Global scribe angle: 40.2° (±2.1°)                             │
│  This glyph: 39.5° mean                                         │
│                                                                  │
│  Controls:                                                       │
│  • Click angle track to select → drag to adjust angle at point   │
│  • Shift+click to pin angle at a point (locks it during solve)   │
│  • 'F' key to flatten (set uniform angle across stroke)          │
│  • 'G' key to set to global baseline angle                       │
│  • Double-click to re-solve pressure given adjusted angle        │
│                                                                  │
│  [ Accept ]  [ Re-analyze ]  [ Use Fixed Angle ]                 │
│                                                                  │
│  Preview: ┌────────────────┐                                     │
│           │  rendered 'd'  │ ← updates live with angle changes   │
│           └────────────────┘                                     │
│  Match score: 0.91                                               │
└──────────────────────────────────────────────────────────────────┘
```

### Nib angle overlay on the glyph crop

On the glyph image itself, show small angle indicators at sample points along each stroke:

```
        ╲  ← nib angle indicator (short line at 40°)
     ╲
  ╲        The line shows the nib orientation at that point.
     ╲     Where it's consistent: all lines are parallel.
        ╲  Where the angle drifts: lines visibly rotate.
```

These are small (3-5px) line segments drawn at the estimated nib angle, colored by confidence:
- **Orange/solid:** high confidence (the measurement strongly determines the angle)
- **Gray/faded:** low confidence (the measurement is ambiguous)

The operator can instantly see whether the nib angle is stable (all indicators parallel) or drifting (indicators rotating along the stroke).

### Interactive angle adjustment

The operator can adjust the nib angle at any point:

```rust
fn on_angle_drag(stroke_idx: usize, sample_idx: usize, new_angle: f64) {
    // Update the nib angle at this point
    stroke_profiles[stroke_idx].angles[sample_idx] = new_angle;
    
    // Re-solve pressure at this point given the new angle
    // (angle and pressure are coupled through the width equation)
    let direction = stroke_directions[stroke_idx][sample_idx];
    let width = measured_widths[stroke_idx][sample_idx];
    let sin_val = (direction - new_angle).sin().abs();
    let new_pressure = width / (nib_width * sin_val);
    stroke_profiles[stroke_idx].pressures[sample_idx] = new_pressure.clamp(0.1, 1.0);
    
    // Smooth the angle and pressure profiles around the edited point
    smooth_local(&mut stroke_profiles[stroke_idx].angles, sample_idx, radius: 3);
    smooth_local(&mut stroke_profiles[stroke_idx].pressures, sample_idx, radius: 3);
    
    // Update live preview
    update_preview();
}
```

When the operator drags the angle at one point, the pressure at that point is automatically recalculated to maintain consistency with the measured width. The live preview updates immediately, showing whether the angle adjustment produces a better match to the original ink.

### The "re-solve" loop

Angle and pressure are coupled — changing one affects the other. The Workbench supports iterative refinement:

1. **Initial analysis:** estimate angles assuming uniform pressure (~0.7)
2. **Operator adjusts angles** where they look wrong → pressure recalculates
3. **Operator adjusts pressure** where it looks wrong → angles recalculate
4. **Converges** after 1-2 adjustments to a consistent angle+pressure profile

```rust
fn re_solve_from_angles(
    measured_widths: &[f64],
    stroke_directions: &[f64],
    current_angles: &[f64],
    nib_width: f64,
) -> Vec<f64> {
    // Given fixed angles, solve for pressure at each point
    measured_widths.iter()
        .zip(stroke_directions.iter())
        .zip(current_angles.iter())
        .map(|((&width, &dir), &angle)| {
            let sin_val = (dir - angle).sin().abs().max(0.05);
            (width / (nib_width * sin_val)).clamp(0.1, 1.0)
        })
        .collect()
}

fn re_solve_from_pressures(
    measured_widths: &[f64],
    stroke_directions: &[f64],
    current_pressures: &[f64],
    nib_width: f64,
    baseline_angle: f64,
) -> Vec<f64> {
    // Given fixed pressures, solve for angles at each point
    measured_widths.iter()
        .zip(stroke_directions.iter())
        .zip(current_pressures.iter())
        .map(|((&width, &dir), &pressure)| {
            let sin_val = (width / (nib_width * pressure)).clamp(0.0, 1.0);
            let arcsin_val = sin_val.asin();
            let candidate_a = dir - arcsin_val;
            let candidate_b = dir - (std::f64::consts::PI - arcsin_val);
            if angle_distance(candidate_a, baseline_angle) 
               < angle_distance(candidate_b, baseline_angle) {
                candidate_a
            } else {
                candidate_b
            }
        })
        .collect()
}
```

---

## Part 6: Storing Per-Stroke Nib Angle in the Allograph Genome

The allograph genome gains a per-segment nib angle profile:

```rust
struct BezierSegment {
    p0: Vec2,
    p1: Vec2,
    p2: Vec2,
    p3: Vec2,
    contact: bool,
    pressure: Vec<f64>,          // existing: pressure at N sample points
    nib_angle: Vec<f64>,         // NEW: nib angle (radians) at N sample points
    nib_angle_confidence: Vec<f64>, // NEW: confidence per sample
}
```

During rendering, instead of using a fixed nib angle:

```rust
// BEFORE (fixed angle):
let mark_width = nib_width * (direction - NIB_ANGLE_FIXED).sin().abs() * pressure;

// AFTER (per-point angle from allograph):
let local_nib_angle = segment.nib_angle[sample_idx];
let mark_width = nib_width * (direction - local_nib_angle).sin().abs() * pressure;
```

This means each allograph renders with its own measured nib angle variation — the exact thick/thin pattern from the original manuscript, not an approximation.

---

## Part 7: Modes of Operation

The Workbench supports three modes for nib angle handling, selectable per glyph:

### Mode 1: Fixed angle (simplest)
Use the global baseline angle for all points. Fast, no analysis needed. Appropriate for initial passes or when the stroke is too short/straight to provide angle information.

```
[Use Fixed Angle: 40.2°]
```

### Mode 2: Auto-analyzed (recommended)
DP analysis proposes per-point angles from measured widths. Operator reviews the angle track and accepts or nudges. Appropriate for most glyphs.

```
[Auto-Analyze] → review angle track → [Accept] or [Nudge]
```

### Mode 3: Manual specification (rare)
Operator directly draws or specifies the nib angle at key points, and the system interpolates between them. Appropriate for unusual strokes or when the auto-analysis fails (damaged ink, overlapping strokes).

```
[Manual] → click to place angle pins → system interpolates
```

---

## Part 8: Calibration Workflow

### First-time setup for a new manuscript

When starting with a new reference manuscript, the nib parameters (angle, width) are unknown. The calibration workflow:

1. **Annotate 5-10 glyphs** with good curved strokes ('d', 'o', 'a', 'g', 'e') — these provide the most angle information
2. **Run global angle estimation** across these glyphs → establishes baseline angle and nib width
3. **Review the global estimates** — does 40.2° look right for this manuscript? Does the nib width match visual inspection?
4. **Adjust if needed** — the operator can override the global estimates
5. **Subsequent glyphs use the calibrated baseline** as the starting point for per-stroke analysis

```bash
# Calibration command
scribesim calibrate-nib \
    --glyphs reference/annotated/d_001.toml reference/annotated/o_001.toml ... \
    --output shared/hands/nib_calibrated.toml

# Output:
# nib.angle_deg = 40.2
# nib.width_mm = 1.35
# nib.angle_variance_deg = 2.1
# nib.downstroke_angle_deg = 39.8
# nib.curve_angle_deg = 41.5
# nib.horizontal_angle_deg = 38.0
```

---

## Relationship to Other TDs

- **TD-012 Addendum B:** the stroke decomposition proposes Bézier segments and pressure profiles. TD-013 adds the nib angle dimension — after strokes are decomposed, the angle analysis runs on each stroke.
- **TD-004:** the nib physics equation is the foundation. TD-013 inverts it — instead of angle→width, we solve width→angle.
- **TD-008:** evolutionary extraction is the alternative path. TD-013's analysis can seed the evolution with better initial angles, or replace it entirely for well-analyzed glyphs.
- **TD-010:** the ink cycle affects measured widths (ink depletion makes strokes thinner). The analysis should account for ink state when interpreting width measurements — a thin stroke might be thin because of angle OR because of low ink. The confidence score is lower when the glyph comes from a likely low-ink region.

---

## Implementation Priority

1. **Per-point angle estimation from width/direction** — the core math. Implement and test on the 'd' bowl crop from Cgm 597.

2. **Confidence scoring** — identify which measurements are informative and which are ambiguous.

3. **Global scribe angle estimation** — aggregate across multiple glyphs to establish the baseline.

4. **Workbench angle track UI** — display the angle profile below the pressure track, with confidence coloring and drag-to-adjust interaction.

5. **Nib angle overlay on glyph** — small angle indicator lines at sample points on the glyph image.

6. **Re-solve loop** — angle↔pressure coupling with live preview updates.

7. **Store per-stroke angle in allograph genome** — extend the genome format and update the renderer.

8. **Nib width estimation** — solve for nib width alongside angle from perpendicular stroke measurements.

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-28 | Initial draft — nib angle analysis in Annotation Workbench | shawn + claude |
