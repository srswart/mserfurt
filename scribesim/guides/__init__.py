"""Letterform guide library (TD-005 Part 3).

Minimal keypoint-based letter definitions that the hand simulator
steers through. NOT complete trajectories — just the structural
points that define each letter's identity.
"""

from scribesim.guides.catalog import GUIDE_CATALOG, lookup_guide
from scribesim.guides.keypoint import Keypoint, LetterformGuide

__all__ = ["GUIDE_CATALOG", "lookup_guide", "Keypoint", "LetterformGuide"]
