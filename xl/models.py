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


# ---------------------------------------------------------------------------
# Translate stage output
# ---------------------------------------------------------------------------

class TranslationMethod:
    API = "api"           # Translated by Claude (primary) + GPT-4 (validation)
    VERBATIM = "verbatim" # Inserted directly from reference table — no LLM
    DRY_RUN = "dry_run"   # --dry-run mode: original text preserved, no API calls
    KEPT = "kept"         # {keep} register: original phrase preserved as-is


@dataclass
class ValidationFlag:
    """A single flag from the GPT-4 validation pass."""
    line_id: str
    issue_type: str   # "anachronism" | "register_error" | "grammatical_form" | "humanist_latin"
    suggestion: str


@dataclass
class TranslatedPassage:
    """One translated passage — the output of translating a single Passage."""
    original: Passage
    translated_text: str
    method: str                       # TranslationMethod constant
    confidence: float = 1.0           # 0.0–1.0; verbatim=1.0, api varies
    validation_flags: list[ValidationFlag] = field(default_factory=list)
    revised: bool = False             # True if GPT-4 flags triggered a Claude revision


@dataclass
class TranslatedSection:
    """Full output of translating one Section."""
    section: Section
    passages: list[TranslatedPassage] = field(default_factory=list)
