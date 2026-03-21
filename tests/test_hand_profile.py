"""Unit tests for HandProfile — scale-based parameter architecture (ADV-SS-HAND-002)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scribesim.hand.params import HandParams
from scribesim.hand.profile import (
    HandProfile,
    FolioParams,
    LineParams,
    WordParams,
    GlyphParams,
    NibParams,
    InkParams,
    MaterialParams,
    load_profile,
    resolve_profile,
    parse_overrides,
    validate_ranges,
)

HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"


# ---------------------------------------------------------------------------
# TestHandProfile — dataclass construction
# ---------------------------------------------------------------------------

class TestHandProfile:
    def test_default_construction(self):
        p = HandProfile()
        assert isinstance(p.folio, FolioParams)
        assert isinstance(p.nib, NibParams)
        assert isinstance(p.ink, InkParams)
        assert p.script == "bastarda"

    def test_all_scale_groups_present(self):
        p = HandProfile()
        for attr in ("folio", "line", "word", "glyph", "nib", "ink", "material"):
            assert getattr(p, attr) is not None

    def test_nib_defaults_match_td002(self):
        p = HandProfile()
        assert p.nib.angle_deg == pytest.approx(40.0)
        assert p.nib.width_mm == pytest.approx(1.8)
        assert p.nib.flexibility == pytest.approx(0.15)

    def test_folio_defaults(self):
        p = HandProfile()
        assert p.folio.base_pressure == pytest.approx(0.72)
        assert p.folio.tremor_amplitude == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# TestToV1 — backward compatibility
# ---------------------------------------------------------------------------

class TestToV1:
    def test_returns_hand_params(self):
        p = HandProfile()
        v1 = p.to_v1()
        assert isinstance(v1, HandParams)

    def test_nib_angle_maps(self):
        p = HandProfile()
        p.nib.angle_deg = 42.0
        v1 = p.to_v1()
        assert v1.nib_angle_deg == pytest.approx(42.0)

    def test_pressure_base_maps(self):
        p = HandProfile()
        p.folio.base_pressure = 0.65
        v1 = p.to_v1()
        assert v1.pressure_base == pytest.approx(0.65)

    def test_tremor_maps(self):
        p = HandProfile()
        p.folio.tremor_amplitude = 0.04
        v1 = p.to_v1()
        assert v1.tremor_amplitude == pytest.approx(0.04)

    def test_v1_round_trip_matches_base(self):
        """Loading v1 TOML → HandProfile → to_v1() should match load_base()."""
        from scribesim.hand.model import load_base
        v1_direct = load_base(HAND_TOML)
        profile = load_profile(HAND_TOML)
        v1_via_profile = profile.to_v1()

        assert v1_via_profile.nib_angle_deg == pytest.approx(v1_direct.nib_angle_deg)
        assert v1_via_profile.nib_width_mm == pytest.approx(v1_direct.nib_width_mm)
        assert v1_via_profile.pressure_base == pytest.approx(v1_direct.pressure_base)
        assert v1_via_profile.ink_density == pytest.approx(v1_direct.ink_density)
        assert v1_via_profile.x_height_px == v1_direct.x_height_px
        assert v1_via_profile.writing_speed == pytest.approx(v1_direct.writing_speed)
        assert v1_via_profile.slant_deg == pytest.approx(v1_direct.slant_deg)
        assert v1_via_profile.script == v1_direct.script
        assert v1_via_profile.tremor_amplitude == pytest.approx(v1_direct.tremor_amplitude)
        assert v1_via_profile.stroke_weight == pytest.approx(v1_direct.stroke_weight)
        assert v1_via_profile.letter_spacing_norm == pytest.approx(v1_direct.letter_spacing_norm)
        assert v1_via_profile.word_spacing_norm == pytest.approx(v1_direct.word_spacing_norm)


# ---------------------------------------------------------------------------
# TestLoadProfile — TOML loading
# ---------------------------------------------------------------------------

class TestLoadProfile:
    def test_loads_v1_toml(self):
        profile = load_profile(HAND_TOML)
        assert isinstance(profile, HandProfile)

    def test_v1_nib_angle_mapped(self):
        profile = load_profile(HAND_TOML)
        assert profile.nib.angle_deg == pytest.approx(45.0)

    def test_v1_pressure_base_mapped(self):
        profile = load_profile(HAND_TOML)
        assert profile.folio.base_pressure == pytest.approx(0.72)

    def test_v1_ink_density_mapped(self):
        profile = load_profile(HAND_TOML)
        assert profile.ink_density == pytest.approx(0.85)

    def test_v1_script_mapped(self):
        profile = load_profile(HAND_TOML)
        assert profile.script == "bastarda"

    def test_v1_tremor_mapped(self):
        profile = load_profile(HAND_TOML)
        assert profile.folio.tremor_amplitude == pytest.approx(0.0)

    def test_missing_toml_raises(self):
        with pytest.raises((FileNotFoundError, OSError)):
            load_profile(Path("/nonexistent/hand.toml"))


# ---------------------------------------------------------------------------
# TestResolveProfile — per-folio modifier application
# ---------------------------------------------------------------------------

class TestResolveProfile:
    def test_f01r_equals_base(self):
        base = load_profile(HAND_TOML)
        resolved = resolve_profile(base, "f01r")
        assert resolved.folio.base_pressure == pytest.approx(base.folio.base_pressure)
        assert resolved.ink_density == pytest.approx(base.ink_density)

    def test_f06r_elevated_pressure(self):
        base = load_profile(HAND_TOML)
        resolved = resolve_profile(base, "f06r")
        assert resolved.folio.base_pressure == pytest.approx(0.84)
        assert resolved.stroke_weight == pytest.approx(1.15)
        assert resolved.slant_deg == pytest.approx(2.8)

    def test_f04v_degraded_ink(self):
        base = load_profile(HAND_TOML)
        resolved = resolve_profile(base, "f04v")
        assert resolved.folio.base_pressure == pytest.approx(0.55)
        assert resolved.ink_density == pytest.approx(0.52)

    def test_f14r_slower_wider(self):
        base = load_profile(HAND_TOML)
        resolved = resolve_profile(base, "f14r")
        assert resolved.x_height_px == 42
        assert resolved.writing_speed == pytest.approx(0.82)
        assert resolved.letter_spacing_norm == pytest.approx(1.12)

    def test_unmodified_fields_preserved(self):
        base = load_profile(HAND_TOML)
        resolved = resolve_profile(base, "f06r")
        assert resolved.nib.width_mm == pytest.approx(base.nib.width_mm)
        assert resolved.script == base.script

    def test_resolved_to_v1_matches_legacy(self):
        """resolve_profile → to_v1() matches legacy resolve() for f06r."""
        from scribesim.hand.model import load_base, resolve
        v1_base = load_base(HAND_TOML)
        v1_resolved = resolve(v1_base, "f06r")

        profile = load_profile(HAND_TOML)
        resolved = resolve_profile(profile, "f06r")
        v1_via_profile = resolved.to_v1()

        assert v1_via_profile.pressure_base == pytest.approx(v1_resolved.pressure_base)
        assert v1_via_profile.stroke_weight == pytest.approx(v1_resolved.stroke_weight)
        assert v1_via_profile.slant_deg == pytest.approx(v1_resolved.slant_deg)


# ---------------------------------------------------------------------------
# TestOverrides — --set parsing
# ---------------------------------------------------------------------------

class TestOverrides:
    def test_parse_dotted_float(self):
        result = parse_overrides(["nib.angle_deg=38.0"])
        assert result == {"nib.angle_deg": 38.0}

    def test_parse_dotted_int(self):
        result = parse_overrides(["folio.lines_per_page=32"])
        assert result == {"folio.lines_per_page": 32}

    def test_parse_boolean(self):
        result = parse_overrides(["word.slant_reset_at_line_start=false"])
        assert result == {"word.slant_reset_at_line_start": False}

    def test_parse_multiple(self):
        result = parse_overrides(["nib.angle_deg=38", "ink.depletion_rate=0.03"])
        assert len(result) == 2
        assert result["nib.angle_deg"] == 38
        assert result["ink.depletion_rate"] == pytest.approx(0.03)

    def test_parse_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid --set format"):
            parse_overrides(["nib.angle_deg"])

    def test_apply_override_to_profile(self):
        p = HandProfile()
        overrides = parse_overrides(["nib.angle_deg=38"])
        p2 = p.apply_delta(overrides)
        assert p2.nib.angle_deg == pytest.approx(38.0)
        assert p.nib.angle_deg == pytest.approx(40.0)  # original unchanged


# ---------------------------------------------------------------------------
# TestDelta — apply_delta behavior
# ---------------------------------------------------------------------------

class TestDelta:
    def test_dotted_key_sets_scale_field(self):
        p = HandProfile()
        p2 = p.apply_delta({"nib.angle_deg": 42.0})
        assert p2.nib.angle_deg == pytest.approx(42.0)

    def test_v1_flat_key_maps_correctly(self):
        p = HandProfile()
        p2 = p.apply_delta({"pressure_base": 0.55})
        assert p2.folio.base_pressure == pytest.approx(0.55)

    def test_v1_nib_angle_maps(self):
        p = HandProfile()
        p2 = p.apply_delta({"nib_angle_deg": 43.0})
        assert p2.nib.angle_deg == pytest.approx(43.0)

    def test_unknown_key_ignored(self):
        p = HandProfile()
        p2 = p.apply_delta({"completely_unknown": 99})
        # Should not raise; profile unchanged
        assert p2.nib.angle_deg == pytest.approx(p.nib.angle_deg)

    def test_delta_returns_new_instance(self):
        p = HandProfile()
        p2 = p.apply_delta({"nib.angle_deg": 42.0})
        assert p2 is not p


# ---------------------------------------------------------------------------
# TestValidation — range checking
# ---------------------------------------------------------------------------

class TestValidation:
    def test_default_profile_valid(self):
        p = HandProfile()
        errors = validate_ranges(p)
        assert errors == []

    def test_out_of_range_detected(self):
        p = HandProfile()
        p.nib.angle_deg = 99.0  # range is [25, 55]
        errors = validate_ranges(p)
        assert any("nib.angle_deg" in e for e in errors)

    def test_below_range_detected(self):
        p = HandProfile()
        p.folio.base_pressure = 0.1  # range is [0.3, 1.0]
        errors = validate_ranges(p)
        assert any("folio.base_pressure" in e for e in errors)


# ---------------------------------------------------------------------------
# TestFlatDict — serialization for display
# ---------------------------------------------------------------------------

class TestFlatDict:
    def test_contains_all_scale_params(self):
        p = HandProfile()
        d = p.to_flat_dict()
        assert "nib.angle_deg" in d
        assert "folio.base_pressure" in d
        assert "ink.depletion_rate" in d
        assert "material.edge_feather_mm" in d

    def test_contains_metadata(self):
        p = HandProfile()
        d = p.to_flat_dict()
        assert d["script"] == "bastarda"
