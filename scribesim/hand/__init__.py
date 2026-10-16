"""Hand model — load base parameters and apply per-folio modifiers."""

from scribesim.hand.params import HandParams
from scribesim.hand.modifiers import MODIFIER_REGISTRY
from scribesim.hand.model import load_base, resolve, resolve_hand
from scribesim.hand.profile import (
    HandProfile,
    load_profile,
    resolve_profile,
    parse_overrides,
    validate_ranges,
    nib_width_for_x_height,
    x_height_to_nib_ratio,
    bastarda_nib_calibrated_profile,
)


__all__ = [
    "HandParams", "MODIFIER_REGISTRY", "load_base", "resolve",
    "HandProfile", "load_profile", "resolve_profile",
    "parse_overrides", "validate_ranges",
    "nib_width_for_x_height", "x_height_to_nib_ratio",
    "bastarda_nib_calibrated_profile",
]
