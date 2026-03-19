"""Mixed-register resolver — produces clause-level language assignments.

For non-mixed passages, returns a single ClauseRegister covering the whole text.
For {mixed} passages, delegates to the translate clause_splitter to split at
clause boundaries and assigns la/de per clause.
"""

from __future__ import annotations

from xl.models import ClauseRegister, Passage, RegisterTag
from xl.translate.clause_splitter import split_mixed


def resolve(passage: Passage) -> list[ClauseRegister]:
    """Return a list of ClauseRegister entries for a passage.

    Non-mixed passages return a single entry. Mixed passages are split
    at clause boundaries and each clause is assigned la or de.
    """
    if passage.register != "mixed":
        return [ClauseRegister(text=passage.text, language=_passage_language(passage))]

    clauses = split_mixed(passage.text)
    return [ClauseRegister(text=c.text, language=c.language) for c in clauses]


def _passage_language(passage: Passage) -> str:
    if passage.is_verbatim:
        src = (passage.verbatim_source or "").lower()
        if "eckhart" in src or "wirt" in src or "mhg" in src:
            return RegisterTag.MHG
        return RegisterTag.LA
    mapping = {
        "de": RegisterTag.DE,
        "la": RegisterTag.LA,
        "mhg": RegisterTag.MHG,
        "keep": RegisterTag.KEEP,
        "kept": RegisterTag.KEEP,
    }
    return mapping.get(passage.register, RegisterTag.DE)
