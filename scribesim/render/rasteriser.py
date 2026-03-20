"""Rasterise glyph layout to PNG — Python/Pillow implementation.

ADV-SS-RENDER-001 initial implementation.
Production performance path: Rust/PyO3 crate (scribesim_render) — see advance
file for the planned upgrade. This implementation is correct and deterministic;
the Rust crate will replace the inner rendering loop for speed at 300 DPI.

Outputs:
  - Page PNG: RGB, 300 DPI, parchment-tinted background with ink strokes
  - Pressure heatmap: Grayscale ("L"), same pixel dimensions, 300 DPI
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

from scribesim.hand.params import HandParams
from scribesim.layout.positioned import PageLayout
from scribesim.glyphs.catalog import GLYPH_CATALOG
from scribesim.render.bezier import sample_bezier, interpolate_pressure
from scribesim.render.nib import nib_ellipse_axes, stroke_opacity

# ---------------------------------------------------------------------------
# Resolution constants
# ---------------------------------------------------------------------------

_DPI = 300
_MM_PER_INCH = 25.4
_PX_PER_MM = _DPI / _MM_PER_INCH   # ≈ 11.811 px/mm

# Parchment background colour (warm off-white)
_PARCHMENT_RGB = (245, 238, 220)
_INK_RGB = (18, 12, 8)              # near-black sepia ink


def _mm_to_px(mm: float) -> int:
    """Convert millimetres to pixels (rounded)."""
    return round(mm * _PX_PER_MM)


def _page_size_px(layout: PageLayout) -> tuple[int, int]:
    g = layout.geometry
    return _mm_to_px(g.page_w_mm), _mm_to_px(g.page_h_mm)


# ---------------------------------------------------------------------------
# Tremor helper
# ---------------------------------------------------------------------------

def _apply_tremor(pts: list, amplitude_mm: float, seed: int) -> list:
    """Jitter sample points by seeded Gaussian noise (for fatigue simulation)."""
    if amplitude_mm <= 0:
        return pts
    rng = random.Random(seed)
    result = []
    for x, y, t in pts:
        dx = rng.gauss(0, amplitude_mm * _PX_PER_MM * 0.3)
        dy = rng.gauss(0, amplitude_mm * _PX_PER_MM * 0.3)
        result.append((x + dx, y + dy, t))
    return result


# ---------------------------------------------------------------------------
# Core stroke rendering
# ---------------------------------------------------------------------------

def _render_stroke(draw: ImageDraw.ImageDraw,
                   heat_arr,          # numpy array for heatmap accumulation
                   p0, p1, p2, p3,    # control points in mm
                   pressure_profile,
                   hand: HandParams,
                   glyph_opacity: float,
                   tremor_seed: int = 0) -> None:
    """Rasterize one cubic Bezier stroke onto *draw* and *heat_arr*."""
    import numpy as np  # local import to keep module importable without numpy

    # Convert control points mm → px
    def to_px(pt):
        return (_mm_to_px(pt[0]), _mm_to_px(pt[1]))

    pts = sample_bezier(p0, p1, p2, p3)
    pts = _apply_tremor(pts, hand.tremor_amplitude, tremor_seed)

    semi_maj, semi_min, angle = nib_ellipse_axes(
        hand.nib_width_mm, hand.nib_angle_deg, _PX_PER_MM
    )

    for x_mm, y_mm, t in pts:
        pressure = interpolate_pressure(pressure_profile, t)
        darkness = stroke_opacity(
            pressure, hand.stroke_weight,
            hand.ink_density, glyph_opacity
        )
        if darkness < 4:
            continue   # skip near-invisible stamps

        x_px = x_mm * _PX_PER_MM
        y_px = y_mm * _PX_PER_MM

        # Build rotated nib ellipse bounding box
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Approximate bounding box of the rotated ellipse
        dx = math.sqrt((semi_maj * cos_a) ** 2 + (semi_min * sin_a) ** 2)
        dy = math.sqrt((semi_maj * sin_a) ** 2 + (semi_min * cos_a) ** 2)

        bbox = [
            x_px - dx, y_px - dy,
            x_px + dx, y_px + dy,
        ]

        # Ink colour with opacity blending toward parchment
        alpha = darkness / 255.0
        r = round(_INK_RGB[0] * alpha + _PARCHMENT_RGB[0] * (1 - alpha))
        g_c = round(_INK_RGB[1] * alpha + _PARCHMENT_RGB[1] * (1 - alpha))
        b = round(_INK_RGB[2] * alpha + _PARCHMENT_RGB[2] * (1 - alpha))

        draw.ellipse(bbox, fill=(r, g_c, b))

        # Accumulate pressure heatmap
        xi, yi = int(x_px), int(y_px)
        h, w = heat_arr.shape
        if 0 <= yi < h and 0 <= xi < w:
            heat_arr[yi, xi] = min(255, int(heat_arr[yi, xi]) + darkness)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_page(layout: PageLayout, hand_params: HandParams,
                output_path: Path) -> Path:
    """Render the glyph layout to a 300 DPI page PNG.

    Args:
        layout:      PageLayout from scribesim.layout.place().
        hand_params: Resolved HandParams.
        output_path: Destination path for the PNG.

    Returns:
        output_path (Path) after writing.
    """
    import numpy as np

    w_px, h_px = _page_size_px(layout)
    img = Image.new("RGB", (w_px, h_px), _PARCHMENT_RGB)
    draw = ImageDraw.Draw(img)
    heat_arr = np.zeros((h_px, w_px), dtype=np.uint8)

    _render_layout(draw, heat_arr, layout, hand_params)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), format="PNG", dpi=(_DPI, _DPI))
    return output_path


def render_heatmap(layout: PageLayout, hand_params: HandParams,
                   output_path: Path) -> Path:
    """Render the pressure heatmap PNG (TD-001-F).

    Args:
        layout:      PageLayout from scribesim.layout.place().
        hand_params: Resolved HandParams.
        output_path: Destination path for the grayscale heatmap PNG.

    Returns:
        output_path (Path) after writing.
    """
    import numpy as np

    w_px, h_px = _page_size_px(layout)
    # Dummy draw surface (heatmap only cares about heat_arr)
    img_dummy = Image.new("RGB", (w_px, h_px), (255, 255, 255))
    draw_dummy = ImageDraw.Draw(img_dummy)
    heat_arr = np.zeros((h_px, w_px), dtype=np.uint8)

    _render_layout(draw_dummy, heat_arr, layout, hand_params)

    heat_img = Image.fromarray(heat_arr, mode="L")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    heat_img.save(str(output_path), format="PNG", dpi=(_DPI, _DPI))
    return output_path


# ---------------------------------------------------------------------------
# Internal layout traversal
# ---------------------------------------------------------------------------

def _render_layout(draw, heat_arr, layout: PageLayout, hand: HandParams) -> None:
    """Walk the PageLayout and rasterize every glyph's strokes."""
    import numpy as np

    for line_layout in layout.lines:
        for pg in line_layout.glyphs:
            glyph = GLYPH_CATALOG.get(pg.glyph_id)
            if glyph is None:
                continue

            # Glyph origin in mm: pg.x_mm, pg.baseline_y_mm
            # Glyph coordinate space: x-height units, y=0 at baseline
            x_height_mm = hand.x_height_px / (_DPI / _MM_PER_INCH)
            # Use the layout's geometry-based x_height instead
            x_height_mm = layout.geometry.ruling_pitch_mm

            for stroke in glyph.strokes:
                # Scale control points from x-height units → mm
                p0, p1, p2, p3 = (
                    (pg.x_mm + pt[0] * x_height_mm,
                     pg.baseline_y_mm - pt[1] * x_height_mm)
                    for pt in stroke.control_points
                )

                # Tremor seed: deterministic from folio_id + position
                seed = hash((layout.folio_id, pg.x_mm, pg.baseline_y_mm,
                             stroke.stroke_name)) & 0xFFFFFFFF

                _render_stroke(
                    draw, heat_arr,
                    p0, p1, p2, p3,
                    pressure_profile=stroke.pressure_profile,
                    hand=hand,
                    glyph_opacity=pg.opacity,
                    tremor_seed=seed,
                )
