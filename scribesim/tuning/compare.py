"""Compare rendered folio against a target manuscript sample."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.metrics.suite import run_metrics, composite_score, MetricResult


def compare_images(rendered_path: Path, target_path: Path,
                   ) -> tuple[list[MetricResult], float]:
    """Run full metric suite on two images.

    Returns (results, composite_score).
    """
    rendered = np.array(Image.open(rendered_path).convert("RGB"))
    target = np.array(Image.open(target_path).convert("RGB"))

    results = run_metrics(rendered, target)
    score = composite_score(results)

    return results, score


def format_report(results: list[MetricResult], score: float) -> str:
    """Format metric results as a human-readable table."""
    lines = []
    lines.append("  ID  Metric                               Distance  Rating")
    lines.append("  --- ------------------------------------ --------  -----------")
    for r in results:
        if r.distance >= 0:
            lines.append(f"  {r.id:3s} {r.name:36s} {r.distance:8.3f}  ({r.rating})")
        else:
            lines.append(f"  {r.id:3s} {r.name:36s}      N/A  ({r.rating})")
    lines.append(f"  --- ------------------------------------ --------  -----------")
    lines.append(f"  COMPOSITE                                {score:8.3f}")
    return "\n".join(lines)
