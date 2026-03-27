"""Coverage-ledger generation for reviewed exemplar work."""

from __future__ import annotations

import json
import re
import tomllib
from collections import defaultdict
from pathlib import Path
from typing import Any

DEFAULT_CORPUS_MANIFEST_PATH = Path("shared/training/handsim/active_review_exemplars_v1/manifest.toml")
DEFAULT_COVERAGE_LEDGER_OUTPUT_PATH = Path("shared/training/handsim/reviewed_annotations/coverage_ledger_v1")

_CROP_CANVAS_RE = re.compile(r"^.+?_\d{3}_(?P<canvas>.+)_l\d+_w\d+_c\d+\.png$")


def _sanitize_fragment(label: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(label))
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_") or "item"


def _load_toml(path: Path | str) -> dict[str, Any]:
    return tomllib.loads(Path(path).read_text())


def _selection_manifest_path(corpus_manifest: dict[str, Any], corpus_manifest_path: Path) -> Path:
    raw = corpus_manifest.get("selection_manifest_path")
    if not raw:
        raise ValueError("corpus manifest missing selection_manifest_path")
    path = Path(str(raw))
    if path.is_absolute():
        return path
    if path.exists():
        return path
    return (corpus_manifest_path.parent / path).resolve()


def _reviewed_manifest_path(path: Path | str | None) -> Path | None:
    if path is None:
        return None
    resolved = Path(path)
    return resolved if resolved.exists() else None


def _build_canvas_to_manuscript(selection_manifest: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    ambiguous: set[str] = set()
    for folio in selection_manifest.get("folios", []):
        slug = _sanitize_fragment(str(folio.get("canvas_label", "")))
        manuscript = str(folio.get("source_manuscript_label", "unknown"))
        if slug in mapping and mapping[slug] != manuscript:
            ambiguous.add(slug)
        else:
            mapping[slug] = manuscript
    for slug in ambiguous:
        mapping[slug] = f"ambiguous:{slug}"
    return mapping


def _manuscript_from_crop_path(path: str, canvas_to_manuscript: dict[str, str]) -> str:
    match = _CROP_CANVAS_RE.match(Path(path).name)
    if not match:
        return "unknown"
    return canvas_to_manuscript.get(match.group("canvas"), f"unknown:{match.group('canvas')}")


def _path_parent_to_manuscript(selection_manifest: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for folio in selection_manifest.get("folios", []):
        local_path = Path(str(folio.get("local_path", "")))
        if local_path.parent.name:
            mapping[local_path.parent.name] = str(folio.get("source_manuscript_label", "unknown"))
    return mapping


def _manuscript_from_source_path(path: str, parent_to_manuscript: dict[str, str]) -> str:
    parts = Path(path).parts
    if "folios" in parts:
        idx = parts.index("folios")
        if idx + 1 < len(parts):
            return parent_to_manuscript.get(parts[idx + 1], parts[idx + 1])
    return Path(path).parent.name or "unknown"


def _parse_reviewed_entries(reviewed_manifest: dict[str, Any] | None) -> dict[tuple[str, str], list[dict[str, Any]]]:
    if not reviewed_manifest:
        return {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for entry in reviewed_manifest.get("entries", []):
        if not bool(entry.get("catalog_included", True)):
            continue
        kind = str(entry.get("kind", ""))
        symbol = str(entry.get("symbol", ""))
        if not kind or not symbol:
            continue
        grouped[(kind, symbol)].append(entry)
    return grouped


def _append_count(bucket: dict[str, Any], *, tier: str, manuscript: str, count: int) -> None:
    bucket[f"{tier}_count"] += count
    manuscripts: dict[str, int] = bucket["by_manuscript"][tier]
    manuscripts[manuscript] = manuscripts.get(manuscript, 0) + count


def _build_entries(
    corpus_manifest: dict[str, Any],
    selection_manifest: dict[str, Any],
    reviewed_manifest: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    canvas_to_manuscript = _build_canvas_to_manuscript(selection_manifest)
    parent_to_manuscript = _path_parent_to_manuscript(selection_manifest)
    reviewed_entries = _parse_reviewed_entries(reviewed_manifest)
    corpus_entries = {
        (str(entry.get("kind", "")), str(entry.get("symbol", ""))): entry
        for entry in corpus_manifest.get("entries", [])
        if str(entry.get("kind", "")) in {"glyph", "join"} and str(entry.get("symbol", ""))
    }
    required_inventory = (
        [("glyph", str(symbol)) for symbol in corpus_manifest.get("required_symbols", [])]
        + [("join", str(symbol)) for symbol in corpus_manifest.get("priority_joins", [])]
    )
    if not required_inventory:
        required_inventory = list(corpus_entries)

    entries: list[dict[str, Any]] = []

    totals = {
        "glyph": {"required": 0, "missing_reviewed": 0, "missing_promoted": 0},
        "join": {"required": 0, "missing_reviewed": 0, "missing_promoted": 0},
    }

    for kind, symbol in required_inventory:
        entry = corpus_entries.get((kind, symbol), {})

        record = {
            "kind": kind,
            "symbol": symbol,
            "auto_admitted_count": 0,
            "quarantined_count": 0,
            "rejected_count": 0,
            "promoted_count": 0,
            "reviewed_count": 0,
            "coverage_promoted": bool(entry.get("coverage_promoted", False)),
            "missing_promoted": 0,
            "missing_reviewed": 0,
            "by_manuscript": {
                "auto_admitted": {},
                "quarantined": {},
                "rejected": {},
                "promoted": {},
                "reviewed": {},
            },
        }

        for tier in ("auto_admitted", "quarantined", "rejected"):
            paths = [str(path) for path in entry.get(f"{tier}_paths", [])]
            for path in paths:
                manuscript = _manuscript_from_crop_path(path, canvas_to_manuscript)
                _append_count(record, tier=tier, manuscript=manuscript, count=1)

        promoted_lookup = {
            (str(item.get("kind", "")), str(item.get("symbol", ""))): item
            for item in (reviewed_manifest or {}).get("_promoted_entries", [])
        }
        promoted_entry = promoted_lookup.get((kind, symbol))
        if promoted_entry is not None:
            for path in promoted_entry.get("promoted_exemplar_source_paths", []):
                manuscript = _manuscript_from_source_path(str(path), parent_to_manuscript)
                _append_count(record, tier="promoted", manuscript=manuscript, count=1)

        for reviewed_entry in reviewed_entries.get((kind, symbol), []):
            source_paths = [str(path) for path in reviewed_entry.get("reviewed_source_paths", [])]
            if not source_paths and reviewed_entry.get("source_path"):
                source_paths = [str(reviewed_entry["source_path"])]
            if not source_paths:
                _append_count(record, tier="reviewed", manuscript="unknown", count=1)
            else:
                for path in source_paths:
                    manuscript = _manuscript_from_source_path(path, parent_to_manuscript)
                    _append_count(record, tier="reviewed", manuscript=manuscript, count=1)

        record["missing_promoted"] = int(record["promoted_count"] == 0)
        record["missing_reviewed"] = int(record["reviewed_count"] == 0)
        totals[kind]["required"] += 1
        totals[kind]["missing_promoted"] += record["missing_promoted"]
        totals[kind]["missing_reviewed"] += record["missing_reviewed"]
        entries.append(record)

    entries.sort(key=lambda item: (item["kind"], item["symbol"]))
    return entries, totals


def _attach_promoted_entries(reviewed_manifest: dict[str, Any] | None, promoted_manifest: dict[str, Any]) -> dict[str, Any]:
    payload = dict(reviewed_manifest or {})
    payload["_promoted_entries"] = promoted_manifest.get("entries", [])
    return payload


def _ledger_summary(entries: list[dict[str, Any]], totals: dict[str, Any]) -> dict[str, Any]:
    glyph_entries = [entry for entry in entries if entry["kind"] == "glyph"]
    join_entries = [entry for entry in entries if entry["kind"] == "join"]
    glyph_missing_auto = [entry["symbol"] for entry in glyph_entries if entry["auto_admitted_count"] == 0]
    join_missing_auto = [entry["symbol"] for entry in join_entries if entry["auto_admitted_count"] == 0]
    return {
        "required_glyph_count": totals["glyph"]["required"],
        "required_join_count": totals["join"]["required"],
        "glyph_auto_admitted_coverage": 1.0 - (len(glyph_missing_auto) / max(totals["glyph"]["required"], 1)),
        "join_auto_admitted_coverage": 1.0 - (len(join_missing_auto) / max(totals["join"]["required"], 1)),
        "glyph_promoted_coverage": 1.0 - (totals["glyph"]["missing_promoted"] / max(totals["glyph"]["required"], 1)),
        "join_promoted_coverage": 1.0 - (totals["join"]["missing_promoted"] / max(totals["join"]["required"], 1)),
        "glyph_reviewed_coverage": 1.0 - (totals["glyph"]["missing_reviewed"] / max(totals["glyph"]["required"], 1)),
        "join_reviewed_coverage": 1.0 - (totals["join"]["missing_reviewed"] / max(totals["join"]["required"], 1)),
        "glyph_missing_auto_admitted": glyph_missing_auto,
        "join_missing_auto_admitted": join_missing_auto,
        "glyph_missing_reviewed": [entry["symbol"] for entry in glyph_entries if entry["missing_reviewed"]],
        "join_missing_reviewed": [entry["symbol"] for entry in join_entries if entry["missing_reviewed"]],
        "glyph_missing_promoted": [entry["symbol"] for entry in glyph_entries if entry["missing_promoted"]],
        "join_missing_promoted": [entry["symbol"] for entry in join_entries if entry["missing_promoted"]],
        "coverage_promoted_glyphs": [entry["symbol"] for entry in glyph_entries if entry["coverage_promoted"]],
        "coverage_promoted_joins": [entry["symbol"] for entry in join_entries if entry["coverage_promoted"]],
    }


def _write_ledger_bundle(
    *,
    output_root: Path,
    corpus_manifest_path: Path,
    promoted_manifest_path: Path,
    reviewed_manifest_path: Path | None,
    entries: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    ledger_json_path = output_root / "coverage_ledger.json"
    ledger_md_path = output_root / "coverage_ledger.md"
    ledger_manifest_path = output_root / "coverage_ledger_manifest.toml"

    payload = {
        "stage_id": "reviewed-coverage-ledger",
        "corpus_manifest_path": corpus_manifest_path.as_posix(),
        "promoted_manifest_path": promoted_manifest_path.as_posix(),
        "reviewed_manifest_path": reviewed_manifest_path.as_posix() if reviewed_manifest_path else "",
        "summary": summary,
        "entries": entries,
    }
    ledger_json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    lines = [
        "# TD-014 Reviewed Coverage Ledger",
        "",
        f"- Corpus manifest: `{corpus_manifest_path.as_posix()}`",
        f"- Promoted manifest: `{promoted_manifest_path.as_posix()}`",
        f"- Reviewed manifest: `{reviewed_manifest_path.as_posix() if reviewed_manifest_path else 'none'}`",
        f"- Glyph promoted coverage: `{summary['glyph_promoted_coverage']:.4f}`",
        f"- Join promoted coverage: `{summary['join_promoted_coverage']:.4f}`",
        f"- Glyph reviewed coverage: `{summary['glyph_reviewed_coverage']:.4f}`",
        f"- Join reviewed coverage: `{summary['join_reviewed_coverage']:.4f}`",
        f"- Missing reviewed glyphs: {', '.join(f'`{s}`' for s in summary['glyph_missing_reviewed']) or 'none'}",
        f"- Missing reviewed joins: {', '.join(f'`{s}`' for s in summary['join_missing_reviewed']) or 'none'}",
        "",
        "## Glyph Counts",
    ]
    for entry in entries:
        if entry["kind"] != "glyph":
            continue
        lines.append(
            f"- `{entry['symbol']}`: auto={entry['auto_admitted_count']} "
            f"promoted={entry['promoted_count']} reviewed={entry['reviewed_count']} "
            f"quarantined={entry['quarantined_count']} rejected={entry['rejected_count']}"
        )
    lines.extend(["", "## Join Counts"])
    for entry in entries:
        if entry["kind"] != "join":
            continue
        lines.append(
            f"- `{entry['symbol']}`: auto={entry['auto_admitted_count']} "
            f"promoted={entry['promoted_count']} reviewed={entry['reviewed_count']} "
            f"quarantined={entry['quarantined_count']} rejected={entry['rejected_count']}"
        )
    ledger_md_path.write_text("\n".join(lines) + "\n")

    manifest_lines = [
        "# TD-014 reviewed coverage ledger manifest",
        "schema_version = 1",
        'stage_id = "reviewed-coverage-ledger"',
        f'corpus_manifest_path = "{corpus_manifest_path.as_posix()}"',
        f'promoted_manifest_path = "{promoted_manifest_path.as_posix()}"',
        f'reviewed_manifest_path = "{reviewed_manifest_path.as_posix() if reviewed_manifest_path else ""}"',
        f'ledger_json_path = "{ledger_json_path.as_posix()}"',
        f'ledger_md_path = "{ledger_md_path.as_posix()}"',
        f"glyph_promoted_coverage = {summary['glyph_promoted_coverage']:.6f}",
        f"join_promoted_coverage = {summary['join_promoted_coverage']:.6f}",
        f"glyph_reviewed_coverage = {summary['glyph_reviewed_coverage']:.6f}",
        f"join_reviewed_coverage = {summary['join_reviewed_coverage']:.6f}",
        "",
    ]
    for entry in entries:
        manifest_lines.append("[[entries]]")
        manifest_lines.append(f'kind = "{entry["kind"]}"')
        manifest_lines.append(f'symbol = "{entry["symbol"]}"')
        manifest_lines.append(f'auto_admitted_count = {entry["auto_admitted_count"]}')
        manifest_lines.append(f'quarantined_count = {entry["quarantined_count"]}')
        manifest_lines.append(f'rejected_count = {entry["rejected_count"]}')
        manifest_lines.append(f'promoted_count = {entry["promoted_count"]}')
        manifest_lines.append(f'reviewed_count = {entry["reviewed_count"]}')
        manifest_lines.append(f'missing_promoted = {"true" if entry["missing_promoted"] else "false"}')
        manifest_lines.append(f'missing_reviewed = {"true" if entry["missing_reviewed"] else "false"}')
        manifest_lines.append(f'coverage_promoted = {"true" if entry["coverage_promoted"] else "false"}')
        for tier in ("auto_admitted", "quarantined", "rejected", "promoted", "reviewed"):
            manifest_lines.append(f"[entries.by_manuscript.{tier}]")
            for manuscript, count in sorted(entry["by_manuscript"][tier].items()):
                manifest_lines.append(f'{json.dumps(manuscript, ensure_ascii=False)} = {int(count)}')
        manifest_lines.append("")
    ledger_manifest_path.write_text("\n".join(manifest_lines) + "\n")

    return {
        "ledger_json_path": ledger_json_path,
        "ledger_md_path": ledger_md_path,
        "ledger_manifest_path": ledger_manifest_path,
    }


def build_reviewed_coverage_ledger(
    corpus_manifest_path: Path | str = DEFAULT_CORPUS_MANIFEST_PATH,
    *,
    output_root: Path | str = DEFAULT_COVERAGE_LEDGER_OUTPUT_PATH,
    reviewed_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    corpus_manifest_path = Path(corpus_manifest_path)
    corpus_manifest = _load_toml(corpus_manifest_path)
    promoted_manifest = _load_toml(corpus_manifest.get("promoted_manifest_path", corpus_manifest_path.parent / "promoted_manifest.toml"))
    selection_manifest = _load_toml(_selection_manifest_path(corpus_manifest, corpus_manifest_path))
    reviewed_path = _reviewed_manifest_path(reviewed_manifest_path)
    reviewed_manifest = _load_toml(reviewed_path) if reviewed_path else None

    entries, totals = _build_entries(
        corpus_manifest,
        selection_manifest,
        _attach_promoted_entries(reviewed_manifest, promoted_manifest),
    )
    summary = _ledger_summary(entries, totals)
    bundle_paths = _write_ledger_bundle(
        output_root=Path(output_root),
        corpus_manifest_path=corpus_manifest_path,
        promoted_manifest_path=Path(corpus_manifest.get("promoted_manifest_path", "")),
        reviewed_manifest_path=reviewed_path,
        entries=entries,
        summary=summary,
    )
    return {
        "summary": summary,
        "entries": entries,
        "output_root": Path(output_root),
        **bundle_paths,
    }
