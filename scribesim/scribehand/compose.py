"""Neural page composition (TD-018 §2.5).

Places HTR-verified word strips onto the folio page:

- page geometry, ruling, and gutter side come from the existing layout stack
  (`scribesim.layout.geometry`)
- movement realism (baseline undulation, per-word offsets, margin drift) is
  applied at word placement, seeded deterministically
- strips are scaled so the strip x-height matches the page x-height, then
  alpha-composited as sepia ink over parchment
- word bounding boxes are recorded exactly — Weather's word-level
  pre-degradation and the PAGE XML writer consume them
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

from scribesim.layout.geometry import PageGeometry, make_geometry
from scribesim.scribehand.generate import WordGenerator
from scribesim.scribehand.modifiers import controls_from_profile
from scribesim.scribehand.seeds import word_seed
from scribesim.scribehand.types import WordRequest, WordResult
from scribesim.scribehand.verify import verify_words

_PARCHMENT = (245, 238, 220)
_INK = (48, 28, 12)   # warm iron-gall sepia

_LACUNA_OPACITY = {
    "water_damage": 0.35,
    "ink_fade": 0.50,
    "physical_loss": 0.05,
    "missing": 0.05,
}


class ComposeError(RuntimeError):
    """Raised when composition cannot proceed (e.g. unverified words)."""


@dataclass
class PlacedWord:
    text: str
    x_px: int
    y_px: int
    w_px: int
    h_px: int
    baseline_y_px: int
    provenance: dict = field(default_factory=dict)


@dataclass
class ComposedLine:
    line_index: int
    text: str
    baseline_y_px: int
    words: list[PlacedWord] = field(default_factory=list)


@dataclass
class ComposedFolio:
    folio_id: str
    page: np.ndarray                 # (H, W, 3) uint8 RGB
    geometry: PageGeometry
    dpi: float
    lines: list[ComposedLine] = field(default_factory=list)
    report: dict = field(default_factory=dict)


def _line_lacuna_opacity(annotations: list[dict]) -> float:
    """Minimum lacuna opacity over the line's annotations (1.0 = intact)."""
    opacity = 1.0
    for ann in annotations or []:
        if ann.get("type") != "lacuna":
            continue
        reason = ann.get("detail", {}).get("reason", "unknown")
        opacity = min(opacity, _LACUNA_OPACITY.get(reason, 0.40))
    return opacity


def compose_folio(
    folio_dict: dict,
    profile,
    generator: WordGenerator,
    scorer=None,
    dpi: float = 300.0,
    base_seed: int = 1457,
    cer_threshold: float = 0.05,
    max_retries: int = 3,
    allow_unverified: bool = False,
) -> ComposedFolio:
    """Compose a full folio page from generated word strips."""
    folio_id = folio_dict["id"]
    params = profile.to_v1()
    geom = make_geometry(folio_id, params)
    controls = controls_from_profile(profile)

    px_per_mm = dpi / 25.4
    page_w_px = int(geom.page_w_mm * px_per_mm)
    page_h_px = int(geom.page_h_mm * px_per_mm)

    side = folio_id[-1]
    margin_left_mm = geom.margin_inner if side == "r" else geom.margin_outer
    text_right_mm = margin_left_mm + geom.text_w_mm

    x_height_mm = geom.x_height_mm * controls.x_height_scale
    word_gap_mm = max(
        x_height_mm * 0.30,
        x_height_mm * 0.30 * profile.word.spacing_mean_ratio,
    )
    min_gap_mm = x_height_mm * 0.12

    # ---- build word requests for the whole folio --------------------------
    lines_data = folio_dict.get("lines", [])[: geom.ruling_count or None]
    requests: list[WordRequest] = []
    line_word_spans: list[tuple[int, int]] = []   # request index range per line
    for li, line in enumerate(lines_data):
        words = line.get("text", "").split()
        start = len(requests)
        for wi, word in enumerate(words):
            requests.append(WordRequest(
                text=word,
                seed=word_seed(base_seed, folio_id, li, wi),
                folio_id=folio_id,
                line_index=li,
                word_index=wi,
                controls=controls.to_dict(),
            ))
        line_word_spans.append((start, len(requests)))

    # ---- generate (+ verify) ----------------------------------------------
    if scorer is not None:
        results = verify_words(
            generator, scorer, requests,
            cer_threshold=cer_threshold, max_retries=max_retries,
            base_seed=base_seed,
        )
        unverified = [r for r in results if not r.provenance.get("verified")]
        if unverified and not allow_unverified:
            sample = ", ".join(r.provenance["text"] for r in unverified[:5])
            raise ComposeError(
                f"{len(unverified)} word(s) failed HTR verification "
                f"(e.g. {sample}) — fix generation or pass allow_unverified"
            )
    else:
        results = generator.generate(requests)
        unverified = []

    # ---- movement (seeded, deterministic) ---------------------------------
    rng = np.random.default_rng(base_seed + hash_stable(folio_id))
    n_lines = len(lines_data)
    line_start_jitter = rng.normal(0, profile.line.start_x_variance_mm, size=max(1, n_lines))
    line_phases = rng.uniform(0, 2 * math.pi, size=max(1, n_lines))
    margin_drift_per_line = (
        profile.folio.margin_left_variance_mm / max(1, n_lines - 1) if n_lines > 1 else 0.0
    )

    # ---- composite ----------------------------------------------------------
    page = np.full((page_h_px, page_w_px, 3), _PARCHMENT, dtype=np.uint8)
    composed_lines: list[ComposedLine] = []
    cache_hits = 0

    for li, line in enumerate(lines_data):
        start, end = line_word_spans[li]
        line_results = results[start:end]
        words = [r.provenance["text"] for r in line_results]
        if not words:
            continue

        baseline_y_mm = geom.ruling_y(li) + geom.x_height_mm
        lacuna_opacity = _line_lacuna_opacity(line.get("annotations", []))

        # natural widths at page scale
        scales, widths_mm = [], []
        for res in line_results:
            strip = res.strip
            strip_xheight_px = max(1.0, strip.xheight_frac * strip.height)
            scale = (x_height_mm * px_per_mm) / strip_xheight_px
            scales.append(scale)
            widths_mm.append(strip.width * scale / px_per_mm)

        # fit: compress gaps first, then apply a bounded horizontal squeeze
        # (scribes compress letterforms approaching the margin)
        n_gaps = max(1, len(words) - 1)
        natural = sum(widths_mm) + n_gaps * word_gap_mm
        available = text_right_mm - margin_left_mm
        gap_mm = word_gap_mm
        squeeze = 1.0
        if natural > available and len(words) > 1:
            gap_mm = max(min_gap_mm, (available - sum(widths_mm)) / n_gaps)
        if sum(widths_mm) + n_gaps * gap_mm > available:
            squeeze = max(0.6, (available - n_gaps * gap_mm) / max(0.001, sum(widths_mm)))

        x_mm = margin_left_mm + margin_drift_per_line * li + float(line_start_jitter[li])
        composed = ComposedLine(
            line_index=li, text=line.get("text", ""),
            baseline_y_px=int(baseline_y_mm * px_per_mm),
        )

        word_offsets = rng.normal(0, 0.2, size=len(words))  # ±0.2mm per TD-002
        for wi, res in enumerate(line_results):
            strip = res.strip
            scale = scales[wi]
            w_px = max(1, int(round(strip.width * scale * squeeze)))
            h_px = max(1, int(round(strip.height * scale)))

            # baseline undulation along the line + per-word offset
            x_progress = (x_mm - margin_left_mm) / max(1.0, geom.text_w_mm)
            wave = math.sin(
                2 * math.pi * x_progress / profile.line.baseline_undulation_period_ratio
                + line_phases[li]
            ) * profile.line.baseline_undulation_amplitude_mm
            dy_mm = wave + float(word_offsets[wi])

            ink = np.asarray(
                Image.fromarray(strip.ink, "L").resize((w_px, h_px), Image.LANCZOS),
                dtype=np.float32,
            ) / 255.0

            x_px = int(round(x_mm * px_per_mm))
            baseline_px = int(round((baseline_y_mm + dy_mm) * px_per_mm))
            y_px = baseline_px - int(round(strip.baseline_frac * h_px))

            _blend_ink(page, ink, x_px, y_px,
                       darkness=controls.ink_darkness * lacuna_opacity)

            composed.words.append(PlacedWord(
                text=res.provenance["text"],
                x_px=x_px, y_px=y_px, w_px=w_px, h_px=h_px,
                baseline_y_px=baseline_px,
                provenance=res.provenance,
            ))
            if res.provenance.get("cache_hit"):
                cache_hits += 1
            x_mm += w_px / px_per_mm + gap_mm

        composed_lines.append(composed)

    report = {
        "folio_id": folio_id,
        "backend": generator.backend.name,
        "base_seed": base_seed,
        "scored": scorer is not None,
        "words": len(requests),
        "unverified_words": len(unverified),
        "cache_hits": cache_hits,
        "controls": controls.to_dict(),
        "dpi": dpi,
    }
    return ComposedFolio(
        folio_id=folio_id, page=page, geometry=geom, dpi=dpi,
        lines=composed_lines, report=report,
    )


def hash_stable(text: str) -> int:
    import hashlib
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:4], "big")


def _blend_ink(page: np.ndarray, ink: np.ndarray, x: int, y: int,
               darkness: float = 1.0) -> None:
    """Alpha-composite an ink mask (float 0..1) onto the RGB page at (x, y)."""
    h, w = ink.shape
    ph, pw = page.shape[:2]
    y0, y1 = max(0, y), min(ph, y + h)
    x0, x1 = max(0, x), min(pw, x + w)
    if y0 >= y1 or x0 >= x1:
        return
    alpha = np.clip(ink[y0 - y: y1 - y, x0 - x: x1 - x] * darkness, 0.0, 1.0)[..., None]
    region = page[y0:y1, x0:x1].astype(np.float32)
    ink_color = np.array(_INK, dtype=np.float32)
    page[y0:y1, x0:x1] = (region * (1.0 - alpha) + ink_color * alpha).astype(np.uint8)
