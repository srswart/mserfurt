"""Tests for the diagnostic rendering module — ADV-SS-DIAG-001.

These tests verify that render_single_glyph, render_word_diagnostic, and
render_glyph_sheet return meaningful output: correct types, non-trivial
shapes, and actual ink (pixels darker than the parchment background).
"""

from __future__ import annotations

import numpy as np
import pytest

from scribesim.render.diagnostic import (
    render_single_glyph,
    render_word_diagnostic,
    render_glyph_sheet,
)


# ---------------------------------------------------------------------------
# Parchment background threshold
# ---------------------------------------------------------------------------

_PARCHMENT_BRIGHTNESS = 240  # pixels brighter than this are background
_INK_THRESHOLD = 200          # pixels darker than this count as ink


def _has_ink(arr: np.ndarray, threshold: int = _INK_THRESHOLD) -> bool:
    """Return True if any pixel in the RGB array is darker than threshold."""
    return bool(np.any(arr.min(axis=2) < threshold))


def _ink_fraction(arr: np.ndarray, threshold: int = _INK_THRESHOLD) -> float:
    """Fraction of pixels darker than threshold."""
    dark = np.sum(arr.min(axis=2) < threshold)
    return dark / arr.shape[0] / arr.shape[1]


# ---------------------------------------------------------------------------
# render_single_glyph — shape and type
# ---------------------------------------------------------------------------

def test_render_single_glyph_returns_ndarray():
    img = render_single_glyph("n", dpi=100.0)
    assert isinstance(img, np.ndarray)


def test_render_single_glyph_is_rgb():
    img = render_single_glyph("n", dpi=100.0)
    assert img.ndim == 3
    assert img.shape[2] == 3


def test_render_single_glyph_nonzero_dimensions():
    img = render_single_glyph("n", dpi=100.0)
    assert img.shape[0] > 0
    assert img.shape[1] > 0


def test_render_single_glyph_has_ink():
    img = render_single_glyph("n", dpi=100.0)
    assert _has_ink(img), "render_single_glyph('n') produced no ink pixels — renderer may be broken"


def test_render_single_glyph_ink_not_excessive():
    # Should not fill more than 30% of the canvas with ink
    img = render_single_glyph("n", dpi=100.0)
    assert _ink_fraction(img) < 0.30, "Too much ink — glyph may be rendering as a solid blob"


# ---------------------------------------------------------------------------
# render_single_glyph — several glyphs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("glyph_id", ["a", "b", "m", "i", "o", "d", "h"])
def test_render_single_glyph_common_letters_have_ink(glyph_id):
    img = render_single_glyph(glyph_id, dpi=100.0)
    assert _has_ink(img), f"render_single_glyph({glyph_id!r}) produced no ink"


@pytest.mark.parametrize("glyph_id", ["long_s", "round_s", "esszett", "a_umlaut"])
def test_render_single_glyph_special_forms_have_ink(glyph_id):
    img = render_single_glyph(glyph_id, dpi=100.0)
    assert _has_ink(img), f"render_single_glyph({glyph_id!r}) produced no ink"


# ---------------------------------------------------------------------------
# render_single_glyph — error handling
# ---------------------------------------------------------------------------

def test_render_single_glyph_raises_keyerror_for_unknown():
    with pytest.raises(KeyError):
        render_single_glyph("MISSING_GLYPH_XYZ", dpi=100.0)


# ---------------------------------------------------------------------------
# render_single_glyph — DPI affects output size
# ---------------------------------------------------------------------------

def test_render_single_glyph_higher_dpi_produces_larger_image():
    img_lo = render_single_glyph("n", dpi=75.0)
    img_hi = render_single_glyph("n", dpi=150.0)
    assert img_hi.shape[0] > img_lo.shape[0] or img_hi.shape[1] > img_lo.shape[1]


# ---------------------------------------------------------------------------
# render_word_diagnostic
# ---------------------------------------------------------------------------

def test_render_word_diagnostic_returns_ndarray():
    img = render_word_diagnostic("und", dpi=100.0)
    assert isinstance(img, np.ndarray)


def test_render_word_diagnostic_is_rgb():
    img = render_word_diagnostic("und", dpi=100.0)
    assert img.ndim == 3
    assert img.shape[2] == 3


def test_render_word_diagnostic_has_ink():
    img = render_word_diagnostic("und", dpi=100.0)
    assert _has_ink(img), "render_word_diagnostic('und') produced no ink pixels"


def test_render_word_diagnostic_wider_than_single_glyph():
    single = render_single_glyph("u", dpi=100.0)
    word = render_word_diagnostic("und", dpi=100.0)
    assert word.shape[1] > single.shape[1]


def test_render_word_diagnostic_rejects_long_text():
    import pytest
    with pytest.raises(ValueError):
        render_word_diagnostic("a" * 21, dpi=100.0)


# ---------------------------------------------------------------------------
# render_glyph_sheet
# ---------------------------------------------------------------------------

def test_render_glyph_sheet_returns_ndarray():
    img = render_glyph_sheet(dpi=72.0)
    assert isinstance(img, np.ndarray)


def test_render_glyph_sheet_is_rgb():
    img = render_glyph_sheet(dpi=72.0)
    assert img.ndim == 3
    assert img.shape[2] == 3


def test_render_glyph_sheet_has_ink():
    img = render_glyph_sheet(dpi=72.0)
    assert _has_ink(img), "glyph_sheet produced no ink — all cells may be blank"


def test_render_glyph_sheet_reasonable_dimensions():
    from scribesim.glyphs.catalog import GLYPH_CATALOG
    img = render_glyph_sheet(dpi=72.0)
    n = len(GLYPH_CATALOG)
    cols = 10
    rows = (n + cols - 1) // cols
    # Sheet height should be at least rows * some_minimum_cell_height
    assert img.shape[0] >= rows * 10
    assert img.shape[1] >= cols * 10
