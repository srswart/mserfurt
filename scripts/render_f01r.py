"""Render the full f01r folio page, saving cumulative progress to Desktop every 3 lines."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# ── project root on path ──────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scribesim.evo.compose import render_line
from scribesim.evo.renderer import _PARCHMENT

# ── layout constants ──────────────────────────────────────────────────────────
DPI           = 300
NIB_MM        = 0.65
X_HEIGHT_MM   = 3.8
LINE_HEIGHT_MM = 14.0      # word-canvas height (baseline at 10mm within it)
LINE_SPACING_MM = 10.0     # baseline-to-baseline distance
MARGIN_LEFT_MM  = 10.0
MARGIN_RIGHT_MM = 10.0
MARGIN_TOP_MM   = 12.0
PAGE_WIDTH_MM   = 170.0   # 170 - 10 left - 10 right = 150mm text area, fits widest line (~143mm)

FOLIO_JSON  = ROOT / "output-live" / "f01r.json"
OUT_DIR     = ROOT / "debug" / "f01r_page"
DESKTOP     = Path.home() / "Desktop"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── load lines ────────────────────────────────────────────────────────────────
data  = json.loads(FOLIO_JSON.read_text())
lines = [l["text"] for l in data["lines"]]
N     = len(lines)

# ── page canvas ───────────────────────────────────────────────────────────────
px_per_mm = DPI / 25.4
page_h_mm = MARGIN_TOP_MM + N * LINE_SPACING_MM + LINE_HEIGHT_MM + MARGIN_TOP_MM
w_px = int(PAGE_WIDTH_MM * px_per_mm)
h_px = int(page_h_mm   * px_per_mm)

page = np.full((h_px, w_px, 3), _PARCHMENT, dtype=np.uint8)


def darken_paste(page_arr: np.ndarray, line_arr: np.ndarray, x_off: int, y_off: int) -> None:
    """Composite line_arr onto page_arr using darken blend (min per channel).

    Only updates pixels within the page bounds; parchment background of the
    line canvas does not overwrite page content because min(parchment, parchment)
    is identical and min(parchment, ink) keeps the ink.
    """
    lh, lw = line_arr.shape[:2]
    y0 = max(0, y_off)
    y1 = min(h_px, y_off + lh)
    x0 = max(0, x_off)
    x1 = min(w_px, x_off + lw)
    if y0 >= y1 or x0 >= x1:
        return
    src_y0 = y0 - y_off
    src_y1 = src_y0 + (y1 - y0)
    src_x0 = x0 - x_off
    src_x1 = src_x0 + (x1 - x0)
    page_slice = page_arr[y0:y1, x0:x1]
    line_slice = line_arr[src_y0:src_y1, src_x0:src_x1]
    np.minimum(page_slice, line_slice, out=page_slice)


def save_page(label: str) -> None:
    img = Image.fromarray(page, "RGB")
    # Save to project debug dir
    out_path = OUT_DIR / f"f01r_{label}.png"
    img.save(str(out_path), dpi=(DPI, DPI))
    # Also copy to Desktop for live preview
    desktop_path = DESKTOP / "f01r_page.png"
    img.save(str(desktop_path), dpi=(DPI, DPI))
    print(f"  ── page saved → {out_path.name}  (Desktop updated)", flush=True)


# ── render line by line ───────────────────────────────────────────────────────
x_off_px = int(MARGIN_LEFT_MM * px_per_mm)

for li, line_text in enumerate(lines):
    baseline_y_on_page_mm = MARGIN_TOP_MM + li * LINE_SPACING_MM + 10.0  # 10mm = baseline in canvas
    y_paste_mm = baseline_y_on_page_mm - 10.0   # top of 14mm canvas
    y_off_px = int(y_paste_mm * px_per_mm)

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

    # Save progress snapshot every 3 lines and at the very end
    if (li + 1) % 3 == 0 or li == N - 1:
        save_page(f"line{li+1:02d}")

print(f"\nDone. {N} lines rendered.", flush=True)
