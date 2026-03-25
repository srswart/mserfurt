# MS Erfurt Aug. 12°47 — Manuscript Simulation Pipeline

A three-phase pipeline for producing a simulated physical manuscript: Brother Konrad's 1457 scribal confession (*MS Erfurt Aug. 12°47*), authored in Frühneuhochdeutsch, rendered in Bastarda script, and aged 500 years through a hybrid AI and programmatic weathering system.

## Pipeline overview

```
XL (author)  →  ScribeSim (render)  →  Weather (age)
```

**XL — Authoring and folio structuring.**
Manuscript text is written in Late Middle High German (Thuringian dialect, 1457) and structured as per-folio JSON files. Each line carries register annotation (`de` / `mixed`), a CLIO-7 confidence score, and optional damage metadata. The manuscript now follows a smaller private-manuscript format: standard calfskin folios (f01–f13) are 185×250mm with a 130×180mm text block and a comfortable 22-24 lines/page; smaller irregular folios begin at f14 and target 16-18 lines/page. XL may extend the folio sequence beyond `f17` when the text volume requires it.

**ScribeSim — Scribal hand rendering.**
Each folio JSON is rendered to a 300 DPI PNG using the ScribeSim Bastarda engine. Line spacing, nib width (0.5mm), and x-height (3.0mm) are calibrated to the page layout. Recto pages place the gutter on the left; verso on the right. Output images are clean — no aging applied at this stage.

**Weather — 500-year manuscript aging.**
The weathering system applies aging in gathering order (epicenter f04r first, then outward by leaf distance) so that each folio's AI generation is informed by already-weathered neighbours. The process has three sub-steps:

1. **Codex map** — a physical damage model computed from first principles: water propagation decaying from the epicenter by leaf distance (severity = 0.4^distance), edge darkening by gathering position, deterministic foxing clusters with recto/verso mirroring, and vellum stock per leaf.
2. **Pre-degradation** — CLIO-7 word-level damage annotations applied programmatically in pixel space before any AI involvement, ensuring scholarly specifications are honoured exactly.
3. **AI compositing** — a blank parchment canvas is sent to `gpt-image-1` with a prompt describing the physical aging specific to that folio. The returned aged background is darken-blended with the pre-degraded text render (letterforms are never touched by the AI). A final programmatic pass shifts ink from black toward warm reddish-brown (iron gall oxidation) and fades ink in water damage zones proportionally.

---

## Setup

### Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- OpenAI API key with access to `gpt-image-1`

### Install

```bash
git clone <repo>
cd 041-mserfurt
uv sync
```

Or with pip:

```bash
pip install -e .
```

### API keys

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
```

The weathering pipeline reads this automatically via `python-dotenv`. You can also export it directly:

```bash
export OPENAI_API_KEY=sk-...
```

---

## Running the pipeline

### 1. Author the folios (XL)

Folio JSON files live in `output-live/`. The manuscript begins at `f01r` and may extend beyond `f17v` depending on the current layout density. To inspect or edit a folio:

```
output-live/
├── f01r.json   # standard-stock opening folio
├── f01v.json
├── ...
├── f13v.json   # last standard-stock folio
├── f14r.json   # irregular vellum begins
├── ...
└── fNNv.json   # extent depends on the current line budgets
```

Each file follows this schema:

```json
{
  "id": "f01r",
  "recto_verso": "recto",
  "gathering_position": 1,
  "vellum_stock": "standard",
  "lines": [
    {
      "number": 1,
      "text": "Hie hebt sich an, das ein schreiber nit mag laßen zu",
      "register": "de",
      "annotations": [{"type": "confidence", "detail": {"score": 0.97}}]
    }
  ]
}
```

### 2. Render all folios (ScribeSim)

```bash
uv run python scripts/render_all.py
```

Renders all folio pages present in `output-live/` to `render-output/`. Already-rendered pages can be skipped:

```bash
uv run python scripts/render_all.py --skip-existing
```

To re-render specific folios only:

```bash
uv run python scripts/render_all.py f04r f04v
```

Output: `render-output/f01r.png` … `render-output/fNNv.png`

Standard pages are 2185×2952px (185×250mm at 300dpi); irregular pages are 1830×2503px (155×212mm).

### 3. Generate the codex weathering map

```bash
uv run weather weather-map \
  --gathering-size 17 \
  --output weather/codex_map.json
```

Prints the full damage table (water severity, corner damage, foxing count, vellum stock) for the current folio sequence.

### 4. Weather the full manuscript

```bash
source .env && export OPENAI_API_KEY

uv run weather weather-codex \
  --clean-dir render-output \
  --map weather/codex_map.json \
  --folio-json-dir output-live \
  --output-dir weather-output \
  --model gpt-image-1
```

Processes all folios in gathering order (f04r first). Already-completed folios are skipped automatically (provenance JSON present). Expect the runtime to scale with the current manuscript length.

Output per folio in `weather-output/`:
- `{fid}_weathered.png` — final aged image
- `{fid}_provenance.json` — prompt, spec, seed, model, coherence references, timestamp
- `{fid}_prompt.txt` — full weathering prompt (for reference)

### 5. Weather a single folio

Useful for iteration and prompt tuning:

```bash
uv run weather weather-folio \
  --folio f04r \
  --clean render-output/f04r.png \
  --map weather/codex_map.json \
  --folio-json output-live/f04r.json \
  --output-dir weather-output
```

Add `--dry-run` to skip the API call and inspect the generated prompt without spending tokens.

---

## Repository structure

```
041-mserfurt/
├── output-live/          # Folio JSON files (XL output, manuscript text)
├── render-output/        # ScribeSim PNG renders (gitignored)
├── weather-output/       # Weathered PNGs and provenance (gitignored)
├── debug/                # Per-line render debug snapshots (gitignored)
├── scripts/
│   ├── render_all.py     # Render all folios currently present in output-live
│   ├── render_f01r.py    # Individual folio render scripts
│   ├── render_f01v.py
│   ├── render_f02r.py
│   └── ...
├── weather/
│   ├── cli.py            # weather CLI (weather-map, weather-folio, weather-codex, weather-validate)
│   ├── codexmap.py       # Codex damage map computation
│   ├── promptgen.py      # AI prompt generation (full + background-only)
│   ├── aiweather.py      # AI compositing pipeline + ink aging
│   ├── aivalidation.py   # Post-weathering validation (V1 text drift, V2 pre-degradation, V3 stain consistency)
│   ├── worddegrade.py    # Word-level pre-degradation from CLIO-7 annotations
│   └── codex_map.json    # Generated codex damage map
├── scribesim/            # ScribeSim Bastarda rendering engine
├── xl/                   # XL translation and structuring tools
├── arrive/               # ARRIVE governance artifacts
├── tests/                # Test suite (pytest)
├── pyproject.toml
└── .env                  # API keys (gitignored)
```

---

## Governance

This project uses [ARRIVE](arrive/) for outcome-first development. The three systems (xl, scribesim, weather) each have component YAMLs and advance records under `arrive/systems/`. Cross-system architectural decisions live in `docs/tech-direction/`.

Development follows **Tidy First → Test First → Implement**. Run the test suite with:

```bash
uv run pytest
uv run pytest -m "not slow"   # skip long-running AI integration tests
```
