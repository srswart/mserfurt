"""Reviewed evofit guide freeze for TD-014."""

from __future__ import annotations

import json
import tomllib
from dataclasses import replace
from pathlib import Path
from typing import Any

from scribesim.pathguide.io import load_pathguides_toml, write_pathguides_toml
from scribesim.pathguide.model import DensePathGuide, GuideSource
from scribesim.pathguide.review import (
    build_starter_dataset_report,
    write_dataset_report_bundle,
    write_guide_overlay_snapshot,
    write_nominal_guide_snapshot,
    write_snapshot_panel,
)


DEFAULT_REVIEWED_EVOFIT_MANIFEST_PATH = Path(
    "shared/training/handsim/reviewed_annotations/reviewed_evofit_v1/manifest.toml"
)
DEFAULT_REVIEWED_PROMOTED_GUIDE_OUTPUT_ROOT = Path(
    "shared/training/handsim/reviewed_annotations/reviewed_promoted_guides_v1"
)
DEFAULT_REVIEWED_PROMOTED_GUIDE_CATALOG_PATH = Path("shared/hands/pathguides/reviewed_promoted_v1.toml")
_DEFAULT_SOURCE_RESOLUTION_PPMM = 16.0


def _load_toml(path: Path | str) -> dict[str, Any]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def _slug(symbol: str) -> str:
    return symbol.replace("->", "_to_").replace("/", "_").replace(" ", "_")


def _assign_split(index: int) -> str:
    slot = index % 5
    if slot == 0:
        return "validation"
    if slot == 1:
        return "test"
    return "train"


def _required_symbol_set(reviewed_manifest: dict[str, Any]) -> tuple[str, ...]:
    glyphs = [str(value) for value in reviewed_manifest.get("required_symbols", [])]
    joins = [str(value) for value in reviewed_manifest.get("priority_joins", [])]
    ordered: list[str] = []
    seen: set[str] = set()
    for symbol in [*glyphs, *joins]:
        if symbol in seen:
            continue
        seen.add(symbol)
        ordered.append(symbol)
    return tuple(ordered)


def _join_schedule_map(guides: dict[str, DensePathGuide]) -> dict[str, str]:
    return {
        symbol: "reviewed_evofit"
        for symbol, guide in guides.items()
        if guide.kind == "join"
    }


def _fit_source_map(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for entry in summary.get("fit_sources", []):
        symbol = str(entry.get("symbol", "")).strip()
        if symbol:
            result[symbol] = dict(entry)
    return result


def _promote_guide(
    guide: DensePathGuide,
    *,
    fit_source: dict[str, Any],
    split: str,
) -> DensePathGuide:
    raw_path = str(fit_source.get("selected_source_raw_path", "") or "")
    cleaned_path = str(fit_source.get("selected_source_cleaned_path", "") or "")
    selected_path = str(fit_source.get("selected_source_path", "") or "")
    manuscript = str(fit_source.get("selected_source_manuscript", "") or "")
    variant = str(fit_source.get("selected_source_variant", "raw") or "raw")
    cleanup_count = int(fit_source.get("selected_source_cleanup_stroke_count", 0) or 0)
    quality = str(fit_source.get("selected_source_quality_tier", "") or "")
    object_id = str(fit_source.get("selected_source_object_id", "") or "")
    source_resolution_ppmm = next(
        (
            float(source.source_resolution_ppmm)
            for source in guide.sources
            if source.source_resolution_ppmm is not None
        ),
        _DEFAULT_SOURCE_RESOLUTION_PPMM,
    )

    accepted_sources: list[GuideSource] = []
    if raw_path:
        accepted_sources.append(
            GuideSource(
                source_id=f"reviewed-raw:{guide.symbol}",
                source_path=raw_path,
                extraction_run=f"ADV-SS-PATHGUIDE-004:raw:{manuscript or 'unknown'}",
                confidence_tier="accepted",
                split=split,
                source_resolution_ppmm=source_resolution_ppmm,
            )
        )
    if cleaned_path:
        accepted_sources.append(
            GuideSource(
                source_id=f"reviewed-cleaned:{guide.symbol}",
                source_path=cleaned_path,
                extraction_run=f"ADV-SS-PATHGUIDE-004:cleaned:{manuscript or 'unknown'}",
                confidence_tier="accepted",
                split=split,
                source_resolution_ppmm=source_resolution_ppmm,
            )
        )
    if not accepted_sources and selected_path:
        accepted_sources.append(
            GuideSource(
                source_id=f"reviewed-selected:{guide.symbol}",
                source_path=selected_path,
                extraction_run=f"ADV-SS-PATHGUIDE-004:{variant}:{manuscript or 'unknown'}",
                confidence_tier="accepted",
                split=split,
                source_resolution_ppmm=source_resolution_ppmm,
            )
        )
    if not accepted_sources:
        raise ValueError(f"missing reviewed source provenance for promoted guide {guide.symbol!r}")

    return replace(guide, sources=tuple(accepted_sources))


def _write_provenance_report(
    *,
    output_root: Path,
    guide_catalog_path: Path,
    validation_report_json_path: Path,
    validation_report_md_path: Path,
    overlay_panel_path: Path,
    nominal_panel_path: Path,
    reviewed_manifest_path: Path,
    promoted_guides: dict[str, DensePathGuide],
    fit_source_map_by_symbol: dict[str, dict[str, Any]],
    required_symbols: tuple[str, ...],
) -> tuple[Path, Path, Path]:
    summary: dict[str, Any] = {
        "dataset_id": output_root.name,
        "guide_catalog_path": guide_catalog_path.as_posix(),
        "reviewed_manifest_path": reviewed_manifest_path.as_posix(),
        "validation_report_json_path": validation_report_json_path.as_posix(),
        "validation_report_md_path": validation_report_md_path.as_posix(),
        "overlay_panel_path": overlay_panel_path.as_posix(),
        "nominal_panel_path": nominal_panel_path.as_posix(),
        "guide_count": len(promoted_guides),
        "glyph_count": sum(1 for guide in promoted_guides.values() if guide.kind == "glyph"),
        "join_count": sum(1 for guide in promoted_guides.values() if guide.kind == "join"),
        "required_symbol_count": len(required_symbols),
        "present_symbols": [symbol for symbol in required_symbols if symbol in promoted_guides],
        "missing_symbols": [symbol for symbol in required_symbols if symbol not in promoted_guides],
        "exact_symbol_coverage": (
            len([symbol for symbol in required_symbols if symbol in promoted_guides]) / max(len(required_symbols), 1)
        ),
        "symbols": [],
    }

    for symbol in sorted(promoted_guides):
        fit_source = fit_source_map_by_symbol.get(symbol, {})
        guide = promoted_guides[symbol]
        summary["symbols"].append(
            {
                "symbol": symbol,
                "kind": guide.kind,
                "selected_source_path": str(fit_source.get("selected_source_path", "") or ""),
                "selected_source_raw_path": str(fit_source.get("selected_source_raw_path", "") or ""),
                "selected_source_cleaned_path": str(fit_source.get("selected_source_cleaned_path", "") or ""),
                "selected_source_variant": str(fit_source.get("selected_source_variant", "raw") or "raw"),
                "selected_source_cleanup_stroke_count": int(
                    fit_source.get("selected_source_cleanup_stroke_count", 0) or 0
                ),
                "selected_source_manuscript": str(fit_source.get("selected_source_manuscript", "") or ""),
                "selected_source_quality_tier": str(fit_source.get("selected_source_quality_tier", "") or ""),
                "selected_source_object_id": str(fit_source.get("selected_source_object_id", "") or ""),
                "best_fitness": float(fit_source.get("best_fitness", 0.0) or 0.0),
                "nominal_ncc": float(fit_source.get("nominal_ncc", 0.0) or 0.0),
                "evofit_ncc": float(fit_source.get("evofit_ncc", 0.0) or 0.0),
                "beats_prior_nominal": bool(fit_source.get("beats_prior_nominal", False)),
                "source_paths": [source.source_path or "" for source in guide.sources],
                "source_splits": [source.split for source in guide.sources],
            }
        )

    json_path = output_root / "coverage_provenance_report.json"
    md_path = output_root / "coverage_provenance_report.md"
    manifest_path = output_root / "manifest.toml"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# TD-014 Reviewed Promoted Guide Freeze",
        "",
        f"- Dataset: `{summary['dataset_id']}`",
        f"- Reviewed manifest: `{summary['reviewed_manifest_path']}`",
        f"- Guide catalog: `{summary['guide_catalog_path']}`",
        f"- Guide count: `{summary['guide_count']}`",
        f"- Glyph count: `{summary['glyph_count']}`",
        f"- Join count: `{summary['join_count']}`",
        f"- Exact symbol coverage: `{summary['exact_symbol_coverage']:.4f}`",
        f"- Missing symbols: `{len(summary['missing_symbols'])}`",
        f"- Validation report: `{summary['validation_report_md_path']}`",
        f"- Overlay panel: `{summary['overlay_panel_path']}`",
        f"- Nominal panel: `{summary['nominal_panel_path']}`",
        "",
        "## Missing Symbols",
        "",
        ", ".join(summary["missing_symbols"]) if summary["missing_symbols"] else "(none)",
        "",
        "## Promoted Guides",
        "",
    ]
    for item in summary["symbols"]:
        lines.append(
            f"- `{item['symbol']}` ({item['kind']}): "
            f"variant={item['selected_source_variant']}, "
            f"cleanup={item['selected_source_cleanup_stroke_count']}, "
            f"quality={item['selected_source_quality_tier'] or 'n/a'}, "
            f"manuscript={item['selected_source_manuscript'] or 'unknown'}, "
            f"fitness={item['best_fitness']:.4f}, "
            f"ncc={item['evofit_ncc']:.4f}, "
            f"prior={item['nominal_ncc']:.4f}"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest_lines = [
        "# TD-014 reviewed promoted guide manifest",
        "schema_version = 1",
        'manifest_kind = "reviewed_promoted_guides"',
        f'dataset_id = "{output_root.name}"',
        f'guide_catalog_path = "{guide_catalog_path.as_posix()}"',
        f'reviewed_manifest_path = "{reviewed_manifest_path.as_posix()}"',
        f'validation_report_json_path = "{validation_report_json_path.as_posix()}"',
        f'validation_report_md_path = "{validation_report_md_path.as_posix()}"',
        f'coverage_provenance_report_json_path = "{json_path.as_posix()}"',
        f'coverage_provenance_report_md_path = "{md_path.as_posix()}"',
        f'overlay_panel_path = "{overlay_panel_path.as_posix()}"',
        f'nominal_panel_path = "{nominal_panel_path.as_posix()}"',
        "",
    ]
    for item in summary["symbols"]:
        manifest_lines.extend(
            [
                "[[symbols]]",
                f'symbol = "{item["symbol"]}"',
                f'kind = "{item["kind"]}"',
                f'selected_source_path = {json.dumps(item["selected_source_path"])}',
                f'selected_source_raw_path = {json.dumps(item["selected_source_raw_path"])}',
                f'selected_source_cleaned_path = {json.dumps(item["selected_source_cleaned_path"])}',
                f'selected_source_variant = {json.dumps(item["selected_source_variant"])}',
                f'selected_source_quality_tier = {json.dumps(item["selected_source_quality_tier"])}',
                f'selected_source_manuscript = {json.dumps(item["selected_source_manuscript"])}',
                f'selected_source_object_id = {json.dumps(item["selected_source_object_id"])}',
                f"selected_source_cleanup_stroke_count = {item['selected_source_cleanup_stroke_count']}",
                f"best_fitness = {item['best_fitness']:.6f}",
                f"evofit_ncc = {item['evofit_ncc']:.6f}",
                f"nominal_ncc = {item['nominal_ncc']:.6f}",
                "",
            ]
        )
    manifest_path.write_text("\n".join(manifest_lines), encoding="utf-8")
    return json_path, md_path, manifest_path


def freeze_reviewed_evofit_guides(
    reviewed_evofit_manifest_path: Path | str = DEFAULT_REVIEWED_EVOFIT_MANIFEST_PATH,
    *,
    output_root: Path | str = DEFAULT_REVIEWED_PROMOTED_GUIDE_OUTPUT_ROOT,
    guide_catalog_path: Path | str = DEFAULT_REVIEWED_PROMOTED_GUIDE_CATALOG_PATH,
) -> dict[str, Any]:
    """Freeze reviewed evofit proposals into promoted dense path guides."""

    reviewed_evofit_manifest_path = Path(reviewed_evofit_manifest_path).resolve()
    bundle_manifest = _load_toml(reviewed_evofit_manifest_path)
    if int(bundle_manifest.get("schema_version", 0) or 0) != 1:
        raise ValueError("reviewed evofit manifest must declare schema_version = 1")
    proposal_catalog_path = Path(str(bundle_manifest.get("proposal_catalog_path", ""))).resolve()
    summary_json_path = Path(str(bundle_manifest.get("summary_json_path", ""))).resolve()
    reviewed_manifest_path = Path(str(bundle_manifest.get("corpus_manifest_path", ""))).resolve()
    if not proposal_catalog_path.exists():
        raise ValueError(f"proposal catalog not found: {proposal_catalog_path}")
    if not summary_json_path.exists():
        raise ValueError(f"summary json not found: {summary_json_path}")
    if not reviewed_manifest_path.exists():
        raise ValueError(f"reviewed exemplar manifest not found: {reviewed_manifest_path}")

    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    guide_catalog_path = Path(guide_catalog_path).resolve()
    guide_catalog_path.parent.mkdir(parents=True, exist_ok=True)

    reviewed_manifest = _load_toml(reviewed_manifest_path)
    required_symbols = _required_symbol_set(reviewed_manifest)
    summary = json.loads(summary_json_path.read_text(encoding="utf-8"))
    fit_source_map_by_symbol = _fit_source_map(summary)
    proposal_guides = load_pathguides_toml(proposal_catalog_path)
    if not proposal_guides:
        raise ValueError("reviewed evofit proposal catalog contains no guides")

    promoted_guides: dict[str, DensePathGuide] = {}
    ordered_symbols = sorted(proposal_guides)
    for index, symbol in enumerate(ordered_symbols):
        if symbol not in fit_source_map_by_symbol:
            continue
        fit_source = fit_source_map_by_symbol[symbol]
        if not bool(fit_source.get("structurally_convertible", True)):
            continue
        promoted_guides[symbol] = _promote_guide(
            proposal_guides[symbol],
            fit_source=fit_source,
            split=_assign_split(index),
        )

    if not promoted_guides:
        raise ValueError("no structurally convertible reviewed evofit guides available for promotion")

    write_pathguides_toml(promoted_guides, guide_catalog_path)

    overlay_dir = output_root / "overlay_snapshots"
    nominal_dir = output_root / "nominal_snapshots"
    overlay_paths: list[Path] = []
    nominal_paths: list[Path] = []
    for symbol in sorted(promoted_guides):
        overlay_paths.append(
            write_guide_overlay_snapshot(promoted_guides[symbol], overlay_dir / f"{_slug(symbol)}.png")
        )
        nominal_paths.append(
            write_nominal_guide_snapshot(promoted_guides[symbol], nominal_dir / f"{_slug(symbol)}.png")
        )

    overlay_panel_path = write_snapshot_panel(overlay_paths, overlay_dir / "panel.png", columns=5)
    nominal_panel_path = write_snapshot_panel(nominal_paths, nominal_dir / "panel.png", columns=5)

    report = build_starter_dataset_report(
        promoted_guides,
        required_symbols=required_symbols,
        join_schedules=_join_schedule_map(promoted_guides),
        dataset_policy_name="promotion",
        gate_stage="pathguide_dataset",
    )
    validation_report_json_path, validation_report_md_path = write_dataset_report_bundle(report, output_root)
    coverage_report_json_path, coverage_report_md_path, manifest_path = _write_provenance_report(
        output_root=output_root,
        guide_catalog_path=guide_catalog_path,
        validation_report_json_path=validation_report_json_path,
        validation_report_md_path=validation_report_md_path,
        overlay_panel_path=overlay_panel_path,
        nominal_panel_path=nominal_panel_path,
        reviewed_manifest_path=reviewed_manifest_path,
        promoted_guides=promoted_guides,
        fit_source_map_by_symbol=fit_source_map_by_symbol,
        required_symbols=required_symbols,
    )

    summary_payload = {
        "dataset_id": output_root.name,
        "guide_count": len(promoted_guides),
        "glyph_count": sum(1 for guide in promoted_guides.values() if guide.kind == "glyph"),
        "join_count": sum(1 for guide in promoted_guides.values() if guide.kind == "join"),
        "exact_symbol_coverage": report.metrics.get("required_symbol_coverage", 0.0),
        "validation_gate_passed": bool(report.gate.passed),
        "validation_gate_failures": [failure.metric for failure in report.gate.failures],
        "validation_gate_advisories": list(report.gate.advisories),
    }

    return {
        "summary": summary_payload,
        "guide_catalog_path": guide_catalog_path,
        "manifest_path": manifest_path,
        "validation_report_json_path": validation_report_json_path,
        "validation_report_md_path": validation_report_md_path,
        "coverage_provenance_report_json_path": coverage_report_json_path,
        "coverage_provenance_report_md_path": coverage_report_md_path,
        "overlay_panel_path": overlay_panel_path,
        "nominal_panel_path": nominal_panel_path,
    }
