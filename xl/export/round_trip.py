"""Inverse of build_folio_dict — reconstruct a FolioPage from its JSON dict.

Used by round-trip tests and by any downstream consumer that needs to
re-ingest exported folio JSON without going through the full pipeline.
"""

from __future__ import annotations

from xl.models import Annotation, FolioPage, Line


def parse_folio_dict(d: dict) -> FolioPage:
    """Deserialize a TD-001-A folio dict into a FolioPage.

    The ``metadata`` key is computed and ignored — it is not stored on
    FolioPage and will be re-derived by build_folio_dict on the next export.
    """
    lines = [_parse_line(ld) for ld in d.get("lines", [])]

    return FolioPage(
        id=d["id"],
        recto_verso=d["recto_verso"],
        gathering_position=d["gathering_position"],
        lines=lines,
        damage=d.get("damage"),
        hand_notes=d.get("hand_notes"),
        section_breaks=d.get("section_breaks", []),
        vellum_stock=d.get("vellum_stock", "standard"),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_line(d: dict) -> Line:
    annotations = [_parse_annotation(a) for a in d.get("annotations", [])]
    return Line(
        number=d["number"],
        text=d["text"],
        register=d["register"],
        english=d.get("english"),
        annotations=annotations,
    )


def _parse_annotation(d: dict) -> Annotation:
    span_d = d.get("span")
    span: tuple[int, int] | None = None
    if span_d is not None:
        span = (span_d["char_start"], span_d["char_end"])
    return Annotation(
        type=d["type"],
        span=span,
        detail=d.get("detail", {}),
    )
