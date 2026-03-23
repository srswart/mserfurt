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
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageDraw

from scribesim.evo.genome import WordGenome
from scribesim.ink.cycle import InkState, ink_darkness, ink_width_modifier, hairline_effects, post_dip_blob

if TYPE_CHECKING:
    from scribesim.hand.profile import HandProfile


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


def _heat_value(pressure_signal: float) -> int:
    p = max(0.0, min(1.0, pressure_signal))
    return int(round(p * 255.0))


# ---------------------------------------------------------------------------
# Core drawing primitives
# ---------------------------------------------------------------------------

def _draw_nib_sweep(
    draw: ImageDraw.ImageDraw,
    samples: list[tuple[float, float, float, float, float]],
    heat_draw: ImageDraw.ImageDraw | None = None,
    heat_values: list[int] | None = None,
) -> None:
    """Sweep nib edge through samples, draw filled quadrilaterals."""
    for si in range(len(samples) - 1):
        x0, y0, d0, hx0, hy0 = samples[si]
        x1, y1, d1, hx1, hy1 = samples[si + 1]
        darkness = (d0 + d1) / 2.0
        if darkness < 0.05:
            continue
        color = _ink_color(darkness)
        poly = [
            (x0 - hx0, y0 - hy0),
            (x0 + hx0, y0 + hy0),
            (x1 + hx1, y1 + hy1),
            (x1 - hx1, y1 - hy1),
        ]
        draw.polygon(poly, fill=color)
        if heat_draw is not None and heat_values is not None:
            heat = max(heat_values[si], heat_values[si + 1])
            if heat > 0:
                heat_draw.polygon(poly, fill=heat)

    # Cap stroke endpoints
    for idx, (x_px, y_px, darkness, hx_end, hy_end) in enumerate([samples[0], samples[-1]]):
        if darkness < 0.05:
            continue
        color = _ink_color(darkness)
        width = max(1, int(abs(hy_end) * 0.3 + abs(hx_end) * 0.3))
        draw.line(
            [(x_px - hx_end, y_px - hy_end), (x_px + hx_end, y_px + hy_end)],
            fill=color,
            width=width,
        )
        if heat_draw is not None and heat_values is not None:
            heat = heat_values[0 if idx == 0 else -1]
            if heat > 0:
                heat_draw.line(
                    [(x_px - hx_end, y_px - hy_end), (x_px + hx_end, y_px + hy_end)],
                    fill=heat,
                    width=width,
                )


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


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_word_from_genome(
    genome: WordGenome,
    dpi: float = 100.0,
    nib_width_mm: float = 0.6,
    nib_angle_deg: float = 42.0,
    canvas_width_mm: float | None = None,
    canvas_height_mm: float | None = None,
    variation: float = 1.0,
    ink_state: InkState | None = None,
    profile: "HandProfile | None" = None,
    return_heatmap: bool = False,
) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
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

    hairline_ratio = 0.065
    attack_width_boost = 0.10
    attack_zone_end = 0.10
    foot_width_boost = 0.20
    foot_ink_boost = 0.25
    foot_zone_start = 0.85
    attack_pressure_multiplier = 1.15
    release_taper_length = 0.30
    pressure_modulation_span = 0.08
    fresh_dip_darkness_boost = 0.10
    fresh_dip_width_boost = 0.03

    if profile is not None:
        quality = max(0.5, min(1.0, profile.nib.cut_quality))
        hairline_ratio = max(0.055, min(0.085, 0.09 - 0.05 * (quality - 0.5)))
        attack_width_boost = profile.stroke.attack_width_boost
        attack_zone_end = profile.stroke.attack_zone_end
        foot_width_boost = profile.stroke.foot_width_boost
        foot_ink_boost = profile.stroke.foot_ink_boost
        foot_zone_start = profile.stroke.foot_zone_start
        attack_pressure_multiplier = profile.nib.attack_pressure_multiplier
        release_taper_length = profile.nib.release_taper_length
        pressure_modulation_span = max(
            0.04,
            min(0.16, profile.stroke.pressure_modulation_range * 0.20),
        )
        fresh_dip_darkness_boost = max(0.0, min(0.20, profile.ink.fresh_dip_darkness_boost))
        fresh_dip_width_boost = max(0.01, min(0.06, profile.ink.fresh_dip_darkness_boost * 0.25))

    # Bastarda wants clear hairlines, but not vanishing joins.
    hairline_px = max(1.25, nib_width_mm * hairline_ratio * px_per_mm)

    left_margin_mm = 0.6  # tight — just enough to avoid clipping slanted strokes
    if canvas_width_mm is None:
        canvas_width_mm = genome.word_width_mm + left_margin_mm + 1.2
    if canvas_height_mm is None:
        canvas_height_mm = 14.0

    w_px = max(10, int(canvas_width_mm * px_per_mm))
    h_px = max(10, int(canvas_height_mm * px_per_mm))

    img = Image.new("RGB", (w_px, h_px), _PARCHMENT)
    draw = ImageDraw.Draw(img)
    heat_img = Image.new("L", (w_px, h_px), 0) if return_heatmap else None
    heat_draw = ImageDraw.Draw(heat_img) if heat_img is not None else None

    if ink_state is None:
        ink_state = InkState()
    n_samples = 80
    x_offset_px = left_margin_mm * px_per_mm

    v = variation

    # ------------------------------------------------------------ render glyphs
    for gi, glyph in enumerate(genome.glyphs):
        # Per-glyph slant drift only (no baseline jitter here — handled by affine y-shift below)
        glyph_slant_jitter = random.gauss(0, 0.4 * v) if v > 0 else 0.0
        slant_deg = genome.global_slant_deg + (
            genome.slant_drift[gi] if gi < len(genome.slant_drift) else 0.0
        ) + glyph_slant_jitter
        baseline_offset = genome.baseline_drift[gi] if gi < len(genome.baseline_drift) else 0.0
        slant_rad = math.radians(slant_deg)

        def to_px(x_mm, y_mm, _slant_rad=slant_rad, _baseline_offset=baseline_offset):
            return _world_to_px(
                x_mm, y_mm, genome.baseline_y, _slant_rad,
                _baseline_offset, px_per_mm, x_offset_px,
            )

        # Whole-glyph affine variation: one coherent transform per instance keeps each
        # letter internally consistent while producing visible instance-to-instance variation.
        # All four parameters use uniform distributions (not Gaussian) for bounded control.
        perturb_segs = glyph.segments
        if v > 0 and glyph.segments:
            scale = 1.0 + random.uniform(-0.015, 0.015) * v
            rot_rad = math.radians(random.uniform(-0.3, 0.3) * v)
            cos_r, sin_r = math.cos(rot_rad), math.sin(rot_rad)
            # Pixel shifts in final output pixels → convert to mm
            mm_per_px = _SUPERSAMPLE / px_per_mm  # = 25.4 / dpi
            x_shift_mm = random.uniform(-0.5, 0.5) * v * mm_per_px
            y_shift_mm = random.uniform(-0.3, 0.3) * v * mm_per_px

            # Centroid of all control points — rotate/scale around this
            all_pts = [p for seg in glyph.segments for p in (seg.p0, seg.p1, seg.p2, seg.p3)]
            cx = sum(p[0] for p in all_pts) / len(all_pts)
            cy = sum(p[1] for p in all_pts) / len(all_pts)

            def _affine(pt: tuple) -> tuple[float, float]:
                dx, dy = (pt[0] - cx) * scale, (pt[1] - cy) * scale
                return (cx + dx * cos_r - dy * sin_r + x_shift_mm,
                        cy + dx * sin_r + dy * cos_r + y_shift_mm)

            from scribesim.evo.genome import BezierSegment as _BS
            perturb_segs = [
                _BS(
                    p0=_affine(s.p0), p1=_affine(s.p1),
                    p2=_affine(s.p2), p3=_affine(s.p3),
                    contact=s.contact,
                    pressure_curve=s.pressure_curve,
                    speed_curve=s.speed_curve,
                    nib_angle_drift=s.nib_angle_drift,
                )
                for s in glyph.segments
            ]

        contact_segs = [s for s in perturb_segs if s.contact]
        if not contact_segs:
            continue

        # Render all contact segments
        glyph_nib_angle_drift = random.gauss(0, 1.4 * v) if v > 0 else 0.0

        for seg_idx, seg in enumerate(contact_segs):
            seg_angle_base_deg = nib_angle_deg + glyph_nib_angle_drift + seg.nib_angle_drift * 1.6
            seg_angle_start_deg = seg_angle_base_deg + (random.gauss(0, 0.45 * v) if v > 0 else 0.0)
            seg_angle_end_deg = seg_angle_base_deg + (random.gauss(0, 0.70 * v) if v > 0 else 0.0)
            seg_mid_angle_rad = math.radians((seg_angle_start_deg + seg_angle_end_deg) * 0.5)
            nib_cos = math.cos(seg_mid_angle_rad)
            nib_sin = math.sin(seg_mid_angle_rad)
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
                    if heat_draw is not None:
                        blob_heat = _heat_value(min(1.0, 0.84 + 0.16 * ink_state.reservoir))
                        heat_draw.polygon(pts, fill=blob_heat)
            samples: list[tuple[float, float, float, float, float]] = []
            heat_values: list[int] = []

            # Per-segment pressure variation ±5%
            pressure_scale = 1.0 + random.gauss(0, 0.025 * v) if v > 0 else 1.0
            pressure_scale = max(0.95, min(1.05, pressure_scale))

            # Per-segment stroke wobble: small perpendicular tremor along the path
            wobble_x = 0.0
            wobble_y = 0.0
            wobble_sigma_mm = 0.008 * v  # ±0.008mm lateral tremor
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
            segment_reservoir = ink_state.reservoir
            hfx = hairline_effects(segment_reservoir) if is_hairline else None
            segment_gap_probability = hfx.gap_probability if hfx is not None else 0.0

            # Raking: decide once per segment (split-nib effect at very low reservoir)
            is_raking = (hfx is not None
                         and hfx.raking_probability > 0.0
                         and random.random() < hfx.raking_probability)

            # Mean pressure for this segment → width modulation (TD-004 Fix B).
            # Pressure modulates width ±20%; direction is primary thick/thin driver.
            mean_pressure = sum(seg.pressure_at(t / 8) for t in range(9)) / 9
            mean_pressure *= pressure_scale
            seg_pressure_width = 1.0 + (mean_pressure - 0.5) * pressure_modulation_span

            sample_length_mm = seg.length() / max(1, n_samples)

            for si in range(n_samples + 1):
                t = si / n_samples
                pos = seg.evaluate(t)
                pressure = seg.pressure_at(t) * pressure_scale

                from scribesim.render.nib import stroke_foot_effect, stroke_attack_effect
                _foot_w, foot_i = stroke_foot_effect(
                    t,
                    foot_zone_start=foot_zone_start,
                    width_boost=foot_width_boost,
                    ink_boost=foot_ink_boost,
                )
                _attack_w, attack_i = stroke_attack_effect(
                    t,
                    attack_zone_end=attack_zone_end,
                    width_boost=attack_width_boost,
                )
                if t < attack_zone_end:
                    attack_progress = 1.0 - (t / max(attack_zone_end, 1e-6))
                    attack_i *= 1.0 + (attack_pressure_multiplier - 1.0) * attack_progress
                release_i = 1.0
                if release_taper_length > 0.0:
                    release_start = max(0.0, 1.0 - release_taper_length)
                    if t > release_start:
                        release_progress = (t - release_start) / max(release_taper_length, 1e-6)
                        release_i = max(0.72, 1.0 - 0.28 * release_progress)

                # Keep evo output in the same tonal family as the plain renderer:
                # pressure still matters, but fresh-dip richness should not clip
                # most strokes to near-black.
                current_reservoir = ink_state.reservoir
                current_hfx = hairline_effects(current_reservoir) if is_hairline else None
                base_dark = 0.74 + 0.14 * pressure
                fresh_phase = 0.0
                if ink_state.strokes_since_dip < 4:
                    fresh_phase = max(0.0, 1.0 - ((ink_state.strokes_since_dip + t) / 4.0))
                darkness = min(
                    1.0,
                    base_dark
                    * ink_darkness(current_reservoir)
                    * (1.0 + fresh_dip_darkness_boost * fresh_phase)
                    * foot_i
                    * attack_i
                    * release_i,
                )

                x_px, y_px = to_px(pos[0], pos[1])

                if v > 0:
                    wobble_x = wobble_x * 0.85 + random.gauss(0, wobble_px * 0.4)
                    wobble_y = wobble_y * 0.85 + random.gauss(0, wobble_px * 0.15)
                    x_px += wobble_x
                    y_px += wobble_y

                sample_angle_deg = seg_angle_start_deg + (seg_angle_end_deg - seg_angle_start_deg) * t
                sample_angle_rad = math.radians(sample_angle_deg)
                dynamic_width_mod = ink_width_modifier(current_reservoir) * (1.0 + fresh_dip_width_boost * fresh_phase)
                half_dynamic = nib_width_mm * dynamic_width_mod / 2.0
                hx_sample = half_dynamic * math.cos(sample_angle_rad) * px_per_mm * seg_pressure_width
                hy_sample = half_dynamic * math.sin(sample_angle_rad) * px_per_mm * seg_pressure_width
                if current_hfx is not None and current_hfx.width_reduction > 0.0:
                    scale_w = 1.0 - current_hfx.width_reduction
                    hx_sample *= scale_w
                    hy_sample *= scale_w
                    segment_gap_probability = max(segment_gap_probability, current_hfx.gap_probability)
                sample_norm = math.hypot(hx_sample, hy_sample)
                if sample_norm < hairline_px:
                    floor_scale = hairline_px / max(sample_norm, 1e-6)
                    hx_sample *= floor_scale
                    hy_sample *= floor_scale

                samples.append((x_px, y_px, darkness, hx_sample, hy_sample))
                pressure_signal = min(
                    1.0,
                    max(
                        0.0,
                        pressure
                        * foot_i
                        * attack_i
                        * release_i
                        * min(1.12, seg_pressure_width),
                    ),
                )
                heat_values.append(_heat_value(pressure_signal))
                if si < n_samples:
                    sample_width_mm = max(
                        nib_width_mm * hairline_ratio,
                        2.0 * math.hypot(hx_sample, hy_sample) / px_per_mm,
                    )
                    ink_state.deplete_for_step(sample_length_mm, pressure, sample_width_mm)

            if is_raking and len(samples) >= 2:
                x0s, y0s, _, _, _ = samples[0]
                xes, yes, _, _, _ = samples[-1]
                sdx, sdy = xes - x0s, yes - y0s
                slen = math.sqrt(sdx * sdx + sdy * sdy)
                if slen > 1.0:
                    px_n = -sdy / slen
                    py_n = sdx / slen
                    offset_px = max(0.5, nib_width_mm * 0.20 * px_per_mm / _SUPERSAMPLE)
                    rake_dark = 0.70
                    for sign in (-1.0, 1.0):
                        offset_samples = [
                            (x + sign * px_n * offset_px,
                             y + sign * py_n * offset_px,
                             d * rake_dark,
                             hx_pt * 0.5,
                             hy_pt * 0.5)
                            for x, y, d, hx_pt, hy_pt in samples
                        ]
                        _draw_nib_sweep(draw, offset_samples, heat_draw=heat_draw, heat_values=heat_values)
            else:
                # Normal draw — with per-sample gap smoothing for hairlines
                if hfx is not None and segment_gap_probability > 0.0:
                    gap_active = False
                    gap_prob = segment_gap_probability
                    run: list[tuple[float, float, float, float, float]] = []
                    run_heat: list[int] = []
                    for idx, pt in enumerate(samples):
                        if gap_active:
                            if random.random() > gap_prob * 2.0:
                                gap_active = False
                        else:
                            if random.random() < gap_prob:
                                gap_active = True
                        if gap_active:
                            if len(run) >= 2:
                                _draw_nib_sweep(draw, run, heat_draw=heat_draw, heat_values=run_heat)
                            run = []
                            run_heat = []
                        else:
                            run.append(pt)
                            run_heat.append(heat_values[idx])
                    if len(run) >= 2:
                        _draw_nib_sweep(draw, run, heat_draw=heat_draw, heat_values=run_heat)
                else:
                    _draw_nib_sweep(draw, samples, heat_draw=heat_draw, heat_values=heat_values)

            ink_state.finish_stroke()

    # ----------------------------------------- overline for numeral groups
    if genome.overline and genome.glyphs:
        # Find the actual topmost segment coordinate across all glyphs — handles numeral
        # groups like mcccclvij that have no real ascenders, avoiding a floating overline.
        top_y_mm = genome.baseline_y
        for _g in genome.glyphs:
            for _seg in _g.segments:
                for _pt in (_seg.p0, _seg.p1, _seg.p2, _seg.p3):
                    top_y_mm = min(top_y_mm, _pt[1])

        x_height_mm_est = 3.8
        slant_rad_nom = math.radians(genome.global_slant_deg)
        # Place overline 0.15×xh above the actual topmost glyph point
        overline_y_mm = top_y_mm - 0.15 * x_height_mm_est

        x_start_mm = genome.glyphs[0].x_offset - 0.5
        x_end_mm = genome.glyphs[-1].x_offset + genome.glyphs[-1].x_advance + 0.5

        # Draw as a nib stroke with natural ink gradient:
        #   darkness: light start → builds → long taper to near-invisible at end
        #   width:    slightly thicker at entry → tapers to very fine at exit
        # This matches a scribe making a deliberate thin horizontal mark with the same pen.
        n_ol = 60
        ol_pts = []
        for si in range(n_ol + 1):
            t = si / n_ol
            x_mm = x_start_mm + t * (x_end_mm - x_start_mm)
            x_px, y_px = _world_to_px(x_mm, overline_y_mm, genome.baseline_y,
                                      slant_rad_nom, 0.0, px_per_mm, x_offset_px)
            ol_pts.append((x_px, y_px))

        for si in range(len(ol_pts) - 1):
            t = (si + 0.5) / n_ol
            x0, y0 = ol_pts[si]
            x1, y1 = ol_pts[si + 1]

            # Darkness profile: quick rise then long fade to nearly invisible
            if t < 0.12:
                darkness = 0.35 + (t / 0.12) * 0.40    # 0.35 → 0.75
            elif t < 0.30:
                darkness = 0.75 - (t - 0.12) / 0.18 * 0.08  # 0.75 → 0.67
            else:
                fade = (t - 0.30) / 0.70
                darkness = 0.67 * (1.0 - fade) ** 2.2  # 0.67 → ~0

            # Width profile: entry slightly thick, then tapers strongly toward exit
            if t < 0.08:
                w = 0.42 + (t / 0.08) * 0.18           # 0.42 → 0.60
            else:
                w = 0.60 * (1.0 - (t - 0.08) / 0.92) ** 1.4  # 0.60 → 0

            w = max(w, 0.05)
            lhx = hx * w
            lhy = hy * w

            if darkness < 0.04:
                continue
            color = _ink_color(darkness)
            poly = [
                (x0 - lhx, y0 - lhy), (x0 + lhx, y0 + lhy),
                (x1 + lhx, y1 + lhy), (x1 - lhx, y1 - lhy),
            ]
            draw.polygon(poly, fill=color)
            if heat_draw is not None:
                heat_draw.polygon(poly, fill=_heat_value(darkness))

    # ----------------------------------------- downsample to target resolution
    out_w = max(1, w_px // ss)
    out_h = max(1, h_px // ss)
    img = img.resize((out_w, out_h), Image.LANCZOS)
    page_arr = np.array(img)
    if heat_img is None:
        return page_arr
    heat_img = heat_img.resize((out_w, out_h), Image.LANCZOS)
    return page_arr, np.array(heat_img)


def render_genome_to_file(genome: WordGenome, output_path: str, **kwargs) -> str:
    """Render and save to a PNG file."""
    from pathlib import Path
    arr = render_word_from_genome(genome, **kwargs)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr, "RGB").save(str(out), format="PNG")
    return str(out)
