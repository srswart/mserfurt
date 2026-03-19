"""Unit tests for the scribesim hand model — ADV-SS-HAND-001.

Red tests: TestResolveHandNotes imports resolve_hand() which does not
exist yet. All other tests should be green after the tidy phase.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scribesim.hand.params import HandParams
from scribesim.hand.modifiers import (
    MODIFIER_REGISTRY,
    pressure_increase,
    ink_density_shift,
    hand_scale,
    spacing_drift,
    tremor,
)
from scribesim.hand.model import load_base, resolve

HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"

_BASE_VALUES = dict(
    nib_angle_deg=45.0,
    nib_width_mm=1.8,
    stroke_weight=1.0,
    pressure_base=0.72,
    pressure_upstroke=0.28,
    pressure_variance=0.08,
    ink_density=0.85,
    ink_bleed_radius_px=1.2,
    letter_spacing_norm=1.0,
    word_spacing_norm=2.4,
    line_height_norm=4.2,
    x_height_px=38,
    writing_speed=1.0,
    fatigue_rate=0.0,
    tremor_amplitude=0.0,
    slant_deg=3.5,
    script="bastarda",
    dialect_region="thuringian",
    date_approx=1457,
)


# ---------------------------------------------------------------------------
# TestHandParams — dataclass behaviour
# ---------------------------------------------------------------------------

class TestHandParams:
    def test_default_construction(self):
        p = HandParams()
        assert p.script == "bastarda"
        assert p.pressure_base == pytest.approx(0.72)

    def test_from_dict_round_trip(self):
        p = HandParams(**_BASE_VALUES)
        assert HandParams.from_dict(p.to_dict()) == p

    def test_from_dict_ignores_unknown_keys(self):
        d = {**_BASE_VALUES, "unknown_future_field": 99}
        p = HandParams.from_dict(d)
        assert p.pressure_base == pytest.approx(0.72)

    def test_from_dict_uses_defaults_for_missing_keys(self):
        p = HandParams.from_dict({"pressure_base": 0.5})
        assert p.pressure_base == pytest.approx(0.5)
        assert p.ink_density == pytest.approx(0.85)  # default

    def test_clamp_pressure_above_max(self):
        p = HandParams(pressure_base=2.5)
        assert p.pressure_base == pytest.approx(2.0)

    def test_clamp_pressure_below_zero(self):
        p = HandParams(pressure_base=-0.1)
        assert p.pressure_base == pytest.approx(0.0)

    def test_clamp_ink_density(self):
        p = HandParams(ink_density=3.0)
        assert p.ink_density == pytest.approx(2.0)

    def test_apply_delta_returns_new_instance(self):
        p = HandParams()
        p2 = p.apply_delta({"pressure_base": 0.9})
        assert p2 is not p
        assert p.pressure_base == pytest.approx(0.72)  # original unchanged
        assert p2.pressure_base == pytest.approx(0.9)

    def test_apply_delta_ignores_unknown_keys(self):
        p = HandParams()
        p2 = p.apply_delta({"no_such_field": 99, "pressure_base": 0.8})
        assert p2.pressure_base == pytest.approx(0.8)

    def test_to_dict_contains_all_base_fields(self):
        p = HandParams()
        d = p.to_dict()
        for key in _BASE_VALUES:
            assert key in d, f"to_dict() missing key: {key}"

    def test_equality(self):
        assert HandParams() == HandParams()
        assert HandParams(pressure_base=0.5) != HandParams(pressure_base=0.9)


# ---------------------------------------------------------------------------
# TestLoadBase — TOML loading
# ---------------------------------------------------------------------------

class TestLoadBase:
    def test_returns_hand_params(self):
        base = load_base(HAND_TOML)
        assert isinstance(base, HandParams)

    def test_nib_angle_from_toml(self):
        base = load_base(HAND_TOML)
        assert base.nib_angle_deg == pytest.approx(45.0)

    def test_script_is_bastarda(self):
        base = load_base(HAND_TOML)
        assert base.script == "bastarda"

    def test_dialect_region(self):
        base = load_base(HAND_TOML)
        assert base.dialect_region == "thuringian"

    def test_base_pressure(self):
        base = load_base(HAND_TOML)
        assert base.pressure_base == pytest.approx(0.72)

    def test_base_ink_density(self):
        base = load_base(HAND_TOML)
        assert base.ink_density == pytest.approx(0.85)

    def test_missing_toml_raises(self):
        with pytest.raises((FileNotFoundError, OSError)):
            load_base(Path("/nonexistent/hand.toml"))


# ---------------------------------------------------------------------------
# TestModifiers — modifier function contracts
# ---------------------------------------------------------------------------

class TestModifiers:
    def test_registry_contains_all_modifiers(self):
        for name in ("pressure_increase", "ink_density_shift", "hand_scale",
                     "spacing_drift", "tremor"):
            assert name in MODIFIER_REGISTRY

    def test_pressure_increase_raises_pressure(self):
        base = HandParams()
        result = pressure_increase(base)
        assert result.pressure_base > base.pressure_base

    def test_pressure_increase_raises_stroke_weight(self):
        base = HandParams()
        result = pressure_increase(base)
        assert result.stroke_weight > base.stroke_weight

    def test_pressure_increase_reduces_slant(self):
        base = HandParams(slant_deg=3.5)
        result = pressure_increase(base)
        assert result.slant_deg < base.slant_deg

    def test_pressure_increase_is_pure(self):
        base = HandParams()
        pressure_increase(base)
        assert base.pressure_base == pytest.approx(0.72)  # unchanged

    def test_ink_density_shift_raises_density(self):
        base = HandParams()
        result = ink_density_shift(base)
        assert result.ink_density > base.ink_density

    def test_ink_density_shift_raises_variance(self):
        base = HandParams()
        result = ink_density_shift(base)
        assert result.pressure_variance > base.pressure_variance

    def test_hand_scale_reduces_x_height(self):
        base = HandParams(x_height_px=38)
        result = hand_scale(base)
        assert result.x_height_px < 38

    def test_hand_scale_tightens_letter_spacing(self):
        base = HandParams(letter_spacing_norm=1.0)
        result = hand_scale(base)
        assert result.letter_spacing_norm < 1.0

    def test_hand_scale_increases_speed(self):
        base = HandParams(writing_speed=1.0)
        result = hand_scale(base)
        assert result.writing_speed > 1.0

    def test_spacing_drift_widens_letter_spacing(self):
        base = HandParams()
        result = spacing_drift(base)
        assert result.letter_spacing_norm > base.letter_spacing_norm

    def test_spacing_drift_widens_word_spacing(self):
        base = HandParams()
        result = spacing_drift(base)
        assert result.word_spacing_norm > base.word_spacing_norm

    def test_spacing_drift_slows_writing(self):
        base = HandParams()
        result = spacing_drift(base)
        assert result.writing_speed < base.writing_speed

    def test_spacing_drift_increases_x_height(self):
        base = HandParams(x_height_px=38)
        result = spacing_drift(base)
        assert result.x_height_px > 38

    def test_tremor_sets_amplitude(self):
        base = HandParams(tremor_amplitude=0.0)
        result = tremor(base)
        assert result.tremor_amplitude > 0.0

    def test_tremor_increases_fatigue_rate(self):
        base = HandParams(fatigue_rate=0.0)
        result = tremor(base)
        assert result.fatigue_rate > 0.0

    def test_stacked_modifiers_accumulate(self):
        base = HandParams()
        result = tremor(spacing_drift(base))
        assert result.tremor_amplitude > 0.0
        assert result.letter_spacing_norm > base.letter_spacing_norm

    def test_all_modifier_outputs_within_range(self):
        """Every modifier must keep normalised fields within [0.0, 2.0]."""
        base = HandParams()
        for name, fn in MODIFIER_REGISTRY.items():
            result = fn(base)
            for field in ("pressure_base", "ink_density", "stroke_weight",
                          "writing_speed", "letter_spacing_norm"):
                val = getattr(result, field)
                assert 0.0 <= val <= 2.0, (
                    f"{name}: {field}={val} out of [0.0, 2.0]"
                )


# ---------------------------------------------------------------------------
# TestResolveTOML — folio ID → TOML delta resolution
# ---------------------------------------------------------------------------

class TestResolveTOML:
    def test_f01r_equals_base(self):
        base = load_base(HAND_TOML)
        resolved = resolve(base, "f01r")
        assert resolved == base

    def test_f06r_elevated_pressure(self):
        base = load_base(HAND_TOML)
        resolved = resolve(base, "f06r")
        assert resolved.pressure_base == pytest.approx(0.84)
        assert resolved.stroke_weight == pytest.approx(1.15)
        assert resolved.slant_deg == pytest.approx(2.8)

    def test_f04v_degraded_ink(self):
        base = load_base(HAND_TOML)
        resolved = resolve(base, "f04v")
        assert resolved.pressure_base == pytest.approx(0.55)
        assert resolved.ink_density == pytest.approx(0.52)

    def test_f14r_slower_wider(self):
        base = load_base(HAND_TOML)
        resolved = resolve(base, "f14r")
        assert resolved.x_height_px == 42
        assert resolved.writing_speed == pytest.approx(0.82)
        assert resolved.letter_spacing_norm == pytest.approx(1.12)

    def test_unmodified_fields_preserved(self):
        base = load_base(HAND_TOML)
        resolved = resolve(base, "f06r")
        assert resolved.nib_angle_deg == pytest.approx(base.nib_angle_deg)
        assert resolved.script == base.script

    def test_deterministic(self):
        base = load_base(HAND_TOML)
        assert resolve(base, "f06r") == resolve(base, "f06r")

    def test_folio_id_with_f_prefix(self):
        base = load_base(HAND_TOML)
        assert resolve(base, "f06r") == resolve(base, "06r")


# ---------------------------------------------------------------------------
# TestResolveHandNotes — CLIO-7 hand note string → modifier stack (RED)
# resolve_hand(base, hand_note_str) does not exist yet
# ---------------------------------------------------------------------------

class TestResolveHandNotes:
    """resolve_hand() maps CLIO-7 hand note strings to named modifiers.

    RED: resolve_hand does not exist yet in scribesim.hand.model.
    Each test imports it directly so the rest of the file stays collectable.
    """

    def _resolve_hand(self):
        from scribesim.hand.model import resolve_hand  # noqa: PLC0415
        return resolve_hand

    def test_standard_hand_equals_base(self):
        resolve_hand = self._resolve_hand()
        base = load_base(HAND_TOML)
        result = resolve_hand(base, "standard")
        assert result == base

    def test_increased_lateral_pressure_raises_pressure(self):
        resolve_hand = self._resolve_hand()
        base = load_base(HAND_TOML)
        result = resolve_hand(base, "increased_lateral_pressure_downstrokes")
        assert result.pressure_base > base.pressure_base
        assert result.stroke_weight > base.stroke_weight

    def test_multi_sitting_variable_ink_shifts_density(self):
        resolve_hand = self._resolve_hand()
        base = load_base(HAND_TOML)
        result = resolve_hand(base, "multi_sitting_variable_ink")
        assert result.ink_density > base.ink_density

    def test_smaller_economical_working_reduces_x_height(self):
        resolve_hand = self._resolve_hand()
        base = load_base(HAND_TOML)
        result = resolve_hand(base, "smaller_economical_working")
        assert result.x_height_px < base.x_height_px

    def test_slower_wider_compensating_widens_spacing(self):
        resolve_hand = self._resolve_hand()
        base = load_base(HAND_TOML)
        result = resolve_hand(base, "slower_wider_compensating")
        assert result.letter_spacing_norm > base.letter_spacing_norm
        assert result.tremor_amplitude > 0.0

    def test_unknown_hand_note_returns_base_unchanged(self):
        resolve_hand = self._resolve_hand()
        base = load_base(HAND_TOML)
        result = resolve_hand(base, "some_future_note_not_yet_mapped")
        assert result == base

    def test_resolve_hand_is_deterministic(self):
        resolve_hand = self._resolve_hand()
        base = load_base(HAND_TOML)
        note = "increased_lateral_pressure_downstrokes"
        assert resolve_hand(base, note) == resolve_hand(base, note)

    def test_resolve_hand_returns_hand_params(self):
        resolve_hand = self._resolve_hand()
        base = load_base(HAND_TOML)
        result = resolve_hand(base, "standard")
        assert isinstance(result, HandParams)
