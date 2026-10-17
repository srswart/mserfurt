"""Edge darkening — organic 2D radial-and-lobate marginal dampness, mold stains, and codex handling."""

from __future__ import annotations

import numpy as np
from PIL import Image

from weather.profile import WeatheringProfile
from weather.substrate.noise import perlin_noise


def apply_edge_darkening(
    img: Image.Image,
    profile: WeatheringProfile,
    folio_id: str = "f01r",
    seed: int = 0,
) -> Image.Image:
    """Apply organic, mottled edge darkening and irregular 2D marginal damp/mold stains."""
    ed = profile.aging_edge
    if not ed.enabled:
        return img.copy()

    arr = np.array(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]

    edge_w = max(1, int(w * ed.width_fraction))
    edge_h = max(1, int(h * ed.width_fraction))

    weight = np.zeros((h, w), dtype=np.float32)

    rows = np.arange(min(edge_h, h), dtype=np.float32)
    weight[: len(rows), :] = np.maximum(weight[: len(rows), :], (1.0 - rows / edge_h)[:, np.newaxis])
    weight[h - 1 - rows.astype(int), :] = np.maximum(
        weight[h - 1 - rows.astype(int), :], (1.0 - rows / edge_h)[:, np.newaxis]
    )

    cols = np.arange(min(edge_w, w), dtype=np.float32)
    weight[:, : len(cols)] = np.maximum(weight[:, : len(cols)], (1.0 - cols / edge_w)[np.newaxis, :])
    weight[:, w - 1 - cols.astype(int)] = np.maximum(
        weight[:, w - 1 - cols.astype(int)], (1.0 - cols / edge_w)[np.newaxis, :]
    )

    top_f = np.clip(1.0 - np.arange(h, dtype=np.float32) / max(1.0, h * 0.22), 0.0, 1.0)[:, np.newaxis]
    bot_f = np.clip(1.0 - (h - 1 - np.arange(h, dtype=np.float32)) / max(1.0, h * 0.22), 0.0, 1.0)[:, np.newaxis]
    left_f = np.clip(1.0 - np.arange(w, dtype=np.float32) / max(1.0, w * 0.22), 0.0, 1.0)[np.newaxis, :]
    right_f = np.clip(1.0 - (w - 1 - np.arange(w, dtype=np.float32)) / max(1.0, w * 0.22), 0.0, 1.0)[np.newaxis, :]

    corner_boost = 0.42 * (top_f * left_f + top_f * right_f + bot_f * left_f + bot_f * right_f)

    min_dim = float(min(h, w))
    if min_dim >= 320:
        is_verso = str(folio_id).endswith("v")
        n_coarse = perlin_noise(w, h, scale=max(18.0, min_dim * 0.14), octaves=3, seed=seed + 503)
        n_med = perlin_noise(w, h, scale=max(6.0, min_dim * 0.042), octaves=3, seed=seed + 607)
        n_fine = perlin_noise(w, h, scale=max(2.2, min_dim * 0.013), octaves=3, seed=seed + 709)
        if is_verso:
            n_coarse = np.fliplr(n_coarse)
            n_med = np.fliplr(n_med)
            n_fine = np.fliplr(n_fine)

        yg = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, np.newaxis]
        xg = np.linspace(0.0, 1.0, w, dtype=np.float32)[np.newaxis, :]

        # 6 organic 2D damp/mold stain colonies around the margins with high-contrast tide rings
        colonies = [
            (0.02, 0.78, 0.24, 0.30, 0.92),  # deep lower-left water/mold stain
            (0.01, 0.30, 0.17, 0.26, 0.72),  # upper-left margin stain
            (0.30, 0.97, 0.30, 0.18, 0.80),  # bottom margin stain lobe
            (0.97, 0.82, 0.20, 0.26, 0.68),  # lower-right handling stain
            (0.88, 0.04, 0.24, 0.15, 0.62),  # top-right corner oxidation
            (0.12, 0.03, 0.22, 0.14, 0.64),  # top-left corner oxidation
        ]
        colony_field = np.zeros((h, w), dtype=np.float32)
        ring_field = np.zeros((h, w), dtype=np.float32)
        for cx, cy, rx, ry, strength in colonies:
            eff_cx = (1.0 - cx) if is_verso else cx
            dist = np.sqrt(((xg - eff_cx) / rx) ** 2 + ((yg - cy) / ry) ** 2)
            warped_d = dist + 0.38 * n_coarse + 0.22 * n_med + 0.11 * n_fine
            blob = (np.clip(1.0 - warped_d, 0.0, 1.0) ** 1.25) * (0.78 + 0.38 * n_med)
            ring = np.exp(-((warped_d - 0.86) / 0.075) ** 2) * (0.55 + 0.45 * np.abs(n_fine))
            colony_field = np.maximum(colony_field, blob * strength)
            ring_field = np.maximum(ring_field, ring * strength)

        organic_mod = np.clip(0.70 + 0.48 * n_coarse + 0.32 * n_med, 0.30, 1.45)
        weight = np.clip(weight * organic_mod + corner_boost + 0.72 * colony_field + 0.48 * ring_field, 0.0, 1.0)
    else:
        weight = np.clip(weight + corner_boost, 0.0, 1.0)

    weight *= min(0.88, ed.opacity * 1.35)

    # Rich burnt-umber stain pigment matching the reference dark margin stains (~[138, 112, 74])
    ec = np.array(ed.color, dtype=np.float32) - np.array([18.0, 20.0, 24.0], dtype=np.float32)
    w3 = np.clip(weight[:, :, np.newaxis], 0.0, 0.88)
    absorb = arr * (ec[None, None, :] / 195.0)
    arr = arr * (1.0 - w3) + (0.68 * absorb + 0.32 * ec[None, None, :]) * w3

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")
