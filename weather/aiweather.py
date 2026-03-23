"""AI Weathering Execution Pipeline — TD-011 Parts 4 and 7.

Ties together: codex map lookup → word pre-degradation → prompt generation
→ AI image model API call → provenance recording.

Folios are processed in gathering order (epicenter-first: f04r, f04v, then
outward) so that each folio's coherence context can include already-weathered
adjacent pages as reference images.

Public API:
    generate_gathering_order(weathering_map) -> list[str]
    weather_folio(...) -> WeatheredResult
    weather_codex(...) -> dict[str, WeatheredResult]
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np

from weather.promptgen import (
    FolioWeatherSpec,
    WordDamageEntry,
    CoherenceContext,
    build_coherence_context,
    generate_background_prompt,
    generate_weathering_prompt,
)
from weather.worddegrade import pre_degrade_text


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class WeatheredResult:
    folio_id: str
    image: np.ndarray          # uint8 RGB, weathered output
    prompt: str
    provenance_path: Path


# ---------------------------------------------------------------------------
# Gathering order
# ---------------------------------------------------------------------------

# Canonical folio sequence for 17-leaf gathering: f01r..f17v (34 sides)
_ALL_FOLIOS = [f"f{n:02d}{s}" for n in range(1, 18) for s in ("r", "v")]

# Epicenter leaf is 4 (f04r/f04v). Outward ordering by leaf distance.
_EPICENTER_LEAF = 4
_LEAF_ORDER = sorted(range(1, 18), key=lambda n: (abs(n - _EPICENTER_LEAF), n))


def generate_gathering_order(weathering_map: dict[str, FolioWeatherSpec]) -> list[str]:
    """Return folio IDs in epicenter-first gathering order.

    f04r comes first, then f04v, then outward by leaf distance from leaf 4.
    Within each leaf the recto precedes the verso.
    Only returns folios present in weathering_map.
    """
    order = []
    for leaf in _LEAF_ORDER:
        for side in ("r", "v"):
            fid = f"f{leaf:02d}{side}"
            if fid in weathering_map:
                order.append(fid)
    return order


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def _compute_seed(folio_id: str, seed_base: int) -> int:
    return hash((folio_id, seed_base)) % (2 ** 32)


# ---------------------------------------------------------------------------
# OpenAI adapter
# ---------------------------------------------------------------------------

_PARCHMENT_COLOR = (230, 215, 185)   # warm cream — matches ScribeSim background


def _openai_apply_weathering(
    pre_degraded: np.ndarray,
    background_prompt: str,
    reference_images: list[np.ndarray],
    seed: int,
    model: str = "gpt-image-1",
) -> np.ndarray:
    """Generate an aged parchment background via AI, then darken-blend the rendered
    text on top.

    Two-step approach that guarantees letterform preservation:
      1. Send a BLANK parchment canvas to gpt-image-1 with a background-only prompt.
         The model sees no text, so it cannot regenerate or alter letterforms.
      2. Darken-blend (np.minimum per channel) the pre-degraded text render onto the
         aged background. Dark ink pixels always win; the aged parchment shows through
         wherever the canvas is lighter than the background.
    """
    import io
    import base64
    import openai
    from PIL import Image as PILImage

    client = openai.OpenAI()
    orig_h, orig_w = pre_degraded.shape[:2]

    # Build a blank parchment canvas — same dimensions as the folio render
    blank = PILImage.new("RGB", (orig_w, orig_h), _PARCHMENT_COLOR)
    buf = io.BytesIO()
    blank.save(buf, format="PNG")
    buf.seek(0)

    response = client.images.edit(
        model=model,
        image=("image.png", buf, "image/png"),
        prompt=background_prompt,
        n=1,
        size="auto",
    )

    # Decode response — b64_json (gpt-image-1 default) or URL fallback
    b64 = response.data[0].b64_json
    if b64:
        img_bytes = base64.b64decode(b64)
    else:
        import urllib.request
        url = response.data[0].url
        with urllib.request.urlopen(url) as r:
            img_bytes = r.read()

    aged_bg = PILImage.open(io.BytesIO(img_bytes)).convert("RGB")
    if aged_bg.size != (orig_w, orig_h):
        aged_bg = aged_bg.resize((orig_w, orig_h), PILImage.LANCZOS)

    aged_bg_arr = np.array(aged_bg, dtype=np.uint8)

    # Darken blend: take the minimum per channel.
    # Ink strokes (dark pixels in pre_degraded) always dominate over the background.
    # Parchment areas (light pixels) let the aged texture show through.
    return np.minimum(pre_degraded, aged_bg_arr), aged_bg_arr


# ---------------------------------------------------------------------------
# Ink aging (post-composite)
# ---------------------------------------------------------------------------

def _apply_ink_aging(
    composited: np.ndarray,
    ink_source: np.ndarray,
    aged_bg: np.ndarray,
    folio_spec: "FolioWeatherSpec",
) -> np.ndarray:
    """Apply 500-year iron gall aging to ink pixels after darken-blend compositing.

    Two effects:
      1. Global color shift — all ink pixels shifted from black toward warm
         reddish-brown (iron gall oxidises over centuries: RGB ~(65, 32, 10)).
      2. Water damage fade — in the water zone, ink pixels are additionally
         blended toward the local aged background colour, proportional to
         severity and proximity to the origin corner.

    Args:
        composited: darken-blended result (text on aged background), uint8 RGB
        ink_source:  pre_degraded render — used to locate ink pixels reliably
        aged_bg:     AI-generated aged background — used as blend target in fade zones
        folio_spec:  weathering spec for water damage parameters
    """
    result = composited.astype(np.float32)

    # ── Ink mask ─────────────────────────────────────────────────────────────
    # Detect ink using the pre_degraded source (known-clean black strokes).
    lum = (0.299 * ink_source[..., 0].astype(np.float32)
         + 0.587 * ink_source[..., 1].astype(np.float32)
         + 0.114 * ink_source[..., 2].astype(np.float32))  # (H, W)
    INK_THRESH = 150.0
    ink_mask = lum < INK_THRESH                             # (H, W) bool

    # Darkness factor: 1.0 at pure black, 0.0 at the threshold boundary
    darkness = np.clip(1.0 - lum / INK_THRESH, 0.0, 1.0)  # (H, W)

    # ── 1. Iron gall color shift ──────────────────────────────────────────────
    # Interpolate each ink pixel from its current (near-black) colour toward
    # the target 500-year-aged iron gall brown.  Darker pixels get more shift.
    AGED_INK = np.array([65.0, 32.0, 10.0], dtype=np.float32)  # warm reddish-brown

    d = darkness[ink_mask, None]            # (N, 1)
    pix = result[ink_mask]                  # (N, 3)
    result[ink_mask] = np.clip(pix * (1.0 - d) + AGED_INK * d, 0.0, 255.0)

    # ── 2. Water damage ink fading ────────────────────────────────────────────
    if folio_spec.water_damage:
        wd = folio_spec.water_damage
        h, w = composited.shape[:2]

        # Normalised coordinate grids
        ys = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]  # (H, 1)
        xs = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]  # (1, W)

        # Signed distance from the near edge (0 = that edge, 1 = far edge)
        near_y = ys if "top" in wd.origin else (1.0 - ys)
        near_x = (1.0 - xs) if "right" in wd.origin else xs

        # Within-zone fraction: 0 at origin corner, 1 at tide-line boundary
        # We blend the two axes so the effect is strongest at the corner
        edge_dist = (near_y + 0.5 * near_x) / 1.5      # weighted average
        zone_frac = np.clip(edge_dist / max(wd.penetration, 1e-4), 0.0, 1.0)

        in_zone = zone_frac < 1.0                        # (H, W) bool

        # Fade strength: peaks at corner, tapers to zero at the tide line
        fade = np.clip(wd.severity * (1.0 - zone_frac) * 0.8, 0.0, 0.7)

        water_ink = ink_mask & in_zone
        if water_ink.any():
            f = fade[water_ink, None]                    # (N, 1)
            bg = aged_bg[water_ink].astype(np.float32)   # local background colour
            result[water_ink] = np.clip(
                result[water_ink] * (1.0 - f) + bg * f,
                0.0, 255.0,
            )

    return result.clip(0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------------------------

def _with_retry(fn, max_attempts: int = 3, backoff_base: float = 2.0):
    """Call fn(), retrying up to max_attempts on rate-limit / transient errors."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                sleep_s = backoff_base ** attempt  # 1s, 2s, 4s  (base^0, base^1, base^2)
                time.sleep(sleep_s)
    raise last_exc


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

def _write_provenance(
    folio_id: str,
    prompt: str,
    spec: FolioWeatherSpec,
    coherence_refs: list[str],
    seed: int,
    model: str,
    method: str,
    output_dir: Path,
) -> Path:
    record = {
        "folio_id": folio_id,
        "method": method,
        "model": model,
        "prompt": prompt,
        "seed": seed,
        "weathering_spec": {
            "vellum_stock": spec.vellum_stock,
            "edge_darkening": spec.edge_darkening,
            "gutter_side": spec.gutter_side,
            "water_damage": (
                {
                    "severity": spec.water_damage.severity,
                    "origin": spec.water_damage.origin,
                    "penetration": spec.water_damage.penetration,
                }
                if spec.water_damage
                else None
            ),
            "missing_corner": (
                {
                    "corner": spec.missing_corner.corner,
                    "depth_fraction": spec.missing_corner.depth_fraction,
                    "width_fraction": spec.missing_corner.width_fraction,
                }
                if spec.missing_corner
                else None
            ),
            "foxing_spots": len(spec.foxing_spots),
        },
        "coherence_references": coherence_refs,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    path = output_dir / f"{folio_id}_provenance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False))
    return path


# ---------------------------------------------------------------------------
# weather_folio
# ---------------------------------------------------------------------------

def weather_folio(
    folio_id: str,
    clean_image: np.ndarray,
    folio_spec: FolioWeatherSpec,
    word_damage_map: list[WordDamageEntry],
    weathering_map: dict[str, FolioWeatherSpec],
    weathered_so_far: dict[str, np.ndarray],
    output_dir: Path,
    model: str = "gpt-image-1",
    seed_base: int = 1457,
    dry_run: bool = False,
) -> WeatheredResult:
    """Weather one folio: pre-degrade → prompt → AI → provenance.

    Args:
        folio_id:       e.g. "f04r"
        clean_image:    uint8 RGB numpy array from ScribeSim render
        folio_spec:     FolioWeatherSpec for this folio
        word_damage_map: list of WordDamageEntry for this folio (may be empty)
        weathering_map: full codex weathering map (for coherence context)
        weathered_so_far: {folio_id: image} of already-weathered folios
        output_dir:     directory to write prompt, image, and provenance files
        model:          AI model name (ignored in dry_run)
        seed_base:      base seed; per-folio seed derived from (folio_id, seed_base)
        dry_run:        if True, skip API call; output image = pre-degraded input

    Returns:
        WeatheredResult with image, prompt, and provenance_path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    seed = _compute_seed(folio_id, seed_base)

    # Step 1: Word-level pre-degradation
    pre_degraded, _mask = pre_degrade_text(clean_image, word_damage_map, seed=seed)

    # Step 2: Build coherence context
    context: CoherenceContext = build_coherence_context(
        folio_id, weathering_map, weathered_so_far=weathered_so_far
    )

    # Step 3: Generate prompts
    h, w = clean_image.shape[:2]
    # Full prompt — saved to file for provenance/debugging
    prompt = generate_weathering_prompt(
        folio_spec, context, word_damage_map=word_damage_map,
        page_width=w, page_height=h,
    )
    # Background prompt — sent to AI; describes physical aging on blank parchment,
    # no text preservation language (text is composited programmatically instead)
    bg_prompt = generate_background_prompt(folio_spec, context)

    prompt_path = output_dir / f"{folio_id}_prompt.txt"
    prompt_path.write_text(prompt)

    # Step 4: Apply AI weathering (or dry_run copy)
    if dry_run:
        result_image = pre_degraded.copy()
        method = "dry_run"
    else:
        reference_images = [
            adj_image
            for adj in context.adjacent_folios
            if (adj_image := weathered_so_far.get(adj.folio_id)) is not None
        ]
        composited, aged_bg = _with_retry(
            lambda: _openai_apply_weathering(
                pre_degraded, bg_prompt, reference_images, seed, model
            )
        )
        result_image = _apply_ink_aging(composited, pre_degraded, aged_bg, folio_spec)
        method = "openai"

    # Step 5: Write provenance
    coherence_refs = [adj.folio_id for adj in context.adjacent_folios]
    prov_path = _write_provenance(
        folio_id, prompt, folio_spec, coherence_refs, seed, model, method, output_dir
    )

    return WeatheredResult(
        folio_id=folio_id,
        image=result_image,
        prompt=prompt,
        provenance_path=prov_path,
    )


# ---------------------------------------------------------------------------
# weather_codex
# ---------------------------------------------------------------------------

def weather_codex(
    clean_images: dict[str, np.ndarray],
    weathering_map: dict[str, FolioWeatherSpec],
    word_damage_maps: dict[str, list[WordDamageEntry]],
    output_dir: Path | str,
    model: str = "gpt-image-1",
    seed_base: int = 1457,
    dry_run: bool = False,
) -> dict[str, WeatheredResult]:
    """Process all folios in gathering order.

    Args:
        clean_images:    {folio_id: uint8 RGB array} from ScribeSim
        weathering_map:  {folio_id: FolioWeatherSpec} for all folios
        word_damage_maps: {folio_id: list[WordDamageEntry]} (empty list if none)
        output_dir:      root directory for all output files
        model:           AI model identifier (ignored in dry_run)
        seed_base:       base seed for deterministic per-folio seeds
        dry_run:         if True, skip all API calls

    Returns:
        {folio_id: WeatheredResult} in processing order.
    """
    output_dir = Path(output_dir)
    order = generate_gathering_order(weathering_map)
    weathered_so_far: dict[str, np.ndarray] = {}
    results: dict[str, WeatheredResult] = {}

    for folio_id in order:
        if folio_id not in clean_images:
            continue
        result = weather_folio(
            folio_id=folio_id,
            clean_image=clean_images[folio_id],
            folio_spec=weathering_map[folio_id],
            word_damage_map=word_damage_maps.get(folio_id, []),
            weathering_map=weathering_map,
            weathered_so_far=weathered_so_far,
            output_dir=output_dir,
            model=model,
            seed_base=seed_base,
            dry_run=dry_run,
        )
        weathered_so_far[folio_id] = result.image
        results[folio_id] = result

    return results
