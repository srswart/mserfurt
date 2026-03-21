"""Sliding window motor planning (TD-006 Phase 2).

The hand holds a window of upcoming keypoints and computes a smooth
planned path (Hermite spline) through them. The PD controller follows
this planned path instead of aiming at individual keypoints.

This models anticipatory motor planning: the hand shapes the current
stroke based on what's coming next.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from scribesim.handsim.targets import TargetPoint


# ---------------------------------------------------------------------------
# Planned path point
# ---------------------------------------------------------------------------

@dataclass
class PathNode:
    """A point on the planned path with position and velocity."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    contact: bool = True
    arc_length: float = 0.0  # cumulative distance from path start


# ---------------------------------------------------------------------------
# Hermite spline interpolation
# ---------------------------------------------------------------------------

def _hermite_interp(p0: float, v0: float, p1: float, v1: float, t: float) -> float:
    """Cubic Hermite interpolation between two points."""
    t2 = t * t
    t3 = t2 * t
    h00 = 2 * t3 - 3 * t2 + 1
    h10 = t3 - 2 * t2 + t
    h01 = -2 * t3 + 3 * t2
    h11 = t3 - t2
    return h00 * p0 + h10 * v0 + h01 * p1 + h11 * v1


def _hermite_velocity(p0: float, v0: float, p1: float, v1: float, t: float) -> float:
    """Derivative of Hermite interpolation (velocity along spline)."""
    t2 = t * t
    dh00 = 6 * t2 - 6 * t
    dh10 = 3 * t2 - 4 * t + 1
    dh01 = -6 * t2 + 6 * t
    dh11 = 3 * t2 - 2 * t
    return dh00 * p0 + dh10 * v0 + dh01 * p1 + dh11 * v1


# ---------------------------------------------------------------------------
# Planned path
# ---------------------------------------------------------------------------

@dataclass
class PlannedPath:
    """A smooth path through a sequence of keypoints."""
    nodes: list[PathNode]
    total_length: float = 0.0

    def __post_init__(self):
        if len(self.nodes) >= 2:
            self.total_length = self.nodes[-1].arc_length

    def position_at(self, cursor: float) -> tuple[float, float]:
        """Get interpolated position at cursor [0, 1] along path."""
        if not self.nodes or self.total_length < 1e-6:
            return (0.0, 0.0) if not self.nodes else (self.nodes[0].x, self.nodes[0].y)

        target_dist = cursor * self.total_length

        # Find the segment containing this distance
        for i in range(len(self.nodes) - 1):
            n0 = self.nodes[i]
            n1 = self.nodes[i + 1]
            seg_len = n1.arc_length - n0.arc_length
            if seg_len < 1e-6:
                continue
            if target_dist <= n1.arc_length:
                t = (target_dist - n0.arc_length) / seg_len
                t = max(0.0, min(1.0, t))
                x = _hermite_interp(n0.x, n0.vx * seg_len, n1.x, n1.vx * seg_len, t)
                y = _hermite_interp(n0.y, n0.vy * seg_len, n1.y, n1.vy * seg_len, t)
                return (x, y)

        # Past the end — return last node
        return (self.nodes[-1].x, self.nodes[-1].y)

    def velocity_at(self, cursor: float) -> tuple[float, float]:
        """Get interpolated velocity direction at cursor."""
        if len(self.nodes) < 2 or self.total_length < 1e-6:
            return (0.0, 0.0)

        target_dist = cursor * self.total_length

        for i in range(len(self.nodes) - 1):
            n0 = self.nodes[i]
            n1 = self.nodes[i + 1]
            seg_len = n1.arc_length - n0.arc_length
            if seg_len < 1e-6:
                continue
            if target_dist <= n1.arc_length:
                t = (target_dist - n0.arc_length) / seg_len
                t = max(0.0, min(1.0, t))
                vx = _hermite_velocity(n0.x, n0.vx * seg_len, n1.x, n1.vx * seg_len, t)
                vy = _hermite_velocity(n0.y, n0.vy * seg_len, n1.y, n1.vy * seg_len, t)
                return (vx, vy)

        return (0.0, 0.0)

    def contact_at(self, cursor: float) -> bool:
        """Whether nib should be in contact at this cursor position."""
        if not self.nodes:
            return True
        idx = int(cursor * max(1, len(self.nodes) - 1))
        idx = max(0, min(idx, len(self.nodes) - 1))
        return self.nodes[idx].contact


# ---------------------------------------------------------------------------
# Sliding window
# ---------------------------------------------------------------------------

@dataclass
class SlidingWindow:
    """Holds upcoming keypoints and the planned path through them."""
    keypoints: list[TargetPoint] = field(default_factory=list)
    window_size: int = 6
    plan: PlannedPath | None = None
    plan_cursor: float = 0.0
    steps_since_replan: int = 0
    replan_interval: int = 8


def build_plan(
    keypoints: list[TargetPoint],
    current_pos: tuple[float, float],
    current_vel: tuple[float, float],
    base_speed: float = 30.0,
    speed_reduction_at_turns: float = 0.6,
    air_speed_multiplier: float = 1.5,
) -> PlannedPath:
    """Build a smooth planned path through the window's keypoints.

    Uses Hermite interpolation with velocity estimates at each keypoint.
    """
    if not keypoints:
        return PlannedPath(nodes=[])

    # Build nodes: start from current position
    nodes = [PathNode(x=current_pos[0], y=current_pos[1],
                      vx=current_vel[0], vy=current_vel[1],
                      contact=True, arc_length=0.0)]

    cumulative_dist = 0.0

    for i, kp in enumerate(keypoints):
        # Distance from previous node
        prev = nodes[-1]
        dx = kp.x_mm - prev.x
        dy = kp.y_mm - prev.y
        seg_dist = math.sqrt(dx * dx + dy * dy)
        cumulative_dist += seg_dist

        # Estimate velocity at this keypoint
        if i + 1 < len(keypoints):
            # Look at incoming and outgoing directions
            next_kp = keypoints[i + 1]
            out_dx = next_kp.x_mm - kp.x_mm
            out_dy = next_kp.y_mm - kp.y_mm
            out_dist = math.sqrt(out_dx * out_dx + out_dy * out_dy) + 1e-6

            in_dx = kp.x_mm - prev.x
            in_dy = kp.y_mm - prev.y
            in_dist = math.sqrt(in_dx * in_dx + in_dy * in_dy) + 1e-6

            # Average direction (smooths the path)
            avg_dx = (in_dx / in_dist + out_dx / out_dist) * 0.5
            avg_dy = (in_dy / in_dist + out_dy / out_dist) * 0.5
            avg_len = math.sqrt(avg_dx * avg_dx + avg_dy * avg_dy) + 1e-6

            # Speed: slow at sharp turns
            turn_angle = math.acos(max(-1.0, min(1.0,
                (in_dx * out_dx + in_dy * out_dy) / (in_dist * out_dist))))
            speed = base_speed * (1.0 - speed_reduction_at_turns * (turn_angle / math.pi))

            # Faster through air
            if not kp.contact:
                speed *= air_speed_multiplier

            vx = (avg_dx / avg_len) * speed
            vy = (avg_dy / avg_len) * speed
        else:
            # Last keypoint — decelerate
            if seg_dist > 0.01:
                vx = (dx / seg_dist) * base_speed * 0.3
                vy = (dy / seg_dist) * base_speed * 0.3
            else:
                vx, vy = 0.0, 0.0

        nodes.append(PathNode(
            x=kp.x_mm, y=kp.y_mm,
            vx=vx, vy=vy,
            contact=kp.contact,
            arc_length=cumulative_dist,
        ))

    return PlannedPath(nodes=nodes)


def advance_window(
    window: SlidingWindow,
    hand_pos: tuple[float, float],
    hand_vel: tuple[float, float],
    all_targets: list[TargetPoint],
    current_target_index: int,
    base_speed: float = 30.0,
) -> None:
    """Advance the window: pop passed keypoints, push upcoming ones, replan."""
    # Remove keypoints the hand has passed
    while window.keypoints:
        kp = window.keypoints[0]
        dx = kp.x_mm - hand_pos[0]
        dy = kp.y_mm - hand_pos[1]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.3:  # passed this keypoint
            window.keypoints.pop(0)
        else:
            break

    # Fill window to capacity from upcoming targets
    next_idx = current_target_index
    while len(window.keypoints) < window.window_size and next_idx < len(all_targets):
        kp = all_targets[next_idx]
        if kp not in window.keypoints:
            window.keypoints.append(kp)
        next_idx += 1

    # Replan
    window.plan = build_plan(
        window.keypoints, hand_pos, hand_vel, base_speed)
    window.plan_cursor = 0.0
    window.steps_since_replan = 0
