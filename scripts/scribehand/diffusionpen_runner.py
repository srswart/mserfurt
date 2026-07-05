#!/usr/bin/env python
"""DiffusionPen CommandBackend runner (TD-018).

Run from inside a clone of https://github.com/koninik/DiffusionPen with its
dependencies installed and fine-tuned weights. Invoked by scribesim's
CommandBackend (see scripts/scribehand/README.md for the protocol).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

IMG_SIZE = (64, 256)
LINE_IMG_SIZE = (64, 2048)   # matches train_diffusionpen_finetune.py --img-width
LINE_MAX_TEXT_LEN = 200      # matches training --max-text-len
STYLE_CLASSES = 339
VOCAB_SIZE = 80


def log(msg: str) -> None:
    print(f"[diffusionpen-runner] {msg}", file=sys.stderr, flush=True)


def _prepare_style_image(img, transform):
    from PIL import Image, ImageOps

    from utils.auxilary_functions import centered_PIL, image_resize_PIL  # type: ignore

    img = img.convert("RGB")
    w, h = img.size
    img = img.resize((int(w * 64 / h), 64))
    w, h = img.size
    if w < 256:
        img = ImageOps.pad(img, size=(256, 64), color="white")
    else:
        while w > 256:
            img = image_resize_PIL(img, width=w - 20)
            w, h = img.size
        img = centered_PIL(img, (64, 256), border_value=255.0)
    return transform(img)


def load_pipeline(checkpoint: str, device: str):
    import torch
    import torch.nn as nn
    from diffusers import AutoencoderKL, DDIMScheduler
    from transformers import CanineModel, CanineTokenizer

    ckpt_dir = Path(checkpoint)
    if not ckpt_dir.exists():
        raise FileNotFoundError(f"DiffusionPen checkpoint dir not found: {ckpt_dir}")

    try:
        from feature_extractor import ImageEncoder  # type: ignore
        from unet import UNetModel  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "could not import DiffusionPen modules — run with "
            "cwd=<DiffusionPen clone> (configure workdir in backends.toml). "
            f"underlying error: {exc}"
        ) from exc

    args = SimpleNamespace(
        device=device,
        img_size=IMG_SIZE,
        channels=4,
        emb_dim=320,
        num_heads=4,
        num_res_blocks=1,
        latent=True,
        img_feat=True,
        model_name="diffusionpen",
        stable_dif_path="stable-diffusion-v1-5/stable-diffusion-v1-5",
        interpolation=False,
        mix_rate=None,
    )

    tokenizer = CanineTokenizer.from_pretrained("google/canine-c")
    text_encoder = CanineModel.from_pretrained("google/canine-c").to(device)
    text_encoder.eval()

    unet = UNetModel(
        image_size=IMG_SIZE,
        in_channels=4,
        model_channels=320,
        out_channels=4,
        num_res_blocks=1,
        attention_resolutions=(1, 1),
        channel_mult=(1, 1),
        num_heads=4,
        num_classes=STYLE_CLASSES,
        context_dim=320,
        vocab_size=VOCAB_SIZE,
        text_encoder=text_encoder,
        args=args,
    )
    ckpt = ckpt_dir / "models" / "ckpt.pt"
    state = torch.load(ckpt, map_location=device)
    if any(k.startswith("module.") for k in state):
        state = {k.removeprefix("module."): v for k, v in state.items()}
    # Checkpoint may nest text_encoder weights under text_encoder.module.*
    cleaned: dict = {}
    for k, v in state.items():
        key = k
        if key.startswith("text_encoder.module."):
            key = "text_encoder." + key[len("text_encoder.module."):]
        cleaned[key] = v
    unet.load_state_dict(cleaned, strict=False)
    unet = unet.to(device).eval()

    vae = AutoencoderKL.from_pretrained(args.stable_dif_path, subfolder="vae").to(device)
    vae.requires_grad_(False)
    scheduler = DDIMScheduler.from_pretrained(args.stable_dif_path, subfolder="scheduler")

    style_encoder = ImageEncoder(
        model_name="mobilenetv2_100", num_classes=0, pretrained=True, trainable=False
    )
    style_state = ckpt_dir / "style_models" / "style_encoder.pth"
    if style_state.exists():
        state = torch.load(style_state, map_location=device)
        model_dict = style_encoder.state_dict()
        state = {k: v for k, v in state.items()
                 if k in model_dict and model_dict[k].shape == v.shape}
        model_dict.update(state)
        style_encoder.load_state_dict(model_dict)
    style_encoder = style_encoder.to(device).eval()

    return unet, vae, style_encoder, scheduler, tokenizer, args


def sample_word(
    *,
    unet,
    vae,
    style_encoder,
    scheduler,
    tokenizer,
    args,
    text: str,
    style_images,
    device: str,
    img_size: tuple[int, int] = IMG_SIZE,
    max_text_len: int = 40,
) -> np.ndarray:
    import torch
    import torchvision

    transform = torchvision.transforms.Compose([
        torchvision.transforms.ToTensor(),
        torchvision.transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])

    st_imgs = [_prepare_style_image(im, transform) for im in style_images[:5]]
    while len(st_imgs) < 5:
        st_imgs.append(st_imgs[-1])
    style_stack = torch.stack(st_imgs).to(device)
    style_stack = style_stack.reshape(-1, 3, IMG_SIZE[0], IMG_SIZE[1])
    style_features = style_encoder(style_stack).to(device)

    text_features = tokenizer(
        text, padding="max_length", truncation=True, return_tensors="pt",
        max_length=max_text_len,
    ).to(device)
    labels = torch.zeros(1, dtype=torch.long, device=device)
    n = 1

    x = torch.randn((n, 4, img_size[0] // 8, img_size[1] // 8), device=device)
    scheduler.set_timesteps(50)
    with torch.no_grad():
        for time in scheduler.timesteps:
            t = (torch.ones(n, device=device) * time.item()).long()
            noisy_residual = unet(
                x, t, text_features, labels,
                original_images=style_stack, mix_rate=None,
                style_extractor=style_features,
            )
            x = scheduler.step(noisy_residual, time, x).prev_sample

        latents = x / 0.18215
        image = vae.decode(latents).sample
        image = (image / 2 + 0.5).clamp(0, 1)
        out = image[0].cpu().permute(1, 2, 0).numpy()
    if out.shape[2] == 3:
        out = out.mean(axis=2)
    return out.astype(np.float32)


def style_batch(style_dir: str | None, rng: random.Random, k: int = 5):
    from PIL import Image

    if not style_dir:
        raise ValueError("DiffusionPen requires style_dir (5-shot style anchor)")
    meta = json.loads((Path(style_dir) / "style.json").read_text())
    exemplars = list(meta["exemplars"])
    if len(exemplars) >= k:
        picks = [exemplars[i] for i in rng.sample(range(len(exemplars)), k)]
    else:
        picks = (exemplars * ((k // len(exemplars)) + 1))[:k]
    return [Image.open(Path(style_dir) / p) for p in picks]


def to_ink_mask(sample) -> np.ndarray:
    arr = np.asarray(sample, dtype=np.float32)
    if arr.ndim == 3:
        arr = arr.mean(axis=2)
    if arr.max() <= 1.0:
        arr = arr * 255.0
    mask = np.clip(255.0 - arr, 0, 255)
    mask[mask < 16] = 0
    return mask.astype(np.uint8)


def clean_line_mask(mask: np.ndarray) -> np.ndarray:
    """Remove VAE background-haze artifacts from a line ink mask.

    Real script never fills a column top-to-bottom; columns that are almost
    entirely "ink" are decode artifacts (dark blocks at canvas edges / patch
    seams). Midtone haze below the script threshold is also dropped.
    """
    mask = mask.copy()
    # kill near-solid columns (edge blocks, seam rectangles)
    col_frac = (mask > 96).mean(axis=0)
    mask[:, col_frac > 0.80] = 0
    # drop midtone haze: keep only confident ink
    mask[mask < 64] = 0
    return mask


def crop_line_mask(mask: np.ndarray, pad: int = 4) -> np.ndarray:
    """Trim the white padding _fit_pad added around a generated line strip."""
    cols = np.nonzero(mask.sum(axis=0) > 0)[0]
    if cols.size == 0:
        return mask
    x0 = max(0, int(cols[0]) - pad)
    x1 = min(mask.shape[1], int(cols[-1]) + 1 + pad)
    return mask[:, x0:x1]


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

    sys.path.insert(0, str(Path.cwd()))

    req = json.loads(Path(args.request).read_text())

    import torch
    from PIL import Image

    device = (
        "mps" if torch.backends.mps.is_available()
        else ("cuda" if torch.cuda.is_available() else "cpu")
    )
    log(f"device={device} words={len(req['words'])}")

    unet, vae, style_encoder, scheduler, tokenizer, dp_args = load_pipeline(
        req["checkpoint"], device
    )

    results = []
    for w in req["words"]:
        seed = int(w["seed"])
        torch.manual_seed(seed)
        rng = random.Random(seed)
        styles = style_batch(req.get("style_dir"), rng)

        line_mode = w.get("mode") == "line"
        sample = sample_word(
            unet=unet, vae=vae, style_encoder=style_encoder,
            scheduler=scheduler, tokenizer=tokenizer, args=dp_args,
            text=w["text"], style_images=styles, device=device,
            img_size=LINE_IMG_SIZE if line_mode else IMG_SIZE,
            max_text_len=LINE_MAX_TEXT_LEN if line_mode else 40,
        )
        mask = to_ink_mask(sample)
        if line_mode:
            mask = crop_line_mask(clean_line_mask(mask))
        Image.fromarray(mask, "L").save(w["out"])
        baseline_frac, xheight_frac = estimate_fracs(mask)
        results.append({
            "id": w["id"], "image": w["out"],
            "baseline_frac": baseline_frac, "xheight_frac": xheight_frac,
        })
        log(f"  {'line' if line_mode else 'word'} {w['text']!r} seed={seed} → {w['out']}")

    Path(args.response).write_text(json.dumps({
        "schema": 1,
        "runner": {"name": "diffusionpen", "device": device,
                   "checkpoint": req.get("checkpoint")},
        "results": results,
    }))


if __name__ == "__main__":
    main()
