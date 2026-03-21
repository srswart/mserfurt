"""CLI tests for ScribeSim — ADV-SS-CLI-001.

Red tests: anything that invokes layout/render/groundtruth without --dry-run
will raise NotImplementedError (stubs) and fail until those advances land.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from scribesim.cli import main
from scribesim.hand.model import load_base, resolve

GOLDEN_F01R = Path(__file__).parent / "golden" / "f01r" / "folio.json"
HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def input_dir(tmp_path: Path) -> Path:
    """A temp directory with f01r.json and manifest.json from the golden fixture."""
    folio = json.loads(GOLDEN_F01R.read_text())
    (tmp_path / "f01r.json").write_text(json.dumps(folio))
    manifest = {
        "manuscript": {"shelfmark": "MS Erfurt Aug. 12°47", "folio_count": 1},
        "folios": [{"id": "f01r", "file": "f01r.json", "line_count": folio["metadata"]["line_count"]}],
        "gaps": [],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    return tmp_path


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# TestHelpCommands — basic CLI wiring (should pass immediately)
# ---------------------------------------------------------------------------

class TestHelpCommands:
    def test_root_help_exits_0(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0

    def test_render_help_exits_0(self, runner):
        result = runner.invoke(main, ["render", "--help"])
        assert result.exit_code == 0

    def test_render_batch_help_exits_0(self, runner):
        result = runner.invoke(main, ["render-batch", "--help"])
        assert result.exit_code == 0

    def test_hand_help_exits_0(self, runner):
        result = runner.invoke(main, ["hand", "--help"])
        assert result.exit_code == 0

    def test_groundtruth_help_exits_0(self, runner):
        result = runner.invoke(main, ["groundtruth", "--help"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# TestRenderValidation — input validation (should pass immediately)
# ---------------------------------------------------------------------------

class TestRenderValidation:
    def test_missing_folio_json_exits_nonzero(self, runner, tmp_path):
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(tmp_path),
        ])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_missing_manifest_exits_nonzero(self, runner, tmp_path):
        # folio JSON exists but no manifest
        shutil.copy(GOLDEN_F01R, tmp_path / "f01r.json")
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(tmp_path),
        ])
        assert result.exit_code != 0
        assert "manifest" in result.output.lower()

    def test_invalid_folio_id_exits_nonzero(self, runner, tmp_path):
        result = runner.invoke(main, [
            "render", "notafolio",
            "--input-dir", str(tmp_path),
        ])
        assert result.exit_code != 0

    def test_folio_id_normalised_with_leading_zero(self, runner, input_dir):
        # "1r" and "f01r" should both resolve to f01r.json
        result = runner.invoke(main, [
            "render", "1r",
            "--input-dir", str(input_dir),
            "--dry-run",
        ])
        assert result.exit_code == 0
        assert "f01r" in result.output

    def test_folio_id_with_f_prefix_accepted(self, runner, input_dir):
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--dry-run",
        ])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# TestRenderDryRun — --dry-run shows plan without rendering (should pass)
# ---------------------------------------------------------------------------

class TestRenderDryRun:
    def test_dry_run_exits_0(self, runner, input_dir):
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--dry-run",
        ])
        assert result.exit_code == 0, result.output

    def test_dry_run_shows_folio_id(self, runner, input_dir):
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--dry-run",
        ])
        assert "f01r" in result.output

    def test_dry_run_shows_line_count(self, runner, input_dir):
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--dry-run",
        ])
        assert "lines" in result.output
        assert "8" in result.output   # golden f01r has 8 lines

    def test_dry_run_shows_hand_params(self, runner, input_dir):
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--dry-run",
        ])
        assert "pressure" in result.output
        assert "ink" in result.output

    def test_dry_run_does_not_write_files(self, runner, input_dir, tmp_path):
        out = tmp_path / "render-out"
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--output-dir", str(out),
            "--dry-run",
        ])
        assert result.exit_code == 0
        assert not (out / "f01r.png").exists()
        assert not (out / "f01r_pressure.png").exists()


# ---------------------------------------------------------------------------
# TestRenderLive — actual render (RED: NotImplementedError from layout stub)
# ---------------------------------------------------------------------------

class TestRenderLive:
    def test_render_exits_0(self, runner, input_dir, tmp_path):
        """Full render should complete and exit 0 — RED until layout is implemented."""
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--output-dir", str(tmp_path / "out"),
        ])
        assert result.exit_code == 0, result.output

    def test_render_produces_png(self, runner, input_dir, tmp_path):
        """Render should write {folio_id}.png — RED until render is implemented."""
        out = tmp_path / "out"
        runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--output-dir", str(out),
        ])
        assert (out / "f01r.png").exists()

    def test_render_produces_heatmap(self, runner, input_dir, tmp_path):
        """Render should write {folio_id}_pressure.png — RED until render is implemented."""
        out = tmp_path / "out"
        runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--output-dir", str(out),
        ])
        assert (out / "f01r_pressure.png").exists()


# ---------------------------------------------------------------------------
# TestRenderBatch — batch processing (partial: dry-run passes, live is RED)
# ---------------------------------------------------------------------------

class TestRenderBatch:
    def test_batch_missing_manifest_exits_nonzero(self, runner, tmp_path):
        result = runner.invoke(main, [
            "render-batch",
            "--input-dir", str(tmp_path),
        ])
        assert result.exit_code != 0

    def test_batch_dry_run_exits_0(self, runner, input_dir):
        result = runner.invoke(main, [
            "render-batch",
            "--input-dir", str(input_dir),
            "--dry-run",
        ])
        assert result.exit_code == 0, result.output

    def test_batch_dry_run_lists_all_folios(self, runner, input_dir):
        result = runner.invoke(main, [
            "render-batch",
            "--input-dir", str(input_dir),
            "--dry-run",
        ])
        assert "f01r" in result.output

    def test_batch_dry_run_shows_hand_params(self, runner, input_dir):
        result = runner.invoke(main, [
            "render-batch",
            "--input-dir", str(input_dir),
            "--dry-run",
        ])
        assert "pressure" in result.output
        assert "ink" in result.output

    def test_batch_live_produces_png_per_folio(self, runner, input_dir, tmp_path):
        """Batch live render should write f01r.png — RED until render is implemented."""
        out = tmp_path / "out"
        runner.invoke(main, [
            "render-batch",
            "--input-dir", str(input_dir),
            "--output-dir", str(out),
        ])
        assert (out / "f01r.png").exists()


# ---------------------------------------------------------------------------
# TestHandShow — hand parameter inspection (should pass immediately)
# ---------------------------------------------------------------------------

class TestHandShow:
    def test_hand_show_exits_0(self, runner):
        result = runner.invoke(main, ["hand", "--show"])
        assert result.exit_code == 0, result.output

    def test_hand_show_prints_base_params(self, runner):
        result = runner.invoke(main, ["hand", "--show"])
        assert "base_pressure" in result.output
        assert "ink_density" in result.output  # v1 compat field in metadata
        assert "nib.angle_deg" in result.output
        assert "writing_speed" in result.output  # v1 compat field in metadata

    def test_hand_show_base_pressure_value(self, runner):
        result = runner.invoke(main, ["hand", "--show"])
        assert "0.72" in result.output   # base pressure from TOML

    def test_hand_show_folio_modifier_applied(self, runner):
        # f06r has pressure_base=0.84 and stroke_weight=1.15
        result = runner.invoke(main, ["hand", "--show", "--folio", "f06r"])
        assert result.exit_code == 0
        assert "0.84" in result.output
        assert "1.15" in result.output

    def test_hand_show_f04v_degraded_params(self, runner):
        # f04v is severely damaged: pressure=0.55, ink=0.52
        result = runner.invoke(main, ["hand", "--show", "--folio", "f04v"])
        assert "0.55" in result.output
        assert "0.52" in result.output

    def test_hand_show_f14r_irregular_vellum(self, runner):
        # f14r: wider x_height, slower writing
        result = runner.invoke(main, ["hand", "--show", "--folio", "f14r"])
        assert "42" in result.output      # x_height_px
        assert "0.82" in result.output    # writing_speed

    def test_hand_show_custom_toml(self, runner, tmp_path):
        # Custom TOML with minimal content
        toml_content = '[hand]\npressure_base = 0.99\n'
        toml_path = tmp_path / "test.toml"
        toml_path.write_text(toml_content)
        result = runner.invoke(main, [
            "hand", "--show", "--hand-toml", str(toml_path)
        ])
        assert result.exit_code == 0
        assert "0.99" in result.output


# ---------------------------------------------------------------------------
# TestGroundtruth — PAGE XML generation (RED: NotImplementedError from stub)
# ---------------------------------------------------------------------------

class TestGroundtruth:
    def test_groundtruth_help_exits_0(self, runner):
        result = runner.invoke(main, ["groundtruth", "--help"])
        assert result.exit_code == 0

    def test_groundtruth_exits_0(self, runner, tmp_path):
        """groundtruth command should complete — RED until groundtruth is implemented."""
        result = runner.invoke(main, [
            "groundtruth", "f01r",
            "--input-dir", str(tmp_path),
            "--output-dir", str(tmp_path),
        ])
        assert result.exit_code == 0, result.output

    def test_groundtruth_produces_xml(self, runner, tmp_path):
        """Should write f01r.xml — RED until groundtruth is implemented."""
        runner.invoke(main, [
            "groundtruth", "f01r",
            "--input-dir", str(tmp_path),
            "--output-dir", str(tmp_path),
        ])
        assert (tmp_path / "f01r.xml").exists()


# ---------------------------------------------------------------------------
# TestHandModel — unit tests for hand model directly (should pass)
# ---------------------------------------------------------------------------

class TestHandModel:
    def test_load_base_returns_hand_params(self):
        from scribesim.hand.params import HandParams
        base = load_base(HAND_TOML)
        assert isinstance(base, HandParams)

    def test_base_has_required_fields(self):
        base = load_base(HAND_TOML)
        for attr in ("pressure_base", "ink_density", "nib_angle_deg",
                     "writing_speed", "x_height_px", "script"):
            assert hasattr(base, attr), f"missing field: {attr}"

    def test_resolve_with_no_modifier(self):
        base = load_base(HAND_TOML)
        params = resolve(base, "f01r")
        assert params.pressure_base == pytest.approx(0.72)
        assert params.ink_density == pytest.approx(0.85)

    def test_resolve_applies_f06r_modifier(self):
        base = load_base(HAND_TOML)
        params = resolve(base, "f06r")
        assert params.pressure_base == pytest.approx(0.84)
        assert params.stroke_weight == pytest.approx(1.15)

    def test_resolve_applies_f04v_modifier(self):
        base = load_base(HAND_TOML)
        params = resolve(base, "f04v")
        assert params.pressure_base == pytest.approx(0.55)
        assert params.ink_density == pytest.approx(0.52)

    def test_resolve_preserves_unmodified_fields(self):
        base = load_base(HAND_TOML)
        params = resolve(base, "f06r")
        # nib_angle not in f06r modifier — should keep base value
        assert params.nib_angle_deg == pytest.approx(45.0)

    def test_script_is_bastarda(self):
        base = load_base(HAND_TOML)
        assert base.script == "bastarda"
