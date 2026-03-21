//! scribesim-evo — Rust acceleration for the evolutionary scribe (TD-007).
//!
//! Provides batch genome rendering and fitness evaluation via PyO3.
//! The Python evolutionary logic (selection, crossover, mutation) stays in Python.
//! Only the inner loop (render + evaluate) is in Rust for speed.

use pyo3::prelude::*;

mod genome;
mod render;
mod fitness;

use genome::PyGenome;
use render::render_word;
use fitness::evaluate_fitness;

/// A single fitness evaluation result.
#[pyclass]
#[derive(Clone)]
struct FitnessResult {
    #[pyo3(get)]
    total: f64,
    #[pyo3(get)]
    f1: f64,
    #[pyo3(get)]
    f2: f64,
    #[pyo3(get)]
    f3: f64,
    #[pyo3(get)]
    f4: f64,
    #[pyo3(get)]
    f5: f64,
    #[pyo3(get)]
    f6: f64,
    #[pyo3(get)]
    f7: f64,
}

/// Batch evaluator — evaluates an entire generation in one Python→Rust call.
#[pyclass]
struct BatchEvaluator {
    nib_width: f64,
    nib_angle_rad: f64,
    canvas_width: u32,
    canvas_height: u32,
    dpi: f64,
    fitness_weights: [f64; 7],
}

#[pymethods]
impl BatchEvaluator {
    #[new]
    fn new(
        nib_width: f64,
        nib_angle_deg: f64,
        canvas_width: u32,
        canvas_height: u32,
        dpi: f64,
    ) -> Self {
        BatchEvaluator {
            nib_width,
            nib_angle_rad: nib_angle_deg.to_radians(),
            canvas_width,
            canvas_height,
            dpi,
            fitness_weights: [0.30, 0.10, 0.15, 0.15, 0.10, 0.10, 0.10],
        }
    }

    /// Evaluate a batch of genomes in parallel using rayon.
    fn evaluate_batch(&self, genomes: Vec<PyGenome>) -> Vec<FitnessResult> {
        use rayon::prelude::*;

        genomes.par_iter()
            .map(|g| {
                let canvas = render_word(
                    g, self.nib_width, self.nib_angle_rad,
                    self.canvas_width, self.canvas_height, self.dpi,
                );
                let scores = evaluate_fitness(&canvas, self.canvas_width as usize, self.canvas_height as usize, g);
                let w = &self.fitness_weights;
                let total = w[0]*scores[0] + w[1]*scores[1] + w[2]*scores[2]
                          + w[3]*scores[3] + w[4]*scores[4] + w[5]*scores[5]
                          + w[6]*scores[6];
                FitnessResult {
                    total, f1: scores[0], f2: scores[1], f3: scores[2],
                    f4: scores[3], f5: scores[4], f6: scores[5], f7: scores[6],
                }
            })
            .collect()
    }

    /// Render a single genome and return as a flat grayscale array.
    fn render_single(&self, genome: PyGenome) -> Vec<u8> {
        let canvas = render_word(
            &genome, self.nib_width, self.nib_angle_rad,
            self.canvas_width, self.canvas_height, self.dpi,
        );
        canvas
    }
}

/// Python module definition.
#[pymodule]
fn scribesim_evo(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<BatchEvaluator>()?;
    m.add_class::<FitnessResult>()?;
    m.add_class::<PyGenome>()?;
    Ok(())
}
