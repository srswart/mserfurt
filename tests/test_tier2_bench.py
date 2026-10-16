"""Integration and CLI tests for ADV-SS-HANDVALIDATE-027: Automated Tier-2
HTR/Distribution Bench (B1-HTR-CER, B2-ANGLE-EMD, B3-RHYTHM-ACF, B4-CONTRACTS),
`--approach kinematic` full-folio PNG/pressure/PAGE-XML export, and
Human Checkpoint #3 4-Folio Review Board.
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET

from click.testing import CliRunner
import pytest

from scribesim.cli import main
from scribesim.handvalidate.tier2_bench import (
    render_kinematic_folio,
    run_tier2_kinematic_bench,
)


def test_render_kinematic_folio_exports_png_heatmap_and_page_xml(tmp_path: Path) -> None:
    """`render_kinematic_folio` and `--approach kinematic` co-generate PNG, pressure map, and PAGE XML."""
    folio_dict = json.loads(Path("output-live/f01r.json").read_text(encoding="utf-8"))
    out_dir = tmp_path / "kinematic_f01r"
    res = render_kinematic_folio(
        folio_dict,
        output_dir=out_dir,
        folio_id="f01r",
        dpi=150,
        max_lines=4,
    )

    assert res["page_path"].exists()
    assert res["heatmap_path"].exists()
    assert res["xml_path"].exists()
    assert res["contracts"]["exact_character_coverage"] == 1.0
    assert res["contracts"]["glyph_bbox_iou"] >= 0.95
    assert res["contracts"]["pressure_dynamic_range"] >= 0.40

    # Verify PAGE XML structure (TextRegion -> TextLine -> Baseline, Word -> Glyph)
    tree = ET.parse(res["xml_path"])
    root = tree.getroot()
    xml_str = ET.tostring(root, encoding="unicode")
    assert "TextLine" in xml_str
    assert "Baseline" in xml_str
    assert "Word" in xml_str
    assert "Glyph" in xml_str


def test_tier2_automated_bench_b1_b2_b3_b4(tmp_path: Path) -> None:
    """Tier-2 automated bench passes B1-HTR-CER, B2-ANGLE-EMD, B3-RHYTHM-ACF, and B4-CONTRACTS across 4 proof folios."""
    bench_dir = tmp_path / "tier2_bench"
    report = run_tier2_kinematic_bench(
        folio_ids=("f01r", "f06r", "f07r", "f14r"),
        input_dir=Path("output-live"),
        out_dir=bench_dir,
        dpi=150,
        max_lines=4,
    )

    assert report["passed"] is True, f"Tier-2 bench failed: {report}"
    assert report["b1_htr_cer"]["passed"] is True
    assert report["b1_htr_cer"]["clean_cer"] <= 0.05
    assert report["b2_angle_emd"]["passed"] is True
    assert report["b3_rhythm_acf"]["passed"] is True
    assert report["b4_contracts"]["passed"] is True
    assert report["b4_contracts"]["weather_compatible"] is True
    assert len(report["folios"]) == 4


def test_validate_kinematic_cli_and_checkpoint_3_board(tmp_path: Path) -> None:
    """`scribesim validate-kinematic` and `scribesim render --approach kinematic` succeed via CLI."""
    runner = CliRunner()

    # 1. Test `scribesim render f01r --approach kinematic`
    render_out = tmp_path / "cli_render"
    r_res = runner.invoke(
        main,
        [
            "render",
            "f01r",
            "--input-dir",
            "output-live",
            "--output-dir",
            str(render_out),
            "--approach",
            "kinematic",
        ],
    )
    assert r_res.exit_code == 0, r_res.output
    assert (render_out / "f01r.png").exists()
    assert (render_out / "f01r_pressure.png").exists()
    assert (render_out / "f01r.xml").exists()

    # 2. Test `scribesim validate-kinematic`
    val_out = tmp_path / "cli_validate"
    v_res = runner.invoke(
        main,
        [
            "validate-kinematic",
            "--out-dir",
            str(val_out),
            "--max-lines",
            "3",
            "--dpi",
            "150",
        ],
    )
    assert v_res.exit_code == 0, v_res.output
    assert (val_out / "tier2_report.json").exists()
    assert (val_out / "checkpoint-3-folios" / "index.html").exists()
