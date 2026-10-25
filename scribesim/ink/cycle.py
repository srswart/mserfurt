"""Ink reservoir model — TD-010 Parts 1, 2.1, 2.2, 2.3.

Models the physical ink cycle of a quill: reservoir depletes as strokes are
rendered, the scribe dips between words when running low. Downstream rendering
effects (darkness, width, hairline quality) are driven by the reservoir level.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, auto


# ---------------------------------------------------------------------------
# Reservoir → rendering effect curves (TD-010 Parts 2.1 and 2.2)
# ---------------------------------------------------------------------------

def ink_darkness(reservoir: float) -> float:
    """Map reservoir level to a darkness scaling factor.

    Uses a power curve (reservoir^0.4) so that:
    - Near full: a large reservoir change barely affects output (realistic)
    - Near empty: a small reservoir change is very visible (realistic)

    Returns a factor in [0.58, 0.98]:
      reservoir=1.0 → 0.98  (fresh dip, rich but not clipped)
      reservoir=0.5 → 0.87  (slightly lighter than full)
      reservoir=0.2 → 0.77  (visibly lighter)
      reservoir=0.05 → 0.68 (quite faded)
      reservoir=0.0 → 0.58  (floor — a dry quill still marks the vellum)
    """
    reservoir = max(0.0, min(1.0, reservoir))
    flow_curve = reservoir ** 0.45
    return 0.58 + 0.40 * flow_curve


def ink_width_modifier(reservoir: float) -> float:
    """Map reservoir level to a nib width scaling factor.

    A saturated nib spreads ink laterally; a depleted nib produces thinner
    strokes. Effect is visible but bounded so legibility is preserved.

    Returns a factor in [0.90, 1.08]:
      reservoir=1.0 → 1.08  (8% wider — fresh ink wicks into vellum)
      reservoir=0.5 → 1.02  (slightly wider than neutral)
      reservoir=0.0 → 0.90  (10% thinner — visibly dry but still legible)
    """
    reservoir = max(0.0, min(1.0, reservoir))
    flow_curve = reservoir ** 0.55
    return 0.90 + 0.18 * flow_curve


# ---------------------------------------------------------------------------
# Three-regime capillary plateau curves (TD-021)
# ---------------------------------------------------------------------------

def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Hermite C¹ smoothstep interpolation in [0.0, 1.0]."""
    if edge1 <= edge0:
        return 1.0 if x >= edge1 else 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def capillary_flow_curve(reservoir: float) -> tuple[float, float, float]:
    """Return (shoulder, plateau, fresh_settle) smoothstep components for TD-021.

    - `shoulder`:     smoothstep(0.08, 0.42, r) — gradual meniscus roll-off below 0.42
    - `plateau`:      smoothstep(0.40, 0.90, r) — nearly flat capillary working hold
    - `fresh_settle`: smoothstep(0.86, 1.00, r) — brief post-dip bead richness
    """
    r = max(0.0, min(1.0, reservoir))
    shoulder = smoothstep(0.08, 0.42, r)
    plateau = smoothstep(0.40, 0.90, r)
    fresh = smoothstep(0.86, 1.00, r)
    return shoulder, plateau, fresh


def ink_darkness_capillary(reservoir: float) -> float:
    """Map reservoir level to darkness via TD-021 three-regime capillary plateau curve.

    Key points:
      r = 1.00 → 1.000 (fresh dip bead)
      r = 0.85 → 0.960 (settled capillary plateau)
      r = 0.50 → 0.922 (still on plateau; < 4% change across 0.45..0.85)
      r = 0.35 → 0.885 (upper shoulder where an attentive scribe dips)
      r = 0.22 → 0.805 (late dip under agitation/fatigue)
      r = 0.00 → 0.720 (dry floor)
    """
    shoulder, plateau, fresh = capillary_flow_curve(reservoir)
    return 0.72 + 0.19 * shoulder + 0.055 * plateau + 0.035 * fresh


def ink_width_modifier_capillary(reservoir: float) -> float:
    """Map reservoir level to nib width modifier with a flat capillary plateau.

    Key points:
      r = 1.00 → 1.035 (subtle fresh-dip spread)
      r = 0.70 → 1.005 (steady working width)
      r = 0.45 → 0.992 (nearly unchanged across the plateau)
      r = 0.20 → 0.950 (gentle thinning in the shoulder)
      r = 0.00 → 0.920 (dry floor)
    """
    shoulder, plateau, fresh = capillary_flow_curve(reservoir)
    return 0.92 + 0.068 * shoulder + 0.022 * plateau + 0.025 * fresh


# ---------------------------------------------------------------------------
# Hairline degradation curves (TD-010 Part 2.3)
# ---------------------------------------------------------------------------

@dataclass
class HairlineEffects:
    """Continuous hairline degradation values derived from reservoir level.

    All three values are effectively 0.0 at normal reservoir levels (> 0.4).
    They only become significant as the quill approaches empty, simulating
    the progressive degradation of thin strokes when ink runs low.
    """
    width_reduction: float    # 0.0 = no reduction, 0.45 = max (45% thinner)
    gap_probability: float    # per-sample probability of a break in the hairline
    raking_probability: float # per-stroke probability of split-nib double-line


def hairline_effects(reservoir: float) -> HairlineEffects:
    """Compute continuous hairline degradation from reservoir level.

    All three effects use sigmoid curves centred at low reservoir levels so
    they are imperceptible in normal writing and only emerge near empty.
    Uses the form: effect = max_value / (1 + exp(k * (reservoir - centre)))

    Width reduction:  centre=0.18, k=15 — noticeable below ~0.3
    Gap probability:  centre=0.15, k=18 — noticeable below ~0.25
    Raking:           centre=0.08, k=25 — only at very low levels < ~0.15
    """
    reservoir = max(0.0, min(1.0, reservoir))

    width_sigmoid = 1.0 / (1.0 + math.exp(15.0 * (reservoir - 0.18)))
    gap_sigmoid   = 1.0 / (1.0 + math.exp(18.0 * (reservoir - 0.15)))
    rake_sigmoid  = 1.0 / (1.0 + math.exp(25.0 * (reservoir - 0.08)))

    return HairlineEffects(
        width_reduction=width_sigmoid * 0.45,
        gap_probability=gap_sigmoid * 0.25,
        raking_probability=rake_sigmoid * 0.30,
    )


# ---------------------------------------------------------------------------
# Post-dip blob (TD-010 Part 2.4)
# ---------------------------------------------------------------------------

@dataclass
class BlobParams:
    """Parameters for a small excess-ink blob deposited at first contact after dip."""
    radius_mm: float        # blob radius (0.2–0.5mm)
    darkness_boost: float   # additive darkness boost (0.2 = 20% darker than base)
    elongation: float       # >1.0 = elongated ellipse along stroke direction


def post_dip_blob(
    reservoir: float,
    strokes_since_dip: int,
    *,
    probability: float = 0.15,
) -> "BlobParams | None":
    """Return blob parameters for the first stroke after a dip, or None.

    A fresh quill sometimes deposits a small excess-ink blob at the first
    contact point — ink has accumulated in the nib slit and is released on
    first touch. This only occurs on the very first stroke after dipping
    (strokes_since_dip == 0) when the reservoir is full (> 0.90).

    Args:
        reservoir: Current ink level (0.0–1.0).
        strokes_since_dip: Number of strokes drawn since the last dip.
        probability: Chance of a blob for a careful scribe (default 0.15).
    """
    import random as _random
    if strokes_since_dip != 0 or reservoir <= 0.90:
        return None
    if _random.random() >= probability:
        return None
    radius_mm = 0.2 + _random.random() * 0.3   # uniform 0.2–0.5mm
    return BlobParams(
        radius_mm=radius_mm,
        darkness_boost=0.20,
        elongation=1.0 + _random.random() * 0.5,  # 1.0–1.5× elongated
    )


class DipEvent(Enum):
    NoDip = auto()
    PreferredDip = auto()   # scribe chose to dip (reservoir < preferred threshold)
    ForcedDip = auto()      # reservoir critically low, must dip


class InkState:
    """Tracks the ink reservoir and dip cycle across a writing session.

    The reservoir starts full (1.0) after each dip and depletes as strokes are
    rendered. The scribe dips between words when the reservoir gets low.

    Physical properties are calibrated against manuscript observation (TD-010):
      - base_depletion = 0.002 per mm at standard pressure/width
        (TD-010 specifies 0.0008 as the starting point; calibrated to 0.002
        against the actual stroke lengths produced by GLYPH_CATALOG at x_height=3.8mm
        — average strokes are ~4mm and 6 strokes per word gives ~24mm per word)
      - 35–45 words per dip cycle for a professional scribe
      - 6–8 dips per folio page
    """

    def __init__(
        self,
        capacity: float = 1.0,
        base_depletion: float = 0.002,
        viscosity: float = 1.0,
        dip_threshold: float = 0.15,
        preferred_dip_threshold: float = 0.22,
    ) -> None:
        self.capacity = capacity
        self.base_depletion = base_depletion
        self.viscosity = viscosity
        self.dip_threshold = dip_threshold
        self.preferred_dip_threshold = preferred_dip_threshold

        self.reservoir: float = capacity
        self.strokes_since_dip: int = 0
        self.words_since_dip: int = 0
        self.total_dips: int = 0
        self.last_dip_trigger: str = ""

    # ------------------------------------------------------------------
    # State queries

    def should_dip(self) -> bool:
        """Reservoir critically low — must dip at next opportunity."""
        return self.reservoir < self.dip_threshold

    def wants_to_dip(
        self,
        *,
        word_text: str = "",
        next_word_len: int = 0,
        is_line_end: bool = False,
        attention: float = 1.0,
    ) -> bool:
        """Reservoir getting low — prefer to dip between words rather than
        risk running dry mid-word.

        Under TD-021, an attentive scribe also looks ahead at clause pauses,
        line ends, and long upcoming words, and modulates vigilance by `attention`.
        """
        return self._evaluate_dip_trigger(
            word_text=word_text,
            next_word_len=next_word_len,
            is_line_end=is_line_end,
            attention=attention,
        ) is not None

    def _evaluate_dip_trigger(
        self,
        *,
        word_text: str = "",
        next_word_len: int = 0,
        is_line_end: bool = False,
        attention: float = 1.0,
    ) -> str | None:
        """Return the trigger reason if the scribe prefers to dip now, else None."""
        att_shift = max(-0.08, min(0.08, (attention - 1.0) * 0.25))
        eff_pref = self.preferred_dip_threshold + att_shift

        if self.reservoir < eff_pref:
            return "preferred_shoulder"

        stripped = word_text.strip()
        if stripped and stripped[-1] in ".,;:?!—)" and self.reservoir < eff_pref + 0.08:
            return "punctuation_pause"

        if is_line_end and self.reservoir < eff_pref + 0.07:
            return "line_end"

        if next_word_len >= 7:
            est_demand = 0.011 * next_word_len
            if (self.reservoir - est_demand) < (self.dip_threshold + 0.11 + max(0.0, att_shift)):
                return "long_word_lookahead"

        return None

    # ------------------------------------------------------------------
    # State transitions

    def dip(self) -> None:
        """Dip the quill — restore reservoir to full capacity."""
        self.reservoir = self.capacity
        self.strokes_since_dip = 0
        self.words_since_dip = 0
        self.total_dips += 1

    def deplete_for_stroke(
        self,
        stroke_length_mm: float,
        avg_pressure: float,
        avg_width_mm: float,
    ) -> None:
        """Consume ink for one rendered stroke segment.

        Consumption is proportional to stroke area (length × width) and
        pressure. Thicker ink (higher viscosity) depletes slower.

        Formula from TD-010:
            consumption = length * pressure * (width / 2.0) * base_depletion / viscosity
        """
        consumption = (
            stroke_length_mm
            * avg_pressure
            * (avg_width_mm / 2.0)
            * self.base_depletion
            / self.viscosity
        )
        self.reservoir = max(0.0, self.reservoir - consumption)
        self.strokes_since_dip += 1

    def deplete_for_step(
        self,
        stroke_length_mm: float,
        avg_pressure: float,
        avg_width_mm: float,
    ) -> None:
        """Consume ink without marking a full stroke boundary.

        Used by renderers that model depletion continuously within a stroke so
        darkness can fade across the drawn path instead of only between strokes.
        """
        consumption = (
            stroke_length_mm
            * avg_pressure
            * (avg_width_mm / 2.0)
            * self.base_depletion
            / self.viscosity
        )
        self.reservoir = max(0.0, self.reservoir - consumption)

    def finish_stroke(self) -> None:
        """Record that one stroke has completed."""
        self.strokes_since_dip += 1

    def process_word_boundary(
        self,
        *,
        word_text: str = "",
        next_word_len: int = 0,
        is_line_end: bool = False,
        attention: float = 1.0,
    ) -> DipEvent:
        """Called after each word is rendered.

        Decides whether the scribe dips. Returns the dip event for logging.
        """
        self.words_since_dip += 1

        if self.should_dip():
            self.last_dip_trigger = "forced_low"
            self.dip()
            return DipEvent.ForcedDip

        trigger = self._evaluate_dip_trigger(
            word_text=word_text,
            next_word_len=next_word_len,
            is_line_end=is_line_end,
            attention=attention,
        )
        if trigger is not None:
            self.last_dip_trigger = trigger
            self.dip()
            return DipEvent.PreferredDip

        self.last_dip_trigger = ""
        return DipEvent.NoDip
