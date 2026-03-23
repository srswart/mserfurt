"""Render f01r — recto, leaf 1.  Modest private manuscript layout."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scribesim.evo.compose import render_line
from scribesim.evo.renderer import _PARCHMENT

# ── Page geometry ─────────────────────────────────────────────────────────────
# Standard gathering (f01–f13): modest private confession folio
DPI             = 300
PAGE_WIDTH_MM   = 185.0
PAGE_HEIGHT_MM  = 250.0
MARGIN_TOP_MM   = 20.0
MARGIN_BOTTOM_MM = 50.0
MARGIN_INNER_MM  = 20.0   # binding side
MARGIN_OUTER_MM  = 35.0   # fore-edge

# Text block derived from margins
TEXT_W_MM = PAGE_WIDTH_MM  - MARGIN_INNER_MM - MARGIN_OUTER_MM   # 130 mm
TEXT_H_MM = PAGE_HEIGHT_MM - MARGIN_TOP_MM   - MARGIN_BOTTOM_MM  # 180 mm

# Script parameters
NIB_MM          = 0.50
X_HEIGHT_MM     = 3.0
LINE_HEIGHT_MM  = 11.0    # total canvas height passed to render_line
BASELINE_IN_CANVAS_MM = 7.5  # baseline sits 7.5 mm from top of canvas
LINE_SPACING_MM = 8.0    # baseline-to-baseline
LINES_PER_PAGE  = int(TEXT_H_MM / LINE_SPACING_MM)   # 22

# Recto: gutter on the left → inner margin is left margin
MARGIN_LEFT_MM  = MARGIN_INNER_MM

FOLIO_JSON  = ROOT / "output-live" / "f01r.json"
RENDER_OUT  = ROOT / "render-output" / "f01r.png"
DEBUG_DIR   = ROOT / "debug" / "f01r_page"
DESKTOP     = Path.home() / "Desktop"

DEBUG_DIR.mkdir(parents=True, exist_ok=True)

# ── Canvas ────────────────────────────────────────────────────────────────────
px_per_mm = DPI / 25.4
w_px = int(PAGE_WIDTH_MM  * px_per_mm)
h_px = int(PAGE_HEIGHT_MM * px_per_mm)
page = np.full((h_px, w_px, 3), _PARCHMENT, dtype=np.uint8)

data  = json.loads(FOLIO_JSON.read_text())
lines = [l["text"] for l in data["lines"]][:LINES_PER_PAGE]
N     = len(lines)


def darken_paste(page_arr, line_arr, x_off, y_off):
    lh, lw = line_arr.shape[:2]
    y0 = max(0, y_off);  y1 = min(h_px, y_off + lh)
    x0 = max(0, x_off);  x1 = min(w_px, x_off + lw)
    if y0 >= y1 or x0 >= x1:
        return
    src = line_arr[y0-y_off:y0-y_off+(y1-y0), x0-x_off:x0-x_off+(x1-x0)]
    np.minimum(page_arr[y0:y1, x0:x1], src, out=page_arr[y0:y1, x0:x1])


def save_progress(label):
    img = Image.fromarray(page, "RGB")
    img.save(str(DEBUG_DIR / f"f01r_{label}.png"), dpi=(DPI, DPI))
    img.save(str(DESKTOP / "f01r_page.png"),        dpi=(DPI, DPI))
    print(f"  ── {label}  (Desktop updated)", flush=True)


x_off_px = int(MARGIN_LEFT_MM * px_per_mm)

for li, line_text in enumerate(lines):
    # Baseline position on page, then back-calculate canvas top
    baseline_mm = MARGIN_TOP_MM + li * LINE_SPACING_MM + BASELINE_IN_CANVAS_MM
    y_off_px    = int((baseline_mm - BASELINE_IN_CANVAS_MM) * px_per_mm)

    print(f"\nLine {li+1:2d}/{N}  {line_text[:60]!r}", flush=True)

    line_arr = render_line(
        line_text,
        dpi=DPI,
        nib_width_mm=NIB_MM,
        x_height_mm=X_HEIGHT_MM,
        line_height_mm=LINE_HEIGHT_MM,
        verbose=True,
        variation=1.0,
    )
    darken_paste(page, line_arr, x_off_px, y_off_px)

    if (li + 1) % 3 == 0 or li == N - 1:
        save_progress(f"line{li+1:02d}")

# Save final render to render-output/
final = Image.fromarray(page, "RGB")
final.save(str(RENDER_OUT), dpi=(DPI, DPI))
print(f"\nDone. {N} lines → {RENDER_OUT}", flush=True)
