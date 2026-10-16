"""Fast zero-lockout sandbox renderer and kinematic/nib diagnostic viewer (TD-019 Pillar 4).

Renders words, bigrams, or multi-line specimens in <0.5s using Bastarda nib-width
proportions (H = 4.2 * w_nib), true 40° chisel sweep, pressure tine splay, and
velocity-minimum turn pooling. Emits PNG, SVG kinematic overlay, JSON metrics,
and a self-contained HTML diagnostic sheet without any hash-pin preflight lockouts.
"""

from __future__ import annotations

import html
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scribesim.hand.profile import (
    BASTARDA_DEFAULT_X_HEIGHT_MM,
    BASTARDA_NIB_PROPORTION_RATIO,
    HandProfile,
    bastarda_nib_calibrated_profile,
)
from scribesim.render.nib import (
    PhysicsNib,
    chisel_apparent_width_mm,
    evaluate_a1_proportion,
    turn_pooling_factor,
)

_PARCHMENT_RGB = (245, 238, 220)
_INK_RGB = (38, 26, 18)


@dataclass(frozen=True)
class SandboxSample:
    """Single trajectory sample in physical mm coordinates (y-down canvas frame)."""
    x_mm: float
    y_mm: float
    vx_mm_s: float
    vy_mm_s: float
    contact: bool
    pressure: float
    nib_angle_deg: float
    letter: str = ""
    role: str = "body"


def _ink_rgb(alpha: float) -> tuple[int, int, int]:
    a = max(0.0, min(1.0, alpha))
    return (
        round(_INK_RGB[0] * a + _PARCHMENT_RGB[0] * (1.0 - a)),
        round(_INK_RGB[1] * a + _PARCHMENT_RGB[1] * (1.0 - a)),
        round(_INK_RGB[2] * a + _PARCHMENT_RGB[2] * (1.0 - a)),
    )


def render_trajectory_samples(
    samples: list[SandboxSample] | tuple[SandboxSample, ...],
    *,
    profile: HandProfile | None = None,
    dpi: float = 220.0,
    supersample: int = 2,
    margin_mm: float = 2.0,
    via_points_mm: list[dict] | None = None,
) -> tuple[np.ndarray, str, dict]:
    """Render trajectory samples with true 40° broad-nib chisel sweep and turn pooling.

    Returns (rgb_array, svg_overlay_str, metrics_dict).
    """
    prof = profile or bastarda_nib_calibrated_profile()
    nib = PhysicsNib(
        width_mm=prof.nib.width_mm,
        angle_deg=prof.nib.angle_deg,
        flexibility=prof.nib.flexibility,
        cut_quality=prof.nib.cut_quality,
    )
    xh = prof.letterform.x_height_mm

    contact_pts = [s for s in samples if s.contact]
    if not contact_pts:
        empty = np.full((64, 128, 3), _PARCHMENT_RGB, dtype=np.uint8)
        verdict = evaluate_a1_proportion([], x_height_mm=xh, nib_width_mm=nib.width_mm)
        return empty, "<svg xmlns='http://www.w3.org/2000/svg' width='128' height='64'></svg>", {"a1_proportion": verdict}

    xs = [s.x_mm for s in contact_pts]
    ys = [s.y_mm for s in contact_pts]
    min_x = min(xs) - margin_mm
    max_x = max(xs) + margin_mm
    min_y = min(ys) - margin_mm
    max_y = max(ys) + margin_mm

    w_mm = max(4.0, max_x - min_x)
    h_mm = max(4.0, max_y - min_y)

    px_per_mm_out = dpi / 25.4
    px_per_mm_int = px_per_mm_out * supersample

    w_out = max(32, round(w_mm * px_per_mm_out))
    h_out = max(32, round(h_mm * px_per_mm_out))
    w_int = max(64, round(w_mm * px_per_mm_int))
    h_int = max(64, round(h_mm * px_per_mm_int))

    img = Image.new("RGB", (w_int, h_int), _PARCHMENT_RGB)
    draw = ImageDraw.Draw(img)

    widths_mm: list[float] = []
    svg_Paths: list[str] = []
    svg_nibs: list[str] = []

    svg_scale = 28.0  # px per mm in diagnostic SVG
    svg_w = round(w_mm * svg_scale)
    svg_h = round(h_mm * svg_scale)

    for idx in range(1, len(samples)):
        prev = samples[idx - 1]
        curr = samples[idx]
        if not (prev.contact and curr.contact):
            continue

        dx = curr.x_mm - prev.x_mm
        dy = curr.y_mm - prev.y_mm
        seg_len = math.hypot(dx, dy)
        if seg_len < 1e-6:
            continue

        # In physical y-up calligraphic angle: dy_up = -dy_canvas
        dir_deg = math.degrees(math.atan2(-dy, dx))
        speed = math.hypot(curr.vx_mm_s, curr.vy_mm_s)
        avg_p = 0.5 * (prev.pressure + curr.pressure)

        local_nib = PhysicsNib(
            width_mm=nib.width_mm,
            angle_deg=curr.nib_angle_deg,
            flexibility=nib.flexibility,
        )
        app_w = chisel_apparent_width_mm(local_nib, dir_deg, avg_p)
        pool_w, pool_i = turn_pooling_factor(speed, nominal_speed_mm_s=12.0)
        eff_w = app_w * pool_w
        widths_mm.append(eff_w)

        # Chisel edge half-vector in canvas coordinates (y-down, so -sin for +angle_deg up-right)
        angle_rad = math.radians(curr.nib_angle_deg)
        splay_scale = (0.85 + 0.25 * avg_p) * pool_w
        half_edge = 0.5 * nib.width_mm * splay_scale
        hx_mm = half_edge * math.cos(angle_rad)
        hy_mm = -half_edge * math.sin(angle_rad)

        # Normal thickness vector (t_nib) perpendicular to chisel edge so 40° hairlines have finite thickness
        t_half_mm = 0.5 * nib.width_mm * 0.21
        nx_mm = -t_half_mm * math.sin(angle_rad)
        ny_mm = -t_half_mm * math.cos(angle_rad)

        x0 = (prev.x_mm - min_x) * px_per_mm_int
        y0 = (prev.y_mm - min_y) * px_per_mm_int
        x1 = (curr.x_mm - min_x) * px_per_mm_int
        y1 = (curr.y_mm - min_y) * px_per_mm_int

        hx_px = hx_mm * px_per_mm_int
        hy_px = hy_mm * px_per_mm_int
        nx_px = nx_mm * px_per_mm_int
        ny_px = ny_mm * px_per_mm_int

        darkness = min(1.0, max(0.38, (0.62 + 0.32 * avg_p) * pool_i * prof.ink_density))
        color = _ink_rgb(darkness)

        # Sweep both chisel edge and finite nib thickness
        quad_edge = [
            (x0 - hx_px - nx_px, y0 - hy_px - ny_px),
            (x0 + hx_px + nx_px, y0 + hy_px + ny_px),
            (x1 + hx_px + nx_px, y1 + hy_px + ny_px),
            (x1 - hx_px - nx_px, y1 - hy_px - ny_px),
        ]
        draw.polygon(quad_edge, fill=color)
        quad_thick = [
            (x0 - hx_px + nx_px, y0 - hy_px + ny_px),
            (x0 + hx_px - nx_px, y0 + hy_px - ny_px),
            (x1 + hx_px - nx_px, y1 + hy_px - ny_px),
            (x1 - hx_px + nx_px, y1 - hy_px + ny_px),
        ]
        draw.polygon(quad_thick, fill=color)

        sx0 = (prev.x_mm - min_x) * svg_scale
        sy0 = (prev.y_mm - min_y) * svg_scale
        sx1 = (curr.x_mm - min_x) * svg_scale
        sy1 = (curr.y_mm - min_y) * svg_scale
        stroke_col = "#166e68" if curr.role == "join" else "#26322e"
        svg_Paths.append(
            f"<line x1='{sx0:.2f}' y1='{sy0:.2f}' x2='{sx1:.2f}' y2='{sy1:.2f}' "
            f"stroke='{stroke_col}' stroke-width='{max(1.2, eff_w * svg_scale * 0.45):.2f}' stroke-linecap='round' opacity='0.75'/>"
        )
        if idx % 5 == 0:
            shx = hx_mm * svg_scale
            shy = hy_mm * svg_scale
            svg_nibs.append(
                f"<line x1='{sx1 - shx:.2f}' y1='{sy1 - shy:.2f}' x2='{sx1 + shx:.2f}' y2='{sy1 + shy:.2f}' "
                f"stroke='#c85a17' stroke-width='1.3' opacity='0.85'/>"
            )

    svg_vias: list[str] = []
    for vp in via_points_mm or []:
        vx = (vp["x_mm"] - min_x) * svg_scale
        vy = (vp["y_mm"] - min_y) * svg_scale
        rx = max(2.0, vp.get("sigma_x_mm", 0.08) * svg_scale)
        ry = max(2.0, vp.get("sigma_y_mm", 0.08) * svg_scale)
        role_color = "#b8332a" if vp.get("role") == "boundary" else "#2a52be"
        svg_vias.append(
            f"<ellipse cx='{vx:.2f}' cy='{vy:.2f}' rx='{rx:.2f}' ry='{ry:.2f}' "
            f"fill='none' stroke='{role_color}' stroke-width='1.1' stroke-dasharray='2,2'/>"
            f"<circle cx='{vx:.2f}' cy='{vy:.2f}' r='2.4' fill='{role_color}'/>"
        )

    out_img = img.resize((w_out, h_out), Image.LANCZOS) if supersample > 1 else img
    arr = np.asarray(out_img, dtype=np.uint8)

    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {svg_w} {svg_h}' width='100%'>"
        f"<rect width='100%' height='100%' fill='#faf6eb'/>"
        + "".join(svg_Paths)
        + "".join(svg_nibs)
        + "".join(svg_vias)
        + "</svg>"
    )

    a1 = evaluate_a1_proportion(widths_mm, x_height_mm=xh, nib_width_mm=nib.width_mm)
    metrics = {
        "a1_proportion": a1,
        "sample_count": len(samples),
        "contact_segments": len(widths_mm),
        "width_mm": round(w_mm, 3),
        "height_mm": round(h_mm, 3),
    }
    return arr, svg, metrics


def _fallback_samples_for_text(text: str, profile: HandProfile) -> tuple[list[SandboxSample], list[dict]]:
    """Generate kinematic trajectory samples for `text` (uses coarticulate solver when available)."""
    coart_path = Path(__file__).parents[1] / "handflow" / "coarticulate.py"
    if coart_path.exists():
        import importlib.util
        import sys
        mod_name = "scribesim.handflow._coarticulate_fast"
        mod = sys.modules.get(mod_name)
        if mod is None:
            spec = importlib.util.spec_from_file_location(mod_name, coart_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)
        if mod is not None and hasattr(mod, "compose_text_kinematic"):
            return mod.compose_text_kinematic(text, profile=profile)

    # Fallback nib-normalized generator before ADV-SS-HANDFLOW-012 lands
    xh = profile.letterform.x_height_mm
    w_nib = profile.nib.width_mm
    angle = profile.nib.angle_deg
    baseline_y = xh * 2.0
    cursor_x = w_nib * 1.5
    samples: list[SandboxSample] = []
    vias: list[dict] = []

    for ch in text:
        if ch == " ":
            cursor_x += 2.2 * w_nib
            continue
        # 2-minim + 40° hairline join archetype in w_nib units
        tan40 = math.tan(math.radians(angle))
        p0 = (cursor_x, baseline_y - xh)
        p1 = (cursor_x + 0.08 * w_nib, baseline_y)
        # 40° diagonal hairline join rising by dx * tan(40°)
        p2 = (cursor_x + 1.28 * w_nib, baseline_y - 1.20 * w_nib * tan40)
        p3 = (cursor_x + 1.28 * w_nib, baseline_y - xh)
        p4 = (cursor_x + 1.36 * w_nib, baseline_y)
        p5 = (cursor_x + 2.36 * w_nib, baseline_y - 1.00 * w_nib * tan40)
        pts = [p0, p1, p2, p3, p4, p5]
        roles = ["body", "boundary", "join", "body", "boundary", "join"]
        for (x, y), r in zip(pts, roles):
            vias.append({"x_mm": x, "y_mm": y, "sigma_x_mm": 0.12 * w_nib, "sigma_y_mm": 0.12 * w_nib, "role": r, "letter": ch})

        segments = [
            (p0, p1, 0.82, "body"),
            (p1, p2, 0.28, "join"),
            (p3, p4, 0.80, "body"),
            (p4, p5, 0.28, "join"),
        ]
        for idx_s, (a, b, p_val, r_name) in enumerate(segments):
            n_steps = 12
            for k in range(n_steps):
                if idx_s > 0 and k == 0:
                    continue
                u = k / (n_steps - 1)
                # Minimum-jerk polynomial s(u) = 10u^3 - 15u^4 + 6u^5
                s = 10 * u**3 - 15 * u**4 + 6 * u**5
                ds = 30 * u**2 * (1 - u) ** 2  # bell-shaped speed factor [0..1.875]
                x = a[0] + s * (b[0] - a[0])
                y = a[1] + s * (b[1] - a[1])
                speed = 12.0 * (0.15 + 0.85 * (ds / 1.875))
                dx = b[0] - a[0]
                dy = b[1] - a[1]
                norm = max(1e-6, math.hypot(dx, dy))
                samples.append(
                    SandboxSample(
                        x_mm=x,
                        y_mm=y,
                        vx_mm_s=speed * dx / norm,
                        vy_mm_s=speed * dy / norm,
                        contact=True,
                        pressure=p_val,
                        nib_angle_deg=angle,
                        letter=ch,
                        role=r_name,
                    )
                )
        cursor_x += 2.35 * w_nib

    return samples, vias


def render_sandbox(
    text: str,
    *,
    out_dir: Path | str = "debug/sandbox",
    dpi: float = 220.0,
    x_height_mm: float = BASTARDA_DEFAULT_X_HEIGHT_MM,
    xh_in_nib_widths: float = BASTARDA_NIB_PROPORTION_RATIO,
    nib_angle_deg: float = 40.0,
) -> dict:
    """Render `text` in the zero-lockout sandbox and write PNG, SVG, JSON, and HTML."""
    t0 = time.perf_counter()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    profile = bastarda_nib_calibrated_profile(
        x_height_mm=x_height_mm,
        x_height_in_nib_widths=xh_in_nib_widths,
        angle_deg=nib_angle_deg,
    )
    samples, vias = _fallback_samples_for_text(text, profile)
    arr, svg, metrics = render_trajectory_samples(
        samples, profile=profile, dpi=dpi, via_points_mm=vias
    )
    elapsed_s = time.perf_counter() - t0
    metrics["text"] = text
    metrics["elapsed_seconds"] = round(elapsed_s, 4)

    png_path = out / "sandbox.png"
    Image.fromarray(arr, "RGB").save(str(png_path), format="PNG", dpi=(dpi, dpi))

    svg_path = out / "overlay.svg"
    svg_path.write_text(svg, encoding="utf-8")

    metrics_path = out / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    a1 = metrics["a1_proportion"]
    badge_color = "#1b7f4c" if a1["passed"] else "#b8332a"
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>ScribeSim Sandbox — {html.escape(text)}</title>
  <style>
    body {{ font: 16px/1.55 system-ui, sans-serif; background: #f4f1ea; color: #222; max-width: 1100px; margin: 28px auto; padding: 0 20px; }}
    .card {{ background: #fffdf8; border: 1px solid #d8d2c5; border-radius: 10px; padding: 18px; margin-bottom: 20px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; color: white; font-weight: 600; background: {badge_color}; }}
    img {{ max-width: 100%; border: 1px solid #dfd8c8; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>ScribeSim Fast Sandbox: <code>{html.escape(text)}</code></h1>
  <div class="card">
    <span class="badge">A1-PROPORTION: {'PASS' if a1['passed'] else 'FAIL'}</span>
    <span>P95/P05 Width Ratio: <strong>{a1['width_ratio_p95_p05']}</strong> (target 3.2–5.0)</span> ·
    <span>H / w_nib: <strong>{a1['x_height_to_nib_ratio']}</strong> (w_nib={a1['nib_width_mm']}mm, H={a1['x_height_mm']}mm)</span> ·
    <span>Render time: <strong>{metrics['elapsed_seconds']}s</strong></span>
  </div>
  <div class="card">
    <h2>1. Physical Broad-Nib Ink Sweep</h2>
    <img src="sandbox.png" alt="Sandbox ink render"/>
  </div>
  <div class="card">
    <h2>2. Kinematic Via-Point &amp; Chisel Overlay</h2>
    <p>Dark/Teal: solved minimum-jerk trajectory · Orange: 40° chisel edge · Blue/Red ellipses: via-point tolerances Σ_k</p>
    {svg}
  </div>
</body>
</html>
"""
    (out / "index.html").write_text(html_doc, encoding="utf-8")
    return metrics
