"""Tests for the TD-014 dense path guide schema and importers."""

from __future__ import annotations

from dataclasses import replace

from scribesim.guides.catalog import GUIDE_CATALOG
from scribesim.evo.genome import BezierSegment
from scribesim.pathguide import (
    DensePathGuide,
    GuideSample,
    build_starter_proof_guides,
    guide_from_letterform_guide,
    guide_from_trace_segments,
    load_legacy_guides_toml_as_dense,
    load_pathguides_toml,
    load_starter_proof_guides,
    load_trace_as_dense,
    validate_dense_path_guide,
    write_pathguides_toml,
)
from scribesim.refextract.centerline import save_trace


def _minimal_trace():
    from scribesim.evo.genome import BezierSegment

    return [
        BezierSegment(
            p0=(0.0, 0.0),
            p1=(0.0, 20.0),
            p2=(0.0, 40.0),
            p3=(0.0, 60.0),
            contact=True,
        ),
        BezierSegment(
            p0=(0.0, 60.0),
            p1=(8.0, 80.0),
            p2=(14.0, 92.0),
            p3=(18.0, 100.0),
            contact=True,
        ),
    ]


def test_pathguide_toml_roundtrip(tmp_path):
    guide = guide_from_letterform_guide(
        GUIDE_CATALOG["u"],
        x_height_mm=3.5,
        source_id="legacy-guide:u",
        source_path="scribesim/guides/catalog.py",
        confidence_tier="accepted",
        split="train",
    )
    midpoint = len(guide.samples) // 2
    samples = list(guide.samples)
    samples[midpoint] = replace(samples[midpoint], nib_angle_deg=34.5, nib_angle_confidence=0.72)
    guide = replace(guide, samples=tuple(samples))

    output_path = tmp_path / "pathguides.toml"
    write_pathguides_toml({"u": guide}, output_path)
    loaded = load_pathguides_toml(output_path)

    assert set(loaded) == {"u"}
    assert loaded["u"].symbol == "u"
    assert loaded["u"].sources[0].confidence_tier == "accepted"
    assert len(loaded["u"].samples) == len(guide.samples)
    assert loaded["u"].samples[midpoint].nib_angle_deg == 34.5
    assert loaded["u"].samples[midpoint].nib_angle_confidence == 0.72


def test_validate_dense_path_guide_rejects_sparse_contact_spacing():
    guide = DensePathGuide(
        symbol="bad",
        kind="glyph",
        samples=(
            GuideSample(0.0, 0.0, 1.0, 0.0, contact=True),
            GuideSample(1.0, 0.0, 1.0, 0.0, contact=True),
        ),
        x_advance_mm=1.0,
        x_height_mm=3.5,
        entry_tangent=(1.0, 0.0),
        exit_tangent=(1.0, 0.0),
    )

    errors = validate_dense_path_guide(guide)
    assert any("exceed max spacing" in error for error in errors)


def test_validate_dense_path_guide_rejects_self_intersection():
    guide = DensePathGuide(
        symbol="bow",
        kind="glyph",
        samples=(
            GuideSample(0.0, 0.0, 1.0, 0.0, contact=True),
            GuideSample(1.0, 1.0, 1.0, 0.0, contact=True),
            GuideSample(0.0, 1.0, -1.0, 0.0, contact=True),
            GuideSample(1.0, 0.0, 1.0, 0.0, contact=True),
        ),
        x_advance_mm=1.0,
        x_height_mm=3.5,
        entry_tangent=(1.0, 0.0),
        exit_tangent=(1.0, 0.0),
    )

    errors = validate_dense_path_guide(guide)
    assert any("self-intersect" in error for error in errors)


def test_guide_from_letterform_guide_normalizes_to_mm():
    guide = guide_from_letterform_guide(
        GUIDE_CATALOG["n"],
        x_height_mm=4.0,
        source_id="legacy-guide:n",
        confidence_tier="accepted",
        split="train",
    )

    assert guide.symbol == "n"
    assert guide.x_advance_mm == GUIDE_CATALOG["n"].x_advance * 4.0
    assert guide.samples[0].x_mm >= 0.0
    assert guide.samples[0].corridor_half_width_mm > 0.0
    assert not validate_dense_path_guide(guide)


def test_load_trace_as_dense_preserves_provenance(tmp_path):
    trace_path = tmp_path / "u_trace.json"
    save_trace(_minimal_trace(), trace_path)

    guide = load_trace_as_dense(
        "u",
        trace_path,
        x_height_px=100.0,
        x_height_mm=3.5,
        source_resolution_ppmm=12.0,
    )

    assert guide.symbol == "u"
    assert guide.sources[0].source_path == trace_path.as_posix()
    assert guide.sources[0].source_resolution_ppmm == 12.0
    assert len(guide.samples) > 10
    assert not validate_dense_path_guide(guide)


def test_guide_from_trace_segments_uses_arc_length_sampling_for_high_curvature_cubic():
    guide = guide_from_trace_segments(
        "s",
        [
            BezierSegment(
                p0=(0.0, 0.0),
                p1=(12.0, 18.0),
                p2=(-5.0, -20.0),
                p3=(19.0, 15.0),
                contact=True,
            )
        ],
        x_height_px=28.0,
        x_height_mm=3.5,
        source_id="manual-guide:s",
        split="validation",
    )

    errors = validate_dense_path_guide(guide)
    assert not any("exceed max spacing" in error for error in errors)
    on_surface = [sample for sample in guide.samples if sample.contact]
    max_gap = max(
        ((on_surface[idx + 1].x_mm - on_surface[idx].x_mm) ** 2 + (on_surface[idx + 1].y_mm - on_surface[idx].y_mm) ** 2) ** 0.5
        for idx in range(len(on_surface) - 1)
    )
    assert max_gap <= 0.2500001


def test_guide_from_trace_segments_inserts_pen_lift_between_strokes():
    guide = guide_from_trace_segments(
        "k",
        [
            BezierSegment(
                p0=(8.0, 80.0),
                p1=(8.0, 55.0),
                p2=(8.0, 20.0),
                p3=(8.0, 0.0),
                contact=True,
            ),
            BezierSegment(
                p0=(8.0, 38.0),
                p1=(22.0, 38.0),
                p2=(38.0, 35.0),
                p3=(52.0, 28.0),
                contact=True,
            ),
            BezierSegment(
                p0=(8.0, 38.0),
                p1=(4.0, 52.0),
                p2=(2.0, 66.0),
                p3=(14.0, 80.0),
                contact=True,
            ),
        ],
        x_height_px=80.0,
        x_height_mm=3.5,
        stroke_ids=[1, 2, 3],
        source_id="manual-guide:k",
        split="validation",
    )

    errors = validate_dense_path_guide(guide)
    assert not any("exceed max spacing" in error for error in errors)
    assert any(not sample.contact for sample in guide.samples)


def test_load_legacy_guides_toml_as_dense(tmp_path):
    legacy_path = tmp_path / "legacy_guides.toml"
    legacy_path.write_text(
        """
[u]
x_advance = 0.6
ascender = false
descender = false

[[u.keypoints]]
x = 0.05
y = 0.95
point_type = "entry"
contact = true
direction_deg = 270.0
flexibility_mm = 0.15

[[u.keypoints]]
x = 0.15
y = 0.0
point_type = "base"
contact = true
direction_deg = 0.0
flexibility_mm = 0.2

[[u.keypoints]]
x = 0.5
y = 0.95
point_type = "exit"
contact = true
direction_deg = 90.0
flexibility_mm = 0.15
""".strip()
    )

    guides = load_legacy_guides_toml_as_dense(legacy_path, x_height_mm=3.5)
    assert set(guides) == {"u"}
    assert guides["u"].sources[0].source_path == legacy_path.as_posix()
    assert not validate_dense_path_guide(guides["u"])


def test_build_starter_proof_guides_contains_expected_symbols():
    guides = build_starter_proof_guides()
    expected = {"u", "n", "d", "e", "r", "u->n", "n->d", "d->e", "e->r"}
    assert expected.issubset(guides)
    for symbol in expected:
        assert not validate_dense_path_guide(guides[symbol]), symbol


def test_load_starter_proof_guides_from_committed_asset():
    guides = load_starter_proof_guides()
    expected = {"u", "n", "d", "e", "r", "u->n", "n->d", "d->e", "e->r"}
    assert expected.issubset(guides)
    for symbol in expected:
        assert not validate_dense_path_guide(guides[symbol]), symbol
