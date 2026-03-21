"""Generate cursive connection strokes between glyphs within words.

A connection stroke is a hairline Bezier curve arcing upward from the
exit point of one glyph to the entry point of the next. The arc height
is parameterized by connection_lift_height_mm.
"""

from __future__ import annotations

from scribesim.glyphs.catalog import GLYPH_CATALOG
from scribesim.layout.positioned import (
    PositionedGlyph, LineLayout, ConnectionStroke,
)


def generate_connection(
    prev_pg: PositionedGlyph,
    next_pg: PositionedGlyph,
    x_height_mm: float,
    lift_height_mm: float = 0.8,
) -> ConnectionStroke | None:
    """Generate a connection stroke between two positioned glyphs.

    Args:
        prev_pg: The previous glyph (source of exit point).
        next_pg: The next glyph (source of entry point).
        x_height_mm: Physical x-height for coordinate scaling.
        lift_height_mm: How high the arc rises above the baseline (mm).

    Returns:
        A ConnectionStroke, or None if glyphs can't be connected.
    """
    prev_glyph = GLYPH_CATALOG.get(prev_pg.glyph_id)
    next_glyph = GLYPH_CATALOG.get(next_pg.glyph_id)
    if prev_glyph is None or next_glyph is None:
        return None
    if prev_glyph.exit_point is None or next_glyph.entry_point is None:
        return None

    # Exit point in page mm coordinates
    exit_x = prev_pg.x_mm + prev_glyph.exit_point[0] * x_height_mm
    exit_y = prev_pg.baseline_y_mm - prev_glyph.exit_point[1] * x_height_mm

    # Entry point in page mm coordinates
    entry_x = next_pg.x_mm + next_glyph.entry_point[0] * x_height_mm
    entry_y = next_pg.baseline_y_mm - next_glyph.entry_point[1] * x_height_mm

    # Arc: control points rise above the midpoint
    mid_x = (exit_x + entry_x) / 2.0
    mid_y = min(exit_y, entry_y) - lift_height_mm  # rise above

    # P1: 1/3 of the way, lifted
    p1_x = exit_x + (entry_x - exit_x) * 0.33
    p1_y = exit_y - lift_height_mm * 0.7

    # P2: 2/3 of the way, lifted
    p2_x = exit_x + (entry_x - exit_x) * 0.67
    p2_y = entry_y - lift_height_mm * 0.7

    return ConnectionStroke(
        p0=(exit_x, exit_y),
        p1=(p1_x, p1_y),
        p2=(p2_x, p2_y),
        p3=(entry_x, entry_y),
    )


def add_connections_to_line(
    line: LineLayout,
    x_height_mm: float,
    lift_height_mm: float = 0.8,
) -> LineLayout:
    """Add connection strokes between consecutive glyphs within words.

    Detects word boundaries by gaps larger than 1.5× median advance.
    Returns a new LineLayout with connections populated.
    """
    glyphs = line.glyphs
    if len(glyphs) < 2:
        return line

    # Detect word boundaries
    import numpy as np
    advances = [g.advance_w_mm for g in glyphs]
    median_adv = float(np.median(advances)) if advances else 1.0
    gap_threshold = median_adv * 1.5

    connections = []
    for i in range(len(glyphs) - 1):
        prev = glyphs[i]
        nxt = glyphs[i + 1]

        # Check if this is a word boundary (large gap = pen lift)
        gap = nxt.x_mm - (prev.x_mm + prev.advance_w_mm)
        if gap > gap_threshold:
            continue  # pen lifts at word boundary

        conn = generate_connection(prev, nxt, x_height_mm, lift_height_mm)
        if conn is not None:
            connections.append(conn)

    return LineLayout(
        line_index=line.line_index,
        y_mm=line.y_mm,
        glyphs=line.glyphs,
        connections=connections,
    )
