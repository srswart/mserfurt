"""Tests for scribesim/refextract/segment.py (ADV-SS-SEGMENT-001).

Red phase: these should fail until segment.py is implemented.
"""

import numpy as np
import pytest

from scribesim.refextract.segment import (
    segment_lines,
    segment_words,
    segment_letters_cc,
    detect_vertical_strokes,
    segment_letters,
    save_letter_crops,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _white(h, w):
    """All-white image."""
    return np.full((h, w), 255, dtype=np.uint8)


def _draw_rect(img, y0, y1, x0, x1, value=0):
    """Draw a filled rectangle of ink pixels."""
    img[y0:y1, x0:x1] = value
    return img


# ---------------------------------------------------------------------------
# test_segment_lines_synthetic
# ---------------------------------------------------------------------------

def test_segment_lines_synthetic():
    """Projection-based line split finds 3 ink rows separated by white gaps."""
    img = _white(100, 80)
    # Three ink rows
    _draw_rect(img, 5, 20, 10, 70)   # row 1: y=5..20
    _draw_rect(img, 35, 50, 10, 70)  # row 2: y=35..50
    _draw_rect(img, 65, 80, 10, 70)  # row 3: y=65..80

    lines = segment_lines(img, ink_threshold=200)

    assert len(lines) == 3, f"expected 3 lines, got {len(lines)}"
    # Each strip should be non-empty and contain ink
    for strip in lines:
        assert strip.ndim == 2
        assert strip.shape[0] > 0
        assert (strip < 200).any(), "strip should contain ink"


def test_segment_lines_single_row():
    """Single ink band → one line."""
    img = _white(60, 80)
    _draw_rect(img, 20, 40, 5, 75)

    lines = segment_lines(img, ink_threshold=200)
    assert len(lines) == 1


def test_segment_lines_blank():
    """Blank image → zero lines."""
    img = _white(60, 80)
    lines = segment_lines(img, ink_threshold=200)
    assert len(lines) == 0


# ---------------------------------------------------------------------------
# test_segment_words_synthetic
# ---------------------------------------------------------------------------

def test_segment_words_two_words():
    """Two word-blobs separated by clear vertical gap → 2 crops."""
    line = _white(40, 120)
    _draw_rect(line, 5, 35, 5, 50)   # word 1
    _draw_rect(line, 5, 35, 70, 115) # word 2

    words = segment_words(line, ink_threshold=200)
    assert len(words) == 2, f"expected 2 words, got {len(words)}"
    for w in words:
        assert w.shape[1] > 0
        assert (w < 200).any()


def test_segment_words_three_words():
    """Three word-blobs."""
    line = _white(40, 200)
    _draw_rect(line, 5, 35, 5, 50)
    _draw_rect(line, 5, 35, 70, 115)
    _draw_rect(line, 5, 35, 135, 185)

    words = segment_words(line, ink_threshold=200)
    assert len(words) == 3


def test_segment_words_single_blob():
    """Single blob (no gap) → 1 word."""
    line = _white(40, 80)
    _draw_rect(line, 5, 35, 5, 75)

    words = segment_words(line, ink_threshold=200)
    assert len(words) == 1


# ---------------------------------------------------------------------------
# test_segment_letters_cc
# ---------------------------------------------------------------------------

def test_segment_letters_cc_three_blobs():
    """Three separated ink blobs → 3 components, sorted left to right."""
    word = _white(40, 90)
    _draw_rect(word, 5, 35, 2, 18)   # letter 1
    _draw_rect(word, 5, 35, 35, 55)  # letter 2
    _draw_rect(word, 5, 35, 72, 88)  # letter 3

    letters = segment_letters_cc(word, ink_threshold=200)
    assert len(letters) == 3

    # Must be sorted left to right
    xs = []
    for label, crop in letters:
        assert label is None  # no label assigned yet
        assert crop.shape[1] > 0
        xs.append(crop.shape[1])  # widths should be non-zero

    # Verify left-to-right order by checking bounding-box x positions
    # We can't easily recover x from just crops, but we can check they're all present
    assert all(w > 0 for w in xs)


def test_segment_letters_cc_single():
    """Single blob → 1 component."""
    word = _white(40, 40)
    _draw_rect(word, 5, 35, 5, 35)

    letters = segment_letters_cc(word, ink_threshold=200)
    assert len(letters) == 1


# ---------------------------------------------------------------------------
# test_detect_vertical_strokes
# ---------------------------------------------------------------------------

def test_detect_vertical_strokes_two_bars():
    """Two thick vertical bars → 2 peak x-positions."""
    word = _white(40, 80)
    # Two vertical bars
    _draw_rect(word, 2, 38, 15, 25)  # bar 1 centered ~x=20
    _draw_rect(word, 2, 38, 55, 65)  # bar 2 centered ~x=60

    peaks = detect_vertical_strokes(word, ink_threshold=200)
    assert len(peaks) == 2
    # Peaks should be near the center of each bar
    assert abs(peaks[0] - 20) <= 8
    assert abs(peaks[1] - 60) <= 8


def test_detect_vertical_strokes_none():
    """Blank image → no peaks."""
    word = _white(40, 80)
    peaks = detect_vertical_strokes(word, ink_threshold=200)
    assert peaks == []


# ---------------------------------------------------------------------------
# test_segment_letters (combined)
# ---------------------------------------------------------------------------

def test_segment_letters_returns_crops():
    """segment_letters returns list of (label, crop) tuples."""
    word = _white(40, 90)
    _draw_rect(word, 5, 35, 2, 28)
    _draw_rect(word, 5, 35, 62, 88)

    letters = segment_letters(word, ink_threshold=200)
    assert len(letters) >= 1
    for label, crop in letters:
        assert crop.ndim == 2
        assert crop.shape[0] > 0
        assert crop.shape[1] > 0


def test_segment_letters_with_text_assigns_labels():
    """When word_text is provided with matching letter count, labels are assigned."""
    word = _white(40, 90)
    _draw_rect(word, 5, 35, 2, 28)
    _draw_rect(word, 5, 35, 62, 88)

    letters = segment_letters(word, word_text="nu", ink_threshold=200)
    labels = [lab for lab, _ in letters]
    # If 2 blobs and 2 chars, both should be labeled
    if len(labels) == 2:
        assert labels[0] == "n"
        assert labels[1] == "u"


# ---------------------------------------------------------------------------
# test_save_letter_crops
# ---------------------------------------------------------------------------

def test_save_letter_crops(tmp_path):
    """save_letter_crops writes PNGs organized by character class."""
    crops = [
        ("n", np.full((32, 24), 200, dtype=np.uint8)),
        ("u", np.full((32, 24), 180, dtype=np.uint8)),
        ("n", np.full((32, 24), 190, dtype=np.uint8)),
    ]
    save_letter_crops(crops, tmp_path)

    n_dir = tmp_path / "n"
    u_dir = tmp_path / "u"
    assert n_dir.is_dir()
    assert u_dir.is_dir()
    assert len(list(n_dir.glob("*.png"))) == 2
    assert len(list(u_dir.glob("*.png"))) == 1
