"""Unit tests for ADV-SS-TUNING-002: Differentiable PyTorch Broad-Nib Ribbon
Renderer (`scribesim/tuning/diff_render.py`), 30-Word BSB Reference Grounding
with Baseline-Band Weighting (`scribesim/annotate/reference_confirm.py`),
and Human Checkpoint #2 3-Line Specimen Board.
"""

from __future__ import annotations

from pathlib import Path
import torch
import pytest

from scribesim.annotate.reference_confirm import (
    confirm_reference_words,
    load_confirmed_reference_words,
)
from scribesim.annotate.review_board import (
    CHECKPOINT_2_SPECIMENS,
    build_review_sheet,
)
from scribesim.tuning import baseline_band_weight_mask
from scribesim.tuning.diff_render import (
    DifferentiableRibbonRenderer,
    refine_viapoints_on_reference_words,
)


def test_confirm_bsb_reference_words_with_baseline_band_weighting(tmp_path: Path) -> None:
    """Confirms >= 30 clean BSB reference words with baseline-band weighting masks."""
    out_manifest = tmp_path / "confirmed_reference_words.json"
    summary = confirm_reference_words(
        dataset_root=Path("reference/konrad_hand_recovery_v3"),
        output_path=out_manifest,
    )
    assert summary["confirmed_count"] >= 30
    assert out_manifest.exists()

    words = load_confirmed_reference_words(out_manifest)
    assert len(words) >= 30
    first = words[0]
    assert first["text"]
    mask = baseline_band_weight_mask(
        first["height_px"],
        first["width_px"],
        first["baseline_y_px"],
        first["xheight_px"],
    )
    assert mask.shape == (first["height_px"], first["width_px"])
    # Weight inside core x-height band is 1.0, weight far outside decays < 1.0
    core_y = max(0, min(first["height_px"] - 1, int(first["baseline_y_px"] - 0.5 * first["xheight_px"])))
    assert mask[core_y, 0] == pytest.approx(1.0)


def test_differentiable_soft_ribbon_renderer_gradients() -> None:
    """PyTorch DifferentiableRibbonRenderer produces finite non-zero gradients w.r.t. coordinates and nib angle."""
    renderer = DifferentiableRibbonRenderer(height_px=48, width_px=96, px_per_mm=10.0)

    pts_mm = torch.tensor(
        [[1.5, 1.0], [1.6, 4.2], [2.8, 1.2], [3.0, 4.2]],
        dtype=torch.float32,
        requires_grad=True,
    )
    pressures = torch.tensor([0.80, 0.78, 0.28, 0.82], dtype=torch.float32)
    nib_angle_deg = torch.tensor(40.0, dtype=torch.float32, requires_grad=True)
    nib_width_mm = torch.tensor(0.8333, dtype=torch.float32, requires_grad=True)

    ink_img = renderer(
        pts_mm,
        pressures=pressures,
        nib_angle_deg=nib_angle_deg,
        nib_width_mm=nib_width_mm,
    )
    assert ink_img.shape == (48, 96)
    assert float(ink_img.detach().max()) > 0.4
    assert float(ink_img.detach().min()) >= 0.0

    # Target shifted slightly right -> loss gradient must be finite and non-zero
    target_pts = pts_mm.detach() + torch.tensor([0.25, 0.10])
    target_img = renderer(
        target_pts,
        pressures=pressures,
        nib_angle_deg=torch.tensor(41.5),
        nib_width_mm=torch.tensor(0.85),
    ).detach()

    loss = torch.mean(torch.abs(ink_img - target_img))
    loss.backward()

    assert pts_mm.grad is not None
    assert torch.isfinite(pts_mm.grad).all()
    assert float(torch.norm(pts_mm.grad)) > 1e-4
    assert nib_angle_deg.grad is not None
    assert torch.isfinite(nib_angle_deg.grad)


def test_bounded_viapoint_refinement_and_checkpoint_2_specimen(tmp_path: Path) -> None:
    """Gradient refinement lowers weighted reference loss while preserving Tier-1 gates A1-A4."""
    toml_out = tmp_path / "konrad_kinematic_v1.toml"
    report = refine_viapoints_on_reference_words(
        dataset_root=Path("reference/konrad_hand_recovery_v3"),
        output_toml=toml_out,
        steps=18,
    )
    assert report["final_loss"] < report["initial_loss"]
    assert report["tier1_gates"]["a1_passed"] is True
    assert report["tier1_gates"]["a2_passed"] is True
    assert report["tier1_gates"]["a3_passed"] is True
    assert report["tier1_gates"]["a4_passed"] is True
    assert toml_out.exists()

    # Build Checkpoint #2 3-line proof specimen review board
    board_dir = tmp_path / "checkpoint_2_board"
    assert len(CHECKPOINT_2_SPECIMENS) == 3
    manifest = build_review_sheet(
        stage_id="checkpoint-2-specimen",
        specimens=CHECKPOINT_2_SPECIMENS,
        out_dir=board_dir,
        dpi=160,
    )
    assert manifest["stage_id"] == "checkpoint-2-specimen"
    assert manifest["tier1_summary"]["a1_all_passed"] is True
    assert manifest["tier1_summary"]["a2_all_passed"] is True
    assert manifest["tier1_summary"]["a3_coarticulate"]["passed"] is True
