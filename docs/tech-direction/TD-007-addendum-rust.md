# TD-007 Addendum A — Rust Acceleration

## Context
TD-007's evolutionary loop requires ~20,000 render+evaluate cycles per word. In pure Python this is ~5 minutes per word. With Rust handling the inner loop (rendering + fitness evaluation), we target ~30-60 seconds per word — fast enough for interactive iteration during development.

## Architecture: Batch Evaluation in Rust

The critical insight: don't call Rust once per candidate. Send the entire generation as a batch and get back a vector of fitness scores.

### Python side (evolutionary logic)

```python
import scribesim_evo  # the Rust extension module

class EvolutionEngine:
    def __init__(self, config, target_exemplars):
        # Initialize the Rust evaluator once with shared data
        # that doesn't change between generations:
        # - nib parameters
        # - target exemplars (pre-loaded images)
        # - fitness weights
        # - rendering config (DPI, canvas size)
        self.evaluator = scribesim_evo.BatchEvaluator(
            nib_config=config.nib,
            exemplars=target_exemplars,  # passed as numpy arrays
            fitness_weights=config.fitness_weights,
            render_width_px=config.preview_width,
            render_height_px=config.preview_height,
            render_dpi=config.preview_dpi,  # 72-100 DPI for evolution, 300 for final
        )
    
    def evaluate_generation(self, population):
        # Serialize all genomes into a flat representation Rust can consume
        genome_batch = [genome.to_rust_repr() for genome in population]
        
        # Single call to Rust — evaluates entire generation
        # Returns: list of (total_fitness, per_metric_scores) tuples
        results = self.evaluator.evaluate_batch(genome_batch)
        
        return results
    
    def evolve_word(self, word_text, generations=200, pop_size=100, **context):
        population = self.initialize_population(word_text, pop_size)
        
        for gen in range(generations):
            # ONE Rust call per generation — evaluates all candidates
            results = self.evaluate_generation(population)
            fitnesses = [r.total for r in results]
            
            # Python handles selection, crossover, mutation
            selected = self.select(population, fitnesses)
            offspring = self.crossover_and_mutate(selected, **context)
            population = offspring
        
        return self.best_candidate(population, results)
```

### Rust side (batch rendering + evaluation)

```rust
use pyo3::prelude::*;
use numpy::PyArray1;
use rayon::prelude::*;  // parallel iteration

#[pyclass]
struct BatchEvaluator {
    nib: NibConfig,
    exemplars: HashMap<char, Vec<GrayImage>>,  // target letter images
    fitness_weights: FitnessWeights,
    canvas_width: u32,
    canvas_height: u32,
    dpi: f64,
}

#[pymethods]
impl BatchEvaluator {
    #[new]
    fn new(nib_config: PyNibConfig, exemplars: HashMap<char, Vec<&PyArray2<u8>>>, 
           fitness_weights: PyFitnessWeights, render_width_px: u32, 
           render_height_px: u32, render_dpi: f64) -> Self {
        // Convert Python data to Rust-native types (one-time cost)
        BatchEvaluator {
            nib: nib_config.into(),
            exemplars: convert_exemplars(exemplars),
            fitness_weights: fitness_weights.into(),
            canvas_width: render_width_px,
            canvas_height: render_height_px,
            dpi: render_dpi,
        }
    }
    
    fn evaluate_batch(&self, genomes: Vec<PyGenome>) -> Vec<PyFitnessResult> {
        // Convert Python genomes to Rust-native representation
        let rust_genomes: Vec<WordGenome> = genomes.iter()
            .map(|g| g.into())
            .collect();
        
        // PARALLEL evaluation using rayon
        let results: Vec<FitnessResult> = rust_genomes.par_iter()
            .map(|genome| self.evaluate_single(genome))
            .collect();
        
        results.into_iter().map(|r| r.into()).collect()
    }
}

impl BatchEvaluator {
    fn evaluate_single(&self, genome: &WordGenome) -> FitnessResult {
        // 1. Render the word from the genome
        let canvas = self.render_word(genome);
        
        // 2. Compute all fitness metrics
        let f1 = self.letter_recognition(&canvas, genome);
        let f2 = self.thick_thin_contrast(&canvas);
        let f3 = self.connection_flow(&canvas, genome);
        let f4 = self.style_consistency(&canvas);
        let f5 = self.smoothness(genome);
        let f6 = self.continuity(genome);
        
        // 3. Weighted composite
        let total = self.fitness_weights.f1 * f1
                  + self.fitness_weights.f2 * f2
                  + self.fitness_weights.f3 * f3
                  + self.fitness_weights.f4 * f4
                  + self.fitness_weights.f5 * f5
                  + self.fitness_weights.f6 * f6;
        
        FitnessResult { total, f1, f2, f3, f4, f5, f6 }
    }
    
    fn render_word(&self, genome: &WordGenome) -> GrayImage {
        let mut canvas = GrayImage::new(self.canvas_width, self.canvas_height);
        let mut ink = InkState::new(genome.word_layer.ink_state_start);
        
        for (i, glyph) in genome.glyphs.iter().enumerate() {
            let slant = genome.word_layer.global_slant_deg 
                      + genome.word_layer.slant_drift[i];
            let baseline = genome.word_layer.baseline_y 
                         + genome.word_layer.baseline_drift[i];
            
            for seg in &glyph.segments {
                if seg.contact {
                    self.render_bezier_stroke(
                        &mut canvas, seg, slant, baseline, &mut ink
                    );
                }
            }
        }
        canvas
    }
    
    fn render_bezier_stroke(&self, canvas: &mut GrayImage, seg: &BezierSegment,
                            slant: f64, baseline: f64, ink: &mut InkState) {
        // Sample the Bézier at fine intervals
        let n_samples = 50;
        for i in 0..n_samples {
            let t = i as f64 / n_samples as f64;
            
            // Position on curve
            let pos = seg.evaluate(t);
            let pos = apply_slant(pos, slant, baseline);
            
            // Direction at this point (for nib-angle width)
            let tangent = seg.tangent(t);
            let direction = tangent.angle();
            
            // Pressure from the genome's pressure curve
            let pressure = seg.pressure_at(t);
            
            // Speed from the genome's speed curve
            let speed = seg.speed_at(t);
            
            // Nib-angle width computation (TD-002/004)
            let direction_width = self.nib.width_mm 
                * (direction - self.nib.angle_rad).sin().abs();
            let pressure_mod = 0.8 + 0.4 * pressure;
            let min_hairline = self.nib.width_mm * self.nib.cut_quality * 0.08;
            let mark_width = (direction_width * pressure_mod).max(min_hairline);
            
            // Stroke foot effect (TD-004)
            let (foot_w, foot_ink) = stroke_foot_effect(t);
            let mark_width = mark_width * foot_w;
            
            // Ink deposit
            let darkness = ink.deposit(pressure, speed) * foot_ink;
            
            // Rasterize: stamp a circle/ellipse of mark_width at pos
            stamp_mark(canvas, pos, mark_width, darkness, self.dpi);
        }
    }
    
    // --- FITNESS FUNCTIONS (all in Rust for speed) ---
    
    fn letter_recognition(&self, canvas: &GrayImage, genome: &WordGenome) -> f64 {
        let mut total_score = 0.0;
        
        for (i, glyph) in genome.glyphs.iter().enumerate() {
            let letter = genome.letter_sequence[i];
            
            // Extract glyph bounding box from canvas
            let glyph_img = extract_glyph_region(canvas, glyph);
            
            // Compare against exemplars using normalized cross-correlation
            if let Some(exemplars) = self.exemplars.get(&letter) {
                let best_match = exemplars.iter()
                    .map(|ex| normalized_cross_correlation(&glyph_img, ex))
                    .fold(0.0f64, f64::max);
                total_score += best_match;
            }
        }
        
        total_score / genome.glyphs.len() as f64
    }
    
    fn thick_thin_contrast(&self, canvas: &GrayImage) -> f64 {
        let widths = extract_stroke_widths_fast(canvas);
        if widths.is_empty() { return 0.0; }
        
        let max_w = widths.iter().cloned().fold(0.0f64, f64::max);
        let min_w = widths.iter().cloned().fold(f64::MAX, f64::min).max(0.1);
        let ratio = max_w / min_w;
        
        let target_ratio = 4.0;
        1.0 - ((ratio - target_ratio).abs() / target_ratio).min(1.0)
    }
    
    fn connection_flow(&self, canvas: &GrayImage, genome: &WordGenome) -> f64 {
        let mut connections_good = 0;
        let n_connections = genome.glyphs.len().saturating_sub(1);
        if n_connections == 0 { return 1.0; }
        
        for i in 0..n_connections {
            let zone = extract_connection_zone(canvas, &genome.glyphs[i], &genome.glyphs[i+1]);
            if has_thin_stroke(&zone) {
                connections_good += 1;
            }
        }
        
        connections_good as f64 / n_connections as f64
    }
    
    fn style_consistency(&self, canvas: &GrayImage) -> f64 {
        let slant = measure_global_slant(canvas);
        let slant_score = 1.0 - ((slant - 5.0).abs() / 10.0).min(1.0);
        
        let proportions = measure_proportions(canvas);
        let prop_score = proportion_match(proportions, &BASTARDA_TARGET_PROPORTIONS);
        
        0.5 * slant_score + 0.5 * prop_score
    }
    
    fn smoothness(&self, genome: &WordGenome) -> f64 {
        let mut penalty = 0.0;
        
        for glyph in &genome.glyphs {
            for seg in &glyph.segments {
                let curvatures = seg.sample_curvature(20);
                for i in 0..curvatures.len()-1 {
                    let change = (curvatures[i+1] - curvatures[i]).abs();
                    if change > 0.5 {  // threshold for "too jagged"
                        penalty += change;
                    }
                }
            }
        }
        
        1.0 / (1.0 + penalty)
    }
    
    fn continuity(&self, genome: &WordGenome) -> f64 {
        let mut penalty = 0.0;
        
        for i in 0..genome.glyphs.len()-1 {
            let exit = genome.glyphs[i].exit_point();
            let entry = genome.glyphs[i+1].entry_point();
            
            // Position gap
            penalty += (exit.pos - entry.pos).length();
            
            // Direction gap
            let exit_dir = genome.glyphs[i].exit_tangent();
            let entry_dir = genome.glyphs[i+1].entry_tangent();
            penalty += exit_dir.angle_between(entry_dir).abs() * 0.3;
        }
        
        1.0 / (1.0 + penalty)
    }
}
```

### Rayon parallelism

The `par_iter()` in `evaluate_batch` distributes candidates across all CPU cores automatically. On an 8-core machine, this gives ~8× speedup over sequential evaluation. No shared mutable state between candidates, so no synchronization overhead.

## Performance estimate with Rust + rayon

| Component | Python (per candidate) | Rust (per candidate) | Speedup |
|---|---|---|---|
| Render word (50 Bézier samples per segment) | ~5ms | ~0.1ms | 50× |
| Stroke width extraction | ~3ms | ~0.05ms | 60× |
| Template matching (5 exemplars) | ~8ms | ~0.15ms | 53× |
| Connection analysis | ~2ms | ~0.03ms | 67× |
| Other fitness terms | ~2ms | ~0.05ms | 40× |
| **Total per candidate** | **~20ms** | **~0.4ms** | **50×** |
| **Per generation (100 candidates, 8 cores)** | **2,000ms** | **~5ms** | **400×** |
| **Per word (200 generations)** | **400s (~7 min)** | **~1s** | **400×** |
| **Per line (8 words)** | **~55 min** | **~8s** | |
| **Per folio (30 lines)** | **~28 hours** | **~4 min** | |

With Rust + rayon, a full folio goes from overnight to a few minutes. Individual words evolve in about a second, making interactive tuning feasible.

## Preview vs. final rendering resolution

During evolution, render at low resolution for speed:

```rust
// Evolution mode: 72-100 DPI, small canvas
let preview_evaluator = BatchEvaluator::new(
    nib, exemplars, weights,
    render_width_px: 200,   // enough for one word
    render_height_px: 80,
    render_dpi: 72.0,
);

// Final rendering: 300 DPI, full folio
let final_renderer = FullRenderer::new(
    nib,
    render_dpi: 300.0,
);
let final_image = final_renderer.render_word(&best_genome);
```

The genome is resolution-independent (Bézier curves in mm coordinates). Evolve at 72 DPI, render the winner at 300 DPI for the final output.

## Crate structure

```
scribesim-evo/                   # new Rust crate (PyO3)
├── Cargo.toml
└── src/
    ├── lib.rs                   # PyO3 module definition
    ├── genome.rs                # WordGenome, GlyphGenome, StrokeGenome structs
    ├── render.rs                # Bézier rendering with nib physics
    ├── fitness/
    │   ├── mod.rs
    │   ├── recognition.rs       # F1: template matching
    │   ├── thick_thin.rs        # F2: stroke width analysis
    │   ├── connection.rs        # F3: inter-glyph connection detection
    │   ├── style.rs             # F4: Bastarda style consistency
    │   ├── smoothness.rs        # F5: curvature analysis
    │   └── continuity.rs        # F6: glyph boundary continuity
    ├── image_ops.rs             # image processing utilities
    └── batch.rs                 # BatchEvaluator, rayon parallel dispatch
```

This crate sits alongside the existing `scribesim-render` crate. The existing crate handles final high-resolution rendering; the new crate handles the evolutionary inner loop at preview resolution.

## Implementation priority

1. **Genome data structures in Rust** — `WordGenome`, `GlyphGenome`, `BezierSegment` with PyO3 bindings
2. **`render_word` in Rust** — port the existing nib physics rendering to operate on genomes at configurable DPI
3. **F1 (letter recognition) in Rust** — normalized cross-correlation against exemplars. This is the most critical fitness term.
4. **`evaluate_batch` with rayon** — parallel evaluation of an entire generation
5. **Python `EvolutionEngine` wrapper** — thin Python layer for the evolutionary logic
6. **Remaining fitness functions (F2-F6)** — implement in Rust, expose through batch evaluator
7. **Benchmark** — verify that per-word evolution completes in ~1-2 seconds
