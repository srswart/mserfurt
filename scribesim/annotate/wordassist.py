"""DP-assisted word segmentation helpers for the annotation workbench."""

from __future__ import annotations

import math
import re
from typing import Any

import numpy as np
from PIL import Image as PILImage
from PIL import ImageDraw

from scribesim.pathguide.model import DensePathGuide
from scribesim.refextract.segment import detect_vertical_strokes
from scribesim.refextract.utils import otsu_threshold

_TARGET_SIZE = (64, 64)
_LIGATURES = (
    "ſch",
    "ch",
    "ck",
    "ſt",
    "ſſ",
    "tz",
    "ng",
    "pf",
    "sp",
)

_WIDTH_RATIOS: dict[str, tuple[float, float]] = {
    "i": (0.15, 0.40),
    "l": (0.15, 0.40),
    "·": (0.15, 0.40),
    "j": (0.25, 0.55),
    "t": (0.25, 0.55),
    "r": (0.25, 0.55),
    "a": (0.35, 0.70),
    "c": (0.35, 0.70),
    "e": (0.35, 0.70),
    "o": (0.35, 0.70),
    "n": (0.35, 0.70),
    "u": (0.35, 0.70),
    "s": (0.35, 0.70),
    "ſ": (0.35, 0.70),
    "d": (0.40, 0.80),
    "b": (0.40, 0.80),
    "h": (0.40, 0.80),
    "g": (0.40, 0.80),
    "p": (0.40, 0.80),
    "q": (0.40, 0.80),
    "v": (0.40, 0.80),
    "f": (0.35, 0.65),
    "k": (0.35, 0.65),
    "z": (0.35, 0.65),
    "m": (0.60, 1.10),
    "w": (0.60, 1.10),
}


def preprocess_transcript(raw: str) -> list[str]:
    """Normalize a typed transcript into glyph units, preserving known ligatures."""

    collapsed = re.sub(r"\s+", "", str(raw or ""))
    if not collapsed:
        return []
    units: list[str] = []
    index = 0
    while index < len(collapsed):
        matched = False
        for ligature in _LIGATURES:
            if collapsed.startswith(ligature, index):
                units.append(ligature)
                index += len(ligature)
                matched = True
                break
        if matched:
            continue
        units.append(collapsed[index])
        index += 1
    return units


def trim_word_image(word_image: np.ndarray, *, padding_px: int = 1) -> tuple[np.ndarray, dict[str, int]]:
    """Crop to the inked word region and return bounds relative to the source crop."""

    gray = _to_gray(word_image)
    binary = _binarize(gray)
    rows = np.where(binary.any(axis=1))[0]
    cols = np.where(binary.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        height, width = gray.shape[:2]
        return gray, {"x": 0, "y": 0, "width": int(width), "height": int(height)}
    top = max(0, int(rows[0]) - padding_px)
    bottom = min(gray.shape[0] - 1, int(rows[-1]) + padding_px)
    left = max(0, int(cols[0]) - padding_px)
    right = min(gray.shape[1] - 1, int(cols[-1]) + padding_px)
    trimmed = gray[top : bottom + 1, left : right + 1]
    return trimmed, {"x": left, "y": top, "width": int(trimmed.shape[1]), "height": int(trimmed.shape[0])}


def build_template_bank(guides: dict[str, DensePathGuide], *, target_size: tuple[int, int] = _TARGET_SIZE) -> dict[str, np.ndarray]:
    bank: dict[str, np.ndarray] = {}
    for symbol, guide in guides.items():
        bank[str(symbol)] = render_dense_guide_template(guide, target_size=target_size)
    return bank


def propose_word_segmentation(
    word_image: np.ndarray,
    transcript: str | list[str] | tuple[str, ...],
    *,
    template_bank: dict[str, np.ndarray] | None = None,
) -> dict[str, Any]:
    units = preprocess_transcript(transcript) if isinstance(transcript, str) else [str(item) for item in transcript]
    if not units:
        raise ValueError("transcript must include at least one glyph unit")
    gray = _to_gray(word_image)
    if gray.size == 0:
        raise ValueError("word image is empty")
    width = int(gray.shape[1])
    if width <= 0:
        raise ValueError("word image width must be positive")

    if len(units) == 1:
        proposal = score_word_segmentation(gray, units, [0, width], template_bank=template_bank)
        proposal["mode"] = _proposal_mode(proposal["segments"])
        return proposal

    dp = np.full((len(units) + 1, width + 1), np.inf, dtype=float)
    back = np.full((len(units) + 1, width + 1), -1, dtype=int)
    dp[0, 0] = 0.0

    for unit_index, unit in enumerate(units, start=1):
        min_width, max_width = expected_width_range(unit, gray.shape[0])
        max_width = min(width, max_width)
        for end_x in range(1, width + 1):
            start_min = max(0, end_x - max_width)
            start_max = max(0, end_x - min_width)
            if start_min > start_max:
                continue
            for start_x in range(start_min, start_max + 1):
                if not math.isfinite(dp[unit_index - 1, start_x]):
                    continue
                slice_image = gray[:, start_x:end_x]
                score = _segment_cost(unit, slice_image, template_bank or {})
                total = float(dp[unit_index - 1, start_x]) + float(score["cost"])
                if total < dp[unit_index, end_x]:
                    dp[unit_index, end_x] = total
                    back[unit_index, end_x] = start_x

    candidate_starts = range(max(1, int(width * 0.9)), width + 1)
    best_end = min(candidate_starts, key=lambda index: float(dp[len(units), index]))
    if not math.isfinite(float(dp[len(units), best_end])):
        boundaries = _fallback_boundaries(width, len(units))
        proposal = score_word_segmentation(gray, units, boundaries, template_bank=template_bank)
        proposal["mode"] = "fallback"
        proposal["fallback"] = True
        return proposal

    boundaries = [best_end]
    current = best_end
    for unit_index in range(len(units), 0, -1):
        current = int(back[unit_index, current])
        if current < 0:
            boundaries = _fallback_boundaries(width, len(units))
            proposal = score_word_segmentation(gray, units, boundaries, template_bank=template_bank)
            proposal["mode"] = "fallback"
            proposal["fallback"] = True
            return proposal
        boundaries.append(current)
    boundaries.reverse()
    if boundaries[0] != 0:
        boundaries[0] = 0
    if boundaries[-1] != width:
        boundaries[-1] = width
    proposal = score_word_segmentation(gray, units, boundaries, template_bank=template_bank)
    proposal["mode"] = _proposal_mode(proposal["segments"])
    proposal["fallback"] = False
    return proposal


def score_word_segmentation(
    word_image: np.ndarray,
    units: list[str] | tuple[str, ...],
    boundaries: list[int] | tuple[int, ...],
    *,
    template_bank: dict[str, np.ndarray] | None = None,
) -> dict[str, Any]:
    gray = _to_gray(word_image)
    if not units:
        raise ValueError("units must not be empty")
    if len(boundaries) != len(units) + 1:
        raise ValueError("boundaries length must equal unit count + 1")
    normalized_boundaries = [int(round(value)) for value in boundaries]
    if normalized_boundaries[0] != 0 or normalized_boundaries[-1] != int(gray.shape[1]):
        raise ValueError("boundaries must start at 0 and end at the word width")
    segments: list[dict[str, Any]] = []
    costs: list[float] = []
    missing_guides: list[str] = []
    for index, unit in enumerate(units):
        start_x = normalized_boundaries[index]
        end_x = normalized_boundaries[index + 1]
        if end_x <= start_x:
            raise ValueError("boundaries must be strictly increasing")
        score = _segment_cost(unit, gray[:, start_x:end_x], template_bank or {})
        segment = {
            "index": index,
            "unit": unit,
            "start_x": start_x,
            "end_x": end_x,
            "width_px": end_x - start_x,
            "cost": float(score["cost"]),
            "confidence": float(1.0 / (1.0 + score["cost"])),
            "guide_available": bool(score["guide_available"]),
            "mode": str(score["mode"]),
            "cost_components": score["components"],
            "template_score": score.get("template_score"),
            "competitor_margin": score.get("competitor_margin"),
            "issues": list(score.get("issues", [])),
        }
        if not segment["guide_available"]:
            missing_guides.append(unit)
        segments.append(segment)
        costs.append(float(segment["cost"]))
    confidence = segmentation_confidence(costs)
    return {
        "units": list(units),
        "boundaries": normalized_boundaries,
        "segments": segments,
        "confidence": float(confidence),
        "highest_cost_unit": max(segments, key=lambda item: item["cost"])["unit"] if segments else None,
        "missing_guides": _dedupe(missing_guides),
        "costs": costs,
        "mode": _proposal_mode(segments),
    }


def segmentation_confidence(costs: list[float] | tuple[float, ...]) -> float:
    if not costs:
        return 0.0
    max_cost = max(float(value) for value in costs)
    mean_cost = sum(float(value) for value in costs) / max(len(costs), 1)
    confidence = 1.0 / (1.0 + mean_cost * 2.0)
    worst_penalty = (max_cost - 1.0) * 0.2 if max_cost > 1.0 else 0.0
    return float(max(0.0, min(1.0, confidence - worst_penalty)))


def render_dense_guide_template(guide: DensePathGuide, *, target_size: tuple[int, int] = _TARGET_SIZE) -> np.ndarray:
    min_x = min(sample.x_mm - sample.corridor_half_width_mm for sample in guide.samples)
    min_y = min(sample.y_mm - sample.corridor_half_width_mm for sample in guide.samples)
    max_x = max(sample.x_mm + sample.corridor_half_width_mm for sample in guide.samples)
    max_y = max(sample.y_mm + sample.corridor_half_width_mm for sample in guide.samples)

    width_mm = max(max_x - min_x, 0.1)
    height_mm = max(max_y - min_y, 0.1)
    inner_w = target_size[1] - 12
    inner_h = target_size[0] - 12
    px_per_mm = min(inner_w / width_mm, inner_h / height_mm)

    canvas = PILImage.new("L", (target_size[1], target_size[0]), 255)
    draw = ImageDraw.Draw(canvas)

    def to_px(x_mm: float, y_mm: float) -> tuple[int, int]:
        x_px = 6 + int(round((x_mm - min_x) * px_per_mm))
        y_px = target_size[0] - 6 - int(round((y_mm - min_y) * px_per_mm))
        return x_px, y_px

    for index in range(len(guide.samples) - 1):
        start = guide.samples[index]
        end = guide.samples[index + 1]
        width = max(
            1,
            int(round((start.corridor_half_width_mm + end.corridor_half_width_mm) * 0.5 * px_per_mm * 0.9)),
        )
        draw.line((*to_px(start.x_mm, start.y_mm), *to_px(end.x_mm, end.y_mm)), fill=0, width=width)
    return np.array(canvas, dtype=np.uint8)


def expected_width_range(unit: str, image_height: int) -> tuple[int, int]:
    x_height = max(float(image_height) * 0.6, 1.0)
    min_ratio = 0.0
    max_ratio = 0.0
    for char in str(unit):
        left, right = _WIDTH_RATIOS.get(char, (0.30, 0.80))
        min_ratio += left
        max_ratio += right
    if len(str(unit)) > 1:
        max_ratio *= 0.92
    min_px = max(3, int(round(x_height * min_ratio)))
    max_px = max(min_px + 1, int(round(x_height * max_ratio)))
    return min_px, max_px


def _proposal_mode(segments: list[dict[str, Any]]) -> str:
    if not segments:
        return "empty"
    guide_count = sum(1 for item in segments if bool(item.get("guide_available")))
    if guide_count == len(segments):
        return "guide-assisted"
    if guide_count == 0:
        return "bootstrap"
    return "mixed"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    kept: list[str] = []
    for value in values:
        if value in seen:
            continue
        kept.append(value)
        seen.add(value)
    return kept


def _fallback_boundaries(width: int, unit_count: int) -> list[int]:
    if unit_count <= 0:
        return [0, max(0, width)]
    boundaries = [0]
    for index in range(1, unit_count):
        boundaries.append(int(round(index * width / unit_count)))
    boundaries.append(width)
    for index in range(1, len(boundaries)):
        if boundaries[index] <= boundaries[index - 1]:
            boundaries[index] = boundaries[index - 1] + 1
    boundaries[-1] = width
    return boundaries


def _segment_cost(unit: str, slice_image: np.ndarray, template_bank: dict[str, np.ndarray]) -> dict[str, Any]:
    gray = _to_gray(slice_image)
    if gray.size == 0 or gray.shape[1] <= 0:
        return {
            "cost": 9999.0,
            "components": {"empty": 9999.0},
            "guide_available": False,
            "mode": "invalid",
            "issues": ["empty slice"],
        }

    components: dict[str, float] = {}
    issues: list[str] = []
    expected_mean = sum(expected_width_range(unit, gray.shape[0])) / 2.0
    width_deviation = abs(float(gray.shape[1]) - expected_mean) / max(expected_mean, 1.0)
    components["width"] = width_deviation * 2.0

    left_edge = _column_ink_density(gray, 0)
    right_edge = _column_ink_density(gray, gray.shape[1] - 1)
    components["cut_edges"] = (left_edge + right_edge) * 1.35

    structural = _bootstrap_structure_cost(unit, gray)
    components["structure"] = structural
    mode = "bootstrap"
    guide_available = unit in template_bank
    template_score: float | None = None
    competitor_margin: float | None = None
    if guide_available:
        normalized = _normalize_slice(gray, target_size=template_bank[unit].shape)
        own = _ncc_score(normalized, template_bank[unit])
        competitor = max(
            (_ncc_score(normalized, template) for symbol, template in template_bank.items() if symbol != unit),
            default=0.0,
        )
        template_score = float(own)
        competitor_margin = float(own - competitor)
        components["template"] = (1.0 - own) * 5.0
        components["competitor"] = max(0.0, 0.2 - competitor_margin) * 2.0
        mode = "guide-assisted"
        if competitor_margin < 0.05:
            issues.append("guide match is close to a competing symbol")
    else:
        components["template"] = 0.0
        issues.append("no exact guide is available; using structural heuristics")

    total = float(sum(components.values()))
    return {
        "cost": total,
        "components": {key: float(value) for key, value in components.items()},
        "guide_available": guide_available,
        "mode": mode,
        "template_score": template_score,
        "competitor_margin": competitor_margin,
        "issues": issues,
    }


def _bootstrap_structure_cost(unit: str, slice_image: np.ndarray) -> float:
    cost = 0.0
    width_mean = sum(expected_width_range(unit, slice_image.shape[0])) / 2.0
    cost += abs(float(slice_image.shape[1]) - width_mean) / max(width_mean, 1.0) * 1.8

    has_ascender = _band_ink_ratio(slice_image, top=True) > 0.18
    has_descender = _band_ink_ratio(slice_image, top=False) > 0.12
    stroke_count = len(detect_vertical_strokes(slice_image, min_height_ratio=0.22, min_distance=max(2, slice_image.shape[1] // 8)))

    chars = tuple(str(unit))
    if any(char in {"b", "d", "h", "k", "l", "ſ", "f", "t"} for char in chars) and not has_ascender:
        cost += 2.4
    if any(char in {"g", "p", "q", "y", "f", "ſ"} for char in chars) and not has_descender:
        cost += 2.4
    if unit == "m" and stroke_count < 3:
        cost += 1.8
    if unit in {"n", "u"} and stroke_count < 2:
        cost += 1.6
    if unit == "i" and stroke_count > 2:
        cost += 1.2
    return float(cost)


def _to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3:
        return np.mean(image[:, :, :3], axis=2).astype(np.uint8)
    return image.astype(np.uint8)


def _binarize(gray: np.ndarray, threshold: int | None = None) -> np.ndarray:
    limit = int(threshold) if threshold is not None else int(otsu_threshold(gray))
    return gray < limit


def _normalize_slice(slice_image: np.ndarray, *, target_size: tuple[int, int]) -> np.ndarray:
    gray = _to_gray(slice_image)
    binary = _binarize(gray)
    rows = np.where(binary.any(axis=1))[0]
    cols = np.where(binary.any(axis=0))[0]
    if len(rows) and len(cols):
        gray = gray[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]
    image = PILImage.fromarray(gray).convert("L")
    inner_w = max(4, target_size[1] - 8)
    inner_h = max(4, target_size[0] - 8)
    scale = min(inner_w / max(image.width, 1), inner_h / max(image.height, 1))
    resized = image.resize(
        (max(1, int(round(image.width * scale))), max(1, int(round(image.height * scale)))),
        resample=PILImage.Resampling.BILINEAR,
    )
    canvas = PILImage.new("L", (target_size[1], target_size[0]), 255)
    offset = ((canvas.width - resized.width) // 2, (canvas.height - resized.height) // 2)
    canvas.paste(resized, offset)
    return np.array(canvas, dtype=np.uint8)


def _ncc_score(left: np.ndarray, right: np.ndarray) -> float:
    lhs = (255.0 - left.astype(float)).reshape(-1)
    rhs = (255.0 - right.astype(float)).reshape(-1)
    lhs -= lhs.mean()
    rhs -= rhs.mean()
    denom = float(np.linalg.norm(lhs) * np.linalg.norm(rhs))
    if denom <= 1e-8:
        return 0.0
    return float(max(0.0, min(1.0, np.dot(lhs, rhs) / denom)))


def _column_ink_density(gray: np.ndarray, index: int) -> float:
    if gray.size == 0:
        return 0.0
    column = gray[:, max(0, min(gray.shape[1] - 1, index))]
    return float(np.mean(column < 200))


def _band_ink_ratio(gray: np.ndarray, *, top: bool) -> float:
    if gray.size == 0:
        return 0.0
    band_height = max(1, gray.shape[0] // 3)
    band = gray[:band_height, :] if top else gray[-band_height:, :]
    return float(np.mean(band < 200))
