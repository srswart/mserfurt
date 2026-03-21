//! Render a word genome to a grayscale canvas using nib physics.

use crate::genome::PyGenome;

const N_SAMPLES: usize = 30;

/// Render a word genome to a flat grayscale buffer (0=white, 255=black).
pub fn render_word(
    genome: &PyGenome,
    nib_width: f64,
    nib_angle_rad: f64,
    canvas_w: u32,
    canvas_h: u32,
    dpi: f64,
) -> Vec<u8> {
    let px_per_mm = dpi / 25.4;
    let w = canvas_w as usize;
    let h = canvas_h as usize;
    let mut canvas = vec![255u8; w * h]; // white background

    let data = &genome.data;
    let mut ink = data.ink_start;

    for (gi, glyph) in data.glyphs.iter().enumerate() {
        let slant_rad = {
            let s = data.global_slant_deg
                + data.slant_drift.get(gi).copied().unwrap_or(0.0);
            s.to_radians()
        };
        let baseline_offset = data.baseline_drift.get(gi).copied().unwrap_or(0.0);

        for seg in &glyph.segments {
            if !seg.contact { continue; }

            for si in 0..=N_SAMPLES {
                let t = si as f64 / N_SAMPLES as f64;

                let (mut x_mm, mut y_mm) = seg.evaluate(t);
                y_mm += baseline_offset;

                // Apply slant
                let y_from_base = y_mm - data.baseline_y;
                x_mm += y_from_base * slant_rad.tan();

                // Nib-angle width
                let direction = seg.direction_rad(t);
                let sin_comp = (direction - nib_angle_rad).sin().abs();
                let pressure = seg.pressure_at(t);
                let pressure_mod = 0.8 + 0.4 * pressure;
                let min_hairline = nib_width * 0.08;
                let mark_w = (nib_width * sin_comp * pressure_mod).max(min_hairline);

                // Stroke foot effect (last 15%)
                let foot_mult = if t > 0.85 {
                    let ft = (t - 0.85) / 0.15;
                    1.0 + 0.2 * (ft * std::f64::consts::PI).sin()
                } else { 1.0 };

                let width = mark_w * foot_mult;
                let darkness = (pressure * 0.9 * ink * foot_mult).min(1.0);

                if darkness < 0.05 { continue; }

                // Rasterize
                let x_px = (x_mm * px_per_mm) as i32;
                let y_px = (y_mm * px_per_mm) as i32;
                let r = ((width * 0.5 * px_per_mm * 0.4).max(0.3)) as i32;

                let val = (255.0 * (1.0 - darkness)) as u8;

                for dy in -r..=r {
                    for dx in -r..=r {
                        if dx*dx + dy*dy > r*r { continue; }
                        let px = (x_px + dx) as usize;
                        let py = (y_px + dy) as usize;
                        if px < w && py < h {
                            let idx = py * w + px;
                            canvas[idx] = canvas[idx].min(val); // darker wins
                        }
                    }
                }
            }

            // Deplete ink
            ink = (ink - 0.002).max(0.0);
        }
    }

    canvas
}
