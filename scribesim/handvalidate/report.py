"""Structured report emitters for TD-014 validation runs."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .model import StageReport


def stage_report_to_dict(report: StageReport) -> dict:
    return asdict(report)


def stage_report_markdown(report: StageReport) -> str:
    lines = [
        f"# TD-014 Validation Report: {report.stage}",
        "",
        f"- Gate: {'PASS' if report.gate.passed else 'FAIL'}",
    ]
    if report.dataset_policy is not None:
        policy_status = "PASS" if report.dataset_policy_passed else "FAIL"
        lines.append(f"- Dataset policy `{report.dataset_policy}`: {policy_status}")
    lines.append("")
    lines.append("## Metrics")
    for name in sorted(report.metrics):
        lines.append(f"- `{name}`: {report.metrics[name]:.4f}")

    if report.gate.failures:
        lines.append("")
        lines.append("## Gate Failures")
        for failure in report.gate.failures:
            lines.append(f"- `{failure.metric}`: {failure.reason}")

    if report.gate.advisories:
        lines.append("")
        lines.append("## Advisories")
        for advisory in report.gate.advisories:
            lines.append(f"- {advisory}")

    if report.dataset_policy_reasons:
        lines.append("")
        lines.append("## Dataset Policy")
        for reason in report.dataset_policy_reasons:
            lines.append(f"- {reason}")

    if report.notes:
        lines.append("")
        lines.append("## Notes")
        for note in report.notes:
            lines.append(f"- {note}")

    lines.append("")
    return "\n".join(lines)


def write_stage_report(report: StageReport, output_dir: Path | str) -> tuple[Path, Path]:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    stem = report.stage.replace(" ", "_")
    json_path = output_root / f"{stem}.json"
    markdown_path = output_root / f"{stem}.md"
    json_path.write_text(json.dumps(stage_report_to_dict(report), indent=2, sort_keys=True) + "\n")
    markdown_path.write_text(stage_report_markdown(report))
    return json_path, markdown_path
