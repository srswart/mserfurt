# TD-003 Addendum A — Hand Simulator Parameters, Group Optimization, and Training Workflow

## Context
TD-003 is implemented with the parameter architecture, metric suite (M1–M9), manual tuning interface, and single-parameter optimization. This addendum adds three things required by TD-004 and TD-005:
1. New parameters from the hand simulator
2. CMA-ES group optimization (replacing single-parameter adjustment)
3. The incremental training workflow (word → line → folio)

---

## 1. New Parameters (Hand Simulator Dynamics)

Add these to the parameter architecture alongside the existing ~45 parameters:

### Hand dynamics group (~8 new parameters)

```toml
[dynamics]
attraction_strength = { default = 5.0, range = [1.0, 20.0], unit = "force" }
    # How strongly the hand is pulled toward the current target keypoint.
    # Higher = snappier, more precise letters. Lower = looser, more flowing.

damping_coefficient = { default = 2.0, range = [0.5, 8.0], unit = "ratio" }
    # Resistance to movement. Higher = hand decelerates faster after each stroke.
    # Lower = more momentum carries between strokes (more connected feel).

lookahead_strength = { default = 1.5, range = [0.0, 5.0], unit = "force" }
    # How much the next target (2-3 strokes ahead) influences current movement.
    # Higher = smoother transitions, hand plans ahead. Lower = more reactive.

max_speed = { default = 80.0, range = [30.0, 200.0], unit = "mm/s" }
    # Biomechanical speed limit. Affects how quickly the hand traverses
    # connections and how compressed letters become at high tempo.

rhythm_strength = { default = 0.3, range = [0.0, 1.0], unit = "ratio" }
    # How strongly the hand falls into a rhythmic cadence.
    # Higher = more regular stroke timing. Lower = more variable.

target_radius_mm = { default = 0.3, range = [0.1, 1.0], unit = "mm" }
    # How close the hand needs to get to a keypoint before advancing to the next.
    # Larger = looser letterforms, more variation. Smaller = more precise.

contact_threshold = { default = 0.2, range = [0.05, 0.5], unit = "mm" }
    # Nib contact height. Below this distance from the surface, the nib makes a mark.
    # Affects how quickly connections transition from contact to lift and back.

word_lift_height_mm = { default = 3.0, range = [1.0, 8.0], unit = "mm" }
    # How high the hand lifts between words.
    # Higher = more separation, cleaner word boundaries.
    # Lower = hand stays closer to surface, possible ink drag between words.
```

### Letterform guide parameters (~4 new parameters)

```toml
[letterform]
keypoint_flexibility_mm = { default = 0.2, range = [0.05, 0.6], unit = "mm" }
    # Global override for how far from ideal keypoint position is acceptable.
    # Higher = more organic variation. Lower = more precise letterforms.

ascender_height_ratio = { default = 1.6, range = [1.2, 2.2], unit = "x_heights" }
    # Ascender height relative to x-height. Bastarda has tall ascenders.

descender_depth_ratio = { default = 0.5, range = [0.3, 1.0], unit = "x_heights" }
    # Descender depth. Bastarda f and long-s have characteristic long descenders.

x_height_mm = { default = 3.0, range = [1.5, 5.0], unit = "mm" }
    # The fundamental vertical measure. All letterform proportions scale from this.
```

### Updated nib parameters (from TD-004)

```toml
[nib]
# Existing parameters remain, add:
min_hairline_ratio = { default = 0.08, range = [0.03, 0.15], unit = "ratio" }

[stroke]
# New parameters from TD-004 nib fixes:
foot_width_boost = { default = 0.20, range = [0.0, 0.4], unit = "ratio" }
foot_ink_boost = { default = 0.25, range = [0.0, 0.5], unit = "ratio" }
foot_zone_start = { default = 0.85, range = [0.75, 0.95], unit = "ratio" }
attack_width_boost = { default = 0.10, range = [0.0, 0.25], unit = "ratio" }
attack_zone_end = { default = 0.10, range = [0.05, 0.20], unit = "ratio" }
pressure_modulation_range = { default = 0.4, range = [0.1, 0.8], unit = "ratio" }
```

**Total parameter count: ~57** (original ~45 + 12 new)

---

## 2. CMA-ES Group Optimization

### Replacing single-parameter adjustment

The current optimizer adjusts one parameter at a time. This is insufficient for TD-005's hand dynamics, where parameters interact (e.g., attraction_strength and damping_coefficient together determine how the hand moves between keypoints — adjusting one without the other produces worse results).

### Parameter groups

Add to the optimizer configuration:

```toml
[optimizer]
method = "grouped-cma-es"   # replaces "single-parameter"

[optimizer.groups.nib_physics]
description = "Mark-making quality (TD-004)"
parameters = [
    "nib.width_mm", "nib.angle_deg", "nib.flexibility",
    "nib.cut_quality", "nib.min_hairline_ratio",
    "stroke.foot_width_boost", "stroke.foot_ink_boost",
    "stroke.attack_width_boost", "stroke.pressure_modulation_range",
]
target_metrics = ["M1"]
method = "cma-es"
priority = 1   # run first

[optimizer.groups.baseline_geometry]
description = "Page geometry (TD-002)"
parameters = [
    "folio.ruling_slope_variance", "folio.ruling_spacing_variance_mm",
    "folio.margin_left_variance_mm",
    "line.start_x_variance_mm", "line.baseline_undulation_amplitude_mm",
    "line.baseline_undulation_period_ratio", "line.line_spacing_variance_mm",
]
target_metrics = ["M2"]
method = "nelder-mead"
priority = 2

[optimizer.groups.hand_dynamics]
description = "Hand simulator mechanics (TD-005)"
parameters = [
    "dynamics.attraction_strength", "dynamics.damping_coefficient",
    "dynamics.lookahead_strength", "dynamics.max_speed",
    "dynamics.rhythm_strength", "dynamics.target_radius_mm",
]
target_metrics = ["M_conn", "M3", "M7"]
method = "cma-es"
priority = 3

[optimizer.groups.letterform_proportion]
description = "Letter shape and proportion"
parameters = [
    "letterform.keypoint_flexibility_mm", "letterform.ascender_height_ratio",
    "letterform.descender_depth_ratio", "letterform.x_height_mm",
]
target_metrics = ["M6", "M5"]
method = "nelder-mead"
priority = 4

[optimizer.groups.ink_material]
description = "Ink and material interaction (TD-002)"
parameters = [
    "ink.depletion_rate", "ink.fresh_dip_darkness_boost",
    "ink.dry_threshold", "ink.raking_threshold",
    "material.edge_feather_mm", "material.pooling_at_direction_change",
    "material.overlap_darkening_factor",
]
target_metrics = ["M4"]
method = "cma-es"
priority = 5
```

### CMA-ES integration

Add to the optimizer:

```python
# In the optimizer module, add CMA-ES support:
import cma

def optimize_group(group, profile, target, render_fn):
    initial = [profile.get(p) for p in group.parameters]
    bounds = [[profile.range(p)[0] for p in group.parameters],
              [profile.range(p)[1] for p in group.parameters]]
    
    def objective(params):
        trial_profile = profile.copy()
        for p, v in zip(group.parameters, params):
            trial_profile.set(p, v)
        rendered = render_fn(trial_profile, preview=True)
        scores = compute_metrics(rendered, target, subset=group.target_metrics)
        return scores.composite
    
    es = cma.CMAEvolutionStrategy(initial, 0.1, {
        'bounds': bounds,
        'maxiter': 200,
        'popsize': max(12, 4 + int(3 * len(initial))),
    })
    
    while not es.stop():
        candidates = es.ask()
        scores = [objective(c) for c in candidates]
        es.tell(candidates, scores)
    
    best = es.result.xbest
    return {p: v for p, v in zip(group.parameters, best)}
```

### Staged execution

```bash
# Run all groups in priority order with quality gates:
scribesim optimize --staged \
    --target samples/target_manuscript.png \
    --profile shared/hands/konrad_erfurt_1457.toml \
    --output shared/hands/konrad_optimized.toml \
    --gate "M1<0.15,M2<0.15,M_conn<0.20,M3<0.15"
```

---

## 3. Incremental Training Workflow

### New workflow: word → line → folio extension

TD-005's training approach starts with a single word and extends incrementally. This integrates with TD-003's existing comparison and optimization infrastructure:

### New CLI commands

```bash
# Extract a training word from the target manuscript
scribesim extract-word <target.png> --word "und" --line 3 -o training/und.png

# Train hand dynamics on a single word
scribesim train --target training/und.png --text "und" \
    --profile shared/hands/konrad_erfurt_1457.toml \
    --output shared/hands/konrad_trained.toml \
    --method cma-es \
    --max-iterations 500

# Extend to two words with quality gate
scribesim train-extend --text "und der" \
    --profile shared/hands/konrad_trained.toml \
    --target-line samples/target_line.png \
    --gate "M_conn<0.20,M9<0.25" \
    --output shared/hands/konrad_extended.toml

# Extend to full line
scribesim train-extend --text "Der strom des glaubens ist nicht mein eigen" \
    --profile shared/hands/konrad_extended.toml \
    --target-line samples/target_line.png \
    --gate "M1<0.15,M2<0.15,M_conn<0.20" \
    --output shared/hands/konrad_line.toml

# Full folio with line-by-line checkpoints
scribesim train-folio f01r.json \
    --profile shared/hands/konrad_line.toml \
    --target samples/target_folio.png \
    --checkpoint-every-line \
    --revert-threshold 0.05 \  # revert if composite score degrades by >5%
    --output shared/hands/konrad_folio.toml
```

### Quality gate logic

At each extension step:
1. Render with current parameters
2. Compute metrics against target
3. If all gate conditions pass → accept, proceed to next extension
4. If any gate fails → run CMA-ES on the hand_dynamics group with locked nib/baseline params
5. Re-evaluate gates after optimization
6. If still failing after max iterations → flag for human review, do not auto-extend

### Revert mechanism

During folio rendering, per-line checkpoints track parameter drift:

```python
def render_folio_with_checkpoints(folio, profile, target, revert_threshold):
    checkpoints = []
    current_profile = profile.copy()
    
    for line_idx, line in enumerate(folio.lines):
        rendered_line = hand_simulator.render_line(line, current_profile)
        score = compute_line_score(rendered_line, target, line_idx)
        
        if checkpoints and score > checkpoints[-1].score + revert_threshold:
            # Quality degraded — revert to last good checkpoint
            current_profile = checkpoints[-1].profile.copy()
            rendered_line = hand_simulator.render_line(line, current_profile, new_seed=True)
            score = compute_line_score(rendered_line, target, line_idx)
        
        checkpoints.append(Checkpoint(line_idx, score, current_profile.copy()))
    
    return compose_lines(checkpoints)
```

---

## 4. New Metric: M_conn

Add M_conn (from TD-004 Part 2) to the existing M1–M9 suite as M10:

```python
# Add to the metrics module:
def m_conn(rendered, target, baselines_r, baselines_t):
    """Connection quality metric. Measures presence, width, and angle
    of inter-letter connections."""
    r_conns = measure_connections(rendered, baselines_r)
    t_conns = measure_connections(target, baselines_t)
    
    presence = abs(conn_ratio(r_conns) - conn_ratio(t_conns))
    width = wasserstein([c.width for c in r_conns if c.present],
                        [c.width for c in t_conns if c.present])
    angle = wasserstein([c.angle for c in r_conns if c.present],
                        [c.angle for c in t_conns if c.present])
    
    return 0.3 * presence + 0.4 * width + 0.3 * angle
```

Update composite score:
```
composite = w1*M1 + w2*M2 + ... + w9*M9 + w10*M_conn
```

Default weight for M_conn: same as M7 (connection angles). During hand_dynamics training, M_conn weight is doubled.

---

## Summary of changes to existing TD-003 implementation

| Existing feature | Change required |
|---|---|
| Parameter file (TOML) | Add ~12 new parameters (dynamics, letterform, stroke fixes) |
| CLI `--set` overrides | No change — works with new parameters automatically |
| Single-parameter optimizer | Replace with CMA-ES group optimizer (keep single-param as fallback) |
| Metric suite (M1–M9) | Add M_conn as M10 |
| `scribesim compare` | Add M_conn to output |
| `scribesim fit` | Add `--staged` flag, `--gate` conditions, group-based execution |
| Interactive tuning UI | Add sliders for new parameters, group them by optimizer group |
| Parameter presets | No change — presets now include dynamics parameters |
| **New** | `scribesim train` — word-level training command |
| **New** | `scribesim train-extend` — incremental extension with gates |
| **New** | `scribesim train-folio` — folio rendering with line checkpoints |
| **New** | `scribesim extract-word` — extract training targets from manuscripts |
