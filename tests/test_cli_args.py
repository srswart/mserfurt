"""Tests for xl CLI argument parsing and subcommand dispatch.

Follows TDD red-green discipline: these tests were written before implementation.
Verifies argument handling only — no LLM or filesystem side effects.
"""

import os
import tempfile

import pytest
from click.testing import CliRunner

from xl.__main__ import main


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def source_file(tmp_path):
    """A minimal stand-in for the annotated source manuscript."""
    f = tmp_path / "ms-erfurt-source-annotated.md"
    f.write_text("# test source\n")
    return str(f)


@pytest.fixture()
def output_dir(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    return str(out)


# ---------------------------------------------------------------------------
# translate subcommand
# ---------------------------------------------------------------------------

class TestTranslateArgs:
    def test_translate_dry_run_exits_zero(self, runner, source_file, output_dir):
        result = runner.invoke(main, ["translate", "--input", source_file, "--output", output_dir, "--dry-run"])
        assert result.exit_code == 0

    def test_translate_dry_run_skips_pipeline(self, runner, source_file, output_dir):
        result = runner.invoke(main, ["translate", "--input", source_file, "--output", output_dir, "--dry-run"])
        assert "dry-run" in result.output.lower()
        assert "pipeline stages skipped" in result.output.lower()

    def test_translate_missing_input_fails(self, runner, output_dir):
        result = runner.invoke(main, ["translate", "--output", output_dir, "--dry-run"])
        assert result.exit_code != 0

    def test_translate_nonexistent_input_fails(self, runner, output_dir):
        result = runner.invoke(main, ["translate", "--input", "/nonexistent/path.md", "--output", output_dir])
        assert result.exit_code != 0

    def test_translate_folio_flag_accepted(self, runner, source_file, output_dir):
        result = runner.invoke(main, ["translate", "--input", source_file, "--output", output_dir, "--folio", "7r", "--dry-run"])
        assert result.exit_code == 0
        assert "7r" in result.output

    def test_translate_missing_output_fails(self, runner, source_file):
        result = runner.invoke(main, ["translate", "--input", source_file, "--dry-run"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# manifest subcommand
# ---------------------------------------------------------------------------

class TestManifestArgs:
    def test_manifest_with_existing_dir_exits_zero(self, runner, output_dir):
        result = runner.invoke(main, ["manifest", output_dir])
        assert result.exit_code == 0

    def test_manifest_with_nonexistent_dir_fails(self, runner):
        result = runner.invoke(main, ["manifest", "/nonexistent/output"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# validate subcommand
# ---------------------------------------------------------------------------

class TestValidateArgs:
    def test_validate_with_existing_dir_exits_zero(self, runner, output_dir):
        result = runner.invoke(main, ["validate", output_dir])
        assert result.exit_code == 0

    def test_validate_with_nonexistent_dir_fails(self, runner):
        result = runner.invoke(main, ["validate", "/nonexistent/output"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# preview subcommand
# ---------------------------------------------------------------------------

class TestPreviewArgs:
    def test_preview_with_existing_file_exits_zero(self, runner, tmp_path):
        folio = tmp_path / "f07r.json"
        folio.write_text('{"id": "f07r"}')
        result = runner.invoke(main, ["preview", str(folio)])
        assert result.exit_code == 0

    def test_preview_with_nonexistent_file_fails(self, runner):
        result = runner.invoke(main, ["preview", "/nonexistent/f99r.json"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# top-level --help
# ---------------------------------------------------------------------------

class TestHelp:
    def test_help_exits_zero(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "translate" in result.output
        assert "manifest" in result.output
        assert "validate" in result.output
        assert "preview" in result.output

    def test_translate_help_exits_zero(self, runner):
        result = runner.invoke(main, ["translate", "--help"])
        assert result.exit_code == 0
        assert "--input" in result.output
        assert "--output" in result.output
        assert "--dry-run" in result.output
        assert "--folio" in result.output
