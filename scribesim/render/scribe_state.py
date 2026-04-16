"""ScribeState machine — temporally coherent scribal variation (TD-017).

Tracks five slowly-evolving state dimensions across lines and words:

  fatigue       — monotonic accumulation across the session
  ink_level     — reservoir level driven by InkState dip cycle
  intensity     — passage intensity (static for now, extensible)
  nib_drift_deg — slow nib angle oscillation growing with fatigue
  motor_memory  — per-glyph control point drift via correlated random walk

All variation is deterministic: seed is derived from folio_id so the same
folio always produces the same state trajectory.

Legibility constraints (hard limits):
  control point offset:  ±0.06 x-height units
  nib angle drift:       ±4°
  baseline drift:        ±0.4 mm
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from scribesim.ink.cycle import InkState, ink_darkness


# ---------------------------------------------------------------------------
# ScribeState
# ---------------------------------------------------------------------------

@dataclass
class ScribeState:
    """Snapshot of the scribe's physical state at a point in the folio."""

    fatigue: float = 0.0
    intensity: float = 0.5
    ink_state: InkState = field(default_factory=InkState)

    # Per-glyph form drift: glyph_id → (dx, dy) in x-height units
    motor_memory: dict = field(default_factory=dict)

    # Internal RNG — seeded deterministically from folio_id
    _rng: random.Random = field(default_factory=random.Random, repr=False)

    @property
    def ink_level(self) -> float:
        return self.ink_state.reservoir

    def darkness_scale(self) -> float:
        """Combined darkness multiplier from ink level and passage intensity.

        ink_darkness() maps reservoir → [0.58, 0.98] (from ink/cycle.py).
        intensity shifts that range by ±15%.
        Overall range: ~0.49 (depleted, low intensity) – 1.13 (fresh, high).
        Caller must still clamp the final darkness to [0, 1].
        """
        ink_scale = ink_darkness(self.ink_level)
        intensity_scale = 0.85 + 0.30 * self.intensity
        return ink_scale * intensity_scale

    def nib_angle_drift_deg(self, line_index: int) -> float:
        """Slow nib angle oscillation whose amplitude grows with fatigue.

        Amplitude: 0° at fatigue=0, ±3° at fatigue=1.
        Period: ~9 lines (sin(line * 0.7)).
        """
        amplitude = self.fatigue * 3.0
        return max(-4.0, min(4.0, amplitude * math.sin(line_index * 0.70 + 1.2)))

    def baseline_drift_mm(self, line_index: int) -> float:
        """Baseline sag driven by fatigue. Slow wave, amplitude ≤ 0.4mm."""
        amplitude = self.fatigue * 0.35
        return max(-0.4, min(0.4, amplitude * math.sin(line_index * 0.40)))

    def motor_offset(self, glyph_id: str) -> tuple[float, float]:
        """Current form drift for a glyph in x-height units."""
        return self.motor_memory.get(glyph_id, (0.0, 0.0))


# ---------------------------------------------------------------------------
# ScribeStateUpdater
# ---------------------------------------------------------------------------

_MOTOR_SIGMA_PER_LINE = 0.008   # control point drift per line
_MOTOR_LIMIT = 0.06             # hard ±limit in x-height units
_MOTOR_INIT_SIGMA = 0.025       # initial per-glyph offset at line 0


class ScribeStateUpdater:
    """Advances ScribeState across lines, deterministically from folio_id."""

    def __init__(
        self,
        folio_id: str,
        fatigue_rate: float = 0.025,
        ink_capacity: float = 1.0,
        ink_depletion_rate: float = 0.002,
        ink_dip_threshold: float = 0.22,
    ) -> None:
        self._folio_id = folio_id
        seed = hash(folio_id) & 0xFFFFFFFF
        rng = random.Random(seed)

        ink = InkState(
            capacity=ink_capacity,
            base_depletion=ink_depletion_rate,
            dip_threshold=ink_dip_threshold,
        )

        self._state = ScribeState(ink_state=ink, _rng=rng)
        self._fatigue_rate = fatigue_rate

    @property
    def state(self) -> ScribeState:
        return self._state

    def ensure_glyph(self, glyph_id: str) -> None:
        """Lazily initialise motor memory for a glyph with a seeded offset."""
        if glyph_id in self._state.motor_memory:
            return
        # Each glyph starts at a small non-zero position so that variation
        # is present from line 1 rather than starting at a common zero point.
        glyph_seed = hash((self._folio_id, glyph_id)) & 0xFFFFFFFF
        init_rng = random.Random(glyph_seed)
        dx = max(-_MOTOR_LIMIT, min(_MOTOR_LIMIT, init_rng.gauss(0, _MOTOR_INIT_SIGMA)))
        dy = max(-_MOTOR_LIMIT, min(_MOTOR_LIMIT, init_rng.gauss(0, _MOTOR_INIT_SIGMA)))
        self._state.motor_memory[glyph_id] = (dx, dy)

    def advance_line(self, line_index: int, n_words: int) -> None:
        """Update state at the start of a new line.

        Args:
            line_index: 0-based line index.
            n_words:    Number of words on this line (drives ink depletion).
        """
        s = self._state

        # Fatigue: monotonic, capped at 1.0
        s.fatigue = min(1.0, s.fatigue + self._fatigue_rate)

        # Motor memory: correlated random walk for all known glyphs
        rng = s._rng
        for glyph_id in list(s.motor_memory.keys()):
            dx, dy = s.motor_memory[glyph_id]
            dx = max(-_MOTOR_LIMIT, min(_MOTOR_LIMIT, dx + rng.gauss(0, _MOTOR_SIGMA_PER_LINE)))
            dy = max(-_MOTOR_LIMIT, min(_MOTOR_LIMIT, dy + rng.gauss(0, _MOTOR_SIGMA_PER_LINE)))
            s.motor_memory[glyph_id] = (dx, dy)

        # Ink: process one word boundary per word to advance the dip cycle
        for _ in range(max(1, n_words)):
            s.ink_state.process_word_boundary()
