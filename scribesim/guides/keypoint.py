"""Keypoint and LetterformGuide data structures.

A Keypoint is a structural position the hand must pass through.
A LetterformGuide is a set of keypoints that defines a letter.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Keypoint:
    """A structural point that defines part of a letter's identity.

    The hand steers through these in sequence. The path between
    keypoints is determined by the hand's dynamics, not prescribed.

    Coordinates are in x-height units relative to the glyph origin
    (x=0 at left edge, y=0 at baseline, y=1.0 at x-height top).
    """
    x: float                    # horizontal position (x-height units)
    y: float                    # vertical position (0=baseline, 1=x-height)
    point_type: str = "stroke"  # "peak", "base", "junction", "loop_apex", "entry", "exit"
    contact: bool = True        # should the nib be touching here?
    direction_deg: float = 270.0  # preferred approach direction (270° = downward)
    flexibility_mm: float = 0.2   # how far from this point is acceptable


@dataclass
class LetterformGuide:
    """Minimal definition of a letter for the hand simulator.

    NOT a complete trajectory — just the structural keypoints that
    make this letter recognizable. Two instances of the same letter
    have the same keypoints but different paths between them because
    the hand arrives from different directions at different speeds.
    """
    letter: str
    keypoints: tuple[Keypoint, ...]
    x_advance: float        # typical horizontal extent (x-height units)
    ascender: bool = False
    descender: bool = False
    # Context variants (future: adjust keypoints based on neighbors)
    variants: dict = field(default_factory=dict)
