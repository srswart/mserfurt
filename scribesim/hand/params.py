"""HandParams — typed dataclass for TD-001-D hand parameter contract."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict


# Fields that are normalised ratios and must stay in [0.0, 2.0]
_CLAMPED = frozenset({
    "pressure_base", "pressure_upstroke", "pressure_variance",
    "ink_density", "stroke_weight", "writing_speed",
    "letter_spacing_norm", "tremor_amplitude", "fatigue_rate",
})


@dataclass
class HandParams:
    """Fully resolved hand configuration for one folio.

    All fields map 1-to-1 to keys in the TD-001-D TOML [hand] section.
    Normalised fields (0.0–2.0) are clamped on construction.
    """
    # Nib geometry
    nib_angle_deg: float = 45.0
    nib_width_mm: float = 1.8
    stroke_weight: float = 1.0

    # Pressure dynamics
    pressure_base: float = 0.72
    pressure_upstroke: float = 0.28
    pressure_variance: float = 0.08

    # Ink
    ink_density: float = 0.85
    ink_bleed_radius_px: float = 1.2

    # Spacing and rhythm
    letter_spacing_norm: float = 1.0
    word_spacing_norm: float = 2.4
    line_height_norm: float = 4.2
    x_height_px: int = 38

    # Speed and fatigue
    writing_speed: float = 1.0
    fatigue_rate: float = 0.0
    tremor_amplitude: float = 0.0

    # Lateral tilt
    slant_deg: float = 3.5

    # Script metadata
    script: str = "bastarda"
    dialect_region: str = "thuringian"
    date_approx: int = 1457

    def __post_init__(self) -> None:
        """Clamp normalised float fields to [0.0, 2.0]."""
        for f in _CLAMPED:
            val = getattr(self, f, None)
            if isinstance(val, float):
                setattr(self, f, max(0.0, min(2.0, val)))

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> HandParams:
        """Construct from a flat dict, ignoring unknown keys."""
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)

    # ------------------------------------------------------------------
    # Merging
    # ------------------------------------------------------------------

    def apply_delta(self, delta: dict) -> HandParams:
        """Return a new HandParams with delta values overlaid.

        Only keys that exist on HandParams are applied; unknown keys are
        ignored so that TOML comments and future fields don't break old code.
        """
        current = self.to_dict()
        current.update({k: v for k, v in delta.items() if k in current})
        return HandParams.from_dict(current)
