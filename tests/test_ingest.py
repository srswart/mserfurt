"""Tests for xl.ingest — manuscript parsing.

Written before implementation (TDD red-green). Uses the real annotated source
file as the primary fixture since ingest's only job is to parse that file.
"""

from pathlib import Path

import pytest

from xl.ingest import parse
from xl.models import ApparatusEntry, IngestResult, Section

SOURCE = Path(__file__).parent.parent / "source" / "ms-erfurt-source-annotated.md"


@pytest.fixture(scope="module")
def result() -> IngestResult:
    return parse(SOURCE)


# ---------------------------------------------------------------------------
# Frontmatter / manuscript metadata
# ---------------------------------------------------------------------------

class TestFrontmatter:
    def test_shelfmark(self, result):
        assert "Erfurt" in result.metadata.shelfmark
        assert "12" in result.metadata.shelfmark

    def test_author(self, result):
        assert "Konrad" in result.metadata.author

    def test_date(self, result):
        assert result.metadata.date == 1457

    def test_gathering_count(self, result):
        assert result.metadata.gathering == 17

    def test_storage(self, result):
        assert result.metadata.storage

    def test_discovery(self, result):
        assert result.metadata.discovery == 2019


# ---------------------------------------------------------------------------
# Folio map
# ---------------------------------------------------------------------------

class TestFolioMap:
    def test_folio_map_not_empty(self, result):
        assert len(result.metadata.folio_map) > 0

    def test_folio_map_contains_f04r(self, result):
        refs = [e.folio_ref for e in result.metadata.folio_map]
        assert any("f04r" in r for r in refs)

    def test_folio_map_contains_f07r(self, result):
        refs = [e.folio_ref for e in result.metadata.folio_map]
        assert any("f07r" in r for r in refs)

    def test_folio_map_contains_f14r(self, result):
        refs = [e.folio_ref for e in result.metadata.folio_map]
        assert any("f14r" in r for r in refs)

    def test_folio_map_f04r_has_damage(self, result):
        for entry in result.metadata.folio_map:
            if "f04r" in entry.folio_ref:
                assert entry.damage and "water" in entry.damage.lower()
                break
        else:
            pytest.fail("f04r not found in folio_map")

    def test_folio_map_f06r_has_hand_note(self, result):
        for entry in result.metadata.folio_map:
            if "f06r" in entry.folio_ref:
                assert entry.hand and "lateral" in entry.hand.lower()
                break
        else:
            pytest.fail("f06r not found in folio_map")


# ---------------------------------------------------------------------------
# Section parsing
# ---------------------------------------------------------------------------

class TestSections:
    def test_section_count(self, result):
        # Source has 7 labeled sections
        assert len(result.sections) == 7

    def test_section_numbers_sequential(self, result):
        numbers = [s.number for s in result.sections]
        assert numbers == list(range(1, 8))

    def test_section_1_title(self, result):
        assert "Opening" in result.sections[0].title

    def test_section_3_title_peter(self, result):
        assert "Peter" in result.sections[2].title

    def test_section_5_title_eckhart(self, result):
        assert "Eckhart" in result.sections[4].title

    def test_section_7_title_final(self, result):
        assert "Final" in result.sections[6].title or "Gathering" in result.sections[6].title

    def test_sections_have_passages(self, result):
        for section in result.sections:
            assert len(section.passages) > 0, f"Section {section.number} has no passages"


# ---------------------------------------------------------------------------
# Folio references per section
# ---------------------------------------------------------------------------

class TestFolioRefs:
    def test_section_1_folio_ref(self, result):
        assert result.sections[0].folio_ref  # f01r

    def test_section_3_folio_ref_contains_range(self, result):
        # Peter narrative: f04r-f05v
        ref = result.sections[2].folio_ref
        assert "f04r" in ref or "f04" in ref

    def test_section_4_folio_ref_f06r(self, result):
        ref = result.sections[3].folio_ref
        assert "f06r" in ref

    def test_section_5_folio_ref_f07r(self, result):
        ref = result.sections[4].folio_ref
        assert "f07r" in ref

    def test_section_7_folio_ref_f14r(self, result):
        ref = result.sections[6].folio_ref
        assert "f14r" in ref


# ---------------------------------------------------------------------------
# Register hints
# ---------------------------------------------------------------------------

class TestRegisterHints:
    def _all_registers(self, result) -> set[str]:
        return {p.register for s in result.sections for p in s.passages}

    def test_register_de_present(self, result):
        assert "de" in self._all_registers(result)

    def test_register_la_present(self, result):
        assert "la" in self._all_registers(result)

    def test_register_mixed_present(self, result):
        assert "mixed" in self._all_registers(result)

    def test_register_mhg_present(self, result):
        assert "mhg" in self._all_registers(result)


# ---------------------------------------------------------------------------
# Apparatus entries
# ---------------------------------------------------------------------------

class TestApparatus:
    def _all_apparatus(self, result) -> list[ApparatusEntry]:
        entries = []
        for s in result.sections:
            entries.extend(s.apparatus)
            for p in s.passages:
                entries.extend(p.apparatus)
        return entries

    def test_damage_entries_present(self, result):
        types = [e.type for e in self._all_apparatus(result)]
        assert "damage" in types or "damage_note" in types

    def test_hand_note_entries_present(self, result):
        types = [e.type for e in self._all_apparatus(result)]
        assert "hand_note" in types

    def test_lacuna_entries_present(self, result):
        types = [e.type for e in self._all_apparatus(result)]
        assert "lacuna" in types

    def test_gap_note_entries_present(self, result):
        types = [e.type for e in self._all_apparatus(result)]
        assert "gap_note" in types

    def test_peter_section_has_lacunae(self, result):
        peter = result.sections[2]  # Section 3: Peter Narrative
        lacuna_passages = [p for p in peter.passages if p.lacunae]
        assert len(lacuna_passages) > 0

    def test_f06r_section_has_hand_note(self, result):
        workshop = result.sections[3]  # Section 4: Workshop Visits (f06r)
        hand_entries = [e for e in workshop.apparatus if e.type == "hand_note"]
        assert len(hand_entries) > 0


# ---------------------------------------------------------------------------
# Verbatim passages
# ---------------------------------------------------------------------------

class TestVerbatim:
    def _verbatim_passages(self, result) -> list:
        return [p for s in result.sections for p in s.passages if p.is_verbatim]

    def test_verbatim_passages_exist(self, result):
        assert len(self._verbatim_passages(result)) > 0

    def test_verbatim_augustine_flagged(self, result):
        verbatim = self._verbatim_passages(result)
        augustine = [p for p in verbatim if p.verbatim_source and "Augustine" in p.verbatim_source or
                     p.verbatim_source and "Augustin" in p.verbatim_source or
                     p.verbatim_source and "fecisti" in p.text.lower() or
                     "fecisti" in p.text.lower()]
        # There should be at least one Augustine verbatim passage
        all_verbatim_texts = " ".join(p.text for p in verbatim)
        assert "fecisti" in all_verbatim_texts.lower() or any(
            p.verbatim_source and "Augustine" in (p.verbatim_source or "") for p in verbatim
        )

    def test_verbatim_mhg_eckhart_flagged(self, result):
        verbatim = self._verbatim_passages(result)
        mhg_verbatim = [p for p in verbatim if p.register == "mhg"]
        assert len(mhg_verbatim) > 0

    def test_wirt_passage_is_verbatim_mhg(self, result):
        # The pivotal Eckhart word "wirt" appears as verbatim MHG
        for s in result.sections:
            for p in s.passages:
                if p.register == "mhg" and "wirt" in p.text.lower():
                    assert p.is_verbatim
                    return
        pytest.fail("No MHG passage containing 'wirt' found")


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

class TestTextExtraction:
    def test_passages_have_non_empty_text(self, result):
        for s in result.sections:
            for p in s.passages:
                assert p.text.strip(), f"Empty passage in section {s.number}"

    def test_html_comments_stripped_from_text(self, result):
        for s in result.sections:
            for p in s.passages:
                assert "<!--" not in p.text, f"HTML comment leaked into passage text in section {s.number}"

    def test_konrad_voice_in_section_1(self, result):
        # Opening line should be in the first section's passages
        all_text = " ".join(p.text for p in result.sections[0].passages)
        assert "scribe" in all_text.lower() or "begins" in all_text.lower()
