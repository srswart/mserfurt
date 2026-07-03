"""Deterministic stub backends for CPU-only development and pipeline tests.

``PILStubBackend`` draws words with a PIL bitmap font — fast, dependency-free,
used by unit tests. ``EvoStubBackend`` renders through the existing evo
Bastarda engine — slower, but produces realistic strips for end-to-end
composition/bench testing without any learned model.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scribesim.scribehand.types import WordRequest, WordStrip


class PILStubBackend:
    """Bitmap-font word strips. For plumbing tests only — looks like a font
    because it is one."""

    name = "stub-pil"

    _CHAR_W = 12
    _HEIGHT = 48
    _BASELINE_FRAC = 0.72
    _XHEIGHT_FRAC = 0.30

    def generate_batch(self, requests: list[WordRequest]) -> list[WordStrip]:
        return [self._one(r) for r in requests]

    def _one(self, req: WordRequest) -> WordStrip:
        rng = np.random.default_rng(req.seed)
        w = max(16, self._CHAR_W * len(req.text) + 8)
        img = Image.new("L", (w, self._HEIGHT), 0)
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        # Small seeded offset so different seeds are distinguishable.
        dx = int(rng.integers(0, 3))
        dy = int(rng.integers(0, 3))
        draw.text((2 + dx, 14 + dy), req.text, fill=255, font=font)
        return WordStrip(
            ink=np.asarray(img, dtype=np.uint8),
            baseline_frac=self._BASELINE_FRAC,
            xheight_frac=self._XHEIGHT_FRAC,
        )


class EvoStubBackend:
    """Word strips rendered by the existing evo Bastarda engine.

    Serves as the CPU-visualizable stand-in for a learned backend so page
    composition, verification, and bench plumbing can be exercised end to end.
    """

    name = "stub-evo"

    _X_HEIGHT_MM = 3.0
    _CANVAS_H_MM = 11.0
    _BASELINE_Y_MM = 7.5
    _DPI = 300.0

    def generate_batch(self, requests: list[WordRequest]) -> list[WordStrip]:
        return [self._one(r) for r in requests]

    def _one(self, req: WordRequest) -> WordStrip:
        import random as _random

        from scribesim.evo.genome import genome_from_guides
        from scribesim.evo.renderer import render_word_from_genome, _PARCHMENT

        # The evo renderer draws per-instance jitter from the global `random`
        # module; seed it for per-request determinism.
        _random.seed(req.seed)
        genome = genome_from_guides(
            req.text,
            baseline_y_mm=self._BASELINE_Y_MM,
            x_height_mm=self._X_HEIGHT_MM,
        )
        rgb = render_word_from_genome(
            genome,
            dpi=self._DPI,
            nib_width_mm=0.5,
            canvas_height_mm=self._CANVAS_H_MM,
            variation=1.0,
        )
        # Convert the parchment-background RGB render to an ink mask: distance
        # from parchment along the darkening axis, scaled to 0..255.
        arr = rgb.astype(np.int16)
        parchment = np.array(_PARCHMENT, dtype=np.int16)
        deficit = np.clip(parchment[None, None, :] - arr, 0, None).max(axis=2)
        max_deficit = max(1, int(parchment.max()))
        ink = np.clip(deficit.astype(np.float32) / max_deficit * 255.0, 0, 255).astype(np.uint8)

        return WordStrip(
            ink=ink,
            baseline_frac=self._BASELINE_Y_MM / self._CANVAS_H_MM,
            xheight_frac=self._X_HEIGHT_MM / self._CANVAS_H_MM,
        )
