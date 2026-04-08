"""Import/export helpers for dense path guides."""

from __future__ import annotations

import bisect
import math
import tomllib
from pathlib import Path

from scribesim.guides.keypoint import LetterformGuide
from scribesim.pathguide.model import DensePathGuide, GuideSample, GuideSource
from scribesim.pathguide.validate import assert_valid_dense_path_guide
from scribesim.refextract.centerline import load_trace


def _unit_vector(dx: float, dy: float) -> tuple[float, float]:
    norm = math.hypot(dx, dy)
    if norm <= 1e-9:
        return (1.0, 0.0)
    return (dx / norm, dy / norm)


def _interpolate_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    max_step_mm: float,
) -> list[tuple[float, float]]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    distance = math.hypot(dx, dy)
    if distance <= 1e-9:
        return [start]
    segments = max(1, math.ceil(distance / max_step_mm))
    points = []
    for idx in range(segments + 1):
        t = idx / segments
        points.append((start[0] * (1.0 - t) + end[0] * t, start[1] * (1.0 - t) + end[1] * t))
    return points


def _build_samples_from_waypoints(
    waypoints: list[tuple[float, float, bool]],
    *,
    default_speed: float,
    default_pressure: float,
    default_nib_angle_deg: float,
    corridor_half_width_mm: float,
    max_step_mm: float = 0.25,
) -> tuple[GuideSample, ...]:
    samples: list[GuideSample] = []
    for idx in range(len(waypoints) - 1):
        x0, y0, c0 = waypoints[idx]
        x1, y1, c1 = waypoints[idx + 1]
        tangent = _unit_vector(x1 - x0, y1 - y0)
        dense_points = _interpolate_segment((x0, y0), (x1, y1), max_step_mm=max_step_mm)
        for point_index, (x_mm, y_mm) in enumerate(dense_points):
            if samples and point_index == 0:
                continue
            samples.append(
                GuideSample(
                    x_mm=x_mm,
                    y_mm=y_mm,
                    tangent_dx=tangent[0],
                    tangent_dy=tangent[1],
                    contact=c0 and c1,
                    speed_nominal=default_speed,
                    pressure_nominal=default_pressure,
                    nib_angle_deg=default_nib_angle_deg,
                    nib_angle_confidence=0.0,
                    corridor_half_width_mm=corridor_half_width_mm,
                )
            )

    return tuple(samples)


def _sample_trace_segment_by_arclength(
    seg,
    *,
    x_height_px: float,
    x_height_mm: float,
    target_sample_step_mm: float,
    min_samples_per_segment: int = 12,
    nib_angle_curve_deg: list[float] | tuple[float, ...] | None = None,
    nib_angle_confidence_curve: list[float] | tuple[float, ...] | None = None,
) -> list[tuple[float, float, float, float, bool, float, float, float, float]]:
    length_mm = seg.length() / x_height_px * x_height_mm
    sample_count = max(min_samples_per_segment, math.ceil(length_mm / target_sample_step_mm))
    probe_count = max(sample_count * 8, 128)

    probe_ts = [idx / probe_count for idx in range(probe_count + 1)]
    probe_points = [seg.evaluate(t) for t in probe_ts]
    cumulative_px = [0.0]
    for idx in range(1, len(probe_points)):
        x0, y0 = probe_points[idx - 1]
        x1, y1 = probe_points[idx]
        cumulative_px.append(cumulative_px[-1] + math.hypot(x1 - x0, y1 - y0))

    total_length_px = cumulative_px[-1]
    if total_length_px <= 1e-9:
        sample_ts = [0.0]
    else:
        sample_ts: list[float] = []
        for idx in range(sample_count + 1):
            target_length_px = total_length_px * (idx / sample_count)
            probe_index = bisect.bisect_left(cumulative_px, target_length_px)
            if probe_index <= 0:
                sample_ts.append(0.0)
                continue
            if probe_index >= len(cumulative_px):
                sample_ts.append(1.0)
                continue
            left_len = cumulative_px[probe_index - 1]
            right_len = cumulative_px[probe_index]
            left_t = probe_ts[probe_index - 1]
            right_t = probe_ts[probe_index]
            if right_len - left_len <= 1e-9:
                sample_ts.append(left_t)
                continue
            frac = (target_length_px - left_len) / (right_len - left_len)
            sample_ts.append(left_t * (1.0 - frac) + right_t * frac)

    raw_points: list[tuple[float, float, float, float, bool, float, float, float, float]] = []
    for t in sample_ts:
        x_px, y_px = seg.evaluate(t)
        dx, dy = seg.tangent(t)
        tangent = _unit_vector(dx, dy)
        nib_angle_deg = float(_interp_curve(nib_angle_curve_deg or [40.0, 40.0, 40.0, 40.0], t))
        nib_angle_confidence = float(_interp_curve(nib_angle_confidence_curve or [0.0, 0.0, 0.0, 0.0], t))
        raw_points.append(
            (
                x_px,
                y_px,
                tangent[0],
                tangent[1],
                seg.contact,
                float(seg.speed_at(t)),
                float(seg.pressure_at(t)),
                nib_angle_deg,
                nib_angle_confidence,
            )
        )
    return raw_points


def _bridge_trace_points(
    start: tuple[float, float, float, float, bool, float, float, float, float],
    end: tuple[float, float, float, float, bool, float, float, float, float],
    *,
    x_height_px: float,
    x_height_mm: float,
    target_sample_step_mm: float,
) -> list[tuple[float, float, float, float, bool, float, float, float, float]]:
    start_xy = (start[0], start[1])
    end_xy = (end[0], end[1])
    max_step_px = max(1e-6, target_sample_step_mm / x_height_mm * x_height_px)
    dense_points = _interpolate_segment(start_xy, end_xy, max_step_mm=max_step_px)
    tangent = _unit_vector(end_xy[0] - start_xy[0], end_xy[1] - start_xy[1])
    return [
        (
            x_px,
            y_px,
            tangent[0],
            tangent[1],
            False,
            1.0,
            0.0,
            float(start[7] * 0.5 + end[7] * 0.5),
            0.0,
        )
        for x_px, y_px in dense_points
    ]


def guide_from_waypoints(
    symbol: str,
    waypoints_xh: list[tuple[float, float, bool]],
    *,
    x_height_mm: float,
    x_advance_xh: float,
    kind: str = "glyph",
    default_speed: float = 1.0,
    default_pressure: float = 0.5,
    default_nib_angle_deg: float = 40.0,
    corridor_half_width_mm: float = 0.2,
    source_id: str,
    source_path: str | None = None,
    extraction_run: str | None = None,
    confidence_tier: str = "accepted",
    split: str = "train",
    source_resolution_ppmm: float | None = None,
) -> DensePathGuide:
    """Create a dense guide from x-height-relative waypoints."""

    waypoints_mm = [(x * x_height_mm, y * x_height_mm, contact) for x, y, contact in waypoints_xh]
    samples = _build_samples_from_waypoints(
        waypoints_mm,
        default_speed=default_speed,
        default_pressure=default_pressure,
        default_nib_angle_deg=default_nib_angle_deg,
        corridor_half_width_mm=corridor_half_width_mm,
    )
    sources = (
        GuideSource(
            source_id=source_id,
            source_path=source_path,
            extraction_run=extraction_run,
            confidence_tier=confidence_tier,
            split=split,
            source_resolution_ppmm=source_resolution_ppmm,
        ),
    )
    guide = DensePathGuide(
        symbol=symbol,
        kind=kind,
        samples=samples,
        x_advance_mm=x_advance_xh * x_height_mm,
        x_height_mm=x_height_mm,
        entry_tangent=(samples[0].tangent_dx, samples[0].tangent_dy),
        exit_tangent=(samples[-1].tangent_dx, samples[-1].tangent_dy),
        sources=sources,
    )
    assert_valid_dense_path_guide(guide)
    return guide


def guide_from_letterform_guide(
    guide: LetterformGuide,
    *,
    x_height_mm: float,
    kind: str = "glyph",
    default_speed: float = 1.0,
    default_pressure: float = 0.5,
    corridor_half_width_mm: float = 0.2,
    source_id: str | None = None,
    source_path: str | None = None,
    extraction_run: str | None = None,
    confidence_tier: str = "accepted",
    split: str = "train",
    source_resolution_ppmm: float | None = None,
) -> DensePathGuide:
    """Convert a sparse LetterformGuide into a dense path guide."""

    waypoints_xh = [(kp.x, kp.y, kp.contact) for kp in guide.keypoints]
    return guide_from_waypoints(
        guide.letter,
        waypoints_xh,
        x_height_mm=x_height_mm,
        x_advance_xh=guide.x_advance,
        kind=kind,
        default_speed=default_speed,
        default_pressure=default_pressure,
        corridor_half_width_mm=corridor_half_width_mm,
        source_id=source_id or f"legacy-guide:{guide.letter}",
        source_path=source_path,
        extraction_run=extraction_run,
        confidence_tier=confidence_tier,
        split=split,
        source_resolution_ppmm=source_resolution_ppmm,
    )


def guide_from_trace_segments(
    symbol: str,
    segments,
    *,
    x_height_px: float,
    x_height_mm: float,
    kind: str = "glyph",
    default_corridor_half_width_mm: float = 0.2,
    target_sample_step_mm: float = 0.10,
    stroke_ids: list[int] | tuple[int, ...] | None = None,
    nib_angle_curves_deg: list[list[float] | tuple[float, ...]] | tuple[list[float] | tuple[float, ...], ...] | None = None,
    nib_angle_confidence_curves: list[list[float] | tuple[float, ...]] | tuple[list[float] | tuple[float, ...], ...] | None = None,
    source_id: str,
    source_path: str | None = None,
    extraction_run: str | None = None,
    confidence_tier: str = "accepted",
    split: str = "train",
    source_resolution_ppmm: float | None = None,
) -> DensePathGuide:
    """Build a dense guide directly from traced Bezier segments."""

    raw_points: list[tuple[float, float, float, float, bool, float, float]] = []
    if stroke_ids is not None and len(stroke_ids) != len(segments):
        raise ValueError("stroke_ids must match the number of trace segments")
    if nib_angle_curves_deg is not None and len(nib_angle_curves_deg) != len(segments):
        raise ValueError("nib_angle_curves_deg must match the number of trace segments")
    if nib_angle_confidence_curves is not None and len(nib_angle_confidence_curves) != len(segments):
        raise ValueError("nib_angle_confidence_curves must match the number of trace segments")
    previous_stroke_id = None

    for seg_index, seg in enumerate(segments):
        segment_points = _sample_trace_segment_by_arclength(
            seg,
            x_height_px=x_height_px,
            x_height_mm=x_height_mm,
            target_sample_step_mm=target_sample_step_mm,
            nib_angle_curve_deg=(nib_angle_curves_deg[seg_index] if nib_angle_curves_deg is not None else None),
            nib_angle_confidence_curve=(
                nib_angle_confidence_curves[seg_index]
                if nib_angle_confidence_curves is not None
                else None
            ),
        )
        current_stroke_id = stroke_ids[seg_index] if stroke_ids is not None else None
        inserted_bridge = False
        if (
            raw_points
            and stroke_ids is not None
            and previous_stroke_id is not None
            and current_stroke_id != previous_stroke_id
        ):
            bridge_points = _bridge_trace_points(
                raw_points[-1],
                segment_points[0],
                x_height_px=x_height_px,
                x_height_mm=x_height_mm,
                target_sample_step_mm=target_sample_step_mm,
            )
            for idx, point in enumerate(bridge_points):
                if raw_points and idx == 0:
                    continue
                raw_points.append(point)
            inserted_bridge = True
        for idx, point in enumerate(segment_points):
            if raw_points and idx == 0 and not inserted_bridge:
                continue
            raw_points.append(point)
        previous_stroke_id = current_stroke_id

    if not raw_points:
        raise ValueError(f"trace for {symbol!r} produced no points")

    min_x = min(point[0] for point in raw_points)
    min_y = min(point[1] for point in raw_points)
    points_mm: list[GuideSample] = []
    for x_px, y_px, dx, dy, contact, speed, pressure, nib_angle_deg, nib_angle_confidence in raw_points:
        x_mm = (x_px - min_x) / x_height_px * x_height_mm
        y_mm = (y_px - min_y) / x_height_px * x_height_mm
        points_mm.append(
            GuideSample(
                x_mm=x_mm,
                y_mm=y_mm,
                tangent_dx=dx,
                tangent_dy=dy,
                contact=contact,
                speed_nominal=speed,
                pressure_nominal=pressure,
                nib_angle_deg=nib_angle_deg,
                nib_angle_confidence=nib_angle_confidence,
                corridor_half_width_mm=default_corridor_half_width_mm,
            )
        )

    guide = DensePathGuide(
        symbol=symbol,
        kind=kind,
        samples=tuple(points_mm),
        x_advance_mm=max(sample.x_mm for sample in points_mm),
        x_height_mm=x_height_mm,
        entry_tangent=(points_mm[0].tangent_dx, points_mm[0].tangent_dy),
        exit_tangent=(points_mm[-1].tangent_dx, points_mm[-1].tangent_dy),
        sources=(
            GuideSource(
                source_id=source_id,
                source_path=source_path,
                extraction_run=extraction_run,
                confidence_tier=confidence_tier,
                split=split,
                source_resolution_ppmm=source_resolution_ppmm,
            ),
        ),
    )
    assert_valid_dense_path_guide(guide)
    return guide


def load_trace_as_dense(
    symbol: str,
    trace_path: Path | str,
    *,
    x_height_px: float,
    x_height_mm: float,
    kind: str = "glyph",
    confidence_tier: str = "accepted",
    split: str = "train",
    source_resolution_ppmm: float | None = None,
) -> DensePathGuide:
    """Load a JSON trace written by refextract.centerline and convert it."""

    path = Path(trace_path)
    return guide_from_trace_segments(
        symbol,
        load_trace(path),
        x_height_px=x_height_px,
        x_height_mm=x_height_mm,
        kind=kind,
        source_id=f"trace:{symbol}",
        source_path=path.as_posix(),
        confidence_tier=confidence_tier,
        split=split,
        source_resolution_ppmm=source_resolution_ppmm,
    )


def load_legacy_guides_toml_as_dense(
    path: Path | str,
    *,
    x_height_mm: float,
    default_confidence_tier: str = "accepted",
    split: str = "train",
    source_resolution_ppmm: float | None = None,
) -> dict[str, DensePathGuide]:
    """Load legacy extracted/sparse guide TOML files as dense guides."""

    data = tomllib.loads(Path(path).read_text())
    guides: dict[str, DensePathGuide] = {}
    for symbol, entry in data.items():
        if not isinstance(entry, dict):
            continue
        keypoints = entry.get("keypoints", [])
        if len(keypoints) < 2:
            continue
        waypoints = [
            (
                float(kp["x"]),
                float(kp["y"]),
                bool(kp.get("contact", True)),
            )
            for kp in keypoints
        ]
        guides[symbol] = guide_from_waypoints(
            symbol,
            waypoints,
            x_height_mm=x_height_mm,
            x_advance_xh=float(entry.get("x_advance", max(kp[0] for kp in waypoints))),
            kind="glyph",
            source_id=f"legacy-toml:{symbol}",
            source_path=Path(path).as_posix(),
            confidence_tier=default_confidence_tier,
            split=split,
            source_resolution_ppmm=source_resolution_ppmm,
        )
    return guides


def write_pathguides_toml(guides: dict[str, DensePathGuide], output_path: Path | str) -> None:
    """Write DensePathGuide objects to a TOML catalog."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Dense path guides — scribesim pathguide",
        "schema_version = 1",
        "",
    ]

    for symbol, guide in sorted(guides.items()):
        assert_valid_dense_path_guide(guide)
        lines.append("[[guides]]")
        lines.append(f'symbol = "{symbol}"')
        lines.append(f'kind = "{guide.kind}"')
        lines.append(f"x_advance_mm = {guide.x_advance_mm:.6f}")
        lines.append(f"x_height_mm = {guide.x_height_mm:.6f}")
        lines.append(f"entry_tangent = [{guide.entry_tangent[0]:.6f}, {guide.entry_tangent[1]:.6f}]")
        lines.append(f"exit_tangent = [{guide.exit_tangent[0]:.6f}, {guide.exit_tangent[1]:.6f}]")

        for source in guide.sources:
            lines.append("[[guides.sources]]")
            lines.append(f'source_id = "{source.source_id}"')
            if source.source_path is not None:
                lines.append(f'source_path = "{source.source_path}"')
            if source.extraction_run is not None:
                lines.append(f'extraction_run = "{source.extraction_run}"')
            lines.append(f'confidence_tier = "{source.confidence_tier}"')
            lines.append(f'split = "{source.split}"')
            if source.source_resolution_ppmm is not None:
                lines.append(f"source_resolution_ppmm = {source.source_resolution_ppmm:.6f}")

        for sample in guide.samples:
            lines.append("[[guides.samples]]")
            lines.append(f"x_mm = {sample.x_mm:.6f}")
            lines.append(f"y_mm = {sample.y_mm:.6f}")
            lines.append(f"tangent_dx = {sample.tangent_dx:.6f}")
            lines.append(f"tangent_dy = {sample.tangent_dy:.6f}")
            lines.append(f"contact = {'true' if sample.contact else 'false'}")
            lines.append(f"speed_nominal = {sample.speed_nominal:.6f}")
            lines.append(f"pressure_nominal = {sample.pressure_nominal:.6f}")
            lines.append(f"nib_angle_deg = {sample.nib_angle_deg:.6f}")
            lines.append(f"nib_angle_confidence = {sample.nib_angle_confidence:.6f}")
            lines.append(f"corridor_half_width_mm = {sample.corridor_half_width_mm:.6f}")
        lines.append("")

    output_path.write_text("\n".join(lines))


def load_pathguides_toml(path: Path | str) -> dict[str, DensePathGuide]:
    """Load a DensePathGuide TOML catalog."""

    data = tomllib.loads(Path(path).read_text())
    guides: dict[str, DensePathGuide] = {}
    for entry in data.get("guides", []):
        sources = tuple(
            GuideSource(
                source_id=str(source["source_id"]),
                source_path=source.get("source_path"),
                extraction_run=source.get("extraction_run"),
                confidence_tier=str(source.get("confidence_tier", "accepted")),
                split=str(source.get("split", "train")),
                source_resolution_ppmm=float(source["source_resolution_ppmm"])
                if "source_resolution_ppmm" in source
                else None,
            )
            for source in entry.get("sources", [])
        )
        samples = tuple(
            GuideSample(
                x_mm=float(sample["x_mm"]),
                y_mm=float(sample["y_mm"]),
                tangent_dx=float(sample["tangent_dx"]),
                tangent_dy=float(sample["tangent_dy"]),
                contact=bool(sample.get("contact", True)),
                speed_nominal=float(sample.get("speed_nominal", 1.0)),
                pressure_nominal=float(sample.get("pressure_nominal", 0.5)),
                nib_angle_deg=float(sample.get("nib_angle_deg", 40.0)),
                nib_angle_confidence=float(sample.get("nib_angle_confidence", 0.0)),
                corridor_half_width_mm=float(sample.get("corridor_half_width_mm", 0.2)),
            )
            for sample in entry.get("samples", [])
        )
        guide = DensePathGuide(
            symbol=str(entry["symbol"]),
            kind=str(entry.get("kind", "glyph")),
            samples=samples,
            x_advance_mm=float(entry["x_advance_mm"]),
            x_height_mm=float(entry["x_height_mm"]),
            entry_tangent=tuple(float(v) for v in entry.get("entry_tangent", (1.0, 0.0))),
            exit_tangent=tuple(float(v) for v in entry.get("exit_tangent", (1.0, 0.0))),
            sources=sources,
        )
        assert_valid_dense_path_guide(guide)
        guides[guide.symbol] = guide
    return guides


def _interp_curve(curve: list[float] | tuple[float, ...], t: float) -> float:
    if not curve:
        return 0.0
    if len(curve) == 1:
        return float(curve[0])
    idx_f = t * (len(curve) - 1)
    idx_lo = min(int(idx_f), len(curve) - 2)
    frac = idx_f - idx_lo
    return float(curve[idx_lo] * (1.0 - frac) + curve[idx_lo + 1] * frac)
