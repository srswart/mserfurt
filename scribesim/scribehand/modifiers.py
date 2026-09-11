"""Map CLIO-7 hand-profile modifiers to generation-time controls (TD-018 §2.4).

The narrative arc (pressure shifts, fatigue, smaller hand on later folios)
lives in the per-folio HandProfile modifier stack. Instead of driving physics
parameters, those values now modulate the generative sampler and the page
compositor:

- ``style_noise``       — style-embedding noise magnitude (variation/fatigue)
- ``guidance_scale``    — sampler guidance (careful vs. hasty writing)
- ``x_height_scale``    — physical scale multiplier at composition
- ``ink_darkness``      — ink tone multiplier at composition (pressure/ink)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GenControls:
    style_noise: float = 0.1
    guidance_scale: float = 2.0
    x_height_scale: float = 1.0
    ink_darkness: float = 1.0

    def to_dict(self) -> dict:
        return {
            "style_noise": round(self.style_noise, 4),
            "guidance_scale": round(self.guidance_scale, 4),
            "x_height_scale": round(self.x_height_scale, 4),
            "ink_darkness": round(self.ink_darkness, 4),
        }


# Baseline profile values the mapping is calibrated around (konrad base hand).
_BASE_PRESSURE = 0.72
_BASE_INK_DENSITY = 0.85


def controls_from_profile(profile) -> GenControls:
    """Derive generation controls from a resolved per-folio HandProfile."""
    folio = profile.folio

    # Pressure and ink density brighten/darken the composited ink.
    pressure_delta = folio.base_pressure - _BASE_PRESSURE
    ink_delta = profile.ink_density - _BASE_INK_DENSITY
    ink_darkness = 1.0 + 0.8 * pressure_delta + 0.6 * ink_delta

    # Variation sources feed style noise: tremor, glyph size variance,
    # writing speed above nominal (hastier hand → looser style).
    style_noise = 0.08
    style_noise += min(0.25, folio.tremor_amplitude * 8.0)
    style_noise += min(0.20, profile.glyph.size_variance * 4.0)
    style_noise += max(0.0, (profile.writing_speed - 1.0) * 0.3)

    # Careful writing (slow speed) → higher guidance; hasty → lower.
    guidance_scale = 2.0 + max(-0.8, min(0.8, (1.0 - profile.writing_speed) * 1.5))

    # Smaller-hand folios scale the x-height at composition.
    x_height_scale = max(0.7, min(1.3, getattr(folio, "size_scale", 1.0)))

    return GenControls(
        style_noise=max(0.0, min(1.0, style_noise)),
        guidance_scale=guidance_scale,
        x_height_scale=x_height_scale,
        ink_darkness=max(0.5, min(1.2, ink_darkness)),
    )
