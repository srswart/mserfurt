"""Render a WordGenome to an image using nib physics (TD-007 Part 4).

The nib is modelled as a flat edge swept through space. Between consecutive
sample points the swept quadrilateral is filled solid, giving crisp edges and
natural thick/thin contrast from geometry.

Hairline connections between glyphs are drawn as cubic Bézier curves whose
control points are derived from the exit/entry tangents of adjacent segments,
so the arc follows the natural pen-path rather than cutting straight across.

Supersampling (3×) then LANCZOS downsample gives smooth anti-aliased edges.
"""

from __future__ import annotations

import math
import random

import numpy as np
from PIL import Image, ImageDraw

from scribesim.evo.genome import WordGenome
from scribesim.ink.cycle import InkState, ink_darkness, ink_width_modifier, hairline_effects, post_dip_blob


_PARCHMENT = (245, 238, 220)
_INK = (18, 12, 8)
_SUPERSAMPLE = 3


def _ink_color(darkness: float) -> tuple[int, int, int]:
    d = max(0.0, min(1.0, darkness))
    return (
        int(_INK[0] * d + _PARCHMENT[0] * (1.0 - d)),
        int(_INK[1] * d + _PARCHMENT[1] * (1.0 - d)),
        int(_INK[2] * d + _PARCHMENT[2] * (1.0 - d)),
    )


def _normalize(tx: float, ty: float) -> tuple[float, float]:
    ln = math.sqrt(tx * tx + ty * ty)
    return (tx / ln, ty / ln) if ln > 1e-6 else (1.0, 0.0)


def _cubic_pt(
    p0: tuple, cp1: tuple, cp2: tuple, p3: tuple, t: float
) -> tuple[float, float]:
    u = 1.0 - t
    return (
        u**3*p0[0] + 3*u**2*t*cp1[0] + 3*u*t**2*cp2[0] + t**3*p3[0],
        u**3*p0[1] + 3*u**2*t*cp1[1] + 3*u*t**2*cp2[1] + t**3*p3[1],
    )


# ---------------------------------------------------------------------------
# Core drawing primitives
# ---------------------------------------------------------------------------

def _draw_nib_sweep(
    draw: ImageDraw.ImageDraw,
    samples: list[tuple[float, float, float]],
    hx: float,
    hy: float,
) -> None:
    """Sweep nib edge through samples, draw filled quadrilaterals."""
    for si in range(len(samples) - 1):
        x0, y0, d0 = samples[si]
        x1, y1, d1 = samples[si + 1]
        darkness = (d0 + d1) / 2.0
        if darkness < 0.05:
            continue
        color = _ink_color(darkness)
        draw.polygon([
            (x0 - hx, y0 - hy),
            (x0 + hx, y0 + hy),
            (x1 + hx, y1 + hy),
            (x1 - hx, y1 - hy),
        ], fill=color)

    # Cap stroke endpoints
    for x_px, y_px, darkness in [samples[0], samples[-1]]:
        if darkness < 0.05:
            continue
        color = _ink_color(darkness)
        draw.line(
            [(x_px - hx, y_px - hy), (x_px + hx, y_px + hy)],
            fill=color,
            width=max(1, int(abs(hy) * 0.3 + abs(hx) * 0.3)),
        )


def _draw_curved_hairline(
    draw: ImageDraw.ImageDraw,
    exit_px: tuple[float, float],
    exit_tan_px: tuple[float, float],
    entry_px: tuple[float, float],
    entry_tan_px: tuple[float, float],
    hairline_px: float,
    darkness: float = 0.75,
    n_samples: int = 28,
) -> None:
    """Draw a curved hairline Bézier connection between two points.

    Control points are set from the exit/entry tangents so the curve
    follows the natural pen path — continuing smoothly out of the
    previous stroke and arriving smoothly into the next.
    """
    if darkness < 0.05:
        return

    x0, y0 = exit_px
    x1, y1 = entry_px
    dx, dy = x1 - x0, y1 - y0
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 1.0:
        return

    color = _ink_color(darkness)

    # Scale the tangent handles to ~35% of the connection distance
    scale = dist * 0.35
    et = _normalize(*exit_tan_px)
    nt = _normalize(*entry_tan_px)

    cp1 = (x0 + et[0] * scale, y0 + et[1] * scale)
    cp2 = (x1 - nt[0] * scale, y1 - nt[1] * scale)

    prev: tuple[float, float] | None = None
    for si in range(n_samples + 1):
        t = si / n_samples
        pt = _cubic_pt((x0, y0), cp1, cp2, (x1, y1), t)
        if prev is not None:
            px0, py0 = prev
            px1, py1 = pt
            sdx, sdy = px1 - px0, py1 - py0
            slen = math.sqrt(sdx * sdx + sdy * sdy)
            if slen > 0.5:
                nx = (-sdy / slen) * (hairline_px / 2.0)
                ny = (sdx / slen) * (hairline_px / 2.0)
                draw.polygon([
                    (px0 - nx, py0 - ny),
                    (px0 + nx, py0 + ny),
                    (px1 + nx, py1 + ny),
                    (px1 - nx, py1 - ny),
                ], fill=color)
        prev = pt


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def _world_to_px(
    x_mm: float, y_mm: float,
    baseline_y: float, slant_rad: float, baseline_offset: float,
    px_per_mm: float, x_offset_px: float,
) -> tuple[float, float]:
    y_mm = y_mm + baseline_offset
    # Positive slant leans letters rightward: tops (y_mm < baseline_y) shift right.
    # y_from_baseline is negative above baseline, so negate to get rightward shift.
    y_above_baseline = baseline_y - y_mm
    x_mm = x_mm + y_above_baseline * math.tan(slant_rad)
    return x_mm * px_per_mm + x_offset_px, y_mm * px_per_mm


def _tangent_to_px(
    tx_mm: float, ty_mm: float,
    slant_rad: float, px_per_mm: float,
) -> tuple[float, float]:
    """Apply slant shear to a tangent vector, return in pixel units."""
    # Match the shear in _world_to_px: x shifts by -tan(slant) * dy
    tx_px = (tx_mm - ty_mm * math.tan(slant_rad)) * px_per_mm
    ty_px = ty_mm * px_per_mm
    return tx_px, ty_px


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_word_from_genome(
    genome: WordGenome,
    dpi: float = 100.0,
    nib_width_mm: float = 0.6,
    nib_angle_deg: float = 35.0,
    canvas_width_mm: float | None = None,
    canvas_height_mm: float | None = None,
    variation: float = 1.0,
    ink_state: InkState | None = None,
) -> np.ndarray:
    """Render a word genome to an RGB image.

    Renders at _SUPERSAMPLE× resolution then downsamples with LANCZOS for
    smooth, sharp-edged calligraphic strokes. Curved hairline connections
    are drawn between every pair of adjacent glyphs using exit/entry tangents.

    Args:
        variation: Scribal hand variation scale [0=none, 1=natural]. Applies
            per-instance jitter to pressure, nib angle, baseline, and slant so
            each render of the same genome looks subtly hand-drawn rather than
            stamped. 0.0 gives deterministic output; 1.0 matches a careful scribe.
        ink_state: Shared InkState instance tracking the reservoir across words.
            If None, a fresh InkState is created (full reservoir). Mutated in place
            as strokes are rendered — callers should call process_word_boundary()
            after each word.

    Returns:
        RGB numpy array (H, W, 3) uint8 at the requested dpi.
    """
    ss = _SUPERSAMPLE
    px_per_mm = dpi * ss / 25.4

    nib_angle_rad = math.radians(nib_angle_deg)
    half = nib_width_mm / 2.0
    hx_mm = half * math.cos(nib_angle_rad)
    hy_mm = half * math.sin(nib_angle_rad)
    hx = hx_mm * px_per_mm
    hy = hy_mm * px_per_mm

    # Hairline: ~9% of nib width at minimum
    hairline_px = max(1.5, nib_width_mm * 0.09 * px_per_mm)

    left_margin_mm = 0.6  # tight — just enough to avoid clipping slanted strokes
    if canvas_width_mm is None:
        canvas_width_mm = genome.word_width_mm + left_margin_mm + 1.2
    if canvas_height_mm is None:
        canvas_height_mm = 14.0

    w_px = max(10, int(canvas_width_mm * px_per_mm))
    h_px = max(10, int(canvas_height_mm * px_per_mm))

    img = Image.new("RGB", (w_px, h_px), _PARCHMENT)
    draw = ImageDraw.Draw(img)

    if ink_state is None:
        ink_state = InkState()
    n_samples = 80
    x_offset_px = left_margin_mm * px_per_mm

    # Collect per-glyph exit/entry points + tangents in pixel space
    glyph_exit_px: list[tuple[float, float]] = []
    glyph_exit_tan_px: list[tuple[float, float]] = []
    glyph_entry_px: list[tuple[float, float]] = []
    glyph_entry_tan_px: list[tuple[float, float]] = []

    v = variation

    # ------------------------------------------------------------ render glyphs
    for gi, glyph in enumerate(genome.glyphs):
        # Per-glyph: baseline wander ±0.12mm, slant drift ±0.8°
        glyph_baseline_jitter = random.gauss(0, 0.12 * v) if v > 0 else 0.0
        glyph_slant_jitter = random.gauss(0, 0.8 * v) if v > 0 else 0.0

        slant_deg = genome.global_slant_deg + (
            genome.slant_drift[gi] if gi < len(genome.slant_drift) else 0.0
        ) + glyph_slant_jitter
        baseline_offset = (
            genome.baseline_drift[gi] if gi < len(genome.baseline_drift) else 0.0
        ) + glyph_baseline_jitter
        slant_rad = math.radians(slant_deg)

        def to_px(x_mm, y_mm, _slant_rad=slant_rad, _baseline_offset=baseline_offset):
            return _world_to_px(
                x_mm, y_mm, genome.baseline_y, _slant_rad,
                _baseline_offset, px_per_mm, x_offset_px,
            )

        def tan_to_px(tx, ty, _slant_rad=slant_rad):
            return _tangent_to_px(tx, ty, _slant_rad, px_per_mm)

        contact_segs = [s for s in glyph.segments if s.contact]
        if not contact_segs:
            glyph_exit_px.append((0.0, 0.0))
            glyph_exit_tan_px.append((1.0, 0.0))
            glyph_entry_px.append((0.0, 0.0))
            glyph_entry_tan_px.append((1.0, 0.0))
            continue

        # Entry: first contact segment p0 and tangent(0)
        first_seg = contact_segs[0]
        ep = first_seg.evaluate(0.0)
        et = first_seg.tangent(0.0)
        glyph_entry_px.append(to_px(*ep))
        glyph_entry_tan_px.append(tan_to_px(*et))

        # Per-glyph nib angle drift ±2°
        nib_angle_drift = random.gauss(0, 2.0 * v) if v > 0 else 0.0
        seg_nib_angle_rad = math.radians(nib_angle_deg + nib_angle_drift)
        # Ink width modulation: fresh nib spreads ink wider, dry nib is narrower
        width_mod = ink_width_modifier(ink_state.reservoir)
        half_seg = nib_width_mm * width_mod / 2.0
        hx_seg = half_seg * math.cos(seg_nib_angle_rad) * px_per_mm
        hy_seg = half_seg * math.sin(seg_nib_angle_rad) * px_per_mm

        # Render all contact segments
        nib_cos = math.cos(seg_nib_angle_rad)
        nib_sin = math.sin(seg_nib_angle_rad)

        for seg_idx, seg in enumerate(contact_segs):
            # Post-dip blob: first contact stroke after a fresh dip (15% chance)
            if seg_idx == 0 and gi == 0:
                blob = post_dip_blob(ink_state.reservoir, ink_state.strokes_since_dip)
                if blob is not None:
                    p0 = seg.evaluate(0.0)
                    bx_px, by_px = to_px(p0[0], p0[1])
                    r_px = blob.radius_mm * px_per_mm
                    # Elongated ellipse aligned with stroke start tangent
                    t0 = seg.tangent(0.0)
                    t0_len = math.sqrt(t0[0] ** 2 + t0[1] ** 2)
                    if t0_len > 1e-6:
                        ta = (t0[0] / t0_len, t0[1] / t0_len)
                    else:
                        ta = (1.0, 0.0)
                    ra = r_px * blob.elongation  # semi-axis along stroke
                    rb = r_px                     # semi-axis perpendicular
                    blob_dark = min(1.0, ink_darkness(ink_state.reservoir) * (1.0 + blob.darkness_boost))
                    blob_color = _ink_color(blob_dark)
                    # Approximate ellipse as 16-gon polygon
                    import math as _math
                    n_sides = 16
                    pts = []
                    for ki in range(n_sides):
                        angle = 2 * _math.pi * ki / n_sides
                        # Local frame: along tangent (ra) and perpendicular (rb)
                        lx = ra * _math.cos(angle)
                        ly = rb * _math.sin(angle)
                        # Rotate by tangent direction
                        gx = bx_px + lx * ta[0] - ly * ta[1]
                        gy = by_px + lx * ta[1] + ly * ta[0]
                        pts.append((gx, gy))
                    draw.polygon(pts, fill=blob_color)
            samples: list[tuple[float, float, float]] = []

            # Per-segment pressure variation ±8%
            pressure_scale = 1.0 + random.gauss(0, 0.08 * v) if v > 0 else 1.0
            pressure_scale = max(0.8, min(1.15, pressure_scale))

            # Per-segment stroke wobble: small perpendicular tremor along the path
            wobble_x = 0.0
            wobble_y = 0.0
            wobble_sigma_mm = 0.015 * v  # ±0.015mm lateral tremor
            wobble_px = wobble_sigma_mm * px_per_mm

            # Hairline detection: |cross(nib_unit, stroke_unit)| < 0.25
            # Uses stroke midpoint tangent as representative direction
            mid_tan = seg.tangent(0.5)
            mid_len = math.sqrt(mid_tan[0] ** 2 + mid_tan[1] ** 2)
            if mid_len > 1e-6:
                tx_n = mid_tan[0] / mid_len
                ty_n = mid_tan[1] / mid_len
                cross_mag = abs(nib_cos * ty_n - nib_sin * tx_n)
            else:
                cross_mag = 1.0  # unknown direction — treat as full-width
            is_hairline = cross_mag < 0.25

            # Hairline effects — only non-zero near empty reservoir
            hfx = hairline_effects(ink_state.reservoir) if is_hairline else None

            # Apply width reduction to a local copy of the nib half-extents
            hx_draw = hx_seg
            hy_draw = hy_seg
            if hfx is not None and hfx.width_reduction > 0.0:
                scale_w = 1.0 - hfx.width_reduction
                hx_draw = hx_seg * scale_w
                hy_draw = hy_seg * scale_w

            # Raking: decide once per segment (split-nib effect at very low reservoir)
            is_raking = (hfx is not None
                         and hfx.raking_probability > 0.0
                         and random.random() < hfx.raking_probability)

            for si in range(n_samples + 1):
                t = si / n_samples
                pos = seg.evaluate(t)
                pressure = seg.pressure_at(t) * pressure_scale

                from scribesim.render.nib import stroke_foot_effect, stroke_attack_effect
                _, foot_i = stroke_foot_effect(t)
                _, attack_i = stroke_attack_effect(t)

                base_dark = 0.88 + 0.12 * pressure
                darkness = min(1.0, base_dark * ink_darkness(ink_state.reservoir) * foot_i * attack_i)

                x_px, y_px = to_px(pos[0], pos[1])

                if v > 0:
                    wobble_x = wobble_x * 0.85 + random.gauss(0, wobble_px * 0.4)
                    wobble_y = wobble_y * 0.85 + random.gauss(0, wobble_px * 0.15)
                    x_px += wobble_x
                    y_px += wobble_y

                samples.append((x_px, y_px, darkness))

            if is_raking and len(samples) >= 2:
                # Split-nib: draw two parallel thin lines offset perpendicular to stroke
                # Compute average stroke direction for offset vector
                x0s, y0s, _ = samples[0]
                xes, yes, _ = samples[-1]
                sdx, sdy = xes - x0s, yes - y0s
                slen = math.sqrt(sdx * sdx + sdy * sdy)
                if slen > 1.0:
                    # Perpendicular unit vector
                    px_n = -sdy / slen
                    py_n = sdx / slen
                    # Offset = 20% of full nib width in pixels
                    offset_px = max(0.5, nib_width_mm * 0.20 * px_per_mm / _SUPERSAMPLE)
                    rake_dark = 0.70  # split nib deposits less ink per rail
                    hx_rake = hx_draw * 0.5
                    hy_rake = hy_draw * 0.5
                    for sign in (-1.0, 1.0):
                        offset_samples = [
                            (x + sign * px_n * offset_px,
                             y + sign * py_n * offset_px,
                             d * rake_dark)
                            for x, y, d in samples
                        ]
                        _draw_nib_sweep(draw, offset_samples, hx_rake, hy_rake)
            else:
                # Normal draw — with per-sample gap smoothing for hairlines
                if hfx is not None and hfx.gap_probability > 0.0:
                    gap_active = False
                    gap_prob = hfx.gap_probability
                    filtered: list[tuple[float, float, float]] = []
                    run: list[tuple[float, float, float]] = []
                    for pt in samples:
                        if gap_active:
                            # Exit gap if random > 2× gap_prob (creates runs)
                            if random.random() > gap_prob * 2.0:
                                gap_active = False
                        else:
                            if random.random() < gap_prob:
                                gap_active = True
                        if gap_active:
                            # Flush accumulated run, start new run
                            if len(run) >= 2:
                                _draw_nib_sweep(draw, run, hx_draw, hy_draw)
                            run = []
                        else:
                            run.append(pt)
                    if len(run) >= 2:
                        _draw_nib_sweep(draw, run, hx_draw, hy_draw)
                else:
                    _draw_nib_sweep(draw, samples, hx_draw, hy_draw)

            ink_state.deplete_for_stroke(seg.length(), 0.85, nib_width_mm)

        # Exit: last contact segment p3 and tangent(1)
        last_seg = contact_segs[-1]
        xp = last_seg.evaluate(1.0)
        xt = last_seg.tangent(1.0)
        glyph_exit_px.append(to_px(*xp))
        glyph_exit_tan_px.append(tan_to_px(*xt))

    # ------------------------------------------------- curved hairline connections
    for i in range(len(genome.glyphs) - 1):
        if i >= len(glyph_exit_px) or (i + 1) >= len(glyph_entry_px):
            continue
        _draw_curved_hairline(
            draw,
            exit_px=glyph_exit_px[i],
            exit_tan_px=glyph_exit_tan_px[i],
            entry_px=glyph_entry_px[i + 1],
            entry_tan_px=glyph_entry_tan_px[i + 1],
            hairline_px=hairline_px,
            darkness=0.72,
        )

    # ----------------------------------------- downsample to target resolution
    out_w = max(1, w_px // ss)
    out_h = max(1, h_px // ss)
    img = img.resize((out_w, out_h), Image.LANCZOS)
    return np.array(img)


def render_genome_to_file(genome: WordGenome, output_path: str, **kwargs) -> str:
    """Render and save to a PNG file."""
    from pathlib import Path
    arr = render_word_from_genome(genome, **kwargs)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr, "RGB").save(str(out), format="PNG")
    return str(out)
