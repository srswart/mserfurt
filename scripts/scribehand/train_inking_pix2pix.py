#!/usr/bin/env python
"""Train the skeleton→ink translation model (hybrid inking, pix2pix-style).

Learns to render a 1px stroke skeleton as realistic Cgm 628 bastarda ink.
Legibility comes from the guided render that produces the skeleton at
inference; this model only supplies ink realism — no text conditioning.

Self-contained: U-Net generator + 70x70 PatchGAN discriminator, L1 + GAN loss
(classic pix2pix). Grayscale in/out. Runs on CUDA (VM) or MPS (smoke test).

Usage (GPU):
    python train_inking_pix2pix.py \\
        --data ~/inking_v1 --out ~/inking_cgm628_v1 \\
        --epochs 60 --batch-size 16 --device cuda

Smoke (local):
    python train_inking_pix2pix.py --data ... --out /tmp/ink_smoke --smoke --device mps
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np

IMG_H = 128
CROP_W = 512


def log(msg: str) -> None:
    print(f"[inking-train {time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def _make_dataset(data_dir: Path, split: str, limit: int | None):
    import torch
    from PIL import Image
    from torch.utils.data import Dataset

    manifest = json.loads((data_dir / "manifest.json").read_text())
    rows = [s for s in manifest["samples"] if s["split"] == split]
    if limit:
        rows = rows[:limit]

    class PairDataset(Dataset):
        def __len__(self):
            return len(rows)

        def __getitem__(self, i):
            sid = rows[i]["id"]
            skel = Image.open(data_dir / "skeleton" / f"{sid}.png").convert("L")
            ink = Image.open(data_dir / "ink" / f"{sid}.png").convert("L")

            # random horizontal crop (train) / left crop (val), pad if narrow
            w = skel.width
            if w < CROP_W:
                pad_s = Image.new("L", (CROP_W, IMG_H), 255)
                pad_i = Image.new("L", (CROP_W, IMG_H), 255)
                pad_s.paste(skel, (0, 0))
                pad_i.paste(ink, (0, 0))
                skel, ink = pad_s, pad_i
            else:
                x0 = random.randint(0, w - CROP_W) if split == "train" else 0
                skel = skel.crop((x0, 0, x0 + CROP_W, IMG_H))
                ink = ink.crop((x0, 0, x0 + CROP_W, IMG_H))

            to_t = lambda im: torch.from_numpy(
                np.asarray(im, dtype=np.float32) / 127.5 - 1.0
            ).unsqueeze(0)
            return to_t(skel), to_t(ink)

    return PairDataset()


# ---------------------------------------------------------------------------
# Models (pix2pix)
# ---------------------------------------------------------------------------

def _build_models(device: str):
    import torch
    import torch.nn as nn

    class Down(nn.Module):
        def __init__(self, cin, cout, norm=True):
            super().__init__()
            layers = [nn.Conv2d(cin, cout, 4, 2, 1, bias=not norm)]
            if norm:
                layers.append(nn.InstanceNorm2d(cout))
            layers.append(nn.LeakyReLU(0.2, inplace=True))
            self.net = nn.Sequential(*layers)

        def forward(self, x):
            return self.net(x)

    class Up(nn.Module):
        def __init__(self, cin, cout, dropout=False):
            super().__init__()
            layers = [
                nn.ConvTranspose2d(cin, cout, 4, 2, 1, bias=False),
                nn.InstanceNorm2d(cout),
                nn.ReLU(inplace=True),
            ]
            if dropout:
                layers.append(nn.Dropout(0.5))
            self.net = nn.Sequential(*layers)

        def forward(self, x, skip):
            x = self.net(x)
            return torch.cat([x, skip], dim=1)

    class UNetGenerator(nn.Module):
        """6-level U-Net; dropout in decoder = stochastic ink texture."""

        def __init__(self, base=64):
            super().__init__()
            self.d1 = Down(1, base, norm=False)          # 64x256
            self.d2 = Down(base, base * 2)               # 32x128
            self.d3 = Down(base * 2, base * 4)           # 16x64
            self.d4 = Down(base * 4, base * 8)           # 8x32
            self.d5 = Down(base * 8, base * 8)           # 4x16
            self.d6 = Down(base * 8, base * 8, norm=False)  # 2x8 bottleneck
            self.u1 = Up(base * 8, base * 8, dropout=True)
            self.u2 = Up(base * 16, base * 8, dropout=True)
            self.u3 = Up(base * 16, base * 4, dropout=True)
            self.u4 = Up(base * 8, base * 2)
            self.u5 = Up(base * 4, base)
            self.final = nn.Sequential(
                nn.ConvTranspose2d(base * 2, 1, 4, 2, 1),
                nn.Tanh(),
            )

        def forward(self, x):
            s1 = self.d1(x)
            s2 = self.d2(s1)
            s3 = self.d3(s2)
            s4 = self.d4(s3)
            s5 = self.d5(s4)
            b = self.d6(s5)
            x = self.u1(b, s5)
            x = self.u2(x, s4)
            x = self.u3(x, s3)
            x = self.u4(x, s2)
            x = self.u5(x, s1)
            return self.final(x)

    class PatchDiscriminator(nn.Module):
        def __init__(self, base=64):
            super().__init__()
            self.net = nn.Sequential(
                Down(2, base, norm=False),
                Down(base, base * 2),
                Down(base * 2, base * 4),
                nn.Conv2d(base * 4, base * 8, 4, 1, 1),
                nn.InstanceNorm2d(base * 8),
                nn.LeakyReLU(0.2, inplace=True),
                nn.Conv2d(base * 8, 1, 4, 1, 1),
            )

        def forward(self, skel, ink):
            return self.net(torch.cat([skel, ink], dim=1))

    return UNetGenerator().to(device), PatchDiscriminator().to(device)


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--l1-weight", type=float, default=100.0)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--num-workers", type=int, default=4)
    ap.add_argument("--log-every", type=int, default=20)
    ap.add_argument("--save-every", type=int, default=5)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader

    device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        log("WARNING: cuda unavailable; falling back")
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    log(f"device={device} data={args.data} epochs={args.epochs} batch={args.batch_size}")

    if args.smoke:
        args.batch_size = 2
    limit = 8 if args.smoke else None
    train_ds = _make_dataset(args.data, "train", limit)
    log(f"train samples: {len(train_ds)}")
    workers = 0 if (args.smoke or device == "mps") else args.num_workers
    loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                        num_workers=workers, drop_last=True)

    gen, disc = _build_models(device)
    opt_g = torch.optim.Adam(gen.parameters(), lr=args.lr, betas=(0.5, 0.999))
    opt_d = torch.optim.Adam(disc.parameters(), lr=args.lr, betas=(0.5, 0.999))
    bce = nn.BCEWithLogitsLoss()
    l1 = nn.L1Loss()

    args.out.mkdir(parents=True, exist_ok=True)
    n_steps_epoch = max(1, len(loader))
    epochs = 1 if args.smoke else args.epochs
    total_steps = epochs * n_steps_epoch
    log(f"steps/epoch={n_steps_epoch} total_steps={total_steps}")

    def save(epoch: int, g_loss: float) -> None:
        torch.save(gen.state_dict(), args.out / "generator.pt")
        (args.out / "training_report.json").write_text(json.dumps({
            "dataset": str(args.data),
            "epochs_completed": epoch + 1,
            "last_g_loss": g_loss,
            "img_h": IMG_H, "crop_w": CROP_W,
            "batch_size": args.batch_size, "lr": args.lr,
            "l1_weight": args.l1_weight,
        }, indent=2) + "\n")

    started = time.monotonic()
    global_step = 0
    for epoch in range(epochs):
        g_running, seen = 0.0, 0
        for skel, ink in loader:
            skel, ink = skel.to(device), ink.to(device)

            # --- discriminator ---
            with torch.no_grad():
                fake = gen(skel)
            d_real = disc(skel, ink)
            d_fake = disc(skel, fake)
            loss_d = 0.5 * (bce(d_real, torch.ones_like(d_real))
                            + bce(d_fake, torch.zeros_like(d_fake)))
            opt_d.zero_grad()
            loss_d.backward()
            opt_d.step()

            # --- generator ---
            fake = gen(skel)
            d_fake = disc(skel, fake)
            loss_g = bce(d_fake, torch.ones_like(d_fake)) + args.l1_weight * l1(fake, ink)
            opt_g.zero_grad()
            loss_g.backward()
            opt_g.step()

            g_running += loss_g.item()
            seen += 1
            global_step += 1
            if global_step % args.log_every == 0 or args.smoke:
                el = time.monotonic() - started
                rate = global_step / el if el > 0 else 0
                eta = (total_steps - global_step) / rate / 60 if rate > 0 else 0
                log(f"epoch {epoch + 1}/{epochs} step {global_step}/{total_steps} "
                    f"g={g_running / seen:.3f} d={loss_d.item():.3f} "
                    f"{rate:.2f} it/s eta={eta:.0f}m")

            if args.smoke and global_step >= 3:
                log("smoke: 3 steps OK — pipeline verified")
                save(epoch, g_running / seen)
                return

        if (epoch + 1) % args.save_every == 0 or epoch == epochs - 1:
            save(epoch, g_running / max(1, seen))
            log(f"epoch {epoch + 1}: checkpoint saved")

    log(f"done — {epochs} epochs in {(time.monotonic() - started) / 60:.1f}m → {args.out}")


if __name__ == "__main__":
    main()
