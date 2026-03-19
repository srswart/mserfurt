"""Shared data classes for the XL pipeline.

These are the internal contracts between ingest, register, translate,
folio, annotate, and export. All downstream components consume these types.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ApparatusEntry:
    """A single CLIO-7 apparatus annotation extracted from the source."""
    type: str               # "damage" | "lacuna" | "hand_note" | "gap_note" | "damage_note"
    description: str
    folio_ref: str | None = None


@dataclass
class Passage:
    """One passage of Konrad's text within a section, with its metadata."""
    text: str
    register: str           # "de" | "la" | "mixed" | "mhg"
    is_verbatim: bool = False
    verbatim_source: str | None = None
    lacunae: list[str] = field(default_factory=list)
    apparatus: list[ApparatusEntry] = field(default_factory=list)


@dataclass
class Section:
    """One section of the manuscript (corresponds to a CLIO-7 section block)."""
    number: int
    title: str
    folio_ref: str          # e.g. "f01r", "f04r-f05v", "f07r-f07v"
    passages: list[Passage] = field(default_factory=list)
    apparatus: list[ApparatusEntry] = field(default_factory=list)


@dataclass
class FolioMapEntry:
    """One entry from the source frontmatter folio_map."""
    folio_ref: str
    content: str | None = None
    damage: str | None = None
    hand: str | None = None
    vellum: str | None = None


@dataclass
class ManuscriptMeta:
    """Parsed from the YAML frontmatter of the annotated source file."""
    shelfmark: str
    author: str
    date: int
    language_primary: str
    language_secondary: str
    language_tertiary: str
    gathering: int
    storage: str
    discovery: int
    folio_map: list[FolioMapEntry] = field(default_factory=list)


@dataclass
class IngestResult:
    """Full output of the ingest stage."""
    metadata: ManuscriptMeta
    sections: list[Section] = field(default_factory=list)
