# Tech Direction: TD-004 — Nib Physics Fixes, Metrics, and Multi-Parameter Optimization

## Status
**Active (revised)** — prerequisite for TD-005.

## Supersession note
TD-004 was originally titled "Letter Connections, Flow Dynamics, and Multi-Parameter Optimization." The connection architecture (letter-pair connection paths, connection type taxonomy, exit/entry angle system) and flow dynamics (speed-along-word, slant momentum, margin compression) have been **superseded by TD-005** (Generative Hand Model), which produces connections and flow as emergent properties of the hand simulation rather than as constructed systems.

The following parts of TD-004 **remain active** because they address mark-making physics and optimization infrastructure that TD-005 depends on:
- Part 1: Thick/thin contrast fixes (nib physics)
- Part 2: M_conn metric (connection quality measurement)
- Part 3: Multi-parameter group optimization (CMA-ES)

**Implementation order:** TD-004 should be implemented **before** TD-005. The generative hand model uses the nib-angle width equation to produce marks — if the equation isn't producing sufficient contrast, the hand simulator inherits the problem. Fix the mark-making first, then build the hand dynamics on top.

---

## Part 1: Thick/Thin Contrast Fixes (Nib Physics)

### Problem
The nib-angle width equation (TD-002) is implemented but producing insufficient thick/thin contrast. Comparison against the target manuscript shows:
- Target: downstrokes are ~3–5× the width of hairline connectors
- Current: downstrokes are ~1.5× the width of connectors

### Fix A: Minimum hairline floor

The width equation `|sin(direction - nib_angle)|` approaches zero when stroke direction is parallel to nib angle. In reality, even a hairline has some width — the nib edge isn't infinitely thin.

```rust
fn mark_width(direction: f64, nib: &Nib, pressure: f64) -> f64 {
    let direction_factor = (direction - nib.angle).sin().abs();
    let pressure_modulation = 0.8 + 0.4 * pressure; // range: 0.8 to 1.2
    let raw_width = nib.width_mm * direction_factor * pressure_modulation;
    let min_hairline = nib.width_mm * nib.cut_quality * 0.08; // ~8% of full width
    raw_width.max(min_hairline)
}
```

This ensures hairlines are thin but visible — roughly 2–3 pixels at 300 DPI for a 1.8mm nib.

### Fix B: Separate pressure from direction

Pressure should modulate width by ±20%, not dominate it. Direction is the primary driver of thick/thin:

```
direction_width = nib.width * |sin(direction - nib.angle)|      // primary: 0 to 100%
pressure_modulation = 0.8 + 0.4 * pressure                      // secondary: 80% to 120%
mark_width = max(direction_width * pressure_modulation, min_hairline)
```

If pressure is currently multiplied directly (making it a ~0 to 100% factor), reduce its influence to the ±20% modulation range. The nib angle should do most of the work.

### Fix C: Stroke-foot thickening at direction changes

In the target manuscript, downstrokes end with a characteristic thickening or diamond-shaped "foot" where the nib decelerates and changes direction. Three physical causes:
1. The nib slows → more ink per mm
2. The nib rotates slightly at direction change → briefly catches a wider angle
3. Ink pools at the deceleration point

```rust
fn stroke_foot_effect(t: f64, stroke_length: f64) -> (f64, f64) {
    // t = position along stroke (0.0 to 1.0)
    let foot_zone = 0.85; // foot starts at 85% of stroke length
    if t > foot_zone {
        let foot_t = (t - foot_zone) / (1.0 - foot_zone); // 0 to 1 within foot
        let width_boost = 1.0 + 0.2 * (foot_t * PI).sin(); // peaks mid-foot: +20%
        let ink_boost = 1.0 + 0.25 * (foot_t * PI).sin();  // peaks mid-foot: +25%
        (width_boost, ink_boost)
    } else {
        (1.0, 1.0)
    }
}
```

Apply this at the end of every downstroke (strokes where direction is within ±30° of vertical down). The result is the diamond feet visible throughout the target manuscript.

### Fix D: Stroke-start attack thickening

Symmetrically, strokes begin with a slight thickening as the nib presses down (attack). Less dramatic than the foot — roughly +10% width for the first 10% of the stroke:

```rust
fn stroke_attack_effect(t: f64) -> (f64, f64) {
    let attack_zone = 0.10;
    if t < attack_zone {
        let attack_t = t / attack_zone;
        let width_boost = 1.0 + 0.1 * (1.0 - attack_t); // +10% at start, tapering
        let ink_boost = 1.0 + 0.15 * (1.0 - attack_t);   // +15% at start
        (width_boost, ink_boost)
    } else {
        (1.0, 1.0)
    }
}
```

### Fix E: Verify rendering scale

At 300 DPI with a 1.8mm nib:
- Full nib width: 1.8mm × 300/25.4 ≈ **21 pixels**
- Hairline (8% floor): ≈ **1.7 pixels** → rounds to 2px
- Typical downstroke (sin(50°) ≈ 0.77): ≈ **16 pixels**
- Ratio: ~8:1 between full downstroke and hairline

If the rendered ratio is less than 3:1, something is clamping the range. Check:
- Is the nib width being scaled correctly from mm to pixels?
- Is the sin() operating on radians or degrees consistently?
- Is there a global stroke width multiplier reducing the range?

### Parameters exposed (for TD-003 optimizer)

```toml
[nib]
width_mm = { default = 1.8, range = [0.8, 3.0] }
angle_deg = { default = 40.0, range = [25.0, 55.0] }
flexibility = { default = 0.15, range = [0.0, 0.5] }
cut_quality = { default = 0.9, range = [0.5, 1.0] }
min_hairline_ratio = { default = 0.08, range = [0.03, 0.15] }

[stroke]
foot_width_boost = { default = 0.20, range = [0.0, 0.4] }
foot_ink_boost = { default = 0.25, range = [0.0, 0.5] }
foot_zone_start = { default = 0.85, range = [0.75, 0.95] }
attack_width_boost = { default = 0.10, range = [0.0, 0.25] }
attack_zone_end = { default = 0.10, range = [0.05, 0.20] }
pressure_modulation_range = { default = 0.4, range = [0.1, 0.8] }
```

---

## Part 2: M_conn Metric (Connection Quality Measurement)

Even with TD-005's generative hand producing connections as emergent behavior, we need a metric to measure whether connections are emerging correctly. M_conn remains relevant as a training signal for the hand simulator.

### M_conn: Connection presence and quality

1. Segment the rendered image into words (whitespace detection)
2. Within each word, detect inter-letter zones (gaps between major vertical strokes)
3. In each inter-letter zone, measure:
   - **Presence**: is there ink in the connection zone? (boolean)
   - **Width**: how wide is the connecting mark? (should be near hairline)
   - **Angle**: what angle does the connection travel? (should be ~30–50° upward-right for Bastarda)
   - **Continuity**: does the connection smoothly join the preceding and following strokes? (measured by curvature at junction points)
4. Compare distributions against the same measurements on the target manuscript

```python
def measure_connections(image, baselines):
    connections = []
    for line_img, baseline in zip(line_crops, baselines):
        verticals = detect_thick_verticals(line_img)
        for v1, v2 in pairwise(verticals):
            zone = line_img[:, v1.right:v2.left]
            ink_present = zone.mean() < background_threshold
            if ink_present:
                connections.append({
                    'present': True,
                    'width': measure_thin_stroke_width(zone),
                    'angle': measure_stroke_angle(zone),
                    'continuity': measure_junction_curvature(zone, v1, v2),
                })
            else:
                connections.append({'present': False})
    return connections

def m_conn_score(rendered_connections, target_connections):
    # Compare presence ratio
    rendered_ratio = mean([c['present'] for c in rendered_connections])
    target_ratio = mean([c['present'] for c in target_connections])
    presence_score = abs(rendered_ratio - target_ratio)
    
    # Compare width distributions (only for present connections)
    rendered_widths = [c['width'] for c in rendered_connections if c['present']]
    target_widths = [c['width'] for c in target_connections if c['present']]
    width_score = wasserstein_distance(rendered_widths, target_widths)
    
    # Compare angle distributions
    rendered_angles = [c['angle'] for c in rendered_connections if c['present']]
    target_angles = [c['angle'] for c in target_connections if c['present']]
    angle_score = wasserstein_distance(rendered_angles, target_angles)
    
    return 0.3 * presence_score + 0.4 * width_score + 0.3 * angle_score
```

### Integration with TD-003 metric suite

M_conn joins M1–M9 as M10 in the composite score:

```
composite = w1*M1 + w2*M2 + ... + w9*M9 + w10*M_conn
```

For TD-005 training, M_conn receives higher weight during the connection-focused optimization stages.

---

## Part 3: Multi-Parameter Group Optimization (CMA-ES)

The single-parameter-at-a-time optimizer cannot fit interconnected parameters (e.g., nib angle + width + flexibility all affect thick/thin together). Group optimization with CMA-ES solves this.

### Parameter groups

```toml
[optimizer.groups]

[optimizer.groups.nib_physics]
description = "Nib-driven mark-making quality"
parameters = [
    "nib.width_mm",
    "nib.angle_deg",
    "nib.flexibility",
    "nib.cut_quality",
    "nib.min_hairline_ratio",
    "stroke.foot_width_boost",
    "stroke.foot_ink_boost",
    "stroke.attack_width_boost",
    "stroke.pressure_modulation_range",
]
target_metrics = ["M1"]  # stroke width distribution
method = "cma-es"

[optimizer.groups.baseline_geometry]
description = "Page geometry and line positioning"
parameters = [
    "folio.ruling_slope_variance",
    "folio.ruling_spacing_variance_mm",
    "folio.margin_left_variance_mm",
    "line.start_x_variance_mm",
    "line.baseline_undulation_amplitude_mm",
    "line.baseline_undulation_period_ratio",
    "line.line_spacing_variance_mm",
]
target_metrics = ["M2"]  # baseline regularity
method = "nelder-mead"   # small group, no correlations expected

[optimizer.groups.hand_dynamics]
description = "Hand simulator dynamics (TD-005)"
parameters = [
    "dynamics.attraction_strength",
    "dynamics.damping_coefficient",
    "dynamics.lookahead_strength",
    "dynamics.max_speed",
    "dynamics.rhythm_strength",
    "dynamics.base_tempo",
]
target_metrics = ["M_conn", "M3", "M7"]  # connections, rhythm, connection angles
method = "cma-es"  # correlations critical here

[optimizer.groups.ink_material]
description = "Ink depletion and material interaction"
parameters = [
    "ink.depletion_rate",
    "ink.fresh_dip_darkness_boost",
    "ink.dry_threshold",
    "ink.raking_threshold",
    "material.edge_feather_mm",
    "material.pooling_at_direction_change",
    "material.overlap_darkening_factor",
]
target_metrics = ["M4"]  # ink density variation
method = "cma-es"
```

### CMA-ES implementation

```python
import cma

def optimize_group(group, target_metrics, render_fn, max_iterations=200):
    """
    Optimize a parameter group using CMA-ES.
    
    group: parameter group definition (names, ranges, current values)
    target_metrics: pre-computed metric values from the real manuscript
    render_fn: function that renders with given parameters and returns metrics
    """
    initial = group.current_values()
    bounds = [group.min_values(), group.max_values()]
    sigma = group.initial_step_size()  # typically 5-10% of range
    
    def objective(params):
        clamped = group.clamp(params)
        profile = group.apply_to_profile(clamped)
        rendered = render_fn(profile, preview=True)  # low-res for speed
        metrics = compute_metrics(rendered, target_metrics, subset=group.target_metrics)
        return metrics.composite_score
    
    es = cma.CMAEvolutionStrategy(initial, sigma, {
        'bounds': bounds,
        'maxiter': max_iterations,
        'popsize': max(12, 4 + int(3 * len(initial))),  # CMA-ES default population
        'tolx': 1e-4,
        'tolfun': 1e-4,
    })
    
    best_score = float('inf')
    best_params = initial
    
    while not es.stop():
        candidates = es.ask()
        scores = [objective(c) for c in candidates]
        es.tell(candidates, scores)
        
        if min(scores) < best_score:
            best_score = min(scores)
            best_params = candidates[scores.index(best_score)]
            log_improvement(es.countiter, best_score, best_params)
    
    return group.to_named_params(best_params), best_score
```

### Staged optimization pipeline

Execute groups in dependency order:

```
Stage 1: nib_physics          (TD-004 Part 1 — fix mark quality)
    → must pass: M1 < 0.15 (stroke width distribution matches target)
    
Stage 2: baseline_geometry    (TD-002 — fix page geometry)
    → must pass: M2 < 0.15 (baseline regularity matches target)
    
Stage 3: hand_dynamics        (TD-005 — fit the hand simulator)
    → must pass: M_conn < 0.20, M3 < 0.15, M7 < 0.20
    
Stage 4: ink_material         (TD-002 Part 2 — fit ink behavior)
    → must pass: M4 < 0.20
    
Stage 5: full_perceptual      (all groups unlocked, small steps)
    → target: M9 < 0.20 (perceptual similarity)
    → human review after each iteration
```

Each stage freezes parameters from previous stages (unless explicitly unlocked in Stage 5).

---

## Implementation priority

All items in this TD are prerequisites for TD-005:

1. **Nib physics fixes (Fix A–E)** — implement immediately. These improve the current renderer AND are required by the TD-005 hand simulator. Highest impact for lowest effort.

2. **M_conn metric** — implement next. Provides the training signal for TD-005's hand dynamics optimization.

3. **CMA-ES group optimizer** — implement the infrastructure. TD-005's training pipeline depends on this.

4. **Staged optimization pipeline** — wire up the stages. Stage 1 (nib_physics) and Stage 2 (baseline_geometry) can run against the current renderer. Stage 3 (hand_dynamics) requires TD-005.

---

## Dependency chain

```
TD-002 (nib model, multi-scale concepts)
  ↓
TD-004 (nib physics fixes, M_conn, CMA-ES groups)  ← YOU ARE HERE
  ↓
TD-005 (generative hand model, motor programs, training)
  ↓
TD-003 (full parameter tuning, all metrics, interactive UI)
```

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Original: connections, flow, optimization | shawn + claude |
| 2026-03-20 | Revised: connection architecture superseded by TD-005; retained nib fixes, M_conn, CMA-ES as prerequisites | shawn + claude |
