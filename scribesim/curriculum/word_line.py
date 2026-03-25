"""Word and line curriculum promotion runner for TD-014."""

from __future__ import annotations

import copy
import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import tomllib

from scribesim.evo.compose import render_line
from scribesim.hand.profile import HandProfile
from scribesim.handflow import (
    GuidedHandFlowController,
    build_line_session,
    render_trajectory_proof,
    load_word_guide_catalog,
)
from scribesim.handvalidate import (
    StageReport,
    dataset_admission_metrics,
    evaluate_dataset_policy,
    evaluate_gate,
    ocr_proxy_score,
    readability_regression_delta,
    spacing_cv,
    write_stage_report,
    x_height_stability_cv,
)
from scribesim.handvalidate.model import TrajectorySample

from .glyph_join import (
    _apply_overrides,
    _guide_render_bounds,
    _nominal_trajectory,
    _write_snapshot_panel,
    _load_primitive_profile,
    load_glyph_join_manifest,
)
from .model import (
    GlyphJoinManifest,
    WordLineCandidate,
    WordLineCheckpoint,
    WordLineManifest,
    WordLineRunResult,
)


DEFAULT_WORD_LINE_MANIFEST_PATH = Path("shared/training/handsim/word_line/manifest.toml")
DEFAULT_WORD_LINE_DATASET_SUMMARY_PATH = Path("shared/training/handsim/word_line/dataset_summary.toml")


def load_word_line_manifest(path: Path | str = DEFAULT_WORD_LINE_MANIFEST_PATH) -> WordLineManifest:
    raw = tomllib.loads(Path(path).read_text())
    candidates = tuple(
        WordLineCandidate(
            name=str(candidate["name"]),
            description=str(candidate.get("description", "")),
            profile_overrides=dict(candidate.get("profile_overrides", {})),
        )
        for candidate in raw.get("candidates", [])
    )
    return WordLineManifest(
        stage_id=str(raw["stage_id"]),
        checkpoint_id=str(raw["checkpoint_id"]),
        dataset_policy=str(raw.get("dataset_policy", "promotion")),
        glyph_join_manifest_path=str(raw["glyph_join_manifest_path"]),
        glyph_join_candidate_name=str(raw.get("glyph_join_candidate_name", "glyph_join_v1_tuned")),
        proof_entries=tuple(str(text) for text in raw.get("proof_entries", [])),
        training_lines=tuple(str(text) for text in raw.get("training_lines", [])),
        promotion_lines=tuple(str(text) for text in raw.get("promotion_lines", [])),
        proof_dpi=int(raw.get("proof_dpi", 220)),
        proof_supersample=int(raw.get("proof_supersample", 3)),
        dt=float(raw.get("dt", 0.002)),
        base_profile_overrides=dict(raw.get("base_profile_overrides", {})),
        candidates=candidates,
    )


def _load_glyph_join_profile(
    base_profile: HandProfile,
    *,
    glyph_join_manifest_path: Path | str,
    glyph_join_candidate_name: str,
) -> HandProfile:
    glyph_join_manifest: GlyphJoinManifest = load_glyph_join_manifest(glyph_join_manifest_path)
    profile = _load_primitive_profile(
        copy.deepcopy(base_profile),
        primitive_manifest_path=glyph_join_manifest.primitive_manifest_path,
        primitive_candidate_name=glyph_join_manifest.primitive_candidate_name,
    )
    if glyph_join_manifest.base_profile_overrides:
        profile = _apply_overrides(profile, glyph_join_manifest.base_profile_overrides)
    for candidate in glyph_join_manifest.candidates:
        if candidate.name == glyph_join_candidate_name:
            return _apply_overrides(profile, candidate.profile_overrides)
    raise KeyError(f"unknown glyph/join candidate: {glyph_join_candidate_name}")


def _slug(text: str) -> str:
    return "_".join(text.split())


def _dedupe_trajectory(samples: list[TrajectorySample]) -> tuple[TrajectorySample, ...]:
    deduped: list[TrajectorySample] = []
    for sample in samples:
        if deduped:
            prev = deduped[-1]
            if (
                math.isclose(prev.x_mm, sample.x_mm, abs_tol=1e-9)
                and math.isclose(prev.y_mm, sample.y_mm, abs_tol=1e-9)
                and prev.contact == sample.contact
            ):
                continue
        deduped.append(sample)
    return tuple(deduped)


def _segment_join_continuity(session_items, segments) -> float:
    scores: list[float] = []
    for item, segment in zip(session_items, segments, strict=False):
        if item.kind != "join":
            continue
        obs_points = [sample for sample in segment.guide_aligned_trajectory if sample.contact]
        ref_points = [sample for sample in item.guide.samples if sample.contact]
        if len(obs_points) < 2 or len(ref_points) < 2:
            continue
        obs_steps = [
            math.dist((obs_points[idx].x_mm, obs_points[idx].y_mm), (obs_points[idx + 1].x_mm, obs_points[idx + 1].y_mm))
            for idx in range(len(obs_points) - 1)
        ]
        ref_steps = [
            math.dist((ref_points[idx].x_mm, ref_points[idx].y_mm), (ref_points[idx + 1].x_mm, ref_points[idx + 1].y_mm))
            for idx in range(len(ref_points) - 1)
        ]
        expected_step = max(sorted(ref_steps)[len(ref_steps) // 2], 1e-6)
        max_step = max(obs_steps)
        gap_penalty = max(0.0, (max_step - expected_step * 1.5) / (expected_step * 3.0))
        last_dx = obs_points[-1].x_mm - obs_points[-2].x_mm
        last_dy = obs_points[-1].y_mm - obs_points[-2].y_mm
        last_norm = math.hypot(last_dx, last_dy)
        if last_norm <= 1e-9:
            tangent_penalty = 1.0
        else:
            last_vec = (last_dx / last_norm, last_dy / last_norm)
            ref_dx, ref_dy = item.guide.exit_tangent
            ref_norm = math.hypot(ref_dx, ref_dy)
            ref_vec = (1.0, 0.0) if ref_norm <= 1e-9 else (ref_dx / ref_norm, ref_dy / ref_norm)
            dot = max(-1.0, min(1.0, last_vec[0] * ref_vec[0] + last_vec[1] * ref_vec[1]))
            tangent_penalty = math.degrees(math.acos(dot)) / 180.0
        scores.append(max(0.0, 1.0 - 0.6 * min(gap_penalty, 1.0) - 0.4 * tangent_penalty))
    if not scores:
        return 1.0
    return sum(scores) / len(scores)


def _line_baseline_drift(aligned: tuple[TrajectorySample, ...], guide) -> float:
    contact_refs = [sample for sample in guide.samples if sample.contact]
    if not contact_refs:
        return 0.0
    baseline_y = min(sample.y_mm for sample in contact_refs)
    baseline_band_limit = baseline_y + guide.x_height_mm * 0.35
    residuals = [
        observed.y_mm - reference.y_mm
        for observed, reference in zip(aligned, guide.samples, strict=False)
        if reference.contact and reference.y_mm <= baseline_band_limit
    ]
    if len(residuals) < 2:
        return 0.0
    mean = sum(residuals) / len(residuals)
    variance = sum((value - mean) ** 2 for value in residuals) / len(residuals)
    return math.sqrt(variance) / max(guide.x_height_mm, 1e-6)


def _word_observed_trajectory(session_items, segments, *, word_index: int) -> tuple[TrajectorySample, ...]:
    samples: list[TrajectorySample] = []
    for item, segment in zip(session_items, segments, strict=False):
        if item.word_index != word_index or item.kind not in {"glyph", "join"}:
            continue
        samples.extend(segment.guide_aligned_trajectory)
    return _dedupe_trajectory(samples)


def _spacing_values(word_guides, session_items, segments) -> list[float]:
    values: list[float] = []
    for prev_word, next_word in zip(word_guides, word_guides[1:], strict=False):
        prev_obs = [sample for sample in _word_observed_trajectory(session_items, segments, word_index=prev_word.word_index) if sample.contact]
        next_obs = [sample for sample in _word_observed_trajectory(session_items, segments, word_index=next_word.word_index) if sample.contact]
        if not prev_obs or not next_obs:
            continue
        values.append(next_obs[0].x_mm - prev_obs[-1].x_mm)
    return values


def _x_height_estimates(word_guides, session_items, segments) -> list[float]:
    values: list[float] = []
    for word_info in word_guides:
        observed = _word_observed_trajectory(session_items, segments, word_index=word_info.word_index)
        if not observed:
            continue
        contact_refs = [sample for sample in word_info.guide.samples if sample.contact]
        if not contact_refs:
            continue
        baseline_y = min(sample.y_mm for sample in contact_refs)
        upper_limit = baseline_y + word_info.guide.x_height_mm * 1.05
        if max(sample.y_mm for sample in contact_refs) > upper_limit:
            continue
        observed_band = [
            observed_sample.y_mm
            for observed_sample, ref_sample in zip(observed, word_info.guide.samples, strict=False)
            if ref_sample.contact and ref_sample.y_mm <= upper_limit
        ]
        reference_band = [
            ref_sample.y_mm
            for ref_sample in word_info.guide.samples
            if ref_sample.contact and ref_sample.y_mm <= upper_limit
        ]
        if len(observed_band) < 2 or len(reference_band) < 2:
            continue
        reference_span = max(reference_band) - min(reference_band)
        if reference_span <= 1e-6:
            continue
        observed_span = max(observed_band) - min(observed_band)
        values.append(observed_span / reference_span)
    return values


def _mean_word_baseline_drift(word_guides, session_items, segments) -> float:
    values: list[float] = []
    for word_info in word_guides:
        observed = _word_observed_trajectory(session_items, segments, word_index=word_info.word_index)
        if not observed:
            continue
        values.append(_line_baseline_drift(observed, word_info.guide))
    if not values:
        return 0.0
    return sum(values) / len(values)


def _build_line_metrics(session_items, result, line_guide, word_guides, rendered, reference) -> dict[str, float]:
    spacing_values = _spacing_values(word_guides, session_items, result.segments)
    x_height_values = _x_height_estimates(word_guides, session_items, result.segments)
    return {
        "ocr_proxy_score": ocr_proxy_score(rendered, reference),
        "spacing_cv": spacing_cv(spacing_values),
        "x_height_stability_cv": x_height_stability_cv(x_height_values),
        "baseline_drift_ratio": _mean_word_baseline_drift(word_guides, session_items, result.segments),
        "join_continuity_score": _segment_join_continuity(session_items, result.segments),
    }


def _write_dataset_admission_markdown(
    path: Path,
    *,
    manifest: WordLineManifest,
    dataset_metrics: dict[str, float],
    dataset_policy_name: str,
    dataset_policy_passed: bool,
    dataset_policy_reasons: tuple[str, ...],
    proof_entries: tuple[str, ...],
    promotion_lines: tuple[str, ...],
) -> None:
    lines = [
        f"# TD-014 Dataset Admission: {manifest.checkpoint_id}",
        "",
        f"- Dataset policy `{dataset_policy_name}`: {'PASS' if dataset_policy_passed else 'FAIL'}",
        "",
        "## Proof Vocabulary",
    ]
    for text in proof_entries:
        lines.append(f"- `{text}`")
    lines.append("")
    lines.append("## Promotion Lines")
    for text in promotion_lines:
        lines.append(f"- `{text}`")
    lines.append("")
    lines.append("## Metrics")
    for key in sorted(dataset_metrics):
        lines.append(f"- `{key}`: {dataset_metrics[key]:.4f}")
    if dataset_policy_reasons:
        lines.append("")
        lines.append("## Policy Reasons")
        for reason in dataset_policy_reasons:
            lines.append(f"- {reason}")
    lines.append("")
    path.write_text("\n".join(lines) + "\n")


def _write_curriculum_summary(
    path: Path,
    *,
    manifest: WordLineManifest,
    dataset_metrics: dict[str, float],
    dataset_policy_name: str,
    dataset_policy_passed: bool,
    dataset_policy_reasons: tuple[str, ...],
    candidates: list[dict[str, object]],
    selected_candidate: str | None,
) -> None:
    lines = [
        f"# TD-014 Word/Line Curriculum: {manifest.checkpoint_id}",
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
            f"(score={candidate['score']:.3f}, proof_vocab_min_ocr={candidate['proof_vocab_min_ocr']:.4f}, "
            f"line_mean_ocr={candidate['line_mean_ocr']:.4f})"
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n")


def _candidate_score(candidate_summary: dict[str, object]) -> float:
    proof_mean = float(candidate_summary["proof_vocab_mean_ocr"])
    line_mean = float(candidate_summary["line_mean_ocr"])
    spacing_mean = float(candidate_summary["line_mean_spacing_cv"])
    x_height_mean = float(candidate_summary["line_mean_x_height_stability_cv"])
    baseline_mean = float(candidate_summary["line_mean_baseline_drift_ratio"])
    delta_mean = float(candidate_summary["baseline_mean_readability_delta"])
    score = proof_mean * 10.0 + line_mean * 12.0
    score += max(0.0, 1.0 - spacing_mean) * 3.0
    score += max(0.0, 1.0 - x_height_mean) * 3.0
    score += max(0.0, 1.0 - baseline_mean) * 3.0
    score -= delta_mean * 6.0
    if bool(candidate_summary["passed"]):
        score += 30.0
    return score


def run_word_line_curriculum(
    output_dir: Path | str,
    *,
    manifest_path: Path | str = DEFAULT_WORD_LINE_MANIFEST_PATH,
    profile: HandProfile | None = None,
    exploratory: bool = False,
) -> WordLineRunResult:
    """Run word/line promotion and freeze line-v1 on gate pass."""

    manifest = load_word_line_manifest(manifest_path)
    base_profile = copy.deepcopy(profile or HandProfile())
    base_profile = _load_glyph_join_profile(
        base_profile,
        glyph_join_manifest_path=manifest.glyph_join_manifest_path,
        glyph_join_candidate_name=manifest.glyph_join_candidate_name,
    )
    if manifest.base_profile_overrides:
        base_profile = _apply_overrides(base_profile, manifest.base_profile_overrides)

    guide_catalog = load_word_guide_catalog(x_height_mm=base_profile.letterform.x_height_mm)
    dataset_guides = []
    for text in (*manifest.proof_entries, *manifest.promotion_lines):
        _, line_guide, word_guides = build_line_session(text, guide_catalog=guide_catalog)
        dataset_guides.append(line_guide)
        dataset_guides.extend(word_info.guide for word_info in word_guides)

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    dataset_policy_name = "exploratory" if exploratory else manifest.dataset_policy
    dataset_decision = evaluate_dataset_policy(list(dataset_guides), policy_name=dataset_policy_name)
    dataset_metrics = dataset_admission_metrics(dataset_guides)
    dataset_summary = {
        "policy": dataset_policy_name,
        "passed": dataset_decision.passed,
        "reasons": list(dataset_decision.reasons),
        "metrics": dataset_metrics,
        "proof_entries": list(manifest.proof_entries),
        "promotion_lines": list(manifest.promotion_lines),
        "accepted_tier_only": all(guide.accepted_only for guide in dataset_guides),
    }
    (output_root / "dataset_summary.json").write_text(json.dumps(dataset_summary, indent=2, sort_keys=True) + "\n")
    (output_root / "dataset_admission_report.json").write_text(
        json.dumps(dataset_summary, indent=2, sort_keys=True) + "\n"
    )
    _write_dataset_admission_markdown(
        output_root / "dataset_admission_report.md",
        manifest=manifest,
        dataset_metrics=dataset_metrics,
        dataset_policy_name=dataset_policy_name,
        dataset_policy_passed=dataset_decision.passed,
        dataset_policy_reasons=dataset_decision.reasons,
        proof_entries=manifest.proof_entries,
        promotion_lines=manifest.promotion_lines,
    )

    candidate_results: list[dict[str, object]] = []
    best_candidate: dict[str, object] | None = None

    for candidate in manifest.candidates:
        candidate_profile = _apply_overrides(base_profile, candidate.profile_overrides)
        controller = GuidedHandFlowController(candidate_profile)
        candidate_dir = output_root / "candidates" / candidate.name
        proof_dir = candidate_dir / "proof_vocabulary"
        lines_dir = candidate_dir / "proof_lines"
        proof_dir.mkdir(parents=True, exist_ok=True)
        lines_dir.mkdir(parents=True, exist_ok=True)

        proof_entries: list[dict[str, object]] = []
        proof_scores: list[float] = []
        proof_word_scores: list[float] = []
        proof_images: list[Path] = []
        for text in manifest.proof_entries:
            session_items, line_guide, word_guides = build_line_session(text, guide_catalog=guide_catalog)
            result = controller.simulate_session(session_items, dt=manifest.dt)
            slug = _slug(text)
            image_path = proof_dir / f"{slug}.png"
            rendered = render_trajectory_proof(
                result.guide_aligned_trajectory,
                profile=candidate_profile,
                output_path=image_path,
                dpi=manifest.proof_dpi,
                supersample=manifest.proof_supersample,
                bounds_mm=_guide_render_bounds(line_guide),
            )
            reference = render_trajectory_proof(
                _nominal_trajectory(line_guide, candidate_profile),
                profile=candidate_profile,
                dpi=manifest.proof_dpi,
                supersample=manifest.proof_supersample,
                bounds_mm=_guide_render_bounds(line_guide),
            )
            metrics = _build_line_metrics(session_items, result, line_guide, word_guides, rendered, reference)
            gate = evaluate_gate("line", metrics)
            report = StageReport(
                stage=f"proof_vocab:{slug}",
                metrics=metrics,
                gate=gate,
                notes=(f"text={text}",),
            )
            write_stage_report(report, proof_dir)
            proof_entries.append(
                {
                    "text": text,
                    "slug": slug,
                    "passed": gate.passed,
                    "metrics": metrics,
                    "image_path": image_path.as_posix(),
                }
            )
            proof_scores.append(metrics["ocr_proxy_score"])
            if " " not in text:
                proof_word_scores.append(metrics["ocr_proxy_score"])
            proof_images.append(image_path)

        _write_snapshot_panel(proof_images, candidate_dir / "proof_vocabulary_panel.png", columns=3)

        line_entries: list[dict[str, object]] = []
        line_reports: list[StageReport] = []
        line_images: list[Path] = []
        baseline_rows: list[dict[str, object]] = []
        for text in manifest.promotion_lines:
            session_items, line_guide, word_guides = build_line_session(text, guide_catalog=guide_catalog)
            result = controller.simulate_session(session_items, dt=manifest.dt)
            slug = _slug(text)
            image_path = lines_dir / f"{slug}.png"
            rendered = render_trajectory_proof(
                result.guide_aligned_trajectory,
                profile=candidate_profile,
                output_path=image_path,
                dpi=manifest.proof_dpi,
                supersample=manifest.proof_supersample,
                bounds_mm=_guide_render_bounds(line_guide),
            )
            reference = render_trajectory_proof(
                _nominal_trajectory(line_guide, candidate_profile),
                profile=candidate_profile,
                dpi=manifest.proof_dpi,
                supersample=manifest.proof_supersample,
                bounds_mm=_guide_render_bounds(line_guide),
            )
            metrics = _build_line_metrics(session_items, result, line_guide, word_guides, rendered, reference)
            gate = evaluate_gate("line", metrics)
            report = StageReport(
                stage=f"line:{slug}",
                metrics=metrics,
                gate=gate,
                notes=(f"text={text}", f"word_count={len(word_guides)}"),
            )
            write_stage_report(report, lines_dir)
            line_reports.append(report)
            line_entries.append(
                {
                    "text": text,
                    "slug": slug,
                    "passed": gate.passed,
                    "metrics": metrics,
                    "image_path": image_path.as_posix(),
                }
            )
            line_images.append(image_path)

            evo_image = render_line(
                text,
                dpi=manifest.proof_dpi,
                nib_width_mm=candidate_profile.nib.width_mm,
                nib_angle_deg=candidate_profile.nib.angle_deg,
                x_height_mm=candidate_profile.letterform.x_height_mm,
                line_height_mm=max(candidate_profile.letterform.x_height_mm * 3.6, 13.5),
                evolve=False,
                verbose=False,
                use_cache=True,
            )
            evo_score = ocr_proxy_score(evo_image, reference)
            baseline_rows.append(
                {
                    "text": text,
                    "guided_metrics": metrics,
                    "guided_ocr_proxy_score": metrics["ocr_proxy_score"],
                    "evo_ocr_proxy_score": evo_score,
                    "readability_regression_delta": readability_regression_delta(metrics["ocr_proxy_score"], evo_score),
                }
            )
            (lines_dir / f"{slug}_evo.json").write_text(
                json.dumps(baseline_rows[-1], indent=2, sort_keys=True) + "\n"
            )

        _write_snapshot_panel(line_images, candidate_dir / "proof_line_panel.png", columns=2)
        baseline_report = {
            "rows": baseline_rows,
            "mean_guided_ocr_proxy_score": float(
                sum(row["guided_ocr_proxy_score"] for row in baseline_rows) / max(len(baseline_rows), 1)
            ),
            "mean_evo_ocr_proxy_score": float(
                sum(row["evo_ocr_proxy_score"] for row in baseline_rows) / max(len(baseline_rows), 1)
            ),
            "mean_readability_regression_delta": float(
                sum(row["readability_regression_delta"] for row in baseline_rows) / max(len(baseline_rows), 1)
            ),
        }
        (candidate_dir / "evo_baseline_report.json").write_text(
            json.dumps(baseline_report, indent=2, sort_keys=True) + "\n"
        )

        summary = {
            "name": candidate.name,
            "description": candidate.description,
            "passed": bool(
                dataset_decision.passed
                and min(proof_word_scores, default=0.0) >= 0.88
                and all(report.gate.passed for report in line_reports)
            ),
            "proof_vocab_min_ocr": float(min(proof_word_scores, default=0.0)),
            "proof_vocab_mean_ocr": float(sum(proof_scores) / max(len(proof_scores), 1)),
            "line_mean_ocr": float(
                sum(entry["metrics"]["ocr_proxy_score"] for entry in line_entries) / max(len(line_entries), 1)
            ),
            "line_mean_spacing_cv": float(
                sum(entry["metrics"]["spacing_cv"] for entry in line_entries) / max(len(line_entries), 1)
            ),
            "line_mean_x_height_stability_cv": float(
                sum(entry["metrics"]["x_height_stability_cv"] for entry in line_entries) / max(len(line_entries), 1)
            ),
            "line_mean_baseline_drift_ratio": float(
                sum(entry["metrics"]["baseline_drift_ratio"] for entry in line_entries) / max(len(line_entries), 1)
            ),
            "baseline_mean_readability_delta": float(baseline_report["mean_readability_regression_delta"]),
            "candidate_dir": candidate_dir.as_posix(),
            "profile_flat": candidate_profile.to_flat_dict(),
            "proof_vocab_path": (candidate_dir / "proof_vocabulary_panel.png").as_posix(),
            "proof_line_path": (candidate_dir / "proof_line_panel.png").as_posix(),
            "evo_baseline_report_path": (candidate_dir / "evo_baseline_report.json").as_posix(),
        }
        summary["score"] = _candidate_score(summary)
        candidate_results.append(summary)
        if best_candidate is None or (summary["passed"], summary["score"]) > (best_candidate["passed"], best_candidate["score"]):
            best_candidate = summary

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
        checkpoint = WordLineCheckpoint(
            checkpoint_id=manifest.checkpoint_id,
            candidate_name=str(best_candidate["name"]),
            manifest_path=Path(manifest_path).as_posix(),
            glyph_join_manifest_path=manifest.glyph_join_manifest_path,
            glyph_join_candidate_name=manifest.glyph_join_candidate_name,
            dataset_policy=dataset_policy_name,
            passed=True,
            proof_entries=manifest.proof_entries,
            promotion_lines=manifest.promotion_lines,
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

    return WordLineRunResult(
        passed=bool(best_candidate and best_candidate["passed"]),
        manifest=manifest,
        selected_candidate=str(best_candidate["name"]) if best_candidate else None,
        checkpoint_path=checkpoint_path.as_posix() if checkpoint_path else None,
        output_dir=output_root.as_posix(),
    )
