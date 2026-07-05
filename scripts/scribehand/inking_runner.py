#!/usr/bin/env python
"""Hybrid inking CommandBackend runner (skeleton → neural ink).

Pipeline per request:
1. Render the text with the deterministic evo Bastarda engine (legible glyphs,
   guaranteed spelling).
2. Binarize + skeletonize the render with the SAME operator used to build the
   training pairs (build_inking_dataset.py) — no domain gap.
3. Translate the skeleton to realistic Cgm 628 ink with the pix2pix generator
   (train_inking_pix2pix.py checkpoint).

Runs from the repo root in the project venv (no external clone needed).
Checkpoint dir must contain generator.pt.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

IMG_H = 128            # generator training height
WIDTH_MULTIPLE = 64    # U-Net has 6 stride-2 levels


def log(msg: str) -> None:
    print(f"[inking-runner] {msg}", file=sys.stderr, flush=True)


def render_evo_line(text: str, seed: int) -> np.ndarray:
    """Render text as an ink mask (0..255, ink=255) with the evo engine."""
    import random as _random

    from scribesim.evo.genome import genome_from_guides
    from scribesim.evo.renderer import render_word_from_genome, _PARCHMENT

    x_height_mm = 3.0
    canvas_h_mm = 11.0
    baseline_y_mm = 7.5
    dpi = 300.0
    gap_px = int(round(x_height_mm * 0.45 * dpi / 25.4))

    strips = []
    for wi, word in enumerate(text.split()):
        _random.seed(seed + wi * 7919)
        genome = genome_from_guides(
            word, baseline_y_mm=baseline_y_mm, x_height_mm=x_height_mm)
        rgb = render_word_from_genome(
            genome, dpi=dpi, nib_width_mm=0.5,
            canvas_height_mm=canvas_h_mm, variation=1.0)
        arr = rgb.astype(np.int16)
        parchment = np.array(_PARCHMENT, dtype=np.int16)
        deficit = np.clip(parchment[None, None, :] - arr, 0, None).max(axis=2)
        ink = np.clip(deficit.astype(np.float32) / max(1, int(parchment.max())) * 255.0,
                      0, 255).astype(np.uint8)
        strips.append(ink)

    if not strips:
        return np.zeros((IMG_H, WIDTH_MULTIPLE), dtype=np.uint8)

    h = max(s.shape[0] for s in strips)
    gap = np.zeros((h, gap_px), dtype=np.uint8)
    padded = []
    for s in strips:
        if s.shape[0] < h:
            s = np.pad(s, ((0, h - s.shape[0]), (0, 0)))
        padded.append(s)
    row = padded[0]
    for s in padded[1:]:
        row = np.concatenate([row, gap, s], axis=1)
    return row


def skeleton_input(ink_mask: np.ndarray) -> np.ndarray:
    """Ink mask → height-normalized skeleton image (white bg, black strokes).

    Mirrors build_inking_dataset.process_strip: vertical crop to the ink band,
    height-normalize, binarize, skeletonize.
    """
    from PIL import Image

    sys.path.insert(0, str(Path(__file__).parent))
    from build_inking_dataset import binarize_ink, skeleton_of, _height_normalize

    rows = np.nonzero(ink_mask.sum(axis=1) > 0)[0]
    if rows.size:
        pad = 4
        y0 = max(0, int(rows[0]) - pad)
        y1 = min(ink_mask.shape[0], int(rows[-1]) + 1 + pad)
        ink_mask = ink_mask[y0:y1]

    gray = (255 - ink_mask).astype(np.uint8)         # ink-on-white
    img = _height_normalize(Image.fromarray(gray, "L"), IMG_H)
    arr = np.asarray(img)
    mask = binarize_ink(arr)
    skel = skeleton_of(mask)
    return np.where(skel, 0, 255).astype(np.uint8)


def load_generator(checkpoint_dir: Path, device: str):
    import torch

    sys.path.insert(0, str(Path(__file__).parent))
    from train_inking_pix2pix import _build_models

    gen, _ = _build_models(device)
    state = torch.load(checkpoint_dir / "generator.pt", map_location=device)
    gen.load_state_dict(state)
    # keep dropout active: seeded stochastic ink texture per line
    gen.train()
    return gen


def ink_line(gen, skel_u8: np.ndarray, seed: int, device: str) -> np.ndarray:
    """Skeleton image (white bg) → generated ink mask (0..255, ink=255)."""
    import torch

    w = skel_u8.shape[1]
    pad_w = (WIDTH_MULTIPLE - w % WIDTH_MULTIPLE) % WIDTH_MULTIPLE
    if pad_w:
        skel_u8 = np.pad(skel_u8, ((0, 0), (0, pad_w)), constant_values=255)

    torch.manual_seed(seed)
    x = torch.from_numpy(skel_u8.astype(np.float32) / 127.5 - 1.0)
    x = x.unsqueeze(0).unsqueeze(0).to(device)
    with torch.no_grad():
        y = gen(x)[0, 0].cpu().numpy()
    ink_on_white = ((y + 1.0) * 127.5).clip(0, 255)
    mask = (255.0 - ink_on_white).clip(0, 255).astype(np.uint8)
    mask[mask < 16] = 0
    return mask[:, :w] if pad_w else mask


def estimate_fracs(mask: np.ndarray) -> tuple[float, float]:
    rows = mask.sum(axis=1).astype(np.float64)
    if rows.sum() <= 0:
        return 0.75, 0.35
    dense = np.nonzero(rows > rows.max() * 0.45)[0]
    ys = np.nonzero(rows > rows.max() * 0.05)[0]
    h = mask.shape[0]
    x_top = int(dense[0]) if dense.size else int(ys[0])
    baseline = int(dense[-1]) if dense.size else int(ys[-1])
    return baseline / h, max(0.05, (baseline - x_top) / h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--response", required=True)
    args = ap.parse_args()

    import torch
    from PIL import Image

    req = json.loads(Path(args.request).read_text())
    device = (
        "mps" if torch.backends.mps.is_available()
        else ("cuda" if torch.cuda.is_available() else "cpu")
    )
    log(f"device={device} items={len(req['words'])}")

    gen = load_generator(Path(req["checkpoint"]), device)

    results = []
    for w in req["words"]:
        seed = int(w["seed"])
        evo_ink = render_evo_line(w["text"], seed)
        skel = skeleton_input(evo_ink)
        mask = ink_line(gen, skel, seed, device)
        Image.fromarray(mask, "L").save(w["out"])
        baseline_frac, xheight_frac = estimate_fracs(mask)
        results.append({
            "id": w["id"], "image": w["out"],
            "baseline_frac": baseline_frac, "xheight_frac": xheight_frac,
        })
        log(f"  {w['text'][:40]!r} seed={seed} → {w['out']}")

    Path(args.response).write_text(json.dumps({
        "schema": 1,
        "runner": {"name": "inking", "device": device,
                   "checkpoint": req.get("checkpoint")},
        "results": results,
    }))


if __name__ == "__main__":
    main()
