#!/usr/bin/env python
"""DiffusionPen CommandBackend runner (TD-018).

Run from inside a clone of https://github.com/koninik/DiffusionPen with its
dependencies installed and fine-tuned weights. Invoked by scribesim's
CommandBackend (see scripts/scribehand/README.md for the protocol).

DiffusionPen builds on SD-1.5's VAE + a 5-shot style encoder. `controls`
from the request map onto sampler knobs:

- ``style_noise``    → noise added to the style embedding (variation)
- ``guidance_scale`` → classifier-free guidance

NOTE: research repo — adjust `load_pipeline` against your checked-out
revision if imports fail; errors are reported verbatim to stderr.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np


def log(msg: str) -> None:
    print(f"[diffusionpen-runner] {msg}", file=sys.stderr, flush=True)


def load_pipeline(checkpoint: str, device: str):
    """Load DiffusionPen UNet + VAE + style encoder. Adjust to your revision."""
    import torch

    ckpt_dir = Path(checkpoint)
    if not ckpt_dir.exists():
        raise FileNotFoundError(f"DiffusionPen checkpoint dir not found: {ckpt_dir}")

    try:
        from unet import UNetModel                              # type: ignore
        from feature_extractor import ImageEncoder              # type: ignore
        from diffusers import AutoencoderKL, DDIMScheduler      # type: ignore
    except ImportError as exc:
        raise ImportError(
            "could not import DiffusionPen modules — run with "
            "cwd=<DiffusionPen clone> (configure workdir in backends.toml). "
            f"underlying error: {exc}"
        ) from exc

    unet = UNetModel().to(device)
    unet.load_state_dict(
        __import__("torch").load(ckpt_dir / "models" / "ckpt.pt", map_location=device)
    )
    unet.eval()
    vae = AutoencoderKL.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5", subfolder="vae"
    ).to(device)
    style_encoder = ImageEncoder()
    style_state = ckpt_dir / "style_models" / "style_encoder.pth"
    if style_state.exists():
        style_encoder.load_state_dict(
            __import__("torch").load(style_state, map_location=device)
        )
    style_encoder = style_encoder.to(device).eval()
    scheduler = DDIMScheduler.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5", subfolder="scheduler"
    )
    return unet, vae, style_encoder, scheduler


def style_batch(style_dir: str | None, rng: random.Random, k: int = 5):
    from PIL import Image

    if not style_dir:
        raise ValueError("DiffusionPen requires style_dir (5-shot style anchor)")
    meta = json.loads((Path(style_dir) / "style.json").read_text())
    exemplars = list(meta["exemplars"])
    picks = [exemplars[i % len(exemplars)]
             for i in rng.sample(range(max(len(exemplars), k)), k)] \
        if len(exemplars) >= k else exemplars * (k // max(1, len(exemplars)) + 1)
    return [Image.open(Path(style_dir) / p).convert("L") for p in picks[:k]]


def to_ink_mask(sample) -> "np.ndarray":
    arr = np.asarray(sample, dtype=np.float32)
    if arr.ndim == 3:
        arr = arr.mean(axis=2)
    if arr.max() <= 1.0:
        arr = arr * 255.0
    mask = np.clip(255.0 - arr, 0, 255)
    mask[mask < 16] = 0
    return mask.astype(np.uint8)


def estimate_fracs(mask: "np.ndarray") -> tuple[float, float]:
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

    req = json.loads(Path(args.request).read_text())

    import torch
    from PIL import Image

    device = ("mps" if torch.backends.mps.is_available()
              else ("cuda" if torch.cuda.is_available() else "cpu"))
    log(f"device={device} words={len(req['words'])}")

    unet, vae, style_encoder, scheduler = load_pipeline(req["checkpoint"], device)

    results = []
    for w in req["words"]:
        seed = int(w["seed"])
        controls = w.get("controls", {})
        torch.manual_seed(seed)
        rng = random.Random(seed)

        styles = style_batch(req.get("style_dir"), rng)

        # ---- sampling: adjust to your DiffusionPen revision's API ----
        from sampling import sample_word                        # type: ignore

        sample = sample_word(
            unet=unet, vae=vae, style_encoder=style_encoder, scheduler=scheduler,
            text=w["text"], style_images=styles, device=device,
            guidance_scale=float(controls.get("guidance_scale", 2.0)),
            style_noise=float(controls.get("style_noise", 0.1)),
            generator=torch.Generator(device="cpu").manual_seed(seed),
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
        "runner": {"name": "diffusionpen", "device": device,
                   "checkpoint": req.get("checkpoint")},
        "results": results,
    }))


if __name__ == "__main__":
    main()
