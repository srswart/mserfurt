"""Golden tests, round-trip validation, and register consistency checks.

Red phase: TestRoundTrip and TestRegisterConsistency import from modules that
do not exist yet (xl.export.round_trip, xl.export.register_check).  All tests
in this file will be collected as errors until those modules are implemented.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from xl.export.json_writer import build_folio_dict, write_folio_json
from xl.export.manifest_writer import build_manifest_dict
from xl.export.page_xml_writer import build_page_xml
from xl.export.round_trip import parse_folio_dict          # red: does not exist yet
from xl.export.register_check import check_pages, Violation  # red: does not exist yet
from xl.models import Annotation, FolioPage, Line, ManuscriptMeta

GOLDEN_DIR = Path(__file__).parent / "golden"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_golden(folio_id: str) -> dict:
    return json.loads((GOLDEN_DIR / folio_id / "folio.json").read_text())


def page_from_fixture(folio_id: str) -> FolioPage:
    """Parse a golden fixture into a FolioPage via the round-trip parser."""
    return parse_folio_dict(load_golden(folio_id))


def _simple_page(
    folio_id: str = "f01r",
    lines: list[Line] | None = None,
    gathering_position: int = 1,
    recto_verso: str = "recto",
    **kwargs,
) -> FolioPage:
    if lines is None:
        lines = [
            Line(number=1, text="Got ist ein wort", register="de"),
            Line(number=2, text="daz ungesprochen bleibt", register="de"),
        ]
    return FolioPage(
        id=folio_id,
        recto_verso=recto_verso,
        gathering_position=gathering_position,
        lines=lines,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# TestGoldenFolios — structural equality after round-trip through folio dict
# ---------------------------------------------------------------------------

GOLDEN_FOLIOS = ["f01r", "f04v", "f07r", "f10r", "f14r"]


@pytest.mark.parametrize("folio_id", GOLDEN_FOLIOS)
class TestGoldenFolios:
    """Each golden fixture: parse → re-serialize → compare to fixture JSON."""

    def test_fixture_parses_without_error(self, folio_id):
        page = page_from_fixture(folio_id)
        assert page.id == folio_id

    def test_line_count_matches_fixture(self, folio_id):
        fixture = load_golden(folio_id)
        page = page_from_fixture(folio_id)
        assert len(page.lines) == fixture["metadata"]["line_count"]

    def test_register_sequence_matches_fixture(self, folio_id):
        fixture = load_golden(folio_id)
        page = page_from_fixture(folio_id)
        expected = [ln["register"] for ln in fixture["lines"]]
        actual = [ln.register for ln in page.lines]
        assert actual == expected

    def test_annotation_types_match_fixture(self, folio_id):
        fixture = load_golden(folio_id)
        page = page_from_fixture(folio_id)
        for fix_line, page_line in zip(fixture["lines"], page.lines):
            expected_types = [a["type"] for a in fix_line["annotations"]]
            actual_types = [a.type for a in page_line.annotations]
            assert actual_types == expected_types, (
                f"{folio_id} line {page_line.number}: annotation types mismatch"
            )

    def test_reserialize_matches_fixture_structure(self, folio_id):
        """Round-trip: fixture JSON → FolioPage → build_folio_dict → same structure."""
        fixture = load_golden(folio_id)
        page = page_from_fixture(folio_id)
        rebuilt = build_folio_dict(page)

        assert rebuilt["id"] == fixture["id"]
        assert rebuilt["recto_verso"] == fixture["recto_verso"]
        assert rebuilt["gathering_position"] == fixture["gathering_position"]
        assert rebuilt["metadata"]["line_count"] == fixture["metadata"]["line_count"]
        assert rebuilt["vellum_stock"] == fixture["vellum_stock"]


class TestGoldenFoliosDamage:
    """f04v-specific damage assertions."""

    def test_damage_present_on_f04v(self):
        page = page_from_fixture("f04v")
        assert page.damage is not None

    def test_f04v_has_lacuna_annotations(self):
        page = page_from_fixture("f04v")
        all_types = [a.type for ln in page.lines for a in ln.annotations]
        assert "lacuna" in all_types

    def test_f04v_damaged_lines_have_low_confidence(self):
        page = page_from_fixture("f04v")
        # Lines 2–5 (index 1–4) should have at least one confidence annotation < 0.5
        for line in page.lines[1:]:
            conf_anns = [
                a for a in line.annotations
                if a.type == "confidence"
            ]
            assert conf_anns, f"line {line.number} has no confidence annotation"
            scores = [a.detail["score"] for a in conf_anns]
            assert any(s < 0.5 for s in scores), (
                f"f04v line {line.number}: expected confidence < 0.5, got {scores}"
            )


class TestGoldenFoliosVerbatim:
    """f07r and f10r verbatim source assertions."""

    def test_f07r_has_verbatim_eckhart(self):
        page = page_from_fixture("f07r")
        sources = [
            a.detail.get("source")
            for ln in page.lines
            for a in ln.annotations
            if a.type == "verbatim_source"
        ]
        assert any(s == "verbatim:eckhart" for s in sources)

    def test_f10r_has_verbatim_psalms(self):
        page = page_from_fixture("f10r")
        sources = [
            a.detail.get("source")
            for ln in page.lines
            for a in ln.annotations
            if a.type == "verbatim_source"
        ]
        assert any(s == "verbatim:psalms" for s in sources)

    def test_f07r_latin_lines_are_verbatim(self):
        page = page_from_fixture("f07r")
        for ln in page.lines:
            if ln.register == "la":
                ann_types = [a.type for a in ln.annotations]
                assert "verbatim_source" in ann_types, (
                    f"f07r line {ln.number}: Latin line missing verbatim_source annotation"
                )


# ---------------------------------------------------------------------------
# TestRoundTrip — FolioPage ↔ dict invertibility
# ---------------------------------------------------------------------------

class TestRoundTrip:
    """export build_folio_dict → parse_folio_dict produces equal FolioPage."""

    def test_basic_round_trip_equality(self):
        original = _simple_page()
        d = build_folio_dict(original)
        recovered = parse_folio_dict(d)
        assert recovered == original

    def test_round_trip_preserves_line_count(self):
        original = _simple_page(lines=[Line(n, f"text {n}", "de") for n in range(1, 7)])
        recovered = parse_folio_dict(build_folio_dict(original))
        assert len(recovered.lines) == 6

    def test_round_trip_preserves_register(self):
        lines = [
            Line(1, "Got ist ein licht", "de"),
            Line(2, "Deus est lux", "la"),
            Line(3, "Got ist ein wort", "de"),
        ]
        original = _simple_page(lines=lines)
        recovered = parse_folio_dict(build_folio_dict(original))
        assert [ln.register for ln in recovered.lines] == ["de", "la", "de"]

    def test_round_trip_preserves_annotation_spans(self):
        ann = Annotation(type="confidence", span=(0, 17), detail={"score": 0.91})
        lines = [Line(1, "Got ist ein licht", "de", annotations=[ann])]
        original = _simple_page(lines=lines)
        recovered = parse_folio_dict(build_folio_dict(original))
        assert recovered.lines[0].annotations[0].span == (0, 17)

    def test_round_trip_preserves_damage(self):
        damage = {"type": "water_damage", "extent": "lower_third"}
        original = _simple_page(damage=damage)
        recovered = parse_folio_dict(build_folio_dict(original))
        assert recovered.damage == damage

    def test_round_trip_preserves_section_breaks(self):
        original = _simple_page(section_breaks=[2, 5])
        recovered = parse_folio_dict(build_folio_dict(original))
        assert recovered.section_breaks == [2, 5]

    def test_round_trip_preserves_vellum_stock(self):
        original = _simple_page(vellum_stock="irregular")
        recovered = parse_folio_dict(build_folio_dict(original))
        assert recovered.vellum_stock == "irregular"

    def test_round_trip_preserves_english_field(self):
        lines = [Line(1, "Got ist ein wort", "de", english="God is a word")]
        original = _simple_page(lines=lines)
        recovered = parse_folio_dict(build_folio_dict(original))
        assert recovered.lines[0].english == "God is a word"

    def test_round_trip_preserves_hand_notes(self):
        hand = {"pressure": "light", "ink_density": "faded"}
        original = _simple_page(hand_notes=hand)
        recovered = parse_folio_dict(build_folio_dict(original))
        assert recovered.hand_notes == hand

    def test_round_trip_golden_f01r(self):
        """Golden round-trip: fixture → FolioPage → dict → FolioPage → same."""
        first_pass = page_from_fixture("f01r")
        second_pass = parse_folio_dict(build_folio_dict(first_pass))
        assert first_pass == second_pass

    def test_round_trip_golden_f04v(self):
        first_pass = page_from_fixture("f04v")
        second_pass = parse_folio_dict(build_folio_dict(first_pass))
        assert first_pass == second_pass


# ---------------------------------------------------------------------------
# TestRegisterConsistency — cross-folio coherence checks
# ---------------------------------------------------------------------------

class TestRegisterConsistency:
    """check_pages returns Violation records for known bad inputs."""

    def test_no_violations_on_clean_page(self):
        page = _simple_page()
        violations = check_pages([page])
        assert violations == []

    def test_unresolved_mixed_tag_is_violation(self):
        lines = [Line(1, "mixed text here", "mixed")]
        page = _simple_page(lines=lines)
        violations = check_pages([page])
        assert any(v.violation_type == "unresolved_mixed" for v in violations)

    def test_unresolved_mixed_violation_names_folio(self):
        lines = [Line(1, "mixed text here", "mixed")]
        page = _simple_page(folio_id="f03r", lines=lines)
        violations = check_pages([page])
        mixed_violations = [v for v in violations if v.violation_type == "unresolved_mixed"]
        assert all(v.folio_id == "f03r" for v in mixed_violations)

    def test_unknown_verbatim_ref_is_violation(self):
        ann = Annotation(
            type="verbatim_source",
            span=(0, 10),
            detail={"source": "verbatim:unknown_corpus", "ref": "X.1.1"},
        )
        lines = [Line(1, "Aliquid ignotum", "la", annotations=[ann])]
        page = _simple_page(lines=lines)
        known_refs = json.loads((FIXTURES_DIR / "verbatim_refs.json").read_text())
        violations = check_pages([page], verbatim_refs=known_refs)
        assert any(v.violation_type == "unknown_verbatim_source" for v in violations)

    def test_known_verbatim_ref_passes(self):
        ann = Annotation(
            type="verbatim_source",
            span=(0, 29),
            detail={"source": "verbatim:eckhart", "ref": "Reden.1.3"},
        )
        lines = [Line(1, "Mittit vobis spiritum veritatis", "la", annotations=[ann])]
        page = _simple_page(lines=lines)
        known_refs = json.loads((FIXTURES_DIR / "verbatim_refs.json").read_text())
        violations = check_pages([page], verbatim_refs=known_refs)
        assert not any(v.violation_type == "unknown_verbatim_source" for v in violations)

    def test_multiple_pages_all_clean(self):
        pages = [page_from_fixture(fid) for fid in GOLDEN_FOLIOS]
        known_refs = json.loads((FIXTURES_DIR / "verbatim_refs.json").read_text())
        violations = check_pages(pages, verbatim_refs=known_refs)
        assert violations == [], f"Unexpected violations: {violations}"

    def test_violation_has_required_fields(self):
        lines = [Line(1, "mixed text here", "mixed")]
        page = _simple_page(lines=lines)
        violations = check_pages([page])
        assert violations
        v = violations[0]
        assert isinstance(v, Violation)
        assert v.folio_id
        assert v.violation_type
        assert v.line_number is not None
        assert v.message

    def test_violation_reports_correct_line_number(self):
        lines = [
            Line(1, "Got ist ein wort", "de"),
            Line(2, "mixed text here", "mixed"),
            Line(3, "Got ist ein licht", "de"),
        ]
        page = _simple_page(lines=lines)
        violations = check_pages([page])
        mixed = [v for v in violations if v.violation_type == "unresolved_mixed"]
        assert mixed[0].line_number == 2


# ---------------------------------------------------------------------------
# TestManifestCompleteness — TD-001-B contract
# ---------------------------------------------------------------------------

def _make_17_pages() -> list[FolioPage]:
    """Build 17 minimal FolioPages (f01r–f17v alternating recto/verso)."""
    pages = []
    for i in range(1, 18):
        rv = "recto" if i % 2 == 1 else "verso"
        fid = f"f{i:02d}r" if rv == "recto" else f"f{i:02d}v"
        pages.append(FolioPage(
            id=fid,
            recto_verso=rv,
            gathering_position=i,
            lines=[Line(1, f"Line one folio {fid}", "de")],
        ))
    return pages


_META = ManuscriptMeta(
    shelfmark="Ms. germ. oct. 63",
    author="Konrad von Megenberg",
    date=1390,
    language_primary="de",
    language_secondary="la",
    language_tertiary="mhg",
    gathering=1,
    storage="Staatsbibliothek Berlin",
    discovery=1887,
)


class TestManifestCompleteness:
    """TD-001-B: manifest covers all 17 folios, gap entry present."""

    def test_manifest_has_all_17_folios(self):
        pages = _make_17_pages()
        m = build_manifest_dict(pages, _META)
        assert len(m["folios"]) == 17

    def test_every_folio_entry_has_file_key(self):
        pages = _make_17_pages()
        m = build_manifest_dict(pages, _META)
        for entry in m["folios"]:
            assert "file" in entry, f"folio {entry.get('id')} missing 'file'"

    def test_folio_file_value_is_json(self):
        pages = _make_17_pages()
        m = build_manifest_dict(pages, _META)
        for entry in m["folios"]:
            assert entry["file"].endswith(".json"), (
                f"folio {entry['id']} file does not end in .json: {entry['file']!r}"
            )

    def test_gaps_key_present_and_non_empty(self):
        pages = _make_17_pages()
        m = build_manifest_dict(pages, _META)
        assert "gaps" in m
        assert isinstance(m["gaps"], list)
        assert len(m["gaps"]) >= 1, "expected at least one gap entry (f05v/f06r)"

    def test_gap_references_f05v(self):
        pages = _make_17_pages()
        m = build_manifest_dict(pages, _META)
        after_refs = [g.get("after_folio") for g in m["gaps"]]
        assert "f05v" in after_refs

    def test_manuscript_shelfmark_present(self):
        pages = _make_17_pages()
        m = build_manifest_dict(pages, _META)
        assert m["manuscript"]["shelfmark"] == "Ms. germ. oct. 63"

    def test_manifest_folio_count_matches_pages(self):
        pages = _make_17_pages()
        m = build_manifest_dict(pages, _META)
        assert m["manuscript"]["folio_count"] == 17

    def test_manifest_without_meta_has_unknown_shelfmark(self):
        pages = _make_17_pages()
        m = build_manifest_dict(pages, None)
        assert m["manuscript"]["shelfmark"] == "unknown"


# ---------------------------------------------------------------------------
# TestPageXmlValidity — TD-001-C contract
# ---------------------------------------------------------------------------

class TestPageXmlValidity:
    """TD-001-C: PAGE XML structural requirements."""

    def _parsed(self, page: FolioPage) -> ET.Element:
        return ET.fromstring(build_page_xml(page))

    def test_root_namespace_is_page_2019(self):
        page = _simple_page()
        root = self._parsed(page)
        assert root.tag == f"{{{PAGE_NS}}}PcGts"

    def test_every_text_line_has_coords(self):
        lines = [Line(i, f"text {i}", "de") for i in range(1, 5)]
        page = _simple_page(lines=lines)
        root = self._parsed(page)
        for tl in root.iter(f"{{{PAGE_NS}}}TextLine"):
            coords = tl.find(f"{{{PAGE_NS}}}Coords")
            assert coords is not None, f"TextLine {tl.attrib.get('id')} missing Coords"

    def test_every_text_line_has_baseline(self):
        lines = [Line(i, f"text {i}", "de") for i in range(1, 4)]
        page = _simple_page(lines=lines)
        root = self._parsed(page)
        for tl in root.iter(f"{{{PAGE_NS}}}TextLine"):
            baseline = tl.find(f"{{{PAGE_NS}}}Baseline")
            assert baseline is not None, f"TextLine {tl.attrib.get('id')} missing Baseline"

    def test_every_text_line_has_text_equiv_index_0(self):
        lines = [Line(i, f"text {i}", "de") for i in range(1, 4)]
        page = _simple_page(lines=lines)
        root = self._parsed(page)
        for tl in root.iter(f"{{{PAGE_NS}}}TextLine"):
            te_indices = [
                te.attrib.get("index")
                for te in tl.findall(f"{{{PAGE_NS}}}TextEquiv")
            ]
            assert "0" in te_indices, (
                f"TextLine {tl.attrib.get('id')} missing TextEquiv index=0"
            )

    def test_text_equiv_0_unicode_matches_line_text(self):
        lines = [Line(1, "Got ist ein wort", "de")]
        page = _simple_page(lines=lines)
        root = self._parsed(page)
        tl = next(root.iter(f"{{{PAGE_NS}}}TextLine"))
        te0 = next(
            te for te in tl.findall(f"{{{PAGE_NS}}}TextEquiv")
            if te.attrib.get("index") == "0"
        )
        uni = te0.find(f"{{{PAGE_NS}}}Unicode")
        assert uni is not None and uni.text == "Got ist ein wort"

    def test_english_line_gets_text_equiv_index_1(self):
        lines = [Line(1, "Got ist ein wort", "de", english="God is a word")]
        page = _simple_page(lines=lines)
        root = self._parsed(page)
        tl = next(root.iter(f"{{{PAGE_NS}}}TextLine"))
        te_indices = [
            te.attrib.get("index")
            for te in tl.findall(f"{{{PAGE_NS}}}TextEquiv")
        ]
        assert "1" in te_indices

    def test_coords_points_attr_parseable_as_int_pairs(self):
        lines = [Line(1, "Got ist ein wort", "de")]
        page = _simple_page(lines=lines)
        root = self._parsed(page)
        for coords in root.iter(f"{{{PAGE_NS}}}Coords"):
            pts = coords.attrib.get("points", "")
            pairs = [tuple(int(v) for v in pt.split(",")) for pt in pts.split()]
            assert len(pairs) >= 2

    def test_text_line_custom_attr_contains_register(self):
        lines = [Line(1, "Deus est lux", "la")]
        page = _simple_page(lines=lines)
        root = self._parsed(page)
        tl = next(root.iter(f"{{{PAGE_NS}}}TextLine"))
        custom = tl.attrib.get("custom", "")
        assert "register:la" in custom
