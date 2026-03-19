"""Register tag parser — maps Passage fields to RegisterTag constants."""

from __future__ import annotations

from xl.models import Passage, RegisterTag


def parse_passage(passage: Passage) -> str:
    """Return the RegisterTag constant for a passage.

    Verbatim passages are mapped to their specific verbatim tag based on
    the verbatim_source string; non-verbatim passages map directly from
    the register field.
    """
    if passage.is_verbatim:
        return _verbatim_tag(passage.verbatim_source or "")
    return _register_tag(passage.register)


def _verbatim_tag(source: str) -> str:
    src = source.lower()
    if "augustine" in src or "augustin" in src or "psalm" in src or "finis" in src:
        return RegisterTag.VERBATIM_LA
    if "eckhart" in src or "wirt" in src or "ist" in src or "mhg" in src or "sînem" in src:
        return RegisterTag.VERBATIM_MHG
    # Default: if the source is Latin-looking, treat as Latin verbatim
    return RegisterTag.VERBATIM_LA


def _register_tag(register: str) -> str:
    mapping = {
        "de": RegisterTag.DE,
        "la": RegisterTag.LA,
        "mixed": RegisterTag.MIXED,
        "mhg": RegisterTag.MHG,
        "keep": RegisterTag.KEEP,
        "kept": RegisterTag.KEEP,
    }
    return mapping.get(register, RegisterTag.DE)
