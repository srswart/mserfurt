"""Fitness function for evolutionary word evaluation (TD-007 Part 2).

Seven fitness criteria:
  F1: Letter recognition (template matching + keypoint hits) — weight 0.30
  F2: Thick/thin contrast (stroke width ratio) — weight 0.10
  F3: Connection flow (inter-glyph hairline presence) — weight 0.15
  F4: Style consistency (Bastarda proportions, slant) — weight 0.15
  F5: Target similarity (perceptual features) — weight 0.10
  F6: Smoothness (curvature regularity) — weight 0.10
  F7: Continuity at glyph boundaries — weight 0.10
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.ndimage import label, distance_transform_edt, gaussian_filter

from scribesim.evo.genome import WordGenome, GlyphGenome
from scribesim.evo.renderer import render_word_from_genome


# ---------------------------------------------------------------------------
# Fitness result
# ---------------------------------------------------------------------------

@dataclass
class FitnessResult:
    """Result of evaluating a genome's fitness."""
    f1: float = 0.0   # letter recognition
    f2: float = 0.0   # thick/thin contrast
    f3: float = 0.0   # connection flow
    f4: float = 0.0   # style consistency
    f5: float = 0.0   # target similarity
    f6: float = 0.0   # smoothness
    f7: float = 0.0   # continuity

    @property
    def total(self) -> float:
        return (0.30 * self.f1 + 0.10 * self.f2 + 0.15 * self.f3 +
                0.15 * self.f4 + 0.10 * self.f5 + 0.10 * self.f6 +
                0.10 * self.f7)


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def _to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 3:
        return np.mean(img.astype(np.float32), axis=2) / 255.0
    return img.astype(np.float32) / 255.0


def _binarize(gray: np.ndarray, threshold: float = 0.7) -> np.ndarray:
    return gray < threshold


# ---------------------------------------------------------------------------
# F1: Letter recognition
# ---------------------------------------------------------------------------

def f1_letter_recognition(
    rendered: np.ndarray,
    genome: WordGenome,
    exemplars: dict[str, list[np.ndarray]] | None = None,
) -> float:
    """Keypoint coverage: do the rendered marks pass through expected positions?"""
    from scribesim.guides.catalog import lookup_guide

    gray = _to_gray(rendered)
    binary = _binarize(gray)

    if not binary.any():
        return 0.0

    # For each glyph, check if keypoints are near ink
    scores = []
    px_per_mm = rendered.shape[1] / max(genome.word_width_mm + 4.0, 1.0)

    for gi, glyph in enumerate(genome.glyphs):
        guide = lookup_guide(glyph.letter)
        if guide is None:
            scores.append(0.5)  # neutral for unguided letters
            continue

        hits = 0
        for kp in guide.keypoints:
            if not kp.contact:
                continue
            # Convert keypoint to pixel coords
            kp_x_mm = glyph.x_offset + kp.x * 3.8  # approximate x_height
            kp_y_mm = genome.baseline_y - kp.y * 3.8
            kp_x_px = int(kp_x_mm * px_per_mm)
            kp_y_px = int(kp_y_mm * px_per_mm)

            # Check if there's ink near this position
            r = max(3, int(kp.flexibility_mm * px_per_mm))
            y0 = max(0, kp_y_px - r)
            y1 = min(binary.shape[0], kp_y_px + r)
            x0 = max(0, kp_x_px - r)
            x1 = min(binary.shape[1], kp_x_px + r)

            if y1 > y0 and x1 > x0:
                region = binary[y0:y1, x0:x1]
                if region.any():
                    hits += 1

        contact_kps = sum(1 for kp in guide.keypoints if kp.contact)
        scores.append(hits / max(contact_kps, 1))

    return sum(scores) / max(len(scores), 1)


# ---------------------------------------------------------------------------
# F2: Thick/thin contrast
# ---------------------------------------------------------------------------

def f2_thick_thin(rendered: np.ndarray) -> float:
    """Stroke width ratio should be 3:1 to 5:1."""
    gray = _to_gray(rendered)
    binary = _binarize(gray)

    if not binary.any():
        return 0.0

    dt = distance_transform_edt(binary)
    widths = dt[binary & (dt > 0.5)]

    if len(widths) < 10:
        return 0.0

    max_w = np.percentile(widths, 95)
    min_w = np.percentile(widths, 5)
    if min_w < 0.1:
        min_w = 0.1

    ratio = max_w / min_w
    target = 4.0

    return max(0.0, 1.0 - abs(ratio - target) / target)


# ---------------------------------------------------------------------------
# F3: Connection flow
# ---------------------------------------------------------------------------

def f3_connection_flow(rendered: np.ndarray, genome: WordGenome) -> float:
    """Adjacent glyphs should be connected by visible hairline strokes."""
    if len(genome.glyphs) < 2:
        return 1.0

    gray = _to_gray(rendered)
    binary = _binarize(gray)
    px_per_mm = rendered.shape[1] / max(genome.word_width_mm + 4.0, 1.0)

    connections_good = 0
    n_connections = len(genome.glyphs) - 1

    for i in range(n_connections):
        g1 = genome.glyphs[i]
        g2 = genome.glyphs[i + 1]

        # Zone between glyphs
        x0 = int((g1.x_offset + g1.x_advance) * px_per_mm)
        x1 = int(g2.x_offset * px_per_mm)
        x0 = max(0, min(x0, binary.shape[1] - 1))
        x1 = max(x0 + 1, min(x1, binary.shape[1]))

        zone = binary[:, x0:x1]
        if zone.any():
            connections_good += 1

    return connections_good / max(n_connections, 1)


# ---------------------------------------------------------------------------
# F4: Style consistency (Bastarda)
# ---------------------------------------------------------------------------

def f4_style_consistency(rendered: np.ndarray, genome: WordGenome) -> float:
    """Bastarda style: ~3-5° slant, consistent proportions."""
    scores = []

    # Slant check
    slant = genome.global_slant_deg
    slant_score = max(0.0, 1.0 - abs(slant - 4.0) / 10.0)
    scores.append(slant_score)

    # Ink density: should have both ink and whitespace (not blank, not solid)
    gray = _to_gray(rendered)
    binary = _binarize(gray)
    ink_ratio = binary.mean()
    # Good range: 5-30% ink
    if 0.05 <= ink_ratio <= 0.30:
        scores.append(1.0)
    elif ink_ratio < 0.01 or ink_ratio > 0.50:
        scores.append(0.0)
    else:
        scores.append(0.5)

    # Width regularity: glyphs should have similar widths (within category)
    if len(genome.glyphs) >= 2:
        advances = [g.x_advance for g in genome.glyphs]
        cv = np.std(advances) / max(np.mean(advances), 0.01)
        scores.append(max(0.0, 1.0 - cv))

    return sum(scores) / max(len(scores), 1)


# ---------------------------------------------------------------------------
# F5: Target similarity (perceptual)
# ---------------------------------------------------------------------------

def f5_target_similarity(
    rendered: np.ndarray,
    target_crop: np.ndarray | None = None,
) -> float:
    """Perceptual similarity to target manuscript crop."""
    if target_crop is None:
        return 0.5  # neutral when no target

    # Simple: normalized cross-correlation on grayscale
    g_r = _to_gray(rendered)
    g_t = _to_gray(target_crop)

    # Resize to match
    from PIL import Image
    h = min(g_r.shape[0], g_t.shape[0], 64)
    w = min(g_r.shape[1], g_t.shape[1], 128)
    r_resized = np.array(Image.fromarray((g_r * 255).astype(np.uint8)).resize((w, h))) / 255.0
    t_resized = np.array(Image.fromarray((g_t * 255).astype(np.uint8)).resize((w, h))) / 255.0

    # NCC
    r_norm = r_resized - r_resized.mean()
    t_norm = t_resized - t_resized.mean()
    denom = max(np.sqrt((r_norm**2).sum() * (t_norm**2).sum()), 1e-8)
    ncc = (r_norm * t_norm).sum() / denom

    return max(0.0, min(1.0, (ncc + 1.0) / 2.0))  # map [-1,1] to [0,1]


# ---------------------------------------------------------------------------
# F6: Smoothness
# ---------------------------------------------------------------------------

def f6_smoothness(genome: WordGenome) -> float:
    """Strokes should be smooth curves, not jagged."""
    penalty = 0.0

    for glyph in genome.glyphs:
        for seg in glyph.segments:
            # Sample curvature at several points
            curvatures = []
            for i in range(20):
                t = i / 19.0
                dx, dy = seg.tangent(t)
                curvatures.append(math.atan2(dy, dx))

            # Penalize sudden curvature changes
            for i in range(len(curvatures) - 1):
                change = abs(curvatures[i + 1] - curvatures[i])
                if change > math.pi:
                    change = 2 * math.pi - change  # handle wrap
                if change > 0.5:
                    penalty += change - 0.5

    return 1.0 / (1.0 + penalty)


# ---------------------------------------------------------------------------
# F7: Continuity at glyph boundaries
# ---------------------------------------------------------------------------

def f7_continuity(genome: WordGenome) -> float:
    """Exit of glyph N should smoothly connect to entry of glyph N+1."""
    if len(genome.glyphs) < 2:
        return 1.0

    penalty = 0.0

    for i in range(len(genome.glyphs) - 1):
        exit_pt = genome.glyphs[i].exit_point
        entry_pt = genome.glyphs[i + 1].entry_point

        # Position gap
        gap = math.sqrt((exit_pt[0] - entry_pt[0])**2 + (exit_pt[1] - entry_pt[1])**2)
        penalty += gap

        # Direction gap
        exit_tan = genome.glyphs[i].exit_tangent()
        entry_tan = genome.glyphs[i + 1].entry_tangent()
        exit_angle = math.atan2(exit_tan[1], exit_tan[0])
        entry_angle = math.atan2(entry_tan[1], entry_tan[0])
        angle_gap = abs(exit_angle - entry_angle)
        if angle_gap > math.pi:
            angle_gap = 2 * math.pi - angle_gap
        penalty += angle_gap * 0.3

    return 1.0 / (1.0 + penalty)


# ---------------------------------------------------------------------------
# Composite fitness
# ---------------------------------------------------------------------------

def evaluate_fitness(
    genome: WordGenome,
    target_crop: np.ndarray | None = None,
    exemplars: dict[str, list[np.ndarray]] | None = None,
    dpi: float = 100.0,
) -> FitnessResult:
    """Evaluate all 7 fitness criteria for a genome.

    Args:
        genome: The word genome to evaluate.
        target_crop: Optional target manuscript word image.
        exemplars: Optional per-letter exemplar images for F1.
        dpi: Rendering resolution for evaluation.

    Returns:
        FitnessResult with all 7 scores and composite total.
    """
    rendered = render_word_from_genome(genome, dpi=dpi)

    return FitnessResult(
        f1=f1_letter_recognition(rendered, genome, exemplars),
        f2=f2_thick_thin(rendered),
        f3=f3_connection_flow(rendered, genome),
        f4=f4_style_consistency(rendered, genome),
        f5=f5_target_similarity(rendered, target_crop),
        f6=f6_smoothness(genome),
        f7=f7_continuity(genome),
    )
