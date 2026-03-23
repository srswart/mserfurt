"""Render all 34 folio pages (f01r–f17v) to render-output/{fid}.png.

Standard gathering (f01–f13): 185×250mm, 22 lines, nib 0.5mm, x-height 3.0mm
Final gathering  (f14–f17):   155×212mm, 18 lines, nib 0.5mm, x-height 3.0mm
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scribesim.evo.compose import render_line
from scribesim.evo.renderer import _PARCHMENT

# ── Layout presets ────────────────────────────────────────────────────────────

STANDARD = dict(
    page_w=185.0, page_h=250.0,
    margin_top=20.0, margin_bottom=50.0,
    margin_inner=20.0, margin_outer=35.0,
    nib=0.50, x_height=3.0,
    line_height=11.0, baseline_in_canvas=7.5,
    line_spacing=8.0,
)

IRREGULAR = dict(
    page_w=155.0, page_h=212.0,
    margin_top=18.0, margin_bottom=46.0,
    margin_inner=15.0, margin_outer=28.0,
    nib=0.50, x_height=3.0,
    line_height=11.0, baseline_in_canvas=7.5,
    line_spacing=8.0,
)

DPI = 300
px_per_mm = DPI / 25.4

FOLIO_DIR  = ROOT / "output-live"
RENDER_DIR = ROOT / "render-output"
RENDER_DIR.mkdir(exist_ok=True)

# All folios in order
ALL_FOLIOS = [f"f{n:02d}{s}" for n in range(1, 18) for s in ("r", "v")]


def layout(fid: str) -> dict:
    n = int(fid[1:3])
    return IRREGULAR if n >= 14 else STANDARD


def lines_per_page(cfg: dict) -> int:
    text_h = cfg["page_h"] - cfg["margin_top"] - cfg["margin_bottom"]
    return int(text_h / cfg["line_spacing"])


def render_folio(fid: str) -> None:
    json_path = FOLIO_DIR / f"{fid}.json"
    if not json_path.exists():
        print(f"  [skip] {fid}: no JSON", flush=True)
        return

    cfg     = layout(fid)
    side    = fid[-1]
    w_px    = int(cfg["page_w"] * px_per_mm)
    h_px    = int(cfg["page_h"] * px_per_mm)
    lpp     = lines_per_page(cfg)

    # Gutter: recto → inner left; verso → outer left
    margin_left = cfg["margin_inner"] if side == "r" else cfg["margin_outer"]
    x_off_px    = int(margin_left * px_per_mm)

    data  = json.loads(json_path.read_text())
    lines = [l["text"] for l in data["lines"]][:lpp]
    N     = len(lines)

    page = np.full((h_px, w_px, 3), _PARCHMENT, dtype=np.uint8)

    def darken_paste(line_arr, x_off, y_off):
        lh, lw = line_arr.shape[:2]
        y0 = max(0, y_off);  y1 = min(h_px, y_off + lh)
        x0 = max(0, x_off);  x1 = min(w_px, x_off + lw)
        if y0 >= y1 or x0 >= x1:
            return
        src = line_arr[y0 - y_off: y0 - y_off + (y1 - y0),
                       x0 - x_off: x0 - x_off + (x1 - x0)]
        np.minimum(page[y0:y1, x0:x1], src, out=page[y0:y1, x0:x1])

    for li, text in enumerate(lines):
        baseline_mm = cfg["margin_top"] + li * cfg["line_spacing"] + cfg["baseline_in_canvas"]
        y_off_px    = int((baseline_mm - cfg["baseline_in_canvas"]) * px_per_mm)

        line_arr = render_line(
            text,
            dpi=DPI,
            nib_width_mm=cfg["nib"],
            x_height_mm=cfg["x_height"],
            line_height_mm=cfg["line_height"],
            verbose=False,
            variation=1.0,
        )
        darken_paste(line_arr, x_off_px, y_off_px)

    out = RENDER_DIR / f"{fid}.png"
    Image.fromarray(page, "RGB").save(str(out), dpi=(DPI, DPI))
    print(f"  saved → {out.name}  ({N} lines)", flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("folios", nargs="*", help="Folio IDs to render (default: all)")
    ap.add_argument("--skip-existing", action="store_true",
                    help="Skip folios that already have a render-output PNG")
    args = ap.parse_args()

    targets = args.folios if args.folios else ALL_FOLIOS

    total = len(targets)
    for i, fid in enumerate(targets, 1):
        out_path = RENDER_DIR / f"{fid}.png"
        if args.skip_existing and out_path.exists():
            print(f"[{i:2d}/{total}] {fid}  (already rendered, skipping)", flush=True)
            continue
        print(f"[{i:2d}/{total}] {fid}", flush=True)
        t0 = time.time()
        render_folio(fid)
        print(f"         {time.time()-t0:.1f}s", flush=True)

    print(f"\nDone. {total} folios processed.", flush=True)
