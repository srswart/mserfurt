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


@dataclass(frozen=True)
class EmotionalLineState:
    """Content- and CLIO-7-driven emotional/cognitive state of Brother Konrad on a line."""
    state_name: str = "standard"
    rationale: str = "standard scriptorium flow"
    pressure_mult: float = 1.0
    width_mult: float = 1.0
    speed_mult: float = 1.0
    tremor_amp_mm: float = 0.010
    slant_delta_deg: float = 0.0
    baseline_undulation_mm: float = 0.0
    word_gap_mult: float = 1.0
    motor_calm_factor: float = 1.0
    force_fresh_dip: bool = False


def resolve_emotional_line_state(
    folio_id: str,
    line_index: int,
    line_text: str = "",
    register: str = "de",
) -> EmotionalLineState:
    """Determine Brother Konrad's emotional and motor state from the manuscript content & CLIO-7 apparatus.

    Models five distinct psychomotor states described in `source/ms-erfurt-source-annotated.md`:
      1. `sacred_steadiness`: The garden blessing scene (`f05r` L04–L09, 0-based 3..8) where CLIO-7 notes:
         *"The folio is clean here, the ink unsmeared, the hand steady. Some things a man writes carefully
         because he intends them to last."*
      2. `deepened_attention`: Where Konrad describes *"the slight thickening of a stroke when my attention
         deepened, the places where I slowed because the meaning arrived in my hands before it arrived in my mind"*
         (`f01v` L05–L11, `f02r` L14–L20, `f03r` L21–L23, `f03v` L01–L03 & L09, `f05v` L06–L11).
      3. `tremor_agitation`: Where Konrad writes of fear, guilt, human hands made to tremble, or standing beside
         the Mainz printing press feeling its impact in his feet (`f02r` L05–L08, `f02v` L18–L23, `f03r` L11–L14,
         `f06r/v`).
      4. `grief_hesitation`: Where Konrad recounts losing Peter and the broken farewell in the rosemary garden
         (`f04r` L11–L13 & L20–L21, `f04v` L07–L08 & L15–L18, `f05v` L12–L14).
      5. `latin_formal`: Ecclesiastical Latin prayers & verbatim Augustine quotations (`register == 'la'` or
         embedded Latin formulas), where monastic habit makes his hand more upright and deliberate.
    """
    fkey = folio_id.lstrip("f")
    txt_low = (line_text or "").lower()
    l_num = line_index + 1  # 1-based line number matching folio JSON

    # 1. CLIO-7 Garden Blessing Scene on f05r L04-L09, or Colophon on f17v L05-L12: extraordinary steadiness
    if (fkey == "05r" and 4 <= l_num <= 9) or (fkey == "17v" and 5 <= l_num <= 12):
        return EmotionalLineState(
            state_name="sacred_steadiness",
            rationale="CLIO-7: deliberate, steady hand ('Some things a man writes carefully because he intends them to last')",
            pressure_mult=1.05,
            width_mult=1.03,
            speed_mult=0.88,
            tremor_amp_mm=0.0,
            slant_delta_deg=-0.6,
            baseline_undulation_mm=0.0,
            word_gap_mult=1.04,
            motor_calm_factor=0.40,
            force_fresh_dip=(l_num in (4, 5)),
        )

    # 2. Verbatim Middle High German (Meister Eckhart's "In sînem grunde" & "Wirt" crux)
    if register == "mhg" or any(kw in txt_low for kw in ("in sînem grunde", "enpfêhet", "ich schreib: wirt", "ich schreib wirt")):
        return EmotionalLineState(
            state_name="deepened_attention",
            rationale="Meister Eckhart MHG theological crux ('Wirt') — intense focus, fresh dip & deliberate weight",
            pressure_mult=1.22,
            width_mult=1.14,
            speed_mult=0.78,
            tremor_amp_mm=0.004,
            slant_delta_deg=+0.4,
            baseline_undulation_mm=0.0,
            word_gap_mult=1.08,
            motor_calm_factor=0.72,
            force_fresh_dip=True,
        )

    # 3. Ecclesiastical Latin & Verbatim Augustine / Psalm 42 Quotations
    if register == "la" or any(
        kw in txt_low
        for kw in (
            "domine, confiteor",
            "secreto meo",
            "scrutaris corda",
            "deus misericordiae",
            "abysso animae",
            "augustinus scribit",
            "fecisti nos",
            "inquietum est",
            "sine licentia",
            "frater conradus",
            "haec est theologia",
            "in agro dominico",
            "quemadmodum desiderat",
            "sic desiderat anima",
            "legunt iudicium",
            "deo volente",
            "omnis spiritus",
            "gloria patri",
        )
    ):
        return EmotionalLineState(
            state_name="latin_formal",
            rationale="Monastic Latin liturgical/Augustinian/Psalm register — upright, formal scriptorium cadence",
            pressure_mult=1.04,
            width_mult=1.02,
            speed_mult=0.92,
            tremor_amp_mm=0.004,
            slant_delta_deg=-1.4,
            baseline_undulation_mm=0.0,
            word_gap_mult=1.03,
            motor_calm_factor=0.62,
            force_fresh_dip=any(q in txt_low for q in ("augustinus scribit", "quemadmodum desiderat", "sic desiderat")),
        )

    # 3. Tremor & Agitation (fear, trembling hands, Mainz press impact)
    if fkey in ("06r", "06v") or any(
        kw in txt_low
        for kw in (
            "zu zittern",
            "zu irren",
            "stein in der brust",
            "gefürchtet",
            "verborgen fewer",
            "maschine zu mainz",
            "in meinen füssen",
            "mit einer kraft",
        )
    ):
        return EmotionalLineState(
            state_name="tremor_agitation",
            rationale="Emotional agitation / physical tremor & lateral downstroke pressure",
            pressure_mult=1.18,
            width_mult=1.08,
            speed_mult=0.92,
            tremor_amp_mm=0.044,
            slant_delta_deg=+2.4,
            baseline_undulation_mm=0.14,
            word_gap_mult=1.06,
            motor_calm_factor=1.16,
        )

    # 4. Grief & Hesitation (losing Peter, rosemary garden farewell, failing eyes)
    if (
        (fkey == "04v" and (7 <= l_num <= 8 or 15 <= l_num <= 18))
        or (fkey == "04r" and l_num in (1, 12, 21))
        or (fkey == "05v" and 12 <= l_num <= 14)
        or any(
            kw in txt_low
            for kw in (
                "rosmarin",
                "kräutergarten",
                "stoltz",
                "augen, die mir feilen",
                "morgenlicht, sind",
                "nicht solde",
                "ich gedenke",
            )
        )
    ):
        return EmotionalLineState(
            state_name="grief_hesitation",
            rationale="Grief & hesitation in Peter narrative / rosemary garden farewell",
            pressure_mult=0.90,
            width_mult=0.94,
            speed_mult=0.76,
            tremor_amp_mm=0.032,
            slant_delta_deg=+1.2,
            baseline_undulation_mm=0.15,
            word_gap_mult=1.18,
            motor_calm_factor=1.12,
        )

    # 5. Deepened Attention (Konrad slowing down & thickening strokes when meaning arrives in his hands)
    if any(
        kw in txt_low
        for kw in (
            "verdickung",
            "aufmerksamkeit",
            "verlangsamte",
            "in meine hende kam",
            "zeugnis, daß ein mensch",
            "druckunge meiner finger",
            "froh, daß es meine hand",
            "gerissenen pergament",
            "etliche sätze",
            "übergabe mir etwas",
            "einsamkeit vollkommen",
            "bewegte sich die strömung",
            "winter des jares",
            "baierisch kalbfell",
            "kalbspergament",
            "desiderat — verlanget",
            "das werck ist immer noch",
            "nicht verbrennen",
            "zwischen das breviarium",
            "ich hielt das blat",
        )
    ):
        return EmotionalLineState(
            state_name="deepened_attention",
            rationale="Konrad's deepened attention — slower tempo & thicker, heavier downstrokes",
            pressure_mult=1.22,
            width_mult=1.13,
            speed_mult=0.80,
            tremor_amp_mm=0.005,
            slant_delta_deg=+0.6,
            baseline_undulation_mm=0.0,
            word_gap_mult=1.05,
            motor_calm_factor=0.82,
        )

    # 6. Final Gathering Compensating Hand (f14r onward: slower, wider-spaced, compensating for failing winter eyesight)
    digits = "".join(ch for ch in fkey if ch.isdigit())
    fnum = int(digits) if digits else 1
    if fnum >= 14:
        return EmotionalLineState(
            state_name="compensating_eyesight",
            rationale="CLIO-7 Section 7: slower, wider-spaced hand on irregular offcut vellum compensating for failing eyesight",
            pressure_mult=1.04,
            width_mult=1.03,
            speed_mult=0.82,
            tremor_amp_mm=0.018,
            slant_delta_deg=+0.8,
            baseline_undulation_mm=0.10,
            word_gap_mult=1.12,
            motor_calm_factor=1.06,
        )

    return EmotionalLineState()


class KinematicScribeSession:
    """Persistent temporal state for kinematic word/line/folio writing (TD-019 Phase 16c).

    Tracks:
      - Slow correlated motor-memory walk per glyph & via-point role
      - Word-initial attack envelope + cross-word air momentum carryover
      - Realistic quill dip cycle (4-6 dips per folio page) & sitting-boundary reloads
      - Content- and emotion-driven scribal affect per line (`active_emotion`)
      - Fatigue and nib-angle drift across lines
    """

    def __init__(
        self,
        folio_id: str = "f01r",
        *,
        seed: int = 1457,
        fatigue_rate: float = 0.022,
        ink_depletion_rate: float = 0.0018,
    ) -> None:
        self.folio_id = folio_id
        self.seed = seed
        self.fatigue_rate = fatigue_rate
        self.current_line: int = 0
        self.word_counter: int = 0
        self.glyph_occurrence_counter: dict[str, int] = {}
        self.sitting_reloads: int = 0
        self.last_word_exit_y_wnib: float | None = None
        self.active_emotion: EmotionalLineState = EmotionalLineState()
        self.dip_events: list[dict] = []

        rng = random.Random(_stable_seed(folio_id, seed, "session"))
        ink = InkState(
            capacity=1.0,
            base_depletion=ink_depletion_rate,
            dip_threshold=0.22,
            preferred_dip_threshold=0.36,
        )
        self.state = ScribeState(ink_state=ink, _rng=rng)
        # Correlated walk state per letter: letter -> [dx, dy, slant, arch, p_bias]
        self._letter_walk: dict[str, list[float]] = {}
        self._sitting_boundaries = set(SITTING_BOUNDARIES_BY_FOLIO.get(folio_id, ()))

    def dip_attention_factor(self) -> float:
        """Compute scribal dip vigilance (TD-021) from emotional state and accumulated fatigue.

        > 1.0: extra-careful (dips early on the upper capillary plateau)
        < 1.0: distracted / agitated / fatigued (occasionally rides lower into the soft shoulder)
        """
        emo_name = self.active_emotion.state_name
        if emo_name in ("sacred_steadiness", "deepened_attention"):
            base_att = 1.22
        elif emo_name in ("latin_formal", "controlled_correction"):
            base_att = 1.12
        elif emo_name in ("tremor_agitation", "grief_hesitation", "compensating_eyes"):
            base_att = 0.80
        else:
            base_att = 1.02
        return max(0.72, min(1.28, base_att - 0.14 * self.state.fatigue))

    def advance_to_line(self, line_index: int, line_text: str = "", register: str = "de") -> None:
        """Advance session state to `line_index`, updating emotional state, sitting boundaries, and fatigue."""
        self.active_emotion = resolve_emotional_line_state(
            self.folio_id, line_index, line_text=line_text, register=register
        )
        if line_index in self._sitting_boundaries or self.active_emotion.force_fresh_dip:
            self.state.ink_state.dip()
            self.sitting_reloads += 1
            self.last_word_exit_y_wnib = None
            self.dip_events.append(
                {
                    "folio_id": self.folio_id,
                    "line_index": line_index,
                    "word_counter": self.word_counter,
                    "reason": "sacred_steadiness_dip" if self.active_emotion.force_fresh_dip else "sitting_boundary",
                }
            )

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
                init_rng.uniform(-0.027, 0.027),  # dx_wnib
                init_rng.uniform(-0.022, 0.022),  # dy_wnib
                init_rng.uniform(-0.020, 0.020),  # slant_shear
                init_rng.uniform(-0.031, 0.031),  # peak_arch_dy
                init_rng.uniform(-0.020, 0.020),  # x_scale_delta
            ]

        vec = self._letter_walk[letter]
        step_rng = random.Random(_stable_seed(self.folio_id, self.seed, "occ", letter, occ, self.word_counter))
        # Subtle fatigue modulation (+10% across a full page, never erratic)
        calm = self.active_emotion.motor_calm_factor * (1.0 + 0.10 * self.state.fatigue)

        # Correlated AR(1) random walk calibrated 85% toward seasoned 30-year scribe consistency:
        # steady x-height ribbon and parallel stems, with gentle personal-journal life.
        deltas = (0.093 * calm, 0.064 * calm, 0.059 * calm, 0.122 * calm, 0.047 * calm)
        cap_mult = min(1.15, max(0.85, calm))
        limits = (0.20 * cap_mult, 0.144 * cap_mult, 0.118 * cap_mult, 0.255 * cap_mult, 0.085 * cap_mult)
        phase = (occ + 1) * 1.73 + self.word_counter * 0.91 + self.current_line * 0.63
        for i in range(5):
            step = step_rng.gauss(0.0, deltas[i]) + 0.40 * deltas[i] * math.sin(phase + i * 1.3)
            val = 0.65 * vec[i] + step
            vec[i] = max(-limits[i], min(limits[i], val))

        entry_hook_dx = 0.0
        entry_hook_dy = 0.0
        loop_spread_dx = round((step_rng.uniform(-0.24, 0.26) + 0.11 * math.cos(phase * 1.3)) * calm, 4)
        loop_height_dy = round((step_rng.uniform(-0.26, 0.29) + 0.13 * math.sin(phase * 0.9)) * calm, 4)
        word_baseline_dy = round(0.090 * calm * math.sin(self.word_counter * 0.85 + self.current_line * 1.4), 4)
        y_scale = round(1.0 + step_rng.uniform(-0.032 * calm, 0.035 * calm), 4)

        if is_word_initial:
            # Cross-word air carryover + word-onset attack variation
            air_pull = 0.0
            if prev_word_exit_y_wnib is not None:
                air_pull = max(-0.20, min(0.20, (prev_word_exit_y_wnib - 1.2) * 0.10))
            onset_angle = (occ * 2.17 + self.word_counter * 1.31 + self.current_line * 0.79)
            entry_hook_dx = round((0.23 * math.cos(onset_angle) + step_rng.uniform(-0.09, 0.09)) * calm, 4)
            entry_hook_dy = round((0.24 * math.sin(onset_angle) + air_pull) * calm, 4)

        slant_from_emotion = math.tan(math.radians(self.active_emotion.slant_delta_deg)) * 0.85

        return {
            "dx_wnib": round(vec[0], 4),
            "dy_wnib": round(vec[1] + word_baseline_dy, 4),
            "slant_shear": round(vec[2] + slant_from_emotion, 4),
            "peak_arch_dy": round(vec[3], 4),
            "x_scale": round(1.0 + vec[4], 4),
            "y_scale": y_scale,
            "entry_hook_dx": entry_hook_dx,
            "entry_hook_dy": entry_hook_dy,
            "loop_spread_dx": loop_spread_dx,
            "loop_height_dy": loop_height_dy,
            "nib_angle_drift_deg": round(
                (self.state.nib_angle_drift_deg(self.current_line) + 1.30 * math.sin(phase)) * calm, 3
            ),
            "occ": occ,
        }

    def viapoint_internal_nuance(
        self,
        letter: str,
        occ: int,
        v_idx: int,
        role: str,
        *,
        is_word_initial: bool,
    ) -> tuple[float, float, float]:
        """Compute per-via-point internal shape nuance (dx_wnib, dy_wnib, dp) so repeated letters are never rigid translations."""
        vp_rng = random.Random(
            _stable_seed(self.folio_id, self.seed, "vp", letter, occ, v_idx, self.word_counter, self.current_line)
        )
        calm = self.active_emotion.motor_calm_factor * (1.0 + 0.08 * self.state.fatigue)
        if role == "loop":
            amp_x, amp_y = 0.105 * calm, 0.140 * calm
        elif role == "peak":
            amp_x, amp_y = 0.068 * calm, 0.090 * calm
        elif role in ("entry", "exit"):
            amp_x, amp_y = 0.108 * calm, 0.130 * calm
        else:
            # body and turn points: 85% toward seasoned consistency
            amp_x, amp_y = 0.033 * calm, 0.050 * calm

        dx = vp_rng.uniform(-amp_x, amp_x)
        dy = vp_rng.uniform(-amp_y, amp_y)
        dp = vp_rng.uniform(-0.040, 0.040)

        if is_word_initial and v_idx <= 1:
            # 3 word-initial onset styles (sweeping hook vs upright attack vs diamond attack)
            style = (occ + self.word_counter + self.current_line) % 3
            if v_idx == 0:
                if style == 0:
                    dx -= 0.155 * calm
                    dy -= 0.115 * calm
                elif style == 1:
                    dx += 0.085 * calm
                    dy += 0.135 * calm
                else:
                    dx -= 0.065 * calm
                    dy += 0.170 * calm
                    dp += 0.055
            elif v_idx == 1:
                dx += (0.050 if style == 1 else -0.040) * calm

        return round(dx, 4), round(dy, 4), round(dp, 4)

