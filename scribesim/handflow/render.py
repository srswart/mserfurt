"""Broad-edge proof rendering for guided handflow."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scribesim.hand.profile import HandProfile
from scribesim.handvalidate import TrajectorySample
from scribesim.render.nib import stroke_opacity


_PARCHMENT = (245, 238, 220)
_INK = (18, 12, 8)


def _ink_color(alpha: float) -> tuple[int, int, int]:
    value = max(0.0, min(1.0, alpha))
    return (
        round(_INK[0] * value + _PARCHMENT[0] * (1.0 - value)),
        round(_INK[1] * value + _PARCHMENT[1] * (1.0 - value)),
        round(_INK[2] * value + _PARCHMENT[2] * (1.0 - value)),
    )


def _sample_direction(
    samples: tuple[TrajectorySample, ...],
    index: int,
) -> tuple[float, float]:
    if len(samples) < 2:
        return (1.0, 0.0)
    if index == 0:
        a = samples[0]
        b = samples[1]
    elif index >= len(samples) - 1:
        a = samples[-2]
        b = samples[-1]
    else:
        a = samples[index - 1]
        b = samples[index + 1]
    dx = b.x_mm - a.x_mm
    dy = b.y_mm - a.y_mm
    norm = math.hypot(dx, dy)
    if norm <= 1e-9:
        return (1.0, 0.0)
    return (dx / norm, dy / norm)


def _trajectory_bounds(
    trajectory: tuple[TrajectorySample, ...],
    *,
    margin_mm: float = 1.0,
) -> tuple[float, float, float, float]:
    contact_samples = [sample for sample in trajectory if sample.contact]
    if not contact_samples:
        raise ValueError("trajectory must contain at least one contact sample")
    x_min = min(sample.x_mm for sample in contact_samples) - margin_mm
    x_max = max(sample.x_mm for sample in contact_samples) + margin_mm
    y_min = min(sample.y_mm for sample in contact_samples) - margin_mm
    y_max = max(sample.y_mm for sample in contact_samples) + margin_mm
    return (x_min, x_max, y_min, y_max)


def render_trajectory_canvas(
    trajectory: tuple[TrajectorySample, ...],
    *,
    profile: HandProfile,
    dpi: int = 300,
    supersample: int = 3,
    margin_mm: float = 1.0,
    bounds_mm: tuple[float, float, float, float] | None = None,
    return_heatmap: bool = False,
) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    """Render a trajectory into a contract-sized canvas, optionally with heatmap."""

    if not trajectory:
        raise ValueError("trajectory must contain at least one sample")

    contact_samples = [sample for sample in trajectory if sample.contact]
    if not contact_samples:
        raise ValueError("trajectory must contain at least one contact sample")

    px_per_mm = dpi * supersample / 25.4
    if bounds_mm is None:
        x_min, x_max, y_min, y_max = _trajectory_bounds(trajectory, margin_mm=margin_mm)
    else:
        x_min, x_max, y_min, y_max = bounds_mm
    output_width_px = max(8, round((x_max - x_min) * dpi / 25.4))
    output_height_px = max(8, round((y_max - y_min) * dpi / 25.4))
    width_px = max(output_width_px * supersample, 8)
    height_px = max(output_height_px * supersample, 8)
    x_px_per_mm = width_px / max(x_max - x_min, 1e-9)
    y_px_per_mm = height_px / max(y_max - y_min, 1e-9)
    width_px_per_mm = (x_px_per_mm + y_px_per_mm) * 0.5

    image = Image.new("RGB", (width_px, height_px), _PARCHMENT)
    draw = ImageDraw.Draw(image)
    heat_image = Image.new("L", (width_px, height_px), 0) if return_heatmap else None
    heat_draw = ImageDraw.Draw(heat_image) if heat_image is not None else None

    on_surface_runs: list[list[int]] = []
    current_run: list[int] = []
    for idx, sample in enumerate(trajectory):
        if sample.contact:
            current_run.append(idx)
        elif current_run:
            on_surface_runs.append(current_run)
            current_run = []
    if current_run:
        on_surface_runs.append(current_run)

    hand = profile.to_v1()
    for run in on_surface_runs:
        if len(run) < 2:
            continue
        sweep_samples: list[tuple[float, float, float, float, float, int]] = []
        for idx in run:
            sample = trajectory[idx]
            width_mm = sample.width_mm or profile.nib.width_mm * 0.08
            half_major = width_mm * 0.5 * width_px_per_mm
            half_minor = width_mm * 0.125 * width_px_per_mm
            nib_angle_rad = math.radians(sample.nib_angle_deg if sample.nib_angle_deg is not None else profile.nib.angle_deg)
            cos_a = math.cos(nib_angle_rad)
            sin_a = math.sin(nib_angle_rad)
            hx = math.sqrt((half_major * cos_a) ** 2 + (half_minor * sin_a) ** 2)
            hy = math.sqrt((half_major * sin_a) ** 2 + (half_minor * cos_a) ** 2)
            x_px = (sample.x_mm - x_min) * x_px_per_mm
            y_px = (sample.y_mm - y_min) * y_px_per_mm
            ink_pressure = sample.pressure or 0.0
            if sample.width_mm is not None:
                width_ratio = sample.width_mm / max(profile.nib.width_mm, 1e-9)
                ink_pressure *= 0.90 + 0.25 * max(0.0, min(width_ratio, 1.35))
            opacity = stroke_opacity(min(1.15, ink_pressure), hand.stroke_weight, hand.ink_density, 1.0)
            sweep_samples.append((x_px, y_px, opacity / 255.0, hx, hy, int(opacity)))

        for idx in range(len(sweep_samples) - 1):
            x0, y0, darkness0, hx0, hy0, heat0 = sweep_samples[idx]
            x1, y1, darkness1, hx1, hy1, heat1 = sweep_samples[idx + 1]
            poly = [
                (x0 - hx0, y0 - hy0),
                (x0 + hx0, y0 + hy0),
                (x1 + hx1, y1 + hy1),
                (x1 - hx1, y1 - hy1),
            ]
            draw.polygon(poly, fill=_ink_color((darkness0 + darkness1) * 0.5))
            if heat_draw is not None:
                heat_draw.polygon(poly, fill=max(heat0, heat1))

    if supersample > 1:
        output_size = (output_width_px, output_height_px)
        image = image.resize(output_size, Image.LANCZOS)
        if heat_image is not None:
            heat_image = heat_image.resize(output_size, Image.LANCZOS)

    rgb = np.array(image)
    if heat_image is None:
        return rgb
    return rgb, np.array(heat_image)


def render_trajectory_proof(
    trajectory: tuple[TrajectorySample, ...],
    *,
    profile: HandProfile,
    output_path: Path | str | None = None,
    dpi: int = 300,
    supersample: int = 3,
    margin_mm: float = 1.0,
    bounds_mm: tuple[float, float, float, float] | None = None,
) -> np.ndarray:
    """Render a trajectory using a broad-edge nib sweep."""

    array = render_trajectory_canvas(
        trajectory,
        profile=profile,
        dpi=dpi,
        supersample=supersample,
        margin_mm=margin_mm,
        bounds_mm=bounds_mm,
        return_heatmap=False,
    )
    if output_path is not None:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(array, "RGB").save(output, format="PNG", dpi=(dpi, dpi))
    return array
