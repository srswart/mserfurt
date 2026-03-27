"""Integration coverage for TD-014 guided folio rendering."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.hand.profile import HandProfile
import pytest

from scribesim.handflow import GuidedFolioResolutionError, render_guided_folio_lines
from scribesim.handvalidate import ocr_proxy_score
from scribesim.pathguide import guide_from_waypoints, write_pathguides_toml


GOLDEN_F01R = Path(__file__).parent / "golden" / "f01r" / "folio.json"
WEATHER_PROFILE_TOML = Path(__file__).parent.parent / "shared" / "profiles" / "ms-erfurt-560yr.toml"


def _folio_lines() -> list[str]:
    folio = json.loads(GOLDEN_F01R.read_text())
    return [line["text"] for line in folio["lines"]]


def _profile() -> HandProfile:
    profile = HandProfile()
    profile.letterform.x_height_mm = 3.5
    profile.dynamics.position_gain = 29.0
    profile.dynamics.velocity_gain = 11.5
    profile.dynamics.max_speed = 28.0
    profile.dynamics.max_acceleration = 620.0
    profile.stroke_weight = 1.0
    profile.ink_density = 0.85
    return profile


def _write_reviewed_catalog(tmp_path: Path) -> Path:
    catalog_path = tmp_path / "reviewed_promoted_v1.toml"
    guides = {
        "H": guide_from_waypoints(
            "H",
            [(0.0, 0.9, True), (0.0, 0.1, True), (0.55, 0.1, True), (0.55, 0.9, True)],
            x_height_mm=3.5,
            x_advance_xh=1.1,
            kind="glyph",
            source_id="reviewed-cleaned:H",
            source_path="cleaned_H.png",
            confidence_tier="accepted",
            split="validation",
            source_resolution_ppmm=16.0,
        ),
        "i": guide_from_waypoints(
            "i",
            [(0.0, 0.7, True), (0.0, 0.2, True)],
            x_height_mm=3.5,
            x_advance_xh=0.45,
            kind="glyph",
            source_id="reviewed-raw:i",
            source_path="raw_i.png",
            confidence_tier="accepted",
            split="train",
            source_resolution_ppmm=16.0,
        ),
        "H->i": guide_from_waypoints(
            "H->i",
            [(0.0, 0.5, True), (0.2, 0.52, True), (0.4, 0.45, True)],
            x_height_mm=3.5,
            x_advance_xh=0.35,
            kind="join",
            source_id="reviewed-cleaned:H->i",
            source_path="cleaned_H_to_i.png",
            confidence_tier="accepted",
            split="test",
            source_resolution_ppmm=16.0,
        ),
    }
    write_pathguides_toml(guides, catalog_path)
    return catalog_path


def test_guided_folio_render_is_deterministic_for_fixed_profile():
    lines = _folio_lines()[:2]
    profile = _profile()

    page_a, heat_a = render_guided_folio_lines(
        lines,
        profile=profile,
        page_width_mm=70.0,
        page_height_mm=100.0,
        margin_left_mm=6.0,
        margin_top_mm=7.0,
        line_spacing_mm=8.0,
        supersample=4,
    )
    page_b, heat_b = render_guided_folio_lines(
        lines,
        profile=profile,
        page_width_mm=70.0,
        page_height_mm=100.0,
        margin_left_mm=6.0,
        margin_top_mm=7.0,
        line_spacing_mm=8.0,
        supersample=4,
    )

    assert np.array_equal(page_a, page_b)
    assert np.array_equal(heat_a, heat_b)


def test_guided_folio_heatmap_matches_page_canvas_shape_and_ink():
    page, heat = render_guided_folio_lines(
        _folio_lines()[:2],
        profile=_profile(),
        page_width_mm=70.0,
        page_height_mm=32.0,
        margin_left_mm=6.0,
        margin_top_mm=7.0,
        line_spacing_mm=8.0,
        supersample=4,
    )

    assert page.shape[:2] == heat.shape
    assert heat.dtype == np.uint8
    assert heat.max() > 0

    parchment = np.array([245, 238, 220], dtype=np.uint8)
    ink_mask = np.any(page != parchment, axis=2)
    heat_mask = heat > 0
    assert ink_mask.any()
    assert heat_mask.any()


def test_guided_folio_exact_metadata_reports_actual_trajectory_mode():
    page, heat, metadata = render_guided_folio_lines(
        _folio_lines()[:1],
        profile=_profile(),
        page_width_mm=70.0,
        page_height_mm=20.0,
        margin_left_mm=6.0,
        margin_top_mm=7.0,
        line_spacing_mm=8.0,
        supersample=4,
        exact_symbols=True,
        return_metadata=True,
    )

    assert page.shape[:2] == heat.shape
    assert metadata["render_trajectory_mode"] == "actual"
    assert metadata["exact_symbols"] is True
    assert metadata["resolution"]["exact_only_passed"] is True
    assert metadata["resolution"]["alias_substitution_count"] == 0
    assert metadata["aligned_page"].shape == page.shape
    assert metadata["activated_parameters"]["folio.base_pressure"] == pytest.approx(_profile().folio.base_pressure)
    assert metadata["activated_parameters"]["glyph.baseline_jitter_mm"] == pytest.approx(
        _profile().glyph.baseline_jitter_mm
    )


def test_guided_folio_exact_symbols_refuse_unresolved_text():
    with pytest.raises(GuidedFolioResolutionError):
        render_guided_folio_lines(
            ["Dāz"],
            profile=_profile(),
            page_width_mm=70.0,
            page_height_mm=20.0,
            margin_left_mm=6.0,
            margin_top_mm=7.0,
            line_spacing_mm=8.0,
            supersample=4,
            exact_symbols=True,
        )


def test_guided_high_supersample_improves_fidelity_against_higher_reference():
    lines = _folio_lines()[:2]
    profile = _profile()
    low_page, _ = render_guided_folio_lines(
        lines,
        profile=profile,
        page_width_mm=70.0,
        page_height_mm=45.0,
        margin_left_mm=6.0,
        margin_top_mm=7.0,
        line_spacing_mm=8.0,
        supersample=2,
    )
    mid_page, _ = render_guided_folio_lines(
        lines,
        profile=profile,
        page_width_mm=70.0,
        page_height_mm=45.0,
        margin_left_mm=6.0,
        margin_top_mm=7.0,
        line_spacing_mm=8.0,
        supersample=4,
    )
    ref_page, _ = render_guided_folio_lines(
        lines,
        profile=profile,
        page_width_mm=70.0,
        page_height_mm=45.0,
        margin_left_mm=6.0,
        margin_top_mm=7.0,
        line_spacing_mm=8.0,
        supersample=6,
    )

    assert ocr_proxy_score(mid_page, ref_page) >= ocr_proxy_score(low_page, ref_page)


def test_guided_folio_variants_render_without_controller_blowup():
    lines = _folio_lines()[:2]
    variants = {
        "clean": {},
        "pressure_heavy": {"folio.base_pressure": 0.88, "stroke_weight": 1.15},
        "multi_sitting": {"folio.base_tempo": 2.2, "word.speed_variance": 0.18},
        "fatigue": {"fatigue_rate": 0.02, "ink.depletion_rate": 0.03},
    }

    for overrides in variants.values():
        profile = _profile().apply_delta(overrides)
        page, heat = render_guided_folio_lines(
            lines,
            profile=profile,
            page_width_mm=70.0,
            page_height_mm=60.0,
            margin_left_mm=6.0,
            margin_top_mm=7.0,
            line_spacing_mm=8.0,
            supersample=4,
        )
        assert np.any(page != np.array([245, 238, 220], dtype=np.uint8))
        assert heat.max() > 0


def test_guided_folio_outputs_are_accepted_by_weather_pipeline():
    from weather.compositor import composite_folio
    from weather.profile import load_profile
    from weather.substrate.vellum import VellumStock

    page, heat = render_guided_folio_lines(
        _folio_lines()[:2],
        profile=_profile(),
        page_width_mm=70.0,
        page_height_mm=32.0,
        margin_left_mm=6.0,
        margin_top_mm=7.0,
        line_spacing_mm=8.0,
        supersample=4,
    )
    weather_profile = load_profile(WEATHER_PROFILE_TOML)
    result = composite_folio(
        Image.fromarray(page, mode="RGB"),
        Image.fromarray(heat, mode="L"),
        "f01r",
        weather_profile,
        stock=VellumStock.STANDARD,
        seed=0,
    )

    assert result.image.size == (page.shape[1], page.shape[0])


def test_guided_folio_metadata_reports_override_reviewed_catalog(tmp_path):
    catalog_path = _write_reviewed_catalog(tmp_path)

    page, heat, metadata = render_guided_folio_lines(
        ["Hi"],
        profile=_profile(),
        page_width_mm=40.0,
        page_height_mm=20.0,
        margin_left_mm=4.0,
        margin_top_mm=4.0,
        line_spacing_mm=8.0,
        supersample=3,
        exact_symbols=True,
        guide_catalog_path=catalog_path,
        return_metadata=True,
    )

    assert page.shape[:2] == heat.shape
    assert metadata["guide_catalog"]["source_label"] == "override"
    assert metadata["guide_catalog"]["guide_catalog_path"] == str(catalog_path)
    assert metadata["guide_catalog"]["reviewed_cleaned_source_count"] >= 1
    assert metadata["resolution"]["exact_only_passed"] is True
