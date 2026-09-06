"""Guided corridor-following controller for TD-014."""

from __future__ import annotations

import math
import copy
from dataclasses import fields, replace
from bisect import bisect_left, bisect_right

from scribesim.hand.profile import HandProfile
from scribesim.handvalidate import TrajectorySample
from scribesim.pathguide import DensePathGuide
from scribesim.render.nib import PhysicsNib, mark_width

from .model import (
    HandStateV2,
    SessionGuide,
    SessionResult,
    SimulationResult,
    StateTraceEntry,
    TrackPlan,
    TrackPlanSample,
)
from .planning import build_track_plan
from .controls import RepertoireControls


class GuidedHandFlowController:
    """Continuous controller that follows a time-indexed plan inside a corridor."""

    def __init__(
        self,
        profile: HandProfile,
        *,
        corridor_gain: float = 42.0,
        arrival_gain: float = 10.0,
        activate_base_pressure: bool = False,
        repertoire_controls: RepertoireControls | None = None,
        execution_version: str = "legacy-v1",
    ) -> None:
        if execution_version not in {"legacy-v1", "event-time-v1"}:
            raise ValueError("Unsupported handflow execution version")
        self.execution_version = execution_version
        self.profile = profile
        self.dyn = profile.dynamics
        self.corridor_gain = corridor_gain
        self.arrival_gain = arrival_gain
        self.activate_base_pressure = activate_base_pressure
        self.repertoire_controls = repertoire_controls
        self.nib = PhysicsNib(
            width_mm=profile.nib.width_mm,
            angle_deg=profile.nib.angle_deg,
            flexibility=profile.nib.flexibility,
            cut_quality=profile.nib.cut_quality,
            attack_pressure_multiplier=profile.nib.attack_pressure_multiplier,
            release_taper_length=profile.nib.release_taper_length,
        )

    def initial_state(self, plan: TrackPlan) -> HandStateV2:
        desired = plan.samples[0]
        return HandStateV2(
            pos_x_mm=desired.x_mm,
            pos_y_mm=desired.y_mm,
            nib_contact=desired.contact,
            nib_pressure=desired.pressure,
            nib_angle_deg=self.profile.nib.angle_deg,
            ink_reservoir=self.profile.ink.reservoir_capacity,
        )

    def desired_acceleration(
        self,
        state: HandStateV2,
        desired: TrackPlanSample,
    ) -> tuple[float, float]:
        """Compute acceleration from desired state and corridor error."""

        pos_err_x = desired.x_mm - state.pos_x_mm
        pos_err_y = desired.y_mm - state.pos_y_mm
        vel_err_x = desired.vx_mm_s - state.vel_x_mm_s
        vel_err_y = desired.vy_mm_s - state.vel_y_mm_s

        acc_x = pos_err_x * self.dyn.position_gain + vel_err_x * self.dyn.velocity_gain
        acc_y = pos_err_y * self.dyn.position_gain + vel_err_y * self.dyn.velocity_gain

        offset = math.hypot(pos_err_x, pos_err_y)
        overflow = max(0.0, offset - desired.corridor_half_width_mm)
        if overflow > 0.0:
            normal_x = pos_err_x / max(offset, 1e-9)
            normal_y = pos_err_y / max(offset, 1e-9)
            acc_x += normal_x * overflow * self.corridor_gain
            acc_y += normal_y * overflow * self.corridor_gain

        if desired.speed_mm_s <= 1.0:
            acc_x -= state.vel_x_mm_s * self.arrival_gain
            acc_y -= state.vel_y_mm_s * self.arrival_gain

        acc_mag = math.hypot(acc_x, acc_y)
        if acc_mag > self.dyn.max_acceleration:
            scale = self.dyn.max_acceleration / acc_mag
            acc_x *= scale
            acc_y *= scale
        return acc_x, acc_y

    def step(self, state: HandStateV2, desired: TrackPlanSample, *, dt: float) -> float:
        """Advance state one timestep and append a trajectory sample."""

        previous_position = state.pos_x_mm, state.pos_y_mm
        previous_contact = state.nib_contact
        previous_ink = state.ink_reservoir
        previous_time = state.time_s
        previous_velocity = state.vel_x_mm_s, state.vel_y_mm_s
        acc_x, acc_y = self.desired_acceleration(state, desired)
        state.acc_x_mm_s2 = acc_x
        state.acc_y_mm_s2 = acc_y
        state.vel_x_mm_s += acc_x * dt
        state.vel_y_mm_s += acc_y * dt

        speed = state.speed_mm_s
        if speed > self.dyn.max_speed:
            scale = self.dyn.max_speed / max(speed, 1e-9)
            state.vel_x_mm_s *= scale
            state.vel_y_mm_s *= scale

        state.pos_x_mm += state.vel_x_mm_s * dt
        state.pos_y_mm += state.vel_y_mm_s * dt
        state.time_s += dt

        corridor_error = math.dist((state.pos_x_mm, state.pos_y_mm), (desired.x_mm, desired.y_mm))
        if (self.execution_version == "legacy-v1" and desired.contact
                and corridor_error > desired.corridor_half_width_mm):
            nx = (state.pos_x_mm - desired.x_mm) / max(corridor_error, 1e-9)
            ny = (state.pos_y_mm - desired.y_mm) / max(corridor_error, 1e-9)
            state.pos_x_mm = desired.x_mm + nx * desired.corridor_half_width_mm
            state.pos_y_mm = desired.y_mm + ny * desired.corridor_half_width_mm
            state.vel_x_mm_s *= 0.82
            state.vel_y_mm_s *= 0.82
            corridor_error = desired.corridor_half_width_mm

        state.rhythm_phase += self.profile.folio.base_tempo * dt
        state.fatigue = min(1.0, state.fatigue + self.profile.fatigue_rate * dt)
        state.nib_contact = desired.contact
        state.nib_angle_deg = desired.nib_angle_deg
        if self.repertoire_controls is not None:
            state.nib_angle_deg += self.repertoire_controls.angle_deg * math.sin(state.time_s * .4 + state.habit_phase)
        direction_rad = math.atan2(state.vel_y_mm_s, state.vel_x_mm_s)
        local_nib = PhysicsNib(
            width_mm=self.nib.width_mm,
            angle_deg=state.nib_angle_deg,
            flexibility=self.nib.flexibility,
            cut_quality=self.nib.cut_quality,
            attack_pressure_multiplier=self.nib.attack_pressure_multiplier,
            release_taper_length=self.nib.release_taper_length,
        )
        broadness = abs(math.sin(direction_rad - local_nib.angle_rad))
        normalized_speed = min(1.0, desired.speed_mm_s / max(self.dyn.max_speed, 1e-9))
        slow_factor = 1.0 - normalized_speed
        pressure_scale = self.profile.folio.base_pressure / 0.72 if self.activate_base_pressure else 1.0
        pressure = desired.pressure * pressure_scale
        # Keep the path legible, but let broad-edge downstrokes carry visibly more ink.
        pressure += (broadness - 0.35) * 0.30
        pressure += slow_factor * 0.12
        pressure += math.sin(state.rhythm_phase * 2.0 * math.pi) * self.dyn.rhythm_strength * 0.06
        if desired.progress_ratio <= 0.10:
            pressure += (0.10 - desired.progress_ratio) / 0.10 * 0.04
        if desired.progress_ratio >= 0.82:
            pressure += (desired.progress_ratio - 0.82) / 0.18 * 0.08
        pressure *= 1.0 + self.profile.ink.fresh_dip_darkness_boost * max(0.0, state.ink_reservoir - 0.5)
        pressure *= 1.0 - 0.12 * state.fatigue
        state.nib_pressure = max(0.0, min(1.15, pressure))
        if self.repertoire_controls is not None:
            pressure = desired.pressure * (1 + self.repertoire_controls.pressure * math.sin(state.time_s * .5 + state.habit_phase))
            if self.repertoire_controls.ink:
                pressure *= min(1, max(0, state.ink_reservoir / self.profile.ink.reservoir_capacity))
            state.nib_pressure = max(0.0, min(1.15, pressure)) if state.nib_contact else 0.0

        width_mm = None
        consumed = 0.0
        contact_mm = math.dist(previous_position, (state.pos_x_mm, state.pos_y_mm)) if previous_contact and state.nib_contact else 0.0
        if self.repertoire_controls is not None:
            state.contact_length_mm += contact_mm
            if state.nib_contact and (state.ink_reservoir > 0 or not self.repertoire_controls.ink):
                width_mm = self.nib.width_mm * (1 + .35 * (state.nib_pressure - .5))
                if self.repertoire_controls.ink:
                    consumed = min(state.ink_reservoir, contact_mm * self.repertoire_controls.ink_per_mm * state.nib_pressure / .5)
                    state.ink_reservoir -= consumed
                    state.consumed_ink += consumed
            else:
                width_mm = 0.0
        elif state.nib_contact and state.ink_reservoir > 0.0:
            direction_deg = math.degrees(direction_rad)
            width_pressure = max(0.0, min(1.0, state.nib_pressure))
            width_mm = mark_width(
                local_nib,
                direction_deg=direction_deg,
                pressure=width_pressure,
                t=desired.progress_ratio,
            )
            state.ink_reservoir = max(
                0.0,
                state.ink_reservoir - self.profile.ink.depletion_rate * state.nib_pressure * dt,
            )

        state.trace.append(
            TrajectorySample(
                x_mm=state.pos_x_mm,
                y_mm=state.pos_y_mm,
                contact=state.nib_contact,
                width_mm=width_mm,
                pressure=state.nib_pressure if state.nib_contact else 0.0,
                nib_angle_deg=state.nib_angle_deg,
            )
        )
        if self.repertoire_controls is not None:
            state.execution_trace.append({"time_before": previous_time, "time_s": state.time_s,
                "from_mm": list(previous_position), "to_mm": [state.pos_x_mm, state.pos_y_mm],
                "desired_mm": [desired.x_mm, desired.y_mm], "corridor_mm": desired.corridor_half_width_mm,
                "previous_contact": previous_contact, "contact": state.nib_contact, "contact_mm": contact_mm,
                "consumed": consumed, "ink_before": previous_ink, "ink_after": state.ink_reservoir,
                "pressure": state.nib_pressure, "width_mm": width_mm, "angle_deg": state.nib_angle_deg,
                "nominal_angle_deg": desired.nib_angle_deg,
                "fatigue": state.fatigue, "rhythm_phase": state.rhythm_phase, "habit_phase": state.habit_phase})
            if self.execution_version == "event-time-v1":
                state.execution_trace[-1].update(velocity_before_mm_s=list(previous_velocity),
                    velocity_mm_s=[state.vel_x_mm_s, state.vel_y_mm_s],
                    execution_version=self.execution_version)
        return corridor_error

    def _follow_timed_plan(self, plan, *, state, dt, settle_time_s):
        for value in (dt, settle_time_s):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("Finite nonnegative execution times required")
        if dt <= 0 or not plan.samples or plan.samples[0].t_s != 0:
            raise ValueError("Positive dt and a nonempty zero-origin plan required")
        for sample in plan.samples:
            if any(not math.isfinite(getattr(sample, field.name)) for field in fields(sample)):
                raise ValueError("Nonfinite plan state")
        for previous, desired in zip(plan.samples, plan.samples[1:]):
            if desired.t_s < previous.t_s or (desired.t_s == previous.t_s and
                    (desired.x_mm, desired.y_mm) != (previous.x_mm, previous.y_mm)):
                raise ValueError("Reversed time or zero-time spatial teleport")
        state = state or self.initial_state(plan)
        start = len(state.trace)
        indices, observed_times = [], []
        errors, maximum = 0, 0.0

        def advance(desired, duration, index):
            nonlocal errors, maximum
            error = self.step(state, desired, dt=duration)
            indices.append(index)
            observed_times.append(state.time_s - origin)
            maximum = max(maximum, error)
            errors += int(desired.contact and error > desired.corridor_half_width_mm)

        origin = state.time_s
        times = [sample.t_s for sample in plan.samples]
        events = {}
        for index, (previous, desired) in enumerate(zip(plan.samples, plan.samples[1:]), start=1):
            if desired.t_s == previous.t_s or desired.contact != previous.contact:
                events.setdefault(desired.t_s, []).append(index)
        schedule = sorted(set([min(index * dt, plan.total_time_s)
                               for index in range(1, math.ceil(plan.total_time_s / dt) + 1)]
                              + list(events) + [plan.total_time_s]))
        advance(plan.samples[0], 0, 0)
        elapsed = 0.0
        for instant in schedule:
            if instant > elapsed:
                index = bisect_left(times, instant)
                previous, desired = plan.samples[index - 1], plan.samples[index]
                fraction = (instant - previous.t_s) / (desired.t_s - previous.t_s)
                values = {field.name: getattr(previous, field.name) * (1 - fraction)
                          + getattr(desired, field.name) * fraction
                          for field in fields(previous) if field.name != "contact"}
                target = replace(previous, **values, contact=previous.contact)
                owner = index if desired.contact == previous.contact else index - 1
                advance(target, instant - elapsed, owner)
            for index in events.get(instant, []):
                advance(plan.samples[index], 0, index)
            elapsed = instant
        if settle_time_s:
            steps = math.ceil(settle_time_s / dt)
            for _ in range(steps):
                advance(plan.samples[-1], settle_time_s / steps, len(plan.samples) - 1)
        trajectory = tuple(state.trace[start:])
        aligned = tuple(trajectory[max(0, bisect_right(observed_times, sample.t_s + 1e-12) - 1)]
                        for sample in plan.samples)
        return SimulationResult(plan, state, trajectory, aligned, errors, maximum,
                                tuple(indices))

    def follow_plan(
        self,
        plan: TrackPlan,
        *,
        state: HandStateV2 | None = None,
        dt: float = 0.002,
        settle_time_s: float = 0.05,
    ) -> SimulationResult:
        if self.execution_version == "event-time-v1":
            return self._follow_timed_plan(plan, state=state, dt=dt, settle_time_s=settle_time_s)
        if not plan.samples:
            raise ValueError("cannot follow an empty TrackPlan")

        state = state or self.initial_state(plan)
        trace_start = len(state.trace)
        final_sample = plan.samples[-1]
        out_of_corridor_steps = 0
        max_corridor_error = 0.0
        trajectory_plan_indices = []
        aligned_trace = [
            TrajectorySample(
                x_mm=state.pos_x_mm,
                y_mm=state.pos_y_mm,
                contact=state.nib_contact,
                width_mm=None,
                pressure=state.nib_pressure if state.nib_contact else 0.0,
                nib_angle_deg=state.nib_angle_deg,
            )
        ]

        for plan_index, (prev, desired) in enumerate(zip(plan.samples, plan.samples[1:], strict=False), start=1):
            segment_dt = max(dt, desired.t_s - prev.t_s)
            substeps = max(1, round(segment_dt / dt))
            actual_dt = segment_dt / substeps
            for _ in range(substeps):
                corridor_error = self.step(state, desired, dt=actual_dt)
                trajectory_plan_indices.append(plan_index)
                max_corridor_error = max(max_corridor_error, corridor_error)
                if corridor_error > desired.corridor_half_width_mm:
                    out_of_corridor_steps += 1
            aligned_trace.append(
                TrajectorySample(
                    x_mm=state.pos_x_mm,
                    y_mm=state.pos_y_mm,
                    contact=state.nib_contact,
                    width_mm=state.trace[-1].width_mm if state.trace else None,
                    pressure=state.nib_pressure if state.nib_contact else 0.0,
                    nib_angle_deg=state.nib_angle_deg,
                )
            )

        settle_steps = max(1, round(settle_time_s / dt))
        if self.repertoire_controls is not None and settle_time_s == 0:
            settle_steps = 0
        for _ in range(settle_steps):
            corridor_error = self.step(state, final_sample, dt=dt)
            trajectory_plan_indices.append(len(plan.samples) - 1)
            max_corridor_error = max(max_corridor_error, corridor_error)
            if corridor_error > final_sample.corridor_half_width_mm:
                out_of_corridor_steps += 1
            if (
                math.dist((state.pos_x_mm, state.pos_y_mm), (final_sample.x_mm, final_sample.y_mm))
                <= final_sample.corridor_half_width_mm * 0.25
                and state.speed_mm_s <= max(1.0, self.dyn.max_speed * 0.04)
            ):
                break

        return SimulationResult(
            plan=plan,
            final_state=state,
            trajectory=tuple(state.trace[trace_start:]),
            guide_aligned_trajectory=tuple(aligned_trace),
            out_of_corridor_steps=out_of_corridor_steps,
            max_corridor_error_mm=max_corridor_error,
            trajectory_plan_indices=tuple(trajectory_plan_indices),
        )

    def simulate_guide(
        self,
        guide: DensePathGuide,
        *,
        dt: float = 0.002,
        base_speed_mm_s: float | None = None,
        air_speed_multiplier: float = 1.35,
        settle_time_s: float = 0.05,
    ) -> SimulationResult:
        plan = build_track_plan(
            guide,
            base_speed_mm_s=base_speed_mm_s or self.dyn.max_speed * 0.65,
            air_speed_multiplier=air_speed_multiplier,
            stop_at_end=True,
        )
        return self.follow_plan(plan, dt=dt, settle_time_s=settle_time_s)

    def simulate_session(
        self,
        guides: tuple[SessionGuide, ...] | list[SessionGuide],
        *,
        dt: float = 0.002,
        base_speed_mm_s: float | None = None,
        air_speed_multiplier: float = 1.35,
    ) -> SessionResult:
        """Follow a persistent sequence of guides without resetting hand state."""

        if not guides:
            raise ValueError("guides must be non-empty")

        state: HandStateV2 | None = None
        segments: list[SimulationResult] = []
        state_trace: list[StateTraceEntry] = []
        aligned_trajectory: list[TrajectorySample] = []

        for idx, item in enumerate(guides):
            if state is not None and item.dip_before:
                state.ink_reservoir = self.profile.ink.reservoir_capacity
            plan = build_track_plan(
                item.guide,
                base_speed_mm_s=base_speed_mm_s or self.dyn.max_speed * 0.65,
                air_speed_multiplier=air_speed_multiplier,
                stop_at_end=idx == len(guides) - 1 or item.pause_after_s > 0.0,
            )
            start_state = copy.deepcopy(state) if state is not None else self.initial_state(plan)
            result = self.follow_plan(
                plan,
                state=state,
                dt=dt,
                settle_time_s=item.pause_after_s,
            )
            state = result.final_state
            segments.append(result)
            for sample in result.guide_aligned_trajectory:
                if aligned_trajectory:
                    prev = aligned_trajectory[-1]
                    if (
                        math.isclose(prev.x_mm, sample.x_mm, abs_tol=1e-9)
                        and math.isclose(prev.y_mm, sample.y_mm, abs_tol=1e-9)
                        and prev.contact == sample.contact
                    ):
                        continue
                aligned_trajectory.append(sample)
            state_trace.append(
                StateTraceEntry(
                    symbol=item.symbol,
                    kind=item.kind,
                    word=item.word,
                    word_index=item.word_index,
                    start_time_s=start_state.time_s,
                    end_time_s=state.time_s,
                    start_speed_mm_s=start_state.speed_mm_s,
                    end_speed_mm_s=state.speed_mm_s,
                    start_pressure=start_state.nib_pressure,
                    end_pressure=state.nib_pressure,
                    start_ink_reservoir=start_state.ink_reservoir,
                    end_ink_reservoir=state.ink_reservoir,
                    dip_before=item.dip_before,
                )
            )

        if state is None:
            raise ValueError("session produced no state")
        return SessionResult(
            final_state=state,
            trajectory=tuple(state.trace),
            guide_aligned_trajectory=tuple(aligned_trajectory),
            segments=tuple(segments),
            state_trace=tuple(state_trace),
        )
