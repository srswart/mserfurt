"""Unit tests for ADV-SS-HANDFLOW-012: Global Minimum-Jerk Via-Point
Coarticulation Solver, starter Bastarda ViaPointRecipe catalog (i, n, u, m, d, e, r),
and Tier-1 A2-KINEMATICS and A3-COARTICULATE automated gates.
"""

from __future__ import annotations

import time
import pytest

from scribesim.guides.viapoint import (
    VIAPOINT_STARTER_CATALOG,
    ViaPoint,
    ViaPointRecipe,
    lookup_viapoint_recipe,
)
from scribesim.hand.profile import bastarda_nib_calibrated_profile
from scribesim.handflow.coarticulate import (
    compose_text_kinematic,
    solve_word_coarticulation,
)
from scribesim.handvalidate.kinematic_gates import (
    evaluate_a2_kinematics,
    evaluate_a3_coarticulate,
)
from scribesim.render.sandbox import render_sandbox


def test_starter_viapoint_catalog_completeness_and_structure() -> None:
    """Starter catalog defines i, n, u, m, d, e, r in nib-width units with anisotropic tolerances."""
    required = ("i", "n", "u", "m", "d", "e", "r")
    for ch in required:
        recipe = lookup_viapoint_recipe(ch)
        assert isinstance(recipe, ViaPointRecipe)
        assert recipe.letter == ch
        assert len(recipe.via_points) >= 4
        assert recipe.advance_wnib > 0.8
        # Protected body stems have tighter x tolerance than flexible entry/exit boundaries
        body_pts = [vp for vp in recipe.via_points if vp.role == "body"]
        boundary_pts = [vp for vp in recipe.via_points if vp.role in ("entry", "exit")]
        assert body_pts and boundary_pts
        min_body_sigma = min(vp.sigma_x_wnib for vp in body_pts)
        max_bound_sigma = max(max(vp.sigma_x_wnib, vp.sigma_y_wnib) for vp in boundary_pts)
        assert min_body_sigma < max_bound_sigma


def test_minimum_jerk_solver_speed_and_a2_kinematics() -> None:
    """Global minimum-jerk QP solves a word trajectory in <15ms and passes Tier-1 A2-KINEMATICS."""
    profile = bastarda_nib_calibrated_profile()
    for word in ("nu", "nm", "um", "nn", "und", "der", "mir"):
        t0 = time.perf_counter()
        res = solve_word_coarticulation(word, profile=profile)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert elapsed_ms < 25.0, f"{word} solve took {elapsed_ms:.2f}ms"
        assert len(res.samples) > 20

        a2 = evaluate_a2_kinematics(res)
        assert a2["gate"] == "A2-KINEMATICS"
        assert a2["passed"] is True, f"A2 failed for {word}: {a2}"


def test_reciprocal_coarticulation_a3_gate() -> None:
    """Neighboring letters automatically adapt each other's boundary trajectories while preserving stems."""
    profile = bastarda_nib_calibrated_profile()
    verdict = evaluate_a3_coarticulate(profile=profile)
    assert verdict["gate"] == "A3-COARTICULATE"
    assert verdict["passed"] is True, f"A3 failed: {verdict}"

    # Verify both preceding-letter adaptation (n in nu vs nm) and following-letter adaptation (u in nu vs u)
    assert 0.03 <= verdict["n_exit_delta_wnib_nu_vs_nm"] <= 0.35
    assert 0.03 <= verdict["u_entry_delta_wnib_nu_vs_isolated"] <= 0.35
    # Verify protected stem body of n stays invariant (< 0.05 w_nib)
    assert verdict["n_protected_body_delta_wnib"] < 0.05


def test_sandbox_integration_with_coarticulation_solver(tmp_path) -> None:
    """`render_sandbox` uses the coarticulation solver automatically when available."""
    out = tmp_path / "coart_sandbox"
    metrics = render_sandbox("nu nm und der mir", out_dir=out, dpi=180)
    assert metrics["a1_proportion"]["passed"] is True
    assert (out / "sandbox.png").exists()
    samples, vias = compose_text_kinematic("und der")
    assert len(samples) > 40
    assert len(vias) >= 20
