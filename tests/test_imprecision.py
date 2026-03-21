"""Unit tests for cumulative imprecision model — ADV-SS-IMPRECISION-001."""

from __future__ import annotations

import numpy as np
import pytest

from scribesim.hand.profile import HandProfile, FolioParams, LineParams
from scribesim.layout.geometry import PageGeometry
from scribesim.layout.positioned import PositionedGlyph, LineLayout, PageLayout
from scribesim.movement.imprecision import ruling_imprecision, apply_imprecision


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


def _make_layout(n_lines: int = 10) -> PageLayout:
    geom = _make_geometry()
    lines = []
    for i in range(n_lines):
        y = geom.margin_top + i * geom.ruling_pitch_mm
        glyphs = [
            PositionedGlyph(
                glyph_id="a", x_mm=25.0 + j * 3.0, y_mm=y,
                baseline_y_mm=y + 9.5, advance_w_mm=3.0,
            )
            for j in range(5)
        ]
        lines.append(LineLayout(line_index=i, y_mm=y, glyphs=glyphs))
    return PageLayout(folio_id="f01r", geometry=geom, lines=lines)


# ---------------------------------------------------------------------------
# TestRulingImprecision
# ---------------------------------------------------------------------------

class TestRulingImprecision:
    def test_produces_correct_count(self):
        profile = HandProfile()
        offsets = ruling_imprecision(10, profile, seed=42)
        assert len(offsets) == 10

    def test_offsets_nonzero(self):
        profile = HandProfile(
            folio=FolioParams(ruling_spacing_variance_mm=0.5),
            line=LineParams(line_spacing_variance_mm=0.3),
        )
        offsets = ruling_imprecision(10, profile, seed=42)
        assert any(abs(o) > 0.001 for o in offsets)

    def test_offsets_vary_between_lines(self):
        profile = HandProfile(
            folio=FolioParams(ruling_spacing_variance_mm=0.5),
            line=LineParams(line_spacing_variance_mm=0.3),
        )
        offsets = ruling_imprecision(10, profile, seed=42)
        unique = set(round(o, 6) for o in offsets)
        assert len(unique) > 1

    def test_offsets_within_reasonable_bounds(self):
        """Offsets should stay within a few mm — not diverge wildly."""
        profile = HandProfile(
            folio=FolioParams(ruling_spacing_variance_mm=0.5),
            line=LineParams(line_spacing_variance_mm=0.3),
        )
        offsets = ruling_imprecision(30, profile, seed=42)
        for o in offsets:
            assert abs(o) < 5.0  # reasonable for 30 lines

    def test_zero_variance_zero_offsets(self):
        profile = HandProfile(
            folio=FolioParams(ruling_spacing_variance_mm=0.0),
            line=LineParams(line_spacing_variance_mm=0.0),
        )
        offsets = ruling_imprecision(10, profile, seed=42)
        for o in offsets:
            assert abs(o) < 0.001

    def test_deterministic(self):
        profile = HandProfile()
        off1 = ruling_imprecision(10, profile, seed=42)
        off2 = ruling_imprecision(10, profile, seed=42)
        assert off1 == off2

    def test_different_seeds_different_offsets(self):
        profile = HandProfile()
        off1 = ruling_imprecision(10, profile, seed=1)
        off2 = ruling_imprecision(10, profile, seed=99)
        assert off1 != off2


# ---------------------------------------------------------------------------
# TestApplyImprecision
# ---------------------------------------------------------------------------

class TestApplyImprecision:
    def test_returns_page_layout(self):
        layout = _make_layout()
        profile = HandProfile()
        result = apply_imprecision(layout, profile, seed=42)
        assert isinstance(result, PageLayout)

    def test_changes_glyph_y_positions(self):
        layout = _make_layout()
        profile = HandProfile(
            folio=FolioParams(ruling_spacing_variance_mm=0.5),
            line=LineParams(line_spacing_variance_mm=0.3),
        )
        result = apply_imprecision(layout, profile, seed=42)
        diffs = []
        for li in range(len(layout.lines)):
            for gi in range(len(layout.lines[li].glyphs)):
                orig_y = layout.lines[li].glyphs[gi].baseline_y_mm
                new_y = result.lines[li].glyphs[gi].baseline_y_mm
                diffs.append(abs(orig_y - new_y))
        assert max(diffs) > 0.001

    def test_preserves_glyph_count(self):
        layout = _make_layout()
        profile = HandProfile()
        result = apply_imprecision(layout, profile, seed=42)
        for li in range(len(layout.lines)):
            assert len(result.lines[li].glyphs) == len(layout.lines[li].glyphs)

    def test_preserves_x_positions(self):
        layout = _make_layout()
        profile = HandProfile()
        result = apply_imprecision(layout, profile, seed=42)
        for li in range(len(layout.lines)):
            for gi in range(len(layout.lines[li].glyphs)):
                assert result.lines[li].glyphs[gi].x_mm == layout.lines[li].glyphs[gi].x_mm

    def test_all_glyphs_on_line_share_offset(self):
        """All glyphs on the same line should shift by the same dy."""
        layout = _make_layout()
        profile = HandProfile(
            folio=FolioParams(ruling_spacing_variance_mm=0.5),
            line=LineParams(line_spacing_variance_mm=0.3),
        )
        result = apply_imprecision(layout, profile, seed=42)
        for li in range(len(layout.lines)):
            shifts = [
                result.lines[li].glyphs[gi].baseline_y_mm - layout.lines[li].glyphs[gi].baseline_y_mm
                for gi in range(len(layout.lines[li].glyphs))
            ]
            # All shifts on the same line should be equal
            assert all(abs(s - shifts[0]) < 0.001 for s in shifts)

    def test_original_unchanged(self):
        layout = _make_layout()
        orig_y = layout.lines[0].glyphs[0].baseline_y_mm
        profile = HandProfile()
        apply_imprecision(layout, profile, seed=42)
        assert layout.lines[0].glyphs[0].baseline_y_mm == orig_y

    def test_empty_layout(self):
        geom = _make_geometry()
        layout = PageLayout(folio_id="f01r", geometry=geom, lines=[])
        profile = HandProfile()
        result = apply_imprecision(layout, profile, seed=42)
        assert len(result.lines) == 0
