"""Validation helpers for dense path guides."""

from __future__ import annotations

import math

from scribesim.pathguide.model import (
    DensePathGuide,
    GuideSample,
    VALID_CONFIDENCE_TIERS,
    VALID_GUIDE_KINDS,
)


def _is_finite_pair(pair: tuple[float, float]) -> bool:
    return all(math.isfinite(value) for value in pair)


def _distance(a: GuideSample, b: GuideSample) -> float:
    return math.hypot(b.x_mm - a.x_mm, b.y_mm - a.y_mm)


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> int:
    value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    if abs(value) < 1e-9:
        return 0
    return 1 if value > 0 else 2


def _on_segment(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    return (
        min(a[0], c[0]) - 1e-9 <= b[0] <= max(a[0], c[0]) + 1e-9
        and min(a[1], c[1]) - 1e-9 <= b[1] <= max(a[1], c[1]) + 1e-9
    )


def _segments_intersect(
    a1: tuple[float, float],
    a2: tuple[float, float],
    b1: tuple[float, float],
    b2: tuple[float, float],
) -> bool:
    o1 = _orientation(a1, a2, b1)
    o2 = _orientation(a1, a2, b2)
    o3 = _orientation(b1, b2, a1)
    o4 = _orientation(b1, b2, a2)

    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _on_segment(a1, b1, a2):
        return True
    if o2 == 0 and _on_segment(a1, b2, a2):
        return True
    if o3 == 0 and _on_segment(b1, a1, b2):
        return True
    if o4 == 0 and _on_segment(b1, a2, b2):
        return True
    return False


def _has_self_intersection(points: list[tuple[float, float]]) -> bool:
    if len(points) < 4:
        return False
    for i in range(len(points) - 1):
        for j in range(i + 2, len(points) - 1):
            if _segments_intersect(points[i], points[i + 1], points[j], points[j + 1]):
                return True
    return False


def _contact_runs(guide: DensePathGuide) -> list[list[tuple[float, float]]]:
    runs: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    for sample in guide.samples:
        if sample.contact:
            current.append((sample.x_mm, sample.y_mm))
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return runs


def validate_dense_path_guide(
    guide: DensePathGuide,
    *,
    max_on_surface_step_mm: float = 0.25,
) -> list[str]:
    """Return validation errors for a DensePathGuide."""

    errors: list[str] = []

    if not guide.symbol:
        errors.append("symbol must be non-empty")
    if guide.kind not in VALID_GUIDE_KINDS:
        errors.append(f"kind must be one of {sorted(VALID_GUIDE_KINDS)}")
    if not math.isfinite(guide.x_height_mm) or guide.x_height_mm <= 0:
        errors.append("x_height_mm must be finite and > 0")
    if not math.isfinite(guide.x_advance_mm) or guide.x_advance_mm <= 0:
        errors.append("x_advance_mm must be finite and > 0")
    if len(guide.samples) < 2:
        errors.append("guide must contain at least two samples")
    if not _is_finite_pair(guide.entry_tangent) or math.hypot(*guide.entry_tangent) <= 1e-9:
        errors.append("entry_tangent must be finite and non-zero")
    if not _is_finite_pair(guide.exit_tangent) or math.hypot(*guide.exit_tangent) <= 1e-9:
        errors.append("exit_tangent must be finite and non-zero")

    for idx, source in enumerate(guide.sources):
        if source.confidence_tier not in VALID_CONFIDENCE_TIERS:
            errors.append(
                f"source[{idx}].confidence_tier must be one of {sorted(VALID_CONFIDENCE_TIERS)}"
            )
        if source.source_resolution_ppmm is not None and (
            not math.isfinite(source.source_resolution_ppmm) or source.source_resolution_ppmm <= 0
        ):
            errors.append(f"source[{idx}].source_resolution_ppmm must be finite and > 0")
        if not source.split:
            errors.append(f"source[{idx}].split must be non-empty")

    for idx, sample in enumerate(guide.samples):
        values = (
            sample.x_mm,
            sample.y_mm,
            sample.tangent_dx,
            sample.tangent_dy,
            sample.speed_nominal,
            sample.pressure_nominal,
            sample.nib_angle_deg,
            sample.nib_angle_confidence,
            sample.corridor_half_width_mm,
        )
        if not all(math.isfinite(value) for value in values):
            errors.append(f"sample[{idx}] must contain only finite values")
        if math.hypot(sample.tangent_dx, sample.tangent_dy) <= 1e-9:
            errors.append(f"sample[{idx}] tangent must be non-zero")
        if sample.corridor_half_width_mm <= 0:
            errors.append(f"sample[{idx}].corridor_half_width_mm must be > 0")
        if sample.speed_nominal < 0:
            errors.append(f"sample[{idx}].speed_nominal must be >= 0")
        if not 0.0 <= sample.pressure_nominal <= 1.5:
            errors.append(f"sample[{idx}].pressure_nominal must be in [0, 1.5]")
        if not 25.0 <= sample.nib_angle_deg <= 55.0:
            errors.append(f"sample[{idx}].nib_angle_deg must be in [25, 55]")
        if not 0.0 <= sample.nib_angle_confidence <= 1.0:
            errors.append(f"sample[{idx}].nib_angle_confidence must be in [0, 1]")

    contact_points = [(sample.x_mm, sample.y_mm) for sample in guide.samples if sample.contact]
    if len(contact_points) < 2:
        errors.append("guide must contain at least two on-surface samples")
    if any(_has_self_intersection(run) for run in _contact_runs(guide)):
        errors.append("contact polyline must not self-intersect")

    for idx in range(len(guide.samples) - 1):
        current = guide.samples[idx]
        nxt = guide.samples[idx + 1]
        if current.contact and nxt.contact:
            step = _distance(current, nxt)
            if step > max_on_surface_step_mm + 1e-9:
                errors.append(
                    f"on-surface samples {idx}->{idx+1} exceed max spacing "
                    f"({step:.4f}mm > {max_on_surface_step_mm:.4f}mm)"
                )

    return errors


def assert_valid_dense_path_guide(
    guide: DensePathGuide,
    *,
    max_on_surface_step_mm: float = 0.25,
) -> None:
    errors = validate_dense_path_guide(guide, max_on_surface_step_mm=max_on_surface_step_mm)
    if errors:
        raise ValueError("; ".join(errors))
