"""Export the corpus into training layouts for the upstream HTG repos.

The ``generic`` layout (images/ + labels.tsv + charset.txt) is the contract
the Mac-side runner and training glue consume; One-DM / DiffusionPen adapters
start from the same layout (see scripts/scribehand/README.md).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from scribesim.handcorpus.manifest import CorpusManifest

FORMATS = ("generic",)


def export_training_format(
    manifest_path: Path,
    out_dir: Path,
    fmt: str = "generic",
    tiers: tuple[str, ...] = ("script_family", "anchor"),
) -> Path:
    """Write a training export from a saved corpus manifest.

    Layout (generic):
        images/<id>.png
        labels.tsv   — id, image path, text, writer, split
        charset.txt  — training charset, one line
    """
    if fmt not in FORMATS:
        raise ValueError(f"unknown export format {fmt!r} — expected one of {FORMATS}")

    manifest_path = Path(manifest_path)
    corpus_root = manifest_path.parent
    manifest = CorpusManifest.load(manifest_path)

    out_dir = Path(out_dir)
    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    rows: list[str] = []
    for s in manifest.samples:
        if s.tier not in tiers:
            continue
        src = corpus_root / s.image
        dst_rel = f"images/{s.id}{src.suffix}"
        shutil.copyfile(src, out_dir / dst_rel)
        rows.append("\t".join([s.id, dst_rel, s.text, s.writer, s.split]))

    (out_dir / "labels.tsv").write_text("\n".join(rows) + "\n")
    (out_dir / "charset.txt").write_text(manifest.training_charset() + "\n")
    return out_dir
