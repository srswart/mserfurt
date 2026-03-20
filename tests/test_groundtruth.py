"""Unit tests for scribesim PAGE XML ground truth — ADV-SS-GROUNDTRUTH-001.

RED phase: generate() raises NotImplementedError.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from scribesim.hand.model import load_base, resolve
from scribesim.layout import place, PageLayout
from scribesim.layout.geometry import make_geometry

HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"
GOLDEN_F01R = Path(__file__).parent / "golden" / "f01r" / "folio.json"

_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"


@pytest.fixture
def f01r_layout() -> PageLayout:
    folio = json.loads(GOLDEN_F01R.read_text())
    base = load_base(HAND_TOML)
    params = resolve(base, "f01r")
    return place(folio, params)


@pytest.fixture
def f01r_xml(f01r_layout, tmp_path) -> Path:
    from scribesim.groundtruth.page_xml import generate  # noqa: PLC0415
    out = tmp_path / "f01r.xml"
    generate(f01r_layout, out)
    return out


# ---------------------------------------------------------------------------
# TestGenerateBasic — file and XML structure
# ---------------------------------------------------------------------------

class TestGenerateBasic:
    def _generate(self):
        from scribesim.groundtruth.page_xml import generate  # noqa: PLC0415
        return generate

    def test_writes_file(self, f01r_layout, tmp_path):
        generate = self._generate()
        out = tmp_path / "f01r.xml"
        result = generate(f01r_layout, out)
        assert out.exists()

    def test_returns_path(self, f01r_layout, tmp_path):
        generate = self._generate()
        out = tmp_path / "f01r.xml"
        result = generate(f01r_layout, out)
        assert result == out

    def test_valid_xml(self, f01r_xml):
        tree = ET.parse(str(f01r_xml))
        assert tree.getroot() is not None

    def test_root_is_pcgts(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        assert root.tag == f"{{{_NS}}}PcGts"

    def test_page_element_present(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        page = root.find(f"{{{_NS}}}Page")
        assert page is not None

    def test_page_has_image_filename(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        page = root.find(f"{{{_NS}}}Page")
        assert page.attrib.get("imageFilename"), "Page element missing imageFilename attribute"

    def test_page_has_dimensions(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        page = root.find(f"{{{_NS}}}Page")
        assert "imageWidth" in page.attrib
        assert "imageHeight" in page.attrib
        assert int(page.attrib["imageWidth"]) > 0
        assert int(page.attrib["imageHeight"]) > 0

    def test_metadata_creator_present(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        meta = root.find(f"{{{_NS}}}Metadata")
        assert meta is not None
        creator = meta.find(f"{{{_NS}}}Creator")
        assert creator is not None and creator.text

    def test_empty_layout_produces_valid_xml(self, tmp_path):
        """generate() with None layout must not crash — produces empty page."""
        from scribesim.groundtruth.page_xml import generate  # noqa: PLC0415
        out = tmp_path / "empty.xml"
        generate(None, out, folio_id="f01r")
        root = ET.parse(str(out)).getroot()
        assert root.tag == f"{{{_NS}}}PcGts"


# ---------------------------------------------------------------------------
# TestPageHierarchy — Page > TextRegion > TextLine > Word > Glyph
# ---------------------------------------------------------------------------

class TestPageHierarchy:
    def test_text_region_present(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        page = root.find(f"{{{_NS}}}Page")
        regions = page.findall(f"{{{_NS}}}TextRegion")
        assert len(regions) >= 1

    def test_text_lines_match_layout_line_count(self, f01r_layout, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        lines = root.findall(f".//{{{_NS}}}TextLine")
        assert len(lines) == len(f01r_layout.lines)

    def test_each_text_line_has_coords(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        for tl in root.findall(f".//{{{_NS}}}TextLine"):
            coords = tl.find(f"{{{_NS}}}Coords")
            assert coords is not None, "TextLine missing Coords"
            assert coords.attrib.get("points"), "TextLine Coords missing points"

    def test_each_text_line_has_baseline(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        for tl in root.findall(f".//{{{_NS}}}TextLine"):
            baseline = tl.find(f"{{{_NS}}}Baseline")
            assert baseline is not None, "TextLine missing Baseline"
            assert baseline.attrib.get("points"), "Baseline missing points"

    def test_words_present(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        words = root.findall(f".//{{{_NS}}}Word")
        assert len(words) >= 1

    def test_glyphs_present(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        glyphs = root.findall(f".//{{{_NS}}}Glyph")
        assert len(glyphs) >= 1

    def test_glyph_has_coords(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        for glyph in root.findall(f".//{{{_NS}}}Glyph"):
            coords = glyph.find(f"{{{_NS}}}Coords")
            assert coords is not None, "Glyph missing Coords"
            assert coords.attrib.get("points"), "Glyph Coords missing points"

    def test_glyph_has_text_equiv(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        for glyph in root.findall(f".//{{{_NS}}}Glyph"):
            te = glyph.find(f"{{{_NS}}}TextEquiv")
            assert te is not None, "Glyph missing TextEquiv"
            uni = te.find(f"{{{_NS}}}Unicode")
            assert uni is not None and uni.text, "Glyph TextEquiv missing Unicode text"

    def test_text_equiv_has_register_attribute(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        for te in root.findall(f".//{{{_NS}}}TextEquiv"):
            custom = te.attrib.get("custom", "")
            assert "register:" in custom, (
                f"TextEquiv missing register: in custom attribute, got {custom!r}"
            )

    def test_coords_polygon_has_at_least_three_points(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        for coords in root.findall(f".//{{{_NS}}}Coords"):
            pts_str = coords.attrib.get("points", "")
            pts = pts_str.strip().split()
            assert len(pts) >= 3, (
                f"Coords polygon has only {len(pts)} points: {pts_str!r}"
            )

    def test_all_element_ids_unique(self, f01r_xml):
        root = ET.parse(str(f01r_xml)).getroot()
        ids = [el.attrib["id"] for el in root.iter() if "id" in el.attrib]
        assert len(ids) == len(set(ids)), "Duplicate element IDs in PAGE XML"
