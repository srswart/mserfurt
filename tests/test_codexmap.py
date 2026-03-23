"""Tests for weather/codexmap.py — ADV-WX-CODEXMAP-001."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from weather.codexmap import (
    compute_water_propagation,
    compute_edge_darkening,
    generate_foxing_clusters,
    compute_codex_weathering_map,
    save_codex_map,
    load_codex_map,
)
from weather.promptgen import FolioWeatherSpec


# ---------------------------------------------------------------------------
# compute_water_propagation
# ---------------------------------------------------------------------------

def test_water_propagation_source_recto():
    assert compute_water_propagation(4, "r") == pytest.approx(1.0)


def test_water_propagation_source_verso():
    assert compute_water_propagation(4, "v") == pytest.approx(0.85)


def test_water_propagation_one_leaf_verso():
    """f03v: 1 leaf from source, no verso attenuation → 0.40."""
    assert compute_water_propagation(3, "v") == pytest.approx(0.40)


def test_water_propagation_one_leaf_recto():
    """f03r and f05r: 1 leaf from source → 0.40."""
    assert compute_water_propagation(3, "r") == pytest.approx(0.40)
    assert compute_water_propagation(5, "r") == pytest.approx(0.40)


def test_water_propagation_three_leaves_away():
    """f01v: 3 leaves from source → 0.4^3 ≈ 0.064.
    Note: advance spec has a typo listing folio 2 here; folio 1 is 3 leaves away.
    """
    val = compute_water_propagation(1, "v")
    assert val == pytest.approx(0.064, abs=0.005)


def test_water_propagation_far_leaf_returns_zero():
    """f08r: 4 leaves from source → 0.4^4 = 0.0256 < 0.03 threshold → 0.0."""
    assert compute_water_propagation(8, "r") == pytest.approx(0.0)


def test_water_propagation_custom_source():
    """Public API supports customisable source folio."""
    # Source at leaf 1, querying leaf 3 → 0.4^2 = 0.16
    val = compute_water_propagation(3, "r", source_folio=1)
    assert val == pytest.approx(0.16, abs=0.005)


# ---------------------------------------------------------------------------
# compute_edge_darkening
# ---------------------------------------------------------------------------

def test_edge_darkening_outermost_leaves():
    """f01 and f17 should be at or near 0.9."""
    assert compute_edge_darkening(1, 17) >= 0.85
    assert compute_edge_darkening(17, 17) >= 0.85


def test_edge_darkening_inner_folio():
    """Inner folios (e.g. leaf 9 of 17) should be <= 0.7."""
    assert compute_edge_darkening(9, 17) <= 0.7


def test_edge_darkening_monotone():
    """Leaves closer to the edge should have higher darkening."""
    assert compute_edge_darkening(1, 17) >= compute_edge_darkening(5, 17)
    assert compute_edge_darkening(5, 17) >= compute_edge_darkening(9, 17)


# ---------------------------------------------------------------------------
# generate_foxing_clusters
# ---------------------------------------------------------------------------

def test_foxing_clusters_mirrored_verso():
    """For each recto foxing spot, the verso of the same leaf should mirror the x position."""
    clusters = generate_foxing_clusters(n_clusters=3, gathering_size=17, seed=1457)

    # Find a leaf that has both recto (positive key) and verso (negative key) spots
    recto_leaves = {k for k in clusters if k > 0}
    verso_leaves = {-k for k in clusters if k < 0}
    shared = recto_leaves & verso_leaves

    assert len(shared) > 0, "Expected at least one leaf with both recto and verso spots"

    leaf = next(iter(shared))
    recto_spots = clusters[leaf]
    verso_spots = clusters[-leaf]

    # Verify at least one recto/verso pair mirrors x
    any_mirrored = any(
        abs((1.0 - r.position[0]) - v.position[0]) < 0.05
        for r in recto_spots
        for v in verso_spots
    )
    assert any_mirrored, "Expected at least one recto/verso spot pair with mirrored x position"


def test_foxing_clusters_deterministic():
    c1 = generate_foxing_clusters(5, 17, 1457)
    c2 = generate_foxing_clusters(5, 17, 1457)
    # Same keys
    assert set(c1.keys()) == set(c2.keys())
    # Same positions
    for k in c1:
        for s1, s2 in zip(c1[k], c2[k]):
            assert s1.position == s2.position


def test_foxing_clusters_different_seeds_differ():
    c1 = generate_foxing_clusters(5, 17, 1457)
    c2 = generate_foxing_clusters(5, 17, 9999)
    # With different seeds, at least some positions differ
    all_same = all(
        c1.get(k) is not None and c2.get(k) is not None and
        all(s1.position == s2.position for s1, s2 in zip(c1.get(k, []), c2.get(k, [])))
        for k in set(c1) & set(c2)
    )
    assert not all_same


# ---------------------------------------------------------------------------
# compute_codex_weathering_map — structural checks
# ---------------------------------------------------------------------------

def test_map_contains_34_folios():
    wmap = compute_codex_weathering_map(gathering_size=17)
    assert len(wmap) == 34


def test_map_missing_corner_only_on_f04():
    wmap = compute_codex_weathering_map()
    assert wmap["f04r"].missing_corner is not None
    assert wmap["f04v"].missing_corner is not None
    assert wmap["f03v"].missing_corner is None
    assert wmap["f05r"].missing_corner is None


def test_map_f04r_corner_bottom_left():
    wmap = compute_codex_weathering_map()
    assert wmap["f04r"].missing_corner.corner == "bottom_left"
    assert wmap["f04r"].missing_corner.depth_fraction == pytest.approx(0.08)
    assert wmap["f04r"].missing_corner.width_fraction == pytest.approx(0.07)


def test_map_f04v_corner_bottom_right():
    wmap = compute_codex_weathering_map()
    assert wmap["f04v"].missing_corner.corner == "bottom_right"


def test_map_vellum_stock():
    wmap = compute_codex_weathering_map()
    assert wmap["f13v"].vellum_stock == "standard"
    assert wmap["f14r"].vellum_stock == "irregular"
    assert wmap["f17v"].vellum_stock == "irregular"


def test_map_deterministic():
    """Two calls with same seed produce byte-identical JSON."""
    m1 = compute_codex_weathering_map(seed=1457)
    m2 = compute_codex_weathering_map(seed=1457)
    with tempfile.TemporaryDirectory() as td:
        p1 = Path(td) / "m1.json"
        p2 = Path(td) / "m2.json"
        save_codex_map(m1, p1)
        save_codex_map(m2, p2)
        assert p1.read_text() == p2.read_text()


def test_map_gutter_sides():
    wmap = compute_codex_weathering_map()
    assert wmap["f04r"].gutter_side == "left"
    assert wmap["f04v"].gutter_side == "right"


# ---------------------------------------------------------------------------
# CLIO-7 merge
# ---------------------------------------------------------------------------

def test_clio7_annotations_sets_text_degradation():
    """Providing clio7_annotations for f04r with a low-confidence line
    should set text_degradation on that spec."""
    clio7 = {
        "f04r": [
            {
                "number": 24,
                "text": "stolz und voll",
                "annotations": [{"type": "confidence", "detail": {"score": 0.55}}],
            }
        ]
    }
    wmap = compute_codex_weathering_map(clio7_annotations=clio7)
    spec = wmap["f04r"]
    assert spec.text_degradation is not None
    assert len(spec.text_degradation) >= 1
    zone = spec.text_degradation[0]
    assert zone.confidence == pytest.approx(0.55)


def test_clio7_high_confidence_not_included():
    """Lines with confidence >= 0.8 should not produce text_degradation zones."""
    clio7 = {
        "f01r": [
            {
                "number": 1,
                "text": "Hie hebt sich an",
                "annotations": [{"type": "confidence", "detail": {"score": 0.97}}],
            }
        ]
    }
    wmap = compute_codex_weathering_map(clio7_annotations=clio7)
    spec = wmap["f01r"]
    # No degradation zones for clear text
    assert spec.text_degradation is None or len(spec.text_degradation) == 0


def test_clio7_lacuna_annotation_included():
    """Lacuna annotations should always produce a text_degradation zone."""
    clio7 = {
        "f04r": [
            {
                "number": 10,
                "text": "",
                "annotations": [{"type": "lacuna", "detail": {"extent_chars": 5}}],
            }
        ]
    }
    wmap = compute_codex_weathering_map(clio7_annotations=clio7)
    assert wmap["f04r"].text_degradation is not None
    zone = wmap["f04r"].text_degradation[0]
    assert zone.confidence == pytest.approx(0.0)


def test_clio7_folios_without_annotations_unaffected():
    """Folios not in clio7_annotations should have text_degradation=None."""
    clio7 = {
        "f04r": [
            {
                "number": 1, "text": "x",
                "annotations": [{"type": "confidence", "detail": {"score": 0.4}}],
            }
        ]
    }
    wmap = compute_codex_weathering_map(clio7_annotations=clio7)
    assert wmap["f01r"].text_degradation is None


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_save_load_roundtrip(tmp_path):
    wmap = compute_codex_weathering_map()
    path = tmp_path / "codex_map.json"
    save_codex_map(wmap, path)
    loaded = load_codex_map(path)
    assert set(loaded.keys()) == set(wmap.keys())
    spec_orig = wmap["f04r"]
    spec_load = loaded["f04r"]
    assert spec_load.water_damage.severity == pytest.approx(spec_orig.water_damage.severity)
    assert spec_load.missing_corner.corner == spec_orig.missing_corner.corner
