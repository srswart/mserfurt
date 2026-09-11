#!/usr/bin/env python
"""One-DM CommandBackend runner (TD-018).

Run from inside a clone of https://github.com/dailenson/One-DM with its
dependencies installed and a fine-tuned checkpoint. Invoked by scribesim's
CommandBackend (see scripts/scribehand/README.md for the protocol).

NOTE: One-DM is a research repo; module paths below target its public layout
(models/unet.py, models/diffusion.py, One-DM-ckpt.pt). Adjust `load_pipeline`
against your checked-out revision if imports fail — the error report in
stderr states exactly what was missing.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np


def log(msg: str) -> None:
    print(f"[onedm-runner] {msg}", file=sys.stderr, flush=True)


def load_pipeline(checkpoint: str, device: str):
    """Load the One-DM sampling pipeline. Adjust against your revision."""
    import torch

    ckpt_path = Path(checkpoint)
    if not ckpt_path.exists():
        raise FileNotFoundError(f"One-DM checkpoint not found: {ckpt_path}")

    # ---- upstream imports (repo root must be on sys.path / cwd) ----
    try:
        from models.unet import UNetModel                      # type: ignore
        from models.diffusion import Diffusion                 # type: ignore
    except ImportError as exc:
        raise ImportError(
            "could not import One-DM modules — run this script with "
            "cwd=<One-DM clone> (configure workdir in backends.toml). "
            f"underlying error: {exc}"
        ) from exc

    state = torch.load(ckpt_path, map_location=device)
    model = UNetModel(
        in_channels=state.get("in_channels", 2) if isinstance(state, dict) else 2,
    )
    model.load_state_dict(state["model"] if "model" in state else state)
    model = model.to(device).eval()
    diffusion = Diffusion(device=device)
    return model, diffusion


def style_reference(style_dir: str | None, rng: random.Random):
    from PIL import Image

    if not style_dir:
        raise ValueError("One-DM requires style_dir (style anchor exemplars)")
    meta = json.loads((Path(style_dir) / "style.json").read_text())
    exemplars = meta["exemplars"]
    pick = rng.choice(exemplars)
    return Image.open(Path(style_dir) / pick).convert("L")


def to_ink_mask(sample: "np.ndarray") -> "np.ndarray":
    """Model output (light bg, dark ink) → ink mask (0 = no ink)."""
    arr = np.asarray(sample, dtype=np.float32)
    if arr.ndim == 3:
        arr = arr.mean(axis=2)
    if arr.max() <= 1.0:
        arr = arr * 255.0
    mask = np.clip(255.0 - arr, 0, 255)
    # normalize faint backgrounds away
    mask[mask < 16] = 0
    return mask.astype(np.uint8)


def estimate_fracs(mask: "np.ndarray") -> tuple[float, float]:
    """Estimate baseline/x-height fractions from the ink profile."""
    rows = mask.sum(axis=1).astype(np.float64)
    if rows.sum() <= 0:
        return 0.75, 0.35
    ys = np.nonzero(rows > rows.max() * 0.05)[0]
    top, bottom = int(ys[0]), int(ys[-1])
    h = mask.shape[0]
    # dense band ≈ x-height zone
    dense = np.nonzero(rows > rows.max() * 0.45)[0]
    x_top = int(dense[0]) if dense.size else top
    baseline = int(dense[-1]) if dense.size else bottom
    return baseline / h, max(0.05, (baseline - x_top) / h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--response", required=True)
    args = ap.parse_args()

    req = json.loads(Path(args.request).read_text())

    import torch
    from PIL import Image

    device = ("mps" if torch.backends.mps.is_available()
              else ("cuda" if torch.cuda.is_available() else "cpu"))
    log(f"device={device} words={len(req['words'])}")

    model, diffusion = load_pipeline(req["checkpoint"], device)

    results = []
    for w in req["words"]:
        seed = int(w["seed"])
        torch.manual_seed(seed)
        rng = random.Random(seed)
        style_img = style_reference(req.get("style_dir"), rng)

        # ---- sampling call: adjust to your One-DM revision's API ----
        sample = diffusion.sample(
            model=model,
            text=w["text"],
            style=style_img,
            device=device,
        )
        mask = to_ink_mask(sample)
        Image.fromarray(mask, "L").save(w["out"])
        baseline_frac, xheight_frac = estimate_fracs(mask)
        results.append({
            "id": w["id"], "image": w["out"],
            "baseline_frac": baseline_frac, "xheight_frac": xheight_frac,
        })
        log(f"  {w['text']!r} seed={seed} → {w['out']}")

    Path(args.response).write_text(json.dumps({
        "schema": 1,
        "runner": {"name": "onedm", "device": device,
                   "checkpoint": req.get("checkpoint")},
        "results": results,
    }))


if __name__ == "__main__":
    main()
