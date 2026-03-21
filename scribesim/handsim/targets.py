"""Target generation for the hand simulator (TD-002-C).

Produces sequences of TargetPoints that the hand simulator steers through.
Targets are derived from:
  1. Glyph catalog entry/exit points (existing)
  2. Baseline undulation (extracted from movement model)
  3. Ruling imprecision (extracted from imprecision model)
  4. Word-level spacing adjustments

The hand doesn't follow these exactly — they are soft attractors.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from scribesim.hand.profile import HandProfile
from scribesim.glyphs.catalog import GLYPH_CATALOG
from scribesim.layout.geometry import PageGeometry, make_geometry, _PX_TO_MM


# ---------------------------------------------------------------------------
# Target point
# ---------------------------------------------------------------------------

@dataclass
class TargetPoint:
    """A position the hand should steer toward.

    Not a hard waypoint — the hand arrives *near* this position,
    influenced by its current velocity, acceleration limits, and
    upcoming targets.
    """
    x_mm: float              # absolute x position on page (mm)
    y_mm: float              # absolute y position on page (mm)
    point_type: str = "stroke"  # "stroke", "peak", "base", "junction", "lift", "entry", "exit"
    contact: bool = True     # should the nib be touching here?
    direction_deg: float = 0.0  # preferred approach direction
    flexibility_mm: float = 0.2  # how far from this point is acceptable


@dataclass
class WordTargets:
    """Target sequence for one word."""
    word: str
    targets: list[TargetPoint]
    x_start_mm: float
    x_end_mm: float


@dataclass
class LineTargets:
    """Target sequence for one line."""
    line_index: int
    baseline_y_mm: float
    words: list[WordTargets]


# ---------------------------------------------------------------------------
# Generate targets from glyph catalog
# ---------------------------------------------------------------------------

def _glyph_targets(
    glyph_id: str,
    x_mm: float,
    baseline_y_mm: float,
    x_height_mm: float,
) -> list[TargetPoint]:
    """Generate target points for a single glyph from the catalog.

    Uses the glyph's stroke start/end points as targets.
    """
    glyph = GLYPH_CATALOG.get(glyph_id)
    if glyph is None:
        return []

    targets = []
    for stroke in glyph.strokes:
        pts = stroke.control_points
        # Start point
        targets.append(TargetPoint(
            x_mm=x_mm + pts[0][0] * x_height_mm,
            y_mm=baseline_y_mm - pts[0][1] * x_height_mm,
            point_type="stroke",
            contact=True,
            direction_deg=0.0,
        ))
        # End point
        targets.append(TargetPoint(
            x_mm=x_mm + pts[-1][0] * x_height_mm,
            y_mm=baseline_y_mm - pts[-1][1] * x_height_mm,
            point_type="stroke",
            contact=True,
            direction_deg=0.0,
        ))

    return targets


def _guide_targets(
    letter: str,
    x_mm: float,
    baseline_y_mm: float,
    x_height_mm: float,
) -> list[TargetPoint] | None:
    """Generate targets from a letterform guide (TD-005).

    Returns None if no guide exists for this letter (falls back to glyph catalog).
    """
    from scribesim.guides.catalog import lookup_guide

    guide = lookup_guide(letter)
    if guide is None:
        return None

    targets = []
    for kp in guide.keypoints:
        targets.append(TargetPoint(
            x_mm=x_mm + kp.x * x_height_mm,
            y_mm=baseline_y_mm - kp.y * x_height_mm,
            point_type=kp.point_type,
            contact=kp.contact,
            direction_deg=kp.direction_deg,
            flexibility_mm=kp.flexibility_mm,
        ))
    return targets


def plan_word(
    word: str,
    x_start_mm: float,
    baseline_y_mm: float,
    x_height_mm: float,
    profile: HandProfile,
    register: str = "german",
) -> WordTargets:
    """Generate a target sequence for a word.

    Creates targets from glyph catalog entries, with connections
    between letters marked as lift points.
    """
    from scribesim.layout.linebreak import char_to_glyph_id, _advance_mm
    from scribesim.hand.params import HandParams

    # Build a temporary HandParams for advance width calculation
    params = profile.to_v1()

    targets: list[TargetPoint] = []
    x = x_start_mm

    # Entry target
    targets.append(TargetPoint(
        x_mm=x, y_mm=baseline_y_mm,
        point_type="entry", contact=False,
        flexibility_mm=profile.letterform.keypoint_flexibility_mm,
    ))

    for i, ch in enumerate(word):
        glyph_id = char_to_glyph_id(ch, register)
        adv = _advance_mm(glyph_id, params)

        # Prefer letterform guides (TD-005) over glyph catalog
        guide_tgts = _guide_targets(ch, x, baseline_y_mm, x_height_mm)
        if guide_tgts is not None:
            targets.extend(guide_tgts)
        else:
            # Fallback to glyph catalog
            glyph_tgts = _glyph_targets(glyph_id, x, baseline_y_mm, x_height_mm)
            targets.extend(glyph_tgts)

        # Connection target between letters (not at word end)
        if i < len(word) - 1:
            glyph = GLYPH_CATALOG.get(glyph_id)
            if glyph and glyph.exit_point:
                exit_x = x + glyph.exit_point[0] * x_height_mm
                exit_y = baseline_y_mm - glyph.exit_point[1] * x_height_mm
                # Connection: slight lift between letters
                targets.append(TargetPoint(
                    x_mm=exit_x + 0.3 * x_height_mm,
                    y_mm=exit_y - 0.5 * x_height_mm,  # arc upward
                    point_type="lift",
                    contact=False,
                    flexibility_mm=0.5,
                ))

        x += adv

    # Exit target
    targets.append(TargetPoint(
        x_mm=x, y_mm=baseline_y_mm,
        point_type="exit", contact=False,
        flexibility_mm=profile.letterform.keypoint_flexibility_mm,
    ))

    return WordTargets(word=word, targets=targets, x_start_mm=x_start_mm, x_end_mm=x)


def plan_line(
    text: str,
    line_index: int,
    geom: PageGeometry,
    profile: HandProfile,
    seed: int = 0,
    register: str = "german",
) -> LineTargets:
    """Generate target sequence for a full text line.

    Applies baseline undulation and ruling imprecision to target positions.
    """
    from scribesim.movement.imprecision import ruling_imprecision

    x_height_mm = geom.x_height_mm
    baseline_y = geom.ruling_y(line_index) + x_height_mm

    # Apply ruling imprecision
    offsets = ruling_imprecision(line_index + 1, profile, seed)
    if offsets:
        baseline_y += offsets[line_index]

    # Split text into words and generate targets
    words_text = text.split()
    x = geom.margin_inner
    params = profile.to_v1()

    word_targets_list = []
    for w in words_text:
        wt = plan_word(w, x, baseline_y, x_height_mm, profile, register)
        word_targets_list.append(wt)
        x = wt.x_end_mm + _advance_mm_space(params) * x_height_mm

    return LineTargets(
        line_index=line_index,
        baseline_y_mm=baseline_y,
        words=word_targets_list,
    )


def _advance_mm_space(params) -> float:
    """Word spacing in x-height units."""
    return 0.45 * params.word_spacing_norm
