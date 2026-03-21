"""Comparison metrics M1-M9 (TD-003 Part 2).

Quantitative measurement of distance between a rendered folio
and a real manuscript sample across 9 dimensions.
"""

from scribesim.metrics.suite import MetricResult, run_metrics, composite_score

__all__ = ["MetricResult", "run_metrics", "composite_score"]
