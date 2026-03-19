"""Register consistency validator.

Checks for:
  - missing_verbatim: is_verbatim=True but no reference table entry exists
  - register_mismatch: {la} passage contains clear German morphology markers
  - incompatible_transition: adjacent passages with hard register incompatibility
"""

from __future__ import annotations

from xl.models import IngestResult, Passage, Section, ValidationError
from xl.translate.verbatim import VerbatimNotFound, lookup as verbatim_lookup

# German morphological markers that would be unexpected in a pure {la} passage
_GERMAN_MARKERS = {"der", "die", "das", "und", "ich", "ein", "eine", "nicht",
                   "ist", "war", "er", "sie", "es", "wir", "ihr", "dem", "den"}


def validate(result: IngestResult) -> list[ValidationError]:
    """Run all consistency checks and return any errors found."""
    errors: list[ValidationError] = []
    for section in result.sections:
        passages = section.passages
        for i, passage in enumerate(passages):
            errors.extend(_check_verbatim(section, i, passage))
            errors.extend(_check_register_mismatch(section, i, passage))
        errors.extend(_check_transitions(section))
    return errors


def _check_verbatim(section: Section, idx: int, passage: Passage) -> list[ValidationError]:
    if not passage.is_verbatim:
        return []
    source = passage.verbatim_source or passage.text.strip()
    try:
        verbatim_lookup(source)
        return []
    except VerbatimNotFound:
        return [ValidationError(
            section_number=section.number,
            passage_index=idx,
            error_type="missing_verbatim",
            message=f"Verbatim source {source!r} has no entry in the reference table",
        )]


def _check_register_mismatch(section: Section, idx: int, passage: Passage) -> list[ValidationError]:
    if passage.register != "la" or passage.is_verbatim:
        return []
    words = set(passage.text.lower().split())
    german_found = words & _GERMAN_MARKERS
    if german_found:
        return [ValidationError(
            section_number=section.number,
            passage_index=idx,
            error_type="register_mismatch",
            message=f"Passage tagged {{la}} contains German markers: {sorted(german_found)}",
        )]
    return []


def _check_transitions(section: Section) -> list[ValidationError]:
    """Flag hard register incompatibilities between adjacent passages."""
    errors: list[ValidationError] = []
    passages = section.passages
    for i in range(len(passages) - 1):
        a, b = passages[i], passages[i + 1]
        # mhg next to la is fine (MHG quote embedded in Latin context)
        # de next to la is fine (normal register switching)
        # verbatim next to anything is fine
        # Only flag: non-verbatim mhg appearing in a section with no Eckhart context
        if a.register == "mhg" and not a.is_verbatim and b.register == "la":
            errors.append(ValidationError(
                section_number=section.number,
                passage_index=i,
                error_type="incompatible_transition",
                message="Non-verbatim MHG passage followed by Latin — expected verbatim MHG",
            ))
    return errors
