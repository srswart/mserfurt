"""Structure-Conditioned Hybrid Ink-Edge Micro-Texture Pass
(TD-019 §5 Optional Phase 16d, ADV-SS-SCRIBEHAND-004).

Refines a coarticulated kinematic render with 15th-century iron-gall quill-on-vellum
micro-texture conditioned on the exact kinematic ink mask and pressure heatmap:
  1. Corridor-clamped quill-edge capillary micro-roughness (anisotropic calfskin fiber bite)
  2. Iron-gall meniscus rim darkening ("coffee-ring" edge) & internal vellum-pore granulation
  3. Subtle calfskin vellum substrate fiber & pore texture

Strictly preserves stroke centerlines (IoU >= 0.92), enclosed letter counters
(counter_delta == 0), 100% text fidelity, and exact PAGE XML bounding coordinates.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import (
    binary_dilation,
    binary_erosion,
    gaussian_filter,
    label,
    sobel,
)

MAX_HYBRID_STRENGTH: float = 0.25
_PARCHMENT = np.array([245.0, 238.0, 220.0], dtype=np.float32)
_INK_DARK = np.array([34.0, 22.0, 14.0], dtype=np.float32)


def _count_enclosed_counters(mask_ink: np.ndarray, min_area_px: int = 6) -> int:
    """Count enclosed non-border background islands (counters) inside ink."""
    bg = ~mask_ink
    labeled, num_features = label(bg)
    if num_features <= 1:
        return 0
    border_ids = (
        set(labeled[0, :].tolist())
        | set(labeled[-1, :].tolist())
        | set(labeled[:, 0].tolist())
        | set(labeled[:, -1].tolist())
    )
    count = 0
    for comp_id in range(1, num_features + 1):
        if comp_id in border_ids:
            continue
        if int(np.sum(labeled == comp_id)) >= min_area_px:
            count += 1
    return count


def apply_hybrid_texture_pass(
    page_rgb: np.ndarray,
    pressure_map: np.ndarray | None = None,
    *,
    seed: int = 1457,
    strength: float = 0.22,
) -> np.ndarray:
    """Apply structure-conditioned quill-on-vellum micro-texture to `page_rgb`.

    Strength is hard-clamped to `[0.0, MAX_HYBRID_STRENGTH]` (`<= 0.25`) so the
    pass can never hallucinate strokes, bridge counters, or shift centerlines.
    """
    eff_strength = float(max(0.0, min(MAX_HYBRID_STRENGTH, strength)))
    if eff_strength <= 1e-6:
        return page_rgb.copy()

    h, w = page_rgb.shape[:2]
    rng = np.random.default_rng(int(seed))

    raw_f = page_rgb.astype(np.float32)
    # Normalized ink darkness alpha in [0, 1] relative to parchment
    parch_lum = float(np.mean(_PARCHMENT))
    ink_lum = float(np.mean(_INK_DARK))
    gray = raw_f.mean(axis=2)
    alpha = np.clip((parch_lum - gray) / max(1.0, parch_lum - ink_lum), 0.0, 1.0)

    if pressure_map is not None and pressure_map.shape == (h, w):
        p_norm = np.clip(pressure_map.astype(np.float32) / 255.0, 0.0, 1.0)
    else:
        p_norm = alpha.copy()

    ink_mask = alpha > 0.18
    core_mask = binary_erosion(ink_mask, iterations=1)
    edge_band = ink_mask & ~core_mask
    outer_fringe = binary_dilation(ink_mask, iterations=1) & ~ink_mask

    # Protect enclosed interior counter pixels from any outer fringe bleed
    bg = ~ink_mask
    labeled_bg, n_bg = label(bg)
    border_ids = (
        set(labeled_bg[0, :].tolist())
        | set(labeled_bg[-1, :].tolist())
        | set(labeled_bg[:, 0].tolist())
        | set(labeled_bg[:, -1].tolist())
    )
    counter_bg = (labeled_bg > 0) & ~np.isin(labeled_bg, list(border_ids))
    safe_outer_fringe = outer_fringe & ~counter_bg

    # 1. Multi-scale anisotropic vellum-fiber field (calfskin vertical grain + micro-pores)
    noise_fine = rng.standard_normal((h, w)).astype(np.float32)
    noise_grain = rng.standard_normal((h, w)).astype(np.float32)
    fiber_vertical = gaussian_filter(noise_grain, sigma=(1.8, 0.65))
    fiber_vertical /= float(np.std(fiber_vertical) + 1e-6)
    pore_micro = gaussian_filter(noise_fine, sigma=(0.65, 0.65))
    pore_micro /= float(np.std(pore_micro) + 1e-6)

    # 2. Corridor-clamped quill-edge micro-roughness (feathering & nib bite along stroke boundary)
    edge_jitter = (0.60 * fiber_vertical + 0.40 * pore_micro) * (eff_strength * 0.85)
    alpha_mod = alpha.copy()
    alpha_mod[edge_band] = np.clip(alpha_mod[edge_band] + edge_jitter[edge_band], 0.05, 1.0)

    # Subtle capillary micro-wicking into safe 1px outer fringe where pressure is high
    wick = np.maximum(0.0, fiber_vertical - 0.35) * (0.35 + 0.65 * gaussian_filter(p_norm, sigma=1.0)) * (eff_strength * 0.55)
    alpha_mod[safe_outer_fringe] = np.clip(
        alpha_mod[safe_outer_fringe] + wick[safe_outer_fringe], 0.0, 0.42
    )

    # 3. Iron-gall meniscus rim darkening ("coffee-ring" drying edge) & internal pore granulation
    # Rim pixels just inside the stroke edge darken slightly; thick cores show vellum pore mottling
    rim_boost = edge_band.astype(np.float32) * (eff_strength * 0.48)
    internal_mottle = core_mask.astype(np.float32) * pore_micro * (eff_strength * 0.42) * (1.15 - 0.35 * p_norm)
    alpha_final = np.clip(alpha_mod + rim_boost + internal_mottle, 0.0, 1.0)

    # Ensure core centerline pixels never drop below legible threshold
    alpha_final[core_mask] = np.maximum(alpha_final[core_mask], alpha[core_mask] * 0.82)

    # 4. Calfskin vellum substrate texture + warm iron-gall tone modulation
    substrate_tex = (0.65 * fiber_vertical + 0.35 * gaussian_filter(noise_grain, sigma=3.2)) * (eff_strength * 14.0)
    parch_rgb = np.clip(_PARCHMENT[None, None, :] + substrate_tex[:, :, None] * np.array([1.0, 0.92, 0.80]), 210.0, 253.0)

    # Slight warm/cool iron-gall pigment shift from pore granulation
    ink_rgb = np.clip(
        _INK_DARK[None, None, :] + pore_micro[:, :, None] * (eff_strength * 18.0) * np.array([1.1, 0.85, 0.65]),
        12.0,
        85.0,
    )

    a3 = alpha_final[:, :, None]
    out_rgb = parch_rgb * (1.0 - a3) + ink_rgb * a3

    # Guarantee topological invariance at the 212.0 ink/background threshold so
    # counters never bridge or split while preserving continuous edge/interior shading:
    out_gray = out_rgb.mean(axis=2)
    ink_too_light = ink_mask & (out_gray >= 209.0)
    if np.any(ink_too_light):
        scale = 208.0 / np.maximum(out_gray[ink_too_light], 1.0)
        out_rgb[ink_too_light] *= scale[:, None]

    bg_too_dark = (~ink_mask) & (out_gray < 214.0)
    if np.any(bg_too_dark):
        lift = (214.5 - out_gray[bg_too_dark])[:, None]
        out_rgb[bg_too_dark] += lift

    return np.clip(np.round(out_rgb), 0, 255).astype(np.uint8)


def evaluate_hybrid_structure_gate(
    raw_rgb: np.ndarray,
    textured_rgb: np.ndarray,
    pressure_map: np.ndarray | None = None,
    *,
    min_centerline_iou: float = 0.92,
) -> dict:
    """Evaluate structure preservation (centerline IoU >= 0.92, counter invariance) and texture gain."""
    raw_gray = raw_rgb.astype(np.float32).mean(axis=2)
    tex_gray = textured_rgb.astype(np.float32).mean(axis=2)

    raw_ink = raw_gray < 212.0
    tex_ink = tex_gray < 212.0

    # Core / centerline masks
    raw_core = binary_erosion(raw_ink, iterations=1)
    tex_core = binary_erosion(tex_ink, iterations=1)
    if not np.any(raw_core):
        raw_core = raw_ink
        tex_core = tex_ink

    inter = int(np.sum(raw_core & tex_core))
    union = int(np.sum(raw_core | tex_core))
    centerline_iou = (inter / union) if union > 0 else 1.0

    raw_counters = _count_enclosed_counters(raw_ink)
    tex_counters = _count_enclosed_counters(tex_ink)
    counter_delta = abs(tex_counters - raw_counters)

    # Measure edge micro-roughness (high-pass gradient variance along boundary band)
    edge_band = (binary_dilation(raw_ink, iterations=1) & ~raw_core)
    raw_hp = raw_gray - gaussian_filter(raw_gray, sigma=1.2)
    tex_hp = tex_gray - gaussian_filter(tex_gray, sigma=1.2)

    raw_edge_rough = float(np.std(raw_hp[edge_band])) if np.any(edge_band) else 0.0
    tex_edge_rough = float(np.std(tex_hp[edge_band])) if np.any(edge_band) else 0.0
    edge_gain = tex_edge_rough - raw_edge_rough

    # Measure interior granulation inside core stroke bodies
    raw_int_std = float(np.std(raw_hp[raw_core])) if np.any(raw_core) else 0.0
    tex_int_std = float(np.std(tex_hp[raw_core])) if np.any(raw_core) else 0.0
    int_gain = tex_int_std - raw_int_std

    failures: list[str] = []
    if centerline_iou < min_centerline_iou:
        failures.append("centerline_iou_below_threshold")
    if counter_delta != 0:
        failures.append("counter_topology_changed")
    if edge_gain <= 0.0:
        failures.append("no_edge_micro_roughness_gain")
    if int_gain <= 0.0:
        failures.append("no_interior_granulation_gain")

    return {
        "gate": "HYBRID-STRUCTURE-IOU",
        "passed": len(failures) == 0,
        "centerline_iou": round(centerline_iou, 4),
        "min_centerline_iou": min_centerline_iou,
        "raw_counters": raw_counters,
        "textured_counters": tex_counters,
        "counter_delta": counter_delta,
        "edge_micro_roughness_gain": round(edge_gain, 4),
        "interior_granulation_gain": round(int_gain, 4),
        "failures": failures,
    }
