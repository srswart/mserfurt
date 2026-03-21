# Tech Direction: TD-005 — Generative Hand Model (Motor Program Approach)

## Status
**Proposed** — represents a fundamental shift in ScribeSim's rendering architecture.

## Context
The current ScribeSim architecture treats glyphs as fixed trajectory templates that are placed, warped, and connected. Despite improvements in connections (TD-004), thick/thin contrast, and structured variation, the output still feels mechanical — like a very good typeface rather than a human hand. The root cause is architectural: a system built on fixed glyph retrieval cannot produce organic writing because it starts from the wrong primitive.

This TD proposes replacing the glyph-retrieval architecture with a **generative hand model** — a learned motor program that produces letterforms by simulating the writing act. Glyphs become soft targets that guide the hand, not rigid templates it reproduces.

## The core shift

```
OLD (typeface model):
  for each letter in text:
      template = glyph_catalog.lookup(letter)
      warped = apply_variation(template)
      place(warped, position)
      connect(warped, next_letter)

NEW (hand model):
  hand = initialize_hand(folio_state)
  for each word in text:
      hand.plan_word(word)  // sets a motor program for this word
      for each letter in word:
          hand.write_toward(letter)  // hand moves, producing marks
          // the letter that appears is shaped by:
          //   - the target letterform (what the scribe intends)
          //   - the hand's current state (where it is, how fast, how much ink)
          //   - the preceding context (what just happened)
          //   - the following context (what's coming next — the hand plans ahead)
```

The key insight: **the hand, not the glyph, is the generative unit.** The hand has state that evolves continuously. Letters are what happen when a hand with a particular state moves toward a particular target.

---

## Part 1: The Hand as a Continuous State Machine

### Hand state

The hand is a state machine that evolves at every timestep (every few pixels of movement):

```
HandState {
    // Physical position and dynamics
    position:        Vec2       // current nib tip position (mm, sub-pixel)
    velocity:        Vec2       // current movement direction and speed (mm/s)
    acceleration:    Vec2       // current change in velocity
    
    // Nib state
    nib_angle:       Float      // current nib angle (drifts slightly, ~40° ±2°)
    nib_contact:     Bool       // is the nib touching the surface?
    nib_pressure:    Float      // current downward pressure
    
    // Ink state
    ink_reservoir:   Float      // how much ink remains on the nib
    ink_flow_rate:   Float      // current flow (affected by pressure, speed, temperature)
    
    // Motor program state
    current_target:  Vec2       // where the hand is trying to go RIGHT NOW
    lookahead:       [Target]   // upcoming targets (the hand plans 2-3 strokes ahead)
    word_progress:   Float      // 0.0 = word start, 1.0 = word end
    line_progress:   Float      // 0.0 = line start, 1.0 = line end
    
    // Rhythmic state
    tempo:           Float      // current writing speed (strokes/sec)
    phase:           Float      // position in the rhythmic cycle
    
    // Fatigue / session state (from CLIO-7)
    fatigue:         Float      // accumulated fatigue (affects tremor, speed, spacing)
    emotional_state: EmotionParams  // per-folio from CLIO-7
}
```

### The motor program

A **motor program** is a sequence of targets that the hand moves through to produce a word. It is NOT a sequence of glyph templates — it is a sequence of *positions the nib tip should pass through*, derived from the intended letterforms but adapted to context.

For the word "und":
```
MotorProgram for "und":
  1. Approach from left (entry from preceding word or line start)
  2. Target: top of 'u' first stroke      → hand descends, thick downstroke
  3. Target: base of 'u' first stroke     → hand curves right at base
  4. Target: top of 'u' second stroke     → thin upstroke (hairline, parallel to nib)
  5. Target: base of 'u' second stroke    → hand curves right
  6. Target: connection to 'n'            → thin diagonal hairline upward
  7. Target: top of 'n' first stroke      → hand arrives from connection
  8. Target: base of 'n' first stroke     → thick downstroke
  9. Target: top of 'n' arch              → hand curves over (the arch of n)
  10. Target: base of 'n' second stroke   → thick downstroke
  11. Target: connection to 'd'           → thin hairline up and right
  12. Target: top of 'd' ascender         → hand rises to ascender height
  13. Target: loop at top of 'd'          → characteristic Bastarda loop
  14. Target: base of 'd' downstroke      → thick descending stroke
  15. Target: bowl of 'd'                 → curved stroke forming the bowl
  16. Exit: trailing hairline right        → sets up connection to next word/letter
```

Each target is a **soft attractor**, not a hard waypoint. The hand moves toward the target but arrives at a position that is *near* it, influenced by:
- The hand's current velocity (momentum carries it)
- The hand's acceleration limits (biomechanical — a hand can't change direction instantly)
- The upcoming targets (the hand plans ahead and smooths its path)

### The attractor dynamics

At each timestep, the hand's acceleration is determined by:

```
fn hand_step(state: &mut HandState, dt: Float) {
    // The target exerts an attractive force
    let to_target = state.current_target - state.position;
    let attraction = to_target.normalized() * ATTRACTION_STRENGTH / to_target.length().max(0.1);
    
    // The next target exerts a weaker attractive force (lookahead smoothing)
    let lookahead_force = if let Some(next) = state.lookahead.first() {
        let to_next = next.position - state.position;
        to_next.normalized() * LOOKAHEAD_STRENGTH / to_next.length().max(0.5)
    } else {
        Vec2::ZERO
    };
    
    // Velocity damping (the hand has inertia but also friction)
    let damping = -state.velocity * DAMPING_COEFFICIENT;
    
    // Tremor (if any — from fatigue model)
    let tremor = state.fatigue * Vec2::from_angle(noise(state.phase)) * TREMOR_SCALE;
    
    // Rhythm: the hand has a natural oscillation that it falls into
    let rhythm_force = compute_rhythm_force(state.phase, state.tempo);
    
    // Sum forces
    state.acceleration = attraction + lookahead_force + damping + tremor + rhythm_force;
    
    // Integrate
    state.velocity += state.acceleration * dt;
    state.velocity = state.velocity.clamp_length(MAX_SPEED);  // biomechanical limit
    state.position += state.velocity * dt;
    
    // Update nib state
    if state.nib_contact {
        let mark_width = compute_nib_width(state.velocity.angle(), state.nib_angle, state.nib_pressure);
        let ink_deposit = compute_ink_deposit(state.ink_reservoir, state.nib_pressure, state.velocity.length());
        emit_mark(state.position, mark_width, ink_deposit);
        state.ink_reservoir -= ink_deposit.consumed;
    }
    
    // Advance target if close enough
    if (state.position - state.current_target).length() < TARGET_RADIUS {
        advance_to_next_target(state);
    }
    
    // Update rhythmic phase
    state.phase += state.tempo * dt;
}
```

This produces letterforms that are *guided by* the targets but *shaped by* the dynamics. The same targets, with slightly different initial conditions or accumulated state, produce slightly different letterforms — organically, not through artificial noise.

---

## Part 2: Learning the Motor Program from Small Samples

### The training approach

Instead of defining target positions by hand, we **learn** them from the real manuscript:

#### Step 1: Extract a training word from the target manuscript
Pick a common word visible in the target (e.g., "und", "der", "wir"). Extract the word image and its Kraken-segmented baseline.

#### Step 2: Trace the writing path
From the word image, extract the probable path the nib followed:
1. Skeletonize the word image (thin to centerlines)
2. Order the skeleton into a plausible writing sequence (left to right, with detected lifts)
3. Estimate speed from stroke width: thick segments = slow, thin segments = fast
4. Estimate pressure from darkness: darker = more pressure
5. Result: a time-ordered sequence of (position, speed, pressure) samples

#### Step 3: Fit the hand model parameters
Run the hand simulation with initial parameters. Compare its output path against the traced path from the real manuscript. Optimize the hand model parameters (attraction strength, damping, rhythm, tempo, etc.) to minimize the path distance.

```python
def train_on_word(target_word_image, word_text, hand_params):
    # Extract target path from real manuscript
    target_path = trace_writing_path(target_word_image)
    
    # Generate motor program targets for this word
    targets = generate_targets(word_text, hand_params.letterform_guides)
    
    # Simulate the hand
    def simulate_and_compare(params):
        hand = HandState(params)
        hand.load_targets(targets)
        simulated_path = []
        while hand.has_targets():
            hand.step(dt=0.001)
            if hand.nib_contact:
                simulated_path.append(hand.position)
        
        # Compare paths using Dynamic Time Warping
        distance = dtw_distance(simulated_path, target_path)
        return distance
    
    # Optimize using CMA-ES
    optimal_params = cma_optimize(
        simulate_and_compare,
        initial=hand_params.dynamics_vector(),
        sigma=0.1,
        max_iterations=200
    )
    return optimal_params
```

#### Step 4: Validate on a slightly longer sample
Take the learned parameters and simulate a two-word phrase ("und der"). Does it still look right? The word-to-word transition is the test — if the hand model has learned the right dynamics, the transition should be natural.

#### Step 5: Incremental extension
Try progressively longer text:
- 1 word ✓
- 2 words → evaluate, adjust if needed
- 1 line → evaluate, adjust if needed
- 3 lines → evaluate, adjust if needed
- 1 folio → evaluate, accept or revert

At each extension, compare against the target manuscript using the TD-003 metric suite. If metrics degrade, identify which parameters are drifting and constrain them.

### What the model learns

The hand model doesn't learn letterforms. It learns **writing mechanics**:
- How quickly the hand accelerates toward a target (attraction strength)
- How much momentum carries between strokes (damping coefficient)
- The natural rhythm of the writing (tempo, phase relationships)
- How pressure varies with stroke direction and position
- How connections form between letters (exit/entry dynamics)
- How the hand behaves differently at word boundaries vs. mid-word

These mechanics are scribe-specific. Training on one scribe's "und" teaches us how *that scribe's hand moves*, and those dynamics apply to everything that scribe writes.

---

## Part 3: The Letterform Guide (replacing the glyph catalog)

The old glyph catalog stored complete trajectories per letter. The new system stores **letterform guides** — minimal descriptions of what makes each letter recognizable:

```
LetterformGuide {
    letter:          char
    // Key structural points that define the letter's identity
    // NOT a complete trajectory — just the points the hand must hit
    keypoints: [
        Keypoint {
            position:    Vec2      // relative to baseline and x-advance
            type:        "peak" | "base" | "junction" | "loop_apex"
            contact:     Bool      // should the nib be touching here?
            direction:   Float     // preferred approach direction
            flexibility: Float     // how far from this point is acceptable (mm)
        }
    ]
    // Structural constraints
    x_advance:       Float         // typical horizontal extent
    ascender:        Bool
    descender:       Bool
    // Context adaptations
    variants: {
        "before_ascender": { /* keypoint adjustments */ },
        "after_descender": { /* keypoint adjustments */ },
        "word_initial": { /* keypoint adjustments */ },
        "word_final": { /* keypoint adjustments */ },
    }
}
```

For example, the guide for 'n':
```
'n': {
    keypoints: [
        { pos: (0.0, 1.0),   type: "peak",     contact: true,  dir: 270°, flex: 0.2mm },  // top of first minim
        { pos: (0.0, 0.0),   type: "base",     contact: true,  dir: 270°, flex: 0.1mm },  // base of first minim
        { pos: (0.3, 1.0),   type: "peak",     contact: true,  dir: 0°,   flex: 0.3mm },  // top of arch
        { pos: (0.6, 1.0),   type: "peak",     contact: true,  dir: 270°, flex: 0.2mm },  // top of second minim
        { pos: (0.6, 0.0),   type: "base",     contact: true,  dir: 270°, flex: 0.1mm },  // base of second minim
    ],
    x_advance: 0.6,  // in x-height units
    ascender: false,
    descender: false,
}
```

The hand model steers through these keypoints. The *path between them* is determined by the hand's dynamics, not prescribed. Two instances of 'n' have the same keypoints but different paths because the hand arrives from different directions, at different speeds, with different ink states.

### Context-dependent guides

The guide for 'e' after 'r' is different from 'e' after 'd':
- After 'r': the hand arrives from high-right, so 'e' entry is from above
- After 'd': the hand arrives from mid-right after the bowl, so 'e' entry is more horizontal

This is specified as a variant in the guide, not as a separate glyph.

---

## Part 4: The Training and Extension Pipeline

### Phase 1: Single word training
```bash
# Extract target word from manuscript
scribesim extract-word samples/target_manuscript.png --word "und" --line 3 -o training/und.png

# Train hand dynamics on this word
scribesim train --target training/und.png --text "und" \
    --initial-params shared/hands/konrad_erfurt_1457.toml \
    --output shared/hands/konrad_trained_v1.toml \
    --max-iterations 500

# Render the trained word and compare
scribesim render-word "und" --params shared/hands/konrad_trained_v1.toml -o output/und_trained.png
scribesim compare output/und_trained.png training/und.png --metrics all
```

### Phase 2: Extension with quality gates
```bash
# Try two words
scribesim render-word "und der" --params shared/hands/konrad_trained_v1.toml -o output/und_der.png
scribesim compare output/und_der.png --target-line samples/target_line.png --metrics all

# If quality holds, try a full line
scribesim render-line "Der strom des glaubens ist nicht mein eigen" \
    --params shared/hands/konrad_trained_v1.toml -o output/test_line.png

# If quality degrades, identify which metrics dropped and re-train with constraints
scribesim train --target samples/target_line.png \
    --text "Der strom des glaubens ist nicht mein eigen" \
    --initial-params shared/hands/konrad_trained_v1.toml \
    --lock-params "nib.*,dynamics.attraction_strength" \  # keep what works, adjust what broke
    --output shared/hands/konrad_trained_v2.toml
```

### Phase 3: Full folio rendering with checkpoints
```bash
# Render line by line, compare each
scribesim render-folio f01r.json \
    --params shared/hands/konrad_trained_v2.toml \
    --checkpoint-every-line \
    --compare-target samples/target_folio.png \
    -o output/f01r_trained.png

# Output: per-line quality scores, overall score, suggested parameter adjustments
```

### Revert mechanism
Every render is checkpointed. If line N degrades quality, the system can:
1. Revert to the parameters that worked for line N-1
2. Try line N with slightly different random seed (different micro-variation)
3. If that doesn't help, flag for human review

---

## Part 5: What This Changes

### Architecture impact
- The **glyph catalog** becomes the **letterform guide library** — much simpler per-letter definitions
- The **stroke renderer** is replaced by the **hand simulator** — a continuous physics simulation
- The **connection path system** (TD-004) is subsumed — connections emerge naturally from the hand moving between letter targets
- The **structured variation system** (TD-002 Part 1) is subsumed — variation emerges from the hand's continuous state evolution
- The **parameter tuning system** (TD-003) remains and becomes MORE important — it's how we train the hand

### What we keep from TD-002/003/004
- Nib physics (nib angle, width equation) — still the foundation of mark-making
- Ink state model — still tracks reservoir, depletion, deposit
- Vellum interaction — still a post-process on the marks the hand produces
- Metric suite — still how we measure quality
- CMA-ES optimizer — still how we fit parameters

### What changes
- Fixed trajectories → hand dynamics simulation
- Glyph placement → target-guided hand steering
- Explicit connections → emergent connections from continuous hand movement
- Artificial variation → natural variation from state evolution
- Per-glyph rendering → continuous simulation with mark emission

### Risk
The hand simulator is more complex and harder to debug than glyph placement. If the dynamics are wrong, the output can be worse than the current approach. Mitigation: keep the old glyph-based renderer as a fallback, and A/B test every improvement.

---

## Implementation priority

1. **Hand state machine + basic dynamics** — implement the continuous simulation loop with attraction, damping, and nib physics. Render a single straight line of minims (nnnnnn) to validate.

2. **Letterform guides for 5 core letters** — n, u, d, e, r. These cover: minim, arch, ascender, bowl, and the most common connections in German.

3. **Train on "und"** — extract from target, trace path, fit dynamics with CMA-ES. This is the proof of concept.

4. **Extend to "und der"** — validate that the hand transitions between words naturally.

5. **Add remaining letterform guides** — complete the alphabet incrementally, training each against target samples.

6. **Full line rendering** — render a complete line, compare against target, iterate.

7. **Full folio with quality gates** — render line by line with checkpoints and revert mechanism.

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-20 | Initial draft — generative hand model, motor programs, training pipeline | shawn + claude |
