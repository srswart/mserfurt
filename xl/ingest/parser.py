"""Parse ms-erfurt-source-annotated.md into an IngestResult.

The source file has three structural layers:
  1. YAML frontmatter (between --- delimiters) — manuscript metadata + folio_map
  2. Section comment blocks (<!-- SECTION N: title -->) — major content divisions
  3. Register hints (<!-- register: X -->) — per-passage language tags

Within passages, CLIO-7 apparatus is encoded as HTML comments:
  <!-- hand_note: "..." -->
  <!-- lacuna: [—] ... -->
  <!-- damage_note: ... -->
  <!-- gap_note: ... -->
  <!-- VERBATIM: source -->
  <!-- VERBATIM MHG: source -->
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import yaml

from xl.models import (
    ApparatusEntry,
    FolioMapEntry,
    IngestResult,
    ManuscriptMeta,
    Passage,
    Section,
)

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

# Locate each SECTION header line — used as split points
_SECTION_LINE_RE = re.compile(r"<!--\s*SECTION\s+(\d+):\s*(.+?)\s*-->")

# Folio reference line in header block
_FOLIO_RE = re.compile(r"<!--\s*Folios?:\s*(.+?)\s*-->")

# Header-block single-line apparatus
_HAND_HEADER_RE = re.compile(r"<!--\s*Hand:\s*(.+?)\s*-->")
_DAMAGE_HEADER_RE = re.compile(r"<!--\s*DAMAGE:\s*(.+?)\s*-->")

# Inline apparatus within passage blocks (single-line comments only)
_HAND_NOTE_RE = re.compile(r"""<!--\s*hand_note:\s*"(.+?)"\s*-->""")
_HAND_NOTE_RE2 = re.compile(r"""<!--\s*hand_note:\s*'(.+?)'\s*-->""")
_HAND_NOTE_RE3 = re.compile(r"""<!--\s*hand_note:\s*(.+?)\s*-->""")  # unquoted fallback
_GAP_NOTE_RE = re.compile(r"<!--\s*gap_note:\s*(.+?)\s*-->")
_DAMAGE_NOTE_RE = re.compile(r"<!--\s*damage_note:\s*(.+?)\s*-->")
_LACUNA_RE = re.compile(r"<!--\s*lacuna:\s*(.+?)\s*-->")

# Register and verbatim
_REGISTER_RE = re.compile(r"<!--\s*register:\s*(\w+)\s*-->")
# Verbatim: match <!-- VERBATIM ... --> or <!-- VERBATIM MHG: ... --> etc.
_VERBATIM_LINE_RE = re.compile(r"<!--\s*VERBATIM(?:\s+\w+)?:\s*(.+?)\s*-->")
# Also match bare <!-- VERBATIM MHG --> / <!-- VERBATIM Latin --> (no colon)
_VERBATIM_BARE_RE = re.compile(r"<!--\s*VERBATIM(?:\s+\w+)?\s*-->")

# Strip all HTML comments from text
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

_DIVIDER = "✦ ✦ ✦"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse(source_path: str | Path) -> IngestResult:
    """Parse the annotated source manuscript and return a structured IngestResult."""
    text = Path(source_path).read_text(encoding="utf-8")

    fm_match = _FRONTMATTER_RE.match(text)
    if not fm_match:
        raise ValueError(f"No YAML frontmatter found in {source_path}")

    metadata = _parse_frontmatter(fm_match.group(1))
    body = text[fm_match.end():]
    sections = list(_parse_sections(body))

    return IngestResult(metadata=metadata, sections=sections)


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------

def _parse_frontmatter(yaml_text: str) -> ManuscriptMeta:
    data = yaml.safe_load(yaml_text)
    ms = data["manuscript"]
    folio_map = _parse_folio_map(data.get("folio_map", {}))
    gathering_raw = ms.get("gathering", "17 folios")
    if isinstance(gathering_raw, str):
        m = re.search(r"\d+", gathering_raw)
        gathering = int(m.group(0)) if m else 17
    else:
        gathering = int(gathering_raw)
    return ManuscriptMeta(
        shelfmark=ms["shelfmark"],
        author=ms["author"],
        date=int(ms["date"]),
        language_primary=ms["language_primary"],
        language_secondary=ms["language_secondary"],
        language_tertiary=ms["language_tertiary"],
        gathering=gathering,
        storage=ms["storage"],
        discovery=int(ms["discovery"]),
        folio_map=folio_map,
    )


def _parse_folio_map(raw: dict) -> list[FolioMapEntry]:
    entries = []
    for ref, info in raw.items():
        if isinstance(info, dict):
            entries.append(FolioMapEntry(
                folio_ref=str(ref),
                content=info.get("content"),
                damage=str(info["damage"]) if info.get("damage") and info["damage"] != "none" else None,
                hand=str(info["hand"]) if info.get("hand") and info["hand"] != "standard" else info.get("hand"),
                vellum=info.get("vellum"),
            ))
        else:
            entries.append(FolioMapEntry(folio_ref=str(ref)))
    return entries


# ---------------------------------------------------------------------------
# Section parsing — two-pass approach
# ---------------------------------------------------------------------------

def _parse_sections(body: str) -> Iterator[Section]:
    """Split body on SECTION header lines, yield one Section per header."""
    # Find all section-header line positions
    markers = list(_SECTION_LINE_RE.finditer(body))
    if not markers:
        return

    for i, marker in enumerate(markers):
        number = int(marker.group(1))
        title = marker.group(2).strip()

        # The header block is the lines immediately around the SECTION line.
        # Look back to find the opening <!-- === --> divider.
        block_start = _find_divider_before(body, marker.start())
        # Look forward to find the closing <!-- === --> divider.
        block_end = _find_divider_after(body, marker.end())

        header_block = body[block_start:block_end]

        # Content runs from end of header block to start of next section's opening divider
        content_start = block_end
        if i + 1 < len(markers):
            next_block_start = _find_divider_before(body, markers[i + 1].start())
            content_end = next_block_start
        else:
            content_end = len(body)
        content = body[content_start:content_end]

        # Folio reference
        folio_match = _FOLIO_RE.search(header_block)
        folio_ref = folio_match.group(1).strip() if folio_match else ""

        # Section-level apparatus
        apparatus: list[ApparatusEntry] = []
        hand_match = _HAND_HEADER_RE.search(header_block)
        if hand_match:
            apparatus.append(ApparatusEntry(type="hand_note", description=hand_match.group(1).strip(), folio_ref=folio_ref))
        damage_match = _DAMAGE_HEADER_RE.search(header_block)
        if damage_match:
            apparatus.append(ApparatusEntry(type="damage", description=damage_match.group(1).strip(), folio_ref=folio_ref))

        # Inline apparatus in the content (single-line comment forms)
        for hn in _iter_hand_notes(content):
            apparatus.append(ApparatusEntry(type="hand_note", description=hn, folio_ref=folio_ref))
        for gn in _GAP_NOTE_RE.finditer(content):
            apparatus.append(ApparatusEntry(type="gap_note", description=gn.group(1).strip(), folio_ref=folio_ref))
        for dn in _DAMAGE_NOTE_RE.finditer(content):
            apparatus.append(ApparatusEntry(type="damage_note", description=dn.group(1).strip(), folio_ref=folio_ref))

        passages = list(_parse_passages(content, folio_ref))

        yield Section(
            number=number,
            title=title,
            folio_ref=folio_ref,
            passages=passages,
            apparatus=apparatus,
        )


def _find_divider_before(body: str, pos: int) -> int:
    """Find the start of the <!-- ==== --> line before pos, or pos if not found."""
    segment = body[:pos]
    last_divider = segment.rfind("<!-- =")
    return last_divider if last_divider != -1 else pos


def _find_divider_after(body: str, pos: int) -> int:
    """Find the end of the first <!-- ==== --> line after pos."""
    m = re.search(r"<!--\s*={20,}\s*-->", body[pos:])
    if m:
        return pos + m.end()
    return pos


def _iter_hand_notes(content: str) -> Iterator[str]:
    """Yield all hand_note values from content, handling quoted and unquoted forms."""
    for m in _HAND_NOTE_RE.finditer(content):
        yield m.group(1).strip()
    for m in _HAND_NOTE_RE2.finditer(content):
        yield m.group(1).strip()
    # Unquoted form: only if not already matched by quoted forms
    seen_positions = set(
        m.start() for m in _HAND_NOTE_RE.finditer(content)
    ) | set(
        m.start() for m in _HAND_NOTE_RE2.finditer(content)
    )
    for m in _HAND_NOTE_RE3.finditer(content):
        if m.start() not in seen_positions:
            val = m.group(1).strip().strip('"').strip("'")
            yield val


# ---------------------------------------------------------------------------
# Passage parsing
# ---------------------------------------------------------------------------

def _parse_passages(content: str, folio_ref: str) -> Iterator[Passage]:
    """Split content on register hints and yield one Passage per register block."""
    markers = list(_REGISTER_RE.finditer(content))
    if not markers:
        return

    for i, marker in enumerate(markers):
        register = marker.group(1)
        block_start = marker.end()
        block_end = markers[i + 1].start() if i + 1 < len(markers) else len(content)
        block = content[block_start:block_end]

        # Passage-level apparatus
        apparatus: list[ApparatusEntry] = []
        lacunae: list[str] = []

        for m in _LACUNA_RE.finditer(block):
            desc = m.group(1).strip()
            lacunae.append(desc)
            apparatus.append(ApparatusEntry(type="lacuna", description=desc, folio_ref=folio_ref))

        # Verbatim detection: either <!-- VERBATIM ...: source --> or <!-- VERBATIM MHG -->
        verbatim_match = _VERBATIM_LINE_RE.search(block)
        verbatim_bare = _VERBATIM_BARE_RE.search(block)
        is_verbatim = verbatim_match is not None or verbatim_bare is not None
        verbatim_source: str | None = None
        if verbatim_match:
            verbatim_source = verbatim_match.group(1).strip()
        elif verbatim_bare:
            verbatim_source = verbatim_bare.group(0).strip("<!-- >").strip()

        # Strip all HTML comments to get clean text
        text = _COMMENT_RE.sub("", block).strip()
        text = text.replace(_DIVIDER, "").strip()

        if not text:
            continue

        yield Passage(
            text=text,
            register=register,
            is_verbatim=is_verbatim,
            verbatim_source=verbatim_source,
            lacunae=lacunae,
            apparatus=apparatus,
        )
