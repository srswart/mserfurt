"""Folio structuring for the smaller private-manuscript format.

Consumes TranslatedSection + RegisterMap and produces an ordered list of
FolioPage objects matching the TD-001-A contract.

Current physical assumptions:
  - Standard folios (f01-f13) target a comfortable 22-24 lines/page
  - The final vellum stock begins at f14 and targets 16-18 lines/page
  - Water-damaged folios f04r-f05v carry reduced line budgets
  - Section 5 must not begin before f07r
  - Section 7 must not begin before f14r

Unlike the earlier fixed 17-folio plan, this allocator may continue beyond
f17v when the manuscript volume requires more space at the new density.
"""

from __future__ import annotations

from xl.models import FolioPage, Line, RegisterMap, TranslatedPassage, TranslatedSection

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CHARS_PER_LINE = 52

_STANDARD_LINE_BUDGET = 23
_FINAL_LINE_BUDGET = 17
_DEFAULT_LINE_BUDGET = _STANDARD_LINE_BUDGET

# Reduced line budgets for damaged pages on the smaller layout.
_LINE_BUDGETS: dict[str, int] = {
    "f04r": 16,
    "f04v": 13,
    "f05r": 18,
    "f05v": 18,
}

_SECTION_MIN_START: dict[int, str] = {
    1: "f01r",
    2: "f01r",
    5: "f07r",
    7: "f14r",
}

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

_HAND_NOTES: dict[str, dict] = {
    "f06r": {"pressure": "increased_lateral", "notes": "increased lateral pressure on downstrokes"},
    "f06v": {"pressure": "increased_lateral", "notes": "increased lateral pressure"},
    "f07r": {"ink_density": "variable_multi_sitting", "notes": "written across multiple sittings — ink density varies"},
    "f07v": {"ink_density": "variable_multi_sitting", "scale": "smaller_economical",
             "notes": "multi-sitting (upper); smaller economical hand (lower)"},
    "f14r": {"speed": "compensating", "spacing": "wider",
             "notes": "smaller irregular vellum; slower wider compensating hand"},
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def structure(
    translated_sections: list[TranslatedSection],
    register_map: RegisterMap,
) -> list[FolioPage]:
    """Distribute translated text across sequential folios.

    Pages are created lazily as content lands on them, preserving gathering
    order and allowing the manuscript to extend beyond the old 17-folio cap.
    """
    pages: dict[str, FolioPage] = {}
    page_fill: dict[str, int] = {}
    page_order: list[str] = []

    def ensure_page(fid: str) -> FolioPage:
        if fid not in pages:
            pages[fid] = _make_page(fid)
            page_fill[fid] = 0
            page_order.append(fid)
        return pages[fid]

    cursor = "f01r"
    section_map = {ts.section.number: ts for ts in translated_sections}

    for section_num in sorted(section_map):
        ts = section_map[section_num]

        all_lines: list[Line] = []
        for passage_idx, tp in enumerate(ts.passages):
            pr = register_map.entries.get((section_num, passage_idx))
            register = pr.tag if pr else tp.original.register
            all_lines.extend(_passage_to_lines(tp, register))

        if not all_lines:
            continue

        min_start = _SECTION_MIN_START.get(section_num)
        if min_start and _folio_rank(cursor) < _folio_rank(min_start):
            cursor = min_start

        line_cursor = 0
        while line_cursor < len(all_lines):
            page = ensure_page(cursor)
            budget = _budget_for(cursor)
            available = budget - page_fill[cursor]
            if available <= 0:
                cursor = _next_page_id(cursor)
                continue

            chunk = all_lines[line_cursor: line_cursor + available]
            start_number = page_fill[cursor] + 1
            for i, line in enumerate(chunk):
                line.number = start_number + i
            page.lines.extend(chunk)
            page_fill[cursor] += len(chunk)
            line_cursor += len(chunk)

            if line_cursor < len(all_lines):
                cursor = _next_page_id(cursor)

    return [pages[fid] for fid in page_order if pages[fid].lines]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _folio_number(fid: str) -> int:
    stripped = fid.lstrip("f")
    digits = []
    for ch in stripped:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    return int("".join(digits)) if digits else 1


def _folio_rank(fid: str) -> int:
    num = _folio_number(fid)
    side = 0 if fid.endswith("r") else 1
    return num * 2 + side


def _next_page_id(fid: str) -> str:
    num = _folio_number(fid)
    if fid.endswith("r"):
        return f"f{num:02d}v"
    return f"f{num + 1:02d}r"


def _is_final_stock(fid: str) -> bool:
    return _folio_number(fid) >= 14


def _budget_for(fid: str) -> int:
    if fid in _LINE_BUDGETS:
        return _LINE_BUDGETS[fid]
    return _FINAL_LINE_BUDGET if _is_final_stock(fid) else _STANDARD_LINE_BUDGET


def _hand_notes_for(fid: str) -> dict | None:
    if fid in _HAND_NOTES:
        return _HAND_NOTES[fid]
    if _is_final_stock(fid):
        return {"speed": "compensating", "spacing": "wider"}
    return None


def _make_page(fid: str) -> FolioPage:
    folio_num = _folio_number(fid)
    return FolioPage(
        id=fid,
        recto_verso="recto" if fid.endswith("r") else "verso",
        gathering_position=folio_num,
        damage=_DAMAGE.get(fid),
        hand_notes=_hand_notes_for(fid),
        vellum_stock="irregular" if _is_final_stock(fid) else "standard",
    )


def _passage_to_lines(tp: TranslatedPassage, register: str) -> list[Line]:
    """Word-wrap a translated passage into comfortable physical text lines."""
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
                current_len += 1
            current.append(word)
            current_len += wlen

    if current:
        line_texts.append(" ".join(current))

    return [Line(number=0, text=t, register=register) for t in line_texts]
