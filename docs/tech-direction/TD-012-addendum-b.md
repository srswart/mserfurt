# TD-012 Addendum B — DP-Assisted Stroke Decomposition

## Context
Addendum A uses DP to segment words into glyph crops. This addendum uses DP to decompose a single glyph crop into its constituent strokes — the Bézier segments and pressure profiles that describe how the scribe's pen moved to form that letter.

Currently this decomposition happens via evolutionary extraction (TD-008): evolve a genome until the rendered output matches the crop. This works but is slow (minutes per glyph) and opaque (you can't see or adjust the intermediate stroke structure).

The DP approach proposes the stroke decomposition interactively — the Workbench shows the proposed strokes overlaid on the glyph crop, and the operator can accept, nudge control points, add/remove strokes, or adjust pressure before committing. The result is a high-quality allograph genome that's been human-verified at the stroke level.

---

## Part 1: What We're Decomposing

A glyph crop is a small image (~40-80px tall, 20-60px wide) containing one letter. Inside that image, the scribe made a series of pen movements:

```
Example: the letter 'n'

Stroke 1: pen down at top-left, draw minim downward to baseline
           (thick downstroke — nib perpendicular to travel direction)
           
Stroke 2: pen curves up from baseline, arches rightward to top of second minim
           (thin arch — nib nearly parallel to travel direction)
           
Stroke 3: pen draws second minim downward to baseline
           (thick downstroke again)

Pen lifts: possibly between stroke 1 and 2 (or continuous — scribe-dependent)
```

The decomposition needs to recover: the path of each stroke (as Bézier curves), the pressure along each stroke (which determines rendered width via nib physics), and where the pen lifted between strokes.

---

## Part 2: The Algorithm

### Step 1: Skeletonize the glyph

Extract the medial axis (skeleton) of the ink in the glyph crop. This produces a 1-pixel-wide representation of the writing path.

```rust
fn skeletonize(glyph_image: &GrayImage) -> Skeleton {
    let binary = binarize(glyph_image);
    let skeleton = zhang_suen_thinning(&binary);
    
    // Build a graph from the skeleton pixels
    let graph = skeleton_to_graph(&skeleton);
    // Nodes: branch points (3+ neighbors) and endpoints (1 neighbor)
    // Edges: chains of skeleton pixels between nodes
    
    graph
}
```

### Step 2: Measure width along the skeleton

At each skeleton pixel, measure the distance to the nearest ink edge. This is the half-width of the stroke at that point — a direct measurement of what the nib produced.

```rust
fn measure_widths(glyph_image: &GrayImage, skeleton: &Skeleton) -> Vec<f64> {
    let binary = binarize(glyph_image);
    let distance_transform = cv_distance_transform(&binary);
    
    skeleton.pixels.iter().map(|&(x, y)| {
        distance_transform[(y, x)] as f64 * 2.0  // full width = 2 × half-width
    }).collect()
}
```

### Step 3: Structural template for the letter

Each letter has an expected stroke structure — the number of strokes, their approximate directions, and their order. This comes from paleographic knowledge of Bastarda:

```rust
fn stroke_template(letter: char) -> StrokeTemplate {
    match letter {
        'n' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: Down, weight: Heavy, name: "first_minim" },
                ExpectedStroke { direction: UpRight, weight: Light, name: "arch" },
                ExpectedStroke { direction: Down, weight: Heavy, name: "second_minim" },
            ],
            lifts: vec![PossibleLift::Between(0, 1)],  // may lift between minim and arch
        },
        'm' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: Down, weight: Heavy, name: "first_minim" },
                ExpectedStroke { direction: UpRight, weight: Light, name: "first_arch" },
                ExpectedStroke { direction: Down, weight: Heavy, name: "second_minim" },
                ExpectedStroke { direction: UpRight, weight: Light, name: "second_arch" },
                ExpectedStroke { direction: Down, weight: Heavy, name: "third_minim" },
            ],
            lifts: vec![],
        },
        'd' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: CurveLeft, weight: Medium, name: "bowl_left" },
                ExpectedStroke { direction: CurveRight, weight: Light, name: "bowl_right" },
                ExpectedStroke { direction: Up, weight: Heavy, name: "ascender" },
                ExpectedStroke { direction: CurveLeft, weight: Light, name: "ascender_hook" },
            ],
            lifts: vec![PossibleLift::Between(1, 2)],
        },
        'e' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: CurveRight, weight: Light, name: "approach" },
                ExpectedStroke { direction: CurveLeft, weight: Medium, name: "loop" },
                ExpectedStroke { direction: DownRight, weight: Medium, name: "exit" },
            ],
            lifts: vec![],
        },
        'a' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: CurveLeft, weight: Medium, name: "bowl" },
                ExpectedStroke { direction: Down, weight: Heavy, name: "downstroke" },
            ],
            lifts: vec![PossibleLift::Between(0, 1)],
        },
        'i' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: Down, weight: Heavy, name: "minim" },
                ExpectedStroke { direction: Dot, weight: Light, name: "dot" },
            ],
            lifts: vec![PossibleLift::Between(0, 1)],  // always lifts before dot
        },
        'o' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: CurveLeft, weight: Medium, name: "left_curve" },
                ExpectedStroke { direction: CurveRight, weight: Medium, name: "right_curve" },
            ],
            lifts: vec![],
        },
        'r' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: Down, weight: Heavy, name: "minim" },
                ExpectedStroke { direction: UpRight, weight: Light, name: "shoulder" },
            ],
            lifts: vec![],
        },
        't' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: Down, weight: Heavy, name: "stem" },
                ExpectedStroke { direction: Right, weight: Light, name: "crossbar" },
            ],
            lifts: vec![PossibleLift::Between(0, 1)],
        },
        'ſ' => StrokeTemplate {  // long s
            strokes: vec![
                ExpectedStroke { direction: CurveRight, weight: Light, name: "top_hook" },
                ExpectedStroke { direction: Down, weight: Heavy, name: "descender" },
            ],
            lifts: vec![],
        },
        'b' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: Down, weight: Heavy, name: "ascender_stem" },
                ExpectedStroke { direction: CurveRight, weight: Medium, name: "bowl_out" },
                ExpectedStroke { direction: CurveLeft, weight: Medium, name: "bowl_return" },
            ],
            lifts: vec![],
        },
        'h' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: Down, weight: Heavy, name: "ascender_stem" },
                ExpectedStroke { direction: UpRight, weight: Light, name: "arch" },
                ExpectedStroke { direction: Down, weight: Heavy, name: "second_minim" },
            ],
            lifts: vec![],
        },
        'c' => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: CurveLeft, weight: Medium, name: "open_curve" },
            ],
            lifts: vec![],
        },
        // ... define for all letters
        _ => StrokeTemplate {
            strokes: vec![
                ExpectedStroke { direction: Down, weight: Heavy, name: "main_stroke" },
            ],
            lifts: vec![],
        },
    }
}
```

### Step 4: DP alignment of skeleton graph to stroke template

The skeleton graph has branches and paths. The stroke template expects a specific sequence of strokes. The DP finds the optimal way to assign skeleton paths to template strokes:

```rust
fn dp_stroke_decomposition(
    skeleton_graph: &SkeletonGraph,
    width_measurements: &[f64],
    template: &StrokeTemplate,
    letter: char,
) -> Vec<ProposedStroke> {
    // Enumerate all possible traversals of the skeleton graph
    // that visit all edges (an Euler-path-like problem on a small graph)
    let traversals = enumerate_traversals(skeleton_graph);
    
    // For each traversal, align it to the stroke template using DP
    let mut best_decomposition = None;
    let mut best_cost = f64::MAX;
    
    for traversal in &traversals {
        // The traversal is a sequence of skeleton pixels in writing order
        // We need to split this sequence into segments matching the template strokes
        
        let n_strokes = template.strokes.len();
        let n_pixels = traversal.len();
        
        // DP: dp[s][p] = min cost to assign strokes 0..s using pixels 0..p
        let mut dp = vec![vec![f64::MAX; n_pixels + 1]; n_strokes + 1];
        let mut back = vec![vec![0usize; n_pixels + 1]; n_strokes + 1];
        dp[0][0] = 0.0;
        
        for s in 1..=n_strokes {
            let expected = &template.strokes[s - 1];
            let (min_len, max_len) = expected_stroke_length_range(expected, n_pixels);
            
            for p in 1..=n_pixels {
                let earliest = if p > max_len { p - max_len } else { 0 };
                let latest = if p > min_len { p - min_len } else { 0 };
                
                for p_start in earliest..=latest {
                    if dp[s - 1][p_start] == f64::MAX { continue; }
                    
                    let segment_pixels = &traversal[p_start..p];
                    let segment_widths = &width_measurements[p_start..p];
                    
                    let cost = stroke_match_cost(expected, segment_pixels, segment_widths);
                    
                    // Lift cost: if template says possible lift here, check for gaps
                    let lift_cost = if s > 1 && template.has_possible_lift(s - 2, s - 1) {
                        evaluate_lift(traversal, p_start)
                    } else {
                        0.0
                    };
                    
                    let total = dp[s - 1][p_start] + cost + lift_cost;
                    if total < dp[s][p] {
                        dp[s][p] = total;
                        back[s][p] = p_start;
                    }
                }
            }
        }
        
        // Find best endpoint
        let final_cost = dp[n_strokes].iter()
            .enumerate()
            .filter(|(p, _)| *p >= n_pixels - n_pixels / 10)  // allow slack
            .min_by(|a, b| a.1.partial_cmp(b.1).unwrap())
            .map(|(_, &c)| c)
            .unwrap_or(f64::MAX);
        
        if final_cost < best_cost {
            best_cost = final_cost;
            best_decomposition = Some(traceback_strokes(
                &dp, &back, traversal, width_measurements, template
            ));
        }
    }
    
    best_decomposition.unwrap_or_default()
}
```

### Step 5: Fit Bézier curves to each stroke segment

Once the skeleton pixels are assigned to strokes, fit cubic Bézier curves:

```rust
fn fit_stroke_to_bezier(
    pixels: &[(usize, usize)],
    widths: &[f64],
    nib_angle: f64,
) -> ProposedStroke {
    // Convert pixel coordinates to mm coordinates
    let points: Vec<Vec2> = pixels.iter()
        .map(|&(x, y)| pixel_to_mm(x, y))
        .collect();
    
    // Fit Bézier curves (Schneider's algorithm)
    let bezier_segments = fit_bezier_chain(&points, max_error_mm: 0.1);
    
    // Derive pressure from measured width + nib angle
    // Width = nib_width * |sin(direction - nib_angle)| * pressure
    // Therefore: pressure = width / (nib_width * |sin(direction - nib_angle)|)
    let pressures: Vec<f64> = points.windows(2)
        .zip(widths.iter())
        .map(|(pair, &width)| {
            let direction = (pair[1] - pair[0]).angle();
            let nib_factor = (direction - nib_angle).sin().abs().max(0.1);
            let estimated_pressure = width / (NI_WIDTH * nib_factor);
            estimated_pressure.clamp(0.1, 1.0)
        })
        .collect();
    
    // Sample pressure at Bézier parameter values
    let pressure_per_segment = distribute_pressures(&bezier_segments, &pressures);
    
    ProposedStroke {
        segments: bezier_segments,
        pressures: pressure_per_segment,
        contact: true,  // assume contact unless this is a lift segment
        name: String::new(),  // filled in from template
    }
}
```

### The pressure derivation is key

The measured width at each point, combined with the known stroke direction and nib angle, lets us solve for pressure directly:

```
measured_width = nib_width × |sin(direction - nib_angle)| × pressure

Therefore:

pressure = measured_width / (nib_width × |sin(direction - nib_angle)|)
```

This means the pressure profile isn't guessed or evolved — it's **measured** from the glyph image. The thick/thin pattern in the original manuscript directly produces the pressure curve. When this allograph is later rendered through the nib model, it reproduces the original stroke widths because the pressure was derived from those widths.

---

## Part 3: Workbench Integration

### The decomposition review UI

```
┌──────────────────────────────────────────────────────────────────┐
│  Glyph: 'n' from "nicht" (Cgm 100, f003r)                      │
│                                                                  │
│  ┌────────────────────────┐   ┌────────────────────────┐        │
│  │                        │   │     ╱ ← arch (thin)    │        │
│  │    [glyph crop]        │   │    ╱                    │        │
│  │                        │   │   ║          ║          │        │
│  │                        │   │   ║ minim 1  ║ minim 2  │        │
│  │                        │   │   ║ (thick)  ║ (thick)  │        │
│  └────────────────────────┘   └────────────────────────┘        │
│     Original image              Proposed strokes overlaid        │
│                                                                  │
│  Strokes:                                                        │
│  ┌────────────────────────────────────────────────────────┐      │
│  │ 1. first_minim  ████████████░░  dir: ↓  p: 0.85  ✓   │      │
│  │ 2. arch          ███░░░░░░░░░░  dir: ↗  p: 0.35  ✓   │      │
│  │ 3. second_minim ████████████░░  dir: ↓  p: 0.82  ✓   │      │
│  └────────────────────────────────────────────────────────┘      │
│  Pressure bars: ████ = measured pressure along stroke            │
│                                                                  │
│  Confidence: 0.91                                                │
│                                                                  │
│  Controls:                                                       │
│  • Click a stroke to select → drag control points to adjust      │
│  • Right-click to split a stroke into two                        │
│  • Delete key to remove a stroke                                 │
│  • 'A' key to add a new stroke                                   │
│  • Drag pressure bar endpoints to adjust pressure profile        │
│                                                                  │
│  [ Accept ]  [ Re-analyze ]  [ Reset to Proposal ]               │
│                                                                  │
│  Preview: ┌──────────────┐                                       │
│           │  rendered 'n' │  ← live preview: renders from        │
│           │  from current │    current Bézier + pressure          │
│           │  strokes      │    through nib model                  │
│           └──────────────┘                                       │
│  Match score: 0.88 (overlay comparison with original)            │
└──────────────────────────────────────────────────────────────────┘
```

### The live preview loop

As the operator adjusts control points or pressure values, the Workbench re-renders the glyph through the nib model in real time and shows:
- The rendered output overlaid on the original crop (alignment check)
- A match score (how closely the rendered output matches the original)
- A side-by-side: original | proposed strokes | rendered from strokes

This gives immediate feedback: if you drag a control point and the rendered output stops matching the original, you know you've moved it too far.

```rust
fn live_preview(
    proposed_strokes: &[ProposedStroke],
    original_crop: &GrayImage,
    nib: &NibConfig,
) -> PreviewResult {
    // Render from the current stroke description
    let rendered = render_allograph(proposed_strokes, nib);
    
    // Compare against original
    let match_score = compute_match_score(&rendered, original_crop);
    
    // Generate overlay image
    let overlay = blend_images(&rendered, original_crop, 0.5);
    
    PreviewResult {
        rendered,
        overlay,
        match_score,
    }
}
```

---

## Part 4: From Proposal to Allograph Genome

When the operator accepts the decomposition (possibly after adjustments), the proposed strokes become the allograph genome:

```rust
fn finalize_allograph(
    proposed: &[ProposedStroke],
    letter: char,
    source_metadata: &AnnotationMetadata,
) -> AllographGenome {
    AllographGenome {
        letter,
        source_manuscript: source_metadata.manuscript.clone(),
        source_folio: source_metadata.folio.clone(),
        source_word: source_metadata.word.clone(),
        instance_id: generate_id(),
        
        segments: proposed.iter().flat_map(|stroke| {
            stroke.segments.iter().map(|seg| BezierSegment {
                p0: seg.p0,
                p1: seg.p1,
                p2: seg.p2,
                p3: seg.p3,
                contact: stroke.contact,
                pressure: stroke.pressures.clone(),
            })
        }).collect(),
        
        // Entry/exit geometry from first/last strokes
        entry_point: proposed.first().unwrap().segments.first().unwrap().p0,
        entry_angle: proposed.first().unwrap().entry_angle(),
        entry_pressure: proposed.first().unwrap().pressures.first().copied().unwrap_or(0.5),
        
        exit_point: proposed.last().unwrap().segments.last().unwrap().p3,
        exit_angle: proposed.last().unwrap().exit_angle(),
        exit_pressure: proposed.last().unwrap().pressures.last().copied().unwrap_or(0.5),
        
        // Metrics computed from the strokes
        x_advance: compute_x_advance(proposed),
        weight: compute_overall_weight(proposed),
        width_ratio: compute_width_ratio(proposed),
        
        // Context from annotation
        observed_predecessor: source_metadata.predecessor,
        observed_successor: source_metadata.successor,
        word_position: source_metadata.position,
        
        extraction_fitness: live_preview_match_score,
    }
}
```

This replaces the evolutionary extraction (TD-008) for cases where the DP decomposition + human review produces a good result. The evolutionary approach remains available as a fallback for glyphs where the skeleton analysis fails (heavily connected letters, damaged ink, unusual forms).

---

## Part 5: The Complete Extraction Workflow

```
1. Select a word in the Workbench from the reference manuscript
2. Type the transcription: "schreiber"
3. Addendum A (word DP): segments the word into 9 glyph crops
4. Operator reviews/nudges boundaries
5. For each accepted glyph crop:
   a. Addendum B (stroke DP): proposes stroke decomposition
   b. Workbench shows strokes overlaid on crop + live rendered preview
   c. Operator reviews:
      - Accept (most cases — decomposition is correct)
      - Nudge control points (drag to adjust)
      - Adjust pressure (drag pressure bar)
      - Split/add/remove strokes (rare)
   d. Accept → allograph genome saved to library
6. Repeat for next word
```

**Time per word (estimated):**
- Type transcription: 3 seconds
- Review word segmentation: 3 seconds
- Review 8 stroke decompositions: 3-5 seconds each × 8 = 24-40 seconds
- Total per word: ~30-45 seconds

**Compare to fully manual:** 5-10 minutes per word (drawing every boundary and every stroke by hand)

**Compare to evolutionary extraction (TD-008):** 20 minutes per word of computation, no human review of stroke structure

The DP-assisted approach is faster than both and produces human-verified results at the stroke level.

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-27 | Initial draft — DP stroke decomposition within glyphs | shawn + claude |
