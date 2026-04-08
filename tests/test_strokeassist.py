from __future__ import annotations

import numpy as np

from scribesim.annotate.strokeassist import _sample_peak_ink, propose_stroke_decomposition


def _white(height: int, width: int) -> np.ndarray:
    return np.full((height, width), 255, dtype=np.uint8)


def test_propose_stroke_decomposition_returns_pressure_scaffold_for_simple_glyph():
    glyph = _white(48, 24)
    glyph[4:44, 10:15] = 0

    proposal = propose_stroke_decomposition(glyph, "x")

    assert proposal["stroke_count"] >= 1
    assert proposal["primitive_count"] >= 1
    assert proposal["confidence"] > 0.0
    assert proposal["mode"] == "auto-minimized"
    assert proposal["candidate_counts"]
    assert proposal["image_fit"] > 0.0
    assert proposal["segments"]
    assert len(proposal["segments"][0]["pressure_curve"]) == 4
    assert proposal["segments"][0]["nib_angle_mode"] == "auto"
    assert len(proposal["segments"][0]["nib_angle_curve"]) == 4
    assert len(proposal["segments"][0]["nib_angle_confidence"]) == 4
    assert all(25.0 <= value <= 55.0 for value in proposal["segments"][0]["nib_angle_curve"])
    assert all(0.0 <= value <= 1.0 for value in proposal["segments"][0]["nib_angle_confidence"])
    assert proposal["segments"][0]["proposal_source"] == "stroke_assist"


def test_propose_stroke_decomposition_accepts_requested_stroke_count():
    glyph = _white(60, 40)
    glyph[6:54, 9:14] = 0
    glyph[22:28, 12:34] = 0

    proposal = propose_stroke_decomposition(glyph, "t", desired_stroke_count=2)

    assert proposal["mode"] == "requested-count"
    assert proposal["requested_stroke_count"] == 2
    assert proposal["template_stroke_count"] == 2
    assert proposal["stroke_count"] == 2
    assert proposal["selected_stroke_count"] == 2


def test_sample_peak_ink_returns_zero_for_fully_outside_window():
    ink = np.zeros((12, 12), dtype=np.float32)

    assert _sample_peak_ink(ink, (-40.0, -20.0), radius=2) == 0.0
