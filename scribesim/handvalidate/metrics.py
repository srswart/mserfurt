"""Deterministic validation metrics for TD-014 guided hand recovery."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Iterable

import numpy as np

from scribesim.metrics import composite_score, run_metrics
from scribesim.pathguide import DensePathGuide, GuideSample, GuideSource

from .model import TrajectorySample


def _trajectory_points(samples: Iterable[TrajectorySample]) -> list[tuple[float, float]]:
    return [(sample.x_mm, sample.y_mm) for sample in samples]


def _guide_points(samples: Iterable[GuideSample]) -> list[tuple[float, float]]:
    return [(sample.x_mm, sample.y_mm) for sample in samples]


def _contact_points(samples: Iterable[TrajectorySample]) -> list[tuple[float, float]]:
    return [(sample.x_mm, sample.y_mm) for sample in samples if sample.contact]


def _guide_contact_points(guide: DensePathGuide) -> list[tuple[float, float]]:
    return [(sample.x_mm, sample.y_mm) for sample in guide.samples if sample.contact]


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _normalize_vector(dx: float, dy: float) -> tuple[float, float]:
    norm = math.hypot(dx, dy)
    if norm <= 1e-9:
        return (1.0, 0.0)
    return (dx / norm, dy / norm)


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
    if a1 == b1 or a1 == b2 or a2 == b1 or a2 == b2:
        return False

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


def _dtw_path(
    trace: list[tuple[float, float]],
    reference: list[tuple[float, float]],
) -> list[tuple[int, int]]:
    if not trace or not reference:
        return []

    n = len(trace)
    m = len(reference)
    cost = [[math.dist(trace[i], reference[j]) for j in range(m)] for i in range(n)]
    dtw = [[float("inf")] * m for _ in range(n)]
    dtw[0][0] = cost[0][0]
    for i in range(1, n):
        dtw[i][0] = dtw[i - 1][0] + cost[i][0]
    for j in range(1, m):
        dtw[0][j] = dtw[0][j - 1] + cost[0][j]
    for i in range(1, n):
        for j in range(1, m):
            dtw[i][j] = cost[i][j] + min(dtw[i - 1][j], dtw[i][j - 1], dtw[i - 1][j - 1])

    path: list[tuple[int, int]] = []
    i, j = n - 1, m - 1
    while i > 0 or j > 0:
        path.append((i, j))
        if i == 0:
            j -= 1
        elif j == 0:
            i -= 1
        else:
            best = min(
                (dtw[i - 1][j - 1], 0),
                (dtw[i - 1][j], 1),
                (dtw[i][j - 1], 2),
            )
            if best[1] == 0:
                i -= 1
                j -= 1
            elif best[1] == 1:
                i -= 1
            else:
                j -= 1
    path.append((0, 0))
    path.reverse()
    return path


def _align_observed_to_guide(
    observed: Iterable[TrajectorySample],
    guide: DensePathGuide,
) -> list[TrajectorySample]:
    observed_list = list(observed)
    if not observed_list:
        return []

    ref_points = _guide_points(guide.samples)
    obs_points = _trajectory_points(observed_list)
    path = _dtw_path(obs_points, ref_points)
    if not path:
        return []

    mapped: dict[int, list[TrajectorySample]] = defaultdict(list)
    for obs_idx, ref_idx in path:
        mapped[ref_idx].append(observed_list[obs_idx])

    aligned: list[TrajectorySample] = []
    for ref_idx in range(len(guide.samples)):
        group = mapped.get(ref_idx)
        if not group:
            group = [observed_list[0]]
        x_mm = sum(sample.x_mm for sample in group) / len(group)
        y_mm = sum(sample.y_mm for sample in group) / len(group)
        contact = Counter(sample.contact for sample in group).most_common(1)[0][0]
        widths = [sample.width_mm for sample in group if sample.width_mm is not None]
        pressures = [sample.pressure for sample in group if sample.pressure is not None]
        aligned.append(
            TrajectorySample(
                x_mm=x_mm,
                y_mm=y_mm,
                contact=contact,
                width_mm=sum(widths) / len(widths) if widths else None,
                pressure=sum(pressures) / len(pressures) if pressures else None,
            )
        )
    return aligned


def _turning_angles(points: list[tuple[float, float]]) -> np.ndarray:
    if len(points) < 3:
        return np.zeros(1, dtype=float)

    values: list[float] = []
    for idx in range(1, len(points) - 1):
        ax = points[idx][0] - points[idx - 1][0]
        ay = points[idx][1] - points[idx - 1][1]
        bx = points[idx + 1][0] - points[idx][0]
        by = points[idx + 1][1] - points[idx][1]
        an = math.hypot(ax, ay)
        bn = math.hypot(bx, by)
        if an <= 1e-9 or bn <= 1e-9:
            continue
        cross = ax * by - ay * bx
        dot = ax * bx + ay * by
        values.append(math.atan2(cross, dot))
    if not values:
        return np.zeros(1, dtype=float)
    return np.asarray(values, dtype=float)


def trajectory_from_guide(
    guide: DensePathGuide,
    *,
    width_scale_mm: float = 1.0,
) -> tuple[TrajectorySample, ...]:
    """Build a nominal observed trajectory from a dense guide for tests and reports."""

    return tuple(
        TrajectorySample(
            x_mm=sample.x_mm,
            y_mm=sample.y_mm,
            contact=sample.contact,
            width_mm=sample.pressure_nominal * width_scale_mm,
            pressure=sample.pressure_nominal,
        )
        for sample in guide.samples
    )


def corridor_containment_ratio(observed: Iterable[TrajectorySample], guide: DensePathGuide) -> float:
    aligned = _align_observed_to_guide(observed, guide)
    if not aligned:
        return 0.0

    inside = 0
    total = 0
    for obs, ref in zip(aligned, guide.samples, strict=False):
        if not ref.contact:
            continue
        total += 1
        if math.dist((obs.x_mm, obs.y_mm), (ref.x_mm, ref.y_mm)) <= ref.corridor_half_width_mm + 1e-9:
            inside += 1
    if total == 0:
        return 0.0
    return inside / total


def self_intersection_count(observed: Iterable[TrajectorySample]) -> int:
    points = _contact_points(observed)
    if len(points) < 4:
        return 0

    count = 0
    for i in range(len(points) - 1):
        for j in range(i + 2, len(points) - 1):
            if _segments_intersect(points[i], points[i + 1], points[j], points[j + 1]):
                count += 1
    return count


def contact_accuracy(observed: Iterable[TrajectorySample], guide: DensePathGuide) -> float:
    observed_list = list(observed)
    if len(observed_list) == len(guide.samples):
        correct = sum(
            int(obs.contact == ref.contact)
            for obs, ref in zip(observed_list, guide.samples, strict=False)
        )
        return correct / len(guide.samples) if guide.samples else 0.0

    aligned = _align_observed_to_guide(observed_list, guide)
    if not aligned:
        return 0.0
    correct = sum(int(obs.contact == ref.contact) for obs, ref in zip(aligned, guide.samples, strict=False))
    return correct / len(guide.samples)


def width_profile_error(
    observed_widths: Iterable[float | None],
    reference_widths: Iterable[float | None],
) -> float:
    obs = np.asarray([float(value) for value in observed_widths if value is not None], dtype=float)
    ref = np.asarray([float(value) for value in reference_widths if value is not None], dtype=float)
    if len(obs) == 0 or len(ref) == 0:
        return 1.0

    sample_count = max(len(obs), len(ref))
    x_obs = np.linspace(0.0, 1.0, len(obs))
    x_ref = np.linspace(0.0, 1.0, len(ref))
    x_common = np.linspace(0.0, 1.0, sample_count)
    obs_interp = np.interp(x_common, x_obs, obs)
    ref_interp = np.interp(x_common, x_ref, ref)
    denom = max(np.max(np.abs(ref_interp)), 1e-6)
    return float(np.mean(np.abs(obs_interp - ref_interp)) / denom)


def dtw_centerline_distance(observed: Iterable[TrajectorySample], guide: DensePathGuide) -> float:
    aligned = _align_observed_to_guide(observed, guide)
    if not aligned:
        return 1.0
    distances = [
        math.dist((obs.x_mm, obs.y_mm), (ref.x_mm, ref.y_mm))
        for obs, ref in zip(aligned, guide.samples, strict=False)
        if ref.contact
    ]
    if not distances:
        return 1.0
    return float(np.mean(distances) / max(guide.x_height_mm, 1e-6))


def curvature_histogram_distance(
    observed: Iterable[TrajectorySample],
    guide: DensePathGuide,
    *,
    bins: int = 24,
) -> float:
    obs_hist, _ = np.histogram(_turning_angles(_contact_points(observed)), bins=bins, range=(-math.pi, math.pi))
    ref_hist, _ = np.histogram(_turning_angles(_guide_contact_points(guide)), bins=bins, range=(-math.pi, math.pi))
    obs_total = max(obs_hist.sum(), 1)
    ref_total = max(ref_hist.sum(), 1)
    obs_norm = obs_hist / obs_total
    ref_norm = ref_hist / ref_total
    return float(np.abs(obs_norm - ref_norm).sum() / 2.0)


def normalized_hausdorff_distance(observed: Iterable[TrajectorySample], guide: DensePathGuide) -> float:
    obs_points = _contact_points(observed)
    ref_points = _guide_contact_points(guide)
    if not obs_points or not ref_points:
        return 1.0

    def directed(source: list[tuple[float, float]], target: list[tuple[float, float]]) -> float:
        return max(min(math.dist(point, candidate) for candidate in target) for point in source)

    distance = max(directed(obs_points, ref_points), directed(ref_points, obs_points))
    return distance / max(guide.x_height_mm, 1e-6)


def template_score(rendered: np.ndarray, target: np.ndarray) -> float:
    """Deterministic glyph/word recognition proxy from the existing image metrics."""

    score = max(0.0, 1.0 - composite_score(run_metrics(rendered, target)))
    if score >= 1.0 - 1e-6:
        return 1.0
    return score


def continuity_score(observed: Iterable[TrajectorySample], guide: DensePathGuide) -> float:
    obs_points = _contact_points(observed)
    ref_points = _guide_contact_points(guide)
    if len(obs_points) < 2 or len(ref_points) < 2:
        return 0.0

    obs_steps = [_distance(obs_points[idx], obs_points[idx + 1]) for idx in range(len(obs_points) - 1)]
    ref_steps = [_distance(ref_points[idx], ref_points[idx + 1]) for idx in range(len(ref_points) - 1)]
    expected_step = max(float(np.median(ref_steps)), 1e-6)
    max_step = max(obs_steps)
    gap_penalty = max(0.0, (max_step - expected_step * 1.5) / (expected_step * 3.0))

    last_vec = _normalize_vector(
        obs_points[-1][0] - obs_points[-2][0],
        obs_points[-1][1] - obs_points[-2][1],
    )
    ref_vec = _normalize_vector(*guide.exit_tangent)
    dot = max(-1.0, min(1.0, last_vec[0] * ref_vec[0] + last_vec[1] * ref_vec[1]))
    tangent_penalty = math.degrees(math.acos(dot)) / 180.0
    return max(0.0, 1.0 - 0.6 * min(gap_penalty, 1.0) - 0.4 * tangent_penalty)


def uncontrolled_exit_count(observed: Iterable[TrajectorySample], guide: DensePathGuide) -> int:
    observed_list = list(observed)
    if len(observed_list) < 2 or len(guide.samples) < 2:
        return 1

    observed_contact = [sample for sample in observed_list if sample.contact]
    guide_contact = [sample for sample in guide.samples if sample.contact]
    if not observed_contact or not guide_contact:
        return 1

    final_obs = observed_contact[-1]
    final_ref = guide_contact[-1]
    distance = math.dist((final_obs.x_mm, final_obs.y_mm), (final_ref.x_mm, final_ref.y_mm))
    tangent_error = exit_tangent_error_deg(observed_list, guide)
    if distance > final_ref.corridor_half_width_mm + 1e-9 or tangent_error > 30.0:
        return 1
    return 0


def forced_lift_count(observed: Iterable[TrajectorySample], guide: DensePathGuide) -> int:
    aligned = _align_observed_to_guide(observed, guide)
    if not aligned:
        return len(guide.samples)
    return sum(int(ref.contact and not obs.contact) for obs, ref in zip(aligned, guide.samples, strict=False))


def exit_tangent_error_deg(observed: Iterable[TrajectorySample], guide: DensePathGuide) -> float:
    points = _contact_points(observed)
    if len(points) < 2:
        return 180.0
    dx = points[-1][0] - points[-2][0]
    dy = points[-1][1] - points[-2][1]
    obs_vec = _normalize_vector(dx, dy)
    ref_vec = _normalize_vector(*guide.exit_tangent)
    dot = max(-1.0, min(1.0, obs_vec[0] * ref_vec[0] + obs_vec[1] * ref_vec[1]))
    return math.degrees(math.acos(dot))


def baseline_drift_ratio(observed: Iterable[TrajectorySample], *, x_height_mm: float) -> float:
    points = _contact_points(observed)
    if len(points) < 2:
        return 1.0
    xs = np.asarray([point[0] for point in points], dtype=float)
    ys = np.asarray([point[1] for point in points], dtype=float)
    if np.allclose(xs, xs[0]):
        residual = np.std(ys)
    else:
        slope, intercept = np.polyfit(xs, ys, deg=1)
        residual = np.std(ys - (slope * xs + intercept))
    return float(residual / max(x_height_mm, 1e-6))


def spacing_cv(spacings: Iterable[float]) -> float:
    values = np.asarray(list(spacings), dtype=float)
    if len(values) < 2:
        return 0.0
    mean = float(np.mean(values))
    if mean <= 1e-9:
        return 0.0
    return float(np.std(values) / mean)


def x_height_stability_cv(x_heights: Iterable[float]) -> float:
    values = np.asarray(list(x_heights), dtype=float)
    if len(values) < 2:
        return 0.0
    mean = float(np.mean(values))
    if mean <= 1e-9:
        return 1.0
    return float(np.std(values) / mean)


def ocr_proxy_score(rendered: np.ndarray, target: np.ndarray) -> float:
    return template_score(rendered, target)


def downstream_contract_pass_rate(checks: dict[str, bool]) -> float:
    if not checks:
        return 0.0
    passed = sum(int(value) for value in checks.values())
    return passed / len(checks)


def readability_regression_delta(candidate_score: float, baseline_score: float) -> float:
    return max(0.0, baseline_score - candidate_score)


def pressure_dynamic_range_score(heatmap: np.ndarray) -> float:
    """Proxy for pressure/ink variation on rendered folio outputs."""

    if heatmap.size == 0:
        return 0.0
    active = heatmap[heatmap > 0]
    if active.size == 0:
        return 0.0
    lo = float(np.percentile(active, 5))
    hi = float(np.percentile(active, 95))
    return max(0.0, hi - lo) / 255.0


def alias_substitution_count(session_items: Iterable[object]) -> float:
    """Count glyphs resolved through explicit alias substitution."""

    count = 0.0
    for item in session_items:
        if getattr(item, "kind", None) != "glyph":
            continue
        if getattr(item, "resolution_kind", "exact") == "alias":
            count += 1.0
    return count


def normalized_substitution_count(session_items: Iterable[object]) -> float:
    """Count glyphs resolved through normalization/casefold fallback."""

    count = 0.0
    for item in session_items:
        if getattr(item, "kind", None) != "glyph":
            continue
        if getattr(item, "resolution_kind", "exact") == "normalized":
            count += 1.0
    return count


def exact_character_coverage(session_items: Iterable[object]) -> float:
    """Share of glyphs resolved without fallback."""

    total = 0.0
    exact = 0.0
    for item in session_items:
        if getattr(item, "kind", None) != "glyph":
            continue
        total += 1.0
        if getattr(item, "resolution_kind", "exact") == "exact":
            exact += 1.0
    if total == 0.0:
        return 1.0
    return exact / total


def ink_state_monotonicity(levels: Iterable[float], *, tolerance: float = 1e-9) -> float:
    values = [float(level) for level in levels]
    if len(values) < 2:
        return 1.0
    monotonic = 0
    total = 0
    for prev, nxt in zip(values, values[1:], strict=False):
        total += 1
        if nxt <= prev + tolerance:
            monotonic += 1
    return monotonic / total if total else 1.0


def ink_state_determinism(
    levels_a: Iterable[float],
    levels_b: Iterable[float],
    *,
    tolerance: float = 1e-9,
) -> float:
    seq_a = [float(level) for level in levels_a]
    seq_b = [float(level) for level in levels_b]
    if not seq_a and not seq_b:
        return 1.0
    if len(seq_a) != len(seq_b):
        return 0.0
    matches = 0
    for left, right in zip(seq_a, seq_b, strict=False):
        if math.isclose(left, right, abs_tol=tolerance):
            matches += 1
    return matches / len(seq_a) if seq_a else 1.0


def thick_thin_ratio_error(
    observed_widths: Iterable[float | None],
    reference_widths: Iterable[float | None],
) -> float:
    obs = np.asarray([float(value) for value in observed_widths if value is not None and value > 1e-9], dtype=float)
    ref = np.asarray([float(value) for value in reference_widths if value is not None and value > 1e-9], dtype=float)
    if len(obs) == 0 or len(ref) == 0:
        return 1.0
    obs_median = float(np.median(obs))
    ref_median = float(np.median(ref))
    obs_core = obs[obs >= obs_median * 0.40]
    ref_core = ref[ref >= ref_median * 0.40]
    if len(obs_core) == 0:
        obs_core = obs
    if len(ref_core) == 0:
        ref_core = ref
    if len(obs_core) >= 4:
        obs_high = float(np.percentile(obs_core, 85))
        obs_low = float(np.percentile(obs_core, 25))
    else:
        obs_high = float(np.max(obs_core))
        obs_low = float(np.min(obs_core))
    if len(ref_core) >= 4:
        ref_high = float(np.percentile(ref_core, 85))
        ref_low = float(np.percentile(ref_core, 25))
    else:
        ref_high = float(np.max(ref_core))
        ref_low = float(np.min(ref_core))
    obs_ratio = obs_high / max(obs_low, 1e-6)
    ref_ratio = ref_high / max(ref_low, 1e-6)
    return abs(obs_ratio - ref_ratio) / max(ref_ratio, 1e-6)


def dataset_admission_metrics(guides: Iterable[DensePathGuide]) -> dict[str, float]:
    symbols: set[str] = set()
    heldout_symbols: set[str] = set()
    tier_counts = {"accepted": 0, "soft_accepted": 0, "rejected": 0}
    resolutions: list[float] = []
    missing_resolution = 0
    missing_provenance = 0

    for guide in guides:
        symbols.add(guide.symbol)
        if not guide.sources:
            missing_provenance += 1
        for source in guide.sources:
            tier_counts[source.confidence_tier] = tier_counts.get(source.confidence_tier, 0) + 1
            if source.split in {"validation", "val", "test"}:
                heldout_symbols.add(guide.symbol)
            if source.source_resolution_ppmm is None:
                missing_resolution += 1
            else:
                resolutions.append(source.source_resolution_ppmm)

    total_symbols = max(len(symbols), 1)
    return {
        "accepted_count": float(tier_counts.get("accepted", 0)),
        "soft_accepted_count": float(tier_counts.get("soft_accepted", 0)),
        "rejected_count": float(tier_counts.get("rejected", 0)),
        "heldout_symbol_coverage": len(heldout_symbols) / total_symbols,
        "missing_resolution_count": float(missing_resolution),
        "missing_provenance_count": float(missing_provenance),
        "mean_source_resolution_ppmm": float(np.mean(resolutions)) if resolutions else 0.0,
        "min_source_resolution_ppmm": float(np.min(resolutions)) if resolutions else 0.0,
    }


def dataset_sources(guides: Iterable[DensePathGuide]) -> tuple[GuideSource, ...]:
    sources: list[GuideSource] = []
    for guide in guides:
        sources.extend(guide.sources)
    return tuple(sources)
