"""Folio structuring — distribute translated passages across 17 folios.

Consumes TranslatedSection + RegisterMap from upstream pipeline stages and
produces an ordered list of FolioPage objects matching the TD-001-A contract.

Key constraints from CLIO-7 / TD-001-A:
  - f04r-f05v: damaged pages (reduced line budgets)
  - f07r-f07v: Eckhart confession (section 5) — hard-pinned start at f07r
  - f14r-f17v: final gathering (section 7) — hard-pinned start at f14r
  - f14r-f17v: irregular vellum stock
  - Section 3 (Peter narrative) must not overflow past f05v
"""

from __future__ import annotations

from xl.models import FolioPage, Line, TranslatedPassage, TranslatedSection, RegisterMap

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CHARS_PER_LINE = 60

_DEFAULT_LINE_BUDGET = 32

# Per-folio reduced line budgets for damaged pages (derived from CLIO-7 folio_map)
_LINE_BUDGETS: dict[str, int] = {
    "f04r": 22,   # water_from_above_partial
    "f04v": 18,   # water_from_above + missing_corner_bottom_right
    "f05r": 25,   # water_diminishing
    "f05v": 25,   # water_diminishing
}

# Per-folio damage metadata (type + extent from CLIO-7)
_DAMAGE: dict[str, dict] = {
    "f04r": {"type": "water", "extent": "partial", "direction": "from_above",
             "notes": "water from above (partial)"},
    "f04v": {"type": "water", "extent": "severe", "direction": "from_above",
             "corner": "bottom_right", "notes": "water from above + missing corner"},
    "f05r": {"type": "water", "extent": "partial", "direction": "from_above",
             "notes": "water diminishing"},
    "f05v": {"type": "water", "extent": "partial", "direction": "from_above",
             "notes": "water diminishing"},
}

# Per-folio hand notes (derived from CLIO-7 folio_map)
_HAND_NOTES: dict[str, dict] = {
    "f06r": {"pressure": "increased_lateral",
             "notes": "increased lateral pressure on downstrokes"},
    "f06v": {"pressure": "increased_lateral",
             "notes": "increased lateral pressure"},
    "f07r": {"ink_density": "variable_multi_sitting",
             "notes": "written across multiple sittings — ink density varies"},
    "f07v": {"ink_density": "variable_multi_sitting", "scale": "smaller_economical",
             "notes": "multi-sitting (upper); smaller economical hand (lower)"},
    "f14r": {"speed": "compensating", "spacing": "wider",
             "notes": "slower, wider spacing, compensating for difficulty"},
    **{
        f"f{n:02}{s}": {"speed": "compensating", "spacing": "wider"}
        for n in range(14, 18) for s in ("r", "v")
        if f"f{n:02}{s}" != "f14r"
    },
}

# Folios on the irregular vellum stock (f14–f17 per CLIO-7)
_IRREGULAR_VELLUM: frozenset[str] = frozenset(
    f"f{n:02}{s}" for n in range(14, 18) for s in ("r", "v")
)

# All folio page IDs in gathering order (f01r through f17v)
_ALL_FOLIO_IDS: list[str] = [
    f"f{n:02}{s}" for n in range(1, 18) for s in ("r", "v")
]

# Page slot assignments: section_number → ordered list of folio IDs the section may fill.
# Section 4 is split: f06r-f06v (before Eckhart) and f08r-f13v (after Eckhart).
# Sections 1+2 share f01r; Sections 5+6 share f07v.
_SECTION_PAGE_SLOTS: dict[int, list[str]] = {
    1: ["f01r"],
    2: ["f01r", "f01v", "f02r", "f02v", "f03r", "f03v"],
    3: ["f04r", "f04v", "f05r", "f05v"],
    4: (
        ["f06r", "f06v"]
        + [f"f{n:02}{s}" for n in range(8, 14) for s in ("r", "v")]
    ),
    5: ["f07r", "f07v"],
    6: ["f07v"],
    7: [f"f{n:02}{s}" for n in range(14, 18) for s in ("r", "v")],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def structure(
    translated_sections: list[TranslatedSection],
    register_map: RegisterMap,
) -> list[FolioPage]:
    """Distribute translated text across folio pages.

    Returns FolioPage objects in gathering order (f01r → f17v).
    Only pages that receive at least one line are returned.
    """
    # Build the full page pool with static metadata
    pages: dict[str, FolioPage] = {}
    for fid in _ALL_FOLIO_IDS:
        folio_num = int(fid[1:3])
        pages[fid] = FolioPage(
            id=fid,
            recto_verso="recto" if fid.endswith("r") else "verso",
            gathering_position=folio_num,
            damage=_DAMAGE.get(fid),
            hand_notes=_HAND_NOTES.get(fid),
            vellum_stock="irregular" if fid in _IRREGULAR_VELLUM else "standard",
        )

    # Track how many lines have been placed on each page
    page_fill: dict[str, int] = {fid: 0 for fid in _ALL_FOLIO_IDS}

    # Process sections in ascending order
    section_map = {ts.section.number: ts for ts in translated_sections}
    for section_num in sorted(section_map):
        ts = section_map[section_num]
        slots = _SECTION_PAGE_SLOTS.get(section_num, [])
        if not slots:
            continue

        # Build all lines for this section from its passages
        all_lines: list[Line] = []
        for passage_idx, tp in enumerate(ts.passages):
            pr = register_map.entries.get((section_num, passage_idx))
            register = pr.tag if pr else tp.original.register
            all_lines.extend(_passage_to_lines(tp, register))

        # Place lines onto pages in slot order
        line_cursor = 0
        for fid in slots:
            if line_cursor >= len(all_lines):
                break
            budget = _LINE_BUDGETS.get(fid, _DEFAULT_LINE_BUDGET)
            available = budget - page_fill[fid]
            if available <= 0:
                continue

            chunk = all_lines[line_cursor: line_cursor + available]
            start_number = page_fill[fid] + 1
            for i, line in enumerate(chunk):
                line.number = start_number + i
            pages[fid].lines.extend(chunk)
            page_fill[fid] += len(chunk)
            line_cursor += len(chunk)

    # Return only pages with content, preserving gathering order
    return [pages[fid] for fid in _ALL_FOLIO_IDS if pages[fid].lines]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _passage_to_lines(tp: TranslatedPassage, register: str) -> list[Line]:
    """Word-wrap a translated passage into physical text lines (~60 chars each)."""
    text = tp.translated_text.strip()
    if not text:
        return []

    words = text.split()
    line_texts: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        wlen = len(word)
        if current and current_len + 1 + wlen > _CHARS_PER_LINE:
            line_texts.append(" ".join(current))
            current = [word]
            current_len = wlen
        else:
            if current:
                current_len += 1  # space
            current.append(word)
            current_len += wlen

    if current:
        line_texts.append(" ".join(current))

    return [
        Line(number=0, text=t, register=register)
        for t in line_texts
    ]
