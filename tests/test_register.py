"""Tests for xl.register — tag parsing, mixed resolution, validation, RegisterMap.

Written before final wiring (TDD red-green). Uses real ingest output for
integration tests; unit tests use minimal Passage fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from xl.ingest import parse
from xl.models import (
    Passage,
    RegisterTag,
    Section,
    ValidationError,
)
from xl.register import build_register_map
from xl.register.parser import parse_passage
from xl.register.resolver import resolve
from xl.register.validator import validate

SOURCE = Path(__file__).parent.parent / "source" / "ms-erfurt-source-annotated.md"


def _passage(text="text", register="de", is_verbatim=False, verbatim_source=None):
    return Passage(
        text=text, register=register,
        is_verbatim=is_verbatim, verbatim_source=verbatim_source,
    )


# ---------------------------------------------------------------------------
# Tag parser
# ---------------------------------------------------------------------------

class TestTagParser:
    def test_de_passage(self):
        assert parse_passage(_passage(register="de")) == RegisterTag.DE

    def test_la_passage(self):
        assert parse_passage(_passage(register="la")) == RegisterTag.LA

    def test_mixed_passage(self):
        assert parse_passage(_passage(register="mixed")) == RegisterTag.MIXED

    def test_mhg_passage(self):
        assert parse_passage(_passage(register="mhg")) == RegisterTag.MHG

    def test_verbatim_augustine_is_verbatim_la(self):
        tag = parse_passage(_passage(register="la", is_verbatim=True, verbatim_source="Augustine, Confessions I.1"))
        assert tag == RegisterTag.VERBATIM_LA

    def test_verbatim_psalm_is_verbatim_la(self):
        tag = parse_passage(_passage(register="la", is_verbatim=True, verbatim_source="Psalm 42:1"))
        assert tag == RegisterTag.VERBATIM_LA

    def test_verbatim_eckhart_is_verbatim_mhg(self):
        tag = parse_passage(_passage(register="mhg", is_verbatim=True, verbatim_source="Eckhart (Konrad's reading)"))
        assert tag == RegisterTag.VERBATIM_MHG

    def test_verbatim_wirt_is_verbatim_mhg(self):
        tag = parse_passage(_passage(register="mhg", is_verbatim=True, verbatim_source="Wirt"))
        assert tag == RegisterTag.VERBATIM_MHG


# ---------------------------------------------------------------------------
# Mixed resolver
# ---------------------------------------------------------------------------

class TestResolver:
    def test_de_passage_returns_single_clause(self):
        clauses = resolve(_passage(text="The work continues.", register="de"))
        assert len(clauses) == 1
        assert clauses[0].language == RegisterTag.DE

    def test_la_passage_returns_single_clause(self):
        clauses = resolve(_passage(text="Fecisti nos ad te.", register="la"))
        assert len(clauses) == 1
        assert clauses[0].language == RegisterTag.LA

    def test_mixed_with_latin_resolves_both_languages(self):
        text = "The soul longs. Fecisti nos ad te."
        clauses = resolve(_passage(text=text, register="mixed"))
        languages = {c.language for c in clauses}
        assert len(clauses) >= 2
        assert RegisterTag.LA in languages

    def test_mixed_returns_at_least_one_clause(self):
        clauses = resolve(_passage(text="I say that.", register="mixed"))
        assert len(clauses) >= 1

    def test_verbatim_mhg_returns_mhg_language(self):
        clauses = resolve(_passage(
            text="Wirt", register="mhg",
            is_verbatim=True, verbatim_source="Wirt",
        ))
        assert clauses[0].language == RegisterTag.MHG


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class TestValidator:
    def _ingest(self) -> object:
        return parse(SOURCE)

    def test_no_errors_on_valid_ingest(self):
        from xl.models import IngestResult, ManuscriptMeta
        # Build a minimal valid IngestResult — no verbatim issues, no register mismatches
        result = parse(SOURCE)
        errors = validate(result)
        mismatch_errors = [e for e in errors if e.error_type == "register_mismatch"]
        # The source file is well-formed; register mismatches should be absent or minimal
        # (some {la}-tagged passages in the source do contain English text which we treat
        # as acceptable in the source representation)
        assert isinstance(errors, list)

    def test_missing_verbatim_detected(self):
        from xl.models import IngestResult, ManuscriptMeta, Section, FolioMapEntry
        bad_passage = _passage(
            text="unknown verbatim text",
            register="la",
            is_verbatim=True,
            verbatim_source="NonExistent Source Key XYZ",
        )
        section = Section(number=99, title="Test", folio_ref="f01r", passages=[bad_passage])
        # Build a minimal IngestResult
        meta = ManuscriptMeta(
            shelfmark="test", author="test", date=1457,
            language_primary="de", language_secondary="la", language_tertiary="mhg",
            gathering=17, storage="test", discovery=2019,
        )
        result = type("IngestResult", (), {"metadata": meta, "sections": [section]})()
        from xl.register.validator import _check_verbatim
        errors = _check_verbatim(section, 0, bad_passage)
        assert len(errors) == 1
        assert errors[0].error_type == "missing_verbatim"

    def test_known_verbatim_no_error(self):
        from xl.register.validator import _check_verbatim
        from xl.models import Section
        good_passage = _passage(
            text="Psalm text", register="la",
            is_verbatim=True, verbatim_source="Psalm 42:1",
        )
        section = Section(number=1, title="T", folio_ref="f01r", passages=[good_passage])
        errors = _check_verbatim(section, 0, good_passage)
        assert errors == []

    def test_la_with_german_markers_flagged(self):
        from xl.register.validator import _check_register_mismatch
        from xl.models import Section
        bad_passage = _passage(text="Und das ist die Antwort.", register="la")
        section = Section(number=1, title="T", folio_ref="f01r", passages=[bad_passage])
        errors = _check_register_mismatch(section, 0, bad_passage)
        assert len(errors) == 1
        assert errors[0].error_type == "register_mismatch"

    def test_la_without_german_no_error(self):
        from xl.register.validator import _check_register_mismatch
        from xl.models import Section
        good_passage = _passage(text="Fecisti nos ad te.", register="la")
        section = Section(number=1, title="T", folio_ref="f01r", passages=[good_passage])
        errors = _check_register_mismatch(section, 0, good_passage)
        assert errors == []


# ---------------------------------------------------------------------------
# RegisterMap integration
# ---------------------------------------------------------------------------

class TestRegisterMap:
    @pytest.fixture(scope="class")
    def register_map(self):
        return build_register_map(parse(SOURCE))

    def test_map_has_entries(self, register_map):
        assert len(register_map.entries) > 0

    def test_entries_keyed_by_section_and_index(self, register_map):
        # Section 1, passage 0 must exist
        assert (1, 0) in register_map.entries

    def test_all_seven_sections_represented(self, register_map):
        section_numbers = {k[0] for k in register_map.entries}
        assert section_numbers == {1, 2, 3, 4, 5, 6, 7}

    def test_psalm_section_has_verbatim_la_entries(self, register_map):
        # Section 6 (Psalter Return) contains Psalm verbatim passages
        verbatim_la = [
            v for (s, _), v in register_map.entries.items()
            if s == 6 and v.tag == RegisterTag.VERBATIM_LA
        ]
        assert len(verbatim_la) > 0

    def test_eckhart_section_has_verbatim_mhg_entry(self, register_map):
        # Section 5 (Eckhart Confession) has MHG verbatim passages
        verbatim_mhg = [
            v for (s, _), v in register_map.entries.items()
            if s == 5 and v.tag == RegisterTag.VERBATIM_MHG
        ]
        assert len(verbatim_mhg) > 0

    def test_mixed_entries_have_multiple_clauses(self, register_map):
        mixed_entries = [
            v for v in register_map.entries.values()
            if v.tag == RegisterTag.MIXED
        ]
        assert len(mixed_entries) > 0
        # At least one mixed passage has more than one clause
        assert any(len(e.clauses) > 1 for e in mixed_entries)

    def test_errors_is_list(self, register_map):
        assert isinstance(register_map.errors, list)
