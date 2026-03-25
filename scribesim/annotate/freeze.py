"""Reviewed exemplar freeze for TD-014."""

from __future__ import annotations

import json
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from scribesim.evofit import build_evofit_targets
from scribesim.pathguide.review import write_snapshot_panel

DEFAULT_REVIEWED_MANIFEST_PATH = Path("shared/training/handsim/reviewed_annotations/workbench_v1/reviewed_manifest.toml")
DEFAULT_REVIEWED_EXEMPLAR_OUTPUT_ROOT = Path("shared/training/handsim/reviewed_annotations/reviewed_exemplars_v1")
REVIEWED_EXEMPLAR_TIER = "reviewed_exemplars"


def _load_toml(path: Path | str) -> dict[str, Any]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def _toml_string(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _quoted_list(values: list[str]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"


def _snapshot_stem(symbol: str) -> str:
    return symbol.replace("->", "_to_").replace(" ", "_space_")


@dataclass(frozen=True)
class ReviewedRecord:
    kind: str
    symbol: str
    quality: str
    source_path: str
    source_manuscript_label: str
    canvas_label: str
    source_object_id: str
    bounds_px: dict[str, int]
    image_width_px: int
    image_height_px: int
    reviewed_source_paths: tuple[str, ...]
    created_at: str
    updated_at: str
    raw_path: str
    cleaned_path: str | None
    cleanup_stroke_count: int

    @property
    def path(self) -> str:
        return self.cleaned_path or self.raw_path


def _normalize_bounds(bounds: dict[str, Any]) -> dict[str, int]:
    return {
        "x": int(bounds["x"]),
        "y": int(bounds["y"]),
        "width": int(bounds["width"]),
        "height": int(bounds["height"]),
    }


def _crop_filename(entry: dict[str, Any], index: int) -> str:
    canvas = "".join(ch if ch.isalnum() else "_" for ch in str(entry.get("canvas_label", ""))).strip("_") or "item"
    return f"{_snapshot_stem(str(entry['symbol']))}_{index:03d}_{canvas}.png"


def _apply_cleanup_strokes(crop: Image.Image, cleanup_strokes: list[dict[str, Any]]) -> Image.Image:
    if not cleanup_strokes:
        return crop.copy()

    mask = Image.new("L", crop.size, color=255)
    draw = ImageDraw.Draw(mask)
    for stroke in cleanup_strokes:
        points = [(float(point["x"]), float(point["y"])) for point in stroke.get("points", [])]
        if not points:
            continue
        width = max(1, int(stroke.get("size_px", 1)))
        fill = 0 if stroke.get("mode") == "erase" else 255
        if len(points) == 1:
            x, y = points[0]
            radius = width / 2
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)
        else:
            draw.line(points, fill=fill, width=width, joint="curve")

    foreground = crop.convert("RGBA")
    foreground.putalpha(mask)
    background = Image.new("RGBA", crop.size, (255, 255, 255, 255))
    return Image.alpha_composite(background, foreground).convert("RGB")


def _crop_reviewed_entry(entry: dict[str, Any], raw_destination: Path, cleaned_destination: Path | None = None) -> ReviewedRecord:
    source_path = Path(str(entry["source_path"])).resolve()
    bounds = _normalize_bounds(dict(entry["bounds_px"]))
    cleanup_strokes = list(entry.get("cleanup_strokes", []))
    with Image.open(source_path) as image:
        image = image.convert("RGB")
        crop = image.crop(
            (
                bounds["x"],
                bounds["y"],
                bounds["x"] + bounds["width"],
                bounds["y"] + bounds["height"],
            )
        )
        raw_destination.parent.mkdir(parents=True, exist_ok=True)
        crop.save(raw_destination)
        cleaned_path = None
        if cleanup_strokes and cleaned_destination is not None:
            cleaned_crop = _apply_cleanup_strokes(crop, cleanup_strokes)
            cleaned_destination.parent.mkdir(parents=True, exist_ok=True)
            cleaned_crop.save(cleaned_destination)
            cleaned_path = cleaned_destination.as_posix()

    return ReviewedRecord(
        kind=str(entry["kind"]),
        symbol=str(entry["symbol"]),
        quality=str(entry.get("quality", "usable")),
        source_path=source_path.as_posix(),
        source_manuscript_label=str(entry.get("source_manuscript_label", "unknown")),
        canvas_label=str(entry.get("canvas_label", "")),
        source_object_id=str(entry.get("source_object_id", "")),
        bounds_px=bounds,
        image_width_px=int(entry.get("image_width_px", 0)),
        image_height_px=int(entry.get("image_height_px", 0)),
        reviewed_source_paths=tuple(str(path) for path in entry.get("reviewed_source_paths", []) or [source_path.as_posix()]),
        created_at=str(entry.get("created_at", "")),
        updated_at=str(entry.get("updated_at", "")),
        raw_path=raw_destination.as_posix(),
        cleaned_path=cleaned_path,
        cleanup_stroke_count=len(cleanup_strokes),
    )


def _group_by_symbol(records: list[ReviewedRecord]) -> dict[str, list[ReviewedRecord]]:
    grouped: dict[str, list[ReviewedRecord]] = defaultdict(list)
    for record in sorted(records, key=lambda item: (item.kind, item.symbol, item.path)):
        grouped[record.symbol].append(record)
    return dict(grouped)


def _format_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# TD-014 Reviewed Exemplar Freeze",
        "",
        f"- Dataset: `{summary['dataset_id']}`",
        f"- Reviewed manifest: `{summary['reviewed_manifest_path']}`",
        f"- Reviewed glyph count: `{summary['reviewed_glyph_count']}`",
        f"- Reviewed join count: `{summary['reviewed_join_count']}`",
        f"- Distinct glyph symbols: `{summary['distinct_glyph_symbol_count']}`",
        f"- Distinct join symbols: `{summary['distinct_join_symbol_count']}`",
        f"- Reviewed cleaned glyph count: `{summary['reviewed_cleaned_glyph_count']}`",
        f"- Reviewed cleaned join count: `{summary['reviewed_cleaned_join_count']}`",
        f"- Raw glyph panel: `{summary['raw_glyph_panel_path']}`" if summary.get("raw_glyph_panel_path") else "- Raw glyph panel: `none`",
        f"- Cleaned glyph panel: `{summary['cleaned_glyph_panel_path']}`" if summary.get("cleaned_glyph_panel_path") else "- Cleaned glyph panel: `none`",
        f"- Raw join panel: `{summary['raw_join_panel_path']}`" if summary.get("raw_join_panel_path") else "- Raw join panel: `none`",
        f"- Cleaned join panel: `{summary['cleaned_join_panel_path']}`" if summary.get("cleaned_join_panel_path") else "- Cleaned join panel: `none`",
        f"- Downstream smoke test: `{'PASS' if summary['downstream_smoke_passed'] else 'FAIL'}`",
    ]
    return "\n".join(lines) + "\n"


def _format_dataset_summary(summary: dict[str, Any]) -> str:
    lines = [
        'stage_id = "reviewed_exemplar_freeze"',
        f'dataset_id = {_toml_string(summary["dataset_id"])}',
        f"reviewed_glyph_count = {summary['reviewed_glyph_count']}",
        f"reviewed_join_count = {summary['reviewed_join_count']}",
        f"reviewed_cleaned_glyph_count = {summary['reviewed_cleaned_glyph_count']}",
        f"reviewed_cleaned_join_count = {summary['reviewed_cleaned_join_count']}",
        f"distinct_glyph_symbol_count = {summary['distinct_glyph_symbol_count']}",
        f"distinct_join_symbol_count = {summary['distinct_join_symbol_count']}",
        f'downstream_smoke_passed = {"true" if summary["downstream_smoke_passed"] else "false"}',
        f'reviewed_manifest_path = {_toml_string(summary["reviewed_manifest_path"])}',
        f'raw_glyph_panel_path = {_toml_string(summary.get("raw_glyph_panel_path", ""))}',
        f'cleaned_glyph_panel_path = {_toml_string(summary.get("cleaned_glyph_panel_path", ""))}',
        f'raw_join_panel_path = {_toml_string(summary.get("raw_join_panel_path", ""))}',
        f'cleaned_join_panel_path = {_toml_string(summary.get("cleaned_join_panel_path", ""))}',
    ]
    return "\n".join(lines) + "\n"


def _format_reviewed_freeze_manifest(
    *,
    output_root: Path,
    reviewed_manifest_path: Path,
    glyphs: dict[str, list[ReviewedRecord]],
    joins: dict[str, list[ReviewedRecord]],
    required_symbols: list[str],
    priority_joins: list[str],
) -> str:
    lines = [
        "# TD-014 reviewed exemplar manifest",
        "schema_version = 1",
        'manifest_kind = "reviewed_exemplars"',
        f'dataset_id = {_toml_string(output_root.name)}',
        f'parent_reviewed_manifest_path = {_toml_string(reviewed_manifest_path.as_posix())}',
        f"required_symbols = {_quoted_list(required_symbols)}",
        f"priority_joins = {_quoted_list(priority_joins)}",
        "",
    ]
    for kind, grouped in (("glyph", glyphs), ("join", joins)):
        for symbol in sorted(grouped):
            records = grouped[symbol]
            lines.extend(
                [
                    "[[entries]]",
                    f'kind = "{kind}"',
                    f'symbol = {_toml_string(symbol)}',
                    f"reviewed_exemplar_count = {len(records)}",
                    f"reviewed_exemplar_paths = {_quoted_list([record.path for record in records])}",
                    f"reviewed_raw_exemplar_paths = {_quoted_list([record.raw_path for record in records])}",
                    f"reviewed_cleaned_exemplar_paths = {_quoted_list([record.cleaned_path or '' for record in records])}",
                    f"reviewed_exemplar_source_paths = {_quoted_list([record.source_path for record in records])}",
                    f"reviewed_exemplar_source_manuscripts = {_quoted_list([record.source_manuscript_label for record in records])}",
                    f"reviewed_exemplar_source_object_ids = {_quoted_list([record.source_object_id for record in records])}",
                    f"reviewed_quality_tiers = {_quoted_list([record.quality for record in records])}",
                    f"reviewed_cleanup_stroke_counts = [{', '.join(str(record.cleanup_stroke_count) for record in records)}]",
                    # Compatibility fields so current evofit can consume the reviewed freeze without fallback.
                    f"promoted_exemplar_count = {len(records)}",
                    f"promoted_exemplar_paths = {_quoted_list([record.path for record in records])}",
                    f"promoted_exemplar_source_paths = {_quoted_list([record.source_path for record in records])}",
                    "",
                ]
            )
    return "\n".join(lines)


def _format_reviewed_source_manifest(reviewed_manifest: dict[str, Any], reviewed_manifest_path: Path) -> str:
    payload = dict(reviewed_manifest)
    payload["entry_count"] = len(payload.get("entries", []))
    lines = [
        "# TD-014 reviewed annotation source manifest",
        f"schema_version = {int(payload.get('schema_version', 1))}",
        f"manifest_kind = {_toml_string(str(payload.get('manifest_kind', 'reviewed_annotations')))}",
        f"dataset_id = {_toml_string(str(payload.get('dataset_id', reviewed_manifest_path.parent.name)))}",
        f"coverage_ledger_path = {_toml_string(str(payload.get('coverage_ledger_path', '')))}",
        f"selection_manifest_path = {_toml_string(str(payload.get('selection_manifest_path', '')))}",
        f"created_by = {_toml_string(str(payload.get('created_by', 'annotate-workbench')))}",
        f"created_at = {_toml_string(str(payload.get('created_at', '')))}",
        f"updated_at = {_toml_string(str(payload.get('updated_at', '')))}",
        f"entry_count = {int(payload.get('entry_count', 0))}",
        "",
    ]
    for entry in payload.get("entries", []):
        bounds = _normalize_bounds(dict(entry["bounds_px"]))
        lines.extend(
            [
                "[[entries]]",
                f'id = {_toml_string(str(entry["id"]))}',
                f'kind = {_toml_string(str(entry["kind"]))}',
                f'symbol = {_toml_string(str(entry["symbol"]))}',
                f'quality = {_toml_string(str(entry.get("quality", "usable")))}',
                f'notes = {_toml_string(str(entry.get("notes", "")))}',
                f'source_path = {_toml_string(str(entry["source_path"]))}',
                f'source_manuscript_label = {_toml_string(str(entry.get("source_manuscript_label", "")))}',
                f'canvas_label = {_toml_string(str(entry.get("canvas_label", "")))}',
                f'source_object_id = {_toml_string(str(entry.get("source_object_id", "")))}',
                f"image_width_px = {int(entry.get('image_width_px', 0))}",
                f"image_height_px = {int(entry.get('image_height_px', 0))}",
                "bounds_px = { "
                f"x = {bounds['x']}, y = {bounds['y']}, width = {bounds['width']}, height = {bounds['height']} "
                "}",
                f"reviewed_source_paths = {_quoted_list([str(path) for path in entry.get('reviewed_source_paths', [])])}",
                f'created_at = {_toml_string(str(entry.get("created_at", "")))}',
                f'updated_at = {_toml_string(str(entry.get("updated_at", "")))}',
            ]
        )
        for stroke in entry.get("cleanup_strokes", []):
            points = stroke.get("points", [])
            point_list = ", ".join(
                "{ " + f"x = {int(point.get('x', 0))}, y = {int(point.get('y', 0))}" + " }"
                for point in points
            )
            lines.extend(
                [
                    "[[entries.cleanup_strokes]]",
                    f"mode = {_toml_string(str(stroke.get('mode', 'erase')))}",
                    f"size_px = {int(stroke.get('size_px', 1))}",
                    f"points = [{point_list}]",
                ]
            )
        lines.append("")
    return "\n".join(lines)


def freeze_reviewed_exemplars(
    reviewed_manifest_path: Path | str = DEFAULT_REVIEWED_MANIFEST_PATH,
    *,
    output_root: Path | str = DEFAULT_REVIEWED_EXEMPLAR_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Freeze reviewed annotations into a trusted reviewed exemplar dataset."""

    reviewed_manifest_path = Path(reviewed_manifest_path).resolve()
    reviewed_manifest = _load_toml(reviewed_manifest_path)
    entries = list(reviewed_manifest.get("entries", []))
    if not entries:
        raise ValueError("reviewed manifest contains no entries")

    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    glyph_records: list[ReviewedRecord] = []
    join_records: list[ReviewedRecord] = []
    seen_payloads: set[str] = set()

    for index, entry in enumerate(
        sorted(
            entries,
            key=lambda item: (
                str(item.get("kind", "")),
                str(item.get("symbol", "")),
                str(item.get("source_path", "")),
                int(item.get("bounds_px", {}).get("x", 0)),
                int(item.get("bounds_px", {}).get("y", 0)),
                str(item.get("id", "")),
            ),
        )
    ):
        fingerprint = json.dumps(
            {
                "kind": entry.get("kind"),
                "symbol": entry.get("symbol"),
                "source_path": entry.get("source_path"),
                "bounds_px": entry.get("bounds_px"),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        if fingerprint in seen_payloads:
            continue
        seen_payloads.add(fingerprint)
        kind = str(entry["kind"])
        symbol = str(entry["symbol"])
        stem = _snapshot_stem(symbol)
        filename = _crop_filename(entry, index)
        raw_destination = output_root / f"{kind}s" / REVIEWED_EXEMPLAR_TIER / "raw" / stem / filename
        cleaned_destination = output_root / f"{kind}s" / REVIEWED_EXEMPLAR_TIER / "cleaned" / stem / filename
        record = _crop_reviewed_entry(entry, raw_destination, cleaned_destination)
        if kind == "glyph":
            glyph_records.append(record)
        elif kind == "join":
            join_records.append(record)
        else:
            raise ValueError(f"unsupported reviewed entry kind: {kind}")

    glyphs = _group_by_symbol(glyph_records)
    joins = _group_by_symbol(join_records)

    raw_glyph_panel_path = None
    raw_glyph_images = [Path(record.raw_path) for symbol in sorted(glyphs) for record in glyphs[symbol]]
    if raw_glyph_images:
        raw_glyph_panel_path = write_snapshot_panel(raw_glyph_images, output_root / "reviewed_raw_glyph_panel.png", columns=5)

    cleaned_glyph_panel_path = None
    cleaned_glyph_images = [Path(record.cleaned_path) for symbol in sorted(glyphs) for record in glyphs[symbol] if record.cleaned_path]
    if cleaned_glyph_images:
        cleaned_glyph_panel_path = write_snapshot_panel(
            cleaned_glyph_images, output_root / "reviewed_cleaned_glyph_panel.png", columns=5
        )

    raw_join_panel_path = None
    raw_join_images = [Path(record.raw_path) for symbol in sorted(joins) for record in joins[symbol]]
    if raw_join_images:
        raw_join_panel_path = write_snapshot_panel(raw_join_images, output_root / "reviewed_raw_join_panel.png", columns=4)

    cleaned_join_panel_path = None
    cleaned_join_images = [Path(record.cleaned_path) for symbol in sorted(joins) for record in joins[symbol] if record.cleaned_path]
    if cleaned_join_images:
        cleaned_join_panel_path = write_snapshot_panel(
            cleaned_join_images, output_root / "reviewed_cleaned_join_panel.png", columns=4
        )

    required_symbols = list(reviewed_manifest.get("required_symbols", []))
    priority_joins = list(reviewed_manifest.get("priority_joins", []))
    if not required_symbols or not priority_joins:
        coverage_ledger_path = reviewed_manifest.get("coverage_ledger_path")
        if coverage_ledger_path and Path(str(coverage_ledger_path)).exists():
            ledger = json.loads(Path(str(coverage_ledger_path)).read_text(encoding="utf-8"))
            if not required_symbols:
                required_symbols = [entry["symbol"] for entry in ledger.get("entries", []) if entry.get("kind") == "glyph"]
            if not priority_joins:
                priority_joins = [entry["symbol"] for entry in ledger.get("entries", []) if entry.get("kind") == "join"]

    summary = {
        "dataset_id": output_root.name,
        "reviewed_manifest_path": reviewed_manifest_path.as_posix(),
        "reviewed_glyph_count": len(glyph_records),
        "reviewed_join_count": len(join_records),
        "reviewed_cleaned_glyph_count": sum(1 for record in glyph_records if record.cleaned_path),
        "reviewed_cleaned_join_count": sum(1 for record in join_records if record.cleaned_path),
        "distinct_glyph_symbol_count": len(glyphs),
        "distinct_join_symbol_count": len(joins),
        "raw_glyph_panel_path": raw_glyph_panel_path.as_posix() if raw_glyph_panel_path else "",
        "cleaned_glyph_panel_path": cleaned_glyph_panel_path.as_posix() if cleaned_glyph_panel_path else "",
        "raw_join_panel_path": raw_join_panel_path.as_posix() if raw_join_panel_path else "",
        "cleaned_join_panel_path": cleaned_join_panel_path.as_posix() if cleaned_join_panel_path else "",
    }

    manifest_path = output_root / "reviewed_exemplar_manifest.toml"
    reviewed_source_manifest_copy = output_root / "reviewed_annotation_source_manifest.toml"
    summary_json_path = output_root / "summary.json"
    summary_md_path = output_root / "summary.md"
    dataset_summary_path = output_root / "dataset_summary.toml"
    smoke_report_path = output_root / "downstream_smoke_test.json"

    manifest_path.write_text(
        _format_reviewed_freeze_manifest(
            output_root=output_root,
            reviewed_manifest_path=reviewed_manifest_path,
            glyphs=glyphs,
            joins=joins,
            required_symbols=required_symbols,
            priority_joins=priority_joins,
        ),
        encoding="utf-8",
    )
    reviewed_source_manifest_copy.write_text(
        _format_reviewed_source_manifest(reviewed_manifest, reviewed_manifest_path),
        encoding="utf-8",
    )

    smoke_targets = build_evofit_targets(manifest_path, allowed_tiers=(), max_candidates_per_symbol=3)
    expected_target_count = len(glyphs) + len(joins)
    smoke_passed = len(smoke_targets) == expected_target_count and all(
        tiers == [REVIEWED_EXEMPLAR_TIER] or tiers == ["promoted_exemplars"]
        for tiers in [list(target.candidate_tiers) for target in smoke_targets]
    )
    smoke_payload = {
        "manifest_path": manifest_path.as_posix(),
        "target_count": len(smoke_targets),
        "expected_target_count": expected_target_count,
        "symbols": [target.symbol for target in smoke_targets],
        "tiers": [list(target.candidate_tiers) for target in smoke_targets],
        "passed": smoke_passed,
    }
    smoke_report_path.write_text(json.dumps(smoke_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary["downstream_smoke_passed"] = bool(smoke_payload["passed"])
    summary_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary_md_path.write_text(_format_summary(summary), encoding="utf-8")
    dataset_summary_path.write_text(_format_dataset_summary(summary), encoding="utf-8")

    return {
        "summary": summary,
        "summary_json_path": summary_json_path,
        "summary_md_path": summary_md_path,
        "dataset_summary_path": dataset_summary_path,
        "manifest_path": manifest_path,
        "reviewed_source_manifest_path": reviewed_source_manifest_copy,
        "raw_glyph_panel_path": raw_glyph_panel_path,
        "cleaned_glyph_panel_path": cleaned_glyph_panel_path,
        "raw_join_panel_path": raw_join_panel_path,
        "cleaned_join_panel_path": cleaned_join_panel_path,
        "downstream_smoke_test_path": smoke_report_path,
    }
