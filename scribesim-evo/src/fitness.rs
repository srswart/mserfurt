//! Full fitness evaluation functions (F1-F7) in Rust.

use crate::genome::PyGenome;

/// Evaluate fitness, returning [f1, f2, f3, f4, f5, f6, f7].
pub fn evaluate_fitness(canvas: &[u8], w: usize, h: usize, genome: &PyGenome) -> [f64; 7] {
    let f1 = letter_recognition(canvas, w, h, genome);
    let f2 = thick_thin_contrast(canvas, w, h);
    let f3 = connection_flow(canvas, w, h, genome);
    let f4 = style_consistency(canvas, w, h, genome);
    let f5 = 0.5; // target similarity — requires exemplar images
    let f6 = smoothness(genome);
    let f7 = continuity(genome);

    [f1, f2, f3, f4, f5, f6, f7]
}

/// F1: Letter recognition — ink presence and distribution per glyph region.
fn letter_recognition(canvas: &[u8], w: usize, h: usize, genome: &PyGenome) -> f64 {
    if genome.data.glyphs.is_empty() { return 0.0; }

    let px_per_mm = w as f64 / (genome.data.word_width + 4.0).max(1.0);
    let mut scores = Vec::new();

    for glyph in &genome.data.glyphs {
        let x0 = (glyph.x_offset * px_per_mm) as usize;
        let x1 = ((glyph.x_offset + glyph.x_advance) * px_per_mm) as usize;
        let x0 = x0.min(w);
        let x1 = x1.min(w).max(x0 + 1);

        // Count ink pixels in glyph region
        let mut ink_count = 0;
        let total = (x1 - x0) * h;
        for y in 0..h {
            for x in x0..x1 {
                if canvas[y * w + x] < 200 {
                    ink_count += 1;
                }
            }
        }

        let ink_ratio = ink_count as f64 / total.max(1) as f64;

        // Good: 5-40% ink in glyph region (letter has substance but isn't a blob)
        let score = if ink_ratio >= 0.05 && ink_ratio <= 0.40 {
            1.0
        } else if ink_ratio < 0.02 {
            0.0 // too little ink — letter barely visible
        } else if ink_ratio > 0.60 {
            0.2 // too much ink — blob
        } else {
            0.5
        };

        // Check vertical distribution: ink should span most of x-height zone
        let mut min_ink_row = h;
        let mut max_ink_row = 0;
        for y in 0..h {
            for x in x0..x1 {
                if canvas[y * w + x] < 200 {
                    min_ink_row = min_ink_row.min(y);
                    max_ink_row = max_ink_row.max(y);
                }
            }
        }
        let height_coverage = if max_ink_row > min_ink_row {
            (max_ink_row - min_ink_row) as f64 / h as f64
        } else { 0.0 };

        // Good: spans at least 30% of canvas height
        let height_score = if height_coverage > 0.3 { 1.0 } else { height_coverage / 0.3 };

        scores.push(score * 0.6 + height_score * 0.4);
    }

    scores.iter().sum::<f64>() / scores.len().max(1) as f64
}

/// F2: Thick/thin contrast — stroke width ratio from distance transform approximation.
fn thick_thin_contrast(canvas: &[u8], w: usize, h: usize) -> f64 {
    if w == 0 || h == 0 { return 0.0; }

    // Approximate stroke widths via row-wise run lengths
    let mut min_run = w;
    let mut max_run = 0;
    let mut any_ink = false;

    for y in 0..h {
        let mut run = 0;
        for x in 0..w {
            if canvas[y * w + x] < 200 {
                run += 1;
                any_ink = true;
            } else {
                if run > 0 {
                    min_run = min_run.min(run);
                    max_run = max_run.max(run);
                }
                run = 0;
            }
        }
        if run > 0 {
            min_run = min_run.min(run);
            max_run = max_run.max(run);
        }
    }

    if !any_ink || min_run == 0 { return 0.0; }

    let ratio = max_run as f64 / min_run.max(1) as f64;
    let target = 4.0;
    (1.0 - ((ratio - target).abs() / target)).max(0.0)
}

/// F3: Connection flow — ink presence between adjacent glyphs.
fn connection_flow(canvas: &[u8], w: usize, h: usize, genome: &PyGenome) -> f64 {
    if genome.data.glyphs.len() < 2 { return 1.0; }

    let px_per_mm = w as f64 / (genome.data.word_width + 4.0).max(1.0);
    let mut good = 0;
    let n = genome.data.glyphs.len() - 1;

    for i in 0..n {
        let g1 = &genome.data.glyphs[i];
        let g2 = &genome.data.glyphs[i + 1];
        let x0 = ((g1.x_offset + g1.x_advance) * px_per_mm) as usize;
        let x1 = (g2.x_offset * px_per_mm) as usize;
        let x0 = x0.min(w);
        let x1 = x1.min(w).max(x0);

        let has_ink = (0..h).any(|y| {
            (x0..x1).any(|x| x < w && canvas[y * w + x] < 200)
        });
        if has_ink { good += 1; }
    }

    good as f64 / n.max(1) as f64
}

/// F4: Style consistency — slant, ink density, proportion checks.
fn style_consistency(canvas: &[u8], w: usize, h: usize, genome: &PyGenome) -> f64 {
    let mut scores = Vec::new();

    // Slant check (3-5° is ideal for Bastarda)
    let slant = genome.data.global_slant_deg;
    scores.push((1.0 - ((slant - 4.0).abs() / 10.0)).max(0.0));

    // Overall ink density check
    let dark = canvas.iter().filter(|&&v| v < 200).count();
    let ratio = dark as f64 / canvas.len().max(1) as f64;
    if ratio >= 0.05 && ratio <= 0.30 {
        scores.push(1.0);
    } else if ratio < 0.01 || ratio > 0.50 {
        scores.push(0.0);
    } else {
        scores.push(0.5);
    }

    // Glyph advance regularity
    if genome.data.glyphs.len() >= 2 {
        let advances: Vec<f64> = genome.data.glyphs.iter().map(|g| g.x_advance).collect();
        let mean = advances.iter().sum::<f64>() / advances.len() as f64;
        let variance = advances.iter().map(|a| (a - mean).powi(2)).sum::<f64>() / advances.len() as f64;
        let cv = variance.sqrt() / mean.max(0.01);
        scores.push((1.0 - cv).max(0.0));
    }

    scores.iter().sum::<f64>() / scores.len().max(1) as f64
}

/// F6: Smoothness — curvature regularity of Bézier segments.
fn smoothness(genome: &PyGenome) -> f64 {
    let mut penalty = 0.0;
    for glyph in &genome.data.glyphs {
        for seg in &glyph.segments {
            let mut prev_angle = seg.direction_rad(0.0);
            for i in 1..20 {
                let t = i as f64 / 19.0;
                let angle = seg.direction_rad(t);
                let mut change = (angle - prev_angle).abs();
                if change > std::f64::consts::PI {
                    change = 2.0 * std::f64::consts::PI - change;
                }
                if change > 0.5 { penalty += change - 0.5; }
                prev_angle = angle;
            }
        }
    }
    1.0 / (1.0 + penalty)
}

/// F7: Continuity at glyph boundaries.
fn continuity(genome: &PyGenome) -> f64 {
    if genome.data.glyphs.len() < 2 { return 1.0; }
    let mut penalty = 0.0;

    for i in 0..genome.data.glyphs.len() - 1 {
        let g1 = &genome.data.glyphs[i];
        let g2 = &genome.data.glyphs[i + 1];

        if let (Some(s1), Some(s2)) = (g1.segments.last(), g2.segments.first()) {
            let exit = s1.p3;
            let entry = s2.p0;
            let gap = ((exit.0 - entry.0).powi(2) + (exit.1 - entry.1).powi(2)).sqrt();
            penalty += gap;

            // Direction gap
            let exit_t = s1.tangent(1.0);
            let entry_t = s2.tangent(0.0);
            let exit_a = exit_t.1.atan2(exit_t.0);
            let entry_a = entry_t.1.atan2(entry_t.0);
            let mut angle_gap = (exit_a - entry_a).abs();
            if angle_gap > std::f64::consts::PI {
                angle_gap = 2.0 * std::f64::consts::PI - angle_gap;
            }
            penalty += angle_gap * 0.3;
        }
    }

    1.0 / (1.0 + penalty)
}
