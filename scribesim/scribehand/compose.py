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
    granularity: str = "word",
) -> ComposedFolio:
    """Compose a full folio page from generated word or line strips.

    granularity="word" generates one strip per word (IAM-style backends);
    granularity="line" generates one strip per line (line-trained backends)
    and recovers word bounding boxes by segmenting the generated strip.
    """
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

    lines_data = folio_dict.get("lines", [])[: geom.ruling_count or None]

    if granularity == "line":
        return _compose_folio_lines(
            folio_id=folio_id, lines_data=lines_data, profile=profile,
            generator=generator, scorer=scorer, geom=geom, controls=controls,
            dpi=dpi, px_per_mm=px_per_mm, page_w_px=page_w_px,
            page_h_px=page_h_px, margin_left_mm=margin_left_mm,
            text_right_mm=text_right_mm, x_height_mm=x_height_mm,
            base_seed=base_seed, cer_threshold=cer_threshold,
            max_retries=max_retries, allow_unverified=allow_unverified,
        )

    # ---- build word requests for the whole folio --------------------------
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


def _word_boxes_from_strip(ink: np.ndarray, words: list[str]) -> list[tuple[int, int]]:
    """Split a generated line strip into per-word column spans.

    Boundaries start at char-proportional positions, then snap to the nearest
    ink valley so boxes align with real inter-word gaps when present. Always
    returns exactly len(words) spans.
    """
    n = len(words)
    w = int(ink.shape[1])
    if n <= 0:
        return []
    if n == 1 or w < 2 * n:
        # degenerate: proportional split without snapping
        lens = [max(1, len(t)) for t in words]
        total = sum(lens)
        spans, acc = [], 0
        for t_len in lens:
            x0 = int(round(w * acc / total))
            acc += t_len
            spans.append((x0, int(round(w * acc / total))))
        return spans

    col = ink.astype(np.float32).sum(axis=0)
    lens = [max(1, len(t)) for t in words]
    total = sum(lens) + (n - 1)          # weight inter-word spaces as 1 char

    # proportional boundary targets (middle of each inter-word space)
    targets: list[int] = []
    acc = 0
    for i in range(n - 1):
        acc += lens[i] + 1
        targets.append(int(round(w * (acc - 0.5) / total)))

    # interior low-ink gap runs — candidate word separators
    low = col <= 0.05 * max(1.0, float(col.max()))
    gaps: list[int] = []          # gap centers
    start = None
    for x in range(w):
        if low[x] and start is None:
            start = x
        elif not low[x] and start is not None:
            if start > 0:        # ignore leading whitespace
                gaps.append((start + x - 1) // 2)
            start = None
    # trailing whitespace run is ignored (never closed)

    # match each target to the nearest unused gap center, keeping order
    max_snap = max(4, w // max(2, n))
    snapped: list[int] = []
    prev = 0
    used = 0
    for t in targets:
        best = None
        for gi in range(used, len(gaps)):
            if gaps[gi] <= prev:
                continue
            d = abs(gaps[gi] - t)
            if best is None or d < abs(gaps[best] - t):
                best = gi
        if best is not None and abs(gaps[best] - t) <= max_snap:
            b = gaps[best]
            used = best + 1
        else:
            b = min(max(t, prev + 1), w - 1)
        snapped.append(b)
        prev = b

    spans = []
    prev = 0
    for b in snapped:
        spans.append((prev, b))
        prev = b
    spans.append((prev, w))
    return spans


def _compose_folio_lines(
    *,
    folio_id: str,
    lines_data: list,
    profile,
    generator: WordGenerator,
    scorer,
    geom: PageGeometry,
    controls,
    dpi: float,
    px_per_mm: float,
    page_w_px: int,
    page_h_px: int,
    margin_left_mm: float,
    text_right_mm: float,
    x_height_mm: float,
    base_seed: int,
    cer_threshold: float,
    max_retries: int,
    allow_unverified: bool,
) -> ComposedFolio:
    """Line-granularity composition: one generated strip per folio line."""
    requests: list[WordRequest] = []
    req_line_idx: list[int] = []
    for li, line in enumerate(lines_data):
        text = " ".join(line.get("text", "").split())
        if not text:
            continue
        requests.append(WordRequest(
            text=text,
            seed=word_seed(base_seed, folio_id, li, 0),
            folio_id=folio_id,
            line_index=li,
            word_index=0,
            mode="line",
            controls=controls.to_dict(),
        ))
        req_line_idx.append(li)

    if scorer is not None:
        results = verify_words(
            generator, scorer, requests,
            cer_threshold=cer_threshold, max_retries=max_retries,
            base_seed=base_seed,
        )
        unverified = [r for r in results if not r.provenance.get("verified")]
        if unverified and not allow_unverified:
            sample = "; ".join(r.provenance["text"][:40] for r in unverified[:3])
            raise ComposeError(
                f"{len(unverified)} line(s) failed HTR verification "
                f"(e.g. {sample}) — fix generation or pass allow_unverified"
            )
    else:
        results = generator.generate(requests)
        unverified = []

    rng = np.random.default_rng(base_seed + hash_stable(folio_id))
    n_lines = len(lines_data)
    line_start_jitter = rng.normal(
        0, profile.line.start_x_variance_mm, size=max(1, n_lines))
    line_dy = rng.normal(
        0, profile.line.baseline_undulation_amplitude_mm, size=max(1, n_lines))
    margin_drift_per_line = (
        profile.folio.margin_left_variance_mm / max(1, n_lines - 1)
        if n_lines > 1 else 0.0
    )

    page = np.full((page_h_px, page_w_px, 3), _PARCHMENT, dtype=np.uint8)
    composed_lines: list[ComposedLine] = []
    cache_hits = 0
    total_words = 0
    available_mm = text_right_mm - margin_left_mm

    for res, li in zip(results, req_line_idx):
        line = lines_data[li]
        words = line.get("text", "").split()
        total_words += len(words)
        strip = res.strip
        lacuna_opacity = _line_lacuna_opacity(line.get("annotations", []))
        baseline_y_mm = geom.ruling_y(li) + geom.x_height_mm

        strip_xheight_px = max(1.0, strip.xheight_frac * strip.height)
        scale = (x_height_mm * px_per_mm) / strip_xheight_px
        width_mm = strip.width * scale / px_per_mm
        squeeze = 1.0
        if width_mm > available_mm:
            squeeze = available_mm / width_mm

        w_px = max(1, int(round(strip.width * scale * squeeze)))
        h_px = max(1, int(round(strip.height * scale)))
        ink = np.asarray(
            Image.fromarray(strip.ink, "L").resize((w_px, h_px), Image.LANCZOS),
            dtype=np.float32,
        ) / 255.0

        x_mm = margin_left_mm + margin_drift_per_line * li + float(line_start_jitter[li])
        x_px = int(round(x_mm * px_per_mm))
        baseline_px = int(round((baseline_y_mm + float(line_dy[li])) * px_per_mm))
        y_px = baseline_px - int(round(strip.baseline_frac * h_px))

        _blend_ink(page, ink, x_px, y_px,
                   darkness=controls.ink_darkness * lacuna_opacity)

        composed = ComposedLine(
            line_index=li, text=line.get("text", ""),
            baseline_y_px=baseline_px,
        )
        ink_u8 = (ink * 255).astype(np.uint8)
        for wi, ((wx0, wx1), word_text) in enumerate(
                zip(_word_boxes_from_strip(ink_u8, words), words)):
            composed.words.append(PlacedWord(
                text=word_text,
                x_px=x_px + wx0, y_px=y_px,
                w_px=max(1, wx1 - wx0), h_px=h_px,
                baseline_y_px=baseline_px,
                provenance={**res.provenance,
                            "word_index": wi, "box_source": "resegmented"},
            ))
        if res.provenance.get("cache_hit"):
            cache_hits += 1
        composed_lines.append(composed)

    report = {
        "folio_id": folio_id,
        "backend": generator.backend.name,
        "base_seed": base_seed,
        "scored": scorer is not None,
        "granularity": "line",
        "lines": len(requests),
        "unverified_lines": len(unverified),
        "words": total_words,
        "unverified_words": sum(
            len(lines_data[li].get("text", "").split())
            for r, li in zip(results, req_line_idx)
            if scorer is not None and not r.provenance.get("verified")
        ),
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
