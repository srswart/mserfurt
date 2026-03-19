"""CLIO-7 apparatus overlay — attach confidence scores and lacuna markers to FolioPage lines.

Transforms the structurally complete FolioPage objects (from the folio stage) into
fully annotated folios by:
  1. Assigning per-line confidence scores derived from the page's damage metadata.
  2. Detecting lacuna markers ([—]) in line text and adding lacuna annotations.

This stage is idempotent: re-running annotate() on already-annotated pages does not
add duplicate annotations.
"""

from __future__ import annotations

import re

from xl.models import Annotation, FolioPage

# ---------------------------------------------------------------------------
# Confidence score table
# ---------------------------------------------------------------------------

# Base confidence for a page with no damage
_CLEAN_CONFIDENCE: float = 0.97

# Adjustments by damage extent
_EXTENT_ADJUSTMENT: dict[str, float] = {
    "partial": -0.27,   # e.g. f04r, f05r: 0.97 - 0.27 = 0.70
    "severe": -0.55,    # e.g. f04v: 0.97 - 0.55 = 0.42
    "total": -0.97,     # fully destroyed
}

# Additional penalty when a missing corner is present
_CORNER_PENALTY: float = -0.05

# Confidence assigned to lines containing a lacuna marker ([—])
_LACUNA_CONFIDENCE: float = 0.0

# Regex for lacuna markers in translated text
_LACUNA_RE = re.compile(r"\[—\]")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def annotate(pages: list[FolioPage]) -> list[FolioPage]:
    """Annotate each FolioPage line with confidence scores and lacuna markers.

    Mutates the pages in place and returns them.
    """
    for page in pages:
        base_confidence = _page_confidence(page)
        for line in page.lines:
            _annotate_line(line, base_confidence)
    return pages


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _page_confidence(page: FolioPage) -> float:
    """Compute the base confidence score for all lines on a page."""
    if not page.damage:
        return _CLEAN_CONFIDENCE

    extent = page.damage.get("extent", "")
    confidence = _CLEAN_CONFIDENCE + _EXTENT_ADJUSTMENT.get(extent, 0.0)

    if page.damage.get("corner"):
        confidence += _CORNER_PENALTY

    return max(0.0, confidence)


def _annotate_line(line, base_confidence: float) -> None:
    """Add confidence and lacuna annotations to a single line (idempotent)."""
    # Idempotency: skip if a confidence annotation is already present
    already_annotated = any(a.type == "confidence" for a in line.annotations)
    if already_annotated:
        return

    has_lacuna = bool(_LACUNA_RE.search(line.text))
    score = _LACUNA_CONFIDENCE if has_lacuna else base_confidence

    if has_lacuna:
        line.annotations.append(Annotation(type="lacuna"))

    line.annotations.append(Annotation(type="confidence", detail={"score": score}))
