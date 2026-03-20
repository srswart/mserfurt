"""Unit tests for scribesim glyph catalog — ADV-SS-GLYPHS-001.

RED phase: GLYPH_CATALOG and lookup() do not exist yet (catalog.py stub only).
"""

from __future__ import annotations

import pytest

from scribesim.glyphs.strokes import BezierStroke
from scribesim.glyphs.glyph import Glyph


# ---------------------------------------------------------------------------
# TestBezierStroke — dataclass contracts
# ---------------------------------------------------------------------------

class TestBezierStroke:
    _FOUR = (
        (0.0, 0.0), (0.1, 0.5), (0.3, 0.5), (0.4, 0.0)
    )

    def test_valid_construction(self):
        s = BezierStroke(control_points=self._FOUR, stroke_name="body")
        assert s.stroke_name == "body"

    def test_requires_four_control_points(self):
        with pytest.raises(ValueError, match="4 control points"):
            BezierStroke(control_points=((0.0, 0.0), (1.0, 1.0)))

    def test_pressure_profile_default_has_four_values(self):
        s = BezierStroke(control_points=self._FOUR)
        assert len(s.pressure_profile) == 4

    def test_pressure_profile_values_in_range(self):
        s = BezierStroke(control_points=self._FOUR,
                         pressure_profile=(0.0, 0.5, 1.0))
        assert all(0.0 <= v <= 1.0 for v in s.pressure_profile)

    def test_pressure_profile_out_of_range_raises(self):
        with pytest.raises(ValueError, match="pressure_profile"):
            BezierStroke(control_points=self._FOUR,
                         pressure_profile=(0.0, 1.5))

    def test_pressure_profile_too_short_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            BezierStroke(control_points=self._FOUR,
                         pressure_profile=(0.5,))

    def test_length_approx_nonzero(self):
        s = BezierStroke(control_points=self._FOUR)
        assert s.length_approx() > 0.0

    def test_immutable(self):
        s = BezierStroke(control_points=self._FOUR)
        with pytest.raises(Exception):
            s.stroke_name = "x"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TestGlyph — dataclass contracts
# ---------------------------------------------------------------------------

_STROKE = BezierStroke(
    control_points=((0.0, 0.0), (0.1, 0.5), (0.3, 0.5), (0.4, 0.0)),
    stroke_name="body",
)


class TestGlyph:
    def test_valid_construction(self):
        g = Glyph(id="a", unicode_codepoint=0x61,
                  strokes=(_STROKE,), advance_width=0.6)
        assert g.id == "a"
        assert g.advance_width == pytest.approx(0.6)

    def test_zero_advance_width_raises(self):
        with pytest.raises(ValueError, match="advance_width"):
            Glyph(id="a", unicode_codepoint=0x61,
                  strokes=(_STROKE,), advance_width=0.0)

    def test_empty_strokes_raises(self):
        with pytest.raises(ValueError, match="strokes"):
            Glyph(id="a", unicode_codepoint=0x61,
                  strokes=(), advance_width=0.5)

    def test_equality(self):
        g1 = Glyph(id="a", unicode_codepoint=0x61,
                   strokes=(_STROKE,), advance_width=0.6)
        g2 = Glyph(id="a", unicode_codepoint=0x61,
                   strokes=(_STROKE,), advance_width=0.6)
        assert g1 == g2

    def test_inequality_on_id(self):
        g1 = Glyph(id="a", unicode_codepoint=0x61,
                   strokes=(_STROKE,), advance_width=0.6)
        g2 = Glyph(id="b", unicode_codepoint=0x62,
                   strokes=(_STROKE,), advance_width=0.6)
        assert g1 != g2


# ---------------------------------------------------------------------------
# TestGlyphCatalog — RED: catalog.py not yet populated
# ---------------------------------------------------------------------------

class TestGlyphCatalog:
    def _catalog(self):
        from scribesim.glyphs.catalog import GLYPH_CATALOG  # noqa: PLC0415
        return GLYPH_CATALOG

    def test_catalog_count_at_least_85(self):
        catalog = self._catalog()
        assert len(catalog) >= 85, (
            f"Expected ≥85 glyphs, got {len(catalog)}: {sorted(catalog)}"
        )

    def test_all_lowercase_ascii_present(self):
        catalog = self._catalog()
        for ch in "abcdefghijklmnopqrstuvwxyz":
            assert ch in catalog, f"Missing glyph for '{ch}'"

    def test_all_uppercase_ascii_present(self):
        catalog = self._catalog()
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            assert ch in catalog, f"Missing glyph for '{ch}'"

    def test_long_s_present(self):
        catalog = self._catalog()
        assert "long_s" in catalog

    def test_round_s_present(self):
        catalog = self._catalog()
        assert "round_s" in catalog

    def test_esszett_present(self):
        catalog = self._catalog()
        assert "esszett" in catalog or "ß" in catalog

    def test_umlaut_vowels_present(self):
        catalog = self._catalog()
        for name in ("a_umlaut", "o_umlaut", "u_umlaut"):
            assert name in catalog, f"Missing umlaut glyph: {name}"

    def test_all_glyphs_have_nonzero_advance_width(self):
        catalog = self._catalog()
        for gid, glyph in catalog.items():
            assert glyph.advance_width > 0, (
                f"Glyph '{gid}' has non-positive advance_width"
            )

    def test_all_glyphs_have_at_least_one_stroke(self):
        catalog = self._catalog()
        for gid, glyph in catalog.items():
            assert len(glyph.strokes) >= 1, f"Glyph '{gid}' has no strokes"

    def test_no_degenerate_strokes(self):
        """No stroke should have identical P0 and P3 (zero net displacement)."""
        catalog = self._catalog()
        for gid, glyph in catalog.items():
            for stroke in glyph.strokes:
                p0, _, _, p3 = stroke.control_points
                assert p0 != p3, (
                    f"Glyph '{gid}' stroke '{stroke.stroke_name}' is "
                    f"degenerate: P0 == P3 == {p0}"
                )

    def test_long_s_differs_from_round_s(self):
        catalog = self._catalog()
        long_s = catalog["long_s"]
        round_s = catalog["round_s"]
        assert long_s.strokes != round_s.strokes, (
            "long_s and round_s must have different stroke geometry"
        )

    def test_umlaut_has_more_strokes_than_base(self):
        catalog = self._catalog()
        for base, umlaut in (("a", "a_umlaut"), ("o", "o_umlaut"), ("u", "u_umlaut")):
            assert len(catalog[umlaut].strokes) > len(catalog[base].strokes), (
                f"{umlaut} should have more strokes than {base}"
            )

    def test_esszett_stroke_count(self):
        """esszett ≈ long_s + z strokes (within ±1 for connecting stroke)."""
        catalog = self._catalog()
        esszett_key = "esszett" if "esszett" in catalog else "ß"
        esszett_count = len(catalog[esszett_key].strokes)
        combined = len(catalog["long_s"].strokes) + len(catalog["z"].strokes)
        assert abs(esszett_count - combined) <= 1, (
            f"esszett has {esszett_count} strokes; long_s+z = {combined}"
        )

    def test_paragraph_mark_present(self):
        catalog = self._catalog()
        assert "pilcrow" in catalog or "paragraph" in catalog or "¶" in catalog

    def test_section_mark_present(self):
        catalog = self._catalog()
        assert "section" in catalog or "§" in catalog


# ---------------------------------------------------------------------------
# TestGlyphLookup — RED: lookup() not yet implemented
# ---------------------------------------------------------------------------

class TestGlyphLookup:
    def _lookup(self):
        from scribesim.glyphs.catalog import lookup  # noqa: PLC0415
        return lookup

    def test_lookup_returns_glyph(self):
        lookup = self._lookup()
        result = lookup("a", "german")
        assert isinstance(result, Glyph)

    def test_lookup_german_s_returns_long_s(self):
        lookup = self._lookup()
        result = lookup("s", "german")
        assert result.id == "long_s"

    def test_lookup_latin_s_returns_round_s(self):
        lookup = self._lookup()
        result = lookup("s", "latin")
        assert result.id == "round_s"

    def test_lookup_uppercase_A(self):
        lookup = self._lookup()
        result = lookup("A", "german")
        assert result.id == "A"

    def test_lookup_unknown_char_raises(self):
        lookup = self._lookup()
        with pytest.raises((KeyError, ValueError)):
            lookup("@", "german")

    def test_lookup_case_sensitive_uppercase(self):
        lookup = self._lookup()
        lower = lookup("a", "german")
        upper = lookup("A", "german")
        assert lower.id != upper.id
