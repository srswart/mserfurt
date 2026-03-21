"""Ink-substrate interaction filters (TD-002 Part 3).

Five post-rasterization filters that transform rendered ink into a
physically-motivated ink layer:
  1. Saturation — pressure-dependent darkness
  2. Pooling — dark dots at stroke terminations
  3. Wicking — anisotropic blur along vellum grain
  4. Feathering — edge softening on thin strokes
  5. Depletion — periodic ink darkness cycle (~35 words per dip)
"""

from scribesim.ink.filters import apply_ink_filters

__all__ = ["apply_ink_filters"]
