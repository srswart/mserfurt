# Tech Direction: TD-012 — Allograph Selection via Dynamic Programming

## Status
**Proposed** — word assembly layer between letterform extraction (TD-008) and rendering.

## Context
The evolutionary word assembly (TD-007) treats each letter instance independently — it picks a good 'n', a good 'u', a good 'd', and places them side by side. But a real scribe doesn't write letters independently. The way he finishes the 'n' determines how he starts the 'u'. The hand has momentum, position, ink state, and fatigue that carry across letter boundaries. A word is not a sequence of glyphs — it's a continuous gesture segmented into letter-like units.

The Annotation Workbench now provides manually identified and labeled glyph crops from reference manuscripts (replacing the failed automated segmentation). These crops, once evolved into Bézier+pressure genomes (TD-008), constitute a library of **allographs** — multiple variant forms of each letter, each with specific entry geometry, exit geometry, weight, and stroke character. The question becomes: given a word to render, which sequence of allograph choices produces the most natural-looking continuous writing?

This is a classic sequential optimization problem. Dynamic programming — specifically the Viterbi algorithm — finds the globally optimal path through the allograph space in polynomial time, without the expense of evolutionary search for word assembly.

---

## Part 1: The Allograph Library

### What the Annotation Workbench produces

The Annotation Workbench enables manual identification of glyphs from reference manuscripts (Cgm 100, Werbeschreiben, Kaiserurkunde, etc.). For each identified glyph, the operator:

1. Draws a bounding region around the glyph in the manuscript image
2. Labels it with the character identity (a, b, c, ... ſ, tz, ch, etc.)
3. Optionally tags contextual metadata:
   - Preceding letter (what comes before this instance)
   - Following letter (what comes after)
   - Position in word (initial, medial, terminal)
   - Qualitative notes ("wide form", "compressed", "shows fatigue", "post-dip heavy ink")

### What TD-008 extraction produces from each crop

Each manually identified glyph crop is evolved (TD-008) into a genome:

```rust
struct AllographGenome {
    // Identity
    letter: char,
    source_manuscript: String,     // "cgm100", "werbeschreiben", etc.
    source_folio: String,          // "f003r"
    source_word: String,           // the word this instance came from
    instance_id: String,           // unique identifier
    
    // The evolved writing description
    segments: Vec<BezierSegment>,  // path + pressure
    
    // Entry geometry (how the hand arrives at this letter)
    entry_point: Vec2,             // position where writing begins
    entry_angle: f64,              // direction the hand is traveling on entry
    entry_speed: f64,              // estimated hand speed on entry
    entry_pressure: f64,           // nib pressure at entry
    
    // Exit geometry (how the hand departs)
    exit_point: Vec2,              // position where writing ends
    exit_angle: f64,               // direction the hand is traveling on exit
    exit_speed: f64,               // estimated hand speed on exit  
    exit_pressure: f64,            // nib pressure at exit
    
    // Metrics
    x_advance: f64,               // horizontal space consumed (mm)
    weight: f64,                   // overall stroke heaviness (0-1)
    width_ratio: f64,              // width relative to canonical x_height
    
    // Context from annotation
    observed_predecessor: Option<char>,  // what letter preceded this in the manuscript
    observed_successor: Option<char>,    // what letter followed
    word_position: WordPosition,         // Initial, Medial, Terminal
    
    // Quality
    extraction_fitness: f64,       // how well the evolved genome matches the crop
}

enum WordPosition {
    Initial,   // first letter in a word
    Medial,    // middle of a word
    Terminal,  // last letter in a word
}
```

### Library structure

```
allograph_library/
├── manifest.json                 — index of all allographs with metadata
├── a/
│   ├── a_cgm100_f003r_001.toml  — allograph genome
│   ├── a_cgm100_f003r_002.toml  — different instance from same source
│   ├── a_cgm100_f008v_001.toml  — instance from different folio
│   ├── a_werbe_001.toml         — instance from Werbeschreiben
│   └── ...                       — 5-15 allographs per letter
├── b/
│   └── ...
├── ch/                           — ligature allographs
│   └── ...
└── ſ/                            — long-s allographs
    └── ...
```

Target: **8-15 allographs per letter**, covering the natural variation range. More frequent letters (e, n, r, i, s, t, a, d) should have more allographs; rare letters (x, q, z) can have fewer.

---

## Part 2: Transition Cost Model

The cost of transitioning from allograph A (letter N) to allograph B (letter N+1) encodes how naturally the hand can flow from one to the other.

### Cost components

```rust
struct TransitionCost {
    geometric: f64,      // spatial compatibility of exit/entry points
    angular: f64,        // directional compatibility of exit/entry angles
    pressure: f64,       // pressure continuity across the boundary
    speed: f64,          // speed continuity
    spacing: f64,        // resulting inter-letter gap naturalness
    weight: f64,         // visual weight consistency
    context: f64,        // bonus/penalty from observed bigram context
}

fn compute_transition_cost(a: &AllographGenome, b: &AllographGenome) -> f64 {
    let mut cost = 0.0;
    
    // --- Geometric compatibility ---
    // How far does the hand need to travel from A's exit to B's entry?
    // In tight Bastarda, this should be very short (< 0.5mm)
    let gap = b.entry_point - a.exit_point;
    let gap_distance = gap.length();
    
    // Ideal gap is small but not zero (letters touching but not overlapping)
    let ideal_gap = 0.2;  // mm
    let geometric_cost = (gap_distance - ideal_gap).abs() / 1.0;  // normalize
    cost += geometric_cost * 3.0;  // high weight — spatial flow is critical
    
    // --- Angular compatibility ---
    // Is the hand traveling in a compatible direction?
    // A's exit angle should roughly point toward B's entry point
    let actual_direction = gap.angle();
    let exit_entry_mismatch = angle_difference(a.exit_angle, actual_direction).abs();
    let entry_angle_mismatch = angle_difference(actual_direction, b.entry_angle).abs();
    
    let angular_cost = (exit_entry_mismatch + entry_angle_mismatch) / std::f64::consts::PI;
    cost += angular_cost * 2.5;
    
    // --- Pressure continuity ---
    // Sudden pressure changes at letter boundaries look unnatural
    let pressure_jump = (a.exit_pressure - b.entry_pressure).abs();
    cost += pressure_jump * 1.5;
    
    // --- Speed continuity ---
    // The hand shouldn't suddenly accelerate or decelerate between letters
    let speed_jump = (a.exit_speed - b.entry_speed).abs() / a.exit_speed.max(b.entry_speed).max(0.1);
    cost += speed_jump * 1.0;
    
    // --- Spacing naturalness ---
    // The resulting gap (A's x_advance + gap) should produce natural Bastarda density
    let total_advance = a.x_advance + gap.x;
    let expected_advance = expected_advance_for_pair(a.letter, b.letter);
    let spacing_deviation = (total_advance - expected_advance).abs() / expected_advance;
    cost += spacing_deviation * 2.0;
    
    // --- Weight consistency ---
    // Adjacent letters shouldn't have dramatically different stroke heaviness
    // (unless the ink cycle dictates it — but that's handled separately)
    let weight_jump = (a.weight - b.weight).abs();
    cost += weight_jump * 1.0;
    
    // --- Context bonus ---
    // If allograph A was observed before letter B in the real manuscript,
    // that's a strong signal this transition works well
    if a.observed_successor == Some(b.letter) {
        cost -= 1.5;  // bonus for observed natural sequence
    }
    // If allograph B was observed after letter A in the real manuscript
    if b.observed_predecessor == Some(a.letter) {
        cost -= 1.5;  // bonus
    }
    // Double bonus if this exact bigram was observed
    if a.observed_successor == Some(b.letter) && b.observed_predecessor == Some(a.letter) {
        cost -= 1.0;  // additional bonus for confirmed pair
    }
    
    cost.max(0.0)  // floor at zero
}
```

### The context bonus is key

The Annotation Workbench captures which letter preceded and followed each identified glyph. This means the allograph library knows that "this particular 'n' was written before an 'i' in the real manuscript." When the DP assembles the word "nicht", it can prefer an 'n' allograph that was actually observed before an 'i' — because that allograph's exit geometry is already adapted to the 'i' entry. The scribe's own contextual adaptation, captured in the annotation, feeds directly into the selection algorithm.

This is why manual annotation is so valuable despite being slower than automated extraction — the contextual metadata turns each allograph from an isolated letter form into a letter-in-context with directional flow information.

---

## Part 3: The Viterbi Algorithm for Word Assembly

### Setup

Given:
- A word to render: `w = [c₁, c₂, ..., cₙ]` (sequence of characters)
- For each character cᵢ, a set of allographs: `A(cᵢ) = {a₁, a₂, ..., aₖ}`
- Transition costs: `T(aⱼ, aₖ)` for each pair of allographs at adjacent positions
- Emission costs: `E(aⱼ)` — intrinsic quality of each allograph (from extraction fitness)

### Algorithm

```rust
fn viterbi_word_assembly(
    word: &[char], 
    library: &AllographLibrary,
    ink_state: &InkState,
    hand_state: &HandState,
) -> Vec<&AllographGenome> {
    let n = word.len();
    
    // DP table: dp[i][j] = minimum cost to reach allograph j at position i
    // back[i][j] = which allograph at position i-1 led to this minimum
    let mut dp: Vec<Vec<f64>> = Vec::new();
    let mut back: Vec<Vec<Option<usize>>> = Vec::new();
    
    // --- Initialize first position ---
    let first_allographs = library.get(word[0]);
    let mut first_costs = Vec::new();
    
    for (j, allograph) in first_allographs.iter().enumerate() {
        // Cost for starting with this allograph
        let emission = emission_cost(allograph);
        
        // Entry cost from current hand state (how easily can the hand
        // reach this allograph's entry point from its current position?)
        let entry = hand_entry_cost(hand_state, allograph);
        
        // Word-initial bonus for allographs observed in initial position
        let position_bonus = if allograph.word_position == WordPosition::Initial {
            -0.5  // prefer word-initial forms at word start
        } else {
            0.0
        };
        
        first_costs.push(emission + entry + position_bonus);
    }
    
    dp.push(first_costs);
    back.push(vec![None; first_allographs.len()]);
    
    // --- Fill DP table left to right ---
    for i in 1..n {
        let prev_allographs = library.get(word[i - 1]);
        let curr_allographs = library.get(word[i]);
        
        let mut curr_costs = vec![f64::MAX; curr_allographs.len()];
        let mut curr_back = vec![None; curr_allographs.len()];
        
        for (j, curr) in curr_allographs.iter().enumerate() {
            let emission = emission_cost(curr);
            
            // Word-terminal bonus
            let position_bonus = if i == n - 1 && curr.word_position == WordPosition::Terminal {
                -0.5
            } else {
                0.0
            };
            
            // Ink state modifier: if ink is running low, prefer lighter allographs
            let ink_modifier = ink_preference(ink_state, curr);
            
            // Find the best predecessor
            for (k, prev) in prev_allographs.iter().enumerate() {
                let prev_cost = dp[i - 1][k];
                let transition = compute_transition_cost(prev, curr);
                let total = prev_cost + transition + emission + position_bonus + ink_modifier;
                
                if total < curr_costs[j] {
                    curr_costs[j] = total;
                    curr_back[j] = Some(k);
                }
            }
        }
        
        dp.push(curr_costs);
        back.push(curr_back);
    }
    
    // --- Traceback: find the optimal sequence ---
    let last_costs = dp.last().unwrap();
    let mut best_final = 0;
    for j in 1..last_costs.len() {
        if last_costs[j] < last_costs[best_final] {
            best_final = j;
        }
    }
    
    let mut path = vec![best_final];
    for i in (1..n).rev() {
        let prev_idx = back[i][*path.last().unwrap()].unwrap();
        path.push(prev_idx);
    }
    path.reverse();
    
    // Convert indices to allograph references
    path.iter().enumerate().map(|(i, &j)| {
        &library.get(word[i])[j]
    }).collect()
}
```

### Complexity

For a word of length N with K allographs per letter:
- Time: O(N × K²) — for each position, check all pairs with previous position
- Space: O(N × K)
- Typical case: N=8 (average word length), K=10 (allographs per letter) → 800 operations
- This is essentially **instant** — microseconds per word, compared to minutes for evolutionary assembly

---

## Part 4: Extended State — Hand Dynamics

The basic Viterbi treats each allograph as a discrete state. But the hand has continuous dynamics that carry across letters. We can extend the state to include hand properties:

### Hand state at each position

```rust
struct HandState {
    position: Vec2,      // current hand position (mm from page origin)
    velocity: Vec2,      // current hand velocity (mm/s)
    ink_level: f64,      // current ink reservoir
    fatigue: f64,        // cumulative fatigue factor
    time_in_word: f64,   // time elapsed since word started
}
```

### Hand state propagation

When we select allograph A at position i, the hand state after writing A is deterministic:

```rust
fn propagate_hand_state(
    state: &HandState, 
    allograph: &AllographGenome,
    ink: &mut InkState,
) -> HandState {
    // Position: hand ends at the allograph's exit point (relative to word origin)
    let new_position = state.position + Vec2::new(allograph.x_advance, 0.0);
    
    // Velocity: inferred from the allograph's exit geometry
    let exit_speed = allograph.exit_speed;
    let new_velocity = Vec2::from_angle(allograph.exit_angle) * exit_speed;
    
    // Ink: depleted by the strokes in this allograph
    let ink_consumed = allograph.total_stroke_length() * allograph.weight * 0.001;
    let new_ink = (state.ink_level - ink_consumed).max(0.0);
    
    // Fatigue: increases slightly with each letter
    let new_fatigue = state.fatigue + 0.002;  // very gradual
    
    // Time: estimated from stroke length and speed
    let writing_time = allograph.total_stroke_length() / exit_speed.max(10.0);
    
    HandState {
        position: new_position,
        velocity: new_velocity,
        ink_level: new_ink,
        fatigue: new_fatigue,
        time_in_word: state.time_in_word + writing_time,
    }
}
```

### Incorporating hand state into transition costs

The transition cost now considers whether the hand can physically make the transition:

```rust
fn compute_transition_cost_with_dynamics(
    a: &AllographGenome,
    b: &AllographGenome,
    hand_after_a: &HandState,
) -> f64 {
    let mut cost = compute_transition_cost(a, b);  // base geometric cost
    
    // Can the hand physically reach B's entry from its current state?
    let required_displacement = b.entry_point - hand_after_a.position;
    let available_speed = hand_after_a.velocity.length();
    
    // If the hand is moving fast and B's entry is far away in the wrong direction,
    // the hand would need to decelerate and change direction — expensive
    let velocity_alignment = hand_after_a.velocity.normalized()
        .dot(required_displacement.normalized());
    
    if velocity_alignment < 0.0 {
        // Hand is moving away from the target — needs to reverse
        cost += (1.0 - velocity_alignment) * 2.0;
    }
    
    // Fatigue modifier: when fatigued, prefer allographs with lower pressure
    // (the scribe unconsciously lightens up)
    if hand_after_a.fatigue > 0.3 {
        let fatigue_penalty = (b.weight - 0.5).max(0.0) * hand_after_a.fatigue;
        cost += fatigue_penalty;
    }
    
    cost
}
```

---

## Part 5: Line and Folio Assembly

### Word-to-word transitions

The same DP logic applies between words, but with different cost weights:

```rust
fn assemble_line(
    words: &[Vec<char>],
    library: &AllographLibrary,
    line_state: &mut LineState,
) -> Vec<Vec<&AllographGenome>> {
    let mut assembled_words = Vec::new();
    let mut hand = HandState::new(line_state.margin_left, line_state.baseline_y);
    let mut ink = line_state.ink_state.clone();
    
    for (w, word) in words.iter().enumerate() {
        // Check for dip before this word
        if ink.wants_to_dip() {
            ink.dip();
        }
        
        // Assemble this word using Viterbi
        let allograph_sequence = viterbi_word_assembly(word, library, &ink, &hand);
        
        // Update hand and ink state through the word
        for allograph in &allograph_sequence {
            hand = propagate_hand_state(&hand, allograph, &mut ink);
        }
        
        assembled_words.push(allograph_sequence);
        
        // Word spacing: advance hand with a gap
        let word_gap = word_spacing(&hand, line_state);
        hand.position.x += word_gap;
    }
    
    assembled_words
}
```

### Folio-level fatigue and drift

Across a folio, the hand state accumulates fatigue and drift:

```rust
fn assemble_folio(
    folio_json: &FolioJson,
    library: &AllographLibrary,
) -> AssembledFolio {
    let mut folio_state = FolioState::from_json(folio_json);
    let mut lines = Vec::new();
    
    for (l, line) in folio_json.lines.iter().enumerate() {
        let words: Vec<Vec<char>> = line.text.split(' ')
            .map(|w| w.chars().collect())
            .collect();
        
        let mut line_state = LineState {
            baseline_y: folio_state.baseline_for_line(l),
            margin_left: folio_state.margin_left + random_jitter(0.3), // line start variation
            ink_state: folio_state.ink_state.clone(),
        };
        
        let assembled = assemble_line(&words, library, &mut line_state);
        
        // Update folio state for next line
        folio_state.ink_state = line_state.ink_state;
        folio_state.advance_fatigue(0.005); // slight fatigue increase per line
        
        lines.push(assembled);
    }
    
    AssembledFolio { lines }
}
```

---

## Part 6: Rendering the Assembled Sequence

The Viterbi output is a sequence of allograph genomes. Rendering concatenates them with the nib physics and ink cycle:

```rust
fn render_assembled_word(
    allographs: &[&AllographGenome],
    canvas: &mut Canvas,
    start_x: f64,
    baseline_y: f64,
    nib: &NibConfig,
    ink: &mut InkState,
) {
    let mut cursor_x = start_x;
    
    for (i, allograph) in allographs.iter().enumerate() {
        // Apply whole-glyph affine variation (TD per-instance variation)
        let variation = WholeGlyphVariation::random_subtle();
        
        // Render each segment of the allograph
        for segment in &allograph.segments {
            let transformed = segment
                .translate(cursor_x, baseline_y)
                .apply_variation(&variation);
            
            if transformed.contact {
                render_stroke_with_ink(canvas, &transformed, nib, ink);
            }
        }
        
        cursor_x += allograph.x_advance;
        
        // Render connector to next letter (if within the same word)
        if i + 1 < allographs.len() {
            let next = allographs[i + 1];
            let connector = compute_connector(
                allograph.exit_point,
                allograph.exit_angle,
                next.entry_point, 
                next.entry_angle,
                cursor_x,
                baseline_y,
            );
            
            if let Some(conn) = connector {
                render_stroke_with_ink(canvas, &conn, nib, ink);
            }
        }
    }
}
```

### Connectors from DP are natural

Because the DP selected allographs with compatible exit/entry geometry, the connectors are now short, properly angled, and natural-looking. The transition cost penalized pairs with mismatched exit/entry points, so the selected pairs already flow into each other. The connector is just a short hairline bridge between two compatible endpoints — exactly what it should be.

This is why the connectors failed before: without DP, the allograph selection was random, so exit/entry points often mismatched badly, producing awkward connections. With DP, the connections are selected for compatibility.

---

## Part 7: Relationship to Existing TDs

### What TD-012 replaces
- **TD-007 word-level evolution** for word assembly. The evolutionary algorithm is no longer needed to find good letter combinations — DP does this optimally in microseconds.
- **The connector system** that was generating artifacts. Connectors now emerge naturally from compatible allograph selection.

### What TD-012 uses
- **TD-008 allograph genomes** — the evolved letter forms are the allograph library entries
- **TD-009 reference selection** — the source manuscripts for the Annotation Workbench
- **TD-010 ink cycle** — ink state feeds into the DP as a modifier on allograph preference
- **TD-004 nib physics** — rendering uses the same nib model
- **Annotation Workbench** — manual glyph identification provides the labeled crops and contextual metadata that TD-008 evolves into allograph genomes

### What TD-012 does NOT replace
- **TD-007 evolutionary algorithm** is still used for:
  - Evolving allograph genomes from crops (TD-008)
  - Folio-level parameter optimization
  - Discovering new allograph variants not present in the reference manuscripts
- **TD-010 ink cycle** — computed during rendering, independent of DP
- **TD-011 weathering** — applied after rendering

### Updated pipeline

```
Annotation Workbench (manual glyph identification)
    ↓
TD-008: Evolve allograph genomes from labeled crops
    ↓
TD-012: Allograph library + transition cost model
    ↓
TD-012: Viterbi word assembly (select optimal allograph sequence per word)
    ↓
TD-010: Ink cycle (applied during rendering)
    ↓
TD-004: Nib physics rendering
    ↓
TD-011: AI-assisted weathering
```

---

## Part 8: Performance

| Operation | Time | Note |
|---|---|---|
| Viterbi per word (8 letters, 10 allographs) | ~50µs | O(N×K²), pure computation |
| Transition cost precomputation (full library) | ~2s | One-time: compute all pairwise costs |
| Full folio assembly (250 words) | ~15ms | Essentially instant |
| Rendering (separate step) | ~5 min/folio | Unchanged from current |

The DP assembly is negligible compared to rendering time. The bottleneck remains the stroke-level rendering, not the allograph selection.

---

## Implementation Priority

1. **Allograph library data structure** — define the TOML format for allograph genomes, implement the library loader. Populate from existing manually annotated crops via TD-008 extraction.

2. **Transition cost function** — implement the geometric, angular, pressure, and context cost components. Test with known good/bad letter pairs.

3. **Basic Viterbi** — implement the DP for single-word assembly with the base cost function. Test on "und", "der", "schreiber".

4. **Render from Viterbi output** — wire the allograph sequence into the existing renderer. Verify the output looks at least as good as the current evolutionary assembly.

5. **Connector generation from compatible exits/entries** — re-enable connectors using the DP-selected allograph pairs. These should be naturally compatible.

6. **Extended hand dynamics** — add hand state propagation and dynamics-aware transition costs.

7. **Line and folio assembly** — chain words into lines with word spacing, dip timing, and fatigue accumulation.

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-27 | Initial draft — DP allograph selection with Viterbi algorithm | shawn + claude |
