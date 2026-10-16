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

import hashlib
import math
import random
from dataclasses import dataclass, field

from scribesim.ink.cycle import InkState, ink_darkness


def _stable_seed(*parts: object) -> int:
    """Compute a deterministic 32-bit seed independent of PYTHONHASHSEED."""
    raw = ":".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:4], "big")


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

    def consume_contact_distance(
        self,
        stroke_length_mm: float,
        avg_pressure: float = 0.72,
        avg_width_mm: float = 0.8333,
    ) -> float:
        """Consume ink continuously along on-surface contact arc length and return updated ink_level."""
        if stroke_length_mm > 0:
            self.ink_state.deplete_for_step(stroke_length_mm, avg_pressure, avg_width_mm)
        return self.ink_level


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
        seed = _stable_seed(folio_id)
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
        glyph_seed = _stable_seed(self._folio_id, glyph_id)
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


# ---------------------------------------------------------------------------
# TD-019 Phase 16c: KinematicScribeSession & CLIO-7 Folio Modifiers
# ---------------------------------------------------------------------------

SITTING_BOUNDARIES_BY_FOLIO: dict[str, tuple[int, ...]] = {
    "07r": (8, 17, 25),
    "f07r": (8, 17, 25),
}


def resolve_clio7_kinematic_profile(
    folio_id: str,
    *,
    line_index: int = 0,
    base_profile: "HandProfile | None" = None,
) -> "HandProfile":
    """Resolve a Bastarda kinematic HandProfile with CLIO-7 per-folio and per-line overrides."""
    import copy
    from scribesim.hand.profile import (
        bastarda_nib_calibrated_profile,
        nib_width_for_x_height,
        resolve_profile,
    )

    base = copy.deepcopy(base_profile) if base_profile is not None else bastarda_nib_calibrated_profile()
    prof = resolve_profile(base, folio_id)
    # Keep Bastarda calibrated 4.2:1 nib proportion unless overridden
    prof.letterform.x_height_mm = 3.5
    prof.nib.width_mm = nib_width_for_x_height(prof.letterform.x_height_mm, 4.2)

    fkey = folio_id.lstrip("f")
    digits = "".join(ch for ch in fkey if ch.isdigit())
    fnum = int(digits) if digits else 1

    if fkey in ("06r", "06v"):
        # f06r/v: increased lateral pressure on downstrokes (agitation/tension)
        prof.folio.base_pressure = 0.84 if fkey == "06r" else 0.82
        prof.slant_deg = 2.8
    elif fkey == "07r":
        # f07r: multi-sitting variable ink density
        prof.ink_density = 0.91
    elif fkey == "07v":
        if line_index >= 16:
            # f07v lower half (apply_from_line = 16): smaller, economical working register (85% scale)
            prof.letterform.x_height_mm = round(3.5 * 0.85, 4)
            prof.nib.width_mm = nib_width_for_x_height(prof.letterform.x_height_mm, 4.2)
            prof.letter_spacing_norm = 0.92
            prof.writing_speed = 1.15
        else:
            # Upper half of f07v still uses standard register
            prof.letter_spacing_norm = 1.0
            prof.writing_speed = 1.0
            prof.x_height_px = 38
    elif fnum >= 14:
        # f14r onward: slower, wider-spaced compensating hand (failing eyes)
        drift_rate = 0.008 if fnum == 14 else 0.010
        prof.letter_spacing_norm = round(1.12 + drift_rate * line_index, 4)
        prof.word.spacing_mean_ratio = round(1.42 + drift_rate * line_index, 4)
        prof.writing_speed = 0.82
        prof.nib.angle_deg = 42.0
        prof.folio.tremor_amplitude = 0.003

    return prof


class KinematicScribeSession:
    """Persistent temporal state for kinematic word/line/folio writing (TD-019 Phase 16c).

    Tracks:
      - Slow correlated motor-memory walk per glyph & via-point role
      - Word-initial attack envelope + cross-word air momentum carryover
        (so words starting with the same letter have distinct onset nuances)
      - Continuous contact-distance ink depletion & sitting-boundary reloads
      - Fatigue and nib-angle drift across lines
    """

    def __init__(
        self,
        folio_id: str = "f01r",
        *,
        seed: int = 1457,
        fatigue_rate: float = 0.022,
        ink_depletion_rate: float = 0.0014,
    ) -> None:
        self.folio_id = folio_id
        self.seed = seed
        self.fatigue_rate = fatigue_rate
        self.current_line: int = 0
        self.word_counter: int = 0
        self.glyph_occurrence_counter: dict[str, int] = {}
        self.sitting_reloads: int = 0
        self.last_word_exit_y_wnib: float | None = None

        rng = random.Random(_stable_seed(folio_id, seed, "session"))
        ink = InkState(
            capacity=1.0,
            base_depletion=ink_depletion_rate,
            dip_threshold=0.18,
            preferred_dip_threshold=0.24,
        )
        self.state = ScribeState(ink_state=ink, _rng=rng)
        # Correlated walk state per letter: letter -> [dx, dy, slant, arch, p_bias]
        self._letter_walk: dict[str, list[float]] = {}
        self._sitting_boundaries = set(SITTING_BOUNDARIES_BY_FOLIO.get(folio_id, ()))

    def advance_to_line(self, line_index: int) -> None:
        """Advance session state to `line_index`, checking sitting boundaries and fatigue."""
        if line_index in self._sitting_boundaries:
            self.state.ink_state.dip()
            self.sitting_reloads += 1
            self.last_word_exit_y_wnib = None

        steps = max(1, line_index - self.current_line) if line_index > self.current_line else 1
        self.current_line = line_index
        self.state.fatigue = min(1.0, self.state.fatigue + self.fatigue_rate * steps)
        self.last_word_exit_y_wnib = None

    def next_letter_variation(
        self,
        letter: str,
        *,
        is_word_initial: bool,
        prev_word_exit_y_wnib: float | None = None,
    ) -> dict[str, float]:
        """Advance the correlated motor-memory walk for `letter` and return via-point nuances.

        For word-initial letters (`is_word_initial=True`), incorporates cross-word air
        arrival height from `prev_word_exit_y_wnib` plus a word-onset attack posture so
        repeated word-initial letters never follow a rigid identical formula.
        """
        occ = self.glyph_occurrence_counter.get(letter, 0)
        self.glyph_occurrence_counter[letter] = occ + 1

        if letter not in self._letter_walk:
            init_rng = random.Random(_stable_seed(self.folio_id, self.seed, "init", letter))
            self._letter_walk[letter] = [
                init_rng.uniform(-0.04, 0.04),  # dx_wnib
                init_rng.uniform(-0.04, 0.04),  # dy_wnib
                init_rng.uniform(-0.03, 0.03),  # slant_shear
                init_rng.uniform(-0.05, 0.05),  # peak_arch_dy
                init_rng.uniform(-0.03, 0.03),  # x_scale_delta
            ]

        vec = self._letter_walk[letter]
        step_rng = random.Random(_stable_seed(self.folio_id, self.seed, "occ", letter, occ, self.word_counter))

        # Correlated AR(1) random walk with bounded reflection so consecutive occurrences differ smoothly
        deltas = (0.038, 0.038, 0.026, 0.048, 0.025)
        limits = (0.11, 0.11, 0.065, 0.14, 0.06)
        phase = (occ + 1) * 1.37 + self.word_counter * 0.73
        for i in range(5):
            step = step_rng.gauss(0.0, deltas[i]) + 0.32 * deltas[i] * math.sin(phase + i * 1.1)
            val = 0.78 * vec[i] + step
            vec[i] = max(-limits[i], min(limits[i], val))

        entry_hook_dx = 0.0
        entry_hook_dy = 0.0
        if is_word_initial:
            # Cross-word air carryover + word-onset posture variation
            air_pull = 0.0
            if prev_word_exit_y_wnib is not None:
                air_pull = max(-0.14, min(0.14, (prev_word_exit_y_wnib - 1.2) * 0.08))
            onset_angle = (occ * 1.91 + self.word_counter * 1.13 + self.current_line * 0.57)
            entry_hook_dx = round(0.095 * math.cos(onset_angle) + step_rng.uniform(-0.035, 0.035), 4)
            entry_hook_dy = round(0.115 * math.sin(onset_angle) + air_pull, 4)

        return {
            "dx_wnib": round(vec[0], 4),
            "dy_wnib": round(vec[1], 4),
            "slant_shear": round(vec[2], 4),
            "peak_arch_dy": round(vec[3], 4),
            "x_scale": round(1.0 + vec[4], 4),
            "entry_hook_dx": entry_hook_dx,
            "entry_hook_dy": entry_hook_dy,
            "nib_angle_drift_deg": round(self.state.nib_angle_drift_deg(self.current_line) + 0.8 * math.sin(phase), 3),
        }

