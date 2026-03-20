"""PAGE XML groundtruth updater — apply curl transforms and legibility scores."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional

import numpy as np

from weather.groundtruth.transform import apply_curl_to_points
from weather.groundtruth.legibility import compute_legibility

PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
_NS = {"p": PAGE_NS}

ET.register_namespace("", PAGE_NS)
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")


def _parse_points(points_str: str) -> list[tuple[int, int]]:
    """Parse 'x1,y1 x2,y2 ...' into list of (x, y) tuples."""
    result = []
    for token in points_str.strip().split():
        x, y = token.split(",")
        result.append((int(x), int(y)))
    return result


def _format_points(points: list[tuple[int, int]]) -> str:
    """Format list of (x, y) tuples into 'x1,y1 x2,y2 ...'"""
    return " ".join(f"{x},{y}" for x, y in points)


def _centroid(points: list[tuple[int, int]]) -> tuple[int, int]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (int(sum(xs) / len(xs)), int(sum(ys) / len(ys)))


def update_groundtruth(
    xml_str: str,
    img_w: int,
    img_h: int,
    curl_transform: Optional[np.ndarray] = None,
    water_zone: Optional[np.ndarray] = None,
    corner_mask: Optional[np.ndarray] = None,
) -> str:
    """Update PAGE XML coordinates and add legibility scores.

    For each TextLine:
      - Coords and Baseline points are shifted by the curl displacement map.
      - If the line centroid falls in a damage zone, a ``legibility:X.XX``
        entry is appended to the ``custom`` attribute.

    Args:
        xml_str:         Source PAGE XML string.
        img_w:           Actual weathered image width in pixels.
        img_h:           Actual weathered image height in pixels.
        curl_transform:  Float32 array (H, W, 2) or None.
        water_zone:      Bool array (H, W) or None.
        corner_mask:     Bool array (H, W) or None.

    Returns:
        Updated PAGE XML string.
    """
    root = ET.fromstring(xml_str)
    page_el = root.find(f"{{{PAGE_NS}}}Page")
    if page_el is None:
        return xml_str

    canvas_w = int(page_el.get("imageWidth", img_w))
    canvas_h = int(page_el.get("imageHeight", img_h))

    for region in root.iter(f"{{{PAGE_NS}}}TextRegion"):
        for line in region.findall(f"{{{PAGE_NS}}}TextLine"):
            # Update Coords
            coords_el = line.find(f"{{{PAGE_NS}}}Coords")
            if coords_el is not None:
                pts = _parse_points(coords_el.get("points", ""))
                if pts:
                    pts_shifted = apply_curl_to_points(
                        pts, curl_transform, img_w, img_h, canvas_w, canvas_h
                    )
                    coords_el.set("points", _format_points(pts_shifted))
                    cx, cy = _centroid(pts)  # use original coords for legibility lookup
                else:
                    cx, cy = canvas_w // 2, canvas_h // 2
                    pts_shifted = pts
            else:
                cx, cy = canvas_w // 2, canvas_h // 2

            # Update Baseline
            baseline_el = line.find(f"{{{PAGE_NS}}}Baseline")
            if baseline_el is not None:
                bl_pts = _parse_points(baseline_el.get("points", ""))
                if bl_pts:
                    bl_shifted = apply_curl_to_points(
                        bl_pts, curl_transform, img_w, img_h, canvas_w, canvas_h
                    )
                    baseline_el.set("points", _format_points(bl_shifted))

            # Compute legibility (only if there is a damage zone)
            if water_zone is not None or corner_mask is not None:
                score = compute_legibility(
                    cx, cy, water_zone, corner_mask,
                    img_w, img_h, canvas_w, canvas_h,
                )
                if score < 1.0:
                    custom = line.get("custom", "")
                    legibility_str = f"legibility:{score:.1f}"
                    if custom:
                        line.set("custom", f"{custom}; {legibility_str}")
                    else:
                        line.set("custom", legibility_str)

    return ET.tostring(root, encoding="unicode", xml_declaration=True)
