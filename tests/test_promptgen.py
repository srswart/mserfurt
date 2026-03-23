"""Tests for weather/promptgen.py — ADV-WX-PROMPTGEN-001."""

from __future__ import annotations

import pytest

from weather.promptgen import (
    CoherenceContext,
    FolioWeatherSpec,
    FoxingSpot,
    MissingCornerSpec,
    TextDegradationZone,
    WaterDamageSpec,
    WordDamageEntry,
    build_coherence_context,
    generate_text_degradation_prompt,
    generate_weathering_prompt,
    summarize_weathering,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _f01r_spec() -> FolioWeatherSpec:
    """f01r — outermost recto, standard stock, no water or corner damage, 2 foxing spots."""
    return FolioWeatherSpec(
        folio_id="f01r",
        vellum_stock="standard",
        edge_darkening=0.9,
        gutter_side="left",
        foxing_spots=[
            FoxingSpot(position=(0.72, 0.35), intensity=0.6, radius=0.012),
            FoxingSpot(position=(0.15, 0.78), intensity=0.4, radius=0.008),
        ],
    )


def _f04r_spec() -> FolioWeatherSpec:
    """f04r — severe water damage source, missing corner bottom-left."""
    return FolioWeatherSpec(
        folio_id="f04r",
        vellum_stock="standard",
        edge_darkening=0.7,
        gutter_side="left",
        water_damage=WaterDamageSpec(severity=1.0, origin="top_right", penetration=0.6),
        missing_corner=MissingCornerSpec(
            corner="bottom_left", depth_fraction=0.08, width_fraction=0.07
        ),
    )


def _f04v_spec() -> FolioWeatherSpec:
    """f04v — same leaf as f04r, gutter on right, mirrored corner."""
    return FolioWeatherSpec(
        folio_id="f04v",
        vellum_stock="standard",
        edge_darkening=0.7,
        gutter_side="right",
        water_damage=WaterDamageSpec(severity=0.85, origin="top_left", penetration=0.51),
        missing_corner=MissingCornerSpec(
            corner="bottom_right", depth_fraction=0.08, width_fraction=0.07
        ),
    )


def _f14r_spec() -> FolioWeatherSpec:
    """f14r — irregular vellum stock, no special damage."""
    return FolioWeatherSpec(
        folio_id="f14r",
        vellum_stock="irregular",
        edge_darkening=0.65,
        gutter_side="left",
    )


_EMPTY_CONTEXT = CoherenceContext()


# ---------------------------------------------------------------------------
# generate_weathering_prompt — preservation instruction
# ---------------------------------------------------------------------------

def test_prompt_starts_with_preservation_instruction():
    spec = _f01r_spec()
    prompt = generate_weathering_prompt(spec, _EMPTY_CONTEXT)
    assert prompt.startswith("Apply realistic aging"), (
        "First sentence must be the preservation/apply instruction"
    )


def test_prompt_contains_do_not_alter():
    spec = _f01r_spec()
    prompt = generate_weathering_prompt(spec, _EMPTY_CONTEXT)
    assert "Do NOT alter" in prompt


# ---------------------------------------------------------------------------
# generate_weathering_prompt — vellum stock
# ---------------------------------------------------------------------------

def test_f01r_prompt_standard_vellum():
    prompt = generate_weathering_prompt(_f01r_spec(), _EMPTY_CONTEXT)
    assert "standard calfskin parchment" in prompt


def test_f14r_prompt_irregular_vellum():
    prompt = generate_weathering_prompt(_f14r_spec(), _EMPTY_CONTEXT)
    assert "irregular stock" in prompt


# ---------------------------------------------------------------------------
# generate_weathering_prompt — damage sections present / absent
# ---------------------------------------------------------------------------

def test_f01r_no_water_damage_section():
    prompt = generate_weathering_prompt(_f01r_spec(), _EMPTY_CONTEXT)
    assert "water damage" not in prompt.lower() or "water" not in prompt.lower().split("water damage")[0]
    # Simpler: f01r has no water_damage, so the water section should not appear
    assert "tide lines" not in prompt


def test_f01r_no_missing_corner_section():
    prompt = generate_weathering_prompt(_f01r_spec(), _EMPTY_CONTEXT)
    assert "missing" not in prompt.lower() or "corner" not in prompt


def test_f04r_severe_water_section():
    prompt = generate_weathering_prompt(_f04r_spec(), _EMPTY_CONTEXT)
    assert "severe" in prompt
    assert "top_right" in prompt
    assert "60%" in prompt
    assert "tide lines" in prompt


def test_f04r_missing_corner_bottom_left():
    prompt = generate_weathering_prompt(_f04r_spec(), _EMPTY_CONTEXT)
    assert "bottom_left" in prompt
    assert "torn" in prompt.lower() or "missing" in prompt.lower()


def test_f04v_gutter_right():
    prompt = generate_weathering_prompt(_f04v_spec(), _EMPTY_CONTEXT)
    assert "right" in prompt  # gutter_side=right should appear in edge section


def test_f01r_foxing_section_present():
    prompt = generate_weathering_prompt(_f01r_spec(), _EMPTY_CONTEXT)
    assert "foxing" in prompt.lower()
    assert "2" in prompt  # 2 foxing spots


# ---------------------------------------------------------------------------
# generate_weathering_prompt — section order
# ---------------------------------------------------------------------------

def test_prompt_section_order_preservation_first():
    """Preservation instruction must be the first substantive content."""
    prompt = generate_weathering_prompt(_f04r_spec(), _EMPTY_CONTEXT)
    preserve_idx = prompt.index("Do NOT alter")
    water_idx = prompt.index("tide lines")
    assert preserve_idx < water_idx


def test_prompt_section_order_water_before_corner():
    prompt = generate_weathering_prompt(_f04r_spec(), _EMPTY_CONTEXT)
    water_idx = prompt.index("tide lines")
    corner_idx = prompt.index("bottom_left")
    assert water_idx < corner_idx


# ---------------------------------------------------------------------------
# generate_text_degradation_prompt — word-level
# ---------------------------------------------------------------------------

def test_lacuna_at_position_produces_no_ink_instruction():
    entries = [
        WordDamageEntry(
            word_text="[lacuna]",
            bbox=(600, 670, 750, 710),
            center=(650.0, 720.0),
            confidence=0.0,
            category="lacuna",
            line_number=3,
        )
    ]
    result = generate_text_degradation_prompt(entries, page_width=1000, page_height=1000)
    assert "65%" in result
    assert "72%" in result
    assert "no ink whatsoever" in result


def test_partial_word_stolz_produces_partially_obscure():
    entries = [
        WordDamageEntry(
            word_text="stolz",
            bbox=(600, 680, 660, 710),
            center=(630.0, 695.0),
            confidence=0.55,
            category="trace",
            line_number=24,
            specific_note="partially obscured — alternative reading 'verloren' cannot be ruled out",
        )
    ]
    result = generate_text_degradation_prompt(entries, page_width=1000, page_height=1000)
    assert "partially obscure" in result
    assert "ambiguous" in result


def test_empty_word_damage_map_returns_empty_string():
    result = generate_text_degradation_prompt([], page_width=1000, page_height=1000)
    assert result == ""


def test_clear_word_appears_in_legible_section():
    entries = [
        WordDamageEntry(
            word_text="Hie",
            bbox=(100, 100, 160, 130),
            center=(130.0, 115.0),
            confidence=0.95,
            category="clear",
            line_number=1,
        )
    ]
    result = generate_text_degradation_prompt(entries, page_width=1000, page_height=1000)
    assert "LEGIBLE TEXT" in result


# ---------------------------------------------------------------------------
# build_coherence_context
# ---------------------------------------------------------------------------

def _minimal_map() -> dict[str, FolioWeatherSpec]:
    specs = {}
    for n in range(1, 18):
        for s in ("r", "v"):
            fid = f"f{n:02d}{s}"
            specs[fid] = FolioWeatherSpec(
                folio_id=fid,
                vellum_stock="standard",
                edge_darkening=0.65,
                gutter_side="left" if s == "r" else "right",
            )
    # Give f04r water damage for propagation tests
    specs["f04r"].water_damage = WaterDamageSpec(severity=1.0, origin="top_right", penetration=0.6)
    specs["f04v"].water_damage = WaterDamageSpec(severity=0.85, origin="top_left", penetration=0.51)
    return specs


def test_coherence_context_f04v_same_leaf_is_f04r():
    ctx = build_coherence_context("f04v", _minimal_map())
    same_leaf = [a for a in ctx.adjacent_folios if a.same_leaf]
    assert len(same_leaf) == 1
    assert same_leaf[0].folio_id == "f04r"
    assert same_leaf[0].relation == "recto"


def test_coherence_context_f04v_facing_is_f05r():
    ctx = build_coherence_context("f04v", _minimal_map())
    facing = [a for a in ctx.adjacent_folios if not a.same_leaf]
    assert len(facing) == 1
    assert facing[0].folio_id == "f05r"


def test_coherence_context_reference_image_set_when_weathered():
    mock_image = object()
    weathered = {"f04r": mock_image}
    ctx = build_coherence_context("f04v", _minimal_map(), weathered_so_far=weathered)
    same_leaf = next(a for a in ctx.adjacent_folios if a.same_leaf)
    assert same_leaf.reference_image is mock_image


def test_coherence_context_reference_image_none_when_not_weathered():
    ctx = build_coherence_context("f04v", _minimal_map(), weathered_so_far={})
    for adj in ctx.adjacent_folios:
        assert adj.reference_image is None


def test_coherence_context_f01r_no_facing_page():
    """f01r is the outermost recto — no leaf before it to face."""
    ctx = build_coherence_context("f01r", _minimal_map())
    # Same-leaf partner is f01v
    same_leaf = [a for a in ctx.adjacent_folios if a.same_leaf]
    assert same_leaf[0].folio_id == "f01v"
    # No facing page (f01r has no preceding verso)
    facing = [a for a in ctx.adjacent_folios if not a.same_leaf]
    assert len(facing) == 0


# ---------------------------------------------------------------------------
# summarize_weathering
# ---------------------------------------------------------------------------

def test_summarize_returns_nonempty_for_any_spec():
    for spec in [_f01r_spec(), _f04r_spec(), _f04v_spec(), _f14r_spec()]:
        assert summarize_weathering(spec) != ""


def test_summarize_f04r_mentions_water_and_severe():
    summary = summarize_weathering(_f04r_spec())
    assert "water" in summary.lower()
    assert "severe" in summary.lower()


def test_summarize_f14r_mentions_irregular():
    summary = summarize_weathering(_f14r_spec())
    assert "irregular" in summary.lower()


def test_summarize_f01r_no_water():
    summary = summarize_weathering(_f01r_spec())
    assert "water" not in summary.lower()
