"""Multi-scale movement model (TD-002 Part 1).

Four nested scales of movement compose additively to produce
naturalistic variation in glyph placement:
  1. PagePosture  — page rotation, margin drift
  2. LineTrajectory — baseline undulation, start-x jitter
  3. WordEnvelope — per-word baseline offset, spacing variation
  4. GlyphTrajectory — per-glyph baseline jitter
"""

from scribesim.movement.movement import apply_movement

__all__ = ["apply_movement"]
