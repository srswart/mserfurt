"""Groundtruth orchestrator — update PAGE XML from compositor result."""

from __future__ import annotations

from pathlib import Path

from weather.compositor.compositor import CompositorResult
from weather.groundtruth.pagexml import update_groundtruth


def apply_groundtruth(
    xml_path: Path,
    out_path: Path,
    result: CompositorResult,
) -> None:
    """Update PAGE XML coordinates and legibility from a compositor result.

    Reads the ScribeSim PAGE XML at *xml_path*, applies curl coordinate
    transform and damage legibility scores from *result*, and writes the
    updated XML to *out_path*.

    Args:
        xml_path: Path to the source PAGE XML (ScribeSim output).
        out_path: Path to write the updated PAGE XML.
        result:   CompositorResult from composite_folio().
    """
    xml_str = Path(xml_path).read_text(encoding="utf-8")

    # Determine image dimensions from the compositor result image
    img_w, img_h = result.image.width, result.image.height

    updated = update_groundtruth(
        xml_str,
        img_w=img_w,
        img_h=img_h,
        curl_transform=result.curl_transform,
        water_zone=result.water_zone,
        corner_mask=result.corner_mask,
    )

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(updated, encoding="utf-8")
