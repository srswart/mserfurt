# Tech Direction: TD-010 — Ink Cycle Simulation

## Status
**Active** — integrates with current evolutionary renderer (TD-007) and nib physics (TD-004).

## Context
The current renderer produces letters with uniform ink darkness. Real manuscripts show a visible cyclical variation: dark after a fresh dip, gradually lighter as the quill depletes, then dark again after the next dip. This cycle is physically unavoidable — even a master scribe cannot eliminate it. It produces *motivated* variation: two instances of the same letter look different not because of random noise but because of where they fall in the ink cycle. This is one of the most recognizable signatures of handwritten (vs. printed) text and its absence is a major tell that our output is synthetic.

## What the ink cycle looks like in real manuscripts

Examining the Cgm 100 and Werbeschreiben references:
- Every 4-6 lines (roughly 30-50 words), there's a visible contrast boundary where the ink suddenly gets darker — this is a dip point
- The first word after a dip is noticeably darker, sometimes with a tiny blob at the first stroke
- The last word before a dip is lighter, with thinner hairlines and occasionally broken thin strokes
- The transition from dark to light within a cycle is gradual, not sudden
- A professional scribe's cycles are fairly regular but not metronomic — occasionally a dip comes early (ink-heavy passage) or late (light passage)

---

## Part 1: Ink State Model

### The reservoir

```rust
struct InkState {
    reservoir: f64,          // 0.0 (empty) to 1.0 (freshly dipped)
    strokes_since_dip: u32,  // counter for tracking dip rhythm
    words_since_dip: u32,    // for dip timing decisions
    total_dips: u32,         // for tracking across the folio
    
    // Physical properties (from nib/ink configuration)
    capacity: f64,           // how much ink the nib holds (1.0 = standard quill)
    base_depletion: f64,     // ink consumed per unit stroke length at standard pressure
    viscosity: f64,          // affects flow rate and lateral spread (0.5=thin, 1.0=standard, 1.5=thick)
}

impl InkState {
    fn new(capacity: f64) -> Self {
        InkState {
            reservoir: capacity,  // start full
            strokes_since_dip: 0,
            words_since_dip: 0,
            total_dips: 0,
            capacity,
            base_depletion: 0.0008,  // calibrate against real manuscripts
            viscosity: 1.0,
        }
    }
    
    fn dip(&mut self) {
        self.reservoir = self.capacity;
        self.strokes_since_dip = 0;
        self.words_since_dip = 0;
        self.total_dips += 1;
    }
    
    fn should_dip(&self) -> bool {
        self.reservoir < 0.15
    }
    
    fn wants_to_dip(&self) -> bool {
        // Scribe prefers to dip between words when getting low
        self.reservoir < 0.22
    }
}
```

### Depletion per stroke

Each rendered stroke consumes ink based on how much mark it deposits:

```rust
fn deplete_for_stroke(&mut self, stroke_length_mm: f64, avg_pressure: f64, avg_width_mm: f64) {
    // More ink consumed by:
    //   - longer strokes (more surface to cover)
    //   - higher pressure (more ink pressed out of nib)
    //   - wider strokes (more ink per unit length)
    let consumption = stroke_length_mm 
        * avg_pressure 
        * (avg_width_mm / 2.0)  // normalize to typical stroke width
        * self.base_depletion
        / self.viscosity;       // thicker ink depletes slower
    
    self.reservoir = (self.reservoir - consumption).max(0.0);
    self.strokes_since_dip += 1;
}
```

### Dip timing

A professional scribe dips between words when the reservoir gets low:

```rust
fn process_word_boundary(&mut self) -> DipEvent {
    self.words_since_dip += 1;
    
    if self.should_dip() {
        // Must dip — reservoir critically low
        self.dip();
        return DipEvent::ForcedDip;
    } else if self.wants_to_dip() {
        // Prefer to dip now (between words) rather than risk mid-word
        self.dip();
        return DipEvent::PreferredDip;
    }
    
    DipEvent::NoDip
}

enum DipEvent {
    NoDip,
    PreferredDip,  // clean dip between words
    ForcedDip,     // had to dip (was very low)
    // MidWordDip would be rare for a professional — maybe on f14r (fatigue)
}
```

---

## Part 2: How Ink State Affects Rendering

The ink state modifies three aspects of every rendered stroke:

### Effect 1: Darkness (continuous curve)

Darkness varies smoothly with reservoir level. No thresholds, no steps — a single continuous function that models how ink flow actually works:

```rust
fn ink_darkness(&self, base_darkness: f64) -> f64 {
    // Power curve: reservoir^0.4
    // At reservoir=1.0: curve=1.0 (full darkness)
    // At reservoir=0.5: curve=0.76 (barely lighter)
    // At reservoir=0.2: curve=0.53 (noticeably lighter)
    // At reservoir=0.05: curve=0.30 (quite light)
    //
    // The 0.4 exponent models real ink behavior:
    //   - Near full: large reservoir changes barely affect output
    //     (a nib at 80% looks almost identical to 100%)
    //   - Near empty: small reservoir changes are very visible
    //     (a nib at 5% looks much worse than at 15%)
    
    let flow_curve = self.reservoir.powf(0.4);
    
    // Map the curve to a darkness range
    // full nib: base_darkness * 1.12 (slightly boosted from saturation)
    // empty nib: base_darkness * 0.55 (quite faded)
    let min_factor = 0.55;
    let max_factor = 1.12;
    let factor = min_factor + (max_factor - min_factor) * flow_curve;
    
    base_darkness * factor
}
```

Why a power curve instead of linear: at reservoir=0.8, a linear model would reduce darkness by 20%. That's wrong — a quill at 80% is virtually indistinguishable from 100%. The power curve (0.8^0.4 = 0.91) correctly produces only a 9% reduction. Meanwhile at reservoir=0.1, linear gives 90% reduction (way too much), while the power curve (0.1^0.4 = 0.40) gives a 60% reduction (the ink is faint but not invisible — which is correct, because even a nearly dry quill leaves some mark).

### Effect 2: Stroke width modulation (continuous curve)

Ink spread is also continuous — more ink on the nib means more lateral wicking into the vellum surface:

```rust
fn ink_width_modifier(&self) -> f64 {
    // Saturated nib: ink spreads laterally, strokes slightly wider
    // Dry nib: minimal spread, strokes slightly thinner
    // The effect is subtle — max ±8% width change across the full cycle
    
    let flow_curve = self.reservoir.powf(0.5);  // slightly different exponent than darkness
    
    // Map: full=1.08 (8% wider), empty=0.94 (6% thinner)
    0.94 + 0.14 * flow_curve
}
```

### Effect 3: Hairline quality (continuous probability curves)

Hairline degradation is NOT a threshold event. The probability of gaps, thinning, and raking increases continuously as the reservoir drops. Even at 50% reservoir there's a tiny (nearly zero) chance of a hairline gap; at 5% it's quite likely. The curve shape ensures the effect is imperceptible in the normal range and only becomes visible when the quill is genuinely running dry.

```rust
struct HairlineEffects {
    width_reduction: f64,     // 0.0 = no reduction, 0.5 = half width
    gap_probability: f64,     // per-sample-point probability of a gap
    raking_probability: f64,  // per-stroke probability of split-nib effect
}

fn hairline_effects(&self) -> HairlineEffects {
    // All effects use sigmoid-like curves centered at low reservoir levels
    // so they're effectively zero above ~0.4 and increase smoothly below
    
    // Width reduction: starts becoming noticeable below reservoir ~0.3
    // Uses a soft-knee curve: 1/(1+exp(k*(x-center)))
    let width_sigmoid = 1.0 / (1.0 + ((self.reservoir - 0.18) * 15.0).exp());
    let width_reduction = width_sigmoid * 0.45;  // max 45% reduction at empty
    
    // Gap probability: starts becoming nonzero below reservoir ~0.25
    let gap_sigmoid = 1.0 / (1.0 + ((self.reservoir - 0.15) * 18.0).exp());
    let gap_probability = gap_sigmoid * 0.25;  // max 25% gap chance at empty
    
    // Raking (split nib): only at very low levels, below ~0.12
    let rake_sigmoid = 1.0 / (1.0 + ((self.reservoir - 0.08) * 25.0).exp());
    let raking_probability = rake_sigmoid * 0.30;  // max 30% raking at empty
    
    HairlineEffects { width_reduction, gap_probability, raking_probability }
}
```

The sigmoid function is the key: `1/(1+exp(k*(reservoir - center)))`. The `center` parameter controls where the effect "turns on" (0.18 for width, 0.15 for gaps, 0.08 for raking — progressively lower, because raking only happens when truly dry). The `k` parameter controls how sharp the transition is (higher = sharper, but never a step). At reservoir=0.5, all three effects are effectively zero. At reservoir=0.1, width reduction and gaps are significant. At reservoir=0.02, raking becomes likely.

This means there are no discrete states (Solid/Thinning/Breaking). Every reservoir level produces a unique combination of effects along continuous gradients. The renderer simply evaluates these curves at the current reservoir and applies the results:
```

### Effect 4: Post-dip blob (occasional)

After a dip, the first contact with the vellum sometimes deposits a small excess ink blob:

```rust
fn post_dip_blob(&self) -> Option<BlobParams> {
    if self.strokes_since_dip == 0 && self.reservoir > 0.90 {
        // First stroke after a dip — chance of a small blob
        if random() < 0.15 {  // 15% chance for a careful scribe (higher for a hasty one)
            Some(BlobParams {
                radius_mm: 0.2 + random() * 0.3,   // small, 0.2-0.5mm
                darkness_boost: 0.2,                 // 20% darker than surrounding ink
                shape: BlobShape::SlightlyElongated, // not a perfect circle
            })
        } else {
            None
        }
    } else {
        None
    }
}
```

---

## Part 3: Integration with the Rendering Pipeline

### Where ink state lives in the pipeline

The ink state is **not part of the genome** — it's computed deterministically from the writing sequence. This means:
- The evolutionary algorithm doesn't need to evolve ink parameters
- The same text always produces the same ink cycle (reproducible)
- Ink variation is layered on top of the evolved letterforms during rendering

```
Evolutionary algorithm (TD-007):
  → produces letter genomes (shape, pressure, structure)
  
Rendering pipeline:
  → iterates through words left to right
  → tracks InkState continuously
  → at each stroke: applies ink_darkness(), ink_width_modifier(), hairline_quality()
  → at each word boundary: checks should_dip() / wants_to_dip()
  → after dip: applies post_dip_blob() to first contact point
```

### Modified stroke rendering

The existing stroke renderer gains ink state as an input:

```rust
fn render_stroke_with_ink(
    canvas: &mut Canvas,
    points: &[Vec2],
    pressures: &[f64],
    nib: &NibConfig,
    ink: &mut InkState,
) {
    // Check for post-dip blob at first point
    if let Some(blob) = ink.post_dip_blob() {
        render_blob(canvas, points[0], blob, ink.ink_darkness(0.9));
    }
    
    let hairline_fx = ink.hairline_effects();
    let darkness = ink.ink_darkness(0.88);  // base darkness for iron gall ink
    let width_mod = ink.ink_width_modifier();
    
    let mut stroke_length = 0.0;
    let mut total_pressure = 0.0;
    let mut total_width = 0.0;
    
    for i in 0..points.len() - 1 {
        let dir = (points[i+1] - points[i]).angle();
        let pressure = pressures[i.min(pressures.len() - 1)];
        
        // Nib-angle width (TD-004)
        let base_width = nib_width(dir, nib, pressure);
        let modified_width = base_width * width_mod;
        
        // Is this a hairline stroke?
        let is_hairline = modified_width < nib.width_mm * 0.25;
        
        // Apply continuous hairline effects (all values are smooth curves, no thresholds)
        let (final_width, final_darkness) = if is_hairline {
            // Width reduction (continuous — even slightly reduced at high reservoir, 
            // significantly reduced at low)
            let reduced_width = modified_width * (1.0 - hairline_fx.width_reduction);
            
            // Gap check (probability increases smoothly as reservoir drops)
            if random() < hairline_fx.gap_probability {
                (0.0, 0.0)  // gap in the hairline
            } 
            // Raking check (probability increases smoothly, only significant at very low reservoir)
            else if random() < hairline_fx.raking_probability {
                render_raked_stroke(canvas, points[i], points[i+1], reduced_width, darkness * 0.7);
                continue;
            } else {
                (reduced_width, darkness)
            }
        } else {
            (modified_width, darkness)
        };
        
        if final_width > 0.0 {
            render_segment(canvas, points[i], points[i+1], final_width, final_darkness);
        }
        
        // Track for depletion calculation
        stroke_length += (points[i+1] - points[i]).length();
        total_pressure += pressure;
        total_width += final_width;
    }
    
    // Deplete ink for this stroke
    let avg_pressure = total_pressure / points.len().max(1) as f64;
    let avg_width = total_width / points.len().max(1) as f64;
    ink.deplete_for_stroke(stroke_length, avg_pressure, avg_width);
}
```

### Word-level dip check

```rust
fn render_word_with_ink(
    canvas: &mut Canvas,
    word_genome: &WordGenome,
    nib: &NibConfig,
    ink: &mut InkState,
    cursor: &mut Vec2,
) {
    for glyph in &word_genome.glyphs {
        for stroke in &glyph.segments {
            if stroke.contact {
                render_stroke_with_ink(canvas, &stroke.points, &stroke.pressures, nib, ink);
            }
        }
        // Advance cursor
        cursor.x += glyph.x_advance;
    }
    
    // At word boundary: check for dip
    let dip_event = ink.process_word_boundary();
    
    match dip_event {
        DipEvent::PreferredDip | DipEvent::ForcedDip => {
            // Log dip position for provenance / visualization
            log_dip(cursor, ink.total_dips, dip_event);
        },
        DipEvent::NoDip => {},
    }
}
```

---

## Part 4: Folio-Level Ink Behavior

### Dip cycle pattern across a page

For Brother Konrad writing on standard folios (28-32 lines, ~8-10 words per line):

```
Words per dip cycle:    35-45 (professional scribe, well-loaded quill)
Lines per dip cycle:    ~4-5 lines
Dips per folio:         6-8 times per page

Typical pattern:
  Line 1:  ████████████████████  (freshly dipped, dark)
  Line 2:  ███████████████████   (still good)
  Line 3:  ██████████████████    (slight lightening)
  Line 4:  █████████████████     (noticeably lighter toward end)
  Line 5:  ████████████████████  (dipped between lines 4 and 5, dark again)
  ...
```

### CLIO-7 per-folio ink state modifiers

Different folios may have different ink behavior:

```toml
[ink.folio_overrides]

# f07r: written across multiple sittings — ink density varies in ways
# consistent with the pen being set down and resumed several times
[ink.folio_overrides.f07r]
session_breaks = [8, 17, 25]    # line numbers where Konrad stopped and resumed
session_break_effect = "full_dip_plus_settling"
# After a session break, the ink has settled in the pot — first dip may be
# slightly different viscosity than mid-session dips
viscosity_shift_after_break = 0.05  # slightly thicker after settling

# f14r onward: compensating for physical difficulty
# May press harder (depleting faster) or write more slowly (depleting slower)
[ink.folio_overrides.f14r]
depletion_rate_modifier = 1.15   # presses harder, depletes 15% faster
dip_cycle_words = 30             # dips more frequently (shorter cycles)
```

---

## Part 5: Visualization and Diagnostics

### Ink state overlay

```bash
scribesim render f01r.json --show-ink-state -o debug/f01r_ink_overlay.png
```

Produces the rendered folio with a color-coded overlay:
- Green tint: reservoir > 0.7 (fresh)
- No tint: reservoir 0.3-0.7 (normal)
- Yellow tint: reservoir 0.15-0.3 (getting low)
- Red tint: reservoir < 0.15 (critical, about to dip)
- Blue dot: dip point

### Ink cycle graph

```bash
scribesim render f01r.json --ink-graph -o debug/f01r_ink_graph.png
```

Plots reservoir level vs. word position across the folio. Shows the sawtooth pattern: gradual depletion, sudden refill, gradual depletion, sudden refill. The graph should show 6-8 cycles for a typical folio.

### Darkness histogram comparison

```bash
scribesim compare-ink rendered_f01r.png --target cgm100_005r.jpg
```

Compares the ink darkness distribution of the rendered folio against the reference manuscript. If the cycles are calibrated correctly, the histogram shapes should be similar — both showing a bimodal or skewed distribution (dark post-dip strokes + light pre-dip strokes) rather than a narrow unimodal peak (which would indicate uniform ink, the current problem).

---

## Part 6: Parameters

```toml
[ink]
# Reservoir
capacity = { default = 1.0, range = [0.6, 1.5], unit = "ratio", 
  description = "How much ink the nib holds after dipping" }

# Depletion
base_depletion_rate = { default = 0.0008, range = [0.0003, 0.002], unit = "per_mm",
  description = "Ink consumed per mm of stroke at standard pressure/width" }
viscosity = { default = 1.0, range = [0.5, 1.5], unit = "ratio",
  description = "Ink thickness — affects depletion rate and lateral spread" }

# Dip behavior
dip_threshold = { default = 0.15, range = [0.08, 0.25], unit = "ratio",
  description = "Reservoir level that forces a dip" }
preferred_dip_threshold = { default = 0.22, range = [0.12, 0.35], unit = "ratio",
  description = "Reservoir level where scribe prefers to dip at next word boundary" }

# Post-dip effects
fresh_dip_darkness_boost = { default = 0.15, range = [0.05, 0.30], unit = "ratio",
  description = "How much darker the first strokes after dipping are" }
fresh_dip_width_boost = { default = 0.08, range = [0.0, 0.20], unit = "ratio",
  description = "How much wider strokes are right after dipping (ink spread)" }
dip_blob_probability = { default = 0.15, range = [0.0, 0.4], unit = "ratio",
  description = "Chance of a small ink blob at first contact after dip" }
dip_blob_max_radius_mm = { default = 0.5, range = [0.1, 1.0], unit = "mm",
  description = "Maximum radius of a dip blob" }

# Running-dry effects
dry_darkness_reduction = { default = 0.35, range = [0.15, 0.50], unit = "ratio",
  description = "How much lighter strokes get when nearly empty" }
dry_hairline_gap_probability = { default = 0.10, range = [0.0, 0.30], unit = "ratio",
  description = "Chance of gaps in hairline strokes when running dry" }
dry_raking_probability = { default = 0.05, range = [0.0, 0.20], unit = "ratio",
  description = "Chance of split-nib raking effect when very dry" }

# Iron gall ink color
ink_color_fresh = { default = [35, 22, 10], range = [[20,10,5], [55,35,20]], unit = "rgb",
  description = "Ink color when freshly applied (before aging — Weather handles oxidation)" }
```

**Total: 12 new parameters**, all with ranges suitable for the TD-003 optimizer.

These parameters are calibrated against the reference manuscript during the TD-009 selection process — the ink darkness distribution of the rendered output should match the reference.

---

## Part 7: What This Changes

### Before TD-010
Every stroke rendered at the same darkness. Every hairline at the same quality. Two instances of 'e' on the same page look identical in weight. The output reads as "printed."

### After TD-010
Visible ink cycles across the page — dark bands after dips, gradual lightening, then dark again. Hairlines near the end of a cycle are thinner and may break. The first word after a dip has slightly wider, darker strokes and maybe a tiny blob. Two instances of 'e' look different because one was written with a full nib and one with a depleting nib. The output reads as "written."

### Current renderer contract

In the current `evo` folio pipeline, the ink cycle is not just a tonal effect.
It is part of the operational renderer contract:

- reservoir depletion is applied continuously during stroke rendering
- render reports must declare the ink model mode and the active renderer path
- when `page_renderer = "evo"`, the pressure heatmap must come from the same
  evolved stroke sweep as the page image

This matters because Weather uses the pressure image as a stroke-energy proxy.
If the page and heatmap come from different renderers, ink-aware downstream
effects target the wrong letterforms.

### No changes needed to:
- The evolutionary algorithm (TD-007) — ink state is computed during rendering, not evolved
- The letterform extraction (TD-008) — extracted forms are ink-neutral
- The reference selection (TD-009) — but ink distribution becomes a new comparison metric

### Changes to:
- The Rust renderer (TD-007 Addendum) — gains InkState as a rendering parameter
- The nib physics (TD-004) — stroke width and darkness now modulated by ink state
- The metrics (TD-003) — add M_ink: ink darkness distribution comparison

---

## Implementation Priority

1. **InkState struct + depletion model** — implement the reservoir, depletion per stroke, and dip timing. Verify the sawtooth cycle produces 6-8 dips per folio.

2. **Darkness modulation** — apply ink_darkness() to the rendered stroke darkness. This alone will create visible ink cycles and is the highest-impact change.

3. **Width modulation** — apply ink_width_modifier() to stroke widths. Subtler than darkness but adds realism.

4. **Hairline quality** — implement the thinning/breaking/raking effects for low-reservoir hairlines. This is where the detail-level authenticity comes in.

5. **Post-dip blob** — small detail but very characteristic of real manuscripts. Implement after the core cycle is working.

6. **Diagnostics** — ink state overlay, cycle graph, darkness histogram comparison.

7. **Parameter calibration** — use the reference manuscript from TD-009 to calibrate depletion rate and dip frequency.

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-03-21 | Initial draft — ink cycle simulation | shawn + claude |
| 2026-03-23 | Added current renderer contract for evo page/heatmap coherence | shawn + codex |
