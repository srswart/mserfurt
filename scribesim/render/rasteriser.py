"""Rasterise glyph layout to PNG — stub pending ADV-SS-RENDER-001."""

from __future__ import annotations

from pathlib import Path


def render_page(layout: dict, hand_params: dict, output_path: Path) -> Path:
    """Render the glyph layout to a 300 DPI page PNG.

    Raises:
        NotImplementedError: Until ADV-SS-RENDER-001 is implemented.
    """
    raise NotImplementedError("Render not yet implemented (ADV-SS-RENDER-001)")


def render_heatmap(layout: dict, hand_params: dict, output_path: Path) -> Path:
    """Render the pressure heatmap PNG (TD-001-F).

    Raises:
        NotImplementedError: Until ADV-SS-RENDER-001 is implemented.
    """
    raise NotImplementedError("Heatmap not yet implemented (ADV-SS-RENDER-001)")
