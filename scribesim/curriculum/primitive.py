"""Primitive curriculum promotion runner for TD-014."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import tomllib

from PIL import Image, ImageDraw

from scribesim.hand.profile import HandProfile
from scribesim.handflow import build_primitive_proof_guides, run_primitive_proof
from scribesim.handvalidate import dataset_admission_metrics, evaluate_dataset_policy

from .model import PrimitiveCandidate, PrimitiveCheckpoint, PrimitiveManifest, PrimitiveRunResult


DEFAULT_PRIMITIVE_MANIFEST_PATH = Path("shared/training/handsim/primitive/manifest.toml")
DEFAULT_DATASET_SUMMARY_PATH = Path("shared/training/handsim/primitive/dataset_summary.toml")


def _flatten_overrides(payload: dict[str, object], prefix: str = "") -> dict[str, object]:
    flat: dict[str, object] = {}
    for key, value in payload.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten_overrides(value, dotted))
        else:
            flat[dotted] = value
    return flat


def load_primitive_manifest(path: Path | str = DEFAULT_PRIMITIVE_MANIFEST_PATH) -> PrimitiveManifest:
    raw = tomllib.loads(Path(path).read_text())
    candidates = tuple(
        PrimitiveCandidate(
            name=str(candidate["name"]),
            description=str(candidate.get("description", "")),
            profile_overrides=dict(candidate.get("profile_overrides", {})),
        )
        for candidate in raw.get("candidates", [])
    )
    return PrimitiveManifest(
        stage_id=str(raw["stage_id"]),
        checkpoint_id=str(raw["checkpoint_id"]),
        dataset_policy=str(raw.get("dataset_policy", "promotion")),
        exercises=tuple(str(name) for name in raw.get("exercises", [])),
        proof_dpi=int(raw.get("proof_dpi", 220)),
        proof_supersample=int(raw.get("proof_supersample", 3)),
        dt=float(raw.get("dt", 0.002)),
        base_profile_overrides=dict(raw.get("base_profile_overrides", {})),
        candidates=candidates,
    )


def _apply_overrides(profile: HandProfile, overrides: dict[str, object]) -> HandProfile:
    flat = _flatten_overrides(overrides)
    return profile.apply_delta(flat)


def _candidate_score(reports: dict[str, object]) -> float:
    score = 0.0
    for report in reports.values():
        metrics = report.metrics
        score += metrics.get("corridor_containment", 0.0) * 5.0
        score += metrics.get("contact_accuracy", 0.0) * 3.0
        score -= metrics.get("width_profile_error", 1.0) * 2.0
        score -= metrics.get("self_intersections", 0.0) * 10.0
        if report.gate.passed:
            score += 25.0
    return score


def _write_markdown_summary(
    path: Path,
    *,
    manifest: PrimitiveManifest,
    dataset_metrics: dict[str, float],
    dataset_policy_name: str,
    dataset_policy_passed: bool,
    dataset_policy_reasons: tuple[str, ...],
    candidates: list[dict[str, object]],
    selected_candidate: str | None,
) -> None:
    lines = [
        f"# TD-014 Primitive Curriculum: {manifest.checkpoint_id}",
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


def _write_snapshot_panel(
    image_paths: list[Path],
    output_path: Path,
    *,
    columns: int = 3,
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


def run_primitive_curriculum(
    output_dir: Path | str,
    *,
    manifest_path: Path | str = DEFAULT_PRIMITIVE_MANIFEST_PATH,
    profile: HandProfile | None = None,
    exploratory: bool = False,
) -> PrimitiveRunResult:
    """Run primitive promotion and freeze primitive-v1 on gate pass."""

    manifest = load_primitive_manifest(manifest_path)
    base_profile = copy.deepcopy(profile or HandProfile())
    if manifest.base_profile_overrides:
        base_profile = _apply_overrides(base_profile, manifest.base_profile_overrides)

    guides = build_primitive_proof_guides(x_height_mm=base_profile.letterform.x_height_mm)
    selected_guides = {name: guides[name] for name in manifest.exercises}

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    dataset_policy_name = "exploratory" if exploratory else manifest.dataset_policy
    dataset_decision = evaluate_dataset_policy(
        list(selected_guides.values()),
        policy_name=dataset_policy_name,
    )
    dataset_metrics = dataset_admission_metrics(selected_guides.values())
    dataset_summary = {
        "policy": dataset_policy_name,
        "passed": dataset_decision.passed,
        "reasons": list(dataset_decision.reasons),
        "metrics": dataset_metrics,
    }
    (output_root / "dataset_summary.json").write_text(json.dumps(dataset_summary, indent=2, sort_keys=True) + "\n")

    candidate_results: list[dict[str, object]] = []
    best_candidate: dict[str, object] | None = None
    for candidate in manifest.candidates:
        candidate_profile = _apply_overrides(base_profile, candidate.profile_overrides)
        candidate_dir = output_root / "candidates" / candidate.name
        reports = run_primitive_proof(
            candidate_dir,
            profile=candidate_profile,
            guides=selected_guides,
            dpi=manifest.proof_dpi,
            supersample=manifest.proof_supersample,
            dt=manifest.dt,
        )
        panel_path = candidate_dir / "snapshot_panel.png"
        _write_snapshot_panel([candidate_dir / f"{name}.png" for name in manifest.exercises], panel_path)
        passed = dataset_decision.passed and all(report.gate.passed for report in reports.values())
        score = _candidate_score(reports)
        entry = {
            "name": candidate.name,
            "description": candidate.description,
            "passed": passed,
            "score": score,
            "candidate_dir": candidate_dir.as_posix(),
            "panel_path": panel_path.as_posix(),
            "profile_flat": candidate_profile.to_flat_dict(),
        }
        candidate_results.append(entry)
        if best_candidate is None:
            best_candidate = entry
        else:
            current_key = (entry["passed"], entry["score"])
            best_key = (best_candidate["passed"], best_candidate["score"])
            if current_key > best_key:
                best_candidate = entry

    summary_path = output_root / "curriculum_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "manifest": asdict(manifest),
                "dataset_policy": dataset_summary,
                "candidates": candidate_results,
                "selected_candidate": best_candidate["name"] if best_candidate else None,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    _write_markdown_summary(
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
        checkpoint = PrimitiveCheckpoint(
            checkpoint_id=manifest.checkpoint_id,
            candidate_name=str(best_candidate["name"]),
            manifest_path=Path(manifest_path).as_posix(),
            dataset_policy=dataset_policy_name,
            passed=True,
            exercise_names=manifest.exercises,
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

    return PrimitiveRunResult(
        passed=bool(best_candidate and best_candidate["passed"]),
        manifest=manifest,
        selected_candidate=str(best_candidate["name"]) if best_candidate else None,
        checkpoint_path=checkpoint_path.as_posix() if checkpoint_path else None,
        output_dir=output_root.as_posix(),
    )
