"""Mixed-register clause splitter.

For {mixed} passages, splits at clause boundaries and assigns a language
tag to each clause. Theological/sacred clauses lean Latin; narrative/
material clauses lean German.

Heuristic: clauses containing Latin theological terms are tagged "la";
everything else is tagged "de". The splitter does not translate — it only
annotates boundaries for the Claude API call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Terms strongly associated with the Latin register in Konrad's voice
_LATIN_INDICATORS = {
    # Theological abstractions
    "deus", "dei", "deo", "dominus", "domini", "domino",
    "anima", "animae", "animam",
    "verbum", "verbi", "verbo",
    "gratia", "gratiam", "spiritus",
    "fecisti", "inquietum", "requiescat",
    "agro", "dominico",
    # Direct address to God
    "te", "tibi",
    # Latin proper names and titles
    "augustinus", "augustini", "augustinum",
    "eckhart", "eckhardus",
    "quemadmodum", "desiderat", "cervus", "fontes", "aquarum",
    "sic", "psalmus",
}

# Clause boundary markers
_CLAUSE_SPLIT_RE = re.compile(r"(?<=[.;!?—])\s+")


@dataclass
class Clause:
    text: str
    language: str  # "de" | "la"


def split_mixed(text: str) -> list[Clause]:
    """Split a mixed-register passage into language-annotated clauses.

    Returns a list of Clause objects. If the text cannot be split (no
    boundary markers), returns a single Clause with language="mixed".
    """
    raw_clauses = _CLAUSE_SPLIT_RE.split(text.strip())
    if len(raw_clauses) <= 1:
        return [Clause(text=text.strip(), language="mixed")]

    result = []
    for clause in raw_clauses:
        clause = clause.strip()
        if not clause:
            continue
        lang = _classify_clause(clause)
        result.append(Clause(text=clause, language=lang))
    return result


def _classify_clause(clause: str) -> str:
    """Classify a single clause as 'la' or 'de' based on vocabulary heuristics."""
    words = set(re.findall(r"\b\w+\b", clause.lower()))
    if words & _LATIN_INDICATORS:
        return "la"
    return "de"
