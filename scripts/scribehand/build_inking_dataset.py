#!/usr/bin/env python
"""Build (skeleton → ink) training pairs for the hybrid inking model.

For every Cgm 628 line strip: binarize the ink, skeletonize it to a 1px
centerline, and save (skeleton, ink) as a training pair. No transcription
labels are needed — even strips whose auto-transcription failed are usable.

The same skeletonize operator is applied at inference to the guided render,
so the conditioning domain matches training exactly.

Usage:
    uv run python scripts/scribehand/build_inking_dataset.py \\
        --lines work/cgm628_anchor/lines \\
        --out shared/training/scribehand/inking_v1 \\
        --sheet diagnostics/inking_v1_pairs.png
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np
from PIL import Image

TARGET_H = 128          # strip height (2x the DiffusionPen canvas — more glyph detail)
MIN_INK_FRAC = 0.005    # drop nearly blank strips
MAX_INK_FRAC = 0.60     # drop stain/blob strips
# skeleton px / ink px: bastarda strokes are ~8px wide at h=128, so the
# healthy ratio is ~0.10-0.17 (measured); blobs sit well below 0.05.
MIN_SKEL_FRAC = 0.06
MAX_SKEL_FRAC = 0.75    # too high = hairline noise, nothing to learn


def log(msg: str) -> None:
    print(f"[inking-dataset {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def binarize_ink(gray: np.ndarray) -> np.ndarray:
    """Sauvola-thresholded ink mask (True = ink) for parchment scans."""
    from skimage.filters import threshold_sauvola

    thresh = threshold_sauvola(gray, window_size=25)
    mask = gray < thresh
    # drop tiny specks
    from scipy.ndimage import label

    labeled, n = label(mask)
    if n:
        sizes = np.bincount(labeled.ravel())
        sizes[0] = 0
        keep = sizes >= 6
        mask = keep[labeled]
    return mask


def skeleton_of(mask: np.ndarray) -> np.ndarray:
    """1px-centerline skeleton of an ink mask (True = skeleton)."""
    from skimage.morphology import skeletonize

    return skeletonize(mask)


def _height_normalize(img: Image.Image, target_h: int) -> Image.Image:
    w, h = img.size
    new_w = max(1, int(round(w * target_h / h)))
    return img.resize((new_w, target_h), Image.BILINEAR)


def process_strip(path: Path, target_h: int) -> tuple[np.ndarray, np.ndarray, dict] | None:
    """Return (skeleton_u8, ink_u8, stats) or None if the strip fails QC.

    Both outputs are height-normalized grayscale, ink-on-white (0 = ink).
    Skeletonization runs at normalized scale — identical to inference.
    """
    img = Image.open(path).convert("L")
    if img.height < 12 or img.width < 60:
        return None
    img = _height_normalize(img, target_h)
    gray = np.asarray(img)

    mask = binarize_ink(gray)
    ink_frac = float(mask.mean())
    if not (MIN_INK_FRAC <= ink_frac <= MAX_INK_FRAC):
        return None

    # reject speckle strips: most ink must sit in stroke-sized components
    from scipy.ndimage import label as _label

    labeled, n = _label(mask)
    if n:
        sizes = np.bincount(labeled.ravel())
        sizes[0] = 0
        solid = sizes[sizes >= 40].sum() / max(1, int(mask.sum()))
        if solid < 0.5:
            return None

    skel = skeleton_of(mask)
    skel_frac = float(skel.sum()) / max(1, int(mask.sum()))
    if not (MIN_SKEL_FRAC <= skel_frac <= MAX_SKEL_FRAC):
        return None

    # ink-on-white renderings
    ink_u8 = np.where(mask, gray, 255).astype(np.uint8)
    skel_u8 = np.where(skel, 0, 255).astype(np.uint8)
    stats = {"ink_frac": round(ink_frac, 4), "skel_frac": round(skel_frac, 4),
             "width": int(gray.shape[1])}
    return skel_u8, ink_u8, stats


def _split_for(sample_id: str, val_frac: float) -> str:
    digest = hashlib.sha256(sample_id.encode("utf-8")).digest()
    u = int.from_bytes(digest[:8], "big") / 2**64
    return "val" if u < val_frac else "train"


def write_pair_sheet(pairs: list[tuple[Path, Path]], out_path: Path,
                     n: int = 12, seed: int = 628) -> None:
    """Contact sheet: alternating skeleton/ink rows for visual QC."""
    rng = random.Random(seed)
    picks = rng.sample(pairs, min(n, len(pairs)))
    row_w = 1600
    rows = []
    for skel_p, ink_p in picks:
        for p in (skel_p, ink_p):
            img = Image.open(p).convert("L")
            w = min(img.width, row_w)
            rows.append(img.crop((0, 0, w, img.height)))
        rows.append(Image.new("L", (row_w, 8), 128))   # separator
    sheet_h = sum(r.height for r in rows)
    sheet = Image.new("L", (row_w, sheet_h), 255)
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True, type=Path,
                    help="Root dir with <page>/line_XXXX.png strips")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--target-h", type=int, default=TARGET_H)
    ap.add_argument("--val-frac", type=float, default=0.05)
    ap.add_argument("--sheet", type=Path, default=None,
                    help="Optional visual QC contact sheet path")
    args = ap.parse_args()

    strips = sorted(args.lines.glob("*/line_*.png"))
    if not strips:
        raise SystemExit(f"no line strips under {args.lines}")
    log(f"found {len(strips)} strips")

    skel_dir = args.out / "skeleton"
    ink_dir = args.out / "ink"
    skel_dir.mkdir(parents=True, exist_ok=True)
    ink_dir.mkdir(parents=True, exist_ok=True)

    kept: list[dict] = []
    pair_paths: list[tuple[Path, Path]] = []
    dropped = {"qc": 0, "error": 0}
    started = time.monotonic()

    for i, p in enumerate(strips, 1):
        sample_id = f"{p.parent.name}-{p.stem}"
        try:
            result = process_strip(p, args.target_h)
        except Exception as exc:
            log(f"  ERROR {sample_id}: {exc}")
            dropped["error"] += 1
            continue
        if result is None:
            dropped["qc"] += 1
            continue
        skel_u8, ink_u8, stats = result
        skel_p = skel_dir / f"{sample_id}.png"
        ink_p = ink_dir / f"{sample_id}.png"
        Image.fromarray(skel_u8, "L").save(skel_p)
        Image.fromarray(ink_u8, "L").save(ink_p)
        pair_paths.append((skel_p, ink_p))
        kept.append({"id": sample_id, "split": _split_for(sample_id, args.val_frac),
                     **stats})
        if i % 250 == 0 or i == len(strips):
            el = time.monotonic() - started
            rate = i / el
            eta = (len(strips) - i) / rate
            log(f"  {i}/{len(strips)} kept={len(kept)} dropped={sum(dropped.values())} "
                f"({rate:.0f}/s eta {eta:.0f}s)")

    manifest = {
        "schema": 1,
        "source_lines": str(args.lines),
        "target_h": args.target_h,
        "kept": len(kept),
        "dropped": dropped,
        "train": sum(1 for k in kept if k["split"] == "train"),
        "val": sum(1 for k in kept if k["split"] == "val"),
        "qc_bands": {"ink_frac": [MIN_INK_FRAC, MAX_INK_FRAC],
                     "skel_frac": [MIN_SKEL_FRAC, MAX_SKEL_FRAC]},
        "samples": kept,
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    log(f"kept {len(kept)} pairs (train {manifest['train']} / val {manifest['val']}) "
        f"dropped {dropped} → {args.out}")

    if args.sheet and pair_paths:
        write_pair_sheet(pair_paths, args.sheet)
        log(f"pair sheet → {args.sheet}")


if __name__ == "__main__":
    main()
