"""DP-assisted stroke decomposition helpers for the annotation workbench."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.ndimage import distance_transform_edt, maximum_filter

from scribesim.evo.genome import BezierSegment
from scribesim.refextract.centerline import trace_centerline
from scribesim.refextract.nibcal import estimate_nib_angle, estimate_nib_width, measure_stroke_width
from scribesim.refextract.utils import otsu_threshold


@dataclass(frozen=True)
class ExpectedStroke:
    name: str
    direction: str
    weight: str
    allow_lift_before: bool = False


_STROKE_TEMPLATES: dict[str, tuple[ExpectedStroke, ...]] = {
    "n": (
        ExpectedStroke("first_minim", "Down", "Heavy"),
        ExpectedStroke("arch", "UpRight", "Light"),
        ExpectedStroke("second_minim", "Down", "Heavy"),
    ),
    "m": (
        ExpectedStroke("first_minim", "Down", "Heavy"),
        ExpectedStroke("first_arch", "UpRight", "Light"),
        ExpectedStroke("second_minim", "Down", "Heavy"),
        ExpectedStroke("second_arch", "UpRight", "Light"),
        ExpectedStroke("third_minim", "Down", "Heavy"),
    ),
    "h": (
        ExpectedStroke("ascender_stem", "Down", "Heavy"),
        ExpectedStroke("arch", "UpRight", "Light"),
        ExpectedStroke("second_minim", "Down", "Heavy"),
    ),
    "r": (
        ExpectedStroke("minim", "Down", "Heavy"),
        ExpectedStroke("shoulder", "UpRight", "Light"),
    ),
    "i": (
        ExpectedStroke("minim", "Down", "Heavy"),
        ExpectedStroke("dot", "Dot", "Light", allow_lift_before=True),
    ),
    "t": (
        ExpectedStroke("stem", "Down", "Heavy"),
        ExpectedStroke("crossbar", "Right", "Light", allow_lift_before=True),
    ),
    "e": (
        ExpectedStroke("approach", "CurveRight", "Light"),
        ExpectedStroke("loop", "CurveLeft", "Medium"),
        ExpectedStroke("exit", "DownRight", "Medium"),
    ),
    "a": (
        ExpectedStroke("bowl", "CurveLeft", "Medium"),
        ExpectedStroke("downstroke", "Down", "Heavy", allow_lift_before=True),
    ),
    "o": (
        ExpectedStroke("left_curve", "CurveLeft", "Medium"),
        ExpectedStroke("right_curve", "CurveRight", "Medium"),
    ),
    "c": (
        ExpectedStroke("open_curve", "CurveLeft", "Medium"),
    ),
    "d": (
        ExpectedStroke("bowl_left", "CurveLeft", "Medium"),
        ExpectedStroke("bowl_right", "CurveRight", "Light"),
        ExpectedStroke("ascender", "Up", "Heavy", allow_lift_before=True),
        ExpectedStroke("ascender_hook", "CurveLeft", "Light"),
    ),
    "b": (
        ExpectedStroke("ascender_stem", "Down", "Heavy"),
        ExpectedStroke("bowl_out", "CurveRight", "Medium"),
        ExpectedStroke("bowl_return", "CurveLeft", "Medium"),
    ),
    "ſ": (
        ExpectedStroke("top_hook", "CurveRight", "Light"),
        ExpectedStroke("descender", "Down", "Heavy"),
    ),
}

_DIRECTION_ANGLES: dict[str, tuple[float, ...]] = {
    "Down": (90.0,),
    "Up": (270.0,),
    "Right": (0.0,),
    "UpRight": (315.0,),
    "DownRight": (45.0,),
    "CurveLeft": (135.0, 180.0, 225.0),
    "CurveRight": (315.0, 0.0, 45.0),
    "Dot": (270.0,),
}

_WEIGHT_TARGETS: dict[str, float] = {
    "Light": 0.32,
    "Medium": 0.56,
    "Heavy": 0.82,
}


def propose_stroke_decomposition(
    glyph_image: np.ndarray,
    symbol: str,
    *,
    desired_stroke_count: int | None = None,
    ink_threshold: int = 200,
    max_bezier_error: float = 1.2,
) -> dict[str, Any]:
    gray = _to_gray(glyph_image)
    ink = _ink_strength(gray)
    binary = _binarize(gray, ink_threshold=ink_threshold)
    segments = _extract_candidate_segments(
        gray,
        ink,
        binary,
        desired_stroke_count=desired_stroke_count,
        ink_threshold=ink_threshold,
        max_bezier_error=max_bezier_error,
    )
    if not segments:
        raise ValueError("no centerline could be traced from the glyph crop")
    candidate_infos = [_segment_features(gray, ink, segment) for segment in segments]
    all_widths = [width for info in candidate_infos for width in info["widths_px"]]
    all_directions = [direction for info in candidate_infos for direction in info["directions_rad"]]
    nib_angle_deg = estimate_nib_angle(all_widths, all_directions) if all_widths and all_directions else 40.0
    nib_width_px = max(1.0, estimate_nib_width(all_widths, dpi=300.0) / 25.4 * 300.0 if all_widths else 4.0)
    for info in candidate_infos:
        info["pressure_curve"] = _estimate_pressure_curve(info["segment"], info, nib_angle_deg=nib_angle_deg, nib_width_px=nib_width_px)
        angle_curve, angle_confidence = _estimate_nib_angle_curve(
            info["segment"],
            info,
            baseline_nib_angle_deg=nib_angle_deg,
            nib_width_px=nib_width_px,
        )
        info["nib_angle_curve_deg"] = angle_curve
        info["nib_angle_confidence_curve"] = angle_confidence

    selected_mode = "requested-count" if desired_stroke_count else "auto-minimized"
    candidate_counts: list[dict[str, Any]] = []
    if desired_stroke_count is None:
        max_stroke_count = _max_auto_stroke_count(symbol, candidate_infos)
        best_alignment: tuple[tuple[ExpectedStroke, ...], dict[str, Any], list[dict[str, Any]], int, float] | None = None
        for count in range(1, max_stroke_count + 1):
            template = stroke_template(symbol, desired_stroke_count=count)
            selected_infos = _select_segments_for_count(candidate_infos, count)
            grouping = _group_selected_segments(selected_infos, template, gray.shape)
            objective = _candidate_objective(grouping, stroke_count=count)
            candidate_counts.append(
                {
                    "stroke_count": count,
                    "objective": float(objective),
                    "total_cost": float(grouping["total_cost"]),
                    "fallback": bool(grouping.get("fallback")),
                }
            )
            if best_alignment is None or objective < best_alignment[3]:
                best_alignment = (template, grouping, selected_infos, count, objective)
        assert best_alignment is not None
        template, grouping, primitive_infos, selected_count, selected_objective = best_alignment
    else:
        template = stroke_template(symbol, desired_stroke_count=desired_stroke_count)
        primitive_infos = _select_segments_for_count(candidate_infos, len(template))
        grouping = _group_selected_segments(primitive_infos, template, gray.shape)
        selected_count = len(template)
        selected_objective = _candidate_objective(grouping, stroke_count=selected_count)
    proposed_segments: list[dict[str, Any]] = []
    strokes: list[dict[str, Any]] = []
    for stroke_index, group in enumerate(grouping["groups"], start=1):
        expected = template[min(group["template_index"], len(template) - 1)]
        group_infos = primitive_infos[group["start_index"] : group["end_index"]]
        avg_pressure = float(
            sum(sum(info["pressure_curve"]) / max(len(info["pressure_curve"]), 1) for info in group_infos) / max(len(group_infos), 1)
        )
        strokes.append(
            {
                "stroke_order": stroke_index,
                "name": expected.name,
                "direction": expected.direction,
                "weight": expected.weight,
                "segment_count": len(group_infos),
                "average_pressure": avg_pressure,
                "cost": float(group["cost"]),
                "fit_score": float(sum(info["fit_score"] for info in group_infos) / max(len(group_infos), 1)),
                "darkness_support": float(sum(info["center_darkness"] for info in group_infos) / max(len(group_infos), 1)),
                "mean_nib_angle_deg": float(
                    sum(
                        sum(info["nib_angle_curve_deg"]) / max(len(info["nib_angle_curve_deg"]), 1)
                        for info in group_infos
                    )
                    / max(len(group_infos), 1)
                ),
                "lift_before": bool(group["lift_before"]),
            }
        )
        for primitive_index in range(group["start_index"], group["end_index"]):
            segment = primitive_infos[primitive_index]["segment"]
            info = primitive_infos[primitive_index]
            proposed_segments.append(
                {
                    "stroke_order": stroke_index,
                    "stroke_name": expected.name,
                    "expected_direction": expected.direction,
                    "expected_weight": expected.weight,
                    "contact": bool(segment.contact),
                    "nib_angle_mode": "auto",
                    "nib_angle_curve": list(info["nib_angle_curve_deg"]),
                    "nib_angle_confidence": list(info["nib_angle_confidence_curve"]),
                    "p0": {"x": float(segment.p0[0]), "y": float(segment.p0[1])},
                    "p1": {"x": float(segment.p1[0]), "y": float(segment.p1[1])},
                    "p2": {"x": float(segment.p2[0]), "y": float(segment.p2[1])},
                    "p3": {"x": float(segment.p3[0]), "y": float(segment.p3[1])},
                    "pressure_curve": list(info["pressure_curve"]),
                    "speed_curve": list(segment.speed_curve),
                    "proposal_source": "stroke_assist",
                }
            )

    confidence = _proposal_confidence(grouping["total_cost"], len(strokes))
    return {
        "symbol": symbol,
        "mode": selected_mode,
        "segments": proposed_segments,
        "strokes": strokes,
        "primitive_count": len(candidate_infos),
        "stroke_count": len(strokes),
        "template_stroke_count": len(template),
        "selected_stroke_count": int(selected_count),
        "requested_stroke_count": int(desired_stroke_count) if desired_stroke_count else None,
        "selected_objective": float(selected_objective),
        "image_fit": float(sum(info["fit_score"] for info in primitive_infos) / max(len(primitive_infos), 1)),
        "darkness_support": float(sum(info["center_darkness"] for info in primitive_infos) / max(len(primitive_infos), 1)),
        "candidate_counts": candidate_counts,
        "nib_angle_deg": float(nib_angle_deg),
        "nib_width_px": float(nib_width_px),
        "confidence": confidence,
        "issues": _proposal_issues(grouping, strokes, template),
    }


def stroke_template(symbol: str, desired_stroke_count: int | None = None) -> tuple[ExpectedStroke, ...]:
    base = _STROKE_TEMPLATES.get(str(symbol), (ExpectedStroke("main_stroke", "Down", "Heavy"),))
    if desired_stroke_count is None:
        return base
    count = max(1, int(desired_stroke_count))
    if count == len(base):
        return base
    if count == 1:
        proto = base[min(len(base) - 1, len(base) // 2)]
        return (ExpectedStroke("stroke_1", proto.direction, proto.weight, allow_lift_before=proto.allow_lift_before),)
    remapped: list[ExpectedStroke] = []
    for index in range(count):
        proto_index = round(index * (len(base) - 1) / max(count - 1, 1))
        proto = base[min(len(base) - 1, max(0, proto_index))]
        remapped.append(
            ExpectedStroke(
                name=f"stroke_{index + 1}",
                direction=proto.direction,
                weight=proto.weight,
                allow_lift_before=proto.allow_lift_before,
            )
        )
    return tuple(remapped)


def _align_primitives_to_template(
    primitive_infos: list[dict[str, Any]],
    template: tuple[ExpectedStroke, ...],
    image_shape: tuple[int, ...],
) -> dict[str, Any]:
    primitive_count = len(primitive_infos)
    stroke_count = len(template)
    dp = [[math.inf] * (primitive_count + 1) for _ in range(stroke_count + 1)]
    back: list[list[tuple[int, int] | None]] = [[None] * (primitive_count + 1) for _ in range(stroke_count + 1)]
    dp[0][0] = 0.0

    for stroke_index in range(1, stroke_count + 1):
        expected = template[stroke_index - 1]
        for end_index in range(1, primitive_count + 1):
            for start_index in range(max(0, stroke_index - 1), end_index):
                if not math.isfinite(dp[stroke_index - 1][start_index]):
                    continue
                group = primitive_infos[start_index:end_index]
                cost = _group_cost(expected, group, image_shape=image_shape, lift_before=bool(expected.allow_lift_before))
                total = dp[stroke_index - 1][start_index] + cost
                if total < dp[stroke_index][end_index]:
                    dp[stroke_index][end_index] = total
                    back[stroke_index][end_index] = (start_index, end_index)

    best_end = min(range(1, primitive_count + 1), key=lambda index: dp[stroke_count][index])
    if not math.isfinite(dp[stroke_count][best_end]):
        return _fallback_alignment(primitive_infos, template, image_shape)

    groups: list[dict[str, Any]] = []
    current_end = best_end
    for stroke_index in range(stroke_count, 0, -1):
        edge = back[stroke_index][current_end]
        if edge is None:
            return _fallback_alignment(primitive_infos, template, image_shape)
        start_index, end_index = edge
        expected = template[stroke_index - 1]
        groups.append(
            {
                "template_index": stroke_index - 1,
                "start_index": start_index,
                "end_index": end_index,
                "cost": _group_cost(expected, primitive_infos[start_index:end_index], image_shape=image_shape, lift_before=bool(expected.allow_lift_before)),
                "lift_before": bool(expected.allow_lift_before),
            }
        )
        current_end = start_index
    groups.reverse()
    return {"groups": groups, "total_cost": float(dp[stroke_count][best_end]), "fallback": False}


def _group_selected_segments(
    primitive_infos: list[dict[str, Any]],
    template: tuple[ExpectedStroke, ...],
    image_shape: tuple[int, ...],
) -> dict[str, Any]:
    if not primitive_infos:
        return {"groups": [], "total_cost": 999.0, "fallback": True}
    selected = list(primitive_infos)
    if len(selected) < len(template):
        while len(selected) < len(template):
            selected.append(dict(selected[-1]))
    if len(selected) > len(template):
        selected = selected[: len(template)]
    groups: list[dict[str, Any]] = []
    total_cost = 0.0
    for index, expected in enumerate(template):
        cost = _group_cost(expected, [selected[index]], image_shape=image_shape, lift_before=bool(expected.allow_lift_before))
        total_cost += cost
        groups.append(
            {
                "template_index": index,
                "start_index": index,
                "end_index": index + 1,
                "cost": float(cost),
                "lift_before": bool(expected.allow_lift_before),
            }
        )
    return {"groups": groups, "total_cost": float(total_cost), "fallback": len(primitive_infos) != len(template)}


def _fallback_alignment(
    primitive_infos: list[dict[str, Any]],
    template: tuple[ExpectedStroke, ...],
    image_shape: tuple[int, ...],
) -> dict[str, Any]:
    primitive_count = len(primitive_infos)
    if primitive_count <= 0:
        return {"groups": [], "total_cost": 999.0, "fallback": True}
    boundaries = [0]
    for index in range(1, len(template)):
        boundaries.append(min(primitive_count - 1, max(boundaries[-1], round(index * primitive_count / len(template)))))
    boundaries.append(primitive_count)
    groups = []
    for stroke_index, expected in enumerate(template):
        start_index = boundaries[stroke_index]
        end_index = max(start_index + 1, boundaries[stroke_index + 1]) if stroke_index + 1 < len(boundaries) else primitive_count
        start_index = min(start_index, max(0, primitive_count - 1))
        end_index = min(primitive_count, max(start_index + 1, end_index))
        groups.append(
            {
                "template_index": stroke_index,
                "start_index": start_index,
                "end_index": end_index,
                "cost": _group_cost(expected, primitive_infos[start_index:end_index], image_shape=image_shape, lift_before=bool(expected.allow_lift_before)),
                "lift_before": bool(expected.allow_lift_before),
            }
        )
    return {"groups": groups, "total_cost": float(sum(group["cost"] for group in groups)), "fallback": True}


def _group_cost(
    expected: ExpectedStroke,
    group: list[dict[str, Any]],
    *,
    image_shape: tuple[int, ...],
    lift_before: bool,
) -> float:
    if not group:
        return 999.0
    mean_direction = float(sum(item["direction_deg"] for item in group) / len(group))
    direction_cost = min(_angle_distance_deg(mean_direction, target) for target in _DIRECTION_ANGLES.get(expected.direction, (90.0,))) / 90.0
    mean_pressure = float(sum(sum(item["pressure_curve"]) / max(len(item["pressure_curve"]), 1) for item in group) / len(group))
    weight_cost = abs(mean_pressure - _WEIGHT_TARGETS.get(expected.weight, 0.56)) * 1.6
    mean_fit = float(sum(item["fit_score"] for item in group) / len(group))
    mean_darkness = float(sum(item["center_darkness"] for item in group) / len(group))
    endpoint_support = float(sum(item["endpoint_darkness"] for item in group) / len(group))
    image_fit_cost = max(0.0, 0.88 - mean_fit) * 1.8
    darkness_cost = max(0.0, 0.58 - mean_darkness) * 1.1
    endpoint_cost = max(0.0, 0.42 - endpoint_support) * 0.6
    contact_gap_cost = 0.0
    has_lift = any(not bool(item["contact"]) for item in group)
    if lift_before and not has_lift:
        contact_gap_cost += 0.35
    if not lift_before and has_lift and expected.direction != "Dot":
        contact_gap_cost += 0.25
    continuity_cost = 0.0
    image_diag = max(math.hypot(float(image_shape[1]), float(image_shape[0])), 1.0)
    for left, right in zip(group, group[1:]):
        continuity_cost += math.dist(left["center"], right["center"]) / image_diag
    continuity_cost *= 0.9
    complexity_cost = max(0.0, len(group) - 1) * 0.18
    position_cost = 0.0
    if expected.direction == "Dot":
        center_y = sum(item["center"][1] for item in group) / len(group)
        position_cost += max(0.0, center_y / max(float(image_shape[0]), 1.0) - 0.35) * 1.6
    return float(
        direction_cost * 1.4
        + weight_cost
        + image_fit_cost
        + darkness_cost
        + endpoint_cost
        + contact_gap_cost
        + continuity_cost
        + complexity_cost
        + position_cost
    )


def _segment_features(image: np.ndarray, ink: np.ndarray, segment: BezierSegment) -> dict[str, Any]:
    sample_points = [segment.evaluate(step / 20) for step in range(21)]
    widths_px, directions_rad = measure_stroke_width(image, sample_points)
    mean_direction = _mean_angle_deg([math.degrees(value) % 360.0 for value in directions_rad]) if directions_rad else _segment_direction_deg(segment)
    center = segment.evaluate(0.5)
    center_darkness = float(sum(_sample_ink(ink, point) for point in sample_points) / max(len(sample_points), 1))
    ridge_darkness = float(sum(_sample_peak_ink(ink, point) for point in sample_points) / max(len(sample_points), 1))
    endpoint_darkness = float((_sample_peak_ink(ink, segment.p0) + _sample_peak_ink(ink, segment.p3)) * 0.5)
    off_ink_ratio = float(sum(1 for point in sample_points if _sample_peak_ink(ink, point) < 0.12) / max(len(sample_points), 1))
    fit_score = float(
        max(
            0.0,
            min(
                1.0,
                center_darkness * 0.55 + ridge_darkness * 0.35 + endpoint_darkness * 0.20 - off_ink_ratio * 0.35,
            ),
        )
    )
    return {
        "segment": segment,
        "points": sample_points,
        "widths_px": widths_px,
        "directions_rad": directions_rad,
        "direction_deg": mean_direction,
        "center": center,
        "contact": bool(segment.contact),
        "center_darkness": center_darkness,
        "ridge_darkness": ridge_darkness,
        "endpoint_darkness": endpoint_darkness,
        "off_ink_ratio": off_ink_ratio,
        "fit_score": fit_score,
    }


def _estimate_pressure_curve(
    segment: BezierSegment,
    info: dict[str, Any],
    *,
    nib_angle_deg: float,
    nib_width_px: float,
) -> list[float]:
    samples: list[float] = []
    widths = list(info["widths_px"])
    if not widths:
        return list(segment.pressure_curve)
    for knot_index in range(4):
        t = knot_index / 3 if 3 else 0.0
        direction_deg = _segment_direction_deg(segment, t=t)
        direction_rad = math.radians(direction_deg)
        nib_factor = max(0.1, abs(math.sin(direction_rad - math.radians(nib_angle_deg))))
        source_index = min(len(widths) - 1, max(0, round(t * (len(widths) - 1))))
        estimated = widths[source_index] / max(nib_width_px * nib_factor, 1e-6)
        samples.append(float(max(0.12, min(1.2, estimated))))
    return samples


def _estimate_nib_angle_curve(
    segment: BezierSegment,
    info: dict[str, Any],
    *,
    baseline_nib_angle_deg: float,
    nib_width_px: float,
) -> tuple[list[float], list[float]]:
    widths = list(info["widths_px"])
    if not widths:
        return [float(baseline_nib_angle_deg)] * 4, [0.0] * 4
    pressures = list(info.get("pressure_curve") or segment.pressure_curve or [0.5, 0.5, 0.5, 0.5])
    angles: list[float] = []
    confidences: list[float] = []
    for knot_index in range(4):
        t = knot_index / 3 if 3 else 0.0
        direction_deg = _segment_direction_deg(segment, t=t)
        source_index = min(len(widths) - 1, max(0, round(t * (len(widths) - 1))))
        pressure_index = min(len(pressures) - 1, max(0, round(t * (len(pressures) - 1))))
        width_px = max(0.0, float(widths[source_index]))
        pressure = max(0.12, float(pressures[pressure_index]))
        sin_val = width_px / max(nib_width_px * pressure, 1e-6)
        sin_val = float(max(0.0, min(1.0, sin_val)))
        primary_delta = math.degrees(math.asin(sin_val))
        secondary_delta = max(0.0, 180.0 - primary_delta)
        candidate_angles: list[float] = []
        for delta in (primary_delta, secondary_delta):
            candidate_angles.append(_normalize_angle_near(direction_deg - delta, baseline_nib_angle_deg))
            candidate_angles.append(_normalize_angle_near(direction_deg + delta, baseline_nib_angle_deg))
        chosen = min(candidate_angles, key=lambda angle: _angle_distance_deg(angle, baseline_nib_angle_deg))
        clamped = float(min(55.0, max(25.0, chosen)))
        baseline_delta_rad = math.radians(_angle_distance_deg(direction_deg, baseline_nib_angle_deg))
        geometry_term = abs(math.sin(2.0 * baseline_delta_rad))
        width_term = max(0.0, 1.0 - abs(sin_val - 0.5) / 0.5)
        fit_term = float(max(0.0, min(1.0, info.get("fit_score", 0.0))))
        confidence = float(max(0.0, min(1.0, 0.1 + 0.45 * geometry_term + 0.25 * width_term + 0.2 * fit_term)))
        angles.append(clamped)
        confidences.append(confidence)
    return angles, confidences


def _segment_direction_deg(segment: BezierSegment, *, t: float = 0.5) -> float:
    dx, dy = segment.tangent(t)
    return math.degrees(math.atan2(dy, dx)) % 360.0


def _mean_angle_deg(angles: list[float]) -> float:
    if not angles:
        return 90.0
    sin_sum = sum(math.sin(math.radians(angle)) for angle in angles)
    cos_sum = sum(math.cos(math.radians(angle)) for angle in angles)
    if abs(sin_sum) < 1e-9 and abs(cos_sum) < 1e-9:
        return angles[0] % 360.0
    return math.degrees(math.atan2(sin_sum, cos_sum)) % 360.0


def _angle_distance_deg(left: float, right: float) -> float:
    delta = abs((left - right + 180.0) % 360.0 - 180.0)
    return float(delta)


def _normalize_angle_near(angle_deg: float, baseline_deg: float) -> float:
    normalized = float(angle_deg)
    while normalized - baseline_deg > 180.0:
        normalized -= 360.0
    while baseline_deg - normalized > 180.0:
        normalized += 360.0
    return normalized


def _proposal_confidence(total_cost: float, stroke_count: int) -> float:
    if stroke_count <= 0:
        return 0.0
    mean_cost = total_cost / max(stroke_count, 1)
    return float(max(0.0, min(1.0, 1.0 / (1.0 + mean_cost * 1.4))))


def _proposal_issues(grouping: dict[str, Any], strokes: list[dict[str, Any]], template: tuple[ExpectedStroke, ...]) -> list[str]:
    issues: list[str] = []
    if grouping.get("fallback"):
        issues.append("stroke alignment fell back to proportional grouping; inspect stroke order closely")
    if len(strokes) != len(template):
        issues.append("traced primitives did not match the template stroke count exactly")
    highest = max((stroke["cost"] for stroke in strokes), default=0.0)
    if highest > 1.0:
        worst = max(strokes, key=lambda stroke: stroke["cost"])
        issues.append(f'{worst["name"]} has the highest decomposition cost and likely needs review')
    weakest_fit = min((stroke.get("fit_score", 1.0) for stroke in strokes), default=1.0)
    if weakest_fit < 0.45 and strokes:
        weakest = min(strokes, key=lambda stroke: stroke.get("fit_score", 1.0))
        issues.append(f'{weakest["name"]} is weakly supported by the darkest ink and likely needs manual adjustment')
    return issues


def _to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3:
        return np.mean(image[:, :, :3], axis=2).astype(np.uint8)
    return image.astype(np.uint8)


def _binarize(gray: np.ndarray, *, ink_threshold: int | None = None) -> np.ndarray:
    limit = int(ink_threshold) if ink_threshold is not None else int(otsu_threshold(gray))
    return gray < limit


def _ink_strength(gray: np.ndarray) -> np.ndarray:
    return np.clip((255.0 - gray.astype(np.float32)) / 255.0, 0.0, 1.0)


def _sample_ink(ink: np.ndarray, point: tuple[float, float]) -> float:
    x = int(round(point[0]))
    y = int(round(point[1]))
    x = min(max(x, 0), ink.shape[1] - 1)
    y = min(max(y, 0), ink.shape[0] - 1)
    return float(ink[y, x])


def _sample_peak_ink(ink: np.ndarray, point: tuple[float, float], radius: int = 1) -> float:
    if ink.size == 0 or ink.shape[0] <= 0 or ink.shape[1] <= 0:
        return 0.0
    x = int(round(point[0]))
    y = int(round(point[1]))
    x0 = max(0, x - radius)
    x1 = max(0, min(ink.shape[1], x + radius + 1))
    y0 = max(0, y - radius)
    y1 = max(0, min(ink.shape[0], y + radius + 1))
    if x0 >= x1 or y0 >= y1:
        return 0.0
    window = ink[y0:y1, x0:x1]
    if window.size == 0:
        return 0.0
    return float(np.max(window))


def _segment_image_fit_score(ink: np.ndarray, segment: BezierSegment, baseline_length: float) -> float:
    sample_points = [segment.evaluate(step / 24) for step in range(25)]
    center_darkness = float(sum(_sample_ink(ink, point) for point in sample_points) / len(sample_points))
    ridge_darkness = float(sum(_sample_peak_ink(ink, point) for point in sample_points) / len(sample_points))
    endpoint_darkness = float((_sample_peak_ink(ink, segment.p0) + _sample_peak_ink(ink, segment.p3)) * 0.5)
    off_ink_ratio = float(sum(1 for point in sample_points if _sample_peak_ink(ink, point) < 0.10) / len(sample_points))
    length_penalty = abs(segment.length() - baseline_length) / max(baseline_length, 1.0)
    return float(center_darkness * 1.2 + ridge_darkness * 0.9 + endpoint_darkness * 0.35 - off_ink_ratio * 0.9 - length_penalty * 0.15)


def _offset_segment_point(segment: BezierSegment, point_key: str, dx: float, dy: float) -> BezierSegment:
    points = {
        "p0": segment.p0,
        "p1": segment.p1,
        "p2": segment.p2,
        "p3": segment.p3,
    }
    point = points[point_key]
    points[point_key] = (float(point[0] + dx), float(point[1] + dy))
    return BezierSegment(
        p0=points["p0"],
        p1=points["p1"],
        p2=points["p2"],
        p3=points["p3"],
        contact=segment.contact,
        pressure_curve=list(segment.pressure_curve),
        speed_curve=list(segment.speed_curve),
        nib_angle_drift=segment.nib_angle_drift,
    )


def _segment_within_margin(segment: BezierSegment, image_shape: tuple[int, int], margin: float) -> bool:
    width = float(image_shape[1])
    height = float(image_shape[0])
    for point in (segment.p0, segment.p1, segment.p2, segment.p3):
        if point[0] < -margin or point[1] < -margin:
            return False
        if point[0] > width + margin or point[1] > height + margin:
            return False
    return True


def _refine_segment_to_ink(ink: np.ndarray, segment: BezierSegment) -> BezierSegment:
    baseline_length = max(segment.length(), 1.0)
    candidate = segment
    image_span = float(min(ink.shape[0], ink.shape[1]))
    for radius in (max(1.5, image_span * 0.05), max(0.75, image_span * 0.025)):
        improved = True
        while improved:
            improved = False
            for point_key in ("p0", "p1", "p2", "p3"):
                best_segment = candidate
                best_score = _segment_image_fit_score(ink, candidate, baseline_length)
                for dy in (-radius, 0.0, radius):
                    for dx in (-radius, 0.0, radius):
                        if dx == 0.0 and dy == 0.0:
                            continue
                        trial = _offset_segment_point(candidate, point_key, dx, dy)
                        if not _segment_within_margin(trial, ink.shape, margin=max(4.0, radius * 2.0)):
                            continue
                        score = _segment_image_fit_score(ink, trial, baseline_length)
                        if score > best_score + 1e-4:
                            best_segment = trial
                            best_score = score
                if best_segment is not candidate:
                    candidate = best_segment
                    improved = True
    return candidate


def _extract_candidate_segments(
    gray: np.ndarray,
    ink: np.ndarray,
    binary: np.ndarray,
    *,
    desired_stroke_count: int | None,
    ink_threshold: int,
    max_bezier_error: float,
) -> list[BezierSegment]:
    target_count = max(1, int(desired_stroke_count) if desired_stroke_count else 3)
    extracted = _extract_path_segments(binary, ink, limit=max(6, target_count * 4))
    traced = trace_centerline(gray, ink_threshold=ink_threshold, max_bezier_error=max_bezier_error)
    combined = extracted + list(traced)
    refined = [_refine_segment_to_ink(ink, segment) for segment in combined]
    return _deduplicate_segments(ink, refined, limit=max(4, target_count * 4))


def _extract_path_segments(binary: np.ndarray, ink: np.ndarray, *, limit: int) -> list[BezierSegment]:
    if binary.size == 0 or not binary.any():
        return []
    dt = distance_transform_edt(binary)
    anchors = _candidate_anchors(binary, dt, ink, limit=max(6, min(12, limit + 2)))
    if len(anchors) < 2:
        return []
    candidates: list[tuple[float, BezierSegment]] = []
    for left_index in range(len(anchors)):
        for right_index in range(left_index + 1, len(anchors)):
            start = anchors[left_index]
            end = anchors[right_index]
            if math.dist(start, end) < max(binary.shape) * 0.12:
                continue
            path = _shortest_ink_path(binary, ink, dt, start, end)
            if len(path) < 6:
                continue
            segment = _fit_path_to_bezier(path)
            segment = _refine_segment_to_ink(ink, segment)
            score = _segment_image_fit_score(ink, segment, max(segment.length(), 1.0))
            candidates.append((float(score), segment))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [segment for _, segment in candidates[:limit]]


def _candidate_anchors(binary: np.ndarray, dt: np.ndarray, ink: np.ndarray, *, limit: int) -> list[tuple[float, float]]:
    coords = np.argwhere(binary)
    if coords.size == 0:
        return []
    anchors: list[tuple[float, float]] = []
    top = coords[np.argmin(coords[:, 0])]
    bottom = coords[np.argmax(coords[:, 0])]
    left = coords[np.argmin(coords[:, 1])]
    right = coords[np.argmax(coords[:, 1])]
    for row, col in (top, bottom, left, right):
        anchors.append((float(col), float(row)))
    peak_mask = (dt == maximum_filter(dt, size=5)) & binary & (dt > max(1.0, float(np.max(dt)) * 0.18))
    peak_coords = np.argwhere(peak_mask)
    peak_coords = sorted(
        peak_coords,
        key=lambda rc: float(dt[rc[0], rc[1]] * (0.5 + ink[rc[0], rc[1]])),
        reverse=True,
    )
    for row, col in peak_coords[: max(2, limit)]:
        anchors.append((float(col), float(row)))
    deduped: list[tuple[float, float]] = []
    min_distance = max(3.0, min(binary.shape) * 0.08)
    for point in anchors:
        if any(math.dist(point, existing) < min_distance for existing in deduped):
            continue
        deduped.append(point)
        if len(deduped) >= limit:
            break
    return deduped


def _shortest_ink_path(
    binary: np.ndarray,
    ink: np.ndarray,
    dt: np.ndarray,
    start: tuple[float, float],
    end: tuple[float, float],
) -> list[tuple[float, float]]:
    start_rc = (int(round(start[1])), int(round(start[0])))
    end_rc = (int(round(end[1])), int(round(end[0])))
    start_rc = (
        min(max(start_rc[0], 0), binary.shape[0] - 1),
        min(max(start_rc[1], 0), binary.shape[1] - 1),
    )
    end_rc = (
        min(max(end_rc[0], 0), binary.shape[0] - 1),
        min(max(end_rc[1], 0), binary.shape[1] - 1),
    )
    if not binary[start_rc] or not binary[end_rc]:
        return []
    max_dt = max(float(np.max(dt)), 1.0)
    heap: list[tuple[float, tuple[int, int]]] = [(0.0, start_rc)]
    distance: dict[tuple[int, int], float] = {start_rc: 0.0}
    previous: dict[tuple[int, int], tuple[int, int] | None] = {start_rc: None}
    neighbours = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    )
    while heap:
        cost, node = heapq.heappop(heap)
        if node == end_rc:
            break
        if cost > distance.get(node, math.inf):
            continue
        for dy, dx in neighbours:
            nr = node[0] + dy
            nc = node[1] + dx
            if nr < 0 or nr >= binary.shape[0] or nc < 0 or nc >= binary.shape[1]:
                continue
            if not binary[nr, nc]:
                continue
            step = math.sqrt(2.0) if dx and dy else 1.0
            darkness = float(ink[nr, nc])
            ridge = float(dt[nr, nc] / max_dt)
            travel = step * (1.8 - darkness * 0.9 - ridge * 0.6)
            next_cost = cost + max(0.05, travel)
            next_node = (nr, nc)
            if next_cost + 1e-9 < distance.get(next_node, math.inf):
                distance[next_node] = next_cost
                previous[next_node] = node
                heapq.heappush(heap, (next_cost, next_node))
    if end_rc not in previous:
        return []
    path: list[tuple[float, float]] = []
    current: tuple[int, int] | None = end_rc
    while current is not None:
        path.append((float(current[1]), float(current[0])))
        current = previous.get(current)
    path.reverse()
    return _simplify_path_points(path)


def _simplify_path_points(path: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if len(path) <= 8:
        return path
    simplified = [path[0]]
    step = max(1, len(path) // 12)
    for index in range(step, len(path) - 1, step):
        simplified.append(path[index])
    simplified.append(path[-1])
    return simplified


def _fit_path_to_bezier(path: list[tuple[float, float]]) -> BezierSegment:
    points = list(path)
    if len(points) < 4:
        start = points[0]
        end = points[-1]
        return BezierSegment(p0=start, p1=start, p2=end, p3=end)
    cumulative = [0.0]
    for left, right in zip(points, points[1:]):
        cumulative.append(cumulative[-1] + math.dist(left, right))
    total = max(cumulative[-1], 1.0)
    p0 = points[0]
    p1 = _path_point_at_fraction(points, cumulative, total, 1.0 / 3.0)
    p2 = _path_point_at_fraction(points, cumulative, total, 2.0 / 3.0)
    p3 = points[-1]
    return BezierSegment(p0=p0, p1=p1, p2=p2, p3=p3)


def _path_point_at_fraction(
    points: list[tuple[float, float]],
    cumulative: list[float],
    total: float,
    fraction: float,
) -> tuple[float, float]:
    target = total * fraction
    for index in range(1, len(points)):
        if cumulative[index] < target:
            continue
        span = max(cumulative[index] - cumulative[index - 1], 1e-6)
        alpha = (target - cumulative[index - 1]) / span
        left = points[index - 1]
        right = points[index]
        return (
            float(left[0] * (1.0 - alpha) + right[0] * alpha),
            float(left[1] * (1.0 - alpha) + right[1] * alpha),
        )
    return points[-1]


def _deduplicate_segments(ink: np.ndarray, segments: list[BezierSegment], *, limit: int) -> list[BezierSegment]:
    ranked = sorted(
        segments,
        key=lambda segment: _segment_image_fit_score(ink, segment, max(segment.length(), 1.0)),
        reverse=True,
    )
    accepted: list[BezierSegment] = []
    for segment in ranked:
        if any(_segments_similar(segment, existing) for existing in accepted):
            continue
        accepted.append(segment)
        if len(accepted) >= limit:
            break
    return accepted


def _segments_similar(left: BezierSegment, right: BezierSegment) -> bool:
    direct = math.dist(left.p0, right.p0) + math.dist(left.p3, right.p3)
    reverse = math.dist(left.p0, right.p3) + math.dist(left.p3, right.p0)
    return min(direct, reverse) < 10.0


def _select_segments_for_count(candidate_infos: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    remaining = list(candidate_infos)
    selected: list[dict[str, Any]] = []
    covered: set[tuple[int, int]] = set()
    while remaining and len(selected) < count:
        best_index = 0
        best_score = -math.inf
        for index, info in enumerate(remaining):
            points = {
                (int(round(point[0])), int(round(point[1])))
                for point in info["points"]
            }
            new_coverage = len(points - covered)
            overlap = len(points & covered)
            score = float(info["fit_score"]) * 1.4 + float(info["center_darkness"]) * 0.5 + new_coverage * 0.03 - overlap * 0.02
            if score > best_score:
                best_score = score
                best_index = index
        chosen = remaining.pop(best_index)
        selected.append(chosen)
        covered.update({(int(round(point[0])), int(round(point[1]))) for point in chosen["points"]})
    selected.sort(key=lambda info: (float(info["center"][0]), -float(info["center"][1])))
    return selected


def _max_auto_stroke_count(symbol: str, primitive_infos: list[dict[str, Any]]) -> int:
    template_count = len(_STROKE_TEMPLATES.get(str(symbol), (ExpectedStroke("main_stroke", "Down", "Heavy"),)))
    return max(1, min(template_count, len(primitive_infos)))


def _candidate_objective(grouping: dict[str, Any], *, stroke_count: int) -> float:
    fallback_penalty = 0.35 if grouping.get("fallback") else 0.0
    stroke_penalty = max(0, stroke_count - 1) * 0.22
    return float(grouping["total_cost"] + fallback_penalty + stroke_penalty)
