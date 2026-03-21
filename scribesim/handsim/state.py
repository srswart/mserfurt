"""Hand state machine — continuous dynamics simulation (TD-005 Part 1).

The hand is a state machine that evolves at every timestep. It produces
marks whenever the nib is in contact with the surface. Letterforms emerge
from the hand steering through target keypoints, shaped by attraction,
damping, lookahead, rhythm, and tremor forces.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from scribesim.hand.profile import HandProfile
from scribesim.handsim.targets import TargetPoint
from scribesim.render.nib import PhysicsNib, mark_width, stroke_foot_effect, stroke_attack_effect


# ---------------------------------------------------------------------------
# Mark — a single point of ink deposit
# ---------------------------------------------------------------------------

@dataclass
class Mark:
    """A point where the nib deposited ink."""
    x_mm: float
    y_mm: float
    width_mm: float     # mark width from nib physics
    pressure: float     # nib pressure at this point
    ink_amount: float   # ink deposited
    direction_deg: float  # stroke direction


# ---------------------------------------------------------------------------
# Hand state
# ---------------------------------------------------------------------------

@dataclass
class HandState:
    """Continuous state of the writing hand."""
    # Physical position and dynamics (mm, mm/s, mm/s²)
    pos_x: float = 0.0
    pos_y: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0

    # Nib state
    nib_contact: bool = False
    nib_pressure: float = 0.7
    nib_angle_deg: float = 40.0

    # Ink state
    ink_reservoir: float = 1.0

    # Motor program
    target_index: int = 0
    targets: list = field(default_factory=list)  # list[TargetPoint]
    stroke_t: float = 0.0  # progress within current stroke segment [0, 1]

    # Rhythm
    phase: float = 0.0
    tempo: float = 3.0  # strokes per second

    # Accumulated marks
    marks: list = field(default_factory=list)  # list[Mark]

    @property
    def current_target(self) -> TargetPoint | None:
        if self.target_index < len(self.targets):
            return self.targets[self.target_index]
        return None

    @property
    def speed(self) -> float:
        return math.sqrt(self.vel_x ** 2 + self.vel_y ** 2)

    @property
    def direction_deg(self) -> float:
        return math.degrees(math.atan2(self.vel_y, self.vel_x))

    def has_targets(self) -> bool:
        return self.target_index < len(self.targets)


# ---------------------------------------------------------------------------
# Hand simulator
# ---------------------------------------------------------------------------

class HandSimulator:
    """Simulates a hand writing through a sequence of targets.

    The hand is attracted toward targets, damped by friction, and
    influenced by lookahead (planning ahead). When the nib is in
    contact, it emits marks.
    """

    def __init__(self, profile: HandProfile):
        self.profile = profile
        self.dyn = profile.dynamics
        self.nib = PhysicsNib(
            width_mm=profile.nib.width_mm,
            angle_deg=profile.nib.angle_deg,
        )

    def simulate(
        self,
        targets: list[TargetPoint],
        dt: float = 0.0005,
        max_steps: int = 500000,
    ) -> list[Mark]:
        """Run the hand simulation through a target sequence.

        Args:
            targets: Sequence of TargetPoints to steer through.
            dt: Timestep in seconds (~0.5ms for smooth curves).
            max_steps: Safety limit.

        Returns:
            List of Mark objects (ink deposits).
        """
        if not targets:
            return []

        state = HandState(
            pos_x=targets[0].x_mm,
            pos_y=targets[0].y_mm,
            targets=targets,
            target_index=0,
            nib_angle_deg=self.profile.nib.angle_deg,
            tempo=3.0,  # base writing tempo (strokes/sec)
        )

        # Use sliding window planner if available
        from scribesim.handsim.planner import SlidingWindow, build_plan, advance_window

        window = SlidingWindow(window_size=6, replan_interval=8)
        # Fill initial window
        for i, t in enumerate(targets[:window.window_size]):
            window.keypoints.append(t)
        window.plan = build_plan(
            window.keypoints,
            (state.pos_x, state.pos_y),
            (state.vel_x, state.vel_y),
            base_speed=self.dyn.max_speed * 0.7,
        )

        for step in range(max_steps):
            if not state.has_targets() and not window.keypoints:
                break

            # Follow the planned path via PD controller
            if window.plan and window.plan.total_length > 0:
                plan_pos = window.plan.position_at(window.plan_cursor)
                plan_vel = window.plan.velocity_at(window.plan_cursor)
                plan_contact = window.plan.contact_at(window.plan_cursor)

                # Override target with plan position for PD controller
                state.nib_contact = plan_contact

                # Advance cursor based on speed
                if window.plan.total_length > 0:
                    cursor_advance = (state.speed * dt) / window.plan.total_length
                    window.plan_cursor = min(1.0, window.plan_cursor + cursor_advance)

            self._step(state, dt)

            # Replan periodically
            window.steps_since_replan += 1
            if window.steps_since_replan >= window.replan_interval:
                advance_window(
                    window,
                    (state.pos_x, state.pos_y),
                    (state.vel_x, state.vel_y),
                    targets,
                    state.target_index,
                    base_speed=self.dyn.max_speed * 0.7,
                )

        return state.marks

    def _step(self, state: HandState, dt: float) -> None:
        """Advance the hand state by one timestep."""
        target = state.current_target
        if target is None:
            return

        # --- Compute target position and desired velocity ---

        dx = target.x_mm - state.pos_x
        dy = target.y_mm - state.pos_y
        dist = math.sqrt(dx * dx + dy * dy) + 1e-6

        if self.dyn.use_pd_controller:
            # --- PD Controller (TD-006 Phase 2) ---
            # Position error: where should I be vs where I am
            pos_err_x = dx
            pos_err_y = dy

            # Desired velocity: aim toward target, decelerate near it
            # Speed tapers as we approach (smooth arrival)
            desired_speed = min(self.dyn.max_speed, dist * 8.0)
            if dist > 0.01:
                desired_vx = (dx / dist) * desired_speed
                desired_vy = (dy / dist) * desired_speed
            else:
                desired_vx, desired_vy = 0.0, 0.0

            # Lookahead: blend desired velocity toward next target
            if state.target_index + 1 < len(state.targets):
                next_t = state.targets[state.target_index + 1]
                nx = next_t.x_mm - state.pos_x
                ny = next_t.y_mm - state.pos_y
                ndist = math.sqrt(nx * nx + ny * ny) + 1e-6
                la_weight = self.dyn.lookahead_strength * 0.2
                if ndist > 0.01:
                    desired_vx += (nx / ndist) * desired_speed * la_weight
                    desired_vy += (ny / ndist) * desired_speed * la_weight

            # Velocity error: how I'm moving vs how I should be moving
            vel_err_x = desired_vx - state.vel_x
            vel_err_y = desired_vy - state.vel_y

            # PD correction: proportional (position) + derivative (velocity)
            fx = pos_err_x * self.dyn.position_gain + vel_err_x * self.dyn.velocity_gain
            fy = pos_err_y * self.dyn.position_gain + vel_err_y * self.dyn.velocity_gain

            # Clamp acceleration (biomechanical limit)
            acc_mag = math.sqrt(fx * fx + fy * fy)
            if acc_mag > self.dyn.max_acceleration:
                scale = self.dyn.max_acceleration / acc_mag
                fx *= scale
                fy *= scale
        else:
            # --- Legacy attractor mode (fallback) ---
            attraction_scale = self.dyn.attraction_strength / max(dist, 0.1)
            fx = dx * attraction_scale
            fy = dy * attraction_scale

            if state.target_index + 1 < len(state.targets):
                next_t = state.targets[state.target_index + 1]
                nx = next_t.x_mm - state.pos_x
                ny = next_t.y_mm - state.pos_y
                ndist = math.sqrt(nx * nx + ny * ny) + 1e-6
                la_scale = self.dyn.lookahead_strength / max(ndist, 0.5)
                fx += nx * la_scale
                fy += ny * la_scale

            fx -= state.vel_x * self.dyn.damping_coefficient
            fy -= state.vel_y * self.dyn.damping_coefficient

        # Rhythm (subtle, applies to both modes)
        rhythm_mod = math.sin(state.phase * 2 * math.pi) * self.dyn.rhythm_strength
        if state.speed > 0.1:
            vn_x = state.vel_x / state.speed
            vn_y = state.vel_y / state.speed
            fx += vn_x * rhythm_mod * 2.0
            fy += vn_y * rhythm_mod * 2.0

        # --- Integrate ---
        state.vel_x += fx * dt
        state.vel_y += fy * dt

        # Speed limit
        speed = state.speed
        if speed > self.dyn.max_speed:
            scale = self.dyn.max_speed / speed
            state.vel_x *= scale
            state.vel_y *= scale

        state.pos_x += state.vel_x * dt
        state.pos_y += state.vel_y * dt

        # Update rhythm phase
        state.phase += state.tempo * dt

        # Update stroke progress
        state.stroke_t = min(1.0, state.stroke_t + dt * 2.0)

        # --- Nib contact model ---
        # Contact is driven by keypoint flags, not by distance/height.
        # If current target AND next target are both contact:true, the nib
        # stays on the surface for the entire path between them.
        # Contact lifts only during explicit lift segments (contact:false).
        next_target = (state.targets[state.target_index + 1]
                        if state.target_index + 1 < len(state.targets) else None)

        if target.contact and (next_target is None or next_target.contact):
            # Both endpoints are on-surface → nib stays down
            state.nib_contact = True
        elif target.contact and next_target is not None and not next_target.contact:
            # Current is on-surface, next is a lift → nib stays down until
            # we advance past this target (the lift happens at transition)
            state.nib_contact = True
        else:
            # Current target is a lift point → nib is up
            state.nib_contact = False

        if state.nib_contact and state.ink_reservoir > 0:
            # Compute mark width from nib physics
            direction = state.direction_deg
            pressure = state.nib_pressure

            # Foot/attack effects based on stroke progress
            foot_w, foot_i = stroke_foot_effect(state.stroke_t)
            attack_w, attack_i = stroke_attack_effect(state.stroke_t)

            width = mark_width(self.nib, direction, pressure, state.stroke_t)
            width *= foot_w * attack_w

            ink = 0.01 * pressure * foot_i * attack_i

            state.marks.append(Mark(
                x_mm=state.pos_x,
                y_mm=state.pos_y,
                width_mm=width,
                pressure=pressure,
                ink_amount=ink,
                direction_deg=direction,
            ))

            state.ink_reservoir -= ink * 0.001

        # --- Advance target if close enough AND slow enough (TD-006 velocity gate) ---
        speed = state.speed
        slow_enough = speed < self.dyn.max_speed * 0.3  # must decelerate to 30%
        close_enough = dist < self.dyn.target_radius_mm

        if close_enough and slow_enough:
            state.target_index += 1
            state.stroke_t = 0.0  # reset stroke progress for new segment

            # Update contact state for new target
            new_target = state.current_target
            if new_target and not new_target.contact:
                state.nib_contact = False
