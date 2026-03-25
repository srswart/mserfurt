"""Glyph and join curriculum promotion runner for TD-014."""

from __future__ import annotations

import copy
import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import tomllib

from PIL import Image, ImageDraw

from scribesim.hand.profile import HandProfile
from scribesim.handflow import GuidedHandFlowController, render_trajectory_proof
from scribesim.handvalidate import (
    StageReport,
    continuity_score,
    dataset_admission_metrics,
    dtw_centerline_distance,
    evaluate_dataset_policy,
    evaluate_gate,
    forced_lift_count,
    template_score,
    thick_thin_ratio_error,
    uncontrolled_exit_count,
    write_stage_report,
)
from scribesim.handvalidate.model import TrajectorySample
from scribesim.pathguide import (
    STARTER_ALPHABET_V1_JOIN_SCHEDULES,
    load_starter_alphabet_v1_guides,
)
from scribesim.render.nib import PhysicsNib, mark_width

from .model import (
    GlyphJoinCandidate,
    GlyphJoinCheckpoint,
    GlyphJoinManifest,
    GlyphJoinRunResult,
    PrimitiveManifest,
)
from .primitive import load_primitive_manifest


DEFAULT_GLYPH_JOIN_MANIFEST_PATH = Path("shared/training/handsim/glyph_join/manifest.toml")
DEFAULT_GLYPH_JOIN_DATASET_SUMMARY_PATH = Path("shared/training/handsim/glyph_join/dataset_summary.toml")


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
    return profile.apply_delta(_flatten_overrides(overrides))


def load_glyph_join_manifest(path: Path | str = DEFAULT_GLYPH_JOIN_MANIFEST_PATH) -> GlyphJoinManifest:
    raw = tomllib.loads(Path(path).read_text())
    candidates = tuple(
        GlyphJoinCandidate(
            name=str(candidate["name"]),
            description=str(candidate.get("description", "")),
            profile_overrides=dict(candidate.get("profile_overrides", {})),
        )
        for candidate in raw.get("candidates", [])
    )
    return GlyphJoinManifest(
        stage_id=str(raw["stage_id"]),
        checkpoint_id=str(raw["checkpoint_id"]),
        dataset_policy=str(raw.get("dataset_policy", "promotion")),
        primitive_manifest_path=str(raw["primitive_manifest_path"]),
        primitive_candidate_name=str(raw.get("primitive_candidate_name", "primitive_v1_tuned")),
        training_glyphs=tuple(str(name) for name in raw.get("training_glyphs", [])),
        promotion_glyphs=tuple(str(name) for name in raw.get("promotion_glyphs", [])),
        training_joins=tuple(str(name) for name in raw.get("training_joins", [])),
        promotion_joins=tuple(str(name) for name in raw.get("promotion_joins", [])),
        proof_dpi=int(raw.get("proof_dpi", 220)),
        proof_supersample=int(raw.get("proof_supersample", 3)),
        dt=float(raw.get("dt", 0.002)),
        base_profile_overrides=dict(raw.get("base_profile_overrides", {})),
        candidates=candidates,
    )


def _load_primitive_profile(
    base_profile: HandProfile,
    *,
    primitive_manifest_path: Path | str,
    primitive_candidate_name: str,
) -> HandProfile:
    primitive_manifest: PrimitiveManifest = load_primitive_manifest(primitive_manifest_path)
    profile = copy.deepcopy(base_profile)
    if primitive_manifest.base_profile_overrides:
        profile = _apply_overrides(profile, primitive_manifest.base_profile_overrides)
    for candidate in primitive_manifest.candidates:
        if candidate.name == primitive_candidate_name:
            return _apply_overrides(profile, candidate.profile_overrides)
    raise KeyError(f"unknown primitive candidate: {primitive_candidate_name}")


def _write_snapshot_panel(
    image_paths: list[Path],
    output_path: Path,
    *,
    columns: int = 4,
    cell_padding: int = 16,
    title_height: int = 28,
) -> None:
    if not image_paths:
        raise ValueError("image_paths must be non-empty")

    opened = [(path.stem, Image.open(path).convert("RGB")) for path in image_paths]
    cell_w = max(image.width for _, image in opened)
    cell_h = max(image.height for _, image in opened)
    rows = (len(opened) + columns - 1) // columns
    panel = Image.new(
        "RGB",
        (
            columns * (cell_w + cell_padding) + cell_padding,
            rows * (cell_h + title_height + cell_padding) + cell_padding,
        ),
        (248, 242, 229),
    )
    draw = ImageDraw.Draw(panel)

    for idx, (label, image) in enumerate(opened):
        row = idx // columns
        col = idx % columns
        x = cell_padding + col * (cell_w + cell_padding)
        y = cell_padding + row * (cell_h + title_height + cell_padding)
        draw.text((x, y), label, fill=(40, 30, 20))
        panel.paste(image, (x, y + title_height))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.save(output_path, format="PNG")
    for _, image in opened:
        image.close()


def _nominal_trajectory(guide, profile: HandProfile) -> tuple[TrajectorySample, ...]:
    nib = PhysicsNib(
        width_mm=profile.nib.width_mm,
        angle_deg=profile.nib.angle_deg,
        flexibility=profile.nib.flexibility,
        cut_quality=profile.nib.cut_quality,
        attack_pressure_multiplier=profile.nib.attack_pressure_multiplier,
        release_taper_length=profile.nib.release_taper_length,
    )
    contact_indices = [idx for idx, sample in enumerate(guide.samples) if sample.contact]
    index_lookup = {sample_idx: contact_rank for contact_rank, sample_idx in enumerate(contact_indices)}
    total_contact = max(len(contact_indices) - 1, 1)

    trajectory: list[TrajectorySample] = []
    for idx, sample in enumerate(guide.samples):
        width_mm = None
        pressure = 0.0
        if sample.contact:
            contact_rank = index_lookup[idx]
            direction_deg = math.degrees(math.atan2(sample.tangent_dy, sample.tangent_dx))
            pressure = sample.pressure_nominal
            width_mm = mark_width(
                nib,
                direction_deg=direction_deg,
                pressure=pressure,
                t=contact_rank / total_contact,
            )
        trajectory.append(
            TrajectorySample(
                x_mm=sample.x_mm,
                y_mm=sample.y_mm,
                contact=sample.contact,
                width_mm=width_mm,
                pressure=pressure if sample.contact else 0.0,
            )
        )
    return tuple(trajectory)


def _candidate_score(entries: list[dict[str, object]]) -> float:
    score = 0.0
    for entry in entries:
        metrics = entry["metrics"]
        score += float(metrics.get("template_score", 0.0)) * 6.0
        score += float(metrics.get("continuity_score", 0.0)) * 5.0
        score += max(0.0, 1.0 - float(metrics.get("dtw_centerline_distance", 1.0))) * 3.0
        score += max(0.0, 1.0 - float(metrics.get("thick_thin_ratio_error", 1.0))) * 2.0
        score -= float(metrics.get("forced_lift_count", 0.0)) * 8.0
        score -= float(metrics.get("uncontrolled_exit_count", 0.0)) * 12.0
        if entry["passed"]:
            score += 20.0
    return score


def _render_reference_library(guides, profile: HandProfile, *, dpi: int, supersample: int) -> dict[str, object]:
    return {
        symbol: render_trajectory_proof(
            _nominal_trajectory(guide, profile),
            profile=profile,
            dpi=dpi,
            supersample=supersample,
            bounds_mm=_guide_render_bounds(guide),
        )
        for symbol, guide in guides.items()
    }


def _guide_render_bounds(guide, *, margin_mm: float = 1.0) -> tuple[float, float, float, float]:
    contact = [sample for sample in guide.samples if sample.contact]
    x_min = min(sample.x_mm for sample in contact) - margin_mm
    x_max = max(sample.x_mm for sample in contact) + margin_mm
    y_min = min(sample.y_mm for sample in contact) - margin_mm
    y_max = max(sample.y_mm for sample in contact) + margin_mm
    return (x_min, x_max, y_min, y_max)


def _write_join_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    lines = [
        "# TD-014 Join Continuity Report",
        "",
        "| Join | Continuity | Forced Lifts | Uncontrolled Exits | Pass |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['symbol']}` | {row['continuity_score']:.4f} | {int(row['forced_lift_count'])} | "
            f"{int(row['uncontrolled_exit_count'])} | {'PASS' if row['passed'] else 'FAIL'} |"
        )
    lines.append("")
    path.write_text("\n".join(lines))


def _write_recognition_markdown(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# TD-014 Glyph Recognition Summary",
        "",
        f"- Accuracy: `{float(payload['accuracy']):.4f}`",
        "",
        "## Predictions",
    ]
    for row in payload["rows"]:
        lines.append(
            f"- `{row['actual']}` -> `{row['predicted']}` "
            f"(score={float(row['score']):.4f}, gate={'PASS' if row['passed'] else 'FAIL'})"
        )
    lines.append("")
    path.write_text("\n".join(lines))


def _write_curriculum_summary(
    path: Path,
    *,
    manifest: GlyphJoinManifest,
    dataset_metrics: dict[str, float],
    dataset_policy_name: str,
    dataset_policy_passed: bool,
    dataset_policy_reasons: tuple[str, ...],
    candidates: list[dict[str, object]],
    selected_candidate: str | None,
) -> None:
    lines = [
        f"# TD-014 Glyph/Join Curriculum: {manifest.checkpoint_id}",
        "",
        f"- Stage: `{manifest.stage_id}`",
        f"- Dataset policy `{dataset_policy_name}`: {'PASS' if dataset_policy_passed else 'FAIL'}",
        f"- Selected candidate: `{selected_candidate}`" if selected_candidate else "- Selected candidate: none",
        "",
        "## Dataset Admission",
    ]
    for key in sorted(dataset_metrics):
        lines.append(f"- `{key}`: {dataset_metrics[key]:.4f}")
    if dataset_policy_reasons:
        lines.append("")
        lines.append("## Dataset Policy Reasons")
        for reason in dataset_policy_reasons:
            lines.append(f"- {reason}")
    lines.append("")
    lines.append("## Candidates")
    for candidate in candidates:
        lines.append(
            f"- `{candidate['name']}`: {'PASS' if candidate['passed'] else 'FAIL'} "
            f"(score={candidate['score']:.3f})"
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n")


def run_glyph_join_curriculum(
    output_dir: Path | str,
    *,
    manifest_path: Path | str = DEFAULT_GLYPH_JOIN_MANIFEST_PATH,
    profile: HandProfile | None = None,
    exploratory: bool = False,
) -> GlyphJoinRunResult:
    """Run glyph/join promotion and freeze glyph-join-v1 on gate pass."""

    manifest = load_glyph_join_manifest(manifest_path)
    base_profile = copy.deepcopy(profile or HandProfile())
    base_profile = _load_primitive_profile(
        base_profile,
        primitive_manifest_path=manifest.primitive_manifest_path,
        primitive_candidate_name=manifest.primitive_candidate_name,
    )
    if manifest.base_profile_overrides:
        base_profile = _apply_overrides(base_profile, manifest.base_profile_overrides)

    all_guides = load_starter_alphabet_v1_guides()
    promotion_symbols = (*manifest.promotion_glyphs, *manifest.promotion_joins)
    promotion_guides = {symbol: all_guides[symbol] for symbol in promotion_symbols}

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    dataset_policy_name = "exploratory" if exploratory else manifest.dataset_policy
    dataset_decision = evaluate_dataset_policy(
        list(promotion_guides.values()),
        policy_name=dataset_policy_name,
    )
    dataset_metrics = dataset_admission_metrics(promotion_guides.values())
    dataset_summary = {
        "policy": dataset_policy_name,
        "passed": dataset_decision.passed,
        "reasons": list(dataset_decision.reasons),
        "metrics": dataset_metrics,
        "promotion_symbols": list(promotion_symbols),
        "accepted_tier_only": all(guide.accepted_only for guide in promotion_guides.values()),
    }
    (output_root / "dataset_summary.json").write_text(json.dumps(dataset_summary, indent=2, sort_keys=True) + "\n")

    candidate_results: list[dict[str, object]] = []
    best_candidate: dict[str, object] | None = None

    for candidate in manifest.candidates:
        candidate_profile = _apply_overrides(base_profile, candidate.profile_overrides)
        controller = GuidedHandFlowController(candidate_profile)
        candidate_dir = output_root / "candidates" / candidate.name
        glyph_dir = candidate_dir / "glyphs"
        join_dir = candidate_dir / "joins"
        glyph_dir.mkdir(parents=True, exist_ok=True)
        join_dir.mkdir(parents=True, exist_ok=True)

        promotion_glyph_guides = {symbol: all_guides[symbol] for symbol in manifest.promotion_glyphs}
        promotion_join_guides = {symbol: all_guides[symbol] for symbol in manifest.promotion_joins}
        glyph_reference_images = _render_reference_library(
            promotion_glyph_guides,
            candidate_profile,
            dpi=manifest.proof_dpi,
            supersample=manifest.proof_supersample,
        )

        glyph_entries: list[dict[str, object]] = []
        recognition_rows: list[dict[str, object]] = []
        for symbol, guide in promotion_glyph_guides.items():
            result = controller.simulate_guide(guide, dt=manifest.dt)
            image_path = glyph_dir / f"{symbol}.png"
            bounds = _guide_render_bounds(guide)
            rendered = render_trajectory_proof(
                result.guide_aligned_trajectory,
                profile=candidate_profile,
                output_path=image_path,
                dpi=manifest.proof_dpi,
                supersample=manifest.proof_supersample,
                bounds_mm=bounds,
            )
            reference = glyph_reference_images[symbol]
            nominal = _nominal_trajectory(guide, candidate_profile)
            metrics = {
                "template_score": template_score(rendered, reference),
                "dtw_centerline_distance": dtw_centerline_distance(result.guide_aligned_trajectory, guide),
                "uncontrolled_exit_count": float(uncontrolled_exit_count(result.guide_aligned_trajectory, guide)),
                "thick_thin_ratio_error": thick_thin_ratio_error(
                    [sample.width_mm for sample in result.guide_aligned_trajectory if sample.contact],
                    [sample.width_mm for sample in nominal if sample.contact],
                ),
            }
            gate = evaluate_gate("glyph", metrics)
            report = StageReport(
                stage=f"glyph:{symbol}",
                metrics=metrics,
                gate=gate,
                notes=(f"split={guide.sources[0].split}",),
            )
            write_stage_report(report, glyph_dir)
            scores = {
                ref_symbol: template_score(rendered, ref_img)
                for ref_symbol, ref_img in glyph_reference_images.items()
            }
            predicted_symbol = max(scores.items(), key=lambda item: item[1])[0]
            recognition_rows.append(
                {
                    "actual": symbol,
                    "predicted": predicted_symbol,
                    "score": scores[predicted_symbol],
                    "passed": gate.passed,
                }
            )
            glyph_entries.append(
                {
                    "symbol": symbol,
                    "kind": "glyph",
                    "passed": gate.passed,
                    "metrics": metrics,
                    "image_path": image_path.as_posix(),
                }
            )

        join_entries: list[dict[str, object]] = []
        join_rows: list[dict[str, object]] = []
        for symbol, guide in promotion_join_guides.items():
            result = controller.simulate_guide(guide, dt=manifest.dt)
            image_path = join_dir / f"{symbol.replace('->', '_to_')}.png"
            render_trajectory_proof(
                result.guide_aligned_trajectory,
                profile=candidate_profile,
                output_path=image_path,
                dpi=manifest.proof_dpi,
                supersample=manifest.proof_supersample,
                bounds_mm=_guide_render_bounds(guide),
            )
            join_schedule = STARTER_ALPHABET_V1_JOIN_SCHEDULES.get(symbol, "contact_only")
            forced_lifts = (
                float(forced_lift_count(result.guide_aligned_trajectory, guide))
                if join_schedule == "contact_only"
                else 0.0
            )
            metrics = {
                "continuity_score": continuity_score(result.guide_aligned_trajectory, guide),
                "forced_lift_count": forced_lifts,
                "uncontrolled_exit_count": float(uncontrolled_exit_count(result.guide_aligned_trajectory, guide)),
                "dtw_centerline_distance": dtw_centerline_distance(result.guide_aligned_trajectory, guide),
            }
            gate = evaluate_gate("join", metrics)
            report = StageReport(
                stage=f"join:{symbol}",
                metrics=metrics,
                gate=gate,
                notes=(f"split={guide.sources[0].split}",),
            )
            write_stage_report(report, join_dir)
            join_rows.append(
                {
                    "symbol": symbol,
                    "continuity_score": metrics["continuity_score"],
                    "forced_lift_count": metrics["forced_lift_count"],
                    "uncontrolled_exit_count": metrics["uncontrolled_exit_count"],
                    "passed": gate.passed,
                }
            )
            join_entries.append(
                {
                    "symbol": symbol,
                    "kind": "join",
                    "passed": gate.passed,
                    "metrics": metrics,
                    "image_path": image_path.as_posix(),
                }
            )

        recognition_accuracy = sum(
            int(row["actual"] == row["predicted"])
            for row in recognition_rows
        ) / max(len(recognition_rows), 1)
        confusion_matrix: dict[str, dict[str, int]] = {}
        for actual in manifest.promotion_glyphs:
            confusion_matrix[actual] = {predicted: 0 for predicted in manifest.promotion_glyphs}
        for row in recognition_rows:
            confusion_matrix[row["actual"]][row["predicted"]] += 1
        recognition_summary = {
            "accuracy": recognition_accuracy,
            "rows": recognition_rows,
            "confusion_matrix": confusion_matrix,
        }
        (candidate_dir / "recognition_summary.json").write_text(
            json.dumps(recognition_summary, indent=2, sort_keys=True) + "\n"
        )
        _write_recognition_markdown(candidate_dir / "recognition_summary.md", recognition_summary)

        join_summary = {
            "rows": join_rows,
            "mean_continuity_score": sum(row["continuity_score"] for row in join_rows) / max(len(join_rows), 1),
            "forced_lift_total": sum(int(row["forced_lift_count"]) for row in join_rows),
            "uncontrolled_exit_total": sum(int(row["uncontrolled_exit_count"]) for row in join_rows),
        }
        (candidate_dir / "join_continuity_report.json").write_text(
            json.dumps(join_summary, indent=2, sort_keys=True) + "\n"
        )
        _write_join_markdown(candidate_dir / "join_continuity_report.md", join_rows)

        all_entries = glyph_entries + join_entries
        ranked = sorted(
            all_entries,
            key=lambda entry: (entry["passed"], -entry["metrics"].get("dtw_centerline_distance", 1.0), entry["metrics"].get("template_score", entry["metrics"].get("continuity_score", 0.0))),
            reverse=True,
        )
        good_paths = [Path(entry["image_path"]) for entry in ranked if entry["passed"]][:4]
        bad_paths = [Path(entry["image_path"]) for entry in ranked if not entry["passed"]][:4]
        if not good_paths:
            good_paths = [Path(entry["image_path"]) for entry in ranked[:4]]
        if not bad_paths:
            bad_paths = [Path(entry["image_path"]) for entry in ranked[-4:]]
        _write_snapshot_panel(good_paths, candidate_dir / "good_examples_panel.png")
        _write_snapshot_panel(bad_paths, candidate_dir / "bad_examples_panel.png")

        passed = dataset_decision.passed and all(entry["passed"] for entry in all_entries)
        entry = {
            "name": candidate.name,
            "description": candidate.description,
            "passed": passed,
            "score": _candidate_score(all_entries),
            "candidate_dir": candidate_dir.as_posix(),
            "profile_flat": candidate_profile.to_flat_dict(),
            "recognition_summary_path": (candidate_dir / "recognition_summary.json").as_posix(),
            "join_report_path": (candidate_dir / "join_continuity_report.json").as_posix(),
        }
        candidate_results.append(entry)
        if best_candidate is None or (entry["passed"], entry["score"]) > (
            best_candidate["passed"],
            best_candidate["score"],
        ):
            best_candidate = entry

    summary_payload = {
        "manifest": asdict(manifest),
        "dataset_policy": dataset_summary,
        "candidates": candidate_results,
        "selected_candidate": best_candidate["name"] if best_candidate else None,
    }
    (output_root / "curriculum_summary.json").write_text(
        json.dumps(summary_payload, indent=2, sort_keys=True) + "\n"
    )
    _write_curriculum_summary(
        output_root / "curriculum_summary.md",
        manifest=manifest,
        dataset_metrics=dataset_metrics,
        dataset_policy_name=dataset_policy_name,
        dataset_policy_passed=dataset_decision.passed,
        dataset_policy_reasons=dataset_decision.reasons,
        candidates=candidate_results,
        selected_candidate=best_candidate["name"] if best_candidate else None,
    )

    checkpoint_path: Path | None = None
    if best_candidate is not None and bool(best_candidate["passed"]):
        checkpoint = GlyphJoinCheckpoint(
            checkpoint_id=manifest.checkpoint_id,
            candidate_name=str(best_candidate["name"]),
            manifest_path=Path(manifest_path).as_posix(),
            primitive_manifest_path=manifest.primitive_manifest_path,
            primitive_candidate_name=manifest.primitive_candidate_name,
            dataset_policy=dataset_policy_name,
            passed=True,
            promotion_glyphs=manifest.promotion_glyphs,
            promotion_joins=manifest.promotion_joins,
            profile_flat=dict(best_candidate["profile_flat"]),
        )
        checkpoint_path = output_root / "checkpoints" / manifest.checkpoint_id / "checkpoint.json"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(
            json.dumps(
                {
                    **asdict(checkpoint),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    return GlyphJoinRunResult(
        passed=bool(best_candidate and best_candidate["passed"]),
        manifest=manifest,
        selected_candidate=str(best_candidate["name"]) if best_candidate else None,
        checkpoint_path=checkpoint_path.as_posix() if checkpoint_path else None,
        output_dir=output_root.as_posix(),
    )
