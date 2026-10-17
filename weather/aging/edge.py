"""Edge darkening, period knife-cut nicks, and two-reader corner curl simulation."""

from __future__ import annotations

import math
import re
import numpy as np
from PIL import Image, ImageFilter

from weather.profile import WeatheringProfile
from weather.substrate.noise import perlin_noise

_FOLIO_RE = re.compile(r"^f?(\d+)([rv])$")


def _parse_folio(folio_id: str) -> tuple[int, str]:
    m = _FOLIO_RE.match(str(folio_id))
    if not m:
        return (1, "r")
    return (int(m.group(1)), m.group(2))


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

        # 6 organic 2D damp/mold stain colonies around the margins with sharp, irregular blotch boundaries
        colonies = [
            (0.01, 0.76, 0.25, 0.32, 0.96),  # deep lower-left water/mold stain
            (0.01, 0.26, 0.16, 0.26, 0.78),  # upper-left margin stain
            (0.32, 0.98, 0.32, 0.17, 0.85),  # bottom margin stain lobe
            (0.98, 0.84, 0.17, 0.24, 0.64),  # lower-right handling stain
            (0.90, 0.03, 0.22, 0.12, 0.58),  # top-right corner oxidation
            (0.10, 0.03, 0.20, 0.13, 0.66),  # top-left corner oxidation
        ]
        colony_field = np.zeros((h, w), dtype=np.float32)
        ring_field = np.zeros((h, w), dtype=np.float32)
        for cx, cy, rx, ry, strength in colonies:
            eff_cx = (1.0 - cx) if is_verso else cx
            dist = np.sqrt(((xg - eff_cx) / rx) ** 2 + ((yg - cy) / ry) ** 2)
            warped_d = dist + 0.42 * n_coarse + 0.26 * n_med + 0.13 * n_fine
            blob = (np.clip((0.92 - warped_d) / 0.55, 0.0, 1.0) ** 0.85) * (0.72 + 0.45 * np.abs(n_med))
            ring = np.exp(-((warped_d - 0.88) / 0.055) ** 2) * (0.65 + 0.55 * np.abs(n_fine))
            colony_field = np.maximum(colony_field, blob * strength)
            ring_field = np.maximum(ring_field, ring * strength)

        organic_mod = np.clip(0.55 + 0.55 * n_coarse + 0.35 * n_med, 0.20, 1.45)
        weight = np.clip(weight * 0.55 * organic_mod + corner_boost * 0.65 + 0.78 * colony_field + 0.52 * ring_field, 0.0, 1.0)
    else:
        weight = np.clip(weight + corner_boost, 0.0, 1.0)

    weight *= min(0.88, ed.opacity * 1.35)

    ec = np.array(ed.color, dtype=np.float32) - np.array([18.0, 20.0, 24.0], dtype=np.float32)
    w3 = np.clip(weight[:, :, np.newaxis], 0.0, 0.88)
    absorb = arr * (ec[None, None, :] / 195.0)
    arr = arr * (1.0 - w3) + (0.68 * absorb + 0.32 * ec[None, None, :]) * w3

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")


def _generate_cut_profile_1d(
    length: int,
    *,
    base_inset_px: float,
    is_irregular_stock: bool,
    n_nicks: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate a 1D knife/plough cut profile with straight baseline, age cockling, and discrete edge nicks."""
    u = np.linspace(0.0, 1.0, length, dtype=np.float32)
    p1 = float(rng.uniform(0.0, 2.0 * math.pi))
    p2 = float(rng.uniform(0.0, 2.0 * math.pi))

    # Overall straight medieval plough/knife trim, with subtle low-frequency vellum shrinkage/cockling
    # On irregular offcut stock (f14r-f17v), add a slight off-square shear and stronger hand-knife wave
    cockle_amp = 6.5 if is_irregular_stock else 2.4
    shear_slope = float(rng.uniform(-9.0, 9.0)) if is_irregular_stock else float(rng.uniform(-2.2, 2.2))
    profile = (
        base_inset_px
        + shear_slope * (u - 0.5)
        + cockle_amp * (0.65 * np.sin(2.0 * math.pi * 1.2 * u + p1) + 0.35 * np.cos(2.0 * math.pi * 2.7 * u + p2))
    )

    # Add correlated sub-millimeter fibrous rawhide edge tooth
    steps = rng.normal(0.0, 0.32, size=length).astype(np.float32)
    walk = np.cumsum(steps)
    if walk.std() > 0:
        walk = (walk - walk.mean()) / walk.std() * (0.95 if is_irregular_stock else 0.55)
    profile += walk

    # Add discrete 560-year edge nicks (sharp V-shaped knife/clasp nicks + broader brittle oxidized chips)
    idx_grid = np.arange(length, dtype=np.float32)
    for k in range(n_nicks):
        center = float(rng.uniform(0.08 * length, 0.92 * length))
        if k % 2 == 0:
            # Sharp V-nick from knife slip, binding clasp, or board edge
            half_w = float(rng.uniform(5.0, 12.0))
            depth = float(rng.uniform(5.5, 13.0 if is_irregular_stock else 9.5))
            dist = np.abs(idx_grid - center) / half_w
            nick = np.clip(1.0 - dist, 0.0, 1.0) ** 1.35 * depth
        else:
            # Broader shallow brittle edge chip / abrasion scallop
            half_w = float(rng.uniform(14.0, 32.0))
            depth = float(rng.uniform(3.8, 8.2))
            dist = np.abs(idx_grid - center) / half_w
            nick = (np.clip(1.0 - dist ** 2, 0.0, 1.0) ** 1.5) * depth
        profile += nick

    return np.clip(profile, 3.0, max(10.0, base_inset_px + 24.0))


def apply_edge_wear_and_corner_curl(
    img: Image.Image,
    folio_id: str = "f01r",
    profile: WeatheringProfile | None = None,
    seed: int = 0,
) -> Image.Image:
    """Simulate 560-year straight-cut vellum edges with nicks, fibrous bevels,
    and slight corner curling at the outer page-turning corners (from ~2 readers).

    Recto/Verso Leaf Coherence:
      - The cut profile and nicks are seeded from the physical leaf number (`leaf_num`)
        and mirrored horizontally on verso (`v`) so front and back of the same leaf
        share the exact same physical contour.
      - The bound spine gutter (left on recto, right on verso) remains flush with the
        binding fold, while the head (top), fore-edge (outer), and tail (bottom) show
        the cut edge, nicks, fibrous bevel, and outer-corner page-turning curls.
    """
    arr = np.array(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    min_dim = float(min(h, w))

    leaf_num, side = _parse_folio(folio_id)
    is_verso = side == "v"
    is_irregular = leaf_num >= 14
    has_missing_lower_right_corner = (leaf_num == 4 and is_verso)

    # Scale physical pixel parameters so the cut edge, nicks, and corner curl are clearly visible
    # both at full-page / spread viewing scale (1282x1767) and in close-up inspection
    scale_f = min_dim / 1280.0
    base_inset = max(4.0, (22.0 if is_irregular else 15.0) * scale_f)

    # Deterministic leaf-level RNG so recto and verso of leaf N share physical nicks
    leaf_rng = np.random.default_rng(seed + leaf_num * 97 + 1457)

    top_prof = _generate_cut_profile_1d(
        w, base_inset_px=base_inset, is_irregular_stock=is_irregular, n_nicks=5 if not is_irregular else 7, rng=leaf_rng
    )
    bot_prof = _generate_cut_profile_1d(
        w, base_inset_px=base_inset, is_irregular_stock=is_irregular, n_nicks=5 if not is_irregular else 7, rng=leaf_rng
    )
    fore_prof = _generate_cut_profile_1d(
        h, base_inset_px=base_inset * 1.12, is_irregular_stock=is_irregular, n_nicks=7 if not is_irregular else 10, rng=leaf_rng
    )

    if is_verso:
        # Mirror top and bottom edge profiles horizontally for the reverse side of the same leaf
        top_prof = top_prof[::-1].copy()
        bot_prof = bot_prof[::-1].copy()

    yg = np.arange(h, dtype=np.float32)[:, np.newaxis]
    xg = np.arange(w, dtype=np.float32)[np.newaxis, :]

    # Distance from the outer fore-edge (right on recto, left on verso) and spine gutter
    dist_fore = (xg if is_verso else (w - 1.0 - xg))
    dist_gutter = ((w - 1.0 - xg) if is_verso else xg)

    # --- Two-Reader Outer Corner Curl Geometry & Shading ---
    # Primary turning corner: lower-outer (bottom-right on recto, bottom-left on verso).
    # Secondary turning corner: upper-outer (top-right on recto, top-left on verso).
    # Note: outermost leaves (f01, f17) and key narrative leaves have slightly stronger curl (~1.15x).
    reader_mult = 1.18 if leaf_num in (1, 4, 5, 7, 14, 17) else 1.0

    r_curl_bot = max(24.0, 145.0 * scale_f * reader_mult)
    r_curl_top = max(18.0, 105.0 * scale_f * reader_mult)

    # Diagonal distance from the lower-outer and upper-outer corners:
    # u_bot = (dist_fore + (h - 1 - y)) / r_curl_bot
    d_bot_y = (h - 1.0 - yg)
    d_top_y = yg

    # Radial and diagonal coordinates in the lower-outer corner
    rad_bot = np.sqrt(dist_fore ** 2 + d_bot_y ** 2)
    diag_bot = (dist_fore + d_bot_y) / math.sqrt(2.0)

    # Radial and diagonal coordinates in the upper-outer corner
    rad_top = np.sqrt(dist_fore ** 2 + d_top_y ** 2)
    diag_top = (dist_fore + d_top_y) / math.sqrt(2.0)

    # 1. Local 2D inward curl warp near the outer corners (pulls vellum fibers slightly toward the curl axis)
    if min_dim >= 160:
        warp_bot = np.clip(1.0 - rad_bot / r_curl_bot, 0.0, 1.0) ** 2 * (7.5 * scale_f)
        if has_missing_lower_right_corner:
            warp_bot[:] = 0.0
        warp_top = np.clip(1.0 - rad_top / r_curl_top, 0.0, 1.0) ** 2 * (5.0 * scale_f)

        dx_sign = -1.0 if is_verso else +1.0
        src_x = np.clip(np.round(xg + dx_sign * (warp_bot + warp_top)).astype(np.int32), 0, w - 1)
        src_y = np.clip(np.round(yg + warp_bot - warp_top).astype(np.int32), 0, h - 1)
        arr = arr[src_y, src_x]

    # 2. Corner tip blunting & upward curl lift recession (rounds the sharp 90° outer corners)
    tip_lift_bot = max(6.0, 32.0 * scale_f * reader_mult)
    tip_lift_top = max(4.0, 22.0 * scale_f * reader_mult)

    # Parabolic corner rounding inset where both dist_fore and d_bot_y (or d_top_y) are small
    c_Span_bot = max(20.0, 118.0 * scale_f)
    c_span_top = max(16.0, 86.0 * scale_f)
    ux_b = np.clip(1.0 - dist_fore / c_Span_bot, 0.0, 1.0)
    uy_b = np.clip(1.0 - d_bot_y / c_Span_bot, 0.0, 1.0)
    corner_recess_bot = (ux_b * uy_b) ** 1.35 * tip_lift_bot
    if has_missing_lower_right_corner:
        corner_recess_bot[:] = 0.0

    ux_t = np.clip(1.0 - dist_fore / c_span_top, 0.0, 1.0)
    uy_t = np.clip(1.0 - d_top_y / c_span_top, 0.0, 1.0)
    corner_recess_top = (ux_t * uy_t) ** 1.35 * tip_lift_top

    # Combine 1D cut profiles + corner curl recession into signed distance `sdf` (>0 inside leaf, <0 outside leaf)
    d_from_top_cut = yg - top_prof[np.newaxis, :] - corner_recess_top
    d_from_bot_cut = (h - 1.0 - yg) - bot_prof[np.newaxis, :] - corner_recess_bot
    d_from_fore_cut = dist_fore - fore_prof[:, np.newaxis] - np.maximum(corner_recess_bot, corner_recess_top)
    # Spine gutter stays 100% flush with the binding fold except for tiny 1-2px vellum fold notches at top/bottom spine ends
    gutter_notch = np.clip(1.0 - yg / max(4.0, 18.0 * scale_f), 0.0, 1.0) * (5.5 * scale_f) + np.clip(
        1.0 - (h - 1.0 - yg) / max(4.0, 18.0 * scale_f), 0.0, 1.0
    ) * (5.5 * scale_f)
    d_from_gutter = dist_gutter + (4.0 * scale_f) - gutter_notch

    sdf = np.minimum(np.minimum(d_from_top_cut, d_from_bot_cut), np.minimum(d_from_fore_cut, d_from_gutter))
    inside_leaf = sdf >= 0.0

    # 3. 3D Corner-Curl Shading on the Vellum Surface (Highlight Ridge + Finger-Pinch Inflection Crease + Thumb Patina)
    for diag_d, rad_d, r_curl, strength, skip in [
        (diag_bot, rad_bot, r_curl_bot, 1.0 * reader_mult, has_missing_lower_right_corner),
        (diag_top, rad_top, r_curl_top, 0.68 * reader_mult, False),
    ]:
        if skip:
            continue
        in_corner = (rad_d < r_curl * 1.25) & inside_leaf
        if not in_corner.any():
            continue
        # Normalized diagonal position u_c in [0, 1.2] from the lifted corner tip inward
        u_c = (diag_d - base_inset * 1.1) / max(1.0, r_curl)
        radial_env = np.clip(1.0 - (rad_d / (r_curl * 1.2)) ** 2, 0.0, 1.0)

        # (a) Convex lifted curl ridge (`u_c ≈ 0.22`): catches oblique top-left light (+24 RGB warm cream lift)
        ridge_lift = np.exp(-((u_c - 0.22) / 0.12) ** 2) * radial_env * strength * 24.0

        # (b) Concave finger-pinch inflection shadow trough (`u_c ≈ 0.54`): where two readers' fingers bent the corner
        pinch_trough = np.exp(-((u_c - 0.54) / 0.15) ** 2) * radial_env * strength * 30.0

        # (c) Faint diagonal collagen stress micro-crease right at the inflection line (`u_c ≈ 0.52`)
        fine_crease = np.exp(-((u_c - 0.52) / 0.028) ** 2) * radial_env * strength * 14.0

        # (d) Subtle two-reader thumb patina (warm sebaceous darkening near the corner tip `u_c < 0.50`)
        thumb_patina = np.clip(1.0 - u_c / 0.55, 0.0, 1.0) * radial_env * strength * 0.14

        delta_lum = (ridge_lift - pinch_trough - fine_crease)[:, :, np.newaxis]
        patina_rgb = np.array([145.0, 116.0, 78.0], dtype=np.float32)
        pw = thumb_patina[:, :, np.newaxis]
        arr = arr * (1.0 - pw) + (arr * (patina_rgb / 205.0)) * pw
        arr = arr + delta_lum * np.array([1.0, 0.94, 0.80], dtype=np.float32)

    # 4. Fibrous Cut-Edge Bevel & Oxidized Rawhide Rim just inside the cut edge (`0 <= sdf <= bevel_w`)
    bevel_w = max(2.0, 4.5 * scale_f)
    bevel_zone = (sdf >= 0.0) & (sdf <= bevel_w) & (dist_gutter > 3.0 * scale_f)
    bevel_t = np.clip(1.0 - sdf / bevel_w, 0.0, 1.0)[:, :, np.newaxis]
    rawhide_rim = np.array([118.0, 92.0, 60.0], dtype=np.float32)
    arr = np.where(bevel_zone[:, :, np.newaxis], arr * (1.0 - 0.58 * bevel_t) + rawhide_rim * (0.58 * bevel_t), arr)

    # 5. Exterior Archival Codex Backing & 3D Drop-Shadow (deeper under the lifted curled corners!)
    # Smooth anti-aliased leaf alpha along `sdf == 0`
    leaf_alpha = np.clip(sdf + 0.65, 0.0, 1.0)[:, :, np.newaxis]

    # Drop shadow extends further out under the lifted lower-outer and upper-outer corners
    corner_lift_boost = (
        np.clip(1.0 - rad_bot / (r_curl_bot * 0.95), 0.0, 1.0) * (8.5 * scale_f) * (0.0 if has_missing_lower_right_corner else 1.0)
        + np.clip(1.0 - rad_top / (r_curl_top * 0.95), 0.0, 1.0) * (5.5 * scale_f)
    )
    shadow_reach = max(2.5, 4.5 * scale_f) + corner_lift_boost
    ext_dist = np.maximum(0.0, -sdf)
    shadow_weight = np.exp(-((ext_dist / shadow_reach) ** 1.6)) * (0.55 + 0.35 * (corner_lift_boost / max(1.0, 8.5 * scale_f)))

    mat_bg = np.array([34.0, 29.0, 25.0], dtype=np.float32)
    shadow_rgb = np.array([12.0, 10.0, 8.0], dtype=np.float32)
    sw = np.clip(shadow_weight[:, :, np.newaxis], 0.0, 0.92)
    ext_rgb = mat_bg[None, None, :] * (1.0 - sw) + shadow_rgb[None, None, :] * sw

    out_arr = leaf_alpha * arr + (1.0 - leaf_alpha) * ext_rgb
    return Image.fromarray(np.clip(out_arr, 0, 255).astype(np.uint8), mode="RGB")
