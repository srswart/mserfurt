"""Named modifier functions for the scribal hand model.

Each modifier takes a HandParams and returns a new HandParams with specific
fields adjusted. Modifiers are pure functions — no mutation.

Registry maps CLIO-7 hand note keys → modifier factory callables.
"""

from __future__ import annotations

from scribesim.hand.params import HandParams


# ---------------------------------------------------------------------------
# Modifier functions
# ---------------------------------------------------------------------------

def pressure_increase(params: HandParams, amount: float = 0.12) -> HandParams:
    """Raise downstroke pressure (f06r–f06v: increased lateral pressure).

    Slightly reduces slant (more upright under tension) and boosts stroke weight.
    """
    return HandParams.from_dict({
        **params.to_dict(),
        "pressure_base": params.pressure_base + amount,
        "stroke_weight": params.stroke_weight + 0.15,
        "slant_deg": max(1.0, params.slant_deg - 0.7),
    })


def ink_density_shift(params: HandParams, amount: float = 0.06) -> HandParams:
    """Adjust ink density at a sitting boundary (f07r: multi-sitting).

    First sitting: freshly loaded quill — richer ink, slightly higher variance.
    """
    return HandParams.from_dict({
        **params.to_dict(),
        "ink_density": params.ink_density + amount,
        "pressure_variance": params.pressure_variance + 0.04,
    })


def hand_scale(params: HandParams, scale: float = 0.84) -> HandParams:
    """Scale glyph dimensions (f07v lower: smaller economical working hand).

    Reduces x_height and tightens spacing norms proportionally.
    """
    return HandParams.from_dict({
        **params.to_dict(),
        "x_height_px": max(20, round(params.x_height_px * scale)),
        "letter_spacing_norm": params.letter_spacing_norm * scale,
        "writing_speed": min(2.0, params.writing_speed * 1.15),
    })


def spacing_drift(params: HandParams, amount: float = 0.12) -> HandParams:
    """Widen spacing as fatigue sets in (f14r+: irregular vellum, slower hand).

    Also enlarges x-height slightly as Konrad compensates for vellum texture.
    """
    return HandParams.from_dict({
        **params.to_dict(),
        "letter_spacing_norm": params.letter_spacing_norm + amount,
        "word_spacing_norm": params.word_spacing_norm + amount * 2.5,
        "x_height_px": params.x_height_px + 4,
        "writing_speed": max(0.0, params.writing_speed - 0.18),
    })


def tremor(params: HandParams, amplitude: float = 0.04) -> HandParams:
    """Introduce stroke tremor (f14r+: fatigue, irregular vellum resistance)."""
    return HandParams.from_dict({
        **params.to_dict(),
        "tremor_amplitude": params.tremor_amplitude + amplitude,
        "fatigue_rate": params.fatigue_rate + 0.012,
    })


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

MODIFIER_REGISTRY: dict[str, callable] = {
    "pressure_increase": pressure_increase,
    "ink_density_shift": ink_density_shift,
    "hand_scale": hand_scale,
    "spacing_drift": spacing_drift,
    "tremor": tremor,
}
