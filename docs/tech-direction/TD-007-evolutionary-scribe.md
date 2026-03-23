# Tech Direction: TD-007 — Multilayer Evolutionary Scribe

## Status
**Proposed** — alternative approach to TD-005/TD-006 physics simulation.

## Context
The physics-based hand simulation (TD-005, TD-006) has proven difficult to stabilize. The attractor dynamics produce chaos when loose and fragments when clamped. The fundamental issue: deriving realistic handwriting from physical first principles requires simultaneously tuning dozens of interacting parameters, and the system is brittle — small changes produce qualitatively different (and usually worse) output.

TD-007 proposes an alternative: instead of simulating how a hand moves and hoping legible Bastarda emerges, we **evolve** stroke-level representations that satisfy multiple fitness criteria simultaneously. The algorithm doesn't know how a quill works. It knows what good Bastarda looks like, and it searches for solutions that look right.

This is slower to execute (it's an optimization, not a forward simulation) but more robust — the fitness function is stable even when individual candidates are wild, and the evolutionary pressure steadily drives the population toward the target.

## The core idea

```
PHYSICS APPROACH (TD-005/006):
  Define mechanics → simulate forward → hope output looks right → tune if not

EVOLUTIONARY APPROACH (TD-007):
  Define what "right" looks like → generate candidates → select the fittest → 
  breed and mutate → repeat until output matches target
```

The physics is not discarded — it becomes part of the fitness function and the mutation operators. The nib-angle width equation (TD-002/004) determines how strokes are rendered. But the *paths* those strokes follow are evolved, not derived from dynamics.

---

## Part 1: The Three-Layer Genome

Each word to be rendered has a three-layer genome:

### Layer 1: Word envelope (slow evolution)

```
WordGenome {
    baseline_y:         Float      // vertical position on page
    baseline_drift:     [Float]    // per-glyph y-offsets from baseline
    word_width_mm:      Float      // total horizontal extent
    global_slant_deg:   Float      // overall rightward lean
    slant_drift:        [Float]    // per-glyph slant variation
    ink_state_start:    Float      // reservoir level at word start
    tempo:              Float      // overall writing speed (affects stroke weight)
}
```

This layer evolves slowly — most mutations are small perturbations. It sets the macro-structure that constrains everything below.

### Layer 2: Glyph shapes (medium evolution)

For each letter in the word:

```
GlyphGenome {
    // The actual shape: a sequence of Bézier segments
    // Each segment has control points that define the path
    segments: [
        BézierSegment {
            // 4 control points for a cubic Bézier
            p0: Vec2,     // start (usually inherited from previous segment)
            p1: Vec2,     // control point 1
            p2: Vec2,     // control point 2
            p3: Vec2,     // end
            contact: Bool, // nib on surface?
        }
    ]
    
    // Horizontal extent within the word's allocated space
    x_offset:    Float    // where this glyph starts within the word
    x_advance:   Float    // how much horizontal space it occupies
    
    // Connection to next glyph
    exit_point:  Vec2     // where the pen leaves this glyph
    exit_angle:  Float    // direction of departure
}
```

This layer evolves at medium rate. Mutations include:
- Shifting individual control points
- Adding or removing segments
- Adjusting the connection geometry
- Scaling the glyph horizontally or vertically

### Layer 3: Stroke rendering (fast evolution)

For each Bézier segment:

```
StrokeGenome {
    pressure_curve:  [Float]   // pressure at N sample points along the segment
    speed_curve:     [Float]   // writing speed at N sample points
    nib_angle_drift: Float     // slight deviation from base nib angle for this stroke
}
```

This layer evolves fastest. Mutations are small perturbations to the pressure and speed curves. This is where organic micro-texture comes from — the slight pressure variation within a single downstroke, the speed change at a direction reversal.

---

## Part 2: The Fitness Function

The fitness of a candidate word is a weighted sum of multiple criteria. This is where the style guardrails live — not as rules the algorithm follows, but as objectives it optimizes toward.

### F1: Letter recognition (highest weight)

Each glyph in the candidate must be recognizable as its intended letter. Measured by:

```python
def letter_recognition_fitness(candidate_glyph, intended_letter):
    # Render the glyph in isolation
    glyph_image = render_glyph(candidate_glyph)
    
    # Method A: Template matching against reference exemplars
    # Use 5-10 exemplars of each letter extracted from the target manuscript
    exemplars = load_exemplars(intended_letter)
    best_match = max(
        template_match_score(glyph_image, ex) for ex in exemplars
    )
    
    # Method B: Structural matching against the letterform guide
    # Check that the glyph passes through the required structural keypoints
    guide = letterform_guides[intended_letter]
    keypoint_hits = sum(
        1 for kp in guide.keypoints 
        if glyph_passes_near(candidate_glyph, kp.position, kp.flexibility)
    ) / len(guide.keypoints)
    
    # Method C: OCR verification (expensive but definitive)
    # Run a simple character classifier on the rendered glyph
    # ocr_score = classify(glyph_image, intended_letter)
    
    return 0.5 * best_match + 0.5 * keypoint_hits
```

### F2: Thick/thin contrast

The rendered strokes must show nib-angle-dependent width variation:

```python
def thick_thin_fitness(candidate_word):
    rendered = render_word(candidate_word)
    stroke_widths = extract_stroke_widths(rendered)
    
    # The ratio of thickest to thinnest strokes should be 3:1 to 5:1
    ratio = max(stroke_widths) / max(min(stroke_widths), 0.1)
    target_ratio = 4.0
    
    return 1.0 - abs(ratio - target_ratio) / target_ratio
```

### F3: Connection flow

Adjacent glyphs within the word should be connected by visible hairline strokes:

```python
def connection_fitness(candidate_word):
    rendered = render_word(candidate_word)
    
    connections_present = 0
    connections_expected = len(candidate_word.glyphs) - 1
    
    for i in range(connections_expected):
        zone = extract_inter_glyph_zone(rendered, i, i+1)
        if has_thin_connecting_stroke(zone):
            connections_present += 1
    
    return connections_present / max(connections_expected, 1)
```

### F4: Style consistency (Bastarda guardrails)

The overall appearance must be consistent with Bastarda:

```python
def style_fitness(candidate_word):
    rendered = render_word(candidate_word)
    
    scores = []
    
    # Ascender/descender proportions
    proportions = measure_proportions(rendered)
    scores.append(proportion_score(proportions, target_bastarda_proportions))
    
    # Slant consistency (should be ~5° rightward, ±2°)
    slant = measure_global_slant(rendered)
    scores.append(1.0 - abs(slant - 5.0) / 10.0)
    
    # Stroke angle distribution (Bastarda has characteristic angles)
    angles = extract_stroke_angles(rendered)
    scores.append(angle_distribution_score(angles, target_bastarda_angles))
    
    # Letter spacing regularity
    spacing = measure_inter_glyph_spacing(rendered)
    scores.append(spacing_regularity_score(spacing))
    
    return mean(scores)
```

### F5: Target manuscript similarity

Compare against the real manuscript sample:

```python
def target_similarity_fitness(candidate_word, target_crop):
    rendered = render_word(candidate_word)
    
    # Perceptual similarity using image features
    rendered_features = extract_features(rendered)  # CLIP, DINO, or VGG
    target_features = extract_features(target_crop)
    
    return cosine_similarity(rendered_features, target_features)
```

### F6: Smoothness / organic quality

The strokes should be smooth curves, not jagged or angular:

```python
def smoothness_fitness(candidate_word):
    total_curvature_penalty = 0
    
    for glyph in candidate_word.glyphs:
        for seg in glyph.segments:
            # Measure curvature at sample points along the Bézier
            curvatures = sample_curvature(seg, n_samples=20)
            
            # Penalize sudden curvature changes (indicates jaggedness)
            curvature_changes = [abs(curvatures[i+1] - curvatures[i]) 
                                  for i in range(len(curvatures)-1)]
            total_curvature_penalty += sum(c for c in curvature_changes if c > threshold)
    
    return 1.0 / (1.0 + total_curvature_penalty)
```

### F7: Continuity at glyph boundaries

The exit of glyph N and the entry of glyph N+1 should be smooth (no sudden direction change):

```python
def continuity_fitness(candidate_word):
    penalties = 0
    
    for i in range(len(candidate_word.glyphs) - 1):
        exit_seg = candidate_word.glyphs[i].segments[-1]
        entry_seg = candidate_word.glyphs[i+1].segments[0]
        
        # Position continuity: exit end ≈ entry start
        pos_gap = (exit_seg.p3 - entry_seg.p0).length()
        penalties += pos_gap
        
        # Direction continuity: exit tangent ≈ entry tangent
        exit_tangent = (exit_seg.p3 - exit_seg.p2).normalized()
        entry_tangent = (entry_seg.p1 - entry_seg.p0).normalized()
        angle_gap = exit_tangent.angle_between(entry_tangent).abs()
        penalties += angle_gap * 0.5  # weight direction less than position
    
    return 1.0 / (1.0 + penalties)
```

### Composite fitness

```python
def total_fitness(candidate, target_crop=None):
    f1 = letter_recognition_fitness(candidate)    # weight: 0.30
    f2 = thick_thin_fitness(candidate)             # weight: 0.10
    f3 = connection_fitness(candidate)             # weight: 0.15
    f4 = style_fitness(candidate)                  # weight: 0.15
    f5 = target_similarity_fitness(candidate, target_crop) if target_crop else 0.5  # weight: 0.10
    f6 = smoothness_fitness(candidate)             # weight: 0.10
    f7 = continuity_fitness(candidate)             # weight: 0.10
    
    return (0.30 * f1 + 0.10 * f2 + 0.15 * f3 + 
            0.15 * f4 + 0.10 * f5 + 0.10 * f6 + 0.10 * f7)
```

Letter recognition has the highest weight because nothing else matters if you can't read it.

---

## Part 3: The Evolutionary Algorithm

### Initialization

The initial population is NOT random. It's seeded from the existing letterform guides:

```python
def initialize_population(word_text, pop_size=100):
    population = []
    
    for _ in range(pop_size):
        # Start from the letterform guide (baseline quality)
        word_genome = WordGenome.from_guides(word_text)
        
        # Apply random perturbation to each layer
        word_genome.perturb_word_layer(sigma=0.5)   # small envelope changes
        word_genome.perturb_glyph_layer(sigma=0.3)  # small shape changes
        word_genome.perturb_stroke_layer(sigma=0.2)  # small pressure/speed changes
        
        population.append(word_genome)
    
    return population
```

By seeding from the guides, the initial population is already in the neighborhood of legible text. The evolution refines from there rather than searching from scratch.

### Selection

Tournament selection with elitism:

```python
def select(population, fitnesses, tournament_size=5, elite_count=5):
    # Keep the best N candidates unchanged (elitism)
    sorted_pop = sorted(zip(population, fitnesses), key=lambda x: -x[1])
    next_gen = [p for p, f in sorted_pop[:elite_count]]
    
    # Tournament selection for the rest
    while len(next_gen) < len(population):
        tournament = random.sample(list(zip(population, fitnesses)), tournament_size)
        winner = max(tournament, key=lambda x: x[1])[0]
        next_gen.append(winner)
    
    return next_gen
```

### Crossover (layer-aware)

Crossover operates differently at each layer:

```python
def crossover(parent_a, parent_b):
    child = WordGenome()
    
    # Word layer: blend (average the envelope parameters)
    child.word_layer = blend(parent_a.word_layer, parent_b.word_layer, ratio=0.5)
    
    # Glyph layer: per-glyph selection (take each glyph from one parent)
    for i in range(len(parent_a.glyphs)):
        if random.random() < 0.5:
            child.glyphs.append(deepcopy(parent_a.glyphs[i]))
        else:
            child.glyphs.append(deepcopy(parent_b.glyphs[i]))
    
    # Stroke layer: per-segment crossover within selected glyphs
    for glyph in child.glyphs:
        donor = random.choice([parent_a, parent_b])
        for j, seg in enumerate(glyph.segments):
            if random.random() < 0.3:  # 30% chance to swap stroke details
                donor_seg = donor.glyphs[i].segments[j] if j < len(donor.glyphs[i].segments) else seg
                seg.pressure_curve = deepcopy(donor_seg.pressure_curve)
                seg.speed_curve = deepcopy(donor_seg.speed_curve)
    
    return child
```

### Mutation (layer-specific rates and magnitudes)

```python
def mutate(genome, generation, fatigue=0.0, emotional_state="normal"):
    # Layer 1: Word envelope — rare, small mutations
    if random.random() < 0.1:  # 10% chance
        genome.word_layer.baseline_y += normal(0, 0.1)     # mm
        genome.word_layer.global_slant_deg += normal(0, 0.3)
    
    # Layer 2: Glyph shapes — moderate mutations
    for glyph in genome.glyphs:
        if random.random() < 0.3:  # 30% chance per glyph
            # Perturb 1-2 control points
            seg = random.choice(glyph.segments)
            point = random.choice(['p1', 'p2'])  # don't mutate endpoints (p0, p3)
            delta = Vec2(normal(0, 0.2), normal(0, 0.2))  # mm
            setattr(seg, point, getattr(seg, point) + delta)
    
    # Layer 3: Stroke details — frequent, small mutations
    for glyph in genome.glyphs:
        for seg in glyph.segments:
            if random.random() < 0.5:  # 50% chance per segment
                # Perturb pressure curve
                for k in range(len(seg.pressure_curve)):
                    seg.pressure_curve[k] += normal(0, 0.05)
                    seg.pressure_curve[k] = clamp(seg.pressure_curve[k], 0.1, 1.0)
    
    # --- CONTEXTUAL MODIFIERS ---
    
    # Fatigue: increases mutation magnitude over time (simulates
    # the scribe's hand becoming less precise)
    if fatigue > 0:
        fatigue_boost = 1.0 + fatigue * 0.5  # up to 50% larger mutations
        for glyph in genome.glyphs:
            for seg in glyph.segments:
                for point in ['p1', 'p2']:
                    if random.random() < fatigue * 0.2:  # more frequent perturbation
                        delta = Vec2(normal(0, 0.15 * fatigue_boost), 
                                     normal(0, 0.15 * fatigue_boost))
                        setattr(seg, point, getattr(seg, point) + delta)
    
    # Emotional state modifiers
    if emotional_state == "agitated":
        # Increased pressure variation, more slant drift
        for glyph in genome.glyphs:
            for seg in glyph.segments:
                for k in range(len(seg.pressure_curve)):
                    seg.pressure_curve[k] *= uniform(0.9, 1.2)  # more variable
        genome.word_layer.global_slant_deg += normal(0, 0.5)  # more slant drift
    
    elif emotional_state == "deliberate":
        # Smaller mutations, more precise
        # (reduce mutation magnitudes by 50%)
        pass  # achieved by running more generations with tighter mutation
    
    elif emotional_state == "compensating":
        # Wider spacing, more baseline drift
        genome.word_layer.word_width_mm *= uniform(1.0, 1.08)
        for i in range(len(genome.word_layer.baseline_drift)):
            genome.word_layer.baseline_drift[i] += normal(0, 0.08)
    
    return genome
```

### The main loop

```python
def evolve_word(word_text, target_crop=None, generations=200, 
                pop_size=100, fatigue=0.0, emotional_state="normal"):
    
    population = initialize_population(word_text, pop_size)
    best_ever = None
    best_fitness_ever = 0
    
    for gen in range(generations):
        # Evaluate fitness
        fitnesses = [total_fitness(ind, target_crop) for ind in population]
        
        # Track best
        gen_best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
        if fitnesses[gen_best_idx] > best_fitness_ever:
            best_fitness_ever = fitnesses[gen_best_idx]
            best_ever = deepcopy(population[gen_best_idx])
        
        # Log progress
        if gen % 20 == 0:
            log(f"Gen {gen}: best={max(fitnesses):.3f} mean={mean(fitnesses):.3f}")
        
        # Early stopping if fitness is good enough
        if best_fitness_ever > 0.85:
            break
        
        # Select
        selected = select(population, fitnesses)
        
        # Crossover
        next_gen = []
        for i in range(0, len(selected) - 1, 2):
            if random.random() < 0.7:  # 70% crossover rate
                child = crossover(selected[i], selected[i+1])
                next_gen.append(child)
            else:
                next_gen.append(deepcopy(selected[i]))
            next_gen.append(deepcopy(selected[i+1]))
        
        # Mutate (with contextual modifiers)
        population = [
            mutate(ind, gen, fatigue=fatigue, emotional_state=emotional_state) 
            for ind in next_gen
        ]
        
        # Re-insert elites unmutated
        population[:5] = [deepcopy(p) for p, f in 
                          sorted(zip(selected, fitnesses), key=lambda x: -x[1])[:5]]
    
    return best_ever
```

---

## Part 4: Rendering from Genomes

The genome doesn't replace the nib physics — it provides the paths, and the nib model renders them:

```python
def render_word(word_genome):
    canvas = create_canvas(word_genome.word_layer)
    ink_state = InkState(reservoir=word_genome.word_layer.ink_state_start)
    
    for i, glyph in enumerate(word_genome.glyphs):
        slant = word_genome.word_layer.global_slant_deg + word_genome.word_layer.slant_drift[i]
        baseline = word_genome.word_layer.baseline_y + word_genome.word_layer.baseline_drift[i]
        
        for seg in glyph.segments:
            # Transform segment by slant and baseline
            transformed = apply_slant_and_baseline(seg, slant, baseline)
            
            if transformed.contact:
                # Render using nib physics from TD-002/004
                render_bezier_stroke(
                    canvas,
                    curve=transformed,
                    nib_angle=40.0 + seg.nib_angle_drift,
                    nib_width=1.8,  # mm
                    pressure_curve=seg.pressure_curve,
                    speed_curve=seg.speed_curve,
                    ink_state=ink_state,
                )
                
                # Update ink state
                ink_state.deplete(seg.length())
    
    return canvas
```

The nib-angle width equation, the stroke foot/attack effects, the ink depletion — all from TD-002/004 — are applied during rendering. The evolutionary algorithm controls *what paths* are drawn; the nib physics controls *how those paths look as marks on the surface.*

---

## Part 5: Scaling from Words to Folios

### Word-level evolution (the core unit)

Each word is evolved independently but with context:
- The preceding word's exit state (position, angle, ink level) is the starting condition
- The following word's first letter influences the exit (via the style consistency fitness)
- CLIO-7 per-folio state (fatigue, emotional state) modifies mutation operators

### Line composition

```python
def evolve_line(line_text, target_line_crop=None, folio_state=None):
    words = line_text.split()
    evolved_words = []
    
    cursor_x = folio_state.margin_left + normal(0, 0.3)  # line start variation
    ink_state = folio_state.ink_state
    
    for i, word in enumerate(words):
        # Context for this word
        context = WordContext(
            position_x=cursor_x,
            baseline_y=folio_state.baseline_for_line(line_idx),
            ink_state=ink_state,
            preceding_word=evolved_words[-1] if evolved_words else None,
            following_word_initial=words[i+1][0] if i+1 < len(words) else None,
            fatigue=folio_state.fatigue,
            emotional_state=folio_state.emotional_state,
        )
        
        # Extract target crop for this word's approximate position
        target_crop = extract_word_crop(target_line_crop, cursor_x) if target_line_crop else None
        
        # Evolve this word
        evolved = evolve_word(
            word, 
            target_crop=target_crop,
            generations=150,  # fewer for non-critical words, more for important ones
            fatigue=context.fatigue,
            emotional_state=context.emotional_state,
        )
        
        evolved_words.append(evolved)
        cursor_x += evolved.total_width() + word_spacing(context)
        ink_state = evolved.final_ink_state()
        
        # Dip check
        if ink_state.reservoir < 0.15:
            ink_state.dip()  # refill
    
    return compose_line(evolved_words)
```

### Folio composition

```python
def evolve_folio(folio_json, target_folio=None):
    folio_state = FolioState.from_json(folio_json)
    lines = []
    
    for line_idx, line_text in enumerate(folio_state.lines):
        target_crop = extract_line_crop(target_folio, line_idx) if target_folio else None
        
        evolved_line = evolve_line(
            line_text,
            target_line_crop=target_crop,
            folio_state=folio_state,
        )
        lines.append(evolved_line)
        
        # Update folio state for next line
        folio_state.advance_line()
        
        # Log progress
        log(f"Line {line_idx}/{len(folio_state.lines)}: fitness={evolved_line.best_fitness:.3f}")
    
    return compose_folio(lines, folio_state)
```

---

## Part 6: Performance Considerations

### This will be slow — and that's acceptable

A single word evolution (100 candidates × 200 generations = 20,000 fitness evaluations) with rendering at each evaluation is expensive. At a rough estimate:
- Rendering one word: ~5ms (Rust, low-res preview)
- Fitness evaluation: ~10ms (including metrics)
- Per word: ~300 seconds (5 minutes)
- Per line (~8 words): ~40 minutes
- Per folio (~30 lines): ~20 hours

This is not real-time, but we said it doesn't need to be fast yet. A folio rendered overnight is perfectly acceptable for this project.

### Optimizations (for later)

- **Caching:** many fitness sub-computations (stroke width extraction, feature extraction) can be cached across similar candidates
- **Coarse-to-fine:** evolve at low resolution first (50 DPI), then refine the best candidate at full resolution (300 DPI)
- **Warm starting:** use the evolved genome from the previous word as the seed for the next word, rather than initializing from guides each time
- **GPU-accelerated fitness:** batch-render candidates on GPU, batch-compute perceptual features
- **Reduced generations for common words:** balanced mode may reuse cached word
  genomes, but deep mode should re-evolve each occurrence; both modes should use
  style memory rather than exact cloning

### Parallelization

Each candidate in a generation can be evaluated independently:

```python
# Parallel fitness evaluation
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=8) as executor:
    fitnesses = list(executor.map(total_fitness, population))
```

---

## Part 7: How Contextual Factors Work

### Fatigue (CLIO-7: f14r onward)

Fatigue doesn't change the algorithm — it changes the mutation operators:
- Increased mutation magnitude on control points (hand less precise)
- Wider baseline drift mutations (harder to maintain position)
- Gradual word width increase (spacing opens up)
- Slightly reduced fitness threshold for letter recognition (accept slightly less precise forms)

### Emotional state (CLIO-7: per-folio)

Each emotional state modifies mutations and/or fitness weights:

| State | Mutation change | Fitness change |
|---|---|---|
| **agitated** (f06r) | Higher pressure variance, more slant drift | Increase weight on thick/thin (heavier strokes) |
| **deliberate** (f07r) | Smaller mutations, more generations | Increase weight on letter recognition (more precise) |
| **compensating** (f14r) | Wider spacing, baseline drift | Reduce weight on spacing regularity (accept wider) |
| **working** (f07v lower) | Scale glyphs to 85%, tighter mutations | Increase weight on style consistency (professional register) |

### Ink state

Ink depletion isn't evolved — it's computed deterministically from the word sequence. But it affects rendering: words near the end of a dip cycle are rendered with lighter strokes (less ink deposited). The fitness function doesn't penalize lighter strokes if they're consistent with the ink cycle position.

### Current operating profile

The current public folio renderer runs TD-007 in two quality modes:

- `balanced`: reuses evolved word genomes where appropriate, but still applies
  folio-level style memory
- `deep`: re-evolves each word occurrence and uses per-occurrence progress
  reporting

In both modes, the modern `evo` path is expected to:

- record its active renderer strategy in a render report
- keep page and pressure heatmap generation on the same evolved stroke sweep
- use soft priors from recent same-word history rather than exact template reuse

Contextual scribal memory and bounded character variation are specified in
TD-012.

---

## Part 8: Relationship to Existing TDs

### What we keep
- **TD-001:** interface contracts, folio JSON, PAGE XML — unchanged
- **TD-002:** nib physics, ink model, rendering passes 2-6 — used for rendering genomes
- **TD-003:** metrics M1-M9, M_conn — become fitness sub-functions
- **TD-004:** nib fixes (stroke feet, attack, thick/thin) — applied during genome rendering

### What we replace
- **TD-005:** generative hand simulation — replaced by evolutionary word generation
- **TD-006:** constrained dynamics, PD controller, sliding window — no longer needed

### What we reuse differently
- **TD-003 optimizer:** CMA-ES is no longer the primary optimization method (genetic algorithm replaces it), but CMA-ES could be used for fine-tuning the fitness function weights
- **TD-005 letterform guides:** become the seed for initial populations rather than the target for a physics simulation
- **TD-002 multi-scale model:** the folio/line/word/glyph hierarchy is preserved but implemented as nested evolution loops rather than nested physics simulations

---

## Implementation priority

1. **Genome representation + rendering from genome** — define the data structures, render a single word from a genome using existing nib physics. Verify it produces marks.

2. **Fitness function F1 (letter recognition)** — implement template matching against target exemplars. This is the most critical fitness term.

3. **Basic evolution loop** — initialize from guides, tournament selection, mutation (glyph layer only). Evolve "und" for 50 generations. Verify improvement.

4. **Full fitness function (F1-F7)** — add all fitness terms. Evolve "und" for 200 generations. Compare against target.

5. **Layer-specific mutation and crossover** — implement the three-layer mutation rates and the layer-aware crossover.

6. **Contextual modifiers** — add fatigue, emotional state, ink state effects on mutation operators.

7. **Line composition** — chain evolved words into lines with context passing.

8. **Full folio** — overnight rendering of all seventeen folios.

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-21 | Initial draft — multilayer evolutionary approach | shawn + claude |
| 2026-03-23 | Added current operating profile and TD-012 cross-reference | shawn + codex |
