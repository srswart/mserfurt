"""Render a WordGenome to an image using nib physics (TD-007 Part 4).

The genome provides the paths. The nib-angle width equation, stroke
foot/attack, and ink depletion from TD-002/004 render those paths as marks.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from scribesim.evo.genome import WordGenome, BezierSegment
from scribesim.render.nib import PhysicsNib, mark_width, stroke_foot_effect, stroke_attack_effect


_PARCHMENT = (245, 238, 220)
_INK = (18, 12, 8)


def render_word_from_genome(
    genome: WordGenome,
    dpi: float = 100.0,
    nib_width_mm: float = 0.6,
    nib_angle_deg: float = 35.0,
    canvas_width_mm: float | None = None,
    canvas_height_mm: float | None = None,
) -> np.ndarray:
    """Render a word genome to an RGB image.

    Args:
        genome: The word genome to render.
        dpi: Rendering resolution (72-100 for evolution, 300+ for final).
        nib_width_mm: Nib width for mark-making.
        nib_angle_deg: Nib angle for thick/thin.
        canvas_width_mm: Canvas width (auto-sized if None).
        canvas_height_mm: Canvas height (auto-sized if None).

    Returns:
        RGB numpy array (H, W, 3) uint8.
    """
    px_per_mm = dpi / 25.4
    nib = PhysicsNib(width_mm=nib_width_mm, angle_deg=nib_angle_deg)

    # Auto-size canvas
    if canvas_width_mm is None:
        canvas_width_mm = genome.word_width_mm + 4.0
    if canvas_height_mm is None:
        canvas_height_mm = 12.0  # enough for ascenders + descenders

    w_px = max(10, int(canvas_width_mm * px_per_mm))
    h_px = max(10, int(canvas_height_mm * px_per_mm))

    img = Image.new("RGB", (w_px, h_px), _PARCHMENT)
    draw = ImageDraw.Draw(img)

    ink_reservoir = genome.ink_state_start
    n_samples = 30  # samples per segment

    for gi, glyph in enumerate(genome.glyphs):
        slant_deg = genome.global_slant_deg
        if gi < len(genome.slant_drift):
            slant_deg += genome.slant_drift[gi]
        baseline_offset = 0.0
        if gi < len(genome.baseline_drift):
            baseline_offset = genome.baseline_drift[gi]

        slant_rad = math.radians(slant_deg)

        for seg in glyph.segments:
            if not seg.contact:
                continue

            for si in range(n_samples + 1):
                t = si / n_samples

                # Position on curve
                pos = seg.evaluate(t)
                x_mm = pos[0]
                y_mm = pos[1] + baseline_offset

                # Apply slant (shear x by slant angle × y distance from baseline)
                y_from_baseline = y_mm - genome.baseline_y
                x_mm += y_from_baseline * math.tan(slant_rad)

                # Stroke direction
                direction = seg.direction_deg(t)

                # Pressure from genome
                pressure = seg.pressure_at(t)

                # Mark width from nib physics
                width = mark_width(nib, direction, pressure, t)

                # Foot/attack effects
                foot_w, foot_i = stroke_foot_effect(t)
                attack_w, attack_i = stroke_attack_effect(t)
                width *= foot_w * attack_w

                # Ink deposit
                speed = seg.speed_at(t)
                darkness = min(1.0, pressure * 0.9 * ink_reservoir * foot_i * attack_i)

                if darkness < 0.05:
                    continue

                # Rasterize
                x_px = x_mm * px_per_mm
                y_px = y_mm * px_per_mm
                r = max(0.3, width * 0.5 * px_per_mm * 0.4)

                ink_r = int(_INK[0] * darkness + _PARCHMENT[0] * (1 - darkness))
                ink_g = int(_INK[1] * darkness + _PARCHMENT[1] * (1 - darkness))
                ink_b = int(_INK[2] * darkness + _PARCHMENT[2] * (1 - darkness))

                bbox = [x_px - r, y_px - r, x_px + r, y_px + r]
                draw.ellipse(bbox, fill=(ink_r, ink_g, ink_b))

            # Deplete ink
            ink_reservoir = max(0.0, ink_reservoir - 0.002 * seg.length())

    return np.array(img)


def render_genome_to_file(genome: WordGenome, output_path: str, **kwargs) -> str:
    """Render and save to a PNG file."""
    from pathlib import Path
    arr = render_word_from_genome(genome, **kwargs)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr, "RGB").save(str(out), format="PNG")
    return str(out)
