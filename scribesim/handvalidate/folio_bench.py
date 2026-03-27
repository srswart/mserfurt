"""Folio-level A/B regression bench for TD-014 rollout decisions."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict
from pathlib import Path
import tomllib
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image

from scribesim.groundtruth.page_xml import generate as generate_page_xml
from scribesim.hand.profile import HandProfile
from scribesim.handflow import (
    GuidedFolioResolutionError,
    GuidedHandFlowController,
    build_line_session,
    load_word_guide_catalog,
)
from scribesim.handflow import render_guided_folio_lines, render_trajectory_proof
from scribesim.handvalidate.gates import evaluate_gate, load_gate_config
from scribesim.handvalidate.metrics import (
    alias_substitution_count,
    downstream_contract_pass_rate,
    exact_character_coverage,
    normalized_substitution_count,
    ocr_proxy_score,
    pressure_dynamic_range_score,
    readability_regression_delta,
)
from scribesim.handvalidate.model import (
    FolioBenchCase,
    FolioBenchManifest,
    FolioBenchRunResult,
    FolioPromotionDecision,
    StageReport,
)
from scribesim.handvalidate.report import write_stage_report
from scribesim.layout import place
from scribesim.render.pipeline import render_pipeline
from weather.compositor import composite_folio
from weather.profile import load_profile as load_weather_profile
from weather.substrate.vellum import stock_for_folio


DEFAULT_FOLIO_BENCH_MANIFEST_PATH = Path("shared/training/handsim/folio_bench/manifest.toml")


def _flatten_overrides(payload: dict[str, object], prefix: str = "") -> dict[str, object]:
    flat: dict[str, object] = {}
    for key, value in payload.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten_overrides(value, dotted))
        else:
            flat[dotted] = value
    return flat


def _apply_overrides(profile: HandProfile, overrides: dict[str, object]) -> HandProfile:
    if not overrides:
        return profile
    return profile.apply_delta(_flatten_overrides(overrides))


def load_folio_bench_manifest(path: Path | str = DEFAULT_FOLIO_BENCH_MANIFEST_PATH) -> FolioBenchManifest:
    raw = tomllib.loads(Path(path).read_text())
    cases = tuple(
        FolioBenchCase(
            name=str(case["name"]),
            folio_id=str(case.get("folio_id", "")),
            folio_path=str(case["folio_path"]),
            description=str(case.get("description", "")),
            line_limit=int(case["line_limit"]) if case.get("line_limit") is not None else None,
            profile_overrides=dict(case.get("profile_overrides", {})),
        )
        for case in raw.get("cases", [])
    )
    return FolioBenchManifest(
        stage_id=str(raw["stage_id"]),
        checkpoint_id=str(raw["checkpoint_id"]),
        word_line_manifest_path=str(raw["word_line_manifest_path"]),
        word_line_candidate_name=str(raw.get("word_line_candidate_name", "line_v1_tuned")),
        weather_profile_path=str(raw["weather_profile_path"]),
        guided_supersample=int(raw.get("guided_supersample", 4)),
        proof_dpi=int(raw.get("proof_dpi", 220)),
        proof_supersample=int(raw.get("proof_supersample", 3)),
        dt=float(raw.get("dt", 0.002)),
        evo_quality=str(raw.get("evo_quality", "balanced")),
        evo_evolve=bool(raw.get("evo_evolve", True)),
        base_profile_overrides=dict(raw.get("base_profile_overrides", {})),
        cases=cases,
    )


def _load_line_checkpoint_profile(
    base_profile: HandProfile,
    *,
    word_line_manifest_path: Path | str,
    word_line_candidate_name: str,
) -> HandProfile:
    from scribesim.curriculum.word_line import _load_glyph_join_profile, load_word_line_manifest

    manifest = load_word_line_manifest(word_line_manifest_path)
    profile = _load_glyph_join_profile(
        copy.deepcopy(base_profile),
        glyph_join_manifest_path=manifest.glyph_join_manifest_path,
        glyph_join_candidate_name=manifest.glyph_join_candidate_name,
    )
    profile = _apply_overrides(profile, manifest.base_profile_overrides)
    for candidate in manifest.candidates:
        if candidate.name == word_line_candidate_name:
            return _apply_overrides(profile, candidate.profile_overrides)
    raise KeyError(f"unknown word/line candidate: {word_line_candidate_name}")


def _load_folio_dict(case: FolioBenchCase) -> dict:
    folio = json.loads(Path(case.folio_path).read_text())
    if case.folio_id and not folio.get("id"):
        folio["id"] = case.folio_id
    if case.line_limit is not None:
        folio["lines"] = folio.get("lines", [])[: case.line_limit]
        if "metadata" in folio and isinstance(folio["metadata"], dict):
            folio["metadata"]["line_count"] = len(folio["lines"])
    return folio


def _save_rgb(path: Path, arr: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr, mode="RGB").save(path, format="PNG", dpi=(300, 300))
    return path


def _save_gray(path: Path, arr: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr, mode="L").save(path, format="PNG", dpi=(300, 300))
    return path


def _align_common_canvas(left: np.ndarray, right: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    height = min(left.shape[0], right.shape[0])
    width = min(left.shape[1], right.shape[1])
    return left[:height, :width], right[:height, :width]


def _save_diff(path: Path, left: np.ndarray, right: np.ndarray) -> Path:
    left, right = _align_common_canvas(left, right)
    diff = np.abs(left.astype(np.int16) - right.astype(np.int16)).astype(np.uint8)
    if diff.ndim == 3:
        diff = diff.max(axis=2)
    return _save_gray(path, diff)


def _guide_render_bounds(guide) -> tuple[float, float, float, float]:
    points = guide.samples
    min_x = min(sample.x_mm for sample in points) - guide.x_height_mm * 0.35
    max_x = max(sample.x_mm for sample in points) + guide.x_height_mm * 0.35
    min_y = min(sample.y_mm for sample in points) - guide.x_height_mm * 0.55
    max_y = max(sample.y_mm for sample in points) + guide.x_height_mm * 0.55
    return (min_x, max_x, min_y, max_y)


def _nominal_trajectory(guide, profile: HandProfile):
    from scribesim.handvalidate import trajectory_from_guide

    return trajectory_from_guide(guide, width_scale_mm=profile.nib.width_mm)


def _case_line_metrics(
    lines: list[str],
    *,
    profile: HandProfile,
    proof_dpi: int,
    proof_supersample: int,
    dt: float,
    evo_evolve: bool,
    exact_symbols: bool,
) -> dict[str, float]:
    from scribesim.curriculum.word_line import _build_line_metrics
    from scribesim.evo.compose import render_line

    guide_catalog = load_word_guide_catalog(
        x_height_mm=profile.letterform.x_height_mm,
        exact_symbols=exact_symbols,
    )
    readability_deltas: list[float] = []
    guided_scores: list[float] = []
    spacing_values: list[float] = []
    baseline_values: list[float] = []
    continuity_values: list[float] = []
    exact_coverage_values: list[float] = []
    alias_counts: list[float] = []
    normalized_counts: list[float] = []

    for line_text in lines:
        if not line_text.strip():
            continue
        controller = GuidedHandFlowController(profile, activate_base_pressure=True)
        session_items, line_guide, word_guides = build_line_session(
            line_text,
            guide_catalog=guide_catalog,
            profile=profile,
        )
        result = controller.simulate_session(session_items, dt=dt)
        bounds_mm = _guide_render_bounds(line_guide)
        guided_img = render_trajectory_proof(
            result.trajectory,
            profile=profile,
            dpi=proof_dpi,
            supersample=proof_supersample,
            bounds_mm=bounds_mm,
        )
        reference = render_trajectory_proof(
            _nominal_trajectory(line_guide, profile),
            profile=profile,
            dpi=proof_dpi,
            supersample=proof_supersample,
            bounds_mm=bounds_mm,
        )
        guided_metrics = _build_line_metrics(
            session_items,
            result,
            line_guide,
            word_guides,
            guided_img,
            reference,
        )
        exact_coverage_values.append(exact_character_coverage(session_items))
        alias_counts.append(alias_substitution_count(session_items))
        normalized_counts.append(normalized_substitution_count(session_items))
        evo_img = render_line(
            line_text,
            dpi=proof_dpi,
            nib_width_mm=profile.nib.width_mm,
            nib_angle_deg=profile.nib.angle_deg,
            x_height_mm=profile.letterform.x_height_mm,
            line_height_mm=max(profile.letterform.x_height_mm * 3.6, 13.5),
            evolve=evo_evolve,
            verbose=False,
            use_cache=True,
        )
        evo_score = ocr_proxy_score(evo_img, reference)
        readability_deltas.append(
            readability_regression_delta(guided_metrics["ocr_proxy_score"], evo_score)
        )
        guided_scores.append(guided_metrics["ocr_proxy_score"])
        spacing_values.append(guided_metrics["spacing_cv"])
        baseline_values.append(guided_metrics["baseline_drift_ratio"])
        continuity_values.append(guided_metrics["join_continuity_score"])

    return {
        "mean_guided_ocr_proxy_score": float(sum(guided_scores) / max(len(guided_scores), 1)),
        "mean_spacing_cv": float(sum(spacing_values) / max(len(spacing_values), 1)),
        "mean_baseline_drift_ratio": float(sum(baseline_values) / max(len(baseline_values), 1)),
        "mean_join_continuity_score": float(sum(continuity_values) / max(len(continuity_values), 1)),
        "exact_character_coverage": float(sum(exact_coverage_values) / max(len(exact_coverage_values), 1)),
        "alias_substitution_count": float(sum(alias_counts)),
        "normalized_substitution_count": float(sum(normalized_counts)),
        "mean_readability_regression_delta": float(
            sum(readability_deltas) / max(len(readability_deltas), 1)
        ),
    }


def _render_evo_page(folio: dict, profile: HandProfile, layout, *, evolve: bool, quality: str) -> tuple[np.ndarray, np.ndarray]:
    from scribesim.cli import (
        _evo_config,
        _evo_letter_gap,
        _evo_line_box_height_mm,
        _evo_nib_width_mm,
        _evo_variation,
        _evo_word_gap_mm,
    )
    from scribesim.evo.compose import render_folio_lines

    geom = layout.geometry
    evo_nib_width_mm = _evo_nib_width_mm(profile, geom)
    config = _evo_config(profile, evo_nib_width_mm, quality=quality) if evolve else None
    return render_folio_lines(
        [line.get("text", "") for line in folio.get("lines", [])],
        dpi=300.0,
        nib_width_mm=evo_nib_width_mm,
        nib_angle_deg=profile.nib.angle_deg,
        x_height_mm=geom.x_height_mm,
        line_spacing_mm=geom.ruling_pitch_mm,
        line_height_mm=_evo_line_box_height_mm(geom),
        margin_left_mm=geom.margin_inner,
        margin_top_mm=geom.margin_top,
        page_width_mm=geom.page_w_mm,
        page_height_mm=geom.page_h_mm,
        word_gap_mm=_evo_word_gap_mm(profile, geom.x_height_mm),
        guides_path=None,
        verbose=False,
        variation=_evo_variation(profile),
        letter_gap=_evo_letter_gap(profile),
        profile=profile,
        evolve=evolve,
        config=config,
        use_cache=True,
        return_heatmap=True,
    )


def _render_plain_page(case_dir: Path, folio: dict, profile: HandProfile, layout) -> tuple[np.ndarray, np.ndarray]:
    page_path, heat_path = render_pipeline(
        layout,
        profile.to_v1(),
        case_dir,
        folio.get("id", "folio"),
        profile=profile,
    )
    page = np.array(Image.open(page_path).convert("RGB"))
    heat = np.array(Image.open(heat_path).convert("L"))
    return page, heat


def _render_guided_page(
    folio: dict,
    profile: HandProfile,
    layout,
    *,
    guided_supersample: int,
    exact_symbols: bool,
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    geom = layout.geometry
    return render_guided_folio_lines(
        [line.get("text", "") for line in folio.get("lines", [])],
        profile=profile,
        dpi=300,
        supersample=guided_supersample,
        x_height_mm=geom.x_height_mm,
        line_spacing_mm=geom.ruling_pitch_mm,
        margin_left_mm=geom.margin_inner,
        margin_top_mm=geom.margin_top,
        page_width_mm=geom.page_w_mm,
        page_height_mm=geom.page_h_mm,
        exact_symbols=exact_symbols,
        return_metadata=True,
    )


def _build_case_panel(image_paths: list[Path], output_path: Path) -> None:
    from scribesim.curriculum.glyph_join import _write_snapshot_panel

    _write_snapshot_panel(image_paths, output_path, columns=3)


def _write_dashboard_markdown(
    path: Path,
    *,
    manifest: FolioBenchManifest,
    report: StageReport,
    decision: FolioPromotionDecision,
    cases: list[dict[str, object]],
) -> None:
    lines = [
        f"# TD-014 Folio Rollout Bench: {manifest.checkpoint_id}",
        "",
        f"- Gate: {'PASS' if report.gate.passed else 'FAIL'}",
        f"- Promotion decision: {'PROMOTE' if decision.promotable else 'KEEP EXPERIMENTAL'}",
        "",
        "## Summary Metrics",
    ]
    for key in sorted(report.metrics):
        lines.append(f"- `{key}`: {report.metrics[key]:.4f}")
    if report.gate.failures:
        lines.append("")
        lines.append("## Gate Failures")
        for failure in report.gate.failures:
            lines.append(f"- `{failure.metric}`: {failure.reason}")
    if decision.reasons:
        lines.append("")
        lines.append("## Decision Reasons")
        for reason in decision.reasons:
            lines.append(f"- {reason}")
    if decision.winning_cases:
        lines.append("")
        lines.append("## Winning Cases")
        for name in decision.winning_cases:
            lines.append(f"- `{name}`")
    lines.append("")
    lines.append("## Representative Cases")
    for case in cases:
        lines.append(
            f"- `{case['name']}`: deterministic={case['deterministic_passed']}, "
            f"contracts={case['downstream_contract_pass_rate']:.4f}, "
            f"weather={case['weather_acceptance']:.4f}, "
            f"delta={case['mean_readability_regression_delta']:.4f}, "
            f"continuity={case['mean_join_continuity_score']:.4f}, "
            f"organicness_gain_vs_plain={case['organicness_gain_vs_plain']:.4f}, "
            f"exact_coverage={case['exact_character_coverage']:.4f}, "
            f"alias_count={case['alias_substitution_count']:.0f}, "
            f"resolution={case.get('resolution_status', 'unknown')}, "
            f"trajectory={case.get('guided_render_trajectory_mode', 'unknown')}"
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n")


def run_folio_regression_bench(
    output_dir: Path | str,
    *,
    manifest_path: Path | str = DEFAULT_FOLIO_BENCH_MANIFEST_PATH,
    profile: HandProfile | None = None,
) -> FolioBenchRunResult:
    """Run the final guided folio regression bench and record a promotion decision."""

    manifest = load_folio_bench_manifest(manifest_path)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    base_profile = copy.deepcopy(profile or HandProfile())
    base_profile = _load_line_checkpoint_profile(
        base_profile,
        word_line_manifest_path=manifest.word_line_manifest_path,
        word_line_candidate_name=manifest.word_line_candidate_name,
    )
    base_profile = _apply_overrides(base_profile, manifest.base_profile_overrides)
    weather_profile = load_weather_profile(Path(manifest.weather_profile_path))

    case_rows: list[dict[str, object]] = []
    for case in manifest.cases:
        case_dir = output_root / case.name
        case_dir.mkdir(parents=True, exist_ok=True)
        case_profile = _apply_overrides(copy.deepcopy(base_profile), case.profile_overrides)
        folio = _load_folio_dict(case)
        params = case_profile.to_v1()
        layout = place(folio, params, profile=case_profile)

        try:
            guided_a, guided_heat_a, guided_meta_a = _render_guided_page(
                folio,
                case_profile,
                layout,
                guided_supersample=manifest.guided_supersample,
                exact_symbols=True,
            )
            guided_b, guided_heat_b, guided_meta_b = _render_guided_page(
                folio,
                case_profile,
                layout,
                guided_supersample=manifest.guided_supersample,
                exact_symbols=True,
            )
        except GuidedFolioResolutionError as exc:
            resolution = {
                "glyph_count": sum(status.glyph_count for status in exc.line_statuses),
                "exact_character_coverage": (
                    sum(round(status.exact_character_coverage * status.glyph_count) for status in exc.line_statuses)
                    / max(sum(status.glyph_count for status in exc.line_statuses), 1)
                ),
                "alias_substitution_count": sum(status.alias_substitution_count for status in exc.line_statuses),
                "normalized_substitution_count": sum(
                    status.normalized_substitution_count for status in exc.line_statuses
                ),
                "exact_only_passed": False,
                "line_statuses": [
                    {
                        "line_index": status.line_index,
                        "line_text": status.line_text,
                        "glyph_count": status.glyph_count,
                        "exact_character_coverage": status.exact_character_coverage,
                        "alias_substitution_count": status.alias_substitution_count,
                        "normalized_substitution_count": status.normalized_substitution_count,
                        "exact_only_passed": status.exact_only_passed,
                        "non_exact_symbols": list(status.non_exact_symbols),
                        "resolution_error": status.resolution_error,
                    }
                    for status in exc.line_statuses
                ],
            }
            row = {
                "name": case.name,
                "folio_id": folio.get("id", case.folio_id),
                "description": case.description,
                "line_count": len(folio.get("lines", [])),
                "deterministic_passed": False,
                "downstream_contract_pass_rate": 0.0,
                "weather_acceptance": 0.0,
                "guided_pressure_dynamic_range": 0.0,
                "plain_pressure_dynamic_range": 0.0,
                "evo_pressure_dynamic_range": 0.0,
                "organicness_gain_vs_plain": -1.0,
                "organicness_win": 0.0,
                "guided_ocr_proxy_vs_evo_page": 0.0,
                "guided_page_path": None,
                "guided_heat_path": None,
                "guided_aligned_page_path": None,
                "evo_page_path": None,
                "plain_page_path": None,
                "page_xml_path": None,
                "panel_path": None,
                "diff_guided_evo_path": None,
                "diff_guided_plain_path": None,
                "diff_guided_actual_aligned_path": None,
                "contract_checks": {
                    "page_xml_parseable": False,
                    "page_xml_width_matches": False,
                    "page_xml_height_matches": False,
                },
                "mean_guided_ocr_proxy_score": 0.0,
                "mean_spacing_cv": 1.0,
                "mean_baseline_drift_ratio": 1.0,
                "mean_join_continuity_score": 0.0,
                "exact_character_coverage": float(resolution["exact_character_coverage"]),
                "alias_substitution_count": float(resolution["alias_substitution_count"]),
                "normalized_substitution_count": float(resolution["normalized_substitution_count"]),
                "mean_readability_regression_delta": 1.0,
                "resolution_status": "failed",
                "resolution": resolution,
                "resolution_error": str(exc),
                "guided_render_trajectory_mode": "actual",
            }
            (case_dir / "summary.json").write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
            case_rows.append(row)
            continue
        evo_page, evo_heat = _render_evo_page(
            folio,
            case_profile,
            layout,
            evolve=manifest.evo_evolve,
            quality=manifest.evo_quality,
        )
        plain_page, plain_heat = _render_plain_page(case_dir / "plain", folio, case_profile, layout)

        guided_page_path = _save_rgb(case_dir / "guided.png", guided_a)
        guided_heat_path = _save_gray(case_dir / "guided_heat.png", guided_heat_a)
        guided_aligned_page_path = _save_rgb(case_dir / "guided_aligned.png", guided_meta_a["aligned_page"])
        _save_gray(case_dir / "guided_aligned_heat.png", guided_meta_a["aligned_heat"])
        evo_page_path = _save_rgb(case_dir / "evo.png", evo_page)
        plain_page_path = _save_rgb(case_dir / "plain.png", plain_page)
        _save_gray(case_dir / "evo_heat.png", evo_heat)
        _save_gray(case_dir / "plain_heat.png", plain_heat)
        diff_guided_evo = _save_diff(case_dir / "guided_vs_evo_diff.png", guided_a, evo_page)
        diff_guided_plain = _save_diff(case_dir / "guided_vs_plain_diff.png", guided_a, plain_page)
        diff_guided_actual_aligned = _save_diff(
            case_dir / "guided_actual_vs_aligned_diff.png",
            guided_a,
            guided_meta_a["aligned_page"],
        )

        page_xml_path = generate_page_xml(layout, case_dir / "page.xml", folio_id=folio.get("id", case.folio_id))
        page_root = ET.fromstring(page_xml_path.read_text())
        page_node = page_root.find("{http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15}Page")
        contract_checks = {
            "page_xml_parseable": page_node is not None,
            "page_xml_width_matches": page_node is not None and int(page_node.attrib["imageWidth"]) == guided_a.shape[1],
            "page_xml_height_matches": page_node is not None and int(page_node.attrib["imageHeight"]) == guided_a.shape[0],
        }
        weather_ok = 0.0
        try:
            weather_result = composite_folio(
                Image.fromarray(guided_a, mode="RGB"),
                Image.fromarray(guided_heat_a, mode="L"),
                folio.get("id", case.folio_id),
                weather_profile,
                stock=stock_for_folio(folio.get("id", case.folio_id)),
                seed=0,
            )
            weather_ok = float(
                weather_result.image.size == (guided_a.shape[1], guided_a.shape[0])
            )
        except Exception:
            weather_ok = 0.0

        line_metrics = _case_line_metrics(
            [line.get("text", "") for line in folio.get("lines", [])],
            profile=case_profile,
            proof_dpi=manifest.proof_dpi,
            proof_supersample=manifest.proof_supersample,
            dt=manifest.dt,
            evo_evolve=manifest.evo_evolve,
            exact_symbols=True,
        )
        organicness_gain = pressure_dynamic_range_score(guided_heat_a) - pressure_dynamic_range_score(plain_heat)
        organicness_win = float(
            organicness_gain > 0.0 and line_metrics["mean_readability_regression_delta"] <= 0.05
        )
        guided_page_for_proxy, evo_page_for_proxy = _align_common_canvas(guided_a, evo_page)
        row = {
            "name": case.name,
            "folio_id": folio.get("id", case.folio_id),
            "description": case.description,
            "line_count": len(folio.get("lines", [])),
            "deterministic_passed": bool(
                np.array_equal(guided_a, guided_b) and np.array_equal(guided_heat_a, guided_heat_b)
            ),
            "downstream_contract_pass_rate": downstream_contract_pass_rate(contract_checks),
            "weather_acceptance": weather_ok,
            "guided_pressure_dynamic_range": pressure_dynamic_range_score(guided_heat_a),
            "plain_pressure_dynamic_range": pressure_dynamic_range_score(plain_heat),
            "evo_pressure_dynamic_range": pressure_dynamic_range_score(evo_heat),
            "organicness_gain_vs_plain": organicness_gain,
            "organicness_win": organicness_win,
            "guided_ocr_proxy_vs_evo_page": ocr_proxy_score(guided_page_for_proxy, evo_page_for_proxy),
            "guided_page_path": guided_page_path.as_posix(),
            "guided_heat_path": guided_heat_path.as_posix(),
            "guided_aligned_page_path": guided_aligned_page_path.as_posix(),
            "evo_page_path": evo_page_path.as_posix(),
            "plain_page_path": plain_page_path.as_posix(),
            "page_xml_path": page_xml_path.as_posix(),
            "panel_path": (case_dir / "panel.png").as_posix(),
            "diff_guided_evo_path": diff_guided_evo.as_posix(),
            "diff_guided_plain_path": diff_guided_plain.as_posix(),
            "diff_guided_actual_aligned_path": diff_guided_actual_aligned.as_posix(),
            "contract_checks": contract_checks,
            "resolution_status": "exact" if guided_meta_a["resolution"]["exact_only_passed"] else "non_exact",
            "resolution": guided_meta_a["resolution"],
            "guided_render_trajectory_mode": guided_meta_a["render_trajectory_mode"],
            **line_metrics,
        }
        _build_case_panel(
            [
                guided_page_path,
                guided_aligned_page_path,
                evo_page_path,
                plain_page_path,
                diff_guided_evo,
                diff_guided_actual_aligned,
            ],
            Path(row["panel_path"]),
        )
        (case_dir / "summary.json").write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
        case_rows.append(row)

    summary_metrics = {
        "deterministic_pass_rate": float(
            sum(1.0 if row["deterministic_passed"] else 0.0 for row in case_rows) / max(len(case_rows), 1)
        ),
        "downstream_contract_pass_rate": float(
            sum(float(row["downstream_contract_pass_rate"]) for row in case_rows) / max(len(case_rows), 1)
        ),
        "weather_acceptance": float(
            sum(float(row["weather_acceptance"]) for row in case_rows) / max(len(case_rows), 1)
        ),
        "readability_regression_delta": float(
            sum(float(row["mean_readability_regression_delta"]) for row in case_rows) / max(len(case_rows), 1)
        ),
        "mean_join_continuity_score": float(
            sum(float(row["mean_join_continuity_score"]) for row in case_rows) / max(len(case_rows), 1)
        ),
        "exact_character_coverage": float(
            sum(float(row["exact_character_coverage"]) for row in case_rows) / max(len(case_rows), 1)
        ),
        "alias_substitution_count": float(
            sum(float(row["alias_substitution_count"]) for row in case_rows)
        ),
        "normalized_substitution_count": float(
            sum(float(row["normalized_substitution_count"]) for row in case_rows)
        ),
        "mean_spacing_cv": float(
            sum(float(row["mean_spacing_cv"]) for row in case_rows) / max(len(case_rows), 1)
        ),
        "mean_baseline_drift_ratio": float(
            sum(float(row["mean_baseline_drift_ratio"]) for row in case_rows) / max(len(case_rows), 1)
        ),
        "organicness_win_rate": float(
            sum(float(row["organicness_win"]) for row in case_rows) / max(len(case_rows), 1)
        ),
    }
    gate = evaluate_gate("folio", summary_metrics)
    winning_cases = tuple(
        row["name"]
        for row in case_rows
        if float(row["organicness_win"]) >= 1.0 and float(row["mean_join_continuity_score"]) >= 0.90
    )
    reasons: list[str] = []
    if not gate.passed:
        reasons.append("folio hard gates failed; guided renderer remains experimental")
    if not winning_cases:
        reasons.append("no representative folio beat the plain baseline on organicness without readability regression")
    if gate.passed and winning_cases:
        reasons.append("guided folio path cleared the rollout bench and is promotable")
    decision = FolioPromotionDecision(
        checkpoint_id=manifest.checkpoint_id,
        promotable=bool(gate.passed and winning_cases),
        reasons=tuple(reasons),
        winning_cases=winning_cases,
        summary_metrics=summary_metrics,
    )
    report = StageReport(
        stage=manifest.stage_id,
        metrics=summary_metrics,
        gate=gate,
        notes=decision.reasons,
    )
    write_stage_report(report, output_root)
    dashboard_payload = {
        "manifest": asdict(manifest),
        "summary_metrics": summary_metrics,
        "gate": asdict(gate),
        "decision": asdict(decision),
        "cases": case_rows,
    }
    (output_root / "dashboard.json").write_text(json.dumps(dashboard_payload, indent=2, sort_keys=True) + "\n")
    _write_dashboard_markdown(
        output_root / "dashboard.md",
        manifest=manifest,
        report=report,
        decision=decision,
        cases=case_rows,
    )
    (output_root / "promotion_decision.json").write_text(
        json.dumps(asdict(decision), indent=2, sort_keys=True) + "\n"
    )
    (output_root / "promotion_decision.md").write_text(
        "# TD-014 Promotion Decision\n\n"
        f"- Checkpoint: `{decision.checkpoint_id}`\n"
        f"- Decision: {'PROMOTE' if decision.promotable else 'KEEP EXPERIMENTAL'}\n"
        + "\n".join(f"- {reason}" for reason in decision.reasons)
        + "\n"
    )
    return FolioBenchRunResult(
        passed=decision.promotable,
        manifest=manifest,
        decision=decision,
        output_dir=output_root.as_posix(),
    )
