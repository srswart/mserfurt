# Tech Direction: TD-006 — Constrained Dynamics and Anticipatory Motor Planning

## Status
**Active** — immediate implementation guide. Fixes the chaotic output from TD-005's initial implementation.

## Context
TD-005's generative hand model produces chaotic, tangled output. Root cause: attraction/damping balance is too loose, allowing the hand to overshoot targets and oscillate. The hand has too much freedom and not enough constraint.

This TD defines two phases:
1. **Clamp down:** constrain the hand tightly to produce legible, precise output
2. **Sliding window motor planning:** add anticipatory path planning that models how a trained scribe's muscle memory works

Phase 1 is implemented first and must produce legible output before Phase 2 begins.

---

## Phase 1: Clamp Down

### The problem quantified

Current dynamics produce:
- Target overshoot: hand passes through keypoints and loops back (~3-5mm overshoot)
- Path crossing: strokes overlap themselves creating tangled knots
- Uncontrolled descenders: vertical strokes plunge far below baseline
- Contact during lifts: ink marks appear during what should be air transitions

### Parameter changes (immediate)

Replace the current TD-005 dynamics defaults with clamped values:

```toml
[dynamics]
# CLAMPED VALUES — start precise, loosen later
attraction_strength = 25.0     # was 5.0 — much stronger pull toward target
damping_coefficient = 12.0     # was 2.0 — much higher resistance, kills oscillation
lookahead_strength = 0.5       # was 1.5 — reduced until basic steering works
max_speed = 40.0               # was 80.0 — halved, prevents overshoot
rhythm_strength = 0.1          # was 0.3 — reduced, let precision come first
target_radius_mm = 0.15        # was 0.3 — tighter, hand must get closer before advancing
contact_threshold = 0.08       # was 0.2 — much tighter, prevents ink during lifts
word_lift_height_mm = 5.0      # was 3.0 — higher lift, cleaner word separation
```

### Why these specific values

**attraction = 25, damping = 12:** These values produce *critically damped* or *slightly overdamped* behavior. The hand moves toward each target quickly but decelerates smoothly without oscillation. Like a closing door with a good hydraulic closer — it arrives precisely without bouncing.

The ratio matters: `damping² / (4 * attraction)` determines the damping regime:
- `< 1`: underdamped (oscillates) — this is the current problem
- `= 1`: critically damped (fastest arrival without overshoot)
- `> 1`: overdamped (arrives slowly, no overshoot)

With attraction=25, damping=12: `144 / 100 = 1.44` — slightly overdamped. The hand arrives at each target cleanly, perhaps a touch slowly. This is exactly what we want as a starting point.

**max_speed = 40:** At the current 80mm/s, the hand builds momentum that the damping can't absorb in time. At 40mm/s, the hand moves at a controlled pace. A real scribe writing carefully moves the nib at roughly 20-60mm/s depending on the stroke.

**target_radius = 0.15mm:** The hand must get within 0.15mm of a keypoint before advancing to the next. At 300 DPI, 0.15mm ≈ 1.8 pixels. This forces precision — the hand can't skip past a keypoint on momentum.

**contact_threshold = 0.08mm:** The nib must be within 0.08mm of the surface to leave a mark. This eliminates the "inking during lifts" problem. When the hand lifts between strokes, it rises above this threshold and no mark is made.

### Additional constraint: velocity gate at keypoint transition

Before advancing to the next keypoint, check that the hand has sufficiently decelerated:

```rust
fn should_advance_target(state: &HandState) -> bool {
    let distance = (state.position - state.current_target).length();
    let speed = state.velocity.length();
    
    // Must be close enough AND slow enough
    distance < state.target_radius 
        && speed < state.max_speed * 0.3  // must be below 30% of max speed
}
```

This prevents the hand from blowing through a keypoint at full speed and advancing while still carrying momentum that will cause overshoot at the next target.

### Additional constraint: path bounding box

Each letter has an expected bounding box (from the letterform guide). If the hand's position ever exits this box by more than a tolerance, clamp it back:

```rust
fn clamp_to_letter_bounds(state: &mut HandState, current_letter: &LetterformGuide) {
    let bounds = current_letter.bounding_box(state.baseline_y, state.x_advance_position);
    let tolerance = 0.5; // mm — allow slight overshoot but not wild deviation
    let expanded = bounds.expand(tolerance);
    
    if !expanded.contains(state.position) {
        // Clamp position to expanded bounds
        state.position = expanded.clamp(state.position);
        // Kill velocity component that was taking us out of bounds
        state.velocity = reflect_velocity_at_boundary(state.velocity, expanded, state.position);
    }
}
```

This is a safety net that prevents the tangling problem entirely. Even if the dynamics are slightly off, the hand can't wander more than 0.5mm outside the expected letter boundary.

### Expected result after Phase 1

The output should look like the old glyph-placement renderer but with:
- Slightly softer, more natural curves (the hand steers smoothly, not mechanically)
- Subtle position variation at each keypoint (arriving within 0.15mm, not at the exact point)
- Clean lifts between strokes (no ink during transitions)
- No overshooting, no tangling, no path crossing

It might look too precise — almost typeface-like. That's fine. We have a legible foundation.

---

## Phase 2: Anticipatory Motor Planning (Sliding Window)

### The scribe's muscle memory

A trained scribe doesn't react to one keypoint at a time. Their motor system holds a plan for the next several strokes and executes the beginning of that plan while continuously updating it as new information enters awareness. This is called a **receding horizon** in control theory, or a **sliding window** in the motor planning literature.

For Brother Konrad, who has been writing for 30 years, the window extends roughly one word ahead. When he's writing "und", his hand is executing the first stroke of 'u' while already planning the path through 'n' and 'd'. The plan subtly shapes every stroke — the downstroke of 'u' is angled slightly differently than it would be if 'u' were the last letter, because the hand is already setting up to flow into 'n'.

### The sliding window model

At every timestep, the hand holds a window of upcoming keypoints and computes a smooth planned path through them:

```
SlidingWindow {
    window_size:     Int        // number of keypoints visible to the planner (6-8)
    plan:            PlannedPath // smooth curve through all keypoints in window
    plan_cursor:     Float      // where along the plan the hand currently is (0.0 to 1.0)
    replan_interval: Int        // how often to recompute the plan (every N timesteps)
}
```

### Path planning algorithm

The planned path is a smooth curve that passes through (or near) all keypoints in the window, respecting the dynamics constraints:

```rust
fn plan_path(window: &[Keypoint], hand_state: &HandState) -> PlannedPath {
    // Start from current hand position and velocity
    let start = PathNode {
        position: hand_state.position,
        velocity: hand_state.velocity,
    };
    
    // Build a sequence of nodes from the keypoints
    let mut nodes = vec![start];
    for kp in window {
        nodes.push(PathNode {
            position: kp.position,
            velocity: estimate_velocity_at_keypoint(kp, window),
        });
    }
    
    // Fit a smooth spline through all nodes
    // Using Catmull-Rom or cubic Hermite interpolation:
    // - passes through each node's position
    // - matches each node's velocity direction (not magnitude)
    // - minimizes total curvature (smoothest possible path)
    let spline = fit_hermite_spline(&nodes);
    
    // Apply speed profile along the spline:
    // - slower at sharp turns (nib needs to change direction)
    // - faster on straight segments
    // - decelerate approaching keypoints
    let speed_profile = compute_speed_profile(&spline, hand_state.base_tempo);
    
    PlannedPath { spline, speed_profile }
}

fn estimate_velocity_at_keypoint(kp: &Keypoint, window: &[Keypoint]) -> Vec2 {
    // Estimate the velocity the hand should have at this keypoint
    // based on where it came from and where it's going
    let prev = find_previous_keypoint(kp, window);
    let next = find_next_keypoint(kp, window);
    
    if let (Some(p), Some(n)) = (prev, next) {
        // Velocity direction is the average of incoming and outgoing directions
        let in_dir = (kp.position - p.position).normalized();
        let out_dir = (n.position - kp.position).normalized();
        let avg_dir = (in_dir + out_dir).normalized();
        
        // Speed depends on how sharp the turn is
        let turn_angle = in_dir.angle_between(out_dir).abs();
        let speed = if kp.contact {
            // On-surface: slow down for sharp turns
            hand_state.base_tempo * (1.0 - 0.6 * (turn_angle / PI))
        } else {
            // Lifted: can move faster through air
            hand_state.base_tempo * 1.5
        };
        
        avg_dir * speed
    } else {
        Vec2::ZERO
    }
}
```

### How the plan influences the hand

Instead of the hand being attracted directly to the next keypoint (TD-005), it follows the planned path:

```rust
fn hand_step_with_plan(state: &mut HandState, window: &SlidingWindow, dt: f64) {
    // Where should the hand be right now according to the plan?
    let plan_position = window.plan.position_at(window.plan_cursor);
    let plan_velocity = window.plan.velocity_at(window.plan_cursor);
    
    // Attraction toward the plan (not toward the raw keypoint)
    let position_error = plan_position - state.position;
    let velocity_error = plan_velocity - state.velocity;
    
    // PD controller: proportional (position) + derivative (velocity) control
    // This is how real motor control works — the brain corrects both
    // where the hand IS and how fast it's MOVING
    let correction = position_error * POSITION_GAIN + velocity_error * VELOCITY_GAIN;
    
    // Apply biomechanical limits
    let clamped_correction = correction.clamp_length(MAX_ACCELERATION);
    
    // Update hand state
    state.acceleration = clamped_correction;
    state.velocity += state.acceleration * dt;
    state.velocity = state.velocity.clamp_length(state.max_speed);
    state.position += state.velocity * dt;
    
    // Advance plan cursor based on distance traveled
    window.plan_cursor += (state.velocity.length() * dt) / window.plan.total_length();
    
    // Emit mark if nib is in contact
    if state.nib_contact && state.nib_height < state.contact_threshold {
        let mark_width = compute_nib_width(
            state.velocity.angle(), 
            state.nib_angle, 
            state.nib_pressure
        );
        emit_mark(state.position, mark_width, state.ink_state);
    }
    
    // Replan periodically as new keypoints enter the window
    state.steps_since_replan += 1;
    if state.steps_since_replan >= window.replan_interval {
        advance_window_if_needed(state, window);
        window.plan = plan_path(&window.keypoints, state);
        state.steps_since_replan = 0;
    }
}
```

### The PD controller (why this works)

The PD (Proportional-Derivative) controller is the standard model for how the human motor system works:

- **Proportional (position) term:** "I'm 0.3mm to the left of where I should be → push right." Corrects position errors.
- **Derivative (velocity) term:** "I'm moving too fast in the downward direction → push up." Corrects velocity errors. This is what prevents overshoot — the hand starts braking before it reaches the target.

Two gains to tune:
```toml
[dynamics]
position_gain = 20.0      # how strongly position errors are corrected
velocity_gain = 8.0        # how strongly velocity errors are corrected
```

The ratio `velocity_gain / (2 * sqrt(position_gain))` determines damping:
- With position_gain=20, velocity_gain=8: `8 / (2 * 4.47) = 0.89` — slightly underdamped
- This produces smooth, natural-looking trajectories with *very slight* overshoot (sub-0.1mm) that gives organic feel without tangling

### Window advance and replanning

When the hand passes a keypoint, the window advances:

```rust
fn advance_window_if_needed(state: &HandState, window: &mut SlidingWindow) {
    // Check if we've passed the first keypoint in the window
    let first = &window.keypoints[0];
    let distance = (state.position - first.position).length();
    let passed = distance < first.flexibility 
        && state.velocity.length() < state.max_speed * 0.4;
    
    if passed {
        // Remove the passed keypoint
        window.keypoints.remove(0);
        
        // Add the next keypoint from the letter/word sequence
        if let Some(next_kp) = state.next_keypoint_source.next() {
            window.keypoints.push(next_kp);
        }
        
        // Replan: the path through the window has changed
        window.plan = plan_path(&window.keypoints, state);
        window.plan_cursor = 0.0;
    }
}
```

### What replanning gives us: anticipation

When 'd' enters the window while the hand is writing 'n' in "und":
- The old plan had the hand finishing 'n' and heading toward empty space
- The new plan reshapes the end of 'n' to set up for 'd's ascender
- The final downstroke of 'n' tilts slightly more rightward
- The exit from 'n' aims higher because 'd' starts with an ascender
- This happens automatically from the spline recalculation — no special-case code

This is the muscle memory effect: the hand's current stroke is shaped by what's coming, not just by what's here.

---

## Phase 2 Parameters

```toml
[motor_planning]
window_size = 6                  # keypoints visible to planner
replan_interval = 8              # timesteps between replans
position_gain = 20.0             # PD controller position gain
velocity_gain = 8.0              # PD controller velocity gain
max_acceleration_mm_s2 = 500.0   # biomechanical limit
speed_reduction_at_turns = 0.6   # how much to slow down at sharp direction changes
air_speed_multiplier = 1.5       # hand moves faster when nib is lifted
```

---

## Phase 2 Enrichment: Context-Dependent Keypoint Adjustment

Once the sliding window is working, add context-dependent adjustments to keypoints before they enter the window:

### Preceding-letter adjustment

When generating keypoints for a letter, adjust based on what preceded it:

```rust
fn adjust_keypoints_for_context(
    letter: char,
    guide: &LetterformGuide,
    preceding: Option<char>,
    following: Option<char>,
    hand_state: &HandState,
) -> Vec<Keypoint> {
    let mut keypoints = guide.base_keypoints(letter);
    
    // Adjust entry based on preceding letter
    if let Some(prev) = preceding {
        let prev_exit_angle = estimate_exit_angle(prev);
        let natural_entry = compute_natural_entry(prev_exit_angle, keypoints[0].position);
        
        // Shift the first keypoint to accommodate the natural entry angle
        keypoints[0].position += natural_entry.offset * 0.3; // 30% adaptation
        keypoints[0].preferred_direction = Some(natural_entry.angle);
    }
    
    // Adjust exit based on following letter
    if let Some(next) = following {
        let next_entry_height = estimate_entry_height(next);
        let last = keypoints.last_mut().unwrap();
        
        // If next letter starts high (ascender), aim exit upward
        // If next letter starts at baseline, aim exit across
        let exit_aim = if next_entry_height > 1.2 { // ascender
            last.position + Vec2::new(0.5, 1.0) // up and right
        } else {
            last.position + Vec2::new(0.8, 0.3) // mostly right, slightly up
        };
        
        last.preferred_direction = Some((exit_aim - last.position).angle());
    }
    
    // Adjust for position in word
    if preceding.is_none() {
        // Word-initial: slightly larger, more deliberate entry
        for kp in &mut keypoints {
            kp.position *= 1.03; // 3% larger
        }
    }
    
    keypoints
}
```

### The anticipation effect

With context adjustment + sliding window, the sequence is:

1. Text "und" arrives for rendering
2. Keypoints for 'u' are generated with knowledge that 'n' follows → exit keypoints aim toward 'n' entry
3. Keypoints for 'n' are generated with knowledge that 'u' preceded and 'd' follows → entry adapts, exit aims up for 'd' ascender
4. Keypoints for 'd' are generated with knowledge that 'n' preceded → entry adapts from 'n' exit
5. All keypoints enter the sliding window
6. The path planner computes a smooth spline through the entire word
7. The hand follows the plan, producing a word where every stroke anticipates what's coming

This is the "mental model guiding the word" you described — the letters aren't independent shapes, they're waypoints in a word-level motor program that's been shaped by context before the hand even starts moving.

---

## Implementation Order

### Step 1: Clamp down (30 minutes)
Change dynamics parameters to the Phase 1 values. Add the velocity gate and bounding box clamp. Render "und der" and verify legibility. This is a parameter change + two guard functions, not a rewrite.

### Step 2: Verify legibility (15 minutes)
The output should be precise, maybe too precise. Letters should be recognizable. No tangling. If not, increase damping further until legible.

### Step 3: Replace attractor with PD controller (2 hours)
Swap the current `attraction_force + damping_force` dynamics with the PD controller. Keep the keypoints the same. The hand now follows the plan cursor instead of being attracted to a point. Verify output is similar to Step 2 but slightly smoother.

### Step 4: Add sliding window path planner (3 hours)
Implement `plan_path()` using Hermite spline interpolation through the window's keypoints. The hand follows the planned spline via the PD controller. Verify that the hand anticipates direction changes — the end of one letter should visibly set up for the next.

### Step 5: Add context-dependent keypoint adjustment (2 hours)
Before keypoints enter the window, adjust them based on preceding and following letters. Verify that word-level coherence improves — "und" should look like it was planned as a unit.

### Step 6: Tune and loosen (iterative)
With the PD controller working, gradually reduce `position_gain` and `velocity_gain` to introduce organic looseness:
- Start: position_gain=20, velocity_gain=8 (precise, almost mechanical)
- Target: position_gain=12-15, velocity_gain=5-7 (natural, slightly loose)
- Use CMA-ES to optimize these against the target manuscript
- Human review at each loosening step

### Step 7: Train on "und" (with the new dynamics)
Extract "und" from target manuscript. Run CMA-ES on the motor planning parameters. The training should converge much faster now because the hand isn't fighting chaos — it's starting from controlled behavior and learning how much to relax.

---

## Diagnostic tools

### Keypoint overlay rendering
```bash
scribesim render "und" --show-keypoints --show-plan-path -o debug/und_plan.png
```
Renders the word with:
- Red dots at keypoint positions
- Blue line showing the planned spline path
- Green line showing the actual hand path
- This immediately shows whether the problem is bad keypoints or bad dynamics

### Phase portrait
```bash
scribesim render "und" --phase-portrait -o debug/und_phase.png
```
Plots velocity vs. position for each axis — shows whether the dynamics are underdamped (spiraling), critically damped (smooth approach), or overdamped (sluggish).

### Window state dump
```bash
scribesim render "und" --dump-window-state -o debug/und_window.json
```
Logs the window contents, plan spline, and PD error at every timestep. For debugging replanning behavior.

---

## Relationship to other TDs

- **TD-002:** nib physics, ink model, rendering passes 2-6 unchanged
- **TD-003:** add motor planning parameters to the optimizer; CMA-ES groups remain as defined in Addendum A
- **TD-004:** nib fixes are prerequisites — thick/thin contrast must work before the hand dynamics can be evaluated visually
- **TD-005:** TD-006 replaces TD-005's attractor dynamics with the PD controller + sliding window. The letterform guides, training pipeline, and incremental extension approach from TD-005 remain. The hand state machine structure remains. Only the force model and planning layer change.

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Initial draft — constrained dynamics, sliding window motor planning | shawn + claude |
