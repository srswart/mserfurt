"""Translation dispatcher — routes passages by register and verbatim flag.

Translation paths:
  is_verbatim=True       → verbatim lookup from reference table (no API)
  register="mhg"         → always verbatim (MHG passages are Eckhart quotations)
  dry_run=True           → preserve original English, method=dry_run
  register="de"|"la"     → Claude primary + GPT-4 validation
  register="mixed"       → clause splitter → per-clause Claude + GPT-4
  register="keep"        → original text preserved as-is
"""

from __future__ import annotations

from xl.models import (
    Passage,
    Section,
    TranslatedPassage,
    TranslatedSection,
    TranslationMethod,
    ValidationFlag,
)
from xl.translate import claude_client, gpt4_validator
from xl.translate.clause_splitter import split_mixed
from xl.translate.verbatim import VerbatimNotFound, lookup as verbatim_lookup


def translate_section(section: Section, dry_run: bool = False) -> TranslatedSection:
    """Translate all passages in a section."""
    translated = [
        translate_passage(p, dry_run=dry_run)
        for p in section.passages
    ]
    return TranslatedSection(section=section, passages=translated)


def translate_passage(passage: Passage, dry_run: bool = False) -> TranslatedPassage:
    """Translate a single passage, routing by register and verbatim flag."""

    # --- Verbatim paths (no LLM) ---
    if passage.is_verbatim or passage.register == "mhg":
        return _translate_verbatim(passage)

    # --- Dry-run: preserve original, skip all API calls ---
    if dry_run:
        return TranslatedPassage(
            original=passage,
            translated_text=passage.text,
            method=TranslationMethod.DRY_RUN,
            confidence=1.0,
        )

    # --- Keep: pass-through ---
    if passage.register == "kept":
        return TranslatedPassage(
            original=passage,
            translated_text=passage.text,
            method=TranslationMethod.KEPT,
            confidence=1.0,
        )

    # --- Mixed register: split at clause boundaries, translate each clause ---
    if passage.register == "mixed":
        return _translate_mixed(passage)

    # --- Standard de / la: Claude primary + GPT-4 validation ---
    return _translate_with_validation(passage)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _translate_verbatim(passage: Passage) -> TranslatedPassage:
    """Insert text directly from the reference table."""
    source_key = passage.verbatim_source or passage.text.strip()
    try:
        text = verbatim_lookup(source_key)
    except VerbatimNotFound:
        # Fallback: use the ingest-parsed text as-is (it's already in the
        # source language since ingest strips surrounding comments)
        text = passage.text
    return TranslatedPassage(
        original=passage,
        translated_text=text,
        method=TranslationMethod.VERBATIM,
        confidence=1.0,
    )


def _translate_with_validation(passage: Passage) -> TranslatedPassage:
    """Claude primary translation + GPT-4 validation, with optional revision."""
    translation = claude_client.translate(passage.text, passage.register)
    flags = gpt4_validator.validate(passage.text, translation)

    revised = False
    if flags:
        feedback = _format_feedback(flags)
        translation = claude_client.translate(passage.text, passage.register, feedback=feedback)
        revised = True

    return TranslatedPassage(
        original=passage,
        translated_text=translation,
        method=TranslationMethod.API,
        confidence=_confidence_from_flags(flags),
        validation_flags=flags,
        revised=revised,
    )


def _translate_mixed(passage: Passage) -> TranslatedPassage:
    """Split mixed passage at clause boundaries, translate each clause."""
    clauses = split_mixed(passage.text)

    translated_parts = []
    all_flags: list[ValidationFlag] = []
    any_revised = False

    for clause in clauses:
        if clause.language == "mixed":
            # Unsplittable: translate as a whole mixed passage
            translated = claude_client.translate(clause.text, "mixed")
        else:
            translated = claude_client.translate(clause.text, clause.language)

        flags = gpt4_validator.validate(clause.text, translated)
        if flags:
            feedback = _format_feedback(flags)
            translated = claude_client.translate(clause.text, clause.language, feedback=feedback)
            any_revised = True
            all_flags.extend(flags)

        translated_parts.append(translated)

    return TranslatedPassage(
        original=passage,
        translated_text=" ".join(translated_parts),
        method=TranslationMethod.API,
        confidence=_confidence_from_flags(all_flags),
        validation_flags=all_flags,
        revised=any_revised,
    )


def _format_feedback(flags: list[ValidationFlag]) -> str:
    return "\n".join(
        f"- [{f.line_id}] {f.issue_type}: {f.suggestion}" for f in flags
    )


def _confidence_from_flags(flags: list[ValidationFlag]) -> float:
    if not flags:
        return 0.95  # High but not 1.0 for API translations
    # Each flag reduces confidence slightly
    return max(0.5, 0.95 - len(flags) * 0.1)
