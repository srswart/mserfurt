# AGENTS.md

## Cursor Cloud specific instructions

This is a Python 3.11+ manuscript-simulation pipeline with three subsystems exposed as
console scripts (see `pyproject.toml` `[project.scripts]`):

- `xl` — authoring / folio structuring
- `scribesim` — Bastarda-script rendering engine (`python -m scribesim ...`)
- `weather` — 500-year manuscript aging (`python -m weather ...` / `weather` script)

Standard setup/run/test commands live in `README.md`. Notes below are the non-obvious
gotchas discovered while setting up the cloud environment.

### Dependencies / tooling
- The project uses **uv**. `uv` is already installed and on `PATH` (the installer added
  `. "$HOME/.local/bin/env"` to `~/.bashrc`, so fresh login shells find it). The startup
  update script runs `uv sync` (creates `.venv/`) and `uv pip install pytest`.
- **`pytest` is NOT declared** in `pyproject.toml` dependencies even though tests and the
  README rely on it. It is installed separately by the update script; if you re-run
  `uv sync` manually it will prune `pytest`, so reinstall it with `uv pip install pytest`.
- `uv.lock` is **gitignored** — do not expect it in version control; `uv sync` regenerates it.
- The `run_*.sh` helper scripts invoke `.venv/bin/python` directly, so they require a prior
  `uv sync`.

### Linting
- No linter is configured (no ruff/flake8/black/mypy config in the repo). There is no lint
  command to run.

### Known pre-existing test breakage (NOT an environment problem)
- `scribesim/refextract/`, `scribesim/refselect/`, and `scribesim/transcribe/` are
  **gitignored** (`.gitignore` "ScribeSim runtime caches"), so those modules are absent from
  a fresh clone. Code such as `scribesim.pathguide.io` imports `scribesim.refextract.centerline`,
  which causes ~26 test-collection **errors** (e.g. `test_pathguide*`, `test_segment`,
  `test_handflow*`, `test_annotate*`, `test_refselect_*`, `test_wordassist`, `test_strokeassist`).
- Beyond the collection errors, ~166 tests **fail** due to test/code drift (e.g.
  `tests/test_promptgen.py` asserts older prompt strings the current `weather/promptgen.py`
  no longer emits). These are pre-existing and not caused by environment setup.
- Baseline as of setup: `uv run pytest -m "not slow"` → ~1165 passed, ~166 failed, 26 errors,
  in ~7 min. Run `uv run pytest -m "not slow"` (the `slow` marker gates long AI integration tests).

### Running the pipeline
- Rendering a folio is CPU-heavy: `uv run python -m scribesim render f01r --input-dir output-live
  --output-dir render-output` runs a genetic-algorithm stroke evolution (~1-2 min for a 23-line
  folio). Add `--dry-run` to skip the actual raster pass. Batch: `uv run python -m scribesim render-batch`.
- `render-output/`, `weather-output/`, and `debug/` are gitignored output directories.
- `uv run weather weather-map --gathering-size 17 --output weather/codex_map.json` computes the
  physical damage model offline (no API key needed).
- The **AI weathering** steps (`weather weather-codex` / `weather-folio` without `--dry-run`)
  call OpenAI `gpt-image-1` and require `OPENAI_API_KEY` in `.env`; they cost money and cannot
  run without a key. Use `--dry-run` to inspect prompts offline.
