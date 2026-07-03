"""Word-level PAGE XML 2019 for neural folio renders (TD-018 §2.6).

Emits TextRegion → TextLine → Word with exact bounding boxes from the
composition step. Glyph-level polygons are intentionally absent — they can be
recovered via forced alignment when a downstream consumer needs them
(TD-001 addendum pending).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from scribesim.scribehand.compose import ComposedFolio

_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
_XSI = "http://www.w3.org/2001/XMLSchema-instance"
_SCHEMA_LOC = (
    f"{_NS} "
    "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15/pagecontent.xsd"
)


def _tag(name: str) -> str:
    return f"{{{_NS}}}{name}"


def _rect(x: int, y: int, w: int, h: int) -> str:
    return f"{x},{y} {x + w},{y} {x + w},{y + h} {x},{y + h}"


def generate_word_level(composed: ComposedFolio, output_path: Path) -> Path:
    """Write word-level PAGE XML for a composed folio."""
    ET.register_namespace("", _NS)
    ET.register_namespace("xsi", _XSI)

    page_h, page_w = composed.page.shape[:2]

    root = ET.Element(_tag("PcGts"), {f"{{{_XSI}}}schemaLocation": _SCHEMA_LOC})
    meta = ET.SubElement(root, _tag("Metadata"))
    ET.SubElement(meta, _tag("Creator")).text = "ScribeSim ADV-SS-SCRIBEHAND-003 (word-level)"
    ET.SubElement(meta, _tag("LastChange")).text = (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    )

    page_el = ET.SubElement(root, _tag("Page"), {
        "imageFilename": f"{composed.folio_id}.png",
        "imageWidth": str(page_w),
        "imageHeight": str(page_h),
    })

    region = ET.SubElement(page_el, _tag("TextRegion"), {
        "id": "r_text", "type": "paragraph",
    })
    ET.SubElement(region, _tag("Coords"), {
        "points": _rect(0, 0, page_w, page_h),
    })

    for line in composed.lines:
        if not line.words:
            continue
        lx0 = min(w.x_px for w in line.words)
        ly0 = min(w.y_px for w in line.words)
        lx1 = max(w.x_px + w.w_px for w in line.words)
        ly1 = max(w.y_px + w.h_px for w in line.words)

        line_el = ET.SubElement(region, _tag("TextLine"), {
            "id": f"l{line.line_index:03d}",
        })
        ET.SubElement(line_el, _tag("Coords"), {
            "points": _rect(lx0, ly0, lx1 - lx0, ly1 - ly0),
        })
        ET.SubElement(line_el, _tag("Baseline"), {
            "points": f"{lx0},{line.baseline_y_px} {lx1},{line.baseline_y_px}",
        })

        for wi, word in enumerate(line.words):
            word_el = ET.SubElement(line_el, _tag("Word"), {
                "id": f"l{line.line_index:03d}_w{wi:03d}",
            })
            ET.SubElement(word_el, _tag("Coords"), {
                "points": _rect(word.x_px, word.y_px, word.w_px, word.h_px),
            })
            te = ET.SubElement(word_el, _tag("TextEquiv"))
            ET.SubElement(te, _tag("Unicode")).text = word.text

        line_te = ET.SubElement(line_el, _tag("TextEquiv"))
        ET.SubElement(line_te, _tag("Unicode")).text = " ".join(
            w.text for w in line.words
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)
    return output_path
