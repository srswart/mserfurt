"""Pair-dependent spacing (kerning) for Bastarda letterforms.

Computes inter-glyph spacing based on exit/entry point positions.
Glyphs whose exit point is far right and whose neighbor's entry point
is far left naturally sit closer together. The kerning adjustment
brings them to a natural pen-travel distance.
"""

from __future__ import annotations

import numpy as np

from scribesim.glyphs.glyph import Glyph
from scribesim.glyphs.catalog import GLYPH_CATALOG


# Target gap between exit and entry in x-height units.
# This represents the natural pen-travel distance during a connection.
# 0.25 = comfortable reading distance; 0.12 was too tight.
_TARGET_GAP = 0.25

# Minimum gap to prevent overlap
_MIN_GAP = 0.08

# Maximum kerning adjustment (x-height units) to prevent extreme shifts
_MAX_KERN = 0.10


def kern_pair(prev_glyph: Glyph, next_glyph: Glyph) -> float:
    """Compute kerning adjustment for a glyph pair.

    Returns a horizontal offset (in x-height units) to add to the
    standard advance width. Negative = tighter, positive = looser.

    The adjustment brings the gap between prev.exit_x and next.entry_x
    closer to _TARGET_GAP.
    """
    if prev_glyph.exit_point is None or next_glyph.entry_point is None:
        return 0.0

    # The natural gap without kerning:
    # After placing prev at x=0, the next glyph starts at x=advance_width.
    # The exit point is at prev.exit_x within the glyph.
    # The entry point of next is at next.entry_x within the next glyph.
    # The actual gap = (advance_width - exit_x) + entry_x
    exit_x = prev_glyph.exit_point[0]
    entry_x = next_glyph.entry_point[0]
    natural_gap = (prev_glyph.advance_width - exit_x) + entry_x

    # Kerning: adjust so gap → target
    adjustment = _TARGET_GAP - natural_gap

    # Clamp to prevent extremes
    adjustment = max(-_MAX_KERN, min(_MAX_KERN, adjustment))

    # Ensure minimum gap is maintained
    resulting_gap = natural_gap + adjustment
    if resulting_gap < _MIN_GAP:
        adjustment = _MIN_GAP - natural_gap

    return adjustment


def kern_pair_by_id(prev_id: str, next_id: str) -> float:
    """Compute kerning for a glyph ID pair."""
    prev = GLYPH_CATALOG.get(prev_id)
    next_g = GLYPH_CATALOG.get(next_id)
    if prev is None or next_g is None:
        return 0.0
    return kern_pair(prev, next_g)


def apply_spacing_jitter(kern: float, seed: int, amplitude: float = 0.02) -> float:
    """Add small seeded jitter to kerning for organic feel.

    Args:
        kern: Base kerning value.
        seed: Deterministic seed for this pair position.
        amplitude: Maximum jitter in x-height units (default ±0.02).

    Returns:
        Kerned value with jitter.
    """
    rng = np.random.default_rng(seed)
    jitter = rng.normal(0, amplitude)
    return kern + jitter
