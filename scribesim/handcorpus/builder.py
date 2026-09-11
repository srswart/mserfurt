"""Build the script-family tier from CATMuS-shaped records.

`build_from_records` is dependency-free and unit-testable; `build_catmus_tier`
wraps it with a streaming HuggingFace `datasets` load (GPU/Mac workstation
path — requires the optional `scribehand` dependency group).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from scribesim.handcorpus.manifest import CorpusManifest, CorpusSample, assign_split

# Default CATMuS Medieval column names (verify against the live dataset on
# first Mac run; override via `field_map` if the schema differs).
_DEFAULT_FIELDS = {
    "image": "im",
    "text": "text",
    "script": "script_type",
    "century": "century",
    "language": "language",
    "writer": "shelfmark",
}


def build_from_records(
    records: Iterable[dict],
    out_dir: Path,
    scripts: tuple[str, ...] = ("cursiva", "bastarda", "hybrida"),
    centuries: tuple[int, ...] = (14, 15, 16),
    languages: tuple[str, ...] | None = None,
    max_lines: int | None = None,
    field_map: dict[str, str] | None = None,
    id_prefix: str = "catmus",
) -> CorpusManifest:
    """Filter records and write images + manifest into *out_dir*.

    Each record must carry a PIL image plus text/script/century metadata
    (column names per *field_map*). Returns the manifest (also saved to
    ``out_dir/manifest.json``).
    """
    fields = {**_DEFAULT_FIELDS, **(field_map or {})}
    out_dir = Path(out_dir)
    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    wanted_scripts = {s.lower() for s in scripts}
    wanted_langs = {l.lower() for l in languages} if languages else None

    manifest = CorpusManifest()
    kept = 0
    for i, rec in enumerate(records):
        script = str(rec.get(fields["script"], "")).lower()
        if script not in wanted_scripts:
            continue
        try:
            century = int(rec.get(fields["century"]))
        except (TypeError, ValueError):
            continue
        if century not in centuries:
            continue
        if wanted_langs is not None:
            lang = str(rec.get(fields["language"], "")).lower()
            if lang not in wanted_langs:
                continue

        text = str(rec.get(fields["text"], "")).strip()
        if not text:
            continue

        sample_id = f"{id_prefix}-{i:06d}"
        rel_image = f"images/{sample_id}.png"
        rec[fields["image"]].save(out_dir / rel_image)

        manifest.samples.append(CorpusSample(
            id=sample_id,
            image=rel_image,
            text=text,
            tier="script_family",
            split=assign_split(sample_id),
            writer=str(rec.get(fields["writer"], "unknown")),
            source={
                "dataset": "CATMuS/medieval",
                "script": rec.get(fields["script"]),
                "century": century,
                "language": rec.get(fields["language"]),
                "shelfmark": rec.get(fields["writer"]),
            },
        ))
        kept += 1
        if max_lines is not None and kept >= max_lines:
            break

    manifest.save(out_dir / "manifest.json")
    return manifest


def build_catmus_tier(
    out_dir: Path,
    scripts: tuple[str, ...] = ("cursiva", "bastarda", "hybrida"),
    centuries: tuple[int, ...] = (14, 15, 16),
    languages: tuple[str, ...] | None = None,
    max_lines: int | None = None,
    dataset_name: str = "CATMuS/medieval",
    split: str = "train",
) -> CorpusManifest:
    """Stream CATMuS Medieval from HuggingFace and build the script-family tier.

    Requires the optional `scribehand` dependency group (``datasets``).
    Intended to run on the Mac workstation; the dev VM path is exercised via
    :func:`build_from_records` with fixture records.
    """
    try:
        from datasets import load_dataset  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - exercised on Mac only
        raise RuntimeError(
            "the `datasets` package is required for CATMuS download — "
            "install the scribehand extra: uv sync --extra scribehand"
        ) from exc

    stream = load_dataset(dataset_name, split=split, streaming=True)
    return build_from_records(
        iter(stream),
        out_dir=out_dir,
        scripts=scripts,
        centuries=centuries,
        languages=languages,
        max_lines=max_lines,
    )
