"""Plan generation from DensePathGuide for TD-014."""

from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace

from scribesim.pathguide import DensePathGuide

from .model import TrackPlan, TrackPlanSample


AIR_BRAKING_VERSION = "braked-air-v1"


@dataclass(frozen=True)
class BrakedPlan:
    plan: TrackPlan
    source_indices: tuple[int, ...]
    arrivals: tuple[dict, ...]
    version: str = AIR_BRAKING_VERSION


def _contact_clock(distance, length, stop):
    acceleration = 250.0
    peak = min(12.0, math.sqrt(acceleration * length)) if stop else 12.0
    ramp = peak ** 2 / (2 * acceleration)
    if stop and distance >= length - ramp:
        remaining = max(0.0, length - distance)
        duration = 2 * peak / acceleration + (length - 2 * ramp) / peak if peak else 0
        return duration - math.sqrt(2 * remaining / acceleration), math.sqrt(2 * acceleration * remaining)
    if distance <= ramp:
        return math.sqrt(2 * distance / acceleration), math.sqrt(2 * acceleration * distance)
    return peak / acceleration + (distance - ramp) / peak, peak


def retime_air_braking(plan: TrackPlan) -> BrakedPlan:
    """Opt-in fixed-tool braking, rest-to-rest air travel and contact acceleration."""
    if not plan.samples or not plan.samples[0].contact or not plan.samples[-1].contact:
        raise ValueError("Braking requires complete contact-bounded input")
    first = plan.samples[0]
    for sample in plan.samples:
        if any(not math.isfinite(getattr(sample, field.name)) for field in fields(sample)):
            raise ValueError("Nonfinite braking input")
        if sample.nib_angle_deg != first.nib_angle_deg or any(
                getattr(sample, name, None) != getattr(first, name, None) for name in ('edge_start', 'edge_end')):
            raise ValueError("Braking requires a fixed tool profile")
        if sample.contact and sample.speed_mm_s not in (0, 12):
            raise ValueError("Braking requires the frozen nominal contact speed")
    if first.t_s != 0 or any(after.t_s < before.t_s for before, after in zip(plan.samples, plan.samples[1:])):
        raise ValueError("Braking requires ordered zero-origin time")
    acceleration, air_speed, sample_time = 250.0, 16.2, .001
    samples, indices, arrivals = [], [], []
    elapsed, arc, contact_distance = 0.0, 0.0, 0.0

    def append(source, index, **changes):
        nonlocal arc
        if len(samples) >= 100000:
            raise ValueError("Braking plan sample budget exceeded")
        point = replace(source, **changes)
        if samples:
            arc += math.dist((samples[-1].x_mm, samples[-1].y_mm), (point.x_mm, point.y_mm))
        samples.append(replace(point, arc_length_mm=arc))
        indices.append(index)

    cursor = 0
    pending_arrival = None
    while cursor < len(plan.samples):
        source = plan.samples[cursor]
        if source.contact:
            beginning = cursor == 0 or not plan.samples[cursor - 1].contact
            if beginning:
                contact_distance, speed = 0.0, 0.0
                contact_start = elapsed
                contact_end = cursor
                while contact_end + 1 < len(plan.samples) and plan.samples[contact_end + 1].contact:
                    contact_end += 1
                contact_length = sum(math.dist((before.x_mm, before.y_mm), (after.x_mm, after.y_mm))
                                     for before, after in zip(plan.samples[cursor:contact_end], plan.samples[cursor + 1:contact_end + 1]))
                stop = plan.samples[contact_end].speed_mm_s == 0
            else:
                previous = samples[-1]
                distance = math.dist((previous.x_mm, previous.y_mm), (source.x_mm, source.y_mm))
                contact_distance += distance
                local_time, speed = _contact_clock(contact_distance, contact_length, stop)
                elapsed = contact_start + local_time
            ratio = speed / source.speed_mm_s if source.speed_mm_s else 0
            append(source, cursor, t_s=elapsed, speed_mm_s=speed,
                   vx_mm_s=source.vx_mm_s * ratio, vy_mm_s=source.vy_mm_s * ratio)
            if pending_arrival is not None:
                arrivals.append({**pending_arrival, 'entry_time_s': elapsed, 'plan_index': len(samples) - 1})
                pending_arrival = None
            cursor += 1
            continue
        end = cursor
        while not plan.samples[end].contact:
            end += 1
        entry = plan.samples[end]
        previous = samples[-1]
        origin = previous.x_mm, previous.y_mm
        velocity = previous.vx_mm_s, previous.vy_mm_s
        duration = math.hypot(*velocity) / acceleration
        lift_time = elapsed
        append(source, cursor, t_s=elapsed, x_mm=origin[0], y_mm=origin[1],
               vx_mm_s=velocity[0], vy_mm_s=velocity[1], speed_mm_s=math.hypot(*velocity), pressure=0)
        steps = max(1, math.ceil(duration / sample_time))
        for step in range(1, steps + 1):
            fraction = step / steps
            local_time = duration * fraction
            append(source, cursor, t_s=elapsed + local_time,
                   x_mm=origin[0] + velocity[0] * local_time * (1 - fraction / 2),
                   y_mm=origin[1] + velocity[1] * local_time * (1 - fraction / 2),
                   vx_mm_s=velocity[0] * (1 - fraction), vy_mm_s=velocity[1] * (1 - fraction),
                   speed_mm_s=math.hypot(*velocity) * (1 - fraction), pressure=0)
        elapsed += duration
        stopped = samples[-1]
        displacement = entry.x_mm - stopped.x_mm, entry.y_mm - stopped.y_mm
        length = math.hypot(*displacement)
        travel = max(1.875 * length / air_speed, math.sqrt(10 / math.sqrt(3) * length / acceleration), sample_time)
        steps = math.ceil(travel / sample_time)
        for step in range(1, steps + 1):
            fraction = step / steps
            position = fraction ** 3 * (10 - 15 * fraction + 6 * fraction ** 2)
            rate = 30 * fraction ** 2 * (1 - fraction) ** 2 / travel
            append(plan.samples[end - 1], end - 1, t_s=elapsed + travel * fraction,
                   x_mm=entry.x_mm if step == steps else stopped.x_mm + displacement[0] * position,
                   y_mm=entry.y_mm if step == steps else stopped.y_mm + displacement[1] * position,
                   vx_mm_s=displacement[0] * rate, vy_mm_s=displacement[1] * rate,
                   speed_mm_s=length * rate, pressure=0)
        elapsed += travel
        pending_arrival = {'lift_time_s': lift_time, 'brake_time_s': duration, 'travel_time_s': travel,
                           'planned_air_acceleration_max_mm_s2': acceleration, 'source_entry_index': end}
        cursor = end
    return BrakedPlan(replace(plan, samples=tuple(samples)), tuple(indices), tuple(arrivals))


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
                nib_angle_deg=sample.nib_angle_deg,
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
            nib_angle_deg=current.nib_angle_deg * (1.0 - alpha) + nxt.nib_angle_deg * alpha,
            contact=current.contact if alpha < 0.5 else nxt.contact,
            corridor_half_width_mm=(
                current.corridor_half_width_mm * (1.0 - alpha)
                + nxt.corridor_half_width_mm * alpha
            ),
            progress_ratio=current.progress_ratio * (1.0 - alpha) + nxt.progress_ratio * alpha,
        )

    return plan.samples[-1]
