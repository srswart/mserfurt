"""Unit and CLI tests for ADV-SS-SCRIBEHAND-004: Structure-Conditioned
Hybrid Ink-Edge Micro-Texture Pass (`scribesim/scribehand/hybrid_texture.py`),
Centerline Preservation IoU Gate (>= 0.92), PAGE XML Coordinate Invariance,
and `--hybrid-texture` CLI Option.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
import numpy as np
import pytest

from scribesim.cli import main
from scribesim.handvalidate.tier2_bench import render_kinematic_folio
from scribesim.scribehand.hybrid_texture import (
    MAX_HYBRID_STRENGTH,
    apply_hybrid_texture_pass,
    evaluate_hybrid_structure_gate,
)


def test_hybrid_texture_pass_structure_preservation_and_determinism(tmp_path: Path) -> None:
    """`apply_hybrid_texture_pass` adds quill-on-vellum edge & pore texture while keeping centerline IoU >= 0.92."""
    folio_dict = json.loads(Path("output-live/f01r.json").read_text(encoding="utf-8"))
    raw_res = render_kinematic_folio(
        folio_dict,
        output_dir=tmp_path / "raw",
        folio_id="f01r",
        dpi=160,
        max_lines=3,
        hybrid_texture=False,
    )
    raw_rgb = raw_res["page_array"]
    from PIL import Image
    heat_arr = np.asarray(Image.open(raw_res["heatmap_path"]).convert("L"), dtype=np.uint8)

    # Apply structure-conditioned hybrid texture pass
    tex_1 = apply_hybrid_texture_pass(raw_rgb, heat_arr, seed=1457, strength=0.22)
    tex_2 = apply_hybrid_texture_pass(raw_rgb, heat_arr, seed=1457, strength=0.22)

    # 1. Bitwise determinism for fixed seed
    assert np.array_equal(tex_1, tex_2)
    assert not np.array_equal(raw_rgb, tex_1)

    # 2. Strength is clamped at MAX_HYBRID_STRENGTH (0.25) even if higher value passed
    tex_clamped = apply_hybrid_texture_pass(raw_rgb, heat_arr, seed=1457, strength=0.85)
    tex_max = apply_hybrid_texture_pass(raw_rgb, heat_arr, seed=1457, strength=MAX_HYBRID_STRENGTH)
    assert np.array_equal(tex_clamped, tex_max)

    # 3. Evaluate structure-preservation gate
    gate = evaluate_hybrid_structure_gate(raw_rgb, tex_1, heat_arr)
    assert gate["gate"] == "HYBRID-STRUCTURE-IOU"
    assert gate["passed"] is True, f"Hybrid structure gate failed: {gate}"
    assert gate["centerline_iou"] >= 0.92
    assert gate["counter_delta"] == 0
    assert gate["edge_micro_roughness_gain"] > 0.0
    assert gate["interior_granulation_gain"] > 0.0


def test_hybrid_texture_page_xml_invariance_and_cli(tmp_path: Path) -> None:
    """`--hybrid-texture` preserves exact PAGE XML coordinates and passes glyph bbox IoU >= 0.95."""
    folio_dict = json.loads(Path("output-live/f01r.json").read_text(encoding="utf-8"))
    raw_dir = tmp_path / "raw_folio"
    hyb_dir = tmp_path / "hyb_folio"

    raw_res = render_kinematic_folio(
        folio_dict, output_dir=raw_dir, folio_id="f01r", dpi=150, max_lines=3, hybrid_texture=False
    )
    hyb_res = render_kinematic_folio(
        folio_dict, output_dir=hyb_dir, folio_id="f01r", dpi=150, max_lines=3, hybrid_texture=True
    )

    assert hyb_res["contracts"]["glyph_bbox_iou"] >= 0.95
    assert hyb_res["hybrid_texture"]["passed"] is True
    assert hyb_res["hybrid_texture"]["centerline_iou"] >= 0.92

    # Verify PAGE XML coordinates are invariant between raw and hybrid renders
    raw_xml = (raw_dir / "f01r.xml").read_text(encoding="utf-8")
    hyb_xml = (hyb_dir / "f01r.xml").read_text(encoding="utf-8")
    # Strip LastChange timestamp line before comparing XML coordinate content
    raw_coords = [line for line in raw_xml.splitlines() if "LastChange" not in line]
    hyb_coords = [line for line in hyb_xml.splitlines() if "LastChange" not in line]
    assert raw_coords == hyb_coords

    # Test CLI `--approach kinematic --hybrid-texture`
    cli_out = tmp_path / "cli_hyb"
    runner = CliRunner()
    res = runner.invoke(
        main,
        [
            "render",
            "f01r",
            "--input-dir",
            "output-live",
            "--output-dir",
            str(cli_out),
            "--approach",
            "kinematic",
            "--hybrid-texture",
        ],
    )
    assert res.exit_code == 0, res.output
    report = json.loads((cli_out / "f01r_render_report.json").read_text(encoding="utf-8"))
    assert report["render_params"]["hybrid_texture"]["passed"] is True
