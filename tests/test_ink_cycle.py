"""Tests for the ink reservoir model and rendering curves (ADV-SS-INK-002/003 / TD-010)."""

import pytest
from scribesim.ink.cycle import (
    DipEvent, InkState,
    ink_darkness, ink_width_modifier,
    HairlineEffects, hairline_effects,
)


# ---------------------------------------------------------------------------
# InkState construction
# ---------------------------------------------------------------------------

def test_initial_reservoir_is_full():
    ink = InkState()
    assert ink.reservoir == 1.0


def test_custom_capacity():
    ink = InkState(capacity=0.8)
    assert ink.reservoir == 0.8
    assert ink.capacity == 0.8


def test_initial_counters_zero():
    ink = InkState()
    assert ink.strokes_since_dip == 0
    assert ink.words_since_dip == 0
    assert ink.total_dips == 0


# ---------------------------------------------------------------------------
# deplete_for_stroke
# ---------------------------------------------------------------------------

def test_depletion_formula():
    """consumption = length * pressure * (width/2) * base_depletion / viscosity"""
    ink = InkState(base_depletion=0.0008, viscosity=1.0)
    length_mm = 5.0
    pressure = 1.0
    width_mm = 2.0
    # expected = 5.0 * 1.0 * (2.0/2.0) * 0.0008 / 1.0 = 0.004
    expected = length_mm * pressure * (width_mm / 2.0) * 0.0008 / 1.0
    ink.deplete_for_stroke(length_mm, pressure, width_mm)
    assert abs(ink.reservoir - (1.0 - expected)) < 1e-9


def test_depletion_viscosity_slows_consumption():
    ink_normal = InkState(viscosity=1.0)
    ink_thick = InkState(viscosity=2.0)
    ink_normal.deplete_for_stroke(10.0, 1.0, 1.0)
    ink_thick.deplete_for_stroke(10.0, 1.0, 1.0)
    assert ink_thick.reservoir > ink_normal.reservoir


def test_depletion_increments_strokes_since_dip():
    ink = InkState()
    ink.deplete_for_stroke(1.0, 1.0, 1.0)
    ink.deplete_for_stroke(1.0, 1.0, 1.0)
    assert ink.strokes_since_dip == 2


def test_depletion_clamps_at_zero():
    ink = InkState()
    ink.reservoir = 0.001
    ink.deplete_for_stroke(1000.0, 1.0, 10.0)
    assert ink.reservoir == 0.0


# ---------------------------------------------------------------------------
# should_dip / wants_to_dip
# ---------------------------------------------------------------------------

def test_should_dip_below_threshold():
    ink = InkState(dip_threshold=0.15)
    ink.reservoir = 0.14
    assert ink.should_dip() is True


def test_should_dip_at_threshold_boundary():
    ink = InkState(dip_threshold=0.15)
    ink.reservoir = 0.15
    assert ink.should_dip() is False  # strictly less than


def test_should_dip_above_threshold():
    ink = InkState(dip_threshold=0.15)
    ink.reservoir = 0.50
    assert ink.should_dip() is False


def test_wants_to_dip_below_preferred_threshold():
    ink = InkState(preferred_dip_threshold=0.22)
    ink.reservoir = 0.20
    assert ink.wants_to_dip() is True


def test_wants_to_dip_above_preferred_threshold():
    ink = InkState(preferred_dip_threshold=0.22)
    ink.reservoir = 0.30
    assert ink.wants_to_dip() is False


# ---------------------------------------------------------------------------
# dip()
# ---------------------------------------------------------------------------

def test_dip_restores_reservoir_to_capacity():
    ink = InkState(capacity=1.0)
    ink.reservoir = 0.10
    ink.dip()
    assert ink.reservoir == 1.0


def test_dip_resets_strokes_since_dip():
    ink = InkState()
    ink.deplete_for_stroke(5.0, 1.0, 1.0)
    assert ink.strokes_since_dip > 0
    ink.dip()
    assert ink.strokes_since_dip == 0


def test_dip_resets_words_since_dip():
    ink = InkState()
    ink.words_since_dip = 12
    ink.dip()
    assert ink.words_since_dip == 0


def test_dip_increments_total_dips():
    ink = InkState()
    ink.dip()
    ink.dip()
    assert ink.total_dips == 2


# ---------------------------------------------------------------------------
# process_word_boundary
# ---------------------------------------------------------------------------

def test_word_boundary_no_dip_at_full_reservoir():
    ink = InkState()
    ink.reservoir = 0.80
    event = ink.process_word_boundary()
    assert event == DipEvent.NoDip
    assert ink.words_since_dip == 1


def test_word_boundary_preferred_dip_in_low_range():
    ink = InkState(dip_threshold=0.15, preferred_dip_threshold=0.22)
    ink.reservoir = 0.18  # below preferred but above forced
    event = ink.process_word_boundary()
    assert event == DipEvent.PreferredDip
    assert ink.reservoir == ink.capacity  # dipped


def test_word_boundary_forced_dip_at_critical():
    ink = InkState(dip_threshold=0.15, preferred_dip_threshold=0.22)
    ink.reservoir = 0.10  # below forced threshold
    event = ink.process_word_boundary()
    assert event == DipEvent.ForcedDip
    assert ink.reservoir == ink.capacity  # dipped


def test_word_boundary_increments_words_since_dip_on_no_dip():
    ink = InkState()
    ink.reservoir = 0.90
    ink.process_word_boundary()
    ink.process_word_boundary()
    assert ink.words_since_dip == 2


def test_word_boundary_resets_words_since_dip_on_dip():
    ink = InkState(preferred_dip_threshold=0.22)
    ink.reservoir = 0.20
    ink.words_since_dip = 15
    ink.process_word_boundary()
    # process_word_boundary() increments to 16, then dip() resets to 0
    assert ink.words_since_dip == 0


# ---------------------------------------------------------------------------
# Calibration check — plausible depletion rate
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# ink_darkness() — TD-010 Part 2.1
# ---------------------------------------------------------------------------

def test_ink_darkness_at_full():
    assert abs(ink_darkness(1.0) - 1.12) < 0.01

def test_ink_darkness_at_half():
    # reservoir=0.5: 0.55 + 0.57 * 0.5^0.4 = 0.55 + 0.57 * 0.758 = 0.982
    assert abs(ink_darkness(0.5) - 0.97) < 0.02

def test_ink_darkness_at_low():
    # reservoir=0.2: 0.55 + 0.57 * 0.2^0.4 = 0.55 + 0.57 * 0.525 = 0.849
    val = ink_darkness(0.2)
    assert 0.75 < val < 0.90

def test_ink_darkness_at_very_low():
    # reservoir=0.05: should be visibly faded but not invisible
    val = ink_darkness(0.05)
    assert 0.55 < val < 0.75

def test_ink_darkness_floor_at_zero():
    """A completely dry quill still leaves a mark — floor is 0.55."""
    assert ink_darkness(0.0) >= 0.55

def test_ink_darkness_ceiling_at_full():
    """Fresh dip gives a slight saturation boost — ceiling is 1.12."""
    assert ink_darkness(1.0) <= 1.13

def test_ink_darkness_monotone():
    """Darkness is non-decreasing as reservoir increases."""
    vals = [ink_darkness(r / 10) for r in range(11)]
    for i in range(len(vals) - 1):
        assert vals[i] <= vals[i + 1] + 1e-9

def test_ink_darkness_clamps_out_of_range():
    """Values outside [0, 1] are clamped — no exceptions, no negative output."""
    assert ink_darkness(-0.5) == ink_darkness(0.0)
    assert ink_darkness(1.5) == ink_darkness(1.0)


# ---------------------------------------------------------------------------
# ink_width_modifier() — TD-010 Part 2.2
# ---------------------------------------------------------------------------

def test_ink_width_modifier_at_full():
    assert abs(ink_width_modifier(1.0) - 1.08) < 0.01

def test_ink_width_modifier_at_zero():
    assert abs(ink_width_modifier(0.0) - 0.94) < 0.01

def test_ink_width_modifier_range():
    """Always in [0.94, 1.08] across all reservoir levels."""
    for r in range(101):
        val = ink_width_modifier(r / 100)
        assert 0.93 <= val <= 1.09, f"Out of range at reservoir={r/100}: {val}"

def test_ink_width_modifier_monotone():
    """Width modifier is non-decreasing as reservoir increases."""
    vals = [ink_width_modifier(r / 10) for r in range(11)]
    for i in range(len(vals) - 1):
        assert vals[i] <= vals[i + 1] + 1e-9

def test_ink_width_modifier_clamps_out_of_range():
    assert ink_width_modifier(-0.5) == ink_width_modifier(0.0)
    assert ink_width_modifier(1.5) == ink_width_modifier(1.0)


# ---------------------------------------------------------------------------
# Calibration check — plausible depletion rate
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# hairline_effects() — TD-010 Part 2.3
# ---------------------------------------------------------------------------

def test_hairline_effects_negligible_at_normal_reservoir():
    """At reservoir=0.5, all three effects are effectively zero (< 0.5% influence)."""
    fx = hairline_effects(0.5)
    assert fx.width_reduction < 0.005   # < 0.5% width change — imperceptible
    assert fx.gap_probability < 0.002   # < 0.2% gap chance — imperceptible
    assert fx.raking_probability < 0.001

def test_hairline_width_reduction_at_near_empty():
    """At reservoir=0.02, width_reduction approaches max (~0.40+)."""
    fx = hairline_effects(0.02)
    assert fx.width_reduction > 0.40

def test_hairline_gap_probability_at_near_empty():
    """At reservoir=0.02, gap_probability approaches max (~0.22+)."""
    fx = hairline_effects(0.02)
    assert fx.gap_probability > 0.22

def test_hairline_raking_negligible_at_low_mid():
    """At reservoir=0.15, raking_probability should still be low (< 0.06).
    The raking sigmoid is centred at 0.08 so 0.15 is well above it."""
    fx = hairline_effects(0.15)
    assert fx.raking_probability < 0.06

def test_hairline_raking_meaningful_at_very_low():
    """At reservoir=0.02, raking_probability should be meaningful (> 0.15)."""
    fx = hairline_effects(0.02)
    assert fx.raking_probability > 0.15

def test_hairline_effects_non_negative():
    """All effects are non-negative at any reservoir level."""
    for r in range(101):
        fx = hairline_effects(r / 100)
        assert fx.width_reduction >= 0.0
        assert fx.gap_probability >= 0.0
        assert fx.raking_probability >= 0.0

def test_hairline_effects_max_bounds():
    """Effects never exceed their specified maximums."""
    for r in range(101):
        fx = hairline_effects(r / 100)
        assert fx.width_reduction <= 0.451
        assert fx.gap_probability <= 0.251
        assert fx.raking_probability <= 0.301

def test_hairline_effects_monotone_decreasing():
    """All effects increase as reservoir drops (monotone in reservoir order)."""
    vals = [(hairline_effects(r / 20).width_reduction,
             hairline_effects(r / 20).gap_probability,
             hairline_effects(r / 20).raking_probability)
            for r in range(21)]
    for i in range(len(vals) - 1):
        # Higher reservoir → lower effect
        assert vals[i][0] >= vals[i + 1][0] - 1e-9
        assert vals[i][1] >= vals[i + 1][1] - 1e-9
        assert vals[i][2] >= vals[i + 1][2] - 1e-9

def test_hairline_effects_clamps_out_of_range():
    """Out-of-range reservoir values are clamped without exception."""
    fx_low = hairline_effects(-0.5)
    fx_zero = hairline_effects(0.0)
    assert abs(fx_low.width_reduction - fx_zero.width_reduction) < 1e-9

    fx_high = hairline_effects(1.5)
    fx_one = hairline_effects(1.0)
    assert abs(fx_high.width_reduction - fx_one.width_reduction) < 1e-9

def test_hairline_effects_returns_dataclass():
    """hairline_effects returns a HairlineEffects instance."""
    assert isinstance(hairline_effects(0.5), HairlineEffects)


# ---------------------------------------------------------------------------
# Calibration check — plausible depletion rate
# ---------------------------------------------------------------------------

def test_realistic_depletion_rate():
    """A 7-word line (avg 4 letters × ~3 strokes × ~4mm each) should deplete
    reservoir noticeably at default calibration — not trivially (>0.98) and
    not catastrophically (<0.50) for a single line."""
    ink = InkState()
    # Simulate 7 words × 6 strokes × 4mm per stroke at avg pressure 0.85, width 1.0mm
    for _ in range(7 * 6):
        ink.deplete_for_stroke(4.0, 0.85, 1.0)
    assert 0.50 < ink.reservoir < 0.98, (
        f"Expected reservoir in [0.50, 0.98] after simulated 7-word line, "
        f"got {ink.reservoir:.3f}"
    )


def test_folio_dip_count():
    """A 28-line folio (8 words/line) should produce 4–12 dips at default calibration.

    Uses realistic stroke parameters calibrated to GLYPH_CATALOG output at
    x_height=3.8mm: ~6 contact strokes per word at ~4mm each.
    """
    ink = InkState()
    for _ in range(28 * 8):  # 224 words
        # Each word: avg 4 letters × ~1.5 contact strokes × 4mm
        for _ in range(6):
            ink.deplete_for_stroke(4.0, 0.85, 1.0)
        ink.process_word_boundary()

    assert 4 <= ink.total_dips <= 12, (
        f"Expected 4–12 dips for a 28-line folio, got {ink.total_dips}"
    )
