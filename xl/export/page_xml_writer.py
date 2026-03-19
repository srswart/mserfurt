"""TD-001-C serializer — FolioPage → PAGE XML 2019."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from xl.models import FolioPage

PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = (
    f"{PAGE_NS} "
    f"{PAGE_NS}/pagecontent.xsd"
)

# Placeholder canvas: 0,0 to 1000,1000 per TD-001-C
_CANVAS = 1000
# Minimum line height slot (used when page is empty)
_MIN_LINE_HEIGHT = 28


def build_page_xml(page: FolioPage) -> str:
    """Serialize a FolioPage to a TD-001-C PAGE XML string."""
    ET.register_namespace("", PAGE_NS)
    ET.register_namespace("xsi", XSI_NS)

    root = ET.Element(
        f"{{{PAGE_NS}}}PcGts",
        attrib={
            f"{{{XSI_NS}}}schemaLocation": SCHEMA_LOCATION,
        },
    )

    # <Metadata>
    meta_el = ET.SubElement(root, f"{{{PAGE_NS}}}Metadata")
    ET.SubElement(meta_el, f"{{{PAGE_NS}}}Creator").text = "xl-export"
    ET.SubElement(meta_el, f"{{{PAGE_NS}}}Created").text = "2026-03-19T00:00:00Z"
    ET.SubElement(meta_el, f"{{{PAGE_NS}}}LastChange").text = "2026-03-19T00:00:00Z"

    # <Page imageFilename="" imageWidth="1000" imageHeight="1000">
    page_el = ET.SubElement(
        root,
        f"{{{PAGE_NS}}}Page",
        attrib={
            "imageFilename": "",
            "imageWidth": str(_CANVAS),
            "imageHeight": str(_CANVAS),
        },
    )

    # <TextRegion id="r1" custom="type:paragraph">
    region = ET.SubElement(
        page_el,
        f"{{{PAGE_NS}}}TextRegion",
        attrib={"id": "r1", "custom": "type:paragraph"},
    )
    ET.SubElement(
        region,
        f"{{{PAGE_NS}}}Coords",
        attrib={"points": f"0,0 {_CANVAS},0 {_CANVAS},{_CANVAS} 0,{_CANVAS}"},
    )

    n_lines = max(len(page.lines), 1)
    line_h = _CANVAS // n_lines

    for idx, line in enumerate(page.lines):
        y_top = idx * line_h
        y_bot = (idx + 1) * line_h

        line_el = ET.SubElement(
            region,
            f"{{{PAGE_NS}}}TextLine",
            attrib={
                "id": f"l{line.number}",
                "custom": f"register:{line.register}",
            },
        )
        ET.SubElement(
            line_el,
            f"{{{PAGE_NS}}}Coords",
            attrib={
                "points": (
                    f"0,{y_top} {_CANVAS},{y_top} "
                    f"{_CANVAS},{y_bot} 0,{y_bot}"
                )
            },
        )
        ET.SubElement(
            line_el,
            f"{{{PAGE_NS}}}Baseline",
            attrib={"points": f"0,{y_bot - 2} {_CANVAS},{y_bot - 2}"},
        )

        # TextEquiv index=0: German/Latin text
        te0 = ET.SubElement(
            line_el, f"{{{PAGE_NS}}}TextEquiv", attrib={"index": "0"}
        )
        ET.SubElement(te0, f"{{{PAGE_NS}}}Unicode").text = line.text

        # TextEquiv index=1: English original (if present)
        if line.english:
            te1 = ET.SubElement(
                line_el, f"{{{PAGE_NS}}}TextEquiv", attrib={"index": "1"}
            )
            ET.SubElement(te1, f"{{{PAGE_NS}}}Unicode").text = line.english

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def write_page_xml(page: FolioPage, output_dir: Path) -> Path:
    """Write PAGE XML to output_dir/{folio_id}.xml."""
    path = Path(output_dir) / f"{page.id}.xml"
    path.write_text(build_page_xml(page), encoding=None)
    return path
