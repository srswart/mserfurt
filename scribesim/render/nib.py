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
