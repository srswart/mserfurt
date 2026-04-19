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
from scribesim.render.bezier import sample_bezier, interpolate_pressure
from scribesim.render.rasteriser import _apply_tremor, _PARCHMENT_RGB, _INK_RGB, _MM_PER_INCH
from scribesim.render.scribe_state import ScribeStateUpdater

import math

# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

_INTERNAL_DPI = 800
_OUTPUT_DPI = 600
_SCALE = _INTERNAL_DPI / _OUTPUT_DPI  # 4/3 ≈ 1.333
_INT_PX_PER_MM = _INTERNAL_DPI / _MM_PER_INCH  # ≈ 31.496


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
# Nib geometry helpers (TD-015)
# ---------------------------------------------------------------------------

def _nib_half_vec(
    nib_angle_deg: float, nib_width_mm: float, px_per_mm: float
) -> tuple[float, float]:
    """Compute nib edge half-vector in pixels.

    The nib is a line segment of length nib_width_mm at nib_angle_deg from
    horizontal. This returns the half-vector (hx, hy) so that the two ends
    of the nib edge are at (x ± hx, y ± hy) for a pen position (x, y).
    """
    half_mm = nib_width_mm / 2.0
    rad = math.radians(nib_angle_deg)
    return half_mm * math.cos(rad) * px_per_mm, half_mm * math.sin(rad) * px_per_mm


def _ink_color(alpha: float) -> tuple[int, int, int]:
    """Blend ink toward parchment background at the given alpha [0, 1]."""
    a = max(0.0, min(1.0, alpha))
    return (
        round(_INK_RGB[0] * a + _PARCHMENT_RGB[0] * (1.0 - a)),
        round(_INK_RGB[1] * a + _PARCHMENT_RGB[1] * (1.0 - a)),
        round(_INK_RGB[2] * a + _PARCHMENT_RGB[2] * (1.0 - a)),
    )


def _local_nib_half_vec(
    dx_px: float,
    dy_px: float,
    base_angle_deg: float,
    nib_width_mm: float,
    px_per_mm: float,
    coupling: float,
) -> tuple[float, float]:
    """Compute per-segment nib half-vector with direction coupling.

    At coupling=0, returns the fixed nib half-vector for base_angle_deg.
    At coupling=1, the nib angle fully tracks the stroke direction.
    At coupling=0.25, the nib angle is pulled 25% toward the stroke direction.

    A broad-edged nib is thickest when the stroke is perpendicular to the nib
    edge; coupling makes this happen naturally as the stroke changes direction.
    """
    if coupling > 0.0 and (dx_px != 0.0 or dy_px != 0.0):
        stroke_angle_deg = math.degrees(math.atan2(dy_px, dx_px))
        effective_angle_deg = base_angle_deg + coupling * stroke_angle_deg
    else:
        effective_angle_deg = base_angle_deg
    return _nib_half_vec(effective_angle_deg, nib_width_mm, px_per_mm)


def _polygon_sweep_stroke(
    draw: ImageDraw.ImageDraw,
    pts: list[tuple[float, float, float]],
    hx: float,
    hy: float,
    px_per_mm: float,
    pressure_profile: tuple,
    stroke_weight: float,
    ink_density: float,
    glyph_opacity: float,
    heat_arr,
    img_h: int,
    img_w: int,
    nib_angle_deg: float | None = None,
    nib_width_mm: float | None = None,
    nib_coupling: float = 0.0,
) -> None:
    """Sweep the nib edge through sample points as filled polygon quads.

    Each pair of consecutive sample points defines a quadrilateral whose
    corners are offset by the nib edge half-vector in pixels. When
    nib_coupling > 0, the nib angle is pulled toward the local stroke
    direction, producing natural calligraphic thick/thin variation:
    strokes crossing the nib edge are thick, strokes parallel are thin.

    Darkness per quad = average of the endpoint pressure values, multiplied
    by stroke_weight × ink_density × glyph_opacity. Skip quads with
    effective darkness < 0.01 (truly invisible).
    """
    use_coupling = nib_coupling > 0.0 and nib_angle_deg is not None and nib_width_mm is not None

    prev_x_px: float | None = None
    prev_y_px: float | None = None
    prev_dark: float | None = None
    prev_hx: float = hx
    prev_hy: float = hy

    for x_mm, y_mm, t in pts:
        x_px = x_mm * px_per_mm
        y_px = y_mm * px_per_mm
        pressure = interpolate_pressure(pressure_profile, t)
        dark = max(0.0, min(1.0, pressure * stroke_weight * min(1.0, ink_density) * glyph_opacity))

        if prev_x_px is not None and prev_dark is not None:
            avg_dark = (prev_dark + dark) / 2.0
            if avg_dark >= 0.01:
                # Recompute nib half-vector for this segment if coupling is active
                if use_coupling:
                    seg_hx, seg_hy = _local_nib_half_vec(
                        x_px - prev_x_px, y_px - prev_y_px,
                        nib_angle_deg, nib_width_mm, px_per_mm, nib_coupling,
                    )
                else:
                    seg_hx, seg_hy = hx, hy

                color = _ink_color(avg_dark)
                quad = [
                    (prev_x_px - prev_hx, prev_y_px - prev_hy),
                    (prev_x_px + prev_hx, prev_y_px + prev_hy),
                    (x_px + seg_hx,       y_px + seg_hy),
                    (x_px - seg_hx,       y_px - seg_hy),
                ]
                draw.polygon(quad, fill=color)

                xi = int((prev_x_px + x_px) / 2)
                yi = int((prev_y_px + y_px) / 2)
                if 0 <= yi < img_h and 0 <= xi < img_w:
                    heat_val = min(255, int(avg_dark * 255))
                    heat_arr[yi, xi] = min(255, int(heat_arr[yi, xi]) + heat_val)

                prev_hx, prev_hy = seg_hx, seg_hy
            else:
                prev_hx, prev_hy = hx, hy
        else:
            prev_hx, prev_hy = hx, hy

        prev_x_px, prev_y_px, prev_dark = x_px, y_px, dark

    # End caps: short line at the nib angle sealing each stroke terminus
    if pts:
        cap_hx, cap_hy = hx, hy
        for (x_mm, y_mm, t) in (pts[0], pts[-1]):
            x_px = x_mm * px_per_mm
            y_px = y_mm * px_per_mm
            pressure = interpolate_pressure(pressure_profile, t)
            dark = max(0.0, min(1.0,
                pressure * stroke_weight * min(1.0, ink_density) * glyph_opacity))
            if dark >= 0.05:
                color = _ink_color(dark)
                cap_w = max(1, round(math.hypot(cap_hx, cap_hy) * 0.4))
                draw.line(
                    [(x_px - cap_hx, y_px - cap_hy), (x_px + cap_hx, y_px + cap_hy)],
                    fill=color, width=cap_w,
                )


# ---------------------------------------------------------------------------
# Stage 2: Raw rendering at 400 DPI
# ---------------------------------------------------------------------------

def _count_words(glyphs: list, x_height_mm: float) -> int:
    """Count words in a glyph list by detecting inter-word gaps."""
    if not glyphs:
        return 0
    words = 1
    threshold = x_height_mm * 0.3
    for i in range(len(glyphs) - 1):
        gap = glyphs[i + 1].x_mm - (glyphs[i].x_mm + glyphs[i].advance_w_mm)
        if gap > threshold:
            words += 1
    return words


def _render_at_internal_dpi(layout: PageLayout, hand: HandParams
                            ) -> tuple[Image.Image, np.ndarray]:
    """Render page at 400 DPI internal resolution using polygon sweep (TD-015).

    Applies ScribeState (TD-017) for temporally coherent variation:
    ink depletion, fatigue-driven nib angle drift, and per-glyph motor memory.

    Returns (img, heat_arr) at internal resolution.
    """
    w_px, h_px = _page_size_internal(layout)
    img = Image.new("RGB", (w_px, h_px), _PARCHMENT_RGB)
    draw = ImageDraw.Draw(img)
    heat_arr = np.zeros((h_px, w_px), dtype=np.uint8)

    x_height_mm = layout.geometry.x_height_mm
    hairline_width_mm = hand.nib_width_mm * 0.065

    # Initialise scribe state for this folio
    updater = ScribeStateUpdater(
        folio_id=layout.folio_id,
        fatigue_rate=hand.fatigue_rate if hand.fatigue_rate > 0 else 0.025,
    )

    for li, line_layout in enumerate(layout.lines):
        n_words = _count_words(line_layout.glyphs, x_height_mm)
        updater.advance_line(li, n_words)
        state = updater.state

        # Per-line nib parameters (angle drifts with fatigue)
        angle_deg = hand.nib_angle_deg + state.nib_angle_drift_deg(li)
        hx, hy = _nib_half_vec(angle_deg, hand.nib_width_mm, _INT_PX_PER_MM)
        hx_hair, hy_hair = _nib_half_vec(angle_deg, hairline_width_mm, _INT_PX_PER_MM)

        # Baseline sag from fatigue (added to y coordinates)
        baseline_sag_mm = state.baseline_drift_mm(li)

        # Effective ink density scaled by current reservoir and intensity
        effective_density = min(1.0, hand.ink_density * state.darkness_scale())

        for pg in line_layout.glyphs:
            glyph = GLYPH_CATALOG.get(pg.glyph_id)
            if glyph is None:
                continue

            updater.ensure_glyph(pg.glyph_id)
            mdx, mdy = state.motor_offset(pg.glyph_id)

            for stroke in glyph.strokes:
                # Apply motor memory to interior control points (P1, P2);
                # endpoints (P0, P3) are only lightly offset to preserve joins.
                pts_raw = stroke.control_points
                offsets = [(mdx * 0.3, mdy * 0.3),   # P0: light
                           (mdx,        mdy),          # P1: full
                           (mdx,        mdy),          # P2: full
                           (mdx * 0.3, mdy * 0.3)]    # P3: light
                p0, p1, p2, p3 = (
                    (pg.x_mm + (pt[0] + off[0]) * x_height_mm,
                     pg.baseline_y_mm + baseline_sag_mm - (pt[1] + off[1]) * x_height_mm)
                    for pt, off in zip(pts_raw, offsets)
                )

                seed = hash((layout.folio_id, pg.x_mm, pg.baseline_y_mm,
                             stroke.stroke_name)) & 0xFFFFFFFF

                pts = sample_bezier(p0, p1, p2, p3)
                pts = _apply_tremor(pts, hand.tremor_amplitude, seed)

                _polygon_sweep_stroke(
                    draw, pts, hx, hy, _INT_PX_PER_MM,
                    stroke.pressure_profile,
                    hand.stroke_weight, effective_density, pg.opacity,
                    heat_arr, h_px, w_px,
                    nib_angle_deg=angle_deg,
                    nib_width_mm=hand.nib_width_mm,
                    nib_coupling=hand.nib_coupling,
                )

        # Connection strokes use the same per-line nib angle and ink density
        for conn in getattr(line_layout, 'connections', []):
            pts = sample_bezier(conn.p0, conn.p1, conn.p2, conn.p3)
            _polygon_sweep_stroke(
                draw, pts, hx_hair, hy_hair, _INT_PX_PER_MM,
                conn.pressure,
                hand.stroke_weight, effective_density, 1.0,
                heat_arr, h_px, w_px,
            )

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
