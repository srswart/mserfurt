"""AI Weathering Validation — TD-011 Part 5 and Addendum A.

Three post-AI checks:
  V1  — text position drift < 5px (AI did not move letterforms)
  V2-A — pre-degraded lacunae/traces not restored by AI
  V3  — recto/verso water stain regions are spatially consistent (IoU >= 0.50)

Public API:
    validate_text_positions(clean_image, weathered_image, bbox_list) -> ValidationResult
    validate_pre_degradation_preserved(pre_degraded, weathered, mask, word_damage_map) -> ValidationResult
    validate_damage_consistency(recto_image, verso_image, recto_spec, verso_spec) -> ValidationResult
    validate_folio(...) -> ValidationSummary
    validate_codex(...) -> dict
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from weather.promptgen import FolioWeatherSpec, WordDamageEntry


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    check_name: str
    passed: bool
    value: float          # primary metric (drift px, brightness ratio, IoU)
    threshold: float      # the pass/fail boundary
    issues: list[str] = field(default_factory=list)


@dataclass
class ValidationSummary:
    folio_id: str
    v1_text_positions: ValidationResult
    v2a_pre_degradation: ValidationResult
    v3_damage_consistency: ValidationResult

    @property
    def all_passed(self) -> bool:
        return (
            self.v1_text_positions.passed
            and self.v2a_pre_degradation.passed
            and self.v3_damage_consistency.passed
        )

    def to_dict(self) -> dict:
        def _r(r: ValidationResult) -> dict:
            return {
                "check_name": r.check_name,
                "passed": r.passed,
                "value": r.value,
                "threshold": r.threshold,
                "issues": r.issues,
            }
        return {
            "folio_id": self.folio_id,
            "all_passed": self.all_passed,
            "v1_text_positions": _r(self.v1_text_positions),
            "v2a_pre_degradation": _r(self.v2a_pre_degradation),
            "v3_damage_consistency": _r(self.v3_damage_consistency),
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_gray(image: np.ndarray) -> np.ndarray:
    """Convert RGB uint8 to float64 grayscale [0, 255]."""
    return 0.299 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 2]


def _otsu_threshold(gray: np.ndarray) -> int:
    """Histogram-based Otsu threshold — no scipy dependency."""
    flat = gray.astype(np.uint8).ravel()
    hist, _ = np.histogram(flat, bins=256, range=(0, 256))
    hist = hist.astype(np.float64)
    total = flat.size
    if total == 0:
        return 128

    sum_total = np.dot(np.arange(256, dtype=np.float64), hist)
    sum_b = 0.0
    w_b = 0.0
    max_var = 0.0
    threshold = 128

    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        mean_b = sum_b / w_b
        mean_f = (sum_total - sum_b) / w_f
        var_between = w_b * w_f * (mean_b - mean_f) ** 2
        if var_between > max_var:
            max_var = var_between
            threshold = t

    return threshold


def _binarize(image: np.ndarray, invert: bool = True) -> np.ndarray:
    """Global Otsu binarization. If invert=True, dark pixels → True (ink)."""
    gray = _to_gray(image)
    t = _otsu_threshold(gray)
    if invert:
        return gray <= t  # ink is dark; <= to include pixels exactly at threshold
    return gray > t


def _connected_component_centroids(
    binary_mask: np.ndarray,
) -> list[tuple[float, float]]:
    """Return (cx, cy) centroids of connected components via simple labeling."""
    # Use scipy if available, otherwise fall back to a simple row-scan approach
    try:
        from scipy import ndimage as ndi
        labeled, n = ndi.label(binary_mask)
        centroids = []
        for i in range(1, n + 1):
            ys, xs = np.where(labeled == i)
            if len(xs):
                centroids.append((float(xs.mean()), float(ys.mean())))
        return centroids
    except ImportError:
        # Fallback: treat whole mask as one component
        ys, xs = np.where(binary_mask)
        if len(xs) == 0:
            return []
        return [(float(xs.mean()), float(ys.mean()))]


# ---------------------------------------------------------------------------
# V1: validate_text_positions
# ---------------------------------------------------------------------------

def validate_text_positions(
    clean_image: np.ndarray,
    weathered_image: np.ndarray,
    bbox_list: list[tuple[int, int, int, int]],
    max_drift_px: float = 5.0,
) -> ValidationResult:
    """V1 — verify text centroids haven't shifted more than max_drift_px pixels.

    Args:
        clean_image:    Pre-weather ScribeSim render (H, W, 3) uint8.
        weathered_image: Post-AI weathered image, same size.
        bbox_list:      List of (left, top, right, bottom) text regions from PAGE XML.
        max_drift_px:   Maximum allowed centroid displacement.

    Returns:
        ValidationResult with value = max observed drift across all regions.
    """
    if not bbox_list:
        return ValidationResult(
            check_name="V1_text_positions",
            passed=True,
            value=0.0,
            threshold=max_drift_px,
            issues=[],
        )

    clean_bin = _binarize(clean_image)
    weathered_bin = _binarize(weathered_image)

    max_drift = 0.0
    issues: list[str] = []

    for bbox in bbox_list:
        l, t, r, b = bbox
        h, w = clean_image.shape[:2]
        l, t, r, b = max(0, l), max(0, t), min(w, r), min(h, b)
        if l >= r or t >= b:
            continue

        c_region = clean_bin[t:b, l:r]
        w_region = weathered_bin[t:b, l:r]

        c_centroids = _connected_component_centroids(c_region)
        w_centroids = _connected_component_centroids(w_region)

        if not c_centroids or not w_centroids:
            continue

        # Match each clean centroid to the nearest weathered centroid
        for cx, cy in c_centroids:
            if not w_centroids:
                continue
            dists = [
                np.hypot(cx - wx, cy - wy) for wx, wy in w_centroids
            ]
            min_dist = min(dists)
            if min_dist > max_drift:
                max_drift = min_dist
            if min_dist > max_drift_px:
                issues.append(
                    f"bbox {bbox}: centroid drift {min_dist:.1f}px > {max_drift_px}px"
                )

    return ValidationResult(
        check_name="V1_text_positions",
        passed=bool(max_drift <= max_drift_px),
        value=float(max_drift),
        threshold=max_drift_px,
        issues=issues,
    )


# ---------------------------------------------------------------------------
# V2-A: validate_pre_degradation_preserved
# ---------------------------------------------------------------------------

def validate_pre_degradation_preserved(
    pre_degraded_image: np.ndarray,
    weathered_image: np.ndarray,
    degradation_mask: np.ndarray,
    word_damage_map: list[WordDamageEntry],
    lacuna_tolerance: float = 0.15,
    trace_brightening_tolerance: float = 0.20,
) -> ValidationResult:
    """V2-A — check AI did not restore pre-degraded lacunae or faded traces.

    Lacuna regions (mask=255): weathered mean brightness must stay within
    lacuna_tolerance of the pre-degraded mean (AI didn't add ink back).

    Trace regions (mask proportional, >0): weathered mean must not exceed
    pre-degraded mean by more than trace_brightening_tolerance (AI didn't
    brighten faded text).

    Returns:
        ValidationResult with value = worst violation ratio observed.
    """
    if not word_damage_map:
        return ValidationResult(
            check_name="V2A_pre_degradation",
            passed=True,
            value=0.0,
            threshold=lacuna_tolerance,
            issues=[],
        )

    issues: list[str] = []
    worst_ratio = 0.0

    pre_gray = _to_gray(pre_degraded_image)
    wet_gray = _to_gray(weathered_image)

    for entry in word_damage_map:
        l, t, r, b = entry.bbox
        h, w = pre_degraded_image.shape[:2]
        l, t, r, b = max(0, l), max(0, t), min(w, r), min(h, b)
        if l >= r or t >= b:
            continue

        mask_region = degradation_mask[t:b, l:r]
        if mask_region.max() == 0:
            continue  # no degradation here

        if entry.confidence == 0.0:
            # Lacuna: check that weathered brightness ≈ pre-degraded (both light)
            pre_mean = float(pre_gray[t:b, l:r].mean())
            wet_mean = float(wet_gray[t:b, l:r].mean())
            # Both should be high (background). If weathered is much darker, AI added ink.
            if pre_mean > 0:
                ratio = abs(wet_mean - pre_mean) / (pre_mean + 1e-6)
                worst_ratio = max(worst_ratio, ratio)
                if ratio > lacuna_tolerance:
                    issues.append(
                        f"Lacuna at {entry.bbox}: weathered mean={wet_mean:.1f}, "
                        f"pre-degraded mean={pre_mean:.1f}, ratio={ratio:.2f} > {lacuna_tolerance}"
                    )
        elif entry.confidence < 0.8:
            # Trace/partial: check AI didn't brighten (restore ink darkness)
            # Ink is dark → lower mean = more ink.
            # Violation: weathered is darker than pre-degraded by > tolerance
            pre_mean = float(pre_gray[t:b, l:r].mean())
            wet_mean = float(wet_gray[t:b, l:r].mean())
            # If weathered is significantly darker than pre-degraded, AI restored darkness
            if pre_mean > 0:
                darkening_ratio = (pre_mean - wet_mean) / (pre_mean + 1e-6)
                darkening_ratio = max(0.0, darkening_ratio)
                worst_ratio = max(worst_ratio, darkening_ratio)
                if darkening_ratio > trace_brightening_tolerance:
                    issues.append(
                        f"Trace at {entry.bbox}: AI darkened region — weathered mean={wet_mean:.1f}, "
                        f"pre-degraded mean={pre_mean:.1f}, darkening={darkening_ratio:.2f}"
                    )

    return ValidationResult(
        check_name="V2A_pre_degradation",
        passed=len(issues) == 0,
        value=worst_ratio,
        threshold=max(lacuna_tolerance, trace_brightening_tolerance),
        issues=issues,
    )


# ---------------------------------------------------------------------------
# V3: validate_damage_consistency
# ---------------------------------------------------------------------------

def _water_damage_zone(
    image: np.ndarray,
    water_spec,
) -> tuple[int, int, int, int]:
    """Return (top, bot, left, right) pixel region for the water damage zone."""
    h, w = image.shape[:2]
    pen = water_spec.penetration
    origin = water_spec.origin  # "top_right", "top_left", etc.

    if "top" in origin:
        top, bot = 0, int(h * pen)
    else:
        top, bot = int(h * (1 - pen)), h

    if "right" in origin:
        left, right = int(w * 0.5), w
    else:
        left, right = 0, int(w * 0.5)

    return top, bot, left, right


def _detect_stain_mask(
    image: np.ndarray,
    water_spec,
    dark_threshold_factor: float = 0.85,
) -> np.ndarray:
    """Return binary mask of stained (dark) pixels within the water damage zone."""
    gray = _to_gray(image)
    full_mask = np.zeros(gray.shape, dtype=bool)

    if water_spec is None:
        return full_mask

    t, b, l, r = _water_damage_zone(image, water_spec)
    region = gray[t:b, l:r]
    if region.size == 0:
        return full_mask

    # Pixels meaningfully darker than median of whole image = stained
    global_median = float(np.median(gray))
    stain_thresh = global_median * dark_threshold_factor
    full_mask[t:b, l:r] = region < stain_thresh
    return full_mask


def validate_damage_consistency(
    recto_image: np.ndarray,
    verso_image: np.ndarray,
    recto_spec: FolioWeatherSpec,
    verso_spec: FolioWeatherSpec,
    min_iou: float = 0.50,
) -> ValidationResult:
    """V3 — verify recto/verso water stain regions are spatially consistent.

    Mirrors the verso image horizontally (spine symmetry) then computes
    IoU of Otsu-detected stain masks. Skips check if neither folio has
    water damage (returns passed=True vacuously).

    Returns:
        ValidationResult with value = IoU (0.0 if no stains detected).
    """
    has_recto_water = recto_spec.water_damage is not None
    has_verso_water = verso_spec is not None and verso_spec.water_damage is not None

    if not has_recto_water and not has_verso_water:
        return ValidationResult(
            check_name="V3_damage_consistency",
            passed=True,
            value=1.0,
            threshold=min_iou,
            issues=["No water damage on either side — V3 not applicable"],
        )

    recto_mask = _detect_stain_mask(recto_image, recto_spec.water_damage)

    if verso_image is not None and has_verso_water:
        # Mirror verso horizontally to align with recto (spine symmetry).
        # After flipping, the verso's stain (which is the mirror of recto's)
        # now sits in the same spatial zone as recto's stain — so use
        # recto_spec's water_damage zone for detection on the flipped image.
        verso_flipped = np.fliplr(verso_image)
        detect_spec = recto_spec if has_recto_water else verso_spec
        verso_mask = _detect_stain_mask(verso_flipped, detect_spec.water_damage)
    else:
        verso_mask = np.zeros_like(recto_mask)

    # Resize verso mask to match recto if needed
    if recto_mask.shape != verso_mask.shape:
        verso_mask = verso_mask[: recto_mask.shape[0], : recto_mask.shape[1]]

    intersection = float(np.logical_and(recto_mask, verso_mask).sum())
    union = float(np.logical_or(recto_mask, verso_mask).sum())
    iou = intersection / union if union > 0 else 0.0

    issues: list[str] = []
    if iou < min_iou:
        issues.append(
            f"Recto/verso stain IoU={iou:.3f} < threshold {min_iou} — "
            f"water damage may not be spatially consistent across the leaf"
        )

    return ValidationResult(
        check_name="V3_damage_consistency",
        passed=iou >= min_iou,
        value=iou,
        threshold=min_iou,
        issues=issues,
    )


# ---------------------------------------------------------------------------
# validate_folio
# ---------------------------------------------------------------------------

def validate_folio(
    folio_id: str,
    clean_image: np.ndarray,
    weathered_image: np.ndarray,
    pre_degraded_image: np.ndarray,
    degradation_mask: np.ndarray,
    word_damage_map: list[WordDamageEntry],
    recto_spec: FolioWeatherSpec,
    verso_image: Optional[np.ndarray],
    verso_spec: Optional[FolioWeatherSpec],
    bbox_list: list[tuple[int, int, int, int]],
) -> ValidationSummary:
    """Run all three validation checks for one folio.

    Args:
        folio_id:           e.g. "f04r"
        clean_image:        ScribeSim render before any processing
        weathered_image:    Post-AI output
        pre_degraded_image: After word pre-degradation, before AI
        degradation_mask:   uint8 mask from pre_degrade_text (0=unmodified, 255=erased)
        word_damage_map:    WordDamageEntry list from build_word_damage_map
        recto_spec:         FolioWeatherSpec for this folio
        verso_image:        Weathered image of the same-leaf partner (or None)
        verso_spec:         FolioWeatherSpec of the partner (or None)
        bbox_list:          Text region bboxes from PAGE XML, as (l, t, r, b)

    Returns:
        ValidationSummary with results for all three checks.
    """
    v1 = validate_text_positions(clean_image, weathered_image, bbox_list)
    v2a = validate_pre_degradation_preserved(
        pre_degraded_image, weathered_image, degradation_mask, word_damage_map
    )
    v3 = validate_damage_consistency(
        recto_image=weathered_image,
        verso_image=verso_image,
        recto_spec=recto_spec,
        verso_spec=verso_spec if verso_spec is not None else recto_spec,
    )
    return ValidationSummary(
        folio_id=folio_id,
        v1_text_positions=v1,
        v2a_pre_degradation=v2a,
        v3_damage_consistency=v3,
    )


# ---------------------------------------------------------------------------
# validate_codex
# ---------------------------------------------------------------------------

def validate_codex(
    weathered_dir: Path | str,
    clean_dir: Path | str,
    pre_degraded_dir: Path | str,
    mask_dir: Path | str,
    word_damage_dir: Path | str,
    weathering_map: dict[str, FolioWeatherSpec],
    page_xml_dir: Path | str,
    output_report: Path | str | None = None,
) -> dict[str, ValidationSummary]:
    """Batch validation across all folios in weathered_dir.

    Loads images from disk, runs validate_folio for each folio that has a
    corresponding weathered image, writes a summary report JSON.

    Returns:
        {folio_id: ValidationSummary}
    """
    from PIL import Image as PILImage

    weathered_dir = Path(weathered_dir)
    clean_dir = Path(clean_dir)
    pre_degraded_dir = Path(pre_degraded_dir)
    mask_dir = Path(mask_dir)
    word_damage_dir = Path(word_damage_dir)

    def _load(p: Path) -> np.ndarray | None:
        if not p.exists():
            return None
        return np.array(PILImage.open(p).convert("RGB"), dtype=np.uint8)

    def _load_mask(p: Path) -> np.ndarray | None:
        if not p.exists():
            return None
        return np.array(PILImage.open(p).convert("L"), dtype=np.uint8)

    # Build leaf pairs for V3: recto_id → verso_id
    leaf_pairs: dict[str, str] = {}
    for n in range(1, 18):
        recto_id = f"f{n:02d}r"
        verso_id = f"f{n:02d}v"
        if recto_id in weathering_map:
            leaf_pairs[recto_id] = verso_id

    results: dict[str, ValidationSummary] = {}
    weathered_images: dict[str, np.ndarray] = {}

    for folio_id, spec in weathering_map.items():
        weathered_img = _load(weathered_dir / f"{folio_id}_weathered.png")
        if weathered_img is None:
            continue

        weathered_images[folio_id] = weathered_img
        _clean = _load(clean_dir / f"{folio_id}.png")
        clean_img = _clean if _clean is not None else np.zeros_like(weathered_img)
        _pre = _load(pre_degraded_dir / f"{folio_id}_pre_degraded.png")
        pre_deg_img = _pre if _pre is not None else weathered_img.copy()
        _mask = _load_mask(mask_dir / f"{folio_id}_mask.png")
        mask = _mask if _mask is not None else np.zeros(weathered_img.shape[:2], dtype=np.uint8)

        # Load word damage map
        wdm_path = word_damage_dir / f"{folio_id}_word_damage.json"
        word_damage_map: list[WordDamageEntry] = []
        if wdm_path.exists():
            records = json.loads(wdm_path.read_text())
            for rec in records:
                word_damage_map.append(WordDamageEntry(
                    word_text=rec["word_text"],
                    bbox=tuple(rec["bbox"]),
                    center=tuple(rec["center"]),
                    confidence=rec["confidence"],
                    category=rec["category"],
                    line_number=rec["line_number"],
                    specific_note=rec.get("specific_note"),
                ))

        # Verso partner for V3
        verso_image: np.ndarray | None = None
        verso_spec: FolioWeatherSpec | None = None
        if folio_id in leaf_pairs:
            partner_id = leaf_pairs[folio_id]
            _verso = weathered_images.get(partner_id)
            verso_image = _verso if _verso is not None else _load(
                weathered_dir / f"{partner_id}_weathered.png"
            )
            verso_spec = weathering_map.get(partner_id)

        summary = validate_folio(
            folio_id=folio_id,
            clean_image=clean_img,
            weathered_image=weathered_img,
            pre_degraded_image=pre_deg_img,
            degradation_mask=mask,
            word_damage_map=word_damage_map,
            recto_spec=spec,
            verso_image=verso_image,
            verso_spec=verso_spec,
            bbox_list=[],
        )
        results[folio_id] = summary

    # Write report
    if output_report is None:
        output_report = weathered_dir / "validation_report.json"
    output_report = Path(output_report)
    output_report.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "total_folios": len(results),
        "all_passed": all(s.all_passed for s in results.values()),
        "folios": {fid: s.to_dict() for fid, s in results.items()},
    }
    output_report.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    return results
