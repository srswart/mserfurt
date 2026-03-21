"""Cumulative imprecision model (TD-002 Part 4).

Ruling lines on real vellum are not perfectly spaced or perfectly
horizontal. This module adds structured imprecision to ruling line
positions, producing subtle inter-line spacing variation that makes
the page look hand-ruled rather than machine-ruled.

Distinct from the movement model (which simulates the scribe's hand),
imprecision simulates the physical page preparation.
"""

from __future__ import annotations

import numpy as np

from scribesim.hand.profile import HandProfile
from scribesim.layout.positioned import PositionedGlyph, LineLayout, PageLayout


def ruling_imprecision(
    n_lines: int,
    profile: HandProfile,
    seed: int = 0,
) -> list[float]:
    """Compute per-line ruling y-offsets (mm).

    Each ruling line gets a small y-offset representing imprecision in
    the dry-point ruling process. The offsets accumulate slightly
    (earlier jitter affects all subsequent lines).

    Args:
        n_lines: Number of text lines on the page.
        profile: HandProfile with folio.ruling_spacing_variance_mm
                 and line.line_spacing_variance_mm.
        seed: RNG seed for determinism.

    Returns:
        List of n_lines y-offsets in mm (positive = lower on page).
    """
    rng = np.random.default_rng(seed)
    fp = profile.folio
    lp = profile.line

    # Per-line ruling position jitter
    ruling_jitter = rng.normal(0, fp.ruling_spacing_variance_mm * 0.5, size=n_lines)

    # Inter-line spacing variation: cumulative drift
    spacing_jitter = rng.normal(0, lp.line_spacing_variance_mm * 0.3, size=n_lines)
    cumulative = np.cumsum(spacing_jitter)

    # Combine: each line's offset is its own ruling jitter + accumulated spacing drift
    offsets = ruling_jitter + cumulative

    return offsets.tolist()


def apply_imprecision(
    layout: PageLayout,
    profile: HandProfile,
    seed: int = 0,
) -> PageLayout:
    """Apply ruling imprecision offsets to a PageLayout.

    Shifts each line's glyphs vertically by the ruling imprecision offset.
    Returns a new PageLayout; the original is not modified.
    """
    n_lines = len(layout.lines)
    if n_lines == 0:
        return layout

    offsets = ruling_imprecision(n_lines, profile, seed)

    new_lines: list[LineLayout] = []
    for li, line_layout in enumerate(layout.lines):
        dy = offsets[li]
        new_glyphs = []
        for pg in line_layout.glyphs:
            new_glyphs.append(PositionedGlyph(
                glyph_id=pg.glyph_id,
                x_mm=pg.x_mm,
                y_mm=pg.y_mm + dy,
                baseline_y_mm=pg.baseline_y_mm + dy,
                advance_w_mm=pg.advance_w_mm,
                opacity=pg.opacity,
            ))
        new_lines.append(LineLayout(
            line_index=line_layout.line_index,
            y_mm=line_layout.y_mm + dy,
            glyphs=new_glyphs,
        ))

    return PageLayout(
        folio_id=layout.folio_id,
        geometry=layout.geometry,
        lines=new_lines,
    )
