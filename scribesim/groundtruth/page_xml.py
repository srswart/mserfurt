"""Generate PAGE XML 2019 ground truth (TD-001-C).

Hierarchy produced:
    PcGts > Metadata + Page > TextRegion > TextLine > Word > Glyph

Coordinates are in pixel space at 300 DPI (matching render output).
The @custom attribute on TextEquiv carries the register, e.g. "register:german".

Schema namespace: http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from scribesim.layout.positioned import PageLayout, PositionedGlyph

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
_XSI = "http://www.w3.org/2001/XMLSchema-instance"
_SCHEMA_LOC = (
    "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15 "
    "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15/pagecontent.xsd"
)
_DPI = 300
_MM_PER_INCH = 25.4
_PX_PER_MM = _DPI / _MM_PER_INCH   # ≈ 11.811


def _mm_to_px(mm: float) -> int:
    return round(mm * _PX_PER_MM)


def _pt(x_mm: float, y_mm: float) -> str:
    """Format a single coordinate pair for PAGE XML points attribute."""
    return f"{_mm_to_px(x_mm)},{_mm_to_px(y_mm)}"


def _rect_points(x_mm: float, y_mm: float, w_mm: float, h_mm: float) -> str:
    """Four-corner polygon for a rectangle (top-left going clockwise)."""
    x0, y0 = _mm_to_px(x_mm), _mm_to_px(y_mm)
    x1, y1 = _mm_to_px(x_mm + w_mm), _mm_to_px(y_mm + h_mm)
    return f"{x0},{y0} {x1},{y0} {x1},{y1} {x0},{y1}"


def _tag(name: str) -> str:
    return f"{{{_NS}}}{name}"


# ---------------------------------------------------------------------------
# Glyph → character mapping (reverse of layout's char_to_glyph_id)
# ---------------------------------------------------------------------------

def _glyph_id_to_char(glyph_id: str) -> str:
    """Best-effort Unicode character for a glyph catalog key."""
    _MAP = {
        "long_s": "ſ", "round_s": "s", "esszett": "ß",
        "a_umlaut": "ä", "o_umlaut": "ö", "u_umlaut": "ü",
        "A_umlaut": "Ä", "O_umlaut": "Ö", "U_umlaut": "Ü",
        "ae": "æ", "oe": "œ",
        "section": "§", "pilcrow": "¶", "et": "&", "con": "ꝯ",
        "period": ".", "comma": ",", "colon": ":", "semicolon": ";",
        "hyphen": "-", "exclamation": "!", "question": "?", "macron": "̄",
    }
    if glyph_id in _MAP:
        return _MAP[glyph_id]
    # digits and single-char ids map directly
    if len(glyph_id) == 1:
        return glyph_id
    return glyph_id  # fallback


def _register_from_glyph(glyph_id: str, line_register: str) -> str:
    """Determine text register for a glyph."""
    if glyph_id in ("long_s", "a_umlaut", "o_umlaut", "u_umlaut",
                    "A_umlaut", "O_umlaut", "U_umlaut", "esszett"):
        return "german"
    return line_register


# ---------------------------------------------------------------------------
# Word grouping — consecutive non-space glyphs form a Word
# ---------------------------------------------------------------------------

def _group_words(glyphs: list) -> list[list]:
    """Partition a line's glyph list into word groups."""
    words: list[list] = []
    current: list = []
    for pg in glyphs:
        # Space glyphs (mapped to "period" as placeholder) with very small advance
        # are treated as word separators if isolated.  In practice, inter-word gaps
        # in the layout are represented by cursor advance without a glyph entry,
        # so all entries here ARE ink glyphs — just split by x-gap heuristic.
        current.append(pg)
    if current:
        words.append(current)

    # Re-split by x-coordinate gaps: a gap > 2× average advance signals a word break
    if not words or not words[0]:
        return words
    all_glyphs = words[0]
    if len(all_glyphs) < 2:
        return [all_glyphs]

    advances = [pg.advance_w_mm for pg in all_glyphs]
    avg_adv = sum(advances) / len(advances)
    threshold = avg_adv * 2.5

    result: list[list] = []
    group: list = [all_glyphs[0]]
    for prev, cur in zip(all_glyphs, all_glyphs[1:]):
        gap = cur.x_mm - (prev.x_mm + prev.advance_w_mm)
        if gap > threshold:
            result.append(group)
            group = [cur]
        else:
            group.append(cur)
    result.append(group)
    return result


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def generate(
    layout: PageLayout | None,
    output_path: Path,
    folio_id: str = "",
    image_filename: str = "",
) -> Path:
    """Emit PAGE XML 2019 ground truth from a PageLayout.

    Args:
        layout:         PageLayout from scribesim.layout.place(), or None for
                        an empty-page stub.
        output_path:    Destination path for the XML file.
        folio_id:       Override folio ID (used when layout is None).
        image_filename: Override image filename in Page element.

    Returns:
        output_path after writing.
    """
    ET.register_namespace("", _NS)
    ET.register_namespace("xsi", _XSI)

    fid = folio_id or (layout.folio_id if layout else "unknown")
    img_fn = image_filename or f"{fid}.png"

    if layout is not None:
        g = layout.geometry
        img_w = _mm_to_px(g.page_w_mm)
        img_h = _mm_to_px(g.page_h_mm)
    else:
        img_w, img_h = 3307, 4724   # 300 DPI × 280×400 mm default

    # ---- Root & Metadata ----
    root = ET.Element(_tag("PcGts"), {
        f"{{{_XSI}}}schemaLocation": _SCHEMA_LOC,
    })
    meta = ET.SubElement(root, _tag("Metadata"))
    ET.SubElement(meta, _tag("Creator")).text = "ScribeSim ADV-SS-GROUNDTRUTH-001"
    ET.SubElement(meta, _tag("LastChange")).text = (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    )

    # ---- Page ----
    page_el = ET.SubElement(root, _tag("Page"), {
        "imageFilename": img_fn,
        "imageWidth": str(img_w),
        "imageHeight": str(img_h),
    })

    if layout is None or not layout.lines:
        # Empty page stub
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _write(root, output_path)
        return output_path

    g = layout.geometry

    # ---- TextRegion spanning full text block ----
    text_block_pts = _rect_points(
        g.margin_inner, g.margin_top,
        g.text_w_mm, g.text_h_mm,
    )
    region = ET.SubElement(page_el, _tag("TextRegion"), {
        "id": "r1",
        "custom": "type:paragraph",
    })
    ET.SubElement(region, _tag("Coords"), {"points": text_block_pts})

    id_counters = {"l": 0, "w": 0, "gl": 0}

    for line_layout in layout.lines:
        id_counters["l"] += 1
        line_id = f"l{id_counters['l']}"

        glyphs = line_layout.glyphs
        if not glyphs:
            continue

        # TextLine bounding box
        x0 = min(pg.x_mm for pg in glyphs)
        x1 = max(pg.x_mm + pg.advance_w_mm for pg in glyphs)
        y0 = line_layout.y_mm
        y1 = line_layout.y_mm + g.ruling_pitch_mm

        line_el = ET.SubElement(region, _tag("TextLine"), {
            "id": line_id,
        })
        ET.SubElement(line_el, _tag("Coords"), {
            "points": _rect_points(x0, y0, x1 - x0, y1 - y0),
        })

        # Baseline — polyline through midpoints of each glyph's baseline
        baseline_pts = " ".join(
            _pt(pg.x_mm + pg.advance_w_mm * 0.5, pg.baseline_y_mm)
            for pg in glyphs
        )
        ET.SubElement(line_el, _tag("Baseline"), {"points": baseline_pts})

        # Words
        words = _group_words(glyphs)
        line_register = "german"  # default; could be read from line metadata

        for word_glyphs in words:
            if not word_glyphs:
                continue
            id_counters["w"] += 1
            word_id = f"w{id_counters['w']}"

            wx0 = min(pg.x_mm for pg in word_glyphs)
            wx1 = max(pg.x_mm + pg.advance_w_mm for pg in word_glyphs)
            wy0 = y0
            wy1 = y1

            word_el = ET.SubElement(line_el, _tag("Word"), {"id": word_id})
            ET.SubElement(word_el, _tag("Coords"), {
                "points": _rect_points(wx0, wy0, wx1 - wx0, wy1 - wy0),
            })

            for pg in word_glyphs:
                id_counters["gl"] += 1
                glyph_id_str = f"g{id_counters['gl']}"

                x_height_mm = g.ruling_pitch_mm
                glyph_el = ET.SubElement(word_el, _tag("Glyph"), {
                    "id": glyph_id_str,
                })
                # Glyph bounding box: x_mm, baseline_y - x_height → advance_w × x_height
                ET.SubElement(glyph_el, _tag("Coords"), {
                    "points": _rect_points(
                        pg.x_mm, pg.baseline_y_mm - x_height_mm,
                        pg.advance_w_mm, x_height_mm,
                    ),
                })

                char = _glyph_id_to_char(pg.glyph_id)
                register = _register_from_glyph(pg.glyph_id, line_register)
                te = ET.SubElement(glyph_el, _tag("TextEquiv"), {
                    "custom": f"register:{register}",
                })
                ET.SubElement(te, _tag("Unicode")).text = char

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write(root, output_path)
    return output_path


def _write(root: ET.Element, path: Path) -> None:
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(str(path), encoding="UTF-8", xml_declaration=True)
