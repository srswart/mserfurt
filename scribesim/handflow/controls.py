"""Explicit, bounded opt-in repertoire execution controls with physical units."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RepertoireControls:
    ink: bool = False
    ink_per_mm: float = .004
    pressure: float = 0.0
    angle_deg: float = 0.0
    rhythm: float = 0.0

    def __post_init__(self):
        if not isinstance(self.ink, bool):
            raise ValueError("Ink activation must be boolean")
        for name, upper in (("ink_per_mm", .05), ("pressure", .2), ("angle_deg", 5), ("rhythm", .2)):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= upper:
                raise ValueError(f"Unsafe repertoire control: {name}")
