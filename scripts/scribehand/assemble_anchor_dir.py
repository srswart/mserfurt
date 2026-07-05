#!/usr/bin/env python3
"""Assemble anchors/ for scribehand corpus ingest (step_2_anchor_tier).

Consumes one or more word-crop directories with a parallel transcription file
(one word per line, same sort order as *.png). Writes:

    <out>/labels.tsv
    <out>/images/<id>.png

Usage:
  uv run python scripts/scribehand/assemble_anchor_dir.py \\
    --out anchors \\
    --source reference/fullres_words:reference/transcription.txt:bsb_anchor \\
    --source reference/47v_words:reference/47v_transcription.txt:bsb_anchor
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def _parse_source(raw: str) -> tuple[Path, Path, str]:
    parts = raw.split(":")
    if len(parts) < 2:
        raise ValueError(f"expected words_dir:transcription.txt[:writer], got {raw!r}")
    words_dir = Path(parts[0])
    transcription = Path(parts[1])
    writer = parts[2] if len(parts) > 2 else "anchor"
    return words_dir, transcription, writer


def assemble_anchor_dir(
    sources: list[tuple[Path, Path, str]],
    out_dir: Path,
    *,
    skip_unknown: bool = True,
) -> dict:
    out_dir = Path(out_dir)
    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    rows: list[str] = []
    kept = 0
    skipped = 0

    for words_dir, transcription_path, writer in sources:
        words_dir = Path(words_dir)
        lines = Path(transcription_path).read_text().splitlines()
        crops = sorted(words_dir.glob("*.png"), key=lambda p: (
            [int(x) for x in __import__("re").findall(r"\d+", p.stem)] or [0]
        ))
        if len(crops) != len(lines):
            print(
                f"[assemble] warning: {words_dir.name} crops={len(crops)} "
                f"lines={len(lines)} — pairing min length",
                file=sys.stderr,
            )
        tag = words_dir.name.replace("/", "_")
        for i, crop in enumerate(crops):
            if i >= len(lines):
                skipped += 1
                continue
            text = lines[i].strip().lstrip("~")
            if not text or (skip_unknown and text == "?"):
                skipped += 1
                continue
            dest_name = f"{tag}_{crop.stem}.png"
            rel = f"images/{dest_name}"
            shutil.copyfile(crop, out_dir / rel)
            rows.append(f"{rel}\t{text}\t{writer}")
            kept += 1

    (out_dir / "labels.tsv").write_text("\n".join(rows) + ("\n" if rows else ""))
    summary = {"kept": kept, "skipped": skipped, "sources": len(sources)}
    (out_dir / "assemble_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def freeze_style_anchor(
    anchor_dir: Path,
    style_dir: Path,
    *,
    max_exemplars: int = 8,
    shelfmark: str = "BSB anchor hand (assembled bootstrap)",
) -> list[Path]:
    """Pick short-word crops for style_anchor_v1 from assembled anchor images."""
    labels = (anchor_dir / "labels.tsv").read_text().strip().splitlines()
    pairs: list[tuple[str, str, int]] = []
    for raw in labels:
        rel, text, _writer = raw.split("\t", 2)
        pairs.append((rel, text, len(text)))

    # Prefer short common words with clean transcriptions.
    pairs.sort(key=lambda t: (t[2], t[1]))
    seen_text: set[str] = set()
    chosen: list[tuple[str, str]] = []
    for rel, text, _ in pairs:
        if text in seen_text:
            continue
        seen_text.add(text)
        chosen.append((rel, text))
        if len(chosen) >= max_exemplars:
            break

    style_dir = Path(style_dir)
    style_dir.mkdir(parents=True, exist_ok=True)
    exemplar_names: list[str] = []
    for i, (rel, text) in enumerate(chosen):
        src = anchor_dir / rel
        name = f"ex{i + 1}_{text[:12].replace(' ', '_')}.png"
        shutil.copyfile(src, style_dir / name)
        exemplar_names.append(name)

    meta = {
        "id": "anchor_v1",
        "description": "Bootstrap style anchor from assembled reviewed word crops",
        "exemplars": exemplar_names,
        "source": {"shelfmark": shelfmark, "assembled_from": str(anchor_dir)},
    }
    (style_dir / "style.json").write_text(json.dumps(meta, indent=2) + "\n")
    return [style_dir / n for n in exemplar_names]


def populate_anchor_words(style_dir: Path, anchor_words_dir: Path) -> int:
    """Copy style exemplars into anchor_words/ for bench-neural style gate."""
    anchor_words_dir = Path(anchor_words_dir)
    anchor_words_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in sorted(Path(style_dir).glob("ex*.png")):
        shutil.copyfile(src, anchor_words_dir / src.name)
        n += 1
    return n


def main() -> None:
    p = argparse.ArgumentParser(description="Assemble scribehand anchor tier directory")
    p.add_argument("--out", required=True, type=Path, help="Output anchors/ directory")
    p.add_argument(
        "--source",
        action="append",
        required=True,
        help="words_dir:transcription.txt[:writer] (repeatable)",
    )
    p.add_argument(
        "--style-dir",
        default="shared/models/scribehand/style_anchor_v1",
        type=Path,
    )
    p.add_argument("--anchor-words-dir", default="anchor_words", type=Path)
    p.add_argument("--include-unknown", action="store_true")
    args = p.parse_args()

    sources = [_parse_source(s) for s in args.source]
    summary = assemble_anchor_dir(
        sources, args.out, skip_unknown=not args.include_unknown,
    )
    print(f"[assemble] kept={summary['kept']} skipped={summary['skipped']} → {args.out}")

    if summary["kept"] == 0:
        sys.exit(1)

    ex = freeze_style_anchor(args.out, args.style_dir)
    print(f"[assemble] style anchor: {len(ex)} exemplars → {args.style_dir}")

    n = populate_anchor_words(args.style_dir, args.anchor_words_dir)
    print(f"[assemble] anchor_words: {n} PNGs → {args.anchor_words_dir}")


if __name__ == "__main__":
    main()
