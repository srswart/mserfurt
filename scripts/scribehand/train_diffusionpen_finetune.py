#!/usr/bin/env python
"""Fine-tune DiffusionPen on the Cgm 628 line dataset (TD-018 step 4, for real).

This is the adapter the upstream repo lacks: it replaces the IAM-hardcoded
loader with our line dataset, keeps the style-conditioned path (so the 339-writer
checkpoint loads unchanged and label_emb is bypassed), and adds progress logging
+ checkpointing for long unattended runs.

Runs on CUDA (Nebius AI Cloud) or MPS/CPU (local smoke test only).

Example (GPU):
    python scripts/scribehand/train_diffusionpen_finetune.py \\
        --diffusionpen-root /workspace/DiffusionPen \\
        --data shared/training/scribehand/lines_v1 \\
        --checkpoint /workspace/DiffusionPen/ckpt/iam_style_diffusionpen.pth \\
        --out shared/models/scribehand/weights/diffusionpen_cgm628_v1 \\
        --epochs 120 --batch-size 4 --img-width 1024 --device cuda

Local smoke test (verifies the pipeline, does not train to convergence):
    python scripts/scribehand/train_diffusionpen_finetune.py ... --device mps --smoke
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np


IMG_HEIGHT = 64
STYLE_W = 256          # style reference patch width (native DiffusionPen)
STYLE_CLASSES = 339    # keep to load the IAM checkpoint unchanged
VOCAB_SIZE = 80
N_STYLE = 5            # style refs per sample (DiffusionPen 5-shot)


def log(msg: str) -> None:
    print(f"[dp-finetune {time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def _crop_ink_width(gray: np.ndarray) -> tuple[int, int]:
    """Return [x0, x1) columns spanning the ink, so we drop page margins."""
    col_ink = (gray < 200).sum(axis=0)
    cols = np.nonzero(col_ink > 0)[0]
    if len(cols) == 0:
        return 0, gray.shape[1]
    return int(cols[0]), int(cols[-1]) + 1


def _fit_pad(img, target_h: int, target_w: int):
    """Aspect-preserving fit into (target_h, target_w), padded on white."""
    from PIL import Image

    w, h = img.size
    scale = min(target_h / h, target_w / w)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    resized = img.resize((new_w, new_h), Image.BILINEAR)
    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    canvas.paste(resized, ((target_w - new_w) // 2, (target_h - new_h) // 2))
    return canvas


def _line_canvas(img, target_h: int, target_w: int):
    """Height-normalize to target_h, squeeze over-wide lines, left-align.

    Unlike _fit_pad this never letterboxes vertically: script always fills the
    full canvas height, so the model learns x-height at canvas scale (the fix
    for the stacked-row/letterbox artifacts of the v2 run).
    """
    from PIL import Image

    w, h = img.size
    new_w = max(1, int(round(w * target_h / h)))
    resized = img.resize((new_w, target_h), Image.BILINEAR)
    if new_w > target_w:
        resized = resized.resize((target_w, target_h), Image.BILINEAR)
        new_w = target_w
    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    canvas.paste(resized, (0, 0))
    return canvas


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def _make_dataset_classes():
    """Build the Dataset subclass lazily (torch imported inside)."""
    import torch
    import torchvision
    from PIL import Image
    from torch.utils.data import Dataset

    norm = torchvision.transforms.Compose([
        torchvision.transforms.ToTensor(),
        torchvision.transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])

    class LineDataset(Dataset):
        def __init__(self, data_dir: Path, split: str, img_w: int,
                     style_pool: list, limit: int | None = None):
            self.data_dir = Path(data_dir)
            self.img_w = img_w
            self.style_pool = style_pool
            rows = []
            for raw in (self.data_dir / "labels.tsv").read_text(encoding="utf-8").splitlines():
                if not raw.strip():
                    continue
                sid, image, text, writer, sp = raw.split("\t")
                if sp == split:
                    rows.append({"image": image, "text": text})
            if limit:
                rows = rows[:limit]
            self.rows = rows

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, i):
            r = self.rows[i]
            img = Image.open(self.data_dir / r["image"]).convert("L")
            gray = np.asarray(img)
            x0, x1 = _crop_ink_width(gray)
            img = img.crop((x0, 0, x1, img.height)).convert("RGB")
            canvas = _line_canvas(img, IMG_HEIGHT, self.img_w)
            image_t = norm(canvas)

            picks = random.sample(self.style_pool, min(N_STYLE, len(self.style_pool)))
            while len(picks) < N_STYLE:
                picks.append(random.choice(self.style_pool))
            style_t = torch.stack(picks)  # [N_STYLE, 3, 64, 256]

            return image_t, r["text"], torch.tensor(0, dtype=torch.long), style_t

    return LineDataset, norm


def _build_style_pool(data_dir: Path, norm, n_patches: int = 64) -> list:
    """Sample 64x256 style patches from the line images (writer's own hand).

    Lines are height-normalized to 64 first, then a random 256-wide window is
    cropped — so patches show script at canvas scale (a few words), matching
    what the runner's style prep produces from word exemplars at inference.
    """
    from PIL import Image

    rows = []
    for raw in (data_dir / "labels.tsv").read_text(encoding="utf-8").splitlines():
        if raw.strip():
            rows.append(raw.split("\t")[1])
    pool = []
    rng = random.Random(1457)
    tries = 0
    while len(pool) < n_patches and tries < n_patches * 5:
        tries += 1
        rel = rng.choice(rows)
        img = Image.open(data_dir / rel).convert("L")
        gray = np.asarray(img)
        x0, x1 = _crop_ink_width(gray)
        crop = img.crop((x0, 0, x1, img.height)).convert("RGB")
        w, h = crop.size
        new_w = max(1, int(round(w * IMG_HEIGHT / h)))
        line64 = crop.resize((new_w, IMG_HEIGHT), Image.BILINEAR)
        if new_w <= STYLE_W:
            patch = Image.new("RGB", (STYLE_W, IMG_HEIGHT), (255, 255, 255))
            patch.paste(line64, ((STYLE_W - new_w) // 2, 0))
        else:
            wx = rng.randint(0, new_w - STYLE_W)
            patch = line64.crop((wx, 0, wx + STYLE_W, IMG_HEIGHT))
        pool.append(norm(patch))
    if not pool:
        raise SystemExit("could not build a style pool from the dataset")
    return pool


# ---------------------------------------------------------------------------
# Model loading (mirrors the proven inference runner)
# ---------------------------------------------------------------------------

def load_models(checkpoint: str, stable_dif_path: str, device: str, dp_root: Path):
    import torch
    import torch.nn as nn
    from diffusers import AutoencoderKL, DDPMScheduler
    from transformers import CanineModel, CanineTokenizer
    from types import SimpleNamespace

    from feature_extractor import ImageEncoder  # type: ignore
    from unet import UNetModel  # type: ignore

    args = SimpleNamespace(
        device=device, img_size=(IMG_HEIGHT, STYLE_W), channels=4, emb_dim=320,
        num_heads=4, num_res_blocks=1, latent=True, img_feat=True,
        model_name="diffusionpen", stable_dif_path=stable_dif_path,
        interpolation=False, mix_rate=None,
    )

    tokenizer = CanineTokenizer.from_pretrained("google/canine-c")
    text_encoder = CanineModel.from_pretrained("google/canine-c").to(device)

    unet = UNetModel(
        image_size=args.img_size, in_channels=4, model_channels=320,
        out_channels=4, num_res_blocks=1, attention_resolutions=(1, 1),
        channel_mult=(1, 1), num_heads=4, num_classes=STYLE_CLASSES,
        context_dim=320, vocab_size=VOCAB_SIZE, text_encoder=text_encoder, args=args,
    )
    ckpt = Path(checkpoint)
    state = torch.load(ckpt, map_location="cpu")
    if any(k.startswith("module.") for k in state):
        state = {k.removeprefix("module."): v for k, v in state.items()}
    cleaned = {}
    for k, v in state.items():
        key = k
        if key.startswith("text_encoder.module."):
            key = "text_encoder." + key[len("text_encoder.module."):]
        cleaned[key] = v
    missing, unexpected = unet.load_state_dict(cleaned, strict=False)
    log(f"unet loaded (missing={len(missing)} unexpected={len(unexpected)})")
    unet = unet.to(device)

    vae = AutoencoderKL.from_pretrained(stable_dif_path, subfolder="vae").to(device)
    vae.requires_grad_(False)
    vae.eval()

    scheduler = DDPMScheduler.from_pretrained(stable_dif_path, subfolder="scheduler")

    style_encoder = ImageEncoder(model_name="mobilenetv2_100", num_classes=0,
                                 pretrained=True, trainable=False)
    candidates = [
        ckpt.parent / "style_models" / "style_encoder.pth",
        dp_root / "style_models" / "style_encoder.pth",
        dp_root / "ckpt" / "diffusionpen_bastarda_v1" / "style_models" / "style_encoder.pth",
    ]
    src = next((c for c in candidates if c.exists()), None)
    if src is not None:
        sd = torch.load(src, map_location="cpu")
        md = style_encoder.state_dict()
        sd = {k: v for k, v in sd.items() if k in md and md[k].shape == v.shape}
        md.update(sd)
        style_encoder.load_state_dict(md)
        log(f"style encoder loaded from {src}")
    else:
        log("WARNING: no style_encoder weights found; using pretrained mobilenet")
    style_encoder = style_encoder.to(device).eval()

    return unet, vae, scheduler, style_encoder, tokenizer


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diffusionpen-root", required=True, type=Path,
                    help="Path to the DiffusionPen clone (for imports)")
    ap.add_argument("--data", required=True, type=Path, help="lines_v1 dataset dir")
    ap.add_argument("--checkpoint", required=True, type=Path,
                    help="Pretrained DiffusionPen weights (iam_style_diffusionpen.pth)")
    ap.add_argument("--out", required=True, type=Path, help="Output checkpoint dir")
    ap.add_argument("--stable-dif-path", default="stable-diffusion-v1-5/stable-diffusion-v1-5")
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--img-width", type=int, default=1024)
    ap.add_argument("--max-text-len", type=int, default=200)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--num-workers", type=int, default=4)
    ap.add_argument("--log-every", type=int, default=20, help="steps between loss logs")
    ap.add_argument("--save-every", type=int, default=10, help="epochs between checkpoints")
    ap.add_argument("--smoke", action="store_true",
                    help="Run a few steps on a handful of samples then exit")
    args = ap.parse_args()

    sys.path.insert(0, str(args.diffusionpen_root.resolve()))

    import torch
    from torch.utils.data import DataLoader

    device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        log("WARNING: cuda requested but unavailable; falling back")
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    log(f"device={device} data={args.data} epochs={args.epochs} "
        f"batch={args.batch_size} img_w={args.img_width}")

    LineDataset, norm = _make_dataset_classes()
    style_pool = _build_style_pool(args.data, norm)
    log(f"style pool: {len(style_pool)} patches")

    limit = 6 if args.smoke else None
    train_ds = LineDataset(args.data, "train", args.img_width, style_pool, limit=limit)
    log(f"train samples: {len(train_ds)}")
    workers = 0 if (args.smoke or device == "mps") else args.num_workers
    loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                        num_workers=workers, drop_last=False)

    unet, vae, scheduler, style_encoder, tokenizer = load_models(
        str(args.checkpoint), args.stable_dif_path, device,
        args.diffusionpen_root.resolve())

    optim = torch.optim.AdamW(unet.parameters(), lr=args.lr)
    mse = torch.nn.MSELoss()
    n_steps_epoch = max(1, len(loader))
    total_steps = args.epochs * n_steps_epoch
    log(f"steps/epoch={n_steps_epoch} total_steps={total_steps}")

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "models").mkdir(exist_ok=True)
    started = time.monotonic()
    global_step = 0
    unet.train()

    epochs = 1 if args.smoke else args.epochs
    for epoch in range(epochs):
        running, seen = 0.0, 0
        for images, transcr, s_id, style_images in loader:
            images = images.to(device)
            s_id = s_id.to(device)
            style_images = style_images.to(device)

            with torch.no_grad():
                latents = vae.encode(images.to(torch.float32)).latent_dist.sample() * 0.18215
                reshaped = style_images.reshape(-1, 3, IMG_HEIGHT, STYLE_W)
                style_features = style_encoder(reshaped)

            text = tokenizer(list(transcr), padding="max_length", truncation=True,
                             return_tensors="pt", max_length=args.max_text_len).to(device)

            noise = torch.randn_like(latents)
            t = torch.randint(0, scheduler.config.num_train_timesteps,
                              (latents.shape[0],), device=device).long()
            noisy = scheduler.add_noise(latents, noise, t)

            pred = unet(noisy, timesteps=t, context=text, y=s_id,
                        style_extractor=style_features)
            loss = mse(noise, pred)

            optim.zero_grad()
            loss.backward()
            optim.step()

            running += loss.item(); seen += 1; global_step += 1
            if global_step % args.log_every == 0 or args.smoke:
                el = time.monotonic() - started
                rate = global_step / el if el > 0 else 0
                eta = (total_steps - global_step) / rate / 60 if rate > 0 else 0
                log(f"epoch {epoch + 1}/{epochs} step {global_step}/{total_steps} "
                    f"loss={running / seen:.4f} {rate:.2f} it/s eta={eta:.0f}m")

            if args.smoke and global_step >= 3:
                log("smoke: 3 steps OK — pipeline verified")
                _save(unet, args, epoch, running / max(1, seen))
                return

        if (epoch + 1) % args.save_every == 0 or epoch == epochs - 1:
            _save(unet, args, epoch, running / max(1, seen))
            log(f"epoch {epoch + 1}: checkpoint saved (loss {running / max(1, seen):.4f})")

    total_min = (time.monotonic() - started) / 60
    log(f"done — {epochs} epochs in {total_min:.1f}m → {args.out}")


def _save(unet, args, epoch: int, loss: float) -> None:
    import torch

    torch.save(unet.state_dict(), args.out / "models" / "ckpt.pt")
    (args.out / "training_report.json").write_text(json.dumps({
        "base": str(args.checkpoint),
        "dataset": str(args.data),
        "epochs_completed": epoch + 1,
        "last_loss": loss,
        "img_width": args.img_width,
        "batch_size": args.batch_size,
        "lr": args.lr,
    }, indent=2) + "\n")
    # style encoder is frozen; copy alongside so the runner finds it
    style_dst = args.out / "style_models"
    style_dst.mkdir(exist_ok=True)
    ckpt = Path(args.checkpoint)
    candidates = [
        ckpt.parent / "style_models" / "style_encoder.pth",
        ckpt.parent.parent / "style_models" / "style_encoder.pth",
        args.diffusionpen_root / "style_models" / "style_encoder.pth",
    ]
    src = next((c for c in candidates if c.exists()), None)
    if src is not None and not (style_dst / "style_encoder.pth").exists():
        import shutil
        shutil.copyfile(src, style_dst / "style_encoder.pth")


if __name__ == "__main__":
    main()
