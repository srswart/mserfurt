"""CLI tests for ScribeSim — ADV-SS-CLI-001.

Red tests: anything that invokes layout/render/groundtruth without --dry-run
will raise NotImplementedError (stubs) and fail until those advances land.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from scribesim.cli import main, _evo_min_line_box_height_mm
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

    def test_build_exemplar_corpus_help_exits_0(self, runner):
        result = runner.invoke(main, ["build-exemplar-corpus", "--help"])
        assert result.exit_code == 0

    def test_build_exemplar_corpus_help_mentions_clean(self, runner):
        result = runner.invoke(main, ["build-exemplar-corpus", "--help"])
        assert "--clean / --no-clean" in result.output

    def test_build_reviewed_coverage_ledger_help_exits_0(self, runner):
        result = runner.invoke(main, ["build-reviewed-coverage-ledger", "--help"])
        assert result.exit_code == 0

    def test_annotate_reviewed_exemplars_help_exits_0(self, runner):
        result = runner.invoke(main, ["annotate-reviewed-exemplars", "--help"])
        assert result.exit_code == 0

    def test_freeze_reviewed_exemplars_help_exits_0(self, runner):
        result = runner.invoke(main, ["freeze-reviewed-exemplars", "--help"])
        assert result.exit_code == 0

    def test_evofit_reviewed_exemplars_help_exits_0(self, runner):
        result = runner.invoke(main, ["evofit-reviewed-exemplars", "--help"])
        assert result.exit_code == 0


class TestExemplarCorpusCli:
    def test_build_exemplar_corpus_cli_shows_progress_and_summary(self, runner, tmp_path):
        selection_manifest = tmp_path / "selection_manifest.toml"
        selection_manifest.write_text(
            """
schema_version = 1
manifest_path = "shared/training/handsim/exemplar_harvest_v1/manifest.toml"

[[folios]]
canvas_label = "001r"
source_manuscript_label = "Fixture"
local_path = "folio.png"
"""
        )
        output_dir = tmp_path / "out"
        summary_md = output_dir / "summary.md"
        manifest_path = output_dir / "manifest.toml"

        def _fake_build(selection_manifest_path, output_root, progress_callback=None):
            if progress_callback is not None:
                progress_callback({"stage": "setup", "status": "started", "percent_complete": 0.0})
                progress_callback(
                    {
                        "stage": "initial_scan",
                        "status": "running",
                        "percent_complete": 50.0,
                        "pass_label": "initial_scan",
                        "folios_completed": 1,
                        "folios_total": 2,
                        "canvas_label": "001r",
                    }
                )
                progress_callback({"stage": "write_reports", "status": "completed", "percent_complete": 100.0})
            Path(output_root).mkdir(parents=True, exist_ok=True)
            summary_md.write_text("# summary\n")
            manifest_path.write_text('dataset_id = "active-review-exemplars-v1"\n')
            return {
                "summary": {
                    "dataset_id": "active-review-exemplars-v1",
                    "auto_admitted_glyph_coverage": 0.5,
                    "auto_admitted_join_coverage": 0.25,
                    "repair_only_glyph_coverage": 0.1,
                    "repair_only_join_coverage": 0.2,
                    "heldout_symbol_coverage": 0.2,
                },
                "summary_md_path": summary_md,
                "manifest_path": manifest_path,
            }

        with patch("scribesim.refextract.build_exemplar_corpus", side_effect=_fake_build):
            result = runner.invoke(
                main,
                [
                    "build-exemplar-corpus",
                    "--selection-manifest",
                    str(selection_manifest),
                    "--output",
                    str(output_dir),
                ],
            )

        assert result.exit_code == 0, result.output
        assert "Progress →" in result.output
        assert "progress:" in result.output
        assert "Dataset: active-review-exemplars-v1" in result.output

    def test_build_exemplar_corpus_cli_clean_removes_stale_output(self, runner, tmp_path):
        selection_manifest = tmp_path / "selection_manifest.toml"
        selection_manifest.write_text(
            """
schema_version = 1
manifest_path = "shared/training/handsim/exemplar_harvest_v1/manifest.toml"

[[folios]]
canvas_label = "001r"
source_manuscript_label = "Fixture"
local_path = "folio.png"
"""
        )
        output_dir = tmp_path / "out"
        output_dir.mkdir(parents=True, exist_ok=True)
        stale = output_dir / "stale.txt"
        stale.write_text("old")

        def _fake_build(selection_manifest_path, output_root, progress_callback=None):
            assert not stale.exists()
            Path(output_root).mkdir(parents=True, exist_ok=True)
            summary_md = Path(output_root) / "summary.md"
            manifest_path = Path(output_root) / "manifest.toml"
            summary_md.write_text("# summary\n")
            manifest_path.write_text('dataset_id = "active-review-exemplars-v1"\n')
            return {
                "summary": {
                    "dataset_id": "active-review-exemplars-v1",
                    "auto_admitted_glyph_coverage": 0.5,
                    "auto_admitted_join_coverage": 0.25,
                    "repair_only_glyph_coverage": 0.1,
                    "repair_only_join_coverage": 0.2,
                    "heldout_symbol_coverage": 0.2,
                },
                "summary_md_path": summary_md,
                "manifest_path": manifest_path,
            }

        with patch("scribesim.refextract.build_exemplar_corpus", side_effect=_fake_build):
            result = runner.invoke(
                main,
                [
                    "build-exemplar-corpus",
                    "--selection-manifest",
                    str(selection_manifest),
                    "--output",
                    str(output_dir),
                    "--clean",
                ],
            )

        assert result.exit_code == 0, result.output
        assert not stale.exists()

    def test_build_reviewed_coverage_ledger_cli_reports_outputs(self, runner, tmp_path):
        corpus_manifest = tmp_path / "manifest.toml"
        corpus_manifest.write_text('dataset_id = "active-review-exemplars-v1"\n')
        output_dir = tmp_path / "ledger"
        ledger_md = output_dir / "coverage_ledger.md"
        ledger_manifest = output_dir / "coverage_ledger_manifest.toml"

        def _fake_build(corpus_manifest_path, output_root, reviewed_manifest_path=None):
            Path(output_root).mkdir(parents=True, exist_ok=True)
            ledger_md.write_text("# ledger\n")
            ledger_manifest.write_text('stage_id = "reviewed-coverage-ledger"\n')
            return {
                "summary": {
                    "glyph_promoted_coverage": 0.1,
                    "join_promoted_coverage": 0.2,
                    "glyph_reviewed_coverage": 0.0,
                    "join_reviewed_coverage": 0.0,
                },
                "ledger_md_path": ledger_md,
                "ledger_manifest_path": ledger_manifest,
            }

        with patch("scribesim.annotate.build_reviewed_coverage_ledger", side_effect=_fake_build):
            result = runner.invoke(
                main,
                [
                    "build-reviewed-coverage-ledger",
                    "--corpus-manifest",
                    str(corpus_manifest),
                    "--output",
                    str(output_dir),
                ],
            )

        assert result.exit_code == 0, result.output
        assert "Stage: reviewed-coverage-ledger" in result.output
        assert "Glyph promoted coverage: 0.1000" in result.output
        assert "Ledger →" in result.output

    def test_annotate_reviewed_exemplars_cli_reports_url(self, runner, tmp_path):
        ledger_path = tmp_path / "coverage_ledger.json"
        ledger_path.write_text("{}")
        output_dir = tmp_path / "reviewed"

        class _FakeServer:
            def __init__(self, **kwargs):
                self.url = "http://127.0.0.1:8765"
                self.workbench = type(
                    "WB",
                    (),
                    {
                        "reviewed_manifest_path": output_dir / "reviewed_manifest.toml",
                        "coverage_ledger_path": ledger_path,
                        "selection_manifest_path": tmp_path / "selection_manifest.toml",
                    },
                )()

            def serve_forever(self):
                raise KeyboardInterrupt()

            def shutdown(self):
                return None

        with patch("scribesim.annotate.AnnotationWorkbenchServer", _FakeServer):
            result = runner.invoke(
                main,
                [
                    "annotate-reviewed-exemplars",
                    "--coverage-ledger",
                    str(ledger_path),
                    "--output",
                    str(output_dir),
                ],
            )

        assert result.exit_code == 0, result.output
        assert "Stage: reviewed-annotation-workbench" in result.output
        assert "URL: http://127.0.0.1:8765" in result.output
        assert "Reviewed manifest →" in result.output

    def test_freeze_reviewed_exemplars_cli_reports_outputs(self, runner, tmp_path):
        reviewed_manifest = tmp_path / "reviewed_manifest.toml"
        reviewed_manifest.write_text('entry_count = 0\n')
        output_dir = tmp_path / "frozen"
        summary_md = output_dir / "summary.md"
        manifest_path = output_dir / "reviewed_exemplar_manifest.toml"

        def _fake_freeze(reviewed_manifest_path, output_root):
            Path(output_root).mkdir(parents=True, exist_ok=True)
            summary_md.write_text("# summary\n")
            manifest_path.write_text('manifest_kind = "reviewed_exemplars"\n')
            return {
                "summary": {
                    "reviewed_glyph_count": 1,
                    "reviewed_join_count": 1,
                    "downstream_smoke_passed": True,
                },
                "summary_md_path": summary_md,
                "manifest_path": manifest_path,
            }

        with patch("scribesim.annotate.freeze_reviewed_exemplars", side_effect=_fake_freeze):
            result = runner.invoke(
                main,
                [
                    "freeze-reviewed-exemplars",
                    "--reviewed-manifest",
                    str(reviewed_manifest),
                    "--output",
                    str(output_dir),
                ],
            )

        assert result.exit_code == 0, result.output
        assert "Stage: reviewed-exemplar-freeze" in result.output
        assert "Reviewed glyph count: 1" in result.output
        assert "Downstream smoke test: PASS" in result.output

    def test_freeze_reviewed_evofit_guides_cli_reports_outputs(self, runner, tmp_path):
        evofit_manifest = tmp_path / "manifest.toml"
        evofit_manifest.write_text('schema_version = 1\n')
        output_dir = tmp_path / "promoted"
        report_md = output_dir / "coverage_provenance_report.md"
        validation_md = output_dir / "validation_report.md"
        guide_catalog_path = tmp_path / "reviewed_promoted_v1.toml"

        def _fake_freeze(reviewed_evofit_manifest_path, output_root, guide_catalog_path):
            Path(output_root).mkdir(parents=True, exist_ok=True)
            report_md.write_text("# report\n")
            validation_md.write_text("# validation\n")
            Path(guide_catalog_path).write_text('schema_version = 1\n')
            return {
                "summary": {
                    "guide_count": 2,
                    "exact_symbol_coverage": 1.0,
                    "validation_gate_passed": True,
                },
                "guide_catalog_path": Path(guide_catalog_path),
                "coverage_provenance_report_md_path": report_md,
                "validation_report_md_path": validation_md,
            }

        with patch("scribesim.pathguide.freeze_reviewed_evofit_guides", side_effect=_fake_freeze):
            result = runner.invoke(
                main,
                [
                    "freeze-reviewed-evofit-guides",
                    "--evofit-manifest",
                    str(evofit_manifest),
                    "--output",
                    str(output_dir),
                    "--guide-catalog",
                    str(guide_catalog_path),
                ],
            )

        assert result.exit_code == 0, result.output
        assert "Stage: reviewed-evofit-guide-freeze" in result.output
        assert "Guide count: 2" in result.output
        assert "Exact symbol coverage: 1.0000" in result.output
        assert "Validation gate: PASS" in result.output

    def test_validate_reviewed_nominal_guides_cli_reports_outputs(self, runner, tmp_path):
        evofit_manifest = tmp_path / "manifest.toml"
        evofit_manifest.write_text('schema_version = 1\n')
        guide_catalog = tmp_path / "reviewed_promoted_v1.toml"
        guide_catalog.write_text('schema_version = 1\n')
        output_dir = tmp_path / "nominal"
        dashboard_md = output_dir / "dashboard.md"
        report_md = output_dir / "reviewed_nominal.md"

        def _fake_validate(reviewed_evofit_manifest_path, promoted_guide_catalog_path, output_root):
            Path(output_root).mkdir(parents=True, exist_ok=True)
            dashboard_md.write_text("# dashboard\n")
            report_md.write_text("# report\n")
            return {
                "summary_metrics": {
                    "raw_nominal_mean_score": 0.41,
                    "cleaned_nominal_mean_score": 0.57,
                    "guided_mean_score": 0.52,
                },
                "dashboard_md_path": dashboard_md,
                "stage_report_md_path": report_md,
            }

        with patch("scribesim.handvalidate.run_reviewed_nominal_validation", side_effect=_fake_validate):
            result = runner.invoke(
                main,
                [
                    "validate-reviewed-nominal-guides",
                    "--evofit-manifest",
                    str(evofit_manifest),
                    "--guide-catalog",
                    str(guide_catalog),
                    "--output",
                    str(output_dir),
                ],
            )

        assert result.exit_code == 0, result.output
        assert "Stage: reviewed-nominal-validation" in result.output
        assert "Raw nominal mean score: 0.4100" in result.output
        assert "Cleaned nominal mean score: 0.5700" in result.output
        assert "Guided mean score: 0.5200" in result.output


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
        assert "progress" in result.output

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

    def test_dry_run_accepts_deep_evo_quality(self, runner, input_dir):
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--approach", "evo",
            "--evo-quality", "deep",
            "--dry-run",
        ])
        assert result.exit_code == 0, result.output
        assert "deep" in result.output

    def test_dry_run_accepts_deep_character_model(self, runner, input_dir):
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--approach", "evo",
            "--character-model", "deep",
            "--char-rounds", "1",
            "--char-candidates", "2",
            "--dry-run",
        ])
        assert result.exit_code == 0, result.output
        assert "chars : deep" in result.output


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

    def test_batch_dry_run_accepts_deep_evo_quality(self, runner, input_dir):
        result = runner.invoke(main, [
            "render-batch",
            "--input-dir", str(input_dir),
            "--approach", "evo",
            "--evo-quality", "deep",
            "--dry-run",
        ])
        assert result.exit_code == 0, result.output
        assert "deep" in result.output

    def test_batch_dry_run_accepts_guided_approach(self, runner, input_dir):
        result = runner.invoke(main, [
            "render-batch",
            "--input-dir", str(input_dir),
            "--approach", "guided",
            "--guided-supersample", "5",
            "--dry-run",
        ])
        assert result.exit_code == 0, result.output
        assert "guided_supersample=5" in result.output
        assert "exact_symbols=True" in result.output

    def test_batch_dry_run_accepts_guided_substitution_debug_flag(self, runner, input_dir):
        result = runner.invoke(main, [
            "render-batch",
            "--input-dir", str(input_dir),
            "--approach", "guided",
            "--no-guided-exact-symbols",
            "--dry-run",
        ])
        assert result.exit_code == 0, result.output
        assert "exact_symbols=False" in result.output

    def test_batch_dry_run_accepts_deep_character_model(self, runner, input_dir):
        result = runner.invoke(main, [
            "render-batch",
            "--input-dir", str(input_dir),
            "--approach", "evo",
            "--character-model", "deep",
            "--char-rounds", "1",
            "--char-candidates", "2",
            "--dry-run",
        ])
        assert result.exit_code == 0, result.output
        assert "chars=deep" in result.output


class TestExperimentalLineAndSample:
    def test_evo_min_line_box_height_leaves_descender_room(self):
        assert _evo_min_line_box_height_mm(3.8) == pytest.approx(13.68)

    def test_render_line_accepts_deep_character_model(self, runner, tmp_path):
        out = tmp_path / "line.png"
        result = runner.invoke(main, [
            "render-line", "ich bin",
            "--output", str(out),
            "--evolve",
            "--generations", "2",
            "--pop-size", "3",
            "--character-model", "deep",
            "--char-rounds", "1",
            "--char-candidates", "2",
        ])
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_render_sample_writes_page_and_heatmap(self, runner, tmp_path):
        out = tmp_path / "sample.png"
        result = runner.invoke(main, [
            "render-sample",
            "--line", "ich bin",
            "--line", "ein schreiber",
            "--output", str(out),
            "--no-evolve",
            "--character-model", "standard",
        ])
        assert result.exit_code == 0, result.output
        assert out.exists()
        assert (tmp_path / "sample_pressure.png").exists()

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
        # nib_angle not in f06r modifier — should keep base value (40° for Thuringian Bastarda)
        assert params.nib_angle_deg == pytest.approx(40.0)

    def test_script_is_bastarda(self):
        base = load_base(HAND_TOML)
        assert base.script == "bastarda"
