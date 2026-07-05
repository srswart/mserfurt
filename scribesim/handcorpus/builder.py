"""Build the script-family tier from CATMuS-shaped records.

`build_from_records` is dependency-free and unit-testable; `build_catmus_tier`
wraps it with a streaming HuggingFace `datasets` load (GPU/Mac workstation
path — requires the optional `scribehand` dependency group).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Iterable

from scribesim.handcorpus.manifest import CorpusManifest, CorpusSample, assign_split

_PROGRESS_EVERY_KEPT = 500
_PROGRESS_EVERY_SEC = 30.0


def _emit_build_progress(
    *,
    kept: int,
    scanned: int,
    started: float,
    last_kept: int,
    last_emit: float,
    stream_total: int | None,
    max_lines: int | None,
) -> None:
    """Print corpus-build progress to stderr (visible in logs and tee)."""
    now = time.monotonic()
    elapsed = now - started
    dt = now - last_emit
    dk = kept - last_kept
    rate_per_min = (dk / dt * 60.0) if dt > 0 else 0.0
    yield_pct = (100.0 * kept / scanned) if scanned else 0.0
    parts = [
        f"kept={kept}",
        f"scanned={scanned}",
        f"yield={yield_pct:.1f}%",
        f"rate={rate_per_min:.0f}/min",
        f"elapsed={elapsed / 60:.1f}m",
    ]
    if max_lines is not None:
        parts.append(f"target={max_lines}")
    elif stream_total is not None:
        parts.append(f"est_total~{int(stream_total * kept / scanned) if scanned else '?'}")
        parts.append(f"scan={100.0 * scanned / stream_total:.1f}%")
    print(f"[corpus] {' '.join(parts)}", file=sys.stderr, flush=True)

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
    stream_total: int | None = None,
    progress_every_kept: int = _PROGRESS_EVERY_KEPT,
    progress_every_sec: float = _PROGRESS_EVERY_SEC,
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
    started = time.monotonic()
    last_emit = started
    last_kept = 0
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
        scanned = i + 1
        now = time.monotonic()
        if (
            kept == 1
            or kept % progress_every_kept == 0
            or (now - last_emit) >= progress_every_sec
        ):
            _emit_build_progress(
                kept=kept,
                scanned=scanned,
                started=started,
                last_kept=last_kept,
                last_emit=last_emit,
                stream_total=stream_total,
                max_lines=max_lines,
            )
            last_emit = now
            last_kept = kept
        if max_lines is not None and kept >= max_lines:
            break

    if kept:
        _emit_build_progress(
            kept=kept,
            scanned=i + 1,
            started=started,
            last_kept=last_kept,
            last_emit=last_emit,
            stream_total=stream_total,
            max_lines=max_lines,
        )
        print(f"[corpus] done kept={kept} scanned={i + 1}", file=sys.stderr, flush=True)

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

    try:
        from datasets import load_dataset_builder  # type: ignore[import-untyped]
    except ImportError:
        load_dataset_builder = None  # type: ignore[misc, assignment]

    stream_total: int | None = None
    if load_dataset_builder is not None:
        try:
            split_info = load_dataset_builder(dataset_name).info.splits.get(split)
            if split_info is not None:
                stream_total = split_info.num_examples
        except Exception:
            stream_total = None

    try:
        from huggingface_hub import get_token  # type: ignore[import-untyped]
    except ImportError:
        get_token = lambda: None  # type: ignore[misc, assignment]

    if get_token():
        print("[corpus] HuggingFace: authenticated", file=sys.stderr, flush=True)
    else:
        print(
            "[corpus] HuggingFace: unauthenticated — run `huggingface-cli login` "
            "or set HF_TOKEN for faster downloads",
            file=sys.stderr,
            flush=True,
        )

    stream = load_dataset(dataset_name, split=split, streaming=True)
    if stream_total is not None:
        print(f"[corpus] streaming {dataset_name} ({split}, {stream_total:,} records)…",
              file=sys.stderr, flush=True)
    return build_from_records(
        iter(stream),
        out_dir=out_dir,
        scripts=scripts,
        centuries=centuries,
        languages=languages,
        max_lines=max_lines,
        stream_total=stream_total,
    )
