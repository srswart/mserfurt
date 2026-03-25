from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from click.testing import CliRunner

from scribesim.cli import main
from scribesim.evo.genome import genome_from_guides
from scribesim.evo.renderer import render_word_from_genome


GOLDEN_F01R = Path(__file__).parent / "golden" / "f01r" / "folio.json"


def test_render_word_from_genome_can_return_matching_heatmap():
    genome = genome_from_guides("lich", x_height_mm=3.8)
    page_arr, heat_arr = render_word_from_genome(
        genome,
        dpi=100.0,
        nib_width_mm=0.7,
        return_heatmap=True,
        variation=0.0,
    )

    assert page_arr.shape[:2] == heat_arr.shape
    assert heat_arr.dtype == np.uint8
    assert heat_arr.max() > 0

    parchment = np.array([245, 238, 220], dtype=np.uint8)
    page_mask = np.any(page_arr != parchment, axis=2)
    heat_mask = heat_arr > 0

    page_rows, page_cols = np.where(page_mask)
    heat_rows, heat_cols = np.where(heat_mask)
    assert len(page_rows) > 0
    assert len(heat_rows) > 0
    assert abs(int(page_rows.min()) - int(heat_rows.min())) <= 2
    assert abs(int(page_rows.max()) - int(heat_rows.max())) <= 2
    assert abs(int(page_cols.min()) - int(heat_cols.min())) <= 2
    assert abs(int(page_cols.max()) - int(heat_cols.max())) <= 2


def test_evo_cli_report_records_evo_heatmap(tmp_path: Path):
    folio = json.loads(GOLDEN_F01R.read_text())
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "f01r.json").write_text(json.dumps(folio))
    (input_dir / "manifest.json").write_text(json.dumps({
        "manuscript": {"shelfmark": "MS Erfurt Aug. 12°47", "folio_count": 1},
        "folios": [{"id": "f01r", "file": "f01r.json", "line_count": folio["metadata"]["line_count"]}],
        "gaps": [],
    }))

    out_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(main, [
        "render", "f01r",
        "--input-dir", str(input_dir),
        "--output-dir", str(out_dir),
        "--approach", "evo",
        "--evo-quality", "balanced",
    ])

    assert result.exit_code == 0, result.output
    report = json.loads((out_dir / "f01r_render_report.json").read_text())
    assert report["page_renderer"] == "evo"
    assert report["heatmap_renderer"] == "evo"


def test_guided_cli_report_records_guided_renderers(tmp_path: Path):
    folio = json.loads(GOLDEN_F01R.read_text())
    folio["lines"] = folio["lines"][:2]
    folio["metadata"]["line_count"] = 2
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "f01r.json").write_text(json.dumps(folio))
    (input_dir / "manifest.json").write_text(json.dumps({
        "manuscript": {"shelfmark": "MS Erfurt Aug. 12°47", "folio_count": 1},
        "folios": [{"id": "f01r", "file": "f01r.json", "line_count": folio["metadata"]["line_count"]}],
        "gaps": [],
    }))

    out_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(main, [
        "render", "f01r",
        "--input-dir", str(input_dir),
        "--output-dir", str(out_dir),
        "--approach", "guided",
        "--guided-supersample", "5",
    ])

    assert result.exit_code == 0, result.output
    report = json.loads((out_dir / "f01r_render_report.json").read_text())
    assert report["page_renderer"] == "guided"
    assert report["heatmap_renderer"] == "guided"
    assert report["render_params"]["guided_supersample"] == 5
