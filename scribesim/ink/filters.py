"""Ink-substrate interaction filters — post-rasterization image processing.

Each filter operates on a numpy RGB array (H, W, 3) and the pressure
heatmap (H, W) uint8. Filters are composable and individually disableable
by setting their strength parameter to 0.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d

from scribesim.hand.profile import HandProfile
from scribesim.layout.positioned import PageLayout


# ---------------------------------------------------------------------------
# Ink detection helper
# ---------------------------------------------------------------------------

# Parchment background (must match rasteriser)
_PARCHMENT = np.array([245, 238, 220], dtype=np.float32)
_INK_THRESHOLD = 30.0  # L2 distance from parchment to count as "ink"


def _ink_mask(img_arr: np.ndarray) -> np.ndarray:
    """Boolean mask: True where pixel is ink (significantly darker than parchment)."""
    diff = np.linalg.norm(img_arr.astype(np.float32) - _PARCHMENT, axis=2)
    return diff > _INK_THRESHOLD


# ---------------------------------------------------------------------------
# Filter 1: Ink Saturation
# ---------------------------------------------------------------------------

def ink_saturation(img_arr: np.ndarray, heat_arr: np.ndarray,
                   profile: HandProfile) -> np.ndarray:
    """Modulate ink darkness by pressure — high pressure = darker ink.

    Uses the pressure heatmap as a proxy for per-pixel pressure.
    Strength controlled by ink.fresh_dip_darkness_boost (0 = no effect).
    """
    boost = profile.ink.fresh_dip_darkness_boost
    if boost <= 0:
        return img_arr

    mask = _ink_mask(img_arr)
    if not mask.any():
        return img_arr

    arr = img_arr.astype(np.float32)
    # Normalise heatmap to [0, 1]
    heat_norm = heat_arr.astype(np.float32) / 255.0

    # Darken ink pixels proportionally to pressure
    # factor < 1.0 = darker; factor at max pressure = (1 - boost)
    factor = 1.0 - boost * heat_norm
    factor = np.clip(factor, 0.3, 1.0)

    # Apply only to ink pixels
    for c in range(3):
        arr[:, :, c] = np.where(mask, arr[:, :, c] * factor, arr[:, :, c])

    return np.clip(arr, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Filter 2: Ink Pooling
# ---------------------------------------------------------------------------

def ink_pooling(img_arr: np.ndarray, heat_arr: np.ndarray,
                profile: HandProfile) -> np.ndarray:
    """Darken stroke termination points where ink pools.

    Detects high-pressure pixels adjacent to non-ink regions (stroke ends)
    and applies a darkening blob. Strength controlled by
    material.pooling_at_direction_change.
    """
    strength = profile.material.pooling_at_direction_change
    if strength <= 0:
        return img_arr

    mask = _ink_mask(img_arr)
    if not mask.any():
        return img_arr

    # Find edge pixels: ink pixel with at least one non-ink neighbour
    from scipy.ndimage import binary_erosion
    interior = binary_erosion(mask, iterations=1)
    edge = mask & ~interior

    # High-pressure edges are stroke terminations
    high_pressure = heat_arr > 100
    terminations = edge & high_pressure

    if not terminations.any():
        return img_arr

    # Create pooling darkening map: blur the termination points
    pool_map = terminations.astype(np.float32)
    pool_map = gaussian_filter(pool_map, sigma=2.0)
    pool_map = pool_map / (pool_map.max() + 1e-8) * strength

    arr = img_arr.astype(np.float32)
    # Darken: multiply by (1 - pool_map) on ink pixels
    factor = 1.0 - pool_map
    factor = np.clip(factor, 0.3, 1.0)
    for c in range(3):
        arr[:, :, c] = np.where(mask, arr[:, :, c] * factor, arr[:, :, c])

    return np.clip(arr, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Filter 3: Vellum Grain Wicking
# ---------------------------------------------------------------------------

def vellum_wicking(img_arr: np.ndarray, heat_arr: np.ndarray,
                   profile: HandProfile) -> np.ndarray:
    """Anisotropic blur along vellum grain direction (roughly vertical).

    Calfskin grain runs roughly vertical. Ink wicks along the grain more
    than across it. Strength controlled by material.grain_spread_factor.
    """
    spread = profile.material.grain_spread_factor
    if spread <= 0:
        return img_arr

    mask = _ink_mask(img_arr)
    if not mask.any():
        return img_arr

    arr = img_arr.astype(np.float32)

    # Anisotropic blur: more along y (vertical grain) than x
    sigma_y = spread * 4.0   # along grain
    sigma_x = spread * 1.5   # across grain

    # Only blur ink pixels — blend with original based on mask
    blurred = np.empty_like(arr)
    for c in range(3):
        blurred[:, :, c] = gaussian_filter(arr[:, :, c], sigma=[sigma_y, sigma_x])

    # Apply blur only where ink exists (with soft transition)
    mask_float = mask.astype(np.float32)
    mask_soft = gaussian_filter(mask_float, sigma=1.0)
    mask_soft = mask_soft[:, :, np.newaxis]

    result = arr * (1.0 - mask_soft) + blurred * mask_soft
    return np.clip(result, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Filter 4: Hairline Feathering
# ---------------------------------------------------------------------------

def hairline_feathering(img_arr: np.ndarray, heat_arr: np.ndarray,
                        profile: HandProfile) -> np.ndarray:
    """Soften edges of thin strokes (low pressure = more feathering).

    Heavy strokes keep crisp edges; hairlines get soft, slightly irregular
    edges. Strength controlled by material.edge_feather_mm.
    """
    feather = profile.material.edge_feather_mm
    if feather <= 0:
        return img_arr

    mask = _ink_mask(img_arr)
    if not mask.any():
        return img_arr

    arr = img_arr.astype(np.float32)

    # Feathering sigma inversely proportional to local pressure
    # Low pressure (thin strokes) → more blur; high pressure → less blur
    heat_norm = heat_arr.astype(np.float32) / 255.0
    heat_norm = np.clip(heat_norm, 0.01, 1.0)

    # Apply variable blur: use a single moderate blur, then blend based on pressure
    sigma = feather * 15.0  # scale mm to pixel-appropriate sigma
    blurred = np.empty_like(arr)
    for c in range(3):
        blurred[:, :, c] = gaussian_filter(arr[:, :, c], sigma=sigma)

    # Blend: low pressure → more blurred, high pressure → keep original
    # blend_factor = 1 means use blurred, 0 means use original
    blend = np.clip(1.0 - heat_norm * 2.0, 0.0, 0.5)  # max 50% blur
    blend = blend[:, :, np.newaxis]

    # Only apply on ink mask
    mask3 = mask[:, :, np.newaxis].astype(np.float32)
    result = arr * (1.0 - blend * mask3) + blurred * blend * mask3
    return np.clip(result, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Filter 5: Ink Depletion Cycle
# ---------------------------------------------------------------------------

def ink_depletion(img_arr: np.ndarray, heat_arr: np.ndarray,
                  layout: PageLayout, profile: HandProfile) -> np.ndarray:
    """Apply periodic ink darkness modulation across the page.

    The scribe dips the quill every ~35 words. After a dip, ink is rich
    and dark; before the next dip, it thins. This creates a visible
    periodic rhythm. Strength controlled by ink.depletion_rate.
    """
    rate = profile.ink.depletion_rate
    if rate <= 0:
        return img_arr

    mask = _ink_mask(img_arr)
    if not mask.any():
        return img_arr

    arr = img_arr.astype(np.float32)
    h, w = arr.shape[:2]

    # Count words per line from layout
    cycle_length = 35  # words per dip cycle
    word_count = 0
    px_per_mm = w / layout.geometry.page_w_mm if layout.geometry.page_w_mm > 0 else 1.0

    for line_layout in layout.lines:
        # Count spaces in glyph sequence as word boundaries
        line_words = 1
        prev_x = None
        median_adv = 3.0  # default
        if line_layout.glyphs:
            advs = [g.advance_w_mm for g in line_layout.glyphs]
            median_adv = float(np.median(advs)) if advs else 3.0

        for gi, pg in enumerate(line_layout.glyphs):
            if prev_x is not None:
                gap = pg.x_mm - prev_x
                if gap > median_adv * 1.5:
                    line_words += 1
            prev_x = pg.x_mm + pg.advance_w_mm

        # Compute depletion factor for this line
        # Position in current dip cycle [0, 1]
        cycle_pos = (word_count % cycle_length) / cycle_length
        # Depletion: darker at start of cycle (just dipped), lighter at end
        # ink_remaining = 1.0 - (cycle_pos)^1.5  (from TD-002)
        ink_remaining = 1.0 - (cycle_pos ** 1.5) * rate * 10.0
        ink_remaining = max(0.6, min(1.0, ink_remaining))

        # Apply to all ink pixels on this line's y-range
        if line_layout.glyphs:
            y_top = int(line_layout.y_mm * px_per_mm)
            y_bot = int((line_layout.y_mm + layout.geometry.ruling_pitch_mm) * px_per_mm)
            y_top = max(0, min(h - 1, y_top))
            y_bot = max(0, min(h, y_bot))

            line_mask = mask[y_top:y_bot, :]
            if line_mask.any():
                # Lighten ink by reducing distance from parchment
                for c in range(3):
                    ink_vals = arr[y_top:y_bot, :, c]
                    parch_val = _PARCHMENT[c]
                    # Move ink color toward parchment by (1 - ink_remaining)
                    arr[y_top:y_bot, :, c] = np.where(
                        line_mask,
                        parch_val + (ink_vals - parch_val) * ink_remaining,
                        ink_vals,
                    )

        word_count += line_words

    return np.clip(arr, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def apply_ink_filters(img_arr: np.ndarray, heat_arr: np.ndarray,
                      layout: PageLayout, profile: HandProfile) -> np.ndarray:
    """Apply all 5 ink-substrate filters in sequence.

    Args:
        img_arr:  RGB image array (H, W, 3) uint8.
        heat_arr: Pressure heatmap array (H, W) uint8.
        layout:   PageLayout for word counting (depletion cycle).
        profile:  HandProfile with ink/material params.

    Returns:
        Filtered RGB image array (H, W, 3) uint8.
    """
    arr = img_arr.copy()
    arr = ink_saturation(arr, heat_arr, profile)
    arr = ink_pooling(arr, heat_arr, profile)
    arr = vellum_wicking(arr, heat_arr, profile)
    arr = hairline_feathering(arr, heat_arr, profile)
    arr = ink_depletion(arr, heat_arr, layout, profile)
    return arr
