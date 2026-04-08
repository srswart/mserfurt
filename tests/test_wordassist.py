from __future__ import annotations

import numpy as np

from scribesim.annotate.wordassist import preprocess_transcript, propose_word_segmentation, score_word_segmentation


def _white(height: int, width: int) -> np.ndarray:
    return np.full((height, width), 255, dtype=np.uint8)


def _draw_rect(img: np.ndarray, y0: int, y1: int, x0: int, x1: int, value: int = 0) -> np.ndarray:
    img[y0:y1, x0:x1] = value
    return img


def test_preprocess_transcript_preserves_known_ligatures():
    assert preprocess_transcript("chtz") == ["ch", "tz"]
    assert preprocess_transcript("  ſcht  ") == ["ſch", "t"]


def test_propose_word_segmentation_bootstrap_finds_gap_between_minims():
    word = _white(48, 34)
    _draw_rect(word, 4, 44, 3, 9)
    _draw_rect(word, 4, 44, 20, 26)

    proposal = propose_word_segmentation(word, "ii")

    assert proposal["units"] == ["i", "i"]
    assert len(proposal["segments"]) == 2
    assert len(proposal["boundaries"]) == 3
    assert 10 <= proposal["boundaries"][1] <= 19
    assert proposal["mode"] in {"bootstrap", "mixed", "fallback"}


def test_score_word_segmentation_reports_exact_guide_usage():
    glyph = _white(48, 12)
    _draw_rect(glyph, 4, 44, 3, 8)

    proposal = score_word_segmentation(
        glyph,
        ["i"],
        [0, glyph.shape[1]],
        template_bank={"i": glyph},
    )

    assert proposal["segments"][0]["guide_available"] is True
    assert proposal["segments"][0]["template_score"] is not None
    assert proposal["mode"] == "guide-assisted"
