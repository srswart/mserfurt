"""Unit and CLI tests for ADV-SS-HAND-004: Bastarda nib-width proportions,
natural 40-deg chisel contact, turn pooling, Tier-1 A1-PROPORTION gate,
and the fast zero-lockout `scribesim sandbox` CLI.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from click.testing import CliRunner
import pytest

from scribesim.cli import main
from scribesim.hand.profile import (
    BASTARDA_DEFAULT_X_HEIGHT_MM,
    BASTARDA_NIB_PROPORTION_RATIO,
    bastarda_nib_calibrated_profile,
    nib_width_for_x_height,
    validate_ranges,
    x_height_to_nib_ratio,
)
from scribesim.render.nib import (
    PhysicsNib,
    chisel_apparent_width_mm,
    evaluate_a1_proportion,
    turn_pooling_factor,
)
from scribesim.render.sandbox import render_sandbox


def test_bastarda_nib_width_proportion_calibration() -> None:
    """Calibrated Bastarda profile uses H = 4.2 * w_nib (w_nib ≈ 0.8333mm for H = 3.5mm)."""
    profile = bastarda_nib_calibrated_profile(x_height_mm=3.5)
    ratio = x_height_to_nib_ratio(profile.letterform.x_height_mm, profile.nib.width_mm)
    assert 3.8 <= ratio <= 4.6
    assert abs(ratio - BASTARDA_NIB_PROPORTION_RATIO) < 0.02
    assert abs(profile.nib.width_mm - nib_width_for_x_height(3.5, 4.2)) < 1e-4
    assert profile.nib.angle_deg == pytest.approx(40.0)
    assert validate_ranges(profile) == []


def test_natural_40_degree_chisel_hairline_and_tine_splay() -> None:
    """Chisel projection naturally collapses to hairline at 40° and splays with pressure on downstrokes."""
    nib = PhysicsNib(width_mm=0.8333, angle_deg=40.0, flexibility=0.20)

    # Moving parallel to the 40° chisel edge produces a natural hairline (~0.175mm, ~1/4.2 of downstroke)
    hairline_w = chisel_apparent_width_mm(nib, direction_deg=40.0, pressure=0.35)
    assert 0.14 <= hairline_w <= 0.22

    # Moving vertically downward (-90° / 270°) crosses the chisel edge broadly
    downstroke_low_p = chisel_apparent_width_mm(nib, direction_deg=-90.0, pressure=0.3)
    downstroke_high_p = chisel_apparent_width_mm(nib, direction_deg=-90.0, pressure=0.85)
    assert downstroke_low_p > 0.60
    assert downstroke_high_p > downstroke_low_p

    # Thick-to-thin contrast between downstroke and 40° hairline join is in [3.2, 5.0]
    contrast = downstroke_high_p / hairline_w
    assert 3.2 <= contrast <= 5.0


def test_velocity_minimum_turn_pooling() -> None:
    """Slowing down at foot/crown direction reversals increases local pooling."""
    w_cruise, i_cruise = turn_pooling_factor(speed_mm_s=14.0, nominal_speed_mm_s=12.0)
    assert w_cruise == pytest.approx(1.0)
    assert i_cruise == pytest.approx(1.0)

    w_turn, i_turn = turn_pooling_factor(speed_mm_s=1.2, nominal_speed_mm_s=12.0)
    assert w_turn > 1.08
    assert i_turn > 1.12

    w_stop, i_stop = turn_pooling_factor(speed_mm_s=0.0, nominal_speed_mm_s=12.0)
    assert w_stop > w_turn
    assert i_stop > i_turn


def test_tier1_a1_proportion_gate() -> None:
    """Tier-1 A1-PROPORTION accepts calibrated Bastarda widths and rejects pointed-pen or monoline inputs."""
    nib = PhysicsNib(width_mm=0.8333, angle_deg=40.0, flexibility=0.20)
    # Realistic mix of downstrokes, arches, and 40° hairline joins
    directions = [-90.0, -88.0, -85.0, -45.0, 0.0, 38.0, 40.0, 41.0, -90.0, -87.0]
    pressures = [0.80, 0.78, 0.75, 0.65, 0.50, 0.30, 0.28, 0.30, 0.82, 0.76]
    widths = [
        chisel_apparent_width_mm(nib, d, p)
        for d, p in zip(directions, pressures)
    ]

    verdict = evaluate_a1_proportion(widths, x_height_mm=3.5, nib_width_mm=nib.width_mm)
    assert verdict["gate"] == "A1-PROPORTION"
    assert verdict["passed"] is True
    assert 3.2 <= verdict["width_ratio_p95_p05"] <= 5.0
    assert 3.8 <= verdict["x_height_to_nib_ratio"] <= 4.6

    # Reject Pass-15 pointed-pen ratio (0.45mm nib on 3.5mm x-height -> ratio 7.78)
    bad_nib_verdict = evaluate_a1_proportion(widths, x_height_mm=3.5, nib_width_mm=0.45)
    assert bad_nib_verdict["passed"] is False
    assert "x_height_to_nib_ratio" in bad_nib_verdict["failures"]

    # Reject monoline widths (ratio ~1.05)
    monoline_verdict = evaluate_a1_proportion([0.50, 0.51, 0.52, 0.50, 0.51], x_height_mm=3.5, nib_width_mm=0.8333)
    assert monoline_verdict["passed"] is False
    assert "width_ratio_p95_p05" in monoline_verdict["failures"]


def test_fast_sandbox_render_and_cli(tmp_path: Path) -> None:
    """`scribesim sandbox` renders word/specimen + kinematic overlay + A1 metrics in <0.5s with no lockouts."""
    out_dir = tmp_path / "sandbox_nu"
    t0 = time.perf_counter()
    report = render_sandbox("nu und", out_dir=out_dir, dpi=180)
    elapsed = time.perf_counter() - t0

    assert elapsed < 0.5, f"Sandbox took {elapsed:.3f}s (expected < 0.5s)"
    assert (out_dir / "sandbox.png").exists()
    assert (out_dir / "overlay.svg").exists()
    assert (out_dir / "metrics.json").exists()
    assert (out_dir / "index.html").exists()
    assert report["a1_proportion"]["passed"] is True

    # Test CLI invocation
    cli_out = tmp_path / "sandbox_cli"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["sandbox", "nu", "--out-dir", str(cli_out), "--dpi", "180"],
    )
    assert result.exit_code == 0, result.output
    metrics = json.loads((cli_out / "metrics.json").read_text())
    assert metrics["a1_proportion"]["passed"] is True
    assert "A1-PROPORTION" in (cli_out / "index.html").read_text()
