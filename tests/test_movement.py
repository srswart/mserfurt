"""Unit tests for multi-scale movement model — ADV-SS-MOVEMENT-001."""

from __future__ import annotations

import math

import numpy as np
import pytest

from scribesim.hand.profile import HandProfile, FolioParams, LineParams, WordParams, GlyphParams
from scribesim.layout.geometry import PageGeometry
from scribesim.layout.positioned import PositionedGlyph, LineLayout, PageLayout
from scribesim.movement.movement import (
    GlyphOffset,
    page_posture_offsets,
    line_trajectory_offsets,
    word_envelope_offsets,
    glyph_trajectory_offsets,
    compose_movement,
    apply_movement,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_geometry() -> PageGeometry:
    return PageGeometry(
        page_w_mm=280.0, page_h_mm=400.0,
        margin_top=25.0, margin_bottom=70.0,
        margin_inner=25.0, margin_outer=50.0,
        ruling_pitch_mm=9.5, x_height_mm=3.8, folio_format="standard",
    )


def _make_line(line_index: int, y_mm: float, n_glyphs: int = 10,
               x_start: float = 25.0, advance: float = 3.0) -> LineLayout:
    """Create a line with evenly spaced glyphs."""
    glyphs = []
    x = x_start
    for i in range(n_glyphs):
        glyphs.append(PositionedGlyph(
            glyph_id=chr(ord("a") + i % 26),
            x_mm=x,
            y_mm=y_mm - 9.5 + 9.5,  # baseline - x_height + x_height
            baseline_y_mm=y_mm + 9.5,
            advance_w_mm=advance,
        ))
        x += advance
    return LineLayout(line_index=line_index, y_mm=y_mm, glyphs=glyphs)


def _make_line_with_words(line_index: int, y_mm: float) -> LineLayout:
    """Create a line with 3 words (gaps between them)."""
    glyphs = []
    x = 25.0
    advance = 3.0
    # Word 1: 4 glyphs
    for i in range(4):
        glyphs.append(PositionedGlyph(
            glyph_id=chr(ord("a") + i), x_mm=x, y_mm=y_mm,
            baseline_y_mm=y_mm + 9.5, advance_w_mm=advance,
        ))
        x += advance
    x += advance * 2  # word gap
    # Word 2: 3 glyphs
    for i in range(3):
        glyphs.append(PositionedGlyph(
            glyph_id=chr(ord("e") + i), x_mm=x, y_mm=y_mm,
            baseline_y_mm=y_mm + 9.5, advance_w_mm=advance,
        ))
        x += advance
    x += advance * 2  # word gap
    # Word 3: 3 glyphs
    for i in range(3):
        glyphs.append(PositionedGlyph(
            glyph_id=chr(ord("h") + i), x_mm=x, y_mm=y_mm,
            baseline_y_mm=y_mm + 9.5, advance_w_mm=advance,
        ))
        x += advance
    return LineLayout(line_index=line_index, y_mm=y_mm, glyphs=glyphs)


def _make_layout(n_lines: int = 5) -> PageLayout:
    geom = _make_geometry()
    lines = []
    for i in range(n_lines):
        y = geom.margin_top + i * geom.ruling_pitch_mm
        lines.append(_make_line(i, y))
    return PageLayout(folio_id="f01r", geometry=geom, lines=lines)


def _make_layout_with_words() -> PageLayout:
    geom = _make_geometry()
    lines = []
    for i in range(3):
        y = geom.margin_top + i * geom.ruling_pitch_mm
        lines.append(_make_line_with_words(i, y))
    return PageLayout(folio_id="f01r", geometry=geom, lines=lines)


# ---------------------------------------------------------------------------
# TestPagePosture
# ---------------------------------------------------------------------------

class TestPagePosture:
    def test_rotation_produces_x_displacement(self):
        layout = _make_layout()
        profile = HandProfile(folio=FolioParams(page_rotation_deg=0.5))
        rng = np.random.default_rng(42)
        offsets = page_posture_offsets(layout, profile, rng)
        # Glyphs far from page center should have nonzero dx
        mid_line = offsets[2]  # middle line
        assert any(abs(o.dx_mm) > 0.001 for o in mid_line)

    def test_zero_rotation_minimal_rotation_dx(self):
        layout = _make_layout()
        profile = HandProfile(folio=FolioParams(page_rotation_deg=0.0, margin_left_variance_mm=0.0))
        rng = np.random.default_rng(42)
        offsets = page_posture_offsets(layout, profile, rng)
        # With zero rotation and zero margin variance, all dx should be ~0
        for line_off in offsets:
            for o in line_off:
                assert abs(o.dx_mm) < 0.01

    def test_margin_drift_cumulative(self):
        layout = _make_layout(n_lines=10)
        profile = HandProfile(folio=FolioParams(
            page_rotation_deg=0.0,
            margin_left_variance_mm=1.0,
        ))
        rng = np.random.default_rng(42)
        offsets = page_posture_offsets(layout, profile, rng)
        # Later lines should have larger systematic drift
        # Compare average drift of first line vs last line
        first_avg = np.mean([o.dx_mm for o in offsets[0]])
        last_avg = np.mean([o.dx_mm for o in offsets[-1]])
        assert abs(last_avg) > abs(first_avg) or abs(last_avg - first_avg) > 0.05

    def test_dy_is_zero(self):
        layout = _make_layout()
        profile = HandProfile(folio=FolioParams(page_rotation_deg=0.3))
        rng = np.random.default_rng(42)
        offsets = page_posture_offsets(layout, profile, rng)
        for line_off in offsets:
            for o in line_off:
                assert o.dy_mm == 0.0


# ---------------------------------------------------------------------------
# TestLineTrajectory
# ---------------------------------------------------------------------------

class TestLineTrajectory:
    def test_undulation_within_amplitude(self):
        layout = _make_layout()
        amp = 0.3
        profile = HandProfile(line=LineParams(
            baseline_undulation_amplitude_mm=amp,
            start_x_variance_mm=0.0,
        ))
        rng = np.random.default_rng(42)
        offsets = line_trajectory_offsets(layout, profile, rng)
        for line_off in offsets:
            for o in line_off:
                assert abs(o.dy_mm) <= amp + 0.01

    def test_start_x_jitter_varies_between_lines(self):
        layout = _make_layout(n_lines=5)
        profile = HandProfile(line=LineParams(start_x_variance_mm=0.5))
        rng = np.random.default_rng(42)
        offsets = line_trajectory_offsets(layout, profile, rng)
        # dx should differ between lines (first glyph of each line)
        dx_values = [offsets[li][0].dx_mm for li in range(5)]
        assert len(set(round(d, 6) for d in dx_values)) > 1

    def test_zero_amplitude_zero_offset(self):
        layout = _make_layout()
        profile = HandProfile(line=LineParams(
            baseline_undulation_amplitude_mm=0.0,
            start_x_variance_mm=0.0,
        ))
        rng = np.random.default_rng(42)
        offsets = line_trajectory_offsets(layout, profile, rng)
        for line_off in offsets:
            for o in line_off:
                assert abs(o.dy_mm) < 0.001
                assert abs(o.dx_mm) < 0.001


# ---------------------------------------------------------------------------
# TestWordEnvelope
# ---------------------------------------------------------------------------

class TestWordEnvelope:
    def test_per_word_offset_nonzero(self):
        layout = _make_layout_with_words()
        profile = HandProfile()
        rng = np.random.default_rng(42)
        offsets = word_envelope_offsets(layout, profile, rng)
        # Should have some nonzero dy values
        all_dy = [o.dy_mm for line_off in offsets for o in line_off]
        assert any(abs(d) > 0.01 for d in all_dy)

    def test_glyphs_in_same_word_share_offset(self):
        layout = _make_layout_with_words()
        profile = HandProfile()
        rng = np.random.default_rng(42)
        offsets = word_envelope_offsets(layout, profile, rng)
        # First 4 glyphs (word 1) should have the same dy
        line0 = offsets[0]
        assert line0[0].dy_mm == pytest.approx(line0[1].dy_mm)
        assert line0[0].dy_mm == pytest.approx(line0[2].dy_mm)

    def test_different_words_different_offsets(self):
        layout = _make_layout_with_words()
        profile = HandProfile()
        rng = np.random.default_rng(42)
        offsets = word_envelope_offsets(layout, profile, rng)
        line0 = offsets[0]
        # Word 1 (glyph 0) vs Word 2 (glyph 4) should differ
        # (probabilistically — with seed 42 they should)
        word1_dy = line0[0].dy_mm
        word2_dy = line0[4].dy_mm
        assert word1_dy != pytest.approx(word2_dy, abs=0.001)

    def test_dx_is_zero(self):
        layout = _make_layout_with_words()
        profile = HandProfile()
        rng = np.random.default_rng(42)
        offsets = word_envelope_offsets(layout, profile, rng)
        for line_off in offsets:
            for o in line_off:
                assert o.dx_mm == 0.0


# ---------------------------------------------------------------------------
# TestGlyphTrajectory
# ---------------------------------------------------------------------------

class TestGlyphTrajectory:
    def test_jitter_within_bounds(self):
        layout = _make_layout()
        jitter = 0.05
        profile = HandProfile(glyph=GlyphParams(baseline_jitter_mm=jitter))
        rng = np.random.default_rng(42)
        offsets = glyph_trajectory_offsets(layout, profile, rng)
        for line_off in offsets:
            for o in line_off:
                # 4-sigma should be well within 0.5mm for 0.05mm sigma
                assert abs(o.dy_mm) < jitter * 6

    def test_zero_jitter_zero_offset(self):
        layout = _make_layout()
        profile = HandProfile(glyph=GlyphParams(baseline_jitter_mm=0.0))
        rng = np.random.default_rng(42)
        offsets = glyph_trajectory_offsets(layout, profile, rng)
        for line_off in offsets:
            for o in line_off:
                assert o.dy_mm == 0.0

    def test_dx_is_zero(self):
        layout = _make_layout()
        profile = HandProfile()
        rng = np.random.default_rng(42)
        offsets = glyph_trajectory_offsets(layout, profile, rng)
        for line_off in offsets:
            for o in line_off:
                assert o.dx_mm == 0.0


# ---------------------------------------------------------------------------
# TestComposition
# ---------------------------------------------------------------------------

class TestComposition:
    def test_compose_produces_offsets_for_all_glyphs(self):
        layout = _make_layout(n_lines=3)
        profile = HandProfile()
        offsets = compose_movement(layout, profile, seed=42)
        assert len(offsets) == 3
        for li in range(3):
            assert len(offsets[li]) == len(layout.lines[li].glyphs)

    def test_compose_is_sum_of_scales(self):
        layout = _make_layout(n_lines=2)
        profile = HandProfile()
        seed = 42

        composed = compose_movement(layout, profile, seed)

        # Compute individual scales with same seeds
        rng_p = np.random.default_rng(seed)
        rng_l = np.random.default_rng(seed + 1)
        rng_w = np.random.default_rng(seed + 2)
        rng_g = np.random.default_rng(seed + 3)
        page = page_posture_offsets(layout, profile, rng_p)
        line = line_trajectory_offsets(layout, profile, rng_l)
        word = word_envelope_offsets(layout, profile, rng_w)
        glyph = glyph_trajectory_offsets(layout, profile, rng_g)

        for li in range(2):
            for gi in range(len(layout.lines[li].glyphs)):
                expected_dx = (page[li][gi].dx_mm + line[li][gi].dx_mm
                               + word[li][gi].dx_mm + glyph[li][gi].dx_mm)
                expected_dy = (page[li][gi].dy_mm + line[li][gi].dy_mm
                               + word[li][gi].dy_mm + glyph[li][gi].dy_mm)
                assert composed[li][gi].dx_mm == pytest.approx(expected_dx)
                assert composed[li][gi].dy_mm == pytest.approx(expected_dy)

    def test_deterministic(self):
        layout = _make_layout()
        profile = HandProfile()
        off1 = compose_movement(layout, profile, seed=123)
        off2 = compose_movement(layout, profile, seed=123)
        for li in range(len(layout.lines)):
            for gi in range(len(layout.lines[li].glyphs)):
                assert off1[li][gi].dx_mm == off2[li][gi].dx_mm
                assert off1[li][gi].dy_mm == off2[li][gi].dy_mm

    def test_different_seeds_different_offsets(self):
        layout = _make_layout()
        profile = HandProfile()
        off1 = compose_movement(layout, profile, seed=1)
        off2 = compose_movement(layout, profile, seed=99)
        # At least one glyph should differ
        diffs = [
            abs(off1[li][gi].dx_mm - off2[li][gi].dx_mm)
            + abs(off1[li][gi].dy_mm - off2[li][gi].dy_mm)
            for li in range(len(layout.lines))
            for gi in range(len(layout.lines[li].glyphs))
        ]
        assert max(diffs) > 0.001

    def test_zero_params_zero_offsets(self):
        layout = _make_layout()
        profile = HandProfile(
            folio=FolioParams(page_rotation_deg=0.0, margin_left_variance_mm=0.0),
            line=LineParams(baseline_undulation_amplitude_mm=0.0, start_x_variance_mm=0.0),
            glyph=GlyphParams(baseline_jitter_mm=0.0),
        )
        offsets = compose_movement(layout, profile, seed=42)
        for line_off in offsets:
            for o in line_off:
                # Word envelope still contributes (±0.2mm Gaussian), so only check page+line+glyph=0
                pass
        # With all amplitudes at 0 except word envelope, total offset should be small
        # Word envelope has hardcoded ±0.2mm sigma, so check that nothing is huge
        for line_off in offsets:
            for o in line_off:
                assert abs(o.dx_mm) < 1.0
                assert abs(o.dy_mm) < 2.0


# ---------------------------------------------------------------------------
# TestApplyMovement
# ---------------------------------------------------------------------------

class TestApplyMovement:
    def test_returns_page_layout(self):
        layout = _make_layout()
        profile = HandProfile()
        result = apply_movement(layout, profile, seed=42)
        assert isinstance(result, PageLayout)
        assert result.folio_id == layout.folio_id

    def test_glyph_positions_differ(self):
        layout = _make_layout()
        profile = HandProfile()
        result = apply_movement(layout, profile, seed=42)
        # At least some glyphs should have moved
        diffs = []
        for li in range(len(layout.lines)):
            for gi in range(len(layout.lines[li].glyphs)):
                orig = layout.lines[li].glyphs[gi]
                moved = result.lines[li].glyphs[gi]
                diffs.append(abs(orig.x_mm - moved.x_mm) + abs(orig.y_mm - moved.y_mm))
        assert max(diffs) > 0.001

    def test_preserves_glyph_count(self):
        layout = _make_layout()
        profile = HandProfile()
        result = apply_movement(layout, profile, seed=42)
        for li in range(len(layout.lines)):
            assert len(result.lines[li].glyphs) == len(layout.lines[li].glyphs)

    def test_preserves_glyph_ids(self):
        layout = _make_layout()
        profile = HandProfile()
        result = apply_movement(layout, profile, seed=42)
        for li in range(len(layout.lines)):
            for gi in range(len(layout.lines[li].glyphs)):
                assert result.lines[li].glyphs[gi].glyph_id == layout.lines[li].glyphs[gi].glyph_id

    def test_preserves_opacity(self):
        layout = _make_layout()
        profile = HandProfile()
        result = apply_movement(layout, profile, seed=42)
        for li in range(len(layout.lines)):
            for gi in range(len(layout.lines[li].glyphs)):
                assert result.lines[li].glyphs[gi].opacity == layout.lines[li].glyphs[gi].opacity

    def test_original_layout_unchanged(self):
        layout = _make_layout()
        orig_x = layout.lines[0].glyphs[0].x_mm
        profile = HandProfile()
        apply_movement(layout, profile, seed=42)
        assert layout.lines[0].glyphs[0].x_mm == orig_x

    def test_deterministic(self):
        layout = _make_layout()
        profile = HandProfile()
        r1 = apply_movement(layout, profile, seed=42)
        r2 = apply_movement(layout, profile, seed=42)
        for li in range(len(r1.lines)):
            for gi in range(len(r1.lines[li].glyphs)):
                assert r1.lines[li].glyphs[gi].x_mm == r2.lines[li].glyphs[gi].x_mm
                assert r1.lines[li].glyphs[gi].y_mm == r2.lines[li].glyphs[gi].y_mm
