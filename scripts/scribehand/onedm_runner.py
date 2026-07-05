#!/usr/bin/env python
"""One-DM CommandBackend runner (TD-018).

Run from inside a clone of https://github.com/dailenson/One-DM with its
dependencies installed and a fine-tuned checkpoint. Invoked by scribesim's
CommandBackend (see scripts/scribehand/README.md for the protocol).

Requires ``data/unifont.pickle`` from the upstream English dataset bundle.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

STYLE_LEN = 352
# IAM64 charset from One-DM/data_loader/loader.py
LETTERS = (
    "_Only thewigsofrcvdampbkuq.A-210xT5'MDL,RYHJ\"ISPWENj&BC93VGFKz();#:!7U64Q8?+*ZX/%"
)


def log(msg: str) -> None:
    print(f"[onedm-runner] {msg}", file=sys.stderr, flush=True)


def _require_data_dir() -> Path:
    data_dir = Path.cwd() / "data"
    if not (data_dir / "unifont.pickle").exists():
        raise FileNotFoundError(
            "One-DM needs data/unifont.pickle — download English_data.zip from "
            "the One-DM README and extract into <One-DM>/data/"
        )
    return data_dir


def load_pipeline(checkpoint: str, device: str):
    """Load UNet + diffusion + SD VAE for DDIM sampling."""
    import torch
    from diffusers import AutoencoderKL

    ckpt_path = Path(checkpoint)
    if not ckpt_path.exists():
        raise FileNotFoundError(f"One-DM checkpoint not found: {ckpt_path}")

    try:
        from models.unet import UNetModel  # type: ignore
        from models.diffusion import Diffusion  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "could not import One-DM modules — run this script with "
            "cwd=<One-DM clone> (configure workdir in backends.toml). "
            f"underlying error: {exc}"
        ) from exc

    unet = UNetModel(
        in_channels=4,
        model_channels=512,
        out_channels=4,
        num_res_blocks=1,
        attention_resolutions=(1, 1),
        channel_mult=(1, 1),
        num_heads=4,
        context_dim=512,
    )
    state = torch.load(ckpt_path, map_location="cpu")
    unet.load_state_dict(state)
    unet = unet.to(device).eval()

    diffusion = Diffusion(device=device)
    vae = AutoencoderKL.from_pretrained(
        "runwayml/stable-diffusion-v1-5", subfolder="vae"
    ).to(device)
    vae.requires_grad_(False)
    return unet, diffusion, vae


def style_tensors(style_img, device: str):
    """Build style + laplace tensors from a grayscale PIL image."""
    import cv2
    import torch
    from PIL import Image

    # One-DM fusion expects IAM-style reference height (64px tall strips).
    img = style_img.convert("L")
    if img.height != 64:
        scale = 64 / max(1, img.height)
        new_w = max(1, int(img.width * scale))
        img = img.resize((new_w, 64), Image.Resampling.BILINEAR)

    arr = np.asarray(img, dtype=np.float32) / 255.0
    h, w = arr.shape[:2]
    use_w = min(w, STYLE_LEN)

    style = np.ones((h, STYLE_LEN), dtype=np.float32)
    style[:, :use_w] = arr[:, :use_w]

    lap = cv2.Laplacian((arr * 255.0).astype(np.uint8), cv2.CV_64F)
    lap = np.abs(lap)
    if lap.max() > 0:
        lap = lap / lap.max()
    laplace = np.zeros((h, STYLE_LEN), dtype=np.float32)
    laplace[:, :use_w] = lap[:, :use_w]

    style_t = torch.from_numpy(style).unsqueeze(0).unsqueeze(0).to(device)
    laplace_t = torch.from_numpy(laplace).unsqueeze(0).unsqueeze(0).to(device)
    return style_t, laplace_t


def encode_content(text: str, device: str):
    """Content glyph strip for the requested word (IAM64 charset)."""
    from data_loader.loader import ContentData  # type: ignore

    _require_data_dir()
    missing = [c for c in text if c not in LETTERS]
    if missing:
        raise ValueError(
            f"One-DM IAM charset cannot encode {missing!r} in {text!r}"
        )
    loader = ContentData(content_type="unifont")
    return loader.get_content(text).to(device)


def sample_word(
    unet,
    diffusion,
    vae,
    *,
    text: str,
    style_img,
    device: str,
    sampling_timesteps: int = 50,
    eta: float = 0.0,
) -> np.ndarray:
    """Run DDIM sampling; return H×W float32 grayscale (0=paper, 1=ink)."""
    import torch
    import torchvision

    style_input, laplace = style_tensors(style_img, device)
    text_ref = encode_content(text, device)
    n = 1
    x = torch.randn(
        (
            n,
            4,
            style_input.shape[2] // 8,
            (text_ref.shape[1] * 32) // 8,
        ),
        device=device,
    )
    with torch.no_grad():
        out = diffusion.ddim_sample(
            unet,
            vae,
            n,
            x,
            style_input,
            laplace,
            text_ref,
            sampling_timesteps=sampling_timesteps,
            eta=eta,
        )
    im = torchvision.transforms.ToPILImage()(out[0]).convert("L")
    return np.asarray(im, dtype=np.float32) / 255.0


def style_reference(style_dir: str | None, rng: random.Random):
    from PIL import Image

    if not style_dir:
        raise ValueError("One-DM requires style_dir (style anchor exemplars)")
    meta = json.loads((Path(style_dir) / "style.json").read_text())
    exemplars = meta["exemplars"]
    pick = rng.choice(exemplars)
    return Image.open(Path(style_dir) / pick).convert("L")


def to_ink_mask(sample: np.ndarray) -> np.ndarray:
    """Model output (light bg, dark ink) → ink mask (0 = no ink)."""
    arr = np.asarray(sample, dtype=np.float32)
    if arr.ndim == 3:
        arr = arr.mean(axis=2)
    if arr.max() <= 1.0:
        arr = arr * 255.0
    mask = np.clip(255.0 - arr, 0, 255)
    mask[mask < 16] = 0
    return mask.astype(np.uint8)


def estimate_fracs(mask: np.ndarray) -> tuple[float, float]:
    rows = mask.sum(axis=1).astype(np.float64)
    if rows.sum() <= 0:
        return 0.75, 0.35
    ys = np.nonzero(rows > rows.max() * 0.05)[0]
    top, bottom = int(ys[0]), int(ys[-1])
    h = mask.shape[0]
    dense = np.nonzero(rows > rows.max() * 0.45)[0]
    x_top = int(dense[0]) if dense.size else top
    baseline = int(dense[-1]) if dense.size else bottom
    return baseline / h, max(0.05, (baseline - x_top) / h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--response", required=True)
    args = ap.parse_args()

    sys.path.insert(0, str(Path.cwd()))

    req = json.loads(Path(args.request).read_text())

    import torch
    from PIL import Image

    device = (
        "mps"
        if torch.backends.mps.is_available()
        else ("cuda" if torch.cuda.is_available() else "cpu")
    )
    log(f"device={device} words={len(req['words'])}")

    unet, diffusion, vae = load_pipeline(req["checkpoint"], device)

    results = []
    for w in req["words"]:
        seed = int(w["seed"])
        torch.manual_seed(seed)
        rng = random.Random(seed)
        style_img = style_reference(req.get("style_dir"), rng)

        sample = sample_word(
            unet,
            diffusion,
            vae,
            text=w["text"],
            style_img=style_img,
            device=device,
        )
        mask = to_ink_mask(sample)
        Image.fromarray(mask, "L").save(w["out"])
        baseline_frac, xheight_frac = estimate_fracs(mask)
        results.append({
            "id": w["id"],
            "image": w["out"],
            "baseline_frac": baseline_frac,
            "xheight_frac": xheight_frac,
        })
        log(f"  {w['text']!r} seed={seed} → {w['out']}")

    Path(args.response).write_text(
        json.dumps({
            "schema": 1,
            "runner": {
                "name": "onedm",
                "device": device,
                "checkpoint": req.get("checkpoint"),
            },
            "results": results,
        })
    )


if __name__ == "__main__":
    main()
