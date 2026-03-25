"""Plan generation from DensePathGuide for TD-014."""

from __future__ import annotations

import math

from scribesim.pathguide import DensePathGuide

from .model import TrackPlan, TrackPlanSample


def build_track_plan(
    guide: DensePathGuide,
    *,
    base_speed_mm_s: float = 28.0,
    air_speed_multiplier: float = 1.35,
    stop_at_end: bool = True,
) -> TrackPlan:
    """Convert a dense path guide into a time-indexed desired-state plan."""

    if not guide.samples:
        return TrackPlan(
            guide_symbol=guide.symbol,
            samples=tuple(),
            x_height_mm=guide.x_height_mm,
            x_advance_mm=guide.x_advance_mm,
        )

    plan_samples: list[TrackPlanSample] = []
    t_s = 0.0
    arc_length_mm = 0.0
    segment_lengths = [
        math.dist((sample.x_mm, sample.y_mm), (nxt.x_mm, nxt.y_mm))
        for sample, nxt in zip(guide.samples, guide.samples[1:], strict=False)
    ]
    total_length_mm = sum(segment_lengths)

    for idx, sample in enumerate(guide.samples):
        tangent_norm = math.hypot(sample.tangent_dx, sample.tangent_dy)
        if tangent_norm <= 1e-9:
            tangent = (1.0, 0.0)
        else:
            tangent = (sample.tangent_dx / tangent_norm, sample.tangent_dy / tangent_norm)

        speed_mm_s = max(1.0, sample.speed_nominal * base_speed_mm_s)
        if not sample.contact:
            speed_mm_s *= air_speed_multiplier

        vx_mm_s = tangent[0] * speed_mm_s
        vy_mm_s = tangent[1] * speed_mm_s
        if stop_at_end and idx == len(guide.samples) - 1:
            speed_mm_s = 0.0
            vx_mm_s = 0.0
            vy_mm_s = 0.0

        plan_samples.append(
            TrackPlanSample(
                t_s=t_s,
                arc_length_mm=arc_length_mm,
                x_mm=sample.x_mm,
                y_mm=sample.y_mm,
                vx_mm_s=vx_mm_s,
                vy_mm_s=vy_mm_s,
                speed_mm_s=speed_mm_s,
                pressure=sample.pressure_nominal,
                contact=sample.contact,
                corridor_half_width_mm=sample.corridor_half_width_mm,
                progress_ratio=(
                    min(1.0, arc_length_mm / max(total_length_mm, 1e-9))
                    if total_length_mm > 1e-9
                    else 0.0
                ),
            )
        )

        if idx + 1 < len(guide.samples):
            nxt = guide.samples[idx + 1]
            step = math.dist((sample.x_mm, sample.y_mm), (nxt.x_mm, nxt.y_mm))
            arc_length_mm += step
            next_speed = max(1.0, nxt.speed_nominal * base_speed_mm_s)
            if not nxt.contact:
                next_speed *= air_speed_multiplier
            segment_speed = max(1.0, (speed_mm_s + next_speed) * 0.5)
            t_s += step / segment_speed if step > 1e-9 else 0.0

    return TrackPlan(
        guide_symbol=guide.symbol,
        samples=tuple(plan_samples),
        x_height_mm=guide.x_height_mm,
        x_advance_mm=guide.x_advance_mm,
    )


def sample_plan(plan: TrackPlan, time_s: float) -> TrackPlanSample:
    """Interpolate a plan sample at the requested time."""

    if not plan.samples:
        raise ValueError("cannot sample an empty TrackPlan")
    if time_s <= 0.0 or len(plan.samples) == 1:
        return plan.samples[0]
    if time_s >= plan.total_time_s:
        return plan.samples[-1]

    for idx in range(len(plan.samples) - 1):
        current = plan.samples[idx]
        nxt = plan.samples[idx + 1]
        if time_s > nxt.t_s:
            continue
        dt = max(nxt.t_s - current.t_s, 1e-9)
        alpha = (time_s - current.t_s) / dt
        return TrackPlanSample(
            t_s=time_s,
            arc_length_mm=current.arc_length_mm * (1.0 - alpha) + nxt.arc_length_mm * alpha,
            x_mm=current.x_mm * (1.0 - alpha) + nxt.x_mm * alpha,
            y_mm=current.y_mm * (1.0 - alpha) + nxt.y_mm * alpha,
            vx_mm_s=current.vx_mm_s * (1.0 - alpha) + nxt.vx_mm_s * alpha,
            vy_mm_s=current.vy_mm_s * (1.0 - alpha) + nxt.vy_mm_s * alpha,
            speed_mm_s=current.speed_mm_s * (1.0 - alpha) + nxt.speed_mm_s * alpha,
            pressure=current.pressure * (1.0 - alpha) + nxt.pressure * alpha,
            contact=current.contact if alpha < 0.5 else nxt.contact,
            corridor_half_width_mm=(
                current.corridor_half_width_mm * (1.0 - alpha)
                + nxt.corridor_half_width_mm * alpha
            ),
            progress_ratio=current.progress_ratio * (1.0 - alpha) + nxt.progress_ratio * alpha,
        )

    return plan.samples[-1]
