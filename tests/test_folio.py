"""Tests for xl.folio.structurer — folio distribution and page-pin constraints.

TDD discipline: these tests are written BEFORE the implementation.
All tests must fail (red) until xl/folio/structurer.py is written.
"""

from __future__ import annotations

import pytest
from xl.models import (
    Passage, Section, TranslatedPassage, TranslatedSection,
    RegisterMap, PassageRegister,
    ClauseRegister, RegisterTag,
)
from xl.folio.structurer import (
    _DEFAULT_LINE_BUDGET,
    _FINAL_LINE_BUDGET,
    _LINE_BUDGETS,
    structure,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _passage(text: str, register: str = "de") -> Passage:
    return Passage(text=text, register=register)


def _translated(text: str, translated: str, register: str = "de") -> TranslatedPassage:
    return TranslatedPassage(
        original=_passage(text, register),
        translated_text=translated,
        method="dry_run",
    )


def _section(number: int, title: str, folio_ref: str, passages: list[TranslatedPassage]) -> TranslatedSection:
    sec = Section(number=number, title=title, folio_ref=folio_ref)
    original_sec = Section(number=number, title=title, folio_ref=folio_ref,
                           passages=[tp.original for tp in passages])
    return TranslatedSection(section=original_sec, passages=passages)


def _long_text(prefix: str, word_count: int) -> str:
    """Generate a repeated text block of roughly word_count words."""
    word = f"{prefix}Wort"
    return " ".join([word] * word_count)


def _register_map(*entries: tuple[int, int, str]) -> RegisterMap:
    """Build a RegisterMap from (section_number, passage_index, tag) triples."""
    rm = RegisterMap()
    for sn, pi, tag in entries:
        rm.entries[(sn, pi)] = PassageRegister(
            tag=tag,
            clauses=[ClauseRegister(text="", language=tag)],
        )
    return rm


# ---------------------------------------------------------------------------
# Fixture: minimal 7-section translated manuscript
# ---------------------------------------------------------------------------

def _make_full_manuscript() -> tuple[list[TranslatedSection], RegisterMap]:
    """
    Create a 7-section manuscript with enough text to fill pages.
    Each passage is ~120 chars (2 lines at 60 chars/line) with count-based suffix
    so tests can identify which section/passage produced each line.
    """
    # ~100 chars base text + numeric suffix keeps lines identifiable
    base = (
        "Ich schrieb dies nieder in der Stille des Klosters "
        "und bedachte alles was verloren und was gewonnen war "
        "und welche Worte bleiben mochten fur die Nachkommenden"
    )

    def long_section(num, title, folio_ref, passage_count=12, register="de"):
        passages = [
            _translated(base, base + f" ({num}-{i})", register=register)
            for i in range(passage_count)
        ]
        return _section(num, title, folio_ref, passages)

    sections = [
        # Section 1: very short — opening declaration
        _section(1, "Opening Declaration", "f01r", [
            _translated("Here begins.", "Incipit quod scriba scribere non potuit abstinere.", register="mixed"),
        ]),
        # Section 2: press meditation — 6 pages (~192 lines at 32/page); 70 passages × 3 lines each
        long_section(2, "Press Meditation", "f01r-f03v", passage_count=70),
        # Section 3: Peter narrative — 4 damaged pages (~90 lines total); 35 passages
        long_section(3, "Peter Narrative", "f04r-f05v", passage_count=35),
        # Section 4: Workshop + Demetrios — 14 pages (split across f06-f06v and f08-f13v)
        long_section(4, "Workshop Visits", "f06r onward", passage_count=48),
        # Section 5: Eckhart confession — pinned to f07r-f07v
        _section(5, "Eckhart Confession", "f07r-f07v", [
            _translated("Eckhart wrote", "In seinem Grunde: die Seele ist das Wort.", register="mhg"),
            _translated("The soul becomes", "Wirt. Wird. Die Seele wird das Wort.", register="mhg"),
        ]),
        # Section 6: Psalter return — shares f07v lower
        _section(6, "Psalter Return", "f07v lower half", [
            _translated("The Psalter is due.", "Der Psalter ist fällig in sechs Wochen.", register="de"),
        ]),
        # Section 7: final gathering — pinned to f14r
        long_section(7, "Final Gathering", "f14r-f17v", passage_count=20),
    ]

    rm = RegisterMap()
    for ts in sections:
        for i, tp in enumerate(ts.passages):
            sn = ts.section.number
            rm.entries[(sn, i)] = PassageRegister(
                tag=tp.original.register,
                clauses=[ClauseRegister(text=tp.translated_text, language=tp.original.register)],
            )

    return sections, rm


# ---------------------------------------------------------------------------
# Test: page gathering order
# ---------------------------------------------------------------------------

class TestPageGatheringOrder:
    def test_pages_are_in_folio_id_order(self):
        """Returned pages must be in gathering order: f01r, f01v, f02r, ..."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        ids = [p.id for p in pages]
        def _rank(fid: str) -> tuple[int, int]:
            return (int(fid[1:-1]), 0 if fid.endswith("r") else 1)

        for i in range(len(ids) - 1):
            assert _rank(ids[i]) < _rank(ids[i + 1]), (
                f"Page {ids[i]} appears before {ids[i+1]} but should be later in gathering order"
            )

    def test_recto_verso_assignment(self):
        """Folio IDs ending in 'r' must be recto; 'v' must be verso."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        for p in pages:
            expected = "recto" if p.id.endswith("r") else "verso"
            assert p.recto_verso == expected, f"{p.id}: expected {expected}, got {p.recto_verso}"

    def test_gathering_position_matches_folio_number(self):
        """gathering_position must equal the numeric part of the folio ID."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        for p in pages:
            expected_num = int(p.id[1:3])
            assert p.gathering_position == expected_num, (
                f"{p.id}: gathering_position={p.gathering_position}, expected {expected_num}"
            )


# ---------------------------------------------------------------------------
# Test: line budget enforcement
# ---------------------------------------------------------------------------

class TestLineBudgets:
    def test_f04r_within_damage_budget(self):
        """f04r (water damage) must not exceed its reduced line budget."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)
        page = next((p for p in pages if p.id == "f04r"), None)
        if page is None:
            pytest.skip("f04r not produced (section 3 may have insufficient text)")
        assert page.line_count <= _LINE_BUDGETS["f04r"], (
            f"f04r has {page.line_count} lines, budget is {_LINE_BUDGETS['f04r']}"
        )

    def test_f04v_within_damage_budget(self):
        """f04v (water + missing corner) must not exceed its reduced line budget."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)
        page = next((p for p in pages if p.id == "f04v"), None)
        if page is None:
            pytest.skip("f04v not produced")
        assert page.line_count <= _LINE_BUDGETS["f04v"], (
            f"f04v has {page.line_count} lines, budget is {_LINE_BUDGETS['f04v']}"
        )

    def test_f05r_within_damage_budget(self):
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)
        page = next((p for p in pages if p.id == "f05r"), None)
        if page is None:
            pytest.skip("f05r not produced")
        assert page.line_count <= _LINE_BUDGETS["f05r"]

    def test_f05v_within_damage_budget(self):
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)
        page = next((p for p in pages if p.id == "f05v"), None)
        if page is None:
            pytest.skip("f05v not produced")
        assert page.line_count <= _LINE_BUDGETS["f05v"]

    def test_no_page_exceeds_default_budget(self):
        """No clean page must exceed the default line budget."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        for p in pages:
            folio_num = int(p.id[1:-1])
            budget = _LINE_BUDGETS.get(
                p.id,
                _FINAL_LINE_BUDGET if folio_num >= 14 else _DEFAULT_LINE_BUDGET,
            )
            assert p.line_count <= budget, (
                f"{p.id} has {p.line_count} lines, budget is {budget}"
            )

    def test_clean_page_fills_to_minimum(self):
        """A clean standard page with enough text should reach at least 20 lines."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        # Pick f02r — far from any damage, in section 2's range, plenty of text
        page = next((p for p in pages if p.id == "f02r"), None)
        if page is None:
            pytest.skip("f02r not produced")
        assert page.line_count >= 20, (
            f"f02r only has {page.line_count} lines — expected >= 20 for a clean page with enough text"
        )


# ---------------------------------------------------------------------------
# Test: hard-pin constraints
# ---------------------------------------------------------------------------

class TestHardPins:
    def test_section5_does_not_start_before_f07r(self):
        """Eckhart section (5) must not begin before f07r."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        # Find the first page that contains section-5 text
        eckhart_text_prefix = "In seinem Grunde"
        first_eckhart_page = None
        for p in pages:
            if any(eckhart_text_prefix in line.text for line in p.lines):
                first_eckhart_page = p.id
                break

        assert first_eckhart_page is not None
        assert (int(first_eckhart_page[1:-1]), first_eckhart_page.endswith("v")) >= (7, False), (
            f"Eckhart passage first appears on {first_eckhart_page}, expected f07r or later"
        )

    def test_section5_does_not_appear_before_f07r(self):
        """No text from section 5 should appear on pages before f07r."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        pre_f07r = [f"f{n:02}{s}" for n in range(1, 7) for s in ("r", "v")]
        eckhart_phrases = {"In seinem Grunde", "Wirt. Wird."}

        for p in pages:
            if p.id not in pre_f07r:
                continue
            for line in p.lines:
                for phrase in eckhart_phrases:
                    assert phrase not in line.text, (
                        f"Section 5 phrase '{phrase}' found on {p.id} (before f07r pin)"
                    )

    def test_section7_does_not_start_before_f14r(self):
        """Final gathering content must not begin before the smaller-stock folios."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        # Section 7 uses _long_text with prefix "7" — check the first page where
        # section-7 content appears (all its passages share a distinctive suffix pattern)
        s7_marker = "7-0)"   # suffix from _make_full_manuscript helper
        first_s7_page = None
        for p in pages:
            if any(s7_marker in line.text for line in p.lines):
                first_s7_page = p.id
                break

        assert first_s7_page is not None
        assert (int(first_s7_page[1:-1]), first_s7_page.endswith("v")) >= (14, False), (
            f"Section 7 first appears on {first_s7_page}, expected f14r or later"
        )

    def test_section7_does_not_appear_before_f14r(self):
        """No section-7 text should appear on pages earlier than f14r."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        pre_f14r_ids = {f"f{n:02}{s}" for n in range(1, 14) for s in ("r", "v")}
        s7_markers = {"7-0)", "7-1)", "7-2)", "7-3)"}

        for p in pages:
            if p.id not in pre_f14r_ids:
                continue
            for line in p.lines:
                for marker in s7_markers:
                    assert marker not in line.text, (
                        f"Section 7 content found on {p.id} before f14r pin"
                    )

    def test_manuscript_may_extend_beyond_f17v(self):
        """The smaller private-manuscript layout may require more than 17 folios."""
        sections, rm = _make_full_manuscript()
        huge_final = _section(
            7,
            "Huge Final Gathering",
            "f14r onward",
            [_translated("late", _long_text("final", 90) + f" ({i})") for i in range(40)],
        )
        sections[-1] = huge_final
        pages = structure(sections, rm)
        assert any(int(p.id[1:-1]) > 17 for p in pages), (
            "Expected the denser private-manuscript layout to extend beyond f17"
        )


# ---------------------------------------------------------------------------
# Test: register metadata passthrough
# ---------------------------------------------------------------------------

class TestRegisterPassthrough:
    def test_mhg_passage_lines_have_mhg_register(self):
        """Lines from MHG passages must carry the 'mhg' register tag."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        mhg_pages = [p for p in pages if any(l.register == "mhg" for l in p.lines)]
        assert mhg_pages, "Expected at least one page carrying MHG-register lines"
        first_page = mhg_pages[0].id
        assert (int(first_page[1:-1]), first_page.endswith("v")) >= (7, False), (
            f"MHG lines first appeared on {first_page}, expected f07r or later"
        )

    def test_de_passage_lines_have_de_register(self):
        """Lines from German passages must carry the 'de' register tag."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        f01v = next((p for p in pages if p.id == "f01v"), None)
        if f01v is None:
            pytest.skip("f01v not produced")

        de_lines = [l for l in f01v.lines if l.register == "de"]
        assert len(de_lines) > 0, "Expected German-register lines on f01v (section 2)"

    def test_register_from_register_map_overrides_passage(self):
        """If RegisterMap has an entry, its tag is used for line.register."""
        sec = _section(1, "Test", "f01r", [
            _translated("some text", "etwas Text", register="de"),
        ])
        # Override section 1, passage 0 to "la" via RegisterMap
        rm = _register_map((1, 0, "la"))
        pages = structure([sec], rm)

        assert len(pages) > 0
        f01r = next((p for p in pages if p.id == "f01r"), None)
        assert f01r is not None
        assert all(l.register == "la" for l in f01r.lines), (
            "RegisterMap override to 'la' not reflected on lines"
        )


# ---------------------------------------------------------------------------
# Test: page metadata (damage, vellum, hand notes)
# ---------------------------------------------------------------------------

class TestPageMetadata:
    def test_f04r_has_damage_metadata(self):
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)
        page = next((p for p in pages if p.id == "f04r"), None)
        if page is None:
            pytest.skip("f04r not produced")
        assert page.damage is not None, "f04r should carry damage metadata"
        assert page.damage["type"] == "water"

    def test_f04v_has_damage_metadata(self):
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)
        page = next((p for p in pages if p.id == "f04v"), None)
        if page is None:
            pytest.skip("f04v not produced")
        assert page.damage is not None
        assert page.damage.get("corner") == "bottom_right"

    def test_f14r_is_irregular_vellum(self):
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)
        page = next((p for p in pages if p.id == "f14r"), None)
        if page is None:
            pytest.skip("f14r not produced")
        assert page.vellum_stock == "irregular"

    def test_overflow_folio_is_irregular_vellum(self):
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)
        overflow = next((p for p in pages if int(p.id[1:-1]) > 17), None)
        if overflow is None:
            pytest.skip("no overflow folio produced")
        assert overflow.vellum_stock == "irregular"

    def test_f01r_is_standard_vellum(self):
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)
        page = next((p for p in pages if p.id == "f01r"), None)
        assert page is not None
        assert page.vellum_stock == "standard"

    def test_f07r_has_hand_notes(self):
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)
        page = next((p for p in pages if p.id == "f07r"), None)
        if page is None:
            pytest.skip("f07r not produced")
        assert page.hand_notes is not None, "f07r should carry hand notes (multi_sitting)"


# ---------------------------------------------------------------------------
# Test: line numbering
# ---------------------------------------------------------------------------

class TestLineNumbering:
    def test_line_numbers_are_sequential_from_1(self):
        """Lines on each page must be numbered 1, 2, 3, ..."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        for p in pages:
            for expected, line in enumerate(p.lines, start=1):
                assert line.number == expected, (
                    f"{p.id}: line at index {expected-1} has number {line.number}, expected {expected}"
                )

    def test_no_empty_lines(self):
        """No line should have empty text."""
        sections, rm = _make_full_manuscript()
        pages = structure(sections, rm)

        for p in pages:
            for line in p.lines:
                assert line.text.strip(), f"{p.id} line {line.number}: text is empty"
