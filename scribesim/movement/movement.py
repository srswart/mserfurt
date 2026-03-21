"""Multi-scale movement model — compose four scales of positional variation.

Each scale computes (dx_mm, dy_mm) offsets for each glyph. The four scales
compose additively. All randomness is seeded for determinism.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from scribesim.hand.profile import HandProfile
from scribesim.layout.positioned import PositionedGlyph, LineLayout, PageLayout


# ---------------------------------------------------------------------------
# Offset container
# ---------------------------------------------------------------------------

@dataclass
class GlyphOffset:
    """Positional offset for a single glyph (mm)."""
    dx_mm: float = 0.0
    dy_mm: float = 0.0


# ---------------------------------------------------------------------------
# Scale 1: Page Posture
# ---------------------------------------------------------------------------

def page_posture_offsets(
    layout: PageLayout,
    profile: HandProfile,
    rng: np.random.Generator,
) -> list[list[GlyphOffset]]:
    """Page-level rotation and left-margin drift.

    Rotation is modelled as an x-shear proportional to vertical distance
    from the page centre. Left margin drift accumulates linearly across
    lines with per-line Gaussian jitter.
    """
    fp = profile.folio
    page_h = layout.geometry.page_h_mm
    page_cy = page_h / 2.0

    # Page rotation as x-shear: dx = tan(angle) * (y - center)
    angle_rad = math.radians(fp.page_rotation_deg)
    shear = math.tan(angle_rad)

    # Per-line margin drift: systematic + jitter
    n_lines = len(layout.lines)
    drift_per_line = fp.margin_left_variance_mm / max(1, n_lines - 1) if n_lines > 1 else 0.0
    line_jitter = rng.normal(0, fp.margin_left_variance_mm * 0.3, size=n_lines)

    result: list[list[GlyphOffset]] = []
    for li, line_layout in enumerate(layout.lines):
        margin_dx = drift_per_line * li + line_jitter[li]
        line_offsets: list[GlyphOffset] = []
        for pg in line_layout.glyphs:
            rotation_dx = shear * (pg.baseline_y_mm - page_cy)
            line_offsets.append(GlyphOffset(
                dx_mm=rotation_dx + margin_dx,
                dy_mm=0.0,
            ))
        result.append(line_offsets)
    return result


# ---------------------------------------------------------------------------
# Scale 2: Line Trajectory
# ---------------------------------------------------------------------------

def line_trajectory_offsets(
    layout: PageLayout,
    profile: HandProfile,
    rng: np.random.Generator,
) -> list[list[GlyphOffset]]:
    """Per-line baseline undulation and start-x jitter.

    Baseline undulates sinusoidally along the line. Start-x of each line
    gets Gaussian jitter.
    """
    lp = profile.line
    text_w = layout.geometry.text_w_mm

    n_lines = len(layout.lines)
    start_x_jitter = rng.normal(0, lp.start_x_variance_mm, size=n_lines)
    # Random phase per line for undulation
    phases = rng.uniform(0, 2 * math.pi, size=n_lines)

    result: list[list[GlyphOffset]] = []
    for li, line_layout in enumerate(layout.lines):
        line_offsets: list[GlyphOffset] = []
        x_start = line_layout.glyphs[0].x_mm if line_layout.glyphs else 0.0

        for pg in line_layout.glyphs:
            # x-progress along the line [0, 1]
            x_progress = (pg.x_mm - x_start) / text_w if text_w > 0 else 0.0

            # Sinusoidal baseline undulation
            period = lp.baseline_undulation_period_ratio
            wave = math.sin(2 * math.pi * x_progress / period + phases[li])
            dy = wave * lp.baseline_undulation_amplitude_mm

            line_offsets.append(GlyphOffset(
                dx_mm=start_x_jitter[li],
                dy_mm=dy,
            ))
        result.append(line_offsets)
    return result


# ---------------------------------------------------------------------------
# Scale 3: Word Envelope
# ---------------------------------------------------------------------------

def word_envelope_offsets(
    layout: PageLayout,
    profile: HandProfile,
    rng: np.random.Generator,
) -> list[list[GlyphOffset]]:
    """Per-word baseline offset and spacing variation.

    Each word gets a small vertical baseline offset. Words are detected
    by gaps in glyph x-positions (advance > 1.5× typical).
    """
    wp = profile.word

    result: list[list[GlyphOffset]] = []
    for line_layout in layout.lines:
        glyphs = line_layout.glyphs
        if not glyphs:
            result.append([])
            continue

        # Detect word boundaries: gap between consecutive glyphs > threshold
        median_adv = np.median([g.advance_w_mm for g in glyphs]) if glyphs else 1.0
        gap_threshold = median_adv * 1.5

        # Assign word indices
        word_indices: list[int] = [0]
        for gi in range(1, len(glyphs)):
            gap = glyphs[gi].x_mm - (glyphs[gi - 1].x_mm + glyphs[gi - 1].advance_w_mm)
            if gap > gap_threshold:
                word_indices.append(word_indices[-1] + 1)
            else:
                word_indices.append(word_indices[-1])

        n_words = word_indices[-1] + 1 if word_indices else 1
        word_baseline_offsets = rng.normal(0, 0.2, size=n_words)  # ±0.2mm per TD-002

        line_offsets: list[GlyphOffset] = []
        for gi, pg in enumerate(glyphs):
            wi = word_indices[gi]
            line_offsets.append(GlyphOffset(
                dx_mm=0.0,
                dy_mm=word_baseline_offsets[wi],
            ))
        result.append(line_offsets)
    return result


# ---------------------------------------------------------------------------
# Scale 4: Glyph Trajectory
# ---------------------------------------------------------------------------

def glyph_trajectory_offsets(
    layout: PageLayout,
    profile: HandProfile,
    rng: np.random.Generator,
) -> list[list[GlyphOffset]]:
    """Per-glyph baseline jitter."""
    gp = profile.glyph

    result: list[list[GlyphOffset]] = []
    for line_layout in layout.lines:
        n = len(line_layout.glyphs)
        jitter_y = rng.normal(0, gp.baseline_jitter_mm, size=n) if n > 0 else []
        line_offsets = [
            GlyphOffset(dx_mm=0.0, dy_mm=float(jitter_y[i]))
            for i in range(n)
        ]
        result.append(line_offsets)
    return result


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------

def compose_movement(
    layout: PageLayout,
    profile: HandProfile,
    seed: int = 0,
) -> list[list[GlyphOffset]]:
    """Compute composed movement offsets from all four scales.

    Returns a nested list [line_index][glyph_index] of GlyphOffsets.
    """
    # Each scale gets its own sub-seed for independence
    rng_page = np.random.default_rng(seed)
    rng_line = np.random.default_rng(seed + 1)
    rng_word = np.random.default_rng(seed + 2)
    rng_glyph = np.random.default_rng(seed + 3)

    page_off = page_posture_offsets(layout, profile, rng_page)
    line_off = line_trajectory_offsets(layout, profile, rng_line)
    word_off = word_envelope_offsets(layout, profile, rng_word)
    glyph_off = glyph_trajectory_offsets(layout, profile, rng_glyph)

    result: list[list[GlyphOffset]] = []
    for li in range(len(layout.lines)):
        n = len(layout.lines[li].glyphs)
        line_offsets: list[GlyphOffset] = []
        for gi in range(n):
            dx = (page_off[li][gi].dx_mm + line_off[li][gi].dx_mm
                  + word_off[li][gi].dx_mm + glyph_off[li][gi].dx_mm)
            dy = (page_off[li][gi].dy_mm + line_off[li][gi].dy_mm
                  + word_off[li][gi].dy_mm + glyph_off[li][gi].dy_mm)
            line_offsets.append(GlyphOffset(dx_mm=dx, dy_mm=dy))
        result.append(line_offsets)
    return result


# ---------------------------------------------------------------------------
# Public API: apply movement to a PageLayout
# ---------------------------------------------------------------------------

def apply_movement(
    layout: PageLayout,
    profile: HandProfile,
    seed: int = 0,
) -> PageLayout:
    """Apply composed movement offsets to a PageLayout.

    Returns a new PageLayout with adjusted glyph positions. The original
    layout is not modified.
    """
    offsets = compose_movement(layout, profile, seed)

    new_lines: list[LineLayout] = []
    for li, line_layout in enumerate(layout.lines):
        new_glyphs: list[PositionedGlyph] = []
        for gi, pg in enumerate(line_layout.glyphs):
            off = offsets[li][gi]
            new_glyphs.append(PositionedGlyph(
                glyph_id=pg.glyph_id,
                x_mm=pg.x_mm + off.dx_mm,
                y_mm=pg.y_mm + off.dy_mm,
                baseline_y_mm=pg.baseline_y_mm + off.dy_mm,
                advance_w_mm=pg.advance_w_mm,
                opacity=pg.opacity,
            ))
        new_lines.append(LineLayout(
            line_index=line_layout.line_index,
            y_mm=line_layout.y_mm,
            glyphs=new_glyphs,
        ))

    moved_layout = PageLayout(
        folio_id=layout.folio_id,
        geometry=layout.geometry,
        lines=new_lines,
    )

    # Apply ruling imprecision as a final step
    from scribesim.movement.imprecision import apply_imprecision
    return apply_imprecision(moved_layout, profile, seed=seed + 10)
