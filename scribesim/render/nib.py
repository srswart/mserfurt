"""Virtual nib model — elliptical Bastarda nib stamp.

A Bastarda nib is a broad-edge pen held at a fixed angle (typically 40–45°
to the horizontal).  This produces thick downstrokes and thin crossstrokes
— the characteristic thick/thin contrast of Gothic Bastarda script.

The nib is modelled as an ellipse:
  - semi-major axis = nib_width / 2  (along the nib edge direction)
  - semi-minor axis = nib_width / 8  (perpendicular — the pen edge thickness)
  - rotated by nib_angle_deg from the horizontal

At each sample point along a Bezier stroke the nib is "stamped": a small
filled ellipse drawn at (x, y) with opacity modulated by pressure(t) and
ink_density.
"""

from __future__ import annotations

import math


def nib_ellipse_axes(nib_width_mm: float, nib_angle_deg: float, px_per_mm: float
                     ) -> tuple[int, int, float]:
    """Compute the nib stamp ellipse semi-axes in pixels and rotation angle.

    Returns (semi_major_px, semi_minor_px, angle_rad).
    """
    semi_major = max(1, round(nib_width_mm * 0.5 * px_per_mm))
    semi_minor = max(1, round(nib_width_mm * 0.125 * px_per_mm))
    angle_rad = math.radians(nib_angle_deg)
    return semi_major, semi_minor, angle_rad


# ---------------------------------------------------------------------------
# Physics-based nib model (TD-002 Part 2)
# ---------------------------------------------------------------------------

class PhysicsNib:
    """Direction-dependent nib model.

    Mark width emerges from the interaction of nib angle and stroke direction,
    not from a fixed ellipse size.
    """

    __slots__ = ("width_mm", "angle_deg", "angle_rad", "flexibility",
                 "cut_quality", "attack_pressure_multiplier", "release_taper_length")

    def __init__(self, width_mm: float = 1.8, angle_deg: float = 40.0,
                 flexibility: float = 0.15, cut_quality: float = 0.9,
                 attack_pressure_multiplier: float = 1.15,
                 release_taper_length: float = 0.3):
        self.width_mm = width_mm
        self.angle_deg = angle_deg
        self.angle_rad = math.radians(angle_deg)
        self.flexibility = flexibility
        self.cut_quality = cut_quality
        self.attack_pressure_multiplier = attack_pressure_multiplier
        self.release_taper_length = release_taper_length


def stroke_foot_effect(t: float, foot_zone_start: float = 0.85,
                       width_boost: float = 0.20,
                       ink_boost: float = 0.25) -> tuple[float, float]:
    """Compute stroke-foot thickening at end of downstrokes (TD-004 Fix C).

    Returns (width_multiplier, ink_multiplier).
    The diamond-shaped foot is caused by deceleration + nib rotation at direction change.
    """
    if t > foot_zone_start:
        foot_t = (t - foot_zone_start) / (1.0 - foot_zone_start)
        w_mult = 1.0 + width_boost * math.sin(foot_t * math.pi)
        i_mult = 1.0 + ink_boost * math.sin(foot_t * math.pi)
        return w_mult, i_mult
    return 1.0, 1.0


def stroke_attack_effect(t: float, attack_zone_end: float = 0.10,
                         width_boost: float = 0.10) -> tuple[float, float]:
    """Compute stroke-start attack thickening (TD-004 Fix D).

    Returns (width_multiplier, ink_multiplier).
    The nib presses down at stroke onset producing a slight thickening.
    """
    if t < attack_zone_end:
        attack_t = t / attack_zone_end
        w_mult = 1.0 + width_boost * (1.0 - attack_t)
        i_mult = 1.0 + 0.15 * (1.0 - attack_t)
        return w_mult, i_mult
    return 1.0, 1.0


def mark_width(nib: PhysicsNib, direction_deg: float, pressure: float,
               t: float = 0.5) -> float:
    """Compute mark width in mm from nib angle × stroke direction (TD-004 revised).

    Formula:
        direction_width = nib.width × |sin(direction - nib.angle)|
        pressure_mod = 0.8 + 0.4 × pressure  (±20% modulation)
        width = max(direction_width × pressure_mod, min_hairline)
        width × stroke_foot × stroke_attack

    Direction is the PRIMARY driver of thick/thin. Pressure modulates ±20%.
    """
    direction_rad = math.radians(direction_deg)

    # Primary: direction-dependent width
    sin_component = abs(math.sin(direction_rad - nib.angle_rad))
    direction_width = nib.width_mm * sin_component

    # Secondary: pressure modulation ±20% (TD-004 Fix B)
    pressure_mod = 0.8 + 0.4 * pressure  # range: 0.8 to 1.2
    raw_width = direction_width * pressure_mod

    # Hairline floor (TD-004 Fix A): ~8% of nib width
    min_hairline = nib.width_mm * 0.08
    width = max(raw_width, min_hairline)

    # Stroke foot effect (TD-004 Fix C): thickening at stroke end
    foot_w, _ = stroke_foot_effect(t)
    width *= foot_w

    # Stroke attack effect (TD-004 Fix D): thickening at stroke start
    attack_w, _ = stroke_attack_effect(t)
    width *= attack_w

    return width


def stroke_direction(pts: list, i: int) -> float:
    """Compute stroke direction in degrees at sample point i.

    Uses central difference where possible, forward/backward at endpoints.
    """
    if len(pts) < 2:
        return 0.0

    if i == 0:
        x0, y0 = pts[0][0], pts[0][1]
        x1, y1 = pts[1][0], pts[1][1]
    elif i >= len(pts) - 1:
        x0, y0 = pts[-2][0], pts[-2][1]
        x1, y1 = pts[-1][0], pts[-1][1]
    else:
        x0, y0 = pts[i - 1][0], pts[i - 1][1]
        x1, y1 = pts[i + 1][0], pts[i + 1][1]

    return math.degrees(math.atan2(y1 - y0, x1 - x0))


def stroke_opacity(pressure: float, base_opacity: float,
                   ink_density: float, glyph_opacity: float) -> int:
    """Compute the final 0–255 ink value for a nib stamp.

    Args:
        pressure:      Normalised pressure at this sample point [0.0–1.0].
        base_opacity:  Base ink opacity from hand params [0.0–1.0].
        ink_density:   Ink density modifier [0.0–2.0].
        glyph_opacity: Per-glyph lacuna opacity [0.0–1.0].

    Returns:
        Ink darkness as 0–255 integer (255 = maximum ink, 0 = no ink).
    """
    # Combined opacity: pressure × base × density × lacuna
    combined = pressure * base_opacity * min(1.0, ink_density) * glyph_opacity
    # Map to darkness: 0 = white (255 in L image), 255 = black (0 in L image)
    return max(0, min(255, round(combined * 255)))
