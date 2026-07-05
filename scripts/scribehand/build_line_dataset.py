#!/usr/bin/env python
"""Build a line-level training dataset from reviewed line transcriptions.

Consumes the reviewed TSV (page<TAB>line<TAB>relpath<TAB>text) plus the line
strips, filters out illegible/merged-multiline strips, and writes a clean
training layout: images/ + labels.tsv (id<TAB>image<TAB>text<TAB>writer<TAB>split).

Usage:
    uv run python scripts/scribehand/build_line_dataset.py \\
        --tsv work/cgm628_anchor/line_transcription.tsv \\
        --images-root work/cgm628_anchor/lines \\
        --out shared/training/scribehand/lines_v1 \\
        --writer cgm628
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import statistics
import unicodedata
from pathlib import Path

from PIL import Image

# Transcription noise that indicates a bad auto-read, not real content.
_JUNK_CHARS = set("[]()|=~…")


def _split_for(sample_id: str, val_frac: float = 0.1) -> str:
    digest = hashlib.sha256(sample_id.encode("utf-8")).digest()
    u = int.from_bytes(digest[:8], "big") / 2**64
    return "val" if u < val_frac else "train"


def _has_junk(text: str) -> bool:
    for ch in text:
        if ch in _JUNK_CHARS:
            return True
        name = unicodedata.name(ch, "")
        if "CYRILLIC" in name:
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", required=True, type=Path)
    ap.add_argument("--images-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--writer", default="cgm628")
    ap.add_argument("--min-chars", type=int, default=8)
    ap.add_argument("--max-chars", type=int, default=200,
                    help="Drop strips longer than this (merged multi-line blobs)")
    ap.add_argument("--min-width", type=int, default=120,
                    help="Drop strips narrower than this (fragments)")
    ap.add_argument("--max-height-ratio", type=float, default=1.5,
                    help="Drop strips taller than this x median height (merged multi-line)")
    ap.add_argument("--val-frac", type=float, default=0.1)
    args = ap.parse_args()

    rows = [l.split("\t") for l in args.tsv.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = args.out
    images_dir = out / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # first pass: median strip height over plausible rows (for multi-line filter)
    heights: list[int] = []
    for r in rows:
        if len(r) < 4 or not r[3].strip() or r[3].strip() == "?":
            continue
        src = args.images_root / r[2]
        if src.is_file():
            with Image.open(src) as im:
                heights.append(im.height)
    median_h = statistics.median(heights) if heights else 0
    max_h = median_h * args.max_height_ratio if median_h else float("inf")

    kept: list[dict] = []
    dropped = {"illegible": 0, "too_short": 0, "too_long": 0, "narrow": 0,
               "multi_line": 0, "junk_chars": 0, "missing": 0}

    for r in rows:
        if len(r) < 4:
            continue
        page, line, relpath, text = r[0], r[1], r[2], r[3].strip()
        if not text or text == "?":
            dropped["illegible"] += 1
            continue
        n = len(text)
        if n < args.min_chars:
            dropped["too_short"] += 1
            continue
        if n > args.max_chars:
            dropped["too_long"] += 1
            continue
        if _has_junk(text):
            dropped["junk_chars"] += 1
            continue
        src = args.images_root / relpath
        if not src.is_file():
            dropped["missing"] += 1
            continue
        with Image.open(src) as im:
            w, h = im.width, im.height
        if w < args.min_width:
            dropped["narrow"] += 1
            continue
        if h > max_h:
            dropped["multi_line"] += 1
            continue
        sample_id = f"{args.writer}-{page}-{int(line):04d}"
        rel_img = f"images/{sample_id}.png"
        shutil.copyfile(src, out / rel_img)
        kept.append({
            "id": sample_id,
            "image": rel_img,
            "text": text,
            "writer": args.writer,
            "split": _split_for(sample_id, args.val_frac),
        })

    labels = [f"{k['id']}\t{k['image']}\t{k['text']}\t{k['writer']}\t{k['split']}" for k in kept]
    (out / "labels.tsv").write_text("\n".join(labels) + ("\n" if labels else ""), encoding="utf-8")

    charset = sorted({c for k in kept for c in k["text"]})
    (out / "charset.txt").write_text("".join(charset) + "\n", encoding="utf-8")

    n_train = sum(1 for k in kept if k["split"] == "train")
    n_val = len(kept) - n_train
    summary = {
        "kept": len(kept),
        "train": n_train,
        "val": n_val,
        "dropped": dropped,
        "writer": args.writer,
        "charset_size": len(charset),
        "charset": "".join(charset),
        "filters": {
            "min_chars": args.min_chars, "max_chars": args.max_chars,
            "min_width": args.min_width, "val_frac": args.val_frac,
        },
    }
    (out / "dataset_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")

    print(f"[line-dataset] kept {len(kept)} (train {n_train} / val {n_val}) → {out}")
    print(f"[line-dataset] dropped: {dropped}")
    print(f"[line-dataset] charset ({len(charset)}): {''.join(charset)!r}")


if __name__ == "__main__":
    main()
