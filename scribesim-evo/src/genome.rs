//! Genome data structures mirroring the Python WordGenome/GlyphGenome/BezierSegment.

use pyo3::prelude::*;

/// A cubic Bézier segment with rendering metadata.
#[derive(Clone, Debug)]
pub struct BezierSeg {
    pub p0: (f64, f64),
    pub p1: (f64, f64),
    pub p2: (f64, f64),
    pub p3: (f64, f64),
    pub contact: bool,
    pub pressure: Vec<f64>,
    pub speed: Vec<f64>,
    pub nib_drift: f64,
}

impl BezierSeg {
    pub fn evaluate(&self, t: f64) -> (f64, f64) {
        let u = 1.0 - t;
        let x = u*u*u * self.p0.0 + 3.0*u*u*t * self.p1.0
              + 3.0*u*t*t * self.p2.0 + t*t*t * self.p3.0;
        let y = u*u*u * self.p0.1 + 3.0*u*u*t * self.p1.1
              + 3.0*u*t*t * self.p2.1 + t*t*t * self.p3.1;
        (x, y)
    }

    pub fn tangent(&self, t: f64) -> (f64, f64) {
        let u = 1.0 - t;
        let dx = 3.0*u*u * (self.p1.0 - self.p0.0)
               + 6.0*u*t * (self.p2.0 - self.p1.0)
               + 3.0*t*t * (self.p3.0 - self.p2.0);
        let dy = 3.0*u*u * (self.p1.1 - self.p0.1)
               + 6.0*u*t * (self.p2.1 - self.p1.1)
               + 3.0*t*t * (self.p3.1 - self.p2.1);
        (dx, dy)
    }

    pub fn direction_rad(&self, t: f64) -> f64 {
        let (dx, dy) = self.tangent(t);
        dy.atan2(dx)
    }

    pub fn pressure_at(&self, t: f64) -> f64 {
        interp(&self.pressure, t)
    }
}

fn interp(curve: &[f64], t: f64) -> f64 {
    let n = curve.len();
    if n == 0 { return 0.5; }
    if n == 1 { return curve[0]; }
    let idx_f = t * (n as f64 - 1.0);
    let idx_lo = (idx_f as usize).min(n - 2);
    let frac = idx_f - idx_lo as f64;
    curve[idx_lo] * (1.0 - frac) + curve[idx_lo + 1] * frac
}

/// Glyph genome — one letter's shape.
#[derive(Clone, Debug)]
pub struct GlyphData {
    pub letter: char,
    pub segments: Vec<BezierSeg>,
    pub x_offset: f64,
    pub x_advance: f64,
}

/// Word genome — the complete evolved representation.
#[derive(Clone, Debug)]
pub struct WordData {
    pub glyphs: Vec<GlyphData>,
    pub baseline_y: f64,
    pub baseline_drift: Vec<f64>,
    pub global_slant_deg: f64,
    pub slant_drift: Vec<f64>,
    pub ink_start: f64,
    pub word_width: f64,
}

/// Python-facing genome wrapper.
#[pyclass]
#[derive(Clone)]
pub struct PyGenome {
    pub data: WordData,
}

#[pymethods]
impl PyGenome {
    #[new]
    fn new(
        glyphs_json: String,
        baseline_y: f64,
        global_slant_deg: f64,
        ink_start: f64,
        word_width: f64,
    ) -> Self {
        // Parse glyphs from JSON (simplified for initial implementation)
        // In production, use a more efficient serialization format
        let data = WordData {
            glyphs: Vec::new(), // populated via from_python_genome
            baseline_y,
            baseline_drift: Vec::new(),
            global_slant_deg,
            slant_drift: Vec::new(),
            ink_start,
            word_width,
        };
        PyGenome { data }
    }

    /// Create from a Python WordGenome object (extracts all fields).
    #[staticmethod]
    fn from_python(obj: &Bound<'_, PyAny>) -> PyResult<Self> {
        let baseline_y: f64 = obj.getattr("baseline_y")?.extract()?;
        let global_slant_deg: f64 = obj.getattr("global_slant_deg")?.extract()?;
        let ink_start: f64 = obj.getattr("ink_state_start")?.extract()?;
        let word_width: f64 = obj.getattr("word_width_mm")?.extract()?;

        let baseline_drift: Vec<f64> = obj.getattr("baseline_drift")?.extract()?;
        let slant_drift: Vec<f64> = obj.getattr("slant_drift")?.extract()?;

        let py_glyphs: Vec<Bound<'_, PyAny>> = obj.getattr("glyphs")?.extract()?;
        let mut glyphs = Vec::new();

        for pg in &py_glyphs {
            let letter: String = pg.getattr("letter")?.extract()?;
            let x_offset: f64 = pg.getattr("x_offset")?.extract()?;
            let x_advance: f64 = pg.getattr("x_advance")?.extract()?;

            let py_segs: Vec<Bound<'_, PyAny>> = pg.getattr("segments")?.extract()?;
            let mut segments = Vec::new();

            for ps in &py_segs {
                let p0: (f64, f64) = ps.getattr("p0")?.extract()?;
                let p1: (f64, f64) = ps.getattr("p1")?.extract()?;
                let p2: (f64, f64) = ps.getattr("p2")?.extract()?;
                let p3: (f64, f64) = ps.getattr("p3")?.extract()?;
                let contact: bool = ps.getattr("contact")?.extract()?;
                let pressure: Vec<f64> = ps.getattr("pressure_curve")?.extract()?;
                let speed: Vec<f64> = ps.getattr("speed_curve")?.extract()?;
                let nib_drift: f64 = ps.getattr("nib_angle_drift")?.extract()?;

                segments.push(BezierSeg {
                    p0, p1, p2, p3, contact, pressure, speed, nib_drift,
                });
            }

            glyphs.push(GlyphData {
                letter: letter.chars().next().unwrap_or('?'),
                segments,
                x_offset,
                x_advance,
            });
        }

        Ok(PyGenome {
            data: WordData {
                glyphs,
                baseline_y,
                baseline_drift,
                global_slant_deg,
                slant_drift,
                ink_start,
                word_width,
            },
        })
    }
}
