"""Register — parse, resolve, and validate language register hints."""

from __future__ import annotations

from xl.models import IngestResult, PassageRegister, RegisterMap
from xl.register import parser, resolver, validator


def build_register_map(result: IngestResult) -> RegisterMap:
    """Build a complete RegisterMap from an IngestResult.

    For each passage in each section:
    - Parses the raw register hint into a RegisterTag
    - Resolves {mixed} passages to clause-level language assignments
    - Validates consistency across all passages

    Returns a RegisterMap with entries keyed by (section_number, passage_index).
    """
    entries: dict[tuple[int, int], PassageRegister] = {}

    for section in result.sections:
        for i, passage in enumerate(section.passages):
            tag = parser.parse_passage(passage)
            clauses = resolver.resolve(passage)
            entries[(section.number, i)] = PassageRegister(
                tag=tag,
                clauses=clauses,
                is_verbatim=passage.is_verbatim,
                verbatim_source=passage.verbatim_source,
            )

    errors = validator.validate(result)
    return RegisterMap(entries=entries, errors=errors)


__all__ = ["build_register_map"]
