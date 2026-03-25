"""Tests for TD-014 planned-state handflow."""

from __future__ import annotations

import numpy as np

from scribesim.hand.profile import HandProfile
from scribesim.handflow import (
    GuidedHandFlowController,
    PROOF_WORDS,
    build_primitive_proof_guides,
    build_proof_vocabulary_session,
    build_track_plan,
    build_word_session,
    load_word_guide_catalog,
    render_trajectory_proof,
    run_primitive_proof,
    run_stateful_word_proof,
)
from scribesim.handvalidate import corridor_containment_ratio


def _profile() -> HandProfile:
    profile = HandProfile()
    profile.letterform.x_height_mm = 3.5
    profile.dynamics.position_gain = 24.0
    profile.dynamics.velocity_gain = 9.0
    profile.dynamics.max_speed = 34.0
    profile.dynamics.max_acceleration = 520.0
    profile.stroke_weight = 1.0
    profile.ink_density = 0.85
    return profile


def test_build_track_plan_has_monotonic_time_and_length():
    guide = build_primitive_proof_guides()["downstroke"]
    plan = build_track_plan(guide, base_speed_mm_s=20.0)

    assert len(plan.samples) == len(guide.samples)
    assert plan.total_time_s > 0.0
    assert plan.total_length_mm > 0.0
    assert all(plan.samples[idx].t_s <= plan.samples[idx + 1].t_s for idx in range(len(plan.samples) - 1))
    assert all(
        plan.samples[idx].arc_length_mm <= plan.samples[idx + 1].arc_length_mm
        for idx in range(len(plan.samples) - 1)
    )


def test_desired_velocity_affects_acceleration():
    profile = _profile()
    controller = GuidedHandFlowController(profile)
    guide = build_primitive_proof_guides()["downstroke"]
    plan = build_track_plan(guide, base_speed_mm_s=20.0)
    state = controller.initial_state(plan)
    desired = plan.samples[1]
    fast = desired
    slow = type(desired)(
        t_s=desired.t_s,
        arc_length_mm=desired.arc_length_mm,
        x_mm=desired.x_mm,
        y_mm=desired.y_mm,
        vx_mm_s=0.0,
        vy_mm_s=0.0,
        speed_mm_s=1.0,
        pressure=desired.pressure,
        contact=desired.contact,
        corridor_half_width_mm=desired.corridor_half_width_mm,
    )

    ax_fast, ay_fast = controller.desired_acceleration(state, fast)
    ax_slow, ay_slow = controller.desired_acceleration(state, slow)

    assert (ax_fast, ay_fast) != (ax_slow, ay_slow)


def test_simulate_guide_tracks_nominal_primitive_inside_corridor():
    profile = _profile()
    controller = GuidedHandFlowController(profile)
    guide = build_primitive_proof_guides()["downstroke"]
    result = controller.simulate_guide(guide, dt=0.002)

    assert len(result.trajectory) > 10
    assert corridor_containment_ratio(result.trajectory, guide) >= 0.95
    assert result.max_corridor_error_mm < 0.40


def test_render_trajectory_proof_supports_supersampling():
    profile = _profile()
    controller = GuidedHandFlowController(profile)
    guide = build_primitive_proof_guides()["upstroke"]
    result = controller.simulate_guide(guide, dt=0.002)

    baseline = render_trajectory_proof(result.trajectory, profile=profile, dpi=220, supersample=1)
    hi = render_trajectory_proof(result.trajectory, profile=profile, dpi=220, supersample=3)

    assert baseline.ndim == 3
    assert hi.ndim == 3
    assert hi.shape[0] >= baseline.shape[0] - 1
    assert hi.shape[1] >= baseline.shape[1] - 1
    assert not np.array_equal(baseline, hi)


def test_run_primitive_proof_emits_snapshots_and_reports(tmp_path):
    reports = run_primitive_proof(tmp_path, profile=_profile(), dpi=220, supersample=2)

    assert set(reports) == {"downstroke", "upstroke", "bowl_arc", "ascender_loop", "pen_lift", "minim_pair"}
    for name in reports:
        assert (tmp_path / f"{name}.png").exists()
        assert (tmp_path / f"primitive:{name}.json").exists()
        assert (tmp_path / f"primitive:{name}.md").exists()


def test_build_word_session_contains_contact_joins_for_und():
    catalog = load_word_guide_catalog(x_height_mm=_profile().letterform.x_height_mm)
    items, merged = build_word_session("und", guide_catalog=catalog)

    assert [item.symbol for item in items] == ["u", "u->n", "n", "n->d", "d"]
    assert merged.kind == "word"
    assert any(sample.contact for sample in merged.samples)


def test_build_word_session_records_alias_resolution_for_missing_letters():
    catalog = load_word_guide_catalog(x_height_mm=_profile().letterform.x_height_mm)
    items, _ = build_word_session("sůz", guide_catalog=catalog)

    glyphs = [item for item in items if item.kind == "glyph"]
    assert [item.requested_symbol for item in glyphs] == ["s", "ů", "z"]
    assert [item.resolved_symbol for item in glyphs] == ["r", "u", "r"]
    assert [item.resolution_kind for item in glyphs] == ["alias", "normalized", "alias"]


def test_simulate_session_preserves_ink_state_across_guides():
    profile = _profile()
    controller = GuidedHandFlowController(profile)
    catalog = load_word_guide_catalog(x_height_mm=profile.letterform.x_height_mm)
    items, _ = build_word_session("und", guide_catalog=catalog)
    result = controller.simulate_session(items, dt=0.002)

    assert len(result.trajectory) > 20
    assert len(result.state_trace) == len(items)
    assert result.state_trace[0].start_ink_reservoir == profile.ink.reservoir_capacity
    assert result.state_trace[-1].end_ink_reservoir <= result.state_trace[0].start_ink_reservoir


def test_run_stateful_word_proof_emits_word_snapshots_and_logs(tmp_path):
    reports = run_stateful_word_proof(tmp_path, profile=_profile(), dpi=220, supersample=2)

    assert set(reports) == set(PROOF_WORDS)
    for word in PROOF_WORDS:
        assert (tmp_path / f"{word}.png").exists()
        assert (tmp_path / f"stateful_word:{word}.json").exists()
        assert (tmp_path / f"stateful_word:{word}.md").exists()
    assert (tmp_path / "state_trace.json").exists()
    assert (tmp_path / "proof_vocabulary_summary.json").exists()


def test_build_proof_vocabulary_session_includes_word_boundaries():
    catalog = load_word_guide_catalog(x_height_mm=_profile().letterform.x_height_mm)
    session, word_guides = build_proof_vocabulary_session(("und", "der"), guide_catalog=catalog)

    assert "und" in word_guides
    assert "der" in word_guides
    assert any(item.kind == "transition" for item in session)
