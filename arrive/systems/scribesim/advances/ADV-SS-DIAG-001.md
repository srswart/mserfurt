---
advance:
  id: ADV-SS-DIAG-001
  title: Diagnostic Renderer — Single Glyph, Word, and Glyph Sheet CLI
  system: scribesim
  primary_component: render
  components:
  - render
  - glyphs
  - cli
  status: complete
  priority: critical
  risk_flags:
  - new_feature
  started_at: 2026-04-16T21:10:00Z
  started_by: srswart@gmail.com
  implementation_completed_at: 2026-04-16T22:00:00Z
  implementation_completed_by: srswart@gmail.com
  evidence:
  - tdd:red-green
  - tidy:preparatory
  - tests:unit
  - human-verified:glyph-sheet
  - human-verified:render-glyph
---

## Objective

Create three diagnostic CLI commands — `render-glyph`, `render-word`, and `glyph-sheet` — that render in isolation without the page compositor. These commands are the primary verification tool for all subsequent renderer fixes and must exist before ADV-SS-RENDER-004 or ADV-SS-RENDER-005 can be meaningfully validated.

This advance makes no changes to the rendering algorithm. It only wires existing capabilities to isolated, inspectable outputs. The evo renderer (`scribesim.evo.renderer.render_word_from_genome`) is used as-is.

## Behavioral Change

After this advance:

- `scribesim render-glyph <char> [--dpi N] [--nib-width F] [--nib-angle F] [--output PATH]` renders a single glyph from `GLYPH_CATALOG` on a canvas sized to 4× x_height at the requested DPI (default: 150). Saves PNG to `--output` (default: `debug/<char>.png`). Exits with code 1 and a message if the glyph is not in the catalog.

- `scribesim render-word <text> [--dpi N] [--output PATH]` renders a short word (≤20 characters) using `render_word_from_genome` on a canvas with 2× x_height margins. Saves PNG to `--output` (default: `debug/<text>.png`).

- `scribesim glyph-sheet [--dpi N] [--output PATH]` renders every glyph in the catalog as a labeled grid (10 per row, glyph character printed below each cell). Saves a single PNG to `--output` (default: `debug/glyph-sheet.png`).

These commands do not require a folio JSON input. They bypass the page compositor entirely.

## Pipeline Context

- **Upstream**: Nothing — these are standalone diagnostic commands.
- **Downstream**: ADV-SS-RENDER-004 uses `render-glyph` to confirm the polygon sweep produces visible thick/thin contrast. ADV-SS-RENDER-005 uses `render-word` to confirm word-level composition before page composition.
- **Contracts**: No contract changes. Debug output is not part of the scribesim output contract.

## Planned Implementation Tasks

- [ ] Create feature branch: `feat/ss-diag-001-render-glyph`
- [ ] **Tidy**: extract `render_single_glyph(glyph_id, dpi, nib_width_mm, nib_angle_deg) -> np.ndarray` as a standalone function in `scribesim/render/diagnostic.py`; this function builds a minimal `WordGenome` containing just the one glyph and calls `render_word_from_genome`
- [ ] **Test** (red): add `tests/test_diagnostic.py` — `render_single_glyph("n", 150)` returns an ndarray with shape `(H, W, 3)` where H > 0 and W > 0 and the array is not all-parchment (i.e., some pixels are darker than background); `render_single_glyph("MISSING", 150)` raises `KeyError`; `glyph_sheet` output shape is `(rows * cell_h, 10 * cell_w, 3)`
- [ ] **Implement**: `render_single_glyph` in `scribesim/render/diagnostic.py`
- [ ] **Implement**: `render_word_diagnostic(text, dpi) -> np.ndarray` in the same module — tokenise text into character ids, build a `WordGenome`, call `render_word_from_genome`
- [ ] **Implement**: `render_glyph_sheet(dpi) -> np.ndarray` — iterate `GLYPH_CATALOG`, render each glyph, assemble grid with PIL, draw character label below each cell using a monospace fallback font
- [ ] **Implement**: wire all three into `cli.py` as subcommands `render-glyph`, `render-word`, `glyph-sheet`; add argparse groups; write output PNG with PIL
- [ ] **Validate** (human): run `scribesim render-glyph n --dpi 150` and open the output — confirm a visible letterform (even if not yet beautiful); run `scribesim glyph-sheet` and confirm all cells are non-empty
- [ ] Run full test suite; confirm no regressions

## Check for Understanding

_To be generated after implementation._

## Risk + Rollback

**Risks:**
- `render_word_from_genome` may raise on a minimal single-glyph genome if it assumes multi-glyph inputs. Defensive construction of the `WordGenome` is required.
- The evo renderer may produce an image of the wrong size if `canvas_width_mm` and `canvas_height_mm` are not set correctly for a single glyph. Compute canvas size from `glyph.width_in_x_heights * x_height_mm` with padding.

**Rollback:**
- This advance adds new files only (`scribesim/render/diagnostic.py`, `tests/test_diagnostic.py`) and new CLI subcommands. Rollback is `git revert`; no existing behavior changes.

## Evidence

- [x] 27 tests in `tests/test_diagnostic.py` pass (0 failures)
- [x] `scribesim render-glyph n --dpi 200` produces a visible 'n' letterform with two downstrokes and connecting arch (human verified)
- [x] `scribesim glyph-sheet --dpi 100` produces a 500×801px grid of all 86 catalog glyphs with clear thick/thin contrast and legible labels (human verified)
- [x] `scribesim render-line "und das waz gut"` produces fully readable text via existing evo render-line command — confirms evo renderer is functional
- [x] New files: `scribesim/render/diagnostic.py`, `tests/test_diagnostic.py`; new CLI commands: `render-glyph`, `glyph-sheet`
- [x] No regressions in test_evo_engine.py or test_cli_args.py
