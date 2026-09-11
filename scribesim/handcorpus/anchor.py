"""Anchor-tier ingestion — reviewed crops from the BSB anchor hand.

Consumes a directory of reviewed word/line crops plus a ``labels.tsv``
(``filename<TAB>text<TAB>writer``) as produced by converting the TD-014
reviewed-exemplar freeze exports (or assembled by hand in the workbench).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from scribesim.handcorpus.manifest import CorpusManifest, CorpusSample, assign_split


def ingest_anchor_dir(
    src_dir: Path,
    out_dir: Path,
    id_prefix: str = "anchor",
    manifest: CorpusManifest | None = None,
) -> CorpusManifest:
    """Copy reviewed crops into the corpus and append anchor-tier samples.

    If *manifest* is provided, samples are appended to it (merging tiers into
    one corpus); otherwise a fresh manifest is created. The manifest is saved
    to ``out_dir/manifest.json``.
    """
    src_dir = Path(src_dir)
    out_dir = Path(out_dir)
    labels_path = src_dir / "labels.tsv"
    if not labels_path.exists():
        raise FileNotFoundError(f"labels.tsv not found in {src_dir}")

    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    manifest = manifest or CorpusManifest()
    existing = len([s for s in manifest.samples if s.tier == "anchor"])

    for li, raw in enumerate(labels_path.read_text().strip().splitlines()):
        parts = raw.split("\t")
        if len(parts) < 2:
            raise ValueError(f"labels.tsv line {li + 1}: expected filename<TAB>text[<TAB>writer]")
        filename, text = parts[0], parts[1]
        writer = parts[2] if len(parts) > 2 else "anchor"

        src_image = src_dir / filename
        if not src_image.exists():
            raise FileNotFoundError(f"labels.tsv line {li + 1}: image not found: {src_image}")

        sample_id = f"{id_prefix}-{existing + li:05d}"
        rel_image = f"images/{sample_id}{src_image.suffix}"
        shutil.copyfile(src_image, out_dir / rel_image)

        manifest.samples.append(CorpusSample(
            id=sample_id,
            image=rel_image,
            text=text,
            tier="anchor",
            split=assign_split(sample_id),
            writer=writer,
            source={"dataset": "reviewed_anchor", "src": str(src_image)},
        ))

    manifest.save(out_dir / "manifest.json")
    return manifest
