"""Reviewed nominal-guide validation bench for TD-014."""

from __future__ import annotations

import json
import math
import tomllib
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from scribesim.hand.profile import HandProfile
from scribesim.handvalidate.gates import evaluate_gate
from scribesim.handvalidate.metrics import continuity_score, ocr_proxy_score, trajectory_from_guide
from scribesim.handvalidate.model import StageReport
from scribesim.handvalidate.report import write_stage_report
from scribesim.pathguide.io import load_pathguides_toml
from scribesim.pathguide.model import DensePathGuide


DEFAULT_REVIEWED_EVOFIT_MANIFEST_PATH = Path(
    "shared/training/handsim/reviewed_annotations/reviewed_evofit_v1/manifest.toml"
)
DEFAULT_REVIEWED_PROMOTED_GUIDE_CATALOG_PATH = Path("shared/hands/pathguides/reviewed_promoted_v1.toml")
DEFAULT_REVIEWED_NOMINAL_OUTPUT_ROOT = Path(
    "shared/training/handsim/reviewed_annotations/reviewed_nominal_validation_v1"
)
_TARGET_SIZE = (96, 96)


def _load_toml(path: Path | str) -> dict[str, Any]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def _slug(symbol: str) -> str:
    return symbol.replace("->", "_to_").replace("/", "_").replace(" ", "_")


def _load_fit_sources(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(item["symbol"]): dict(item) for item in payload.get("fit_sources", [])}


def _required_symbols(reviewed_manifest: dict[str, Any]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for symbol in [*reviewed_manifest.get("required_symbols", []), *reviewed_manifest.get("priority_joins", [])]:
        sym = str(symbol)
        if sym in seen:
            continue
        seen.add(sym)
        ordered.append(sym)
    return tuple(ordered)


def _guide_bounds(guide: DensePathGuide, *, margin_mm: float = 0.8) -> tuple[float, float, float, float]:
    min_x = min(sample.x_mm for sample in guide.samples) - margin_mm
    max_x = max(sample.x_mm for sample in guide.samples) + margin_mm
    min_y = min(sample.y_mm for sample in guide.samples) - margin_mm
    max_y = max(sample.y_mm for sample in guide.samples) + margin_mm
    return (min_x, max_x, min_y, max_y)


def _normalize_image_array(arr: np.ndarray, *, target_size: tuple[int, int] = _TARGET_SIZE) -> np.ndarray:
    if arr.ndim == 3:
        pil = Image.fromarray(arr, mode="RGB").convert("L")
    else:
        pil = Image.fromarray(arr.astype(np.uint8), mode="L")
    bg = 255
    canvas = Image.new("L", target_size, bg)
    working = pil.copy()
    working.thumbnail(target_size, Image.Resampling.LANCZOS)
    offset = ((target_size[0] - working.width) // 2, (target_size[1] - working.height) // 2)
    canvas.paste(working, offset)
    rgb = Image.merge("RGB", (canvas, canvas, canvas))
    return np.array(rgb, dtype=np.uint8)


def _load_target_image(path: str | Path) -> np.ndarray:
    return _normalize_image_array(np.array(Image.open(path).convert("L")))


def _render_nominal_image(guide: DensePathGuide) -> np.ndarray:
    from scribesim.handflow.render import render_trajectory_proof

    profile = HandProfile()
    profile.letterform.x_height_mm = guide.x_height_mm
    rendered = render_trajectory_proof(
        trajectory_from_guide(guide, width_scale_mm=profile.nib.width_mm),
        profile=profile,
        dpi=180,
        supersample=2,
        bounds_mm=_guide_bounds(guide),
    )
    return _normalize_image_array(rendered)


def _render_guided_image(guide: DensePathGuide) -> tuple[np.ndarray, float]:
    from scribesim.handflow.controller import GuidedHandFlowController
    from scribesim.handflow.render import render_trajectory_proof

    profile = HandProfile()
    profile.letterform.x_height_mm = guide.x_height_mm
    controller = GuidedHandFlowController(profile, activate_base_pressure=True)
    result = controller.simulate_guide(guide, dt=0.002)
    rendered = render_trajectory_proof(
        result.trajectory,
        profile=profile,
        dpi=180,
        supersample=2,
        bounds_mm=_guide_bounds(guide),
    )
    return _normalize_image_array(rendered), continuity_score(result.guide_aligned_trajectory, guide)


def _save_gray(path: Path, arr: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if arr.ndim == 3:
        Image.fromarray(arr.astype(np.uint8), mode="RGB").save(path, format="PNG")
    else:
        Image.fromarray(arr.astype(np.uint8), mode="L").save(path, format="PNG")
    return path


def _comparison_panel(target: np.ndarray, nominal: np.ndarray, guided: np.ndarray | None, output_path: Path) -> Path:
    width = target.shape[1]
    height = target.shape[0]
    columns = 3 if guided is not None else 2
    panel = Image.new("RGB", (width * columns + 16 * (columns + 1), height + 32), (255, 255, 255))
    x = 16
    for title, arr in (
        ("target", target),
        ("nominal", nominal),
        *((("guided", guided),) if guided is not None else ()),
    ):
        tile = Image.fromarray(arr.astype(np.uint8), mode="RGB" if arr.ndim == 3 else "L").convert("RGB")
        panel.paste(tile, (x, 20))
        x += width + 16
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.save(output_path, format="PNG")
    return output_path


def _write_snapshot_panel(paths: list[Path], output_path: Path, *, columns: int = 4, padding: int = 12) -> Path:
    if not paths:
        raise ValueError("paths must be non-empty")
    images = [Image.open(path).convert("RGB") for path in paths]
    cell_w = max(image.width for image in images)
    cell_h = max(image.height for image in images)
    rows = math.ceil(len(images) / max(columns, 1))
    panel = Image.new(
        "RGB",
        (padding + columns * (cell_w + padding), padding + rows * (cell_h + padding)),
        (255, 255, 255),
    )
    for index, image in enumerate(images):
        row = index // columns
        col = index % columns
        x = padding + col * (cell_w + padding)
        y = padding + row * (cell_h + padding)
        panel.paste(image, (x, y))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.save(output_path, format="PNG")
    return output_path


def _write_dashboard_markdown(
    output_path: Path,
    *,
    summary_metrics: dict[str, float],
    rows: list[dict[str, Any]],
    report: StageReport,
) -> None:
    lines = [
        "# TD-014 Reviewed Nominal Validation",
        "",
        f"- Gate: {'PASS' if report.gate.passed else 'FAIL'}",
        "",
        "## Summary Metrics",
        "",
    ]
    for key in sorted(summary_metrics):
        lines.append(f"- `{key}`: {summary_metrics[key]:.4f}")
    if report.gate.failures:
        lines.extend(["", "## Gate Failures", ""])
        for failure in report.gate.failures:
            lines.append(f"- `{failure.metric}`: {failure.reason}")
    lines.extend(["", "## Symbols", ""])
    for row in rows:
        lines.append(
            f"- `{row['symbol']}` ({row['kind']}): "
            f"raw_nominal={row['raw_nominal_score']:.4f}, "
            f"cleaned_nominal={row['cleaned_nominal_score']:.4f}, "
            f"guided={row['guided_score']:.4f}, "
            f"continuity={row['guided_continuity_score']:.4f}"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_reviewed_nominal_validation(
    reviewed_evofit_manifest_path: Path | str = DEFAULT_REVIEWED_EVOFIT_MANIFEST_PATH,
    *,
    promoted_guide_catalog_path: Path | str = DEFAULT_REVIEWED_PROMOTED_GUIDE_CATALOG_PATH,
    output_root: Path | str = DEFAULT_REVIEWED_NOMINAL_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Compare raw nominal, cleaned nominal, and guided outputs on the reviewed slice."""

    reviewed_evofit_manifest_path = Path(reviewed_evofit_manifest_path).resolve()
    evofit_manifest = _load_toml(reviewed_evofit_manifest_path)
    cleaned_summary_path = Path(str(evofit_manifest["summary_json_path"])).resolve()
    reviewed_manifest_path = Path(str(evofit_manifest["corpus_manifest_path"])).resolve()
    cleaned_summary = json.loads(cleaned_summary_path.read_text(encoding="utf-8"))
    raw_summary_path = Path(str(cleaned_summary["raw_reviewed_baseline_summary_path"])).resolve()
    raw_summary = json.loads(raw_summary_path.read_text(encoding="utf-8"))
    reviewed_manifest = _load_toml(reviewed_manifest_path)

    cleaned_fit_sources = _load_fit_sources(cleaned_summary_path)
    raw_fit_sources = _load_fit_sources(raw_summary_path)

    promoted_guides = load_pathguides_toml(promoted_guide_catalog_path)
    raw_catalog_path = Path(str(raw_summary["proposal_catalog_path"])).resolve()
    raw_guides = load_pathguides_toml(raw_catalog_path)
    required = _required_symbols(reviewed_manifest)

    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    raw_panel_paths: list[Path] = []
    cleaned_panel_paths: list[Path] = []
    guided_panel_paths: list[Path] = []
    rows: list[dict[str, Any]] = []

    for symbol in required:
        raw_fit = raw_fit_sources.get(symbol, {})
        cleaned_fit = cleaned_fit_sources.get(symbol, {})
        raw_target_path = str(raw_fit.get("selected_source_raw_path") or raw_fit.get("selected_source_path") or "")
        cleaned_target_path = str(
            cleaned_fit.get("selected_source_cleaned_path")
            or cleaned_fit.get("selected_source_path")
            or cleaned_fit.get("selected_source_raw_path")
            or ""
        )
        if not raw_target_path or not cleaned_target_path:
            continue
        raw_target = _load_target_image(raw_target_path)
        cleaned_target = _load_target_image(cleaned_target_path)
        raw_nominal = _render_nominal_image(raw_guides[symbol]) if symbol in raw_guides else None
        cleaned_nominal = _render_nominal_image(promoted_guides[symbol]) if symbol in promoted_guides else None
        guided_img = None
        guided_continuity = 0.0
        if symbol in promoted_guides:
            guided_img, guided_continuity = _render_guided_image(promoted_guides[symbol])

        symbol_dir = output_root / _slug(symbol)
        kind = promoted_guides[symbol].kind if symbol in promoted_guides else raw_guides[symbol].kind
        raw_score = ocr_proxy_score(raw_nominal, raw_target) if raw_nominal is not None else 0.0
        cleaned_score = ocr_proxy_score(cleaned_nominal, cleaned_target) if cleaned_nominal is not None else 0.0
        guided_score = ocr_proxy_score(guided_img, cleaned_target) if guided_img is not None else 0.0

        _save_gray(symbol_dir / "raw_target.png", raw_target)
        _save_gray(symbol_dir / "cleaned_target.png", cleaned_target)
        if raw_nominal is not None:
            _save_gray(symbol_dir / "raw_nominal.png", raw_nominal)
            raw_panel_paths.append(_comparison_panel(raw_target, raw_nominal, None, symbol_dir / "raw_panel.png"))
        if cleaned_nominal is not None:
            _save_gray(symbol_dir / "cleaned_nominal.png", cleaned_nominal)
            cleaned_panel_paths.append(
                _comparison_panel(cleaned_target, cleaned_nominal, None, symbol_dir / "cleaned_panel.png")
            )
        if guided_img is not None:
            _save_gray(symbol_dir / "guided.png", guided_img)
            guided_panel_paths.append(
                _comparison_panel(cleaned_target, cleaned_nominal, guided_img, symbol_dir / "guided_panel.png")
            )

        rows.append(
            {
                "symbol": symbol,
                "kind": kind,
                "raw_nominal_score": float(raw_score),
                "cleaned_nominal_score": float(cleaned_score),
                "guided_score": float(guided_score),
                "guided_continuity_score": float(guided_continuity),
                "raw_target_path": raw_target_path,
                "cleaned_target_path": cleaned_target_path,
                "selected_source_variant": str(cleaned_fit.get("selected_source_variant", "raw")),
            }
        )

    if not rows:
        raise ValueError("no reviewed nominal symbols available for validation")

    shared_count = len(rows)
    summary_metrics = {
        "raw_nominal_mean_score": float(sum(row["raw_nominal_score"] for row in rows) / shared_count),
        "cleaned_nominal_mean_score": float(sum(row["cleaned_nominal_score"] for row in rows) / shared_count),
        "guided_mean_score": float(sum(row["guided_score"] for row in rows) / shared_count),
        "cleaned_vs_raw_delta": float(
            (sum(row["cleaned_nominal_score"] for row in rows) - sum(row["raw_nominal_score"] for row in rows))
            / shared_count
        ),
        "guided_vs_cleaned_delta": float(
            (sum(row["guided_score"] for row in rows) - sum(row["cleaned_nominal_score"] for row in rows))
            / shared_count
        ),
        "guided_join_continuity_mean_score": float(
            sum(row["guided_continuity_score"] for row in rows if row["kind"] == "join")
            / max(sum(1 for row in rows if row["kind"] == "join"), 1)
        ),
        "exact_symbol_coverage": len([symbol for symbol in required if symbol in promoted_guides]) / max(len(required), 1),
        "symbol_count": float(len(rows)),
    }
    gate = evaluate_gate("reviewed_nominal", summary_metrics)
    report = StageReport(stage="reviewed_nominal", metrics=summary_metrics, gate=gate)
    report_json_path, report_md_path = write_stage_report(report, output_root)

    raw_panel_path = _write_snapshot_panel(raw_panel_paths, output_root / "raw_nominal_panel.png", columns=4)
    cleaned_panel_path = _write_snapshot_panel(cleaned_panel_paths, output_root / "cleaned_nominal_panel.png", columns=4)
    guided_panel_path = _write_snapshot_panel(guided_panel_paths, output_root / "guided_panel.png", columns=4)

    dashboard_payload = {
        "reviewed_evofit_manifest_path": reviewed_evofit_manifest_path.as_posix(),
        "reviewed_manifest_path": reviewed_manifest_path.as_posix(),
        "promoted_guide_catalog_path": str(Path(promoted_guide_catalog_path).resolve()),
        "raw_summary_path": raw_summary_path.as_posix(),
        "summary_metrics": summary_metrics,
        "rows": rows,
        "raw_nominal_panel_path": raw_panel_path.as_posix(),
        "cleaned_nominal_panel_path": cleaned_panel_path.as_posix(),
        "guided_panel_path": guided_panel_path.as_posix(),
        "stage_report_json_path": report_json_path.as_posix(),
        "stage_report_md_path": report_md_path.as_posix(),
    }
    dashboard_json_path = output_root / "dashboard.json"
    dashboard_md_path = output_root / "dashboard.md"
    dashboard_json_path.write_text(json.dumps(dashboard_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_dashboard_markdown(dashboard_md_path, summary_metrics=summary_metrics, rows=rows, report=report)

    return {
        "summary_metrics": summary_metrics,
        "dashboard_json_path": dashboard_json_path,
        "dashboard_md_path": dashboard_md_path,
        "stage_report_json_path": report_json_path,
        "stage_report_md_path": report_md_path,
        "raw_nominal_panel_path": raw_panel_path,
        "cleaned_nominal_panel_path": cleaned_panel_path,
        "guided_panel_path": guided_panel_path,
    }
