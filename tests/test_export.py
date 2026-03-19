"""Tests for xl.export — TD-001-A (Folio JSON), TD-001-B (Manifest), TD-001-C (PAGE XML).

TDD discipline: tests written before implementation.
All tests must fail (red) until xl/export/ modules are written.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from xl.models import (
    Annotation,
    FolioPage,
    Line,
    ManuscriptMeta,
    FolioMapEntry,
    DamageType,
)
from xl.export.json_writer import build_folio_dict, write_folio_json
from xl.export.manifest_writer import build_manifest_dict, write_manifest
from xl.export.page_xml_writer import build_page_xml, write_page_xml
from xl.export.jsonl_writer import write_jsonl
from xl.export import export

PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _line(n: int, text: str, register: str = "de", english: str | None = None) -> Line:
    anns = [Annotation(type="confidence", detail={"score": 0.97})]
    return Line(number=n, text=text, register=register, english=english, annotations=anns)


def _clean_page(folio_id: str = "f01r", lines: int = 3) -> FolioPage:
    folio_num = int(folio_id[1:3])
    page_lines = [_line(i + 1, f"Wort {i} auf dieser Seite") for i in range(lines)]
    return FolioPage(
        id=folio_id,
        recto_verso="recto" if folio_id.endswith("r") else "verso",
        gathering_position=folio_num,
        lines=page_lines,
    )


def _damaged_page() -> FolioPage:
    page = _clean_page("f04r", lines=2)
    page.damage = {"type": DamageType.WATER, "extent": "partial", "direction": "from_above"}
    page.lines[0].annotations.append(Annotation(type="lacuna"))
    # Reduce confidence on the damaged lines
    page.lines[0].annotations[0].detail["score"] = 0.70
    return page


def _mixed_register_page() -> FolioPage:
    folio_num = 7
    return FolioPage(
        id="f07r",
        recto_verso="recto",
        gathering_position=folio_num,
        lines=[
            _line(1, "Deutsche Zeile", "de"),
            _line(2, "Linea Latina", "la"),
            _line(3, "In sînem grunde", "mhg"),
            _line(4, "Gemischte Zeile", "mixed"),
        ],
    )


def _meta() -> ManuscriptMeta:
    return ManuscriptMeta(
        shelfmark="MS Erfurt Aug. 12°47",
        author="Konrad (secular canon, Augustinian house, Erfurt)",
        date=1457,
        language_primary="Frühneuhochdeutsch (Thuringian)",
        language_secondary="Ecclesiastical Latin",
        language_tertiary="Middle High German (Eckhart quotations)",
        gathering=17,
        storage="Bound between a Breviarium and a Lectionary",
        discovery=2019,
    )


# ---------------------------------------------------------------------------
# TD-001-A: Folio JSON — build_folio_dict
# ---------------------------------------------------------------------------

class TestFolioDict:
    def test_required_fields_present(self):
        d = build_folio_dict(_clean_page())
        for field in ("id", "recto_verso", "gathering_position", "lines", "metadata"):
            assert field in d, f"Missing required field: {field}"

    def test_id_matches_page(self):
        d = build_folio_dict(_clean_page("f04v"))
        assert d["id"] == "f04v"

    def test_recto_verso(self):
        assert build_folio_dict(_clean_page("f01r"))["recto_verso"] == "recto"
        assert build_folio_dict(_clean_page("f01v"))["recto_verso"] == "verso"

    def test_gathering_position(self):
        d = build_folio_dict(_clean_page("f07r"))
        assert d["gathering_position"] == 7

    def test_lines_serialized(self):
        d = build_folio_dict(_clean_page("f01r", lines=3))
        assert len(d["lines"]) == 3
        first = d["lines"][0]
        assert "number" in first
        assert "text" in first
        assert "register" in first

    def test_line_number_and_register(self):
        d = build_folio_dict(_mixed_register_page())
        assert d["lines"][0]["register"] == "de"
        assert d["lines"][1]["register"] == "la"
        assert d["lines"][2]["register"] == "mhg"
        assert d["lines"][3]["register"] == "mixed"
        assert d["lines"][0]["number"] == 1

    def test_line_annotations_serialized(self):
        d = build_folio_dict(_clean_page())
        first_line = d["lines"][0]
        assert "annotations" in first_line
        assert isinstance(first_line["annotations"], list)
        # Should have the confidence annotation we added in _line()
        conf = [a for a in first_line["annotations"] if a["type"] == "confidence"]
        assert len(conf) == 1
        assert "detail" in conf[0]

    def test_clean_page_damage_is_null(self):
        d = build_folio_dict(_clean_page())
        assert d.get("damage") is None

    def test_damaged_page_damage_present(self):
        d = build_folio_dict(_damaged_page())
        assert d["damage"] is not None
        assert d["damage"]["type"] == DamageType.WATER
        assert d["damage"]["extent"] == "partial"

    def test_metadata_line_count(self):
        d = build_folio_dict(_clean_page("f01r", lines=5))
        assert d["metadata"]["line_count"] == 5

    def test_metadata_register_ratio_keys(self):
        d = build_folio_dict(_mixed_register_page())
        ratio = d["metadata"]["register_ratio"]
        assert "de" in ratio
        assert "la" in ratio
        assert "mhg" in ratio
        assert "mixed" in ratio

    def test_metadata_register_ratio_sums_to_one(self):
        d = build_folio_dict(_mixed_register_page())
        ratio = d["metadata"]["register_ratio"]
        total = sum(ratio.values())
        assert abs(total - 1.0) < 1e-9, f"Register ratio does not sum to 1.0: {total}"

    def test_metadata_text_density(self):
        d = build_folio_dict(_clean_page("f01r", lines=3))
        assert "text_density_chars_per_line" in d["metadata"]
        assert d["metadata"]["text_density_chars_per_line"] > 0

    def test_vellum_stock_default(self):
        d = build_folio_dict(_clean_page())
        assert d.get("vellum_stock", "standard") == "standard"

    def test_vellum_stock_irregular(self):
        page = _clean_page("f14r")
        page.vellum_stock = "irregular"
        d = build_folio_dict(page)
        assert d["vellum_stock"] == "irregular"

    def test_section_breaks_empty_by_default(self):
        d = build_folio_dict(_clean_page())
        assert d.get("section_breaks", []) == []

    def test_output_is_json_serializable(self):
        d = build_folio_dict(_damaged_page())
        # Should not raise
        json.dumps(d)


# ---------------------------------------------------------------------------
# TD-001-A: write_folio_json (filesystem)
# ---------------------------------------------------------------------------

class TestWriteFolioJson:
    def test_writes_file_with_correct_name(self, tmp_path):
        page = _clean_page("f03v")
        path = write_folio_json(page, tmp_path)
        assert path == tmp_path / "f03v.json"
        assert path.exists()

    def test_written_file_is_valid_json(self, tmp_path):
        page = _clean_page("f01r")
        path = write_folio_json(page, tmp_path)
        data = json.loads(path.read_text())
        assert data["id"] == "f01r"


# ---------------------------------------------------------------------------
# TD-001-B: Manifest JSON — build_manifest_dict
# ---------------------------------------------------------------------------

class TestManifestDict:
    def _pages(self):
        return [_clean_page("f01r", 3), _damaged_page(), _clean_page("f06r", 5)]

    def test_required_top_level_keys(self):
        d = build_manifest_dict(self._pages(), _meta())
        assert "manuscript" in d
        assert "folios" in d

    def test_manuscript_fields(self):
        d = build_manifest_dict(self._pages(), _meta())
        m = d["manuscript"]
        assert m["shelfmark"] == "MS Erfurt Aug. 12°47"
        assert m["date"] == 1457
        assert "folio_count" in m

    def test_folios_list_length(self):
        pages = self._pages()
        d = build_manifest_dict(pages, _meta())
        assert len(d["folios"]) == len(pages)

    def test_folio_entry_required_fields(self):
        d = build_manifest_dict(self._pages(), _meta())
        for entry in d["folios"]:
            assert "id" in entry
            assert "file" in entry

    def test_folio_entry_file_is_relative_json_path(self):
        d = build_manifest_dict(self._pages(), _meta())
        for entry in d["folios"]:
            assert entry["file"].endswith(".json")
            assert entry["id"] in entry["file"]

    def test_folio_entry_line_count(self):
        d = build_manifest_dict(self._pages(), _meta())
        assert d["folios"][0]["line_count"] == 3   # f01r has 3 lines

    def test_damaged_folio_has_damage_fields(self):
        d = build_manifest_dict(self._pages(), _meta())
        f04r_entry = next(e for e in d["folios"] if e["id"] == "f04r")
        assert f04r_entry["damage_type"] == DamageType.WATER
        assert f04r_entry["damage_extent"] == "partial"

    def test_clean_folio_damage_is_null(self):
        d = build_manifest_dict(self._pages(), _meta())
        f01r_entry = next(e for e in d["folios"] if e["id"] == "f01r")
        assert f01r_entry.get("damage_type") is None

    def test_register_dominant(self):
        d = build_manifest_dict([_mixed_register_page()], _meta())
        entry = d["folios"][0]
        assert "register_dominant" in entry
        assert entry["register_dominant"] in ("de", "la", "mhg", "mixed")

    def test_gaps_key_present(self):
        d = build_manifest_dict(self._pages(), _meta())
        assert "gaps" in d
        assert isinstance(d["gaps"], list)

    def test_manifest_is_json_serializable(self):
        d = build_manifest_dict(self._pages(), _meta())
        json.dumps(d)

    def test_manifest_without_meta_still_works(self):
        d = build_manifest_dict(self._pages(), None)
        assert "manuscript" in d
        assert "folios" in d


# ---------------------------------------------------------------------------
# TD-001-B: write_manifest (filesystem)
# ---------------------------------------------------------------------------

class TestWriteManifest:
    def test_writes_manifest_json(self, tmp_path):
        pages = [_clean_page("f01r")]
        path = write_manifest(pages, _meta(), tmp_path)
        assert path == tmp_path / "manifest.json"
        assert path.exists()

    def test_manifest_json_parseable(self, tmp_path):
        pages = [_clean_page("f01r")]
        path = write_manifest(pages, _meta(), tmp_path)
        data = json.loads(path.read_text())
        assert "folios" in data


# ---------------------------------------------------------------------------
# TD-001-C: PAGE XML — build_page_xml
# ---------------------------------------------------------------------------

class TestPageXml:
    def _parsed(self, page: FolioPage = None):
        xml_str = build_page_xml(page or _clean_page("f01r", 3))
        return ET.fromstring(xml_str)

    def test_root_is_pcgts(self):
        root = self._parsed()
        assert root.tag == f"{{{PAGE_NS}}}PcGts"

    def test_has_metadata_element(self):
        root = self._parsed()
        meta = root.find(f"{{{PAGE_NS}}}Metadata")
        assert meta is not None

    def test_has_page_element(self):
        root = self._parsed()
        page_el = root.find(f"{{{PAGE_NS}}}Page")
        assert page_el is not None

    def test_page_has_image_filename_attr(self):
        root = self._parsed()
        page_el = root.find(f"{{{PAGE_NS}}}Page")
        assert "imageFilename" in page_el.attrib

    def test_has_text_region(self):
        root = self._parsed()
        page_el = root.find(f"{{{PAGE_NS}}}Page")
        region = page_el.find(f"{{{PAGE_NS}}}TextRegion")
        assert region is not None

    def test_text_line_count_matches_lines(self):
        page = _clean_page("f01r", lines=4)
        root = ET.fromstring(build_page_xml(page))
        page_el = root.find(f"{{{PAGE_NS}}}Page")
        region = page_el.find(f"{{{PAGE_NS}}}TextRegion")
        lines = region.findall(f"{{{PAGE_NS}}}TextLine")
        assert len(lines) == 4

    def test_text_line_has_register_custom(self):
        root = self._parsed(_mixed_register_page())
        page_el = root.find(f"{{{PAGE_NS}}}Page")
        region = page_el.find(f"{{{PAGE_NS}}}TextRegion")
        lines = region.findall(f"{{{PAGE_NS}}}TextLine")
        assert lines[0].get("custom") == "register:de"
        assert lines[1].get("custom") == "register:la"
        assert lines[2].get("custom") == "register:mhg"

    def test_text_line_has_coords(self):
        root = self._parsed()
        page_el = root.find(f"{{{PAGE_NS}}}Page")
        region = page_el.find(f"{{{PAGE_NS}}}TextRegion")
        first_line = region.find(f"{{{PAGE_NS}}}TextLine")
        coords = first_line.find(f"{{{PAGE_NS}}}Coords")
        assert coords is not None
        assert "points" in coords.attrib

    def test_text_line_has_text_equiv_german(self):
        page = _clean_page("f01r", 1)
        root = ET.fromstring(build_page_xml(page))
        page_el = root.find(f"{{{PAGE_NS}}}Page")
        region = page_el.find(f"{{{PAGE_NS}}}TextRegion")
        first_line = region.find(f"{{{PAGE_NS}}}TextLine")
        equivs = first_line.findall(f"{{{PAGE_NS}}}TextEquiv")
        # At least one TextEquiv with the German text
        texts = [e.find(f"{{{PAGE_NS}}}Unicode").text for e in equivs]
        assert page.lines[0].text in texts

    def test_xml_is_parseable_string(self):
        xml_str = build_page_xml(_clean_page())
        assert isinstance(xml_str, str)
        assert xml_str.startswith("<?xml") or "<PcGts" in xml_str
        ET.fromstring(xml_str)  # must not raise

    def test_write_page_xml_creates_file(self, tmp_path):
        page = _clean_page("f07r", 2)
        path = write_page_xml(page, tmp_path)
        assert path == tmp_path / "f07r.xml"
        assert path.exists()


# ---------------------------------------------------------------------------
# JSONL writer
# ---------------------------------------------------------------------------

class TestJsonlWriter:
    def test_writes_jsonl_file(self, tmp_path):
        pages = [_clean_page("f01r", 3), _clean_page("f01v", 2)]
        path = write_jsonl(pages, tmp_path)
        assert path.exists()
        assert path.name == "folios.jsonl"

    def test_one_record_per_line_per_folio(self, tmp_path):
        pages = [_clean_page("f01r", 3), _clean_page("f01v", 2)]
        path = write_jsonl(pages, tmp_path)
        records = [json.loads(line) for line in path.read_text().splitlines() if line]
        # 3 + 2 = 5 line records
        assert len(records) == 5

    def test_jsonl_record_has_folio_id_and_line_fields(self, tmp_path):
        pages = [_clean_page("f01r", 1)]
        path = write_jsonl(pages, tmp_path)
        record = json.loads(path.read_text().splitlines()[0])
        assert "folio_id" in record
        assert "line_number" in record
        assert "text" in record
        assert "register" in record


# ---------------------------------------------------------------------------
# export() orchestrator
# ---------------------------------------------------------------------------

class TestExportOrchestrator:
    def test_export_writes_folio_json_files(self, tmp_path):
        pages = [_clean_page("f01r"), _clean_page("f02r")]
        export(pages, _meta(), tmp_path)
        assert (tmp_path / "f01r.json").exists()
        assert (tmp_path / "f02r.json").exists()

    def test_export_writes_manifest(self, tmp_path):
        pages = [_clean_page("f01r")]
        export(pages, _meta(), tmp_path)
        assert (tmp_path / "manifest.json").exists()

    def test_export_writes_page_xml_files(self, tmp_path):
        pages = [_clean_page("f01r")]
        export(pages, _meta(), tmp_path)
        assert (tmp_path / "f01r.xml").exists()

    def test_export_jsonl_optional(self, tmp_path):
        pages = [_clean_page("f01r", 2)]
        export(pages, _meta(), tmp_path, formats=["json", "manifest", "xml", "jsonl"])
        assert (tmp_path / "folios.jsonl").exists()

    def test_export_formats_subset(self, tmp_path):
        pages = [_clean_page("f01r")]
        export(pages, _meta(), tmp_path, formats=["json"])
        assert (tmp_path / "f01r.json").exists()
        assert not (tmp_path / "manifest.json").exists()
        assert not (tmp_path / "f01r.xml").exists()
