"""Tests for xl.translate — translation dispatcher, verbatim lookup, clause splitter.

Written before final wiring (TDD red-green). All API calls are mocked —
no ANTHROPIC_API_KEY or OPENAI_API_KEY required to run the test suite.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from xl.models import Passage, TranslationMethod, ValidationFlag
from xl.translate.clause_splitter import split_mixed
from xl.translate.dispatcher import translate_passage, translate_section
from xl.translate.verbatim import VerbatimNotFound, known_keys, lookup


# ---------------------------------------------------------------------------
# Verbatim reference table
# ---------------------------------------------------------------------------

class TestVerbatimLookup:
    def test_augustine_confessions_key_exists(self):
        text = lookup("Augustine, Confessions I.1")
        assert "fecisti nos ad te" in text

    def test_augustine_truncated_key_exists(self):
        text = lookup("Augustine (truncated)")
        assert "fecisti nos ad te" in text
        assert "inquietum" not in text  # truncated form omits the second clause

    def test_psalm_42_1_key_exists(self):
        text = lookup("Psalm 42:1")
        assert "cervus" in text

    def test_psalm_42_2_key_exists(self):
        text = lookup("Psalm 42:2")
        assert "anima mea" in text

    def test_eckhart_original_key_exists(self):
        text = lookup("Eckhart, Sermon 12 (original)")
        assert "ist" in text
        assert "sêle" in text

    def test_eckhart_konrad_variant_key_exists(self):
        text = lookup("Eckhart (Konrad's reading)")
        assert "wirt" in text

    def test_wirt_bare_key_exists(self):
        text = lookup("Wirt")
        assert text == "Wirt"

    def test_unknown_key_raises(self):
        with pytest.raises(VerbatimNotFound):
            lookup("nonexistent key that does not exist")

    def test_known_keys_not_empty(self):
        assert len(known_keys()) > 0


# ---------------------------------------------------------------------------
# Clause splitter
# ---------------------------------------------------------------------------

class TestClauseSplitter:
    def test_splits_at_period(self):
        text = "The work is still the work. I say that without consolation."
        clauses = split_mixed(text)
        assert len(clauses) >= 2

    def test_splits_at_em_dash(self):
        text = "Not proud — I want that distinction to be clear."
        clauses = split_mixed(text)
        assert len(clauses) >= 2

    def test_latin_terms_classified_la(self):
        clauses = split_mixed("Fecisti nos ad te. The current moves through my hand.")
        la_clauses = [c for c in clauses if c.language == "la"]
        assert len(la_clauses) >= 1

    def test_narrative_classified_de(self):
        clauses = split_mixed("I bought eggs I did not need. Fecisti nos ad te.")
        de_clauses = [c for c in clauses if c.language == "de"]
        assert len(de_clauses) >= 1

    def test_single_sentence_returns_one_clause(self):
        clauses = split_mixed("I bought eggs.")
        assert len(clauses) == 1

    def test_unsplittable_returns_mixed_language(self):
        clauses = split_mixed("unsplittable")
        assert clauses[0].language == "mixed"


# ---------------------------------------------------------------------------
# Dispatcher — verbatim path
# ---------------------------------------------------------------------------

def _make_passage(text="test text", register="de", is_verbatim=False, verbatim_source=None):
    return Passage(
        text=text,
        register=register,
        is_verbatim=is_verbatim,
        verbatim_source=verbatim_source,
    )


class TestDispatcherVerbatim:
    def test_verbatim_flag_uses_verbatim_method(self):
        passage = _make_passage(
            text="fecisti nos ad te",
            register="la",
            is_verbatim=True,
            verbatim_source="Augustine, Confessions I.1",
        )
        result = translate_passage(passage)
        assert result.method == TranslationMethod.VERBATIM

    def test_verbatim_no_api_calls(self):
        passage = _make_passage(
            text="Wirt",
            register="mhg",
            is_verbatim=True,
            verbatim_source="Wirt",
        )
        with patch("xl.translate.dispatcher.claude_client.translate") as mock_claude:
            with patch("xl.translate.dispatcher.gpt4_validator.validate") as mock_gpt4:
                translate_passage(passage)
                mock_claude.assert_not_called()
                mock_gpt4.assert_not_called()

    def test_mhg_register_always_verbatim(self):
        # MHG passages are always Eckhart quotations — no LLM
        passage = _make_passage(text="Wirt", register="mhg", is_verbatim=True, verbatim_source="Wirt")
        result = translate_passage(passage)
        assert result.method == TranslationMethod.VERBATIM

    def test_verbatim_text_matches_reference_table(self):
        passage = _make_passage(
            text="Psalm 42:1",
            register="la",
            is_verbatim=True,
            verbatim_source="Psalm 42:1",
        )
        result = translate_passage(passage)
        assert "cervus" in result.translated_text

    def test_verbatim_confidence_is_1(self):
        passage = _make_passage(
            text="Wirt", register="mhg", is_verbatim=True, verbatim_source="Wirt"
        )
        result = translate_passage(passage)
        assert result.confidence == 1.0


# ---------------------------------------------------------------------------
# Dispatcher — dry-run path
# ---------------------------------------------------------------------------

class TestDispatcherDryRun:
    def test_dry_run_de_preserves_original(self):
        passage = _make_passage(text="The work is still the work.", register="de")
        with patch("xl.translate.dispatcher.claude_client.translate") as mock:
            result = translate_passage(passage, dry_run=True)
            mock.assert_not_called()
        assert result.translated_text == passage.text
        assert result.method == TranslationMethod.DRY_RUN

    def test_dry_run_la_preserves_original(self):
        passage = _make_passage(text="You made us for yourself.", register="la")
        with patch("xl.translate.dispatcher.claude_client.translate") as mock:
            result = translate_passage(passage, dry_run=True)
            mock.assert_not_called()
        assert result.translated_text == passage.text

    def test_dry_run_mixed_no_api_calls(self):
        passage = _make_passage(text="I say that without consolation.", register="mixed")
        with patch("xl.translate.dispatcher.claude_client.translate") as mc:
            with patch("xl.translate.dispatcher.gpt4_validator.validate") as mg:
                translate_passage(passage, dry_run=True)
                mc.assert_not_called()
                mg.assert_not_called()


# ---------------------------------------------------------------------------
# Dispatcher — API path (de / la) with mocked clients
# ---------------------------------------------------------------------------

class TestDispatcherAPI:
    def test_de_passage_calls_claude(self):
        passage = _make_passage(text="The current of belief.", register="de")
        with patch("xl.translate.dispatcher.claude_client.translate", return_value="Der Strom des Glaubens.") as mock_claude:
            with patch("xl.translate.dispatcher.gpt4_validator.validate", return_value=[]):
                result = translate_passage(passage)
        mock_claude.assert_called_once_with("The current of belief.", "de")
        assert result.method == TranslationMethod.API

    def test_la_passage_calls_claude_with_la_register(self):
        passage = _make_passage(text="You made us for yourself.", register="la")
        with patch("xl.translate.dispatcher.claude_client.translate", return_value="Fecisti nos ad te.") as mock_claude:
            with patch("xl.translate.dispatcher.gpt4_validator.validate", return_value=[]):
                translate_passage(passage)
        mock_claude.assert_called_once_with("You made us for yourself.", "la")

    def test_gpt4_called_after_claude(self):
        passage = _make_passage(text="The press was loud.", register="de")
        with patch("xl.translate.dispatcher.claude_client.translate", return_value="Die Presse war laut."):
            with patch("xl.translate.dispatcher.gpt4_validator.validate", return_value=[]) as mock_gpt4:
                translate_passage(passage)
        mock_gpt4.assert_called_once()

    def test_gpt4_flag_triggers_revision(self):
        passage = _make_passage(text="The press made sounds.", register="de")
        flag = ValidationFlag(line_id="1", issue_type="anachronism", suggestion="use older form")
        with patch("xl.translate.dispatcher.claude_client.translate", return_value="translation") as mock_claude:
            with patch("xl.translate.dispatcher.gpt4_validator.validate", return_value=[flag]):
                result = translate_passage(passage)
        # Claude called twice: initial + revision
        assert mock_claude.call_count == 2
        assert result.revised is True

    def test_no_flags_means_no_revision(self):
        passage = _make_passage(text="He stood at the window.", register="de")
        with patch("xl.translate.dispatcher.claude_client.translate", return_value="Er stand am Fenster.") as mock_claude:
            with patch("xl.translate.dispatcher.gpt4_validator.validate", return_value=[]):
                result = translate_passage(passage)
        assert mock_claude.call_count == 1
        assert result.revised is False
        assert result.validation_flags == []

    def test_flags_stored_in_result(self):
        passage = _make_passage(text="The soul longs.", register="la")
        flag = ValidationFlag(line_id="1", issue_type="humanist_latin", suggestion="use clerical form")
        with patch("xl.translate.dispatcher.claude_client.translate", return_value="Anima desiderat."):
            with patch("xl.translate.dispatcher.gpt4_validator.validate", return_value=[flag]):
                result = translate_passage(passage)
        assert len(result.validation_flags) == 1
        assert result.validation_flags[0].issue_type == "humanist_latin"


# ---------------------------------------------------------------------------
# Dispatcher — mixed register
# ---------------------------------------------------------------------------

class TestDispatcherMixed:
    def test_mixed_passage_produces_api_translation(self):
        passage = _make_passage(
            text="I say that without consolation. Fecisti nos ad te.",
            register="mixed",
        )
        with patch("xl.translate.dispatcher.claude_client.translate", return_value="Ich sage das. Fecisti nos ad te."):
            with patch("xl.translate.dispatcher.gpt4_validator.validate", return_value=[]):
                result = translate_passage(passage)
        assert result.method == TranslationMethod.API

    def test_mixed_passage_calls_claude_at_least_once(self):
        passage = _make_passage(
            text="The soul is made. Deus fecit.",
            register="mixed",
        )
        with patch("xl.translate.dispatcher.claude_client.translate", return_value="translation") as mock_claude:
            with patch("xl.translate.dispatcher.gpt4_validator.validate", return_value=[]):
                translate_passage(passage)
        assert mock_claude.call_count >= 1


# ---------------------------------------------------------------------------
# translate_section integration
# ---------------------------------------------------------------------------

class TestTranslateSection:
    def test_translate_section_returns_translated_section(self):
        from xl.models import Section
        section = Section(
            number=1,
            title="Test",
            folio_ref="f01r",
            passages=[
                _make_passage("The work continues.", "de"),
                _make_passage("Wirt", "mhg", is_verbatim=True, verbatim_source="Wirt"),
            ],
        )
        with patch("xl.translate.dispatcher.claude_client.translate", return_value="Die Arbeit geht weiter."):
            with patch("xl.translate.dispatcher.gpt4_validator.validate", return_value=[]):
                result = translate_section(section, dry_run=False)
        assert len(result.passages) == 2
        assert result.passages[1].method == TranslationMethod.VERBATIM  # mhg is verbatim
        assert result.section is section
