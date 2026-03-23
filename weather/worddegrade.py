"""Word-Level Pre-Degradation — TD-011 Addendum A.

Applies CLIO-7 confidence annotations as pixel-level ink degradation on the
clean ScribeSim image BEFORE the AI weathering pass.  This ensures scholarly
damage specifications are honoured precisely regardless of AI behaviour.

Public API:
    estimate_local_background(image, bbox, border_px) -> np.ndarray
    build_word_damage_map(folio_json, page_xml_path, page_width, page_height, ...) -> list[WordDamageEntry]
    pre_degrade_text(clean_image, word_damage_map, seed) -> tuple[np.ndarray, np.ndarray]
    save_word_damage_map(word_damage_map, output_path) -> None
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import numpy as np

from weather.promptgen import WordDamageEntry

_PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
_NS = {"p": _PAGE_NS}


# ---------------------------------------------------------------------------
# estimate_local_background
# ---------------------------------------------------------------------------

def estimate_local_background(
    image: np.ndarray,
    bbox: tuple[int, int, int, int],
    border_px: int = 20,
) -> np.ndarray:
    """Estimate background colour by sampling a border ring around bbox.

    Args:
        image:     RGB image array (H, W, 3), uint8.
        bbox:      (left, top, right, bottom) in pixels.
        border_px: Width of the sampling ring outside the bbox.

    Returns:
        Channel-wise median RGB of the border ring, shape (3,), float64.
    """
    left, top, right, bottom = bbox
    h, w = image.shape[:2]

    # Expand the sampling region outward by border_px, clamped to image bounds
    sl = max(0, left - border_px)
    st = max(0, top - border_px)
    sr = min(w, right + border_px)
    sb = min(h, bottom + border_px)

    outer = image[st:sb, sl:sr]

    # Build a mask for the border ring (exclude the inner bbox)
    mask = np.ones((sb - st, sr - sl), dtype=bool)
    inner_t = top - st
    inner_b = bottom - st
    inner_l = left - sl
    inner_r = right - sl
    mask[max(0, inner_t):inner_b, max(0, inner_l):inner_r] = False

    pixels = outer[mask]   # shape (N, 3)
    if len(pixels) == 0:
        return np.array([240.0, 228.0, 196.0])  # fallback: warm parchment

    return np.median(pixels, axis=0)


# ---------------------------------------------------------------------------
# PAGE XML helpers
# ---------------------------------------------------------------------------

def _parse_points(points_str: str) -> list[tuple[int, int]]:
    pts = []
    for token in points_str.strip().split():
        x, y = token.split(",")
        pts.append((int(x), int(y)))
    return pts


def _bbox_from_points(pts: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def _parse_page_xml_line_bboxes(
    page_xml_path: Path,
) -> dict[int, tuple[int, int, int, int]]:
    """Extract {line_number → bbox} from PAGE XML TextLine elements.

    Line numbers are 1-based, matched by the numeric suffix in TextLine id
    (e.g. 'tl_001' → line 1).  Returns empty dict if no TextLines present.
    """
    if not page_xml_path.exists():
        return {}
    try:
        tree = ET.parse(page_xml_path)
    except ET.ParseError:
        return {}

    root = tree.getroot()
    result: dict[int, tuple[int, int, int, int]] = {}

    for tl in root.findall(".//p:TextLine", _NS):
        tl_id = tl.get("id", "")
        coords_el = tl.find("p:Coords", _NS)
        if coords_el is None:
            continue
        points_str = coords_el.get("points", "")
        if not points_str:
            continue
        pts = _parse_points(points_str)
        bbox = _bbox_from_points(pts)

        # Extract 1-based line number from id suffix (e.g. tl_001, line_1)
        # Fall back to sequential order
        num_str = "".join(ch for ch in tl_id.split("_")[-1] if ch.isdigit())
        if num_str:
            result[int(num_str)] = bbox

    return result


# ---------------------------------------------------------------------------
# Annotation → category
# ---------------------------------------------------------------------------

def _annotation_to_category(confidence: float) -> str:
    if confidence == 0.0:
        return "lacuna"
    if confidence < 0.6:
        return "trace"
    if confidence < 0.8:
        return "partial"
    return "clear"


# ---------------------------------------------------------------------------
# build_word_damage_map
# ---------------------------------------------------------------------------

def build_word_damage_map(
    folio_json: dict,
    page_xml_path: Path,
    page_width: int,
    page_height: int,
    dpi: int = 300,
    margin_top_mm: float = 12.0,
    line_spacing_mm: float = 10.0,
    margin_left_mm: float = 10.0,
    line_height_mm: float = 14.0,
) -> list[WordDamageEntry]:
    """Map CLIO-7 annotations to pixel bounding boxes.

    For each annotated line in folio_json:
    - Tries to use TextLine Coords from PAGE XML for accurate bboxes.
    - Falls back to computing bboxes from layout constants when XML is sparse.
    - Produces one WordDamageEntry per annotation (line-level granularity).

    Returns a list of WordDamageEntry objects sorted by line number.
    """
    px_per_mm = dpi / 25.4
    xml_bboxes = _parse_page_xml_line_bboxes(Path(page_xml_path))

    entries: list[WordDamageEntry] = []

    for line in folio_json.get("lines", []):
        line_num = line.get("number", 0)
        annotations = line.get("annotations", [])

        # Compute fallback layout bbox for this line
        y_top_mm = margin_top_mm + (line_num - 1) * line_spacing_mm
        y_bot_mm = y_top_mm + line_height_mm
        x_left_px = int(margin_left_mm * px_per_mm)
        x_right_px = page_width - x_left_px
        y_top_px = int(y_top_mm * px_per_mm)
        y_bot_px = min(int(y_bot_mm * px_per_mm), page_height - 1)
        layout_bbox = (x_left_px, y_top_px, x_right_px, y_bot_px)

        # Use PAGE XML bbox if available for this line
        bbox = xml_bboxes.get(line_num, layout_bbox)
        # Clamp to page
        bbox = (
            max(0, bbox[0]),
            max(0, bbox[1]),
            min(page_width, bbox[2]),
            min(page_height, bbox[3]),
        )
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0

        for ann in annotations:
            ann_type = ann.get("type", "")
            detail = ann.get("detail", {})

            if ann_type == "lacuna":
                entries.append(WordDamageEntry(
                    word_text="[lacuna]",
                    bbox=bbox,
                    center=(cx, cy),
                    confidence=0.0,
                    category="lacuna",
                    line_number=line_num,
                    specific_note=detail.get("note"),
                ))

            elif ann_type == "confidence":
                score = float(detail.get("score", 1.0))
                category = _annotation_to_category(score)
                specific_note = detail.get("note") or ann.get("note")
                entries.append(WordDamageEntry(
                    word_text=line.get("text", ""),
                    bbox=bbox,
                    center=(cx, cy),
                    confidence=score,
                    category=category,
                    line_number=line_num,
                    specific_note=specific_note,
                ))

    entries.sort(key=lambda e: e.line_number)
    return entries


# ---------------------------------------------------------------------------
# pre_degrade_text
# ---------------------------------------------------------------------------

def pre_degrade_text(
    clean_image: np.ndarray,
    word_damage_map: list[WordDamageEntry],
    seed: int = 1457,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply word-level ink degradation before AI weathering.

    Confidence thresholds:
        == 0.0  lacuna   → erase to estimated local background
        <  0.6  trace    → fade to (confidence × 0.5) opacity + noise
        <  0.8  partial  → fade to (0.5 + confidence × 0.25) opacity
        >= 0.8  clear    → unmodified

    Args:
        clean_image:     RGB numpy array (H, W, 3), uint8.
        word_damage_map: List of WordDamageEntry with pixel bboxes.
        seed:            RNG seed for Gaussian noise (deterministic).

    Returns:
        (degraded_image, degradation_mask)
        degradation_mask is uint8 (H, W): 255=fully erased, 0=unmodified,
        proportional values for partial degradation.
    """
    rng = np.random.default_rng(seed)
    result = clean_image.copy().astype(np.float32)
    mask = np.zeros(clean_image.shape[:2], dtype=np.uint8)

    for entry in word_damage_map:
        l, t, r, b = entry.bbox
        # Clamp bbox to image
        h, w = result.shape[:2]
        l, r = max(0, l), min(w, r)
        t, b = max(0, t), min(h, b)
        if l >= r or t >= b:
            continue

        region = result[t:b, l:r]
        conf = entry.confidence

        if conf == 0.0:
            # Lacuna: erase to local background
            bg = estimate_local_background(
                clean_image, (l, t, r, b), border_px=20
            ).astype(np.float32)
            result[t:b, l:r] = bg[np.newaxis, np.newaxis, :]
            mask[t:b, l:r] = 255

        elif conf < 0.6:
            # Trace: fade to (confidence × 0.5) opacity, add dissolution noise
            alpha = conf * 0.5
            bg = estimate_local_background(
                clean_image, (l, t, r, b), border_px=20
            ).astype(np.float32)
            blended = region * alpha + bg[np.newaxis, np.newaxis, :] * (1.0 - alpha)
            noise = rng.normal(0, 15, blended.shape).astype(np.float32)
            blended = np.clip(blended + noise, 0, 255)
            result[t:b, l:r] = blended
            mask_val = int(255 * (1.0 - alpha))
            mask[t:b, l:r] = np.maximum(mask[t:b, l:r], mask_val)

        elif conf < 0.8:
            # Partial: fade to (0.5 + confidence × 0.25) opacity
            alpha = 0.5 + conf * 0.25
            bg = estimate_local_background(
                clean_image, (l, t, r, b), border_px=20
            ).astype(np.float32)
            blended = region * alpha + bg[np.newaxis, np.newaxis, :] * (1.0 - alpha)
            result[t:b, l:r] = np.clip(blended, 0, 255)
            mask_val = int(255 * (1.0 - alpha))
            mask[t:b, l:r] = np.maximum(mask[t:b, l:r], mask_val)

        # else: clear (confidence >= 0.8) — no modification, mask stays 0

    return result.clip(0, 255).astype(np.uint8), mask


# ---------------------------------------------------------------------------
# save_word_damage_map
# ---------------------------------------------------------------------------

def save_word_damage_map(
    word_damage_map: list[WordDamageEntry],
    output_path: Path,
) -> None:
    """Serialise word damage map to JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for e in word_damage_map:
        records.append({
            "word_text": e.word_text,
            "bbox": list(e.bbox),
            "center": list(e.center),
            "confidence": e.confidence,
            "category": e.category,
            "line_number": e.line_number,
            "specific_note": e.specific_note,
        })

    output_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
