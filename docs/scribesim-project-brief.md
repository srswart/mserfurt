# ScribeSim ("scribesim") — Project Brief

## Purpose
Build **ScribeSim**: a scribal hand simulation engine that takes the per-folio German/Latin corpus from XL and generates realistic cursive manuscript text images with embedded pressure hints, laid out to approximate how Brother Konrad — a professional scribe in 1457 Erfurt — would have arranged these pages. ScribeSim is the second stage of the XL → ScribeSim → Weather pipeline for producing the physical manuscript of *MS Erfurt Aug. 12°47*.

**Phase 1 outcome:** a CLI tool named `scribesim` that consumes XL's folio JSON, renders cursive text onto folio-sized canvases using a parameterized scribal hand model, and produces page images with two layout modes — orderly (regularized) and historical (matching the hand variations described in CLIO-7's apparatus, including pressure changes, multi-sitting ink variation, and the shift to a smaller hand on folio 7v).

## Why this exists
Brother Konrad is a professional scribe — the manuscript itself makes this central to its meaning. He has spent thirty years forming letters. He knows when his hand thickens on a downstroke because his attention deepened. He knows the "slight thickening of a stroke when my attention deepened, the places where I slowed because the meaning arrived in my hands before it arrived in my mind." The CLIO-7 apparatus further describes specific hand variations across the manuscript: increased lateral pressure on downstrokes when Konrad is agitated (folio 6r), variable ink density consistent with multiple sittings (folio 7r), a shift to a smaller more economical hand (folio 7v lower half), and slower wider-spaced letterforms compensating for physical difficulty (folio 14r onward).

ScribeSim must model all of this. A fifteenth-century Erfurt scriptorium hand — *Bastarda* or *Cursiva* — with the specific emotional and physical variations that CLIO-7 describes. The result must be:
- visually plausible as a professional fifteenth-century German hand
- structurally responsive to CLIO-7's per-folio hand notes (pressure, speed, spacing, ink density)
- annotated with ground-truth data (glyph bounding boxes, baselines, pressure maps) for HTR model training in eScriptorium/Kraken

## Phase 1 scope (MVP)
### Input
- XL folio JSON (per-folio records with German/Latin text, register tags, line structure, damage annotations, hand notes)
- Scribal hand parameter file (stroke width, slant, spacing, pressure curves — the "base hand")
- Per-folio hand overrides (derived from XL's `hand_notes` field — increased pressure, wider spacing, etc.)
- Layout template: ruling pattern, margins, text block dimensions

### CLI deliverable
A `scribesim` executable (Python with Rust acceleration for stroke rendering) with:
- `scribesim render <folio_json> -o <output.png>` — render a single folio
- `scribesim render-batch <input_dir> -o <output_dir>` — render all folios
- `scribesim render <folio_json> --layout orderly -o <o>` — regularized layout
- `scribesim render <folio_json> --layout expressive -o <o>` — hand varies per CLIO-7 apparatus
- `scribesim hand --show <hand_params.toml>` — preview scribal hand specimen sheet
- `scribesim groundtruth <output_dir>` — export glyph-level ground truth as PAGE XML
- `scribesim --version`, `scribesim --help`

### Rendering scope
**Required**
- Stroke-based glyph rendering: each letter drawn as Bézier strokes with variable width (pressure simulation)
- Pressure model: stroke width varies along path; the base profile shifts per folio based on XL's hand notes
- Ink model: darkness varies with simulated ink flow; multi-sitting folios (7r) show ink density shifts at sitting boundaries
- Script support:
  - **Frühneuhochdeutsch Bastarda:** Konrad's primary hand. Full lowercase Latin alphabet with German-specific forms (long ſ, ß-ligature or sz, umlauted vowels via superscript e)
  - **Ecclesiastical Latin passages:** same hand but with Latin conventions (no umlaut forms, different abbreviation marks)
  - **Middle High German quotations** (Eckhart): distinguished only by orthographic conventions, same hand
- Per-folio hand variation from CLIO-7 apparatus:
  - **f06r:** increased lateral pressure on downstrokes (agitation/fatigue)
  - **f07r:** variable ink density, pen set down and resumed multiple times within the folio
  - **f07v lower half:** shift to smaller, more economical hand — Konrad's "working register"
  - **f14r onward:** slower, wider spacing, compensating for physical difficulty (failing eyes)
- Two layout modes:
  - **Orderly:** uniform line spacing, consistent margins, Konrad at his professional best
  - **Expressive:** hand variations per CLIO-7 notes applied; the manuscript as it "actually" was
- Lacuna handling: where XL marks lacunae, ScribeSim renders partial text trailing off or leaves blank space, depending on lacuna type (damage vs. missing folio)

**Scribal hand parameters (TOML) — Brother Konrad's hand**
- `pen_angle`: 40° (standard Bastarda nib angle)
- `pen_width_range`: variable per folio, base [0.8, 2.0]
- `slant`: 5° rightward (moderate for Bastarda)
- `letter_spacing`: tight for Konrad's normal hand, wider for f14r onward
- `pressure_curve`: deeper attack on downstrokes, lighter upstrokes
- `ink_flow`: consistent within a sitting, with visible shift at sitting boundaries (f07r)
- `fatigue_model`: enabled for f14r onward (wider spacing, slight tremor)

**Output**
- PNG image per folio (300 DPI, ~3000×4000px for standard folios, smaller for f14r onward per CLIO-7)
- Sidecar PAGE XML with glyph-level ground truth (bounding polygons, baselines, Unicode text)
- Pressure heatmap per folio (grayscale, pixel intensity = pen pressure)

### Integration with eScriptorium
- Output images importable as document pages in a seventeen-page eScriptorium document
- PAGE XML importable as segmentation + transcription ground truth
- Pressure heatmaps available for downstream analysis
- Kraken baseline segmentation model should achieve reasonable line detection without fine-tuning

### Developer experience (Phase 1)
- Deterministic rendering for same input + parameters + seed
- Hand parameter preview mode
- Diagnostic mode: visible baselines, glyph boxes, pressure overlay
- Per-folio hand override preview: see the effect of CLIO-7 hand notes before full render

## Non-goals (Phase 1)
- Color rendering, rubrication, or illumination (Konrad's manuscript is plain — he explicitly describes it as private, uncommissioned)
- Illustration rendering (there are no illustrations in MS Erfurt Aug. 12°47)
- Multiple scribal hands (only Konrad writes in this manuscript)
- Vellum texture or weathering (Weather's domain)
- The ✦ ✦ ✦ section dividers as decorative elements (render as simple pen-drawn symbols)
- Interactive hand-tuning UI

## Design principles (project constraints)
- **Konrad's hand is the hand:** this is not a generic Bastarda — it is one specific scribe's hand, with the variations CLIO-7 describes. The hand parameters encode a character, not a typeface.
- **Stroke-first rendering:** every visible mark is a Bézier stroke with pressure metadata. This is essential for the pressure heatmaps that Weather will later use for ink degradation targeting.
- **CLIO-7 fidelity:** if CLIO-7 says the hand shows increased lateral pressure on f06r, ScribeSim must produce strokes that exhibit increased lateral pressure on f06r.
- **Ground truth as primary output:** the PAGE XML is co-generated with the image and guaranteed pixel-accurate.
- **Deterministic output:** same input + parameters + seed = identical image.

## ARRIVE governance plan
We run ScribeSim development with outcome-first discipline:
- work as a sequence of small, reviewable Advances
- keep changes within the reviewability budget
- follow **Tidy First → Test First → Implement** as default execution order

### ScribeSim system + components (initial)
System: `scribesim`

Components (all **incubating** initially):
- `cli` — command-line driver, argument parsing
- `hand` — scribal hand model (base parameters + per-folio CLIO-7 overrides)
- `glyphs` — glyph decomposition: German Bastarda letterforms, Latin forms, MHG forms, abbreviation marks, the ✦ divider
- `layout` — page layout engine (ruling, margins, text block, line breaking)
- `render` — Bézier stroke rasterization, pressure-to-width mapping, ink flow with sitting boundaries
- `groundtruth` — PAGE XML generation, glyph bounding polygon extraction
- `tests` — golden image tests, ground truth validation, hand variation tests
- `docs` — hand parameter guide, CLIO-7 hand-note mapping, eScriptorium import guide

## Phase plan
### Phase 1 — "Konrad's hand on the page"
Deliver the minimal end-to-end pipeline:
1. Parse XL folio JSON with register tags and hand notes
2. Load base hand parameters and compute per-folio overrides from CLIO-7 notes
3. Decompose German/Latin text into glyph stroke sequences
4. Lay out glyphs on ruled pages (orderly mode)
5. Render strokes with pressure-variable width and ink flow
6. Implement expressive mode with per-folio hand variation
7. Export page images + PAGE XML ground truth + pressure heatmaps
8. Provide golden tests for representative folios (clean, agitated, multi-sitting, failing-eyes)

### Phase 2 (preview)
- Abbreviation rendering (scribal abbreviation marks, Tironian et, nasal bars — requires XL Phase 2 abbreviation compression)
- Sitting-boundary visualization in diagnostic mode
- Kraken model training loop: generate synthetic pages → train HTR → evaluate

### Phase 3 (preview)
- Aging hand model: simulate how Konrad's hand changed over the months of writing
- Export as IIIF-compatible image sequence

## Definition of Done (Phase 1)
- `scribesim render examples/f07r.json -o f07r.png` produces a visually plausible manuscript page with multi-sitting ink variation
- `scribesim render examples/f14r.json --layout expressive -o f14r.png` produces a page with wider spacing and slight tremor consistent with CLIO-7's description
- `scribesim groundtruth out/` produces PAGE XML that imports into eScriptorium with correct line segmentation
- Pressure heatmaps show visible variation matching CLIO-7 hand notes (heavier pressure on f06r downstrokes, etc.)
- Automated tests cover: stroke generation, layout constraints, ground truth accuracy (IoU ≥ 0.95), hand variation application, deterministic output
- Repo includes Brother Konrad hand parameter documentation and CLIO-7 hand-note mapping reference

## Key risks + mitigations
- **Stroke rendering performance:** Bézier rasterization at 300 DPI is expensive; implement core renderer in Rust.
- **Glyph decomposition for German Bastarda:** includes forms not in standard Latin (ß, umlauted vowels via superscript e, specific long-s conventions). Start with core set (~90 glyphs), expand.
- **Per-folio hand variation believability:** the difference between "wider spacing" and "obviously wrong" is subtle. Calibrate against photographs of real fifteenth-century manuscripts with known hand variation.
- **Perceptual test brittleness:** supplement perceptual hash golden tests with structural ground truth tests.

## Success metrics (Phase 1)
- Can render all seventeen folios in ≤ 10 minutes on commodity hardware
- PAGE XML achieves ≥ 0.95 IoU for glyph bounding boxes
- Kraken default segmentation model achieves ≥ 90% line detection on ScribeSim output
- The hand variation between f01r (clean, professional) and f14r (compensating, wider) is visually distinguishable
- At least one reader familiar with medieval manuscripts finds the output "plausible as a fifteenth-century hand" at casual inspection
