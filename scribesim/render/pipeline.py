"""Rendering Pipeline v2 — 6-stage unified entry point (TD-002 Part 5).

Stages:
  1. GEOMETRY   — layout + movement + imprecision (already done by placer)
  2. RENDERING  — rasterise at 400 DPI internal resolution
  3. INK FILTERS — saturation, pooling, wicking, feathering, depletion
  4. COMPOSITING — downsample 400→300 DPI (Lanczos)
  5. GROUND TRUTH — PAGE XML from Stage 1 geometry (300 DPI coordinates)
  6. HEATMAP    — pressure heatmap, downsampled to 300 DPI
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scribesim.hand.params import HandParams
from scribesim.hand.profile import HandProfile
from scribesim.layout.positioned import PageLayout
from scribesim.glyphs.catalog import GLYPH_CATALOG
from scribesim.render.bezier import sample_bezier, interpolate_pressure
from scribesim.render.nib import PhysicsNib, mark_width, stroke_direction, stroke_opacity
from scribesim.render.rasteriser import _apply_tremor, _PARCHMENT_RGB, _INK_RGB, _MM_PER_INCH

import math

# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

_INTERNAL_DPI = 400
_OUTPUT_DPI = 300
_SCALE = _INTERNAL_DPI / _OUTPUT_DPI  # 4/3 ≈ 1.333
_INT_PX_PER_MM = _INTERNAL_DPI / _MM_PER_INCH  # ≈ 15.748


def _page_size_internal(layout: PageLayout) -> tuple[int, int]:
    g = layout.geometry
    return (round(g.page_w_mm * _INT_PX_PER_MM),
            round(g.page_h_mm * _INT_PX_PER_MM))


def _page_size_output(layout: PageLayout) -> tuple[int, int]:
    g = layout.geometry
    px_per_mm = _OUTPUT_DPI / _MM_PER_INCH
    return (round(g.page_w_mm * px_per_mm),
            round(g.page_h_mm * px_per_mm))


# ---------------------------------------------------------------------------
# Stage 2: Raw rendering at 400 DPI
# ---------------------------------------------------------------------------

def _render_at_internal_dpi(layout: PageLayout, hand: HandParams
                            ) -> tuple[Image.Image, np.ndarray]:
    """Render page at 400 DPI internal resolution.

    Returns (img, heat_arr) at internal resolution.
    """
    w_px, h_px = _page_size_internal(layout)
    img = Image.new("RGB", (w_px, h_px), _PARCHMENT_RGB)
    draw = ImageDraw.Draw(img)
    heat_arr = np.zeros((h_px, w_px), dtype=np.uint8)

    pnib = PhysicsNib(
        width_mm=hand.nib_width_mm,
        angle_deg=hand.nib_angle_deg,
    )
    nib_angle_rad = math.radians(hand.nib_angle_deg)

    for line_layout in layout.lines:
        for pg in line_layout.glyphs:
            glyph = GLYPH_CATALOG.get(pg.glyph_id)
            if glyph is None:
                continue

            x_height_mm = layout.geometry.x_height_mm

            for stroke in glyph.strokes:
                p0, p1, p2, p3 = (
                    (pg.x_mm + pt[0] * x_height_mm,
                     pg.baseline_y_mm - pt[1] * x_height_mm)
                    for pt in stroke.control_points
                )

                seed = hash((layout.folio_id, pg.x_mm, pg.baseline_y_mm,
                             stroke.stroke_name)) & 0xFFFFFFFF

                pts = sample_bezier(p0, p1, p2, p3)
                pts = _apply_tremor(pts, hand.tremor_amplitude, seed)

                for i, (x_mm, y_mm, t) in enumerate(pts):
                    pressure = interpolate_pressure(stroke.pressure_profile, t)
                    darkness = stroke_opacity(
                        pressure, hand.stroke_weight,
                        hand.ink_density, pg.opacity
                    )
                    if darkness < 4:
                        continue

                    x_px = x_mm * _INT_PX_PER_MM
                    y_px = y_mm * _INT_PX_PER_MM

                    direction = stroke_direction(pts, i)
                    width_mm = mark_width(pnib, direction, pressure, t)
                    semi_maj = max(1, round(width_mm * 0.5 * _INT_PX_PER_MM))
                    semi_min = max(1, round(width_mm * 0.125 * _INT_PX_PER_MM))

                    cos_a = math.cos(nib_angle_rad)
                    sin_a = math.sin(nib_angle_rad)
                    dx = math.sqrt((semi_maj * cos_a) ** 2 + (semi_min * sin_a) ** 2)
                    dy = math.sqrt((semi_maj * sin_a) ** 2 + (semi_min * cos_a) ** 2)

                    bbox = [x_px - dx, y_px - dy, x_px + dx, y_px + dy]

                    alpha = darkness / 255.0
                    r = round(_INK_RGB[0] * alpha + _PARCHMENT_RGB[0] * (1 - alpha))
                    g_c = round(_INK_RGB[1] * alpha + _PARCHMENT_RGB[1] * (1 - alpha))
                    b = round(_INK_RGB[2] * alpha + _PARCHMENT_RGB[2] * (1 - alpha))

                    draw.ellipse(bbox, fill=(r, g_c, b))

                    xi, yi = int(x_px), int(y_px)
                    if 0 <= yi < h_px and 0 <= xi < w_px:
                        heat_arr[yi, xi] = min(255, int(heat_arr[yi, xi]) + darkness)

        # Render connection strokes (hairline upstrokes between glyphs)
        for conn in getattr(line_layout, 'connections', []):
            pts = sample_bezier(conn.p0, conn.p1, conn.p2, conn.p3)

            for i, (x_mm, y_mm, t) in enumerate(pts):
                pressure = interpolate_pressure(conn.pressure, t)
                darkness = stroke_opacity(pressure, hand.stroke_weight,
                                          hand.ink_density, 1.0)
                if darkness < 4:
                    continue

                x_px = x_mm * _INT_PX_PER_MM
                y_px = y_mm * _INT_PX_PER_MM

                direction = stroke_direction(pts, i)
                width_mm_val = mark_width(pnib, direction, pressure, t)
                semi_maj = max(1, round(width_mm_val * 0.5 * _INT_PX_PER_MM))
                semi_min = max(1, round(width_mm_val * 0.125 * _INT_PX_PER_MM))

                cos_a = math.cos(nib_angle_rad)
                sin_a = math.sin(nib_angle_rad)
                dx = math.sqrt((semi_maj * cos_a) ** 2 + (semi_min * sin_a) ** 2)
                dy = math.sqrt((semi_maj * sin_a) ** 2 + (semi_min * cos_a) ** 2)

                bbox = [x_px - dx, y_px - dy, x_px + dx, y_px + dy]

                alpha = darkness / 255.0
                r = round(_INK_RGB[0] * alpha + _PARCHMENT_RGB[0] * (1 - alpha))
                g_c = round(_INK_RGB[1] * alpha + _PARCHMENT_RGB[1] * (1 - alpha))
                b = round(_INK_RGB[2] * alpha + _PARCHMENT_RGB[2] * (1 - alpha))

                draw.ellipse(bbox, fill=(r, g_c, b))

                xi, yi = int(x_px), int(y_px)
                if 0 <= yi < h_px and 0 <= xi < w_px:
                    heat_arr[yi, xi] = min(255, int(heat_arr[yi, xi]) + darkness)

    return img, heat_arr


# ---------------------------------------------------------------------------
# Stage 4: Downsample 400→300 DPI
# ---------------------------------------------------------------------------

def _downsample(img: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    """Downsample with Lanczos for anti-aliased output."""
    return img.resize(target_size, Image.LANCZOS)


def _downsample_array(arr: np.ndarray, target_size: tuple[int, int]) -> np.ndarray:
    """Downsample a 2D array via PIL for consistent quality."""
    img = Image.fromarray(arr, mode="L")
    resized = img.resize(target_size, Image.LANCZOS)
    return np.array(resized)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_pipeline(
    layout: PageLayout,
    hand_params: HandParams,
    output_dir: Path,
    folio_id: str,
    profile: HandProfile | None = None,
) -> tuple[Path, Path]:
    """Execute the 6-stage rendering pipeline.

    Args:
        layout:      PageLayout (Stage 1 output — geometry already resolved).
        hand_params: Resolved HandParams (v1 compat).
        output_dir:  Directory for output files.
        folio_id:    Folio identifier for filenames.
        profile:     HandProfile for ink filters. If None, filters are skipped.

    Returns:
        (page_path, heatmap_path) — paths to the output PNG files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    out_size = _page_size_output(layout)

    # Stage 2: Raw rendering at 400 DPI
    img_internal, heat_internal = _render_at_internal_dpi(layout, hand_params)

    # Stage 3: Ink-substrate filters (at 400 DPI for maximum quality)
    if profile is not None:
        from scribesim.ink import apply_ink_filters
        img_arr = np.array(img_internal)
        img_arr = apply_ink_filters(img_arr, heat_internal, layout, profile)
        img_internal = Image.fromarray(img_arr, "RGB")

    # Stage 4: Downsample 400→300 DPI
    img_output = _downsample(img_internal, out_size)

    # Stage 6: Heatmap downsample
    heat_output = _downsample_array(heat_internal, out_size)

    # Save outputs
    page_path = output_dir / f"{folio_id}.png"
    img_output.save(str(page_path), format="PNG", dpi=(_OUTPUT_DPI, _OUTPUT_DPI))

    heatmap_path = output_dir / f"{folio_id}_pressure.png"
    heat_img = Image.fromarray(heat_output, mode="L")
    heat_img.save(str(heatmap_path), format="PNG", dpi=(_OUTPUT_DPI, _OUTPUT_DPI))

    return page_path, heatmap_path
