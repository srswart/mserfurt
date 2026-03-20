"""Unit tests for the Weather CLI — ADV-WX-CLI-001.

RED phase: weather.cli and weather.profile are not yet implemented.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

HAND_TOML = Path(__file__).parent.parent / "shared" / "hands" / "konrad_erfurt_1457.toml"
PROFILE_TOML = Path(__file__).parent.parent / "shared" / "profiles" / "ms-erfurt-560yr.toml"
MANIFEST = Path(__file__).parent.parent / "output-live" / "manifest.json"
RENDER_OUTPUT = Path(__file__).parent.parent / "render-output"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli():
    from weather.cli import main
    return main


# ---------------------------------------------------------------------------
# TestHelp — all commands advertise their flags
# ---------------------------------------------------------------------------

class TestHelp:
    def test_main_help_exits_zero(self, runner, cli):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

    def test_main_help_lists_all_commands(self, runner, cli):
        result = runner.invoke(cli, ["--help"])
        for cmd in ("apply", "apply-batch", "preview", "catalog"):
            assert cmd in result.output, f"'{cmd}' not listed in --help output"

    def test_apply_help(self, runner, cli):
        result = runner.invoke(cli, ["apply", "--help"])
        assert result.exit_code == 0
        assert "--folio" in result.output
        assert "--output-dir" in result.output

    def test_apply_batch_help(self, runner, cli):
        result = runner.invoke(cli, ["apply-batch", "--help"])
        assert result.exit_code == 0

    def test_preview_help_shows_effect_flag(self, runner, cli):
        result = runner.invoke(cli, ["preview", "--help"])
        assert result.exit_code == 0
        assert "--effect" in result.output

    def test_catalog_help(self, runner, cli):
        result = runner.invoke(cli, ["catalog", "--help"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# TestFolioValidation — bad folio IDs are rejected cleanly
# ---------------------------------------------------------------------------

class TestFolioValidation:
    def test_invalid_folio_id_rejected(self, runner, cli, tmp_path):
        result = runner.invoke(cli, [
            "apply", "--folio", "f99z",
            "--input-dir", str(tmp_path),
            "--output-dir", str(tmp_path),
            "--dry-run",
        ])
        assert result.exit_code != 0
        assert "invalid" in result.output.lower() or "error" in result.output.lower()

    def test_folio_without_leading_f_normalised(self, runner, cli, tmp_path):
        """'1r' should be accepted and normalised to 'f01r'."""
        result = runner.invoke(cli, [
            "apply", "--folio", "1r",
            "--input-dir", str(tmp_path),
            "--output-dir", str(tmp_path),
            "--dry-run",
        ])
        # Should not fail with a validation error (may fail with missing file)
        assert "invalid folio" not in result.output.lower()


# ---------------------------------------------------------------------------
# TestProfileLoading — ms-erfurt-560yr.toml loads correctly
# ---------------------------------------------------------------------------

class TestProfileLoading:
    def test_profile_file_exists(self):
        assert PROFILE_TOML.exists(), f"Profile TOML not found: {PROFILE_TOML}"

    def test_profile_loads_without_error(self):
        from weather.profile import load_profile
        profile = load_profile(PROFILE_TOML)
        assert profile is not None

    def test_profile_has_meta_section(self):
        from weather.profile import load_profile
        profile = load_profile(PROFILE_TOML)
        assert profile.name
        assert profile.seed == 1457
        assert profile.age_years == 560

    def test_profile_has_substrate_section(self):
        from weather.profile import load_profile
        profile = load_profile(PROFILE_TOML)
        assert profile.substrate_standard is not None
        assert profile.substrate_irregular is not None

    def test_profile_has_ink_section(self):
        from weather.profile import load_profile
        profile = load_profile(PROFILE_TOML)
        assert profile.ink_fade is not None
        assert profile.ink_bleed is not None
        assert profile.ink_flake is not None

    def test_profile_has_damage_section(self):
        from weather.profile import load_profile
        profile = load_profile(PROFILE_TOML)
        assert profile.damage_water is not None
        assert profile.damage_missing_corner is not None

    def test_missing_profile_raises_helpful_error(self, runner, cli, tmp_path):
        bogus = tmp_path / "nonexistent.toml"
        result = runner.invoke(cli, [
            "--profile", str(bogus),
            "catalog",
            "--input-dir", str(tmp_path),
        ])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# TestApplyDryRun — apply command with --dry-run reports plan, no file writes
# ---------------------------------------------------------------------------

class TestApplyDryRun:
    def test_apply_dry_run_exits_zero(self, runner, cli, tmp_path):
        # Copy a known folio JSON into tmp_path to simulate input
        import shutil
        src = Path(__file__).parent / "golden" / "f01r" / "folio.json"
        shutil.copy(src, tmp_path / "f01r.json")
        (tmp_path / "manifest.json").write_text(json.dumps({
            "folios": [{"id": "f01r", "file": "f01r.json", "line_count": 8}]
        }))

        result = runner.invoke(cli, [
            "apply", "--folio", "f01r",
            "--input-dir", str(tmp_path),
            "--output-dir", str(tmp_path),
            "--dry-run",
        ])
        assert result.exit_code == 0, result.output

    def test_apply_dry_run_writes_no_files(self, runner, cli, tmp_path):
        import shutil
        src = Path(__file__).parent / "golden" / "f01r" / "folio.json"
        shutil.copy(src, tmp_path / "f01r.json")
        (tmp_path / "manifest.json").write_text(json.dumps({
            "folios": [{"id": "f01r", "file": "f01r.json", "line_count": 8}]
        }))

        before = set(tmp_path.iterdir())
        runner.invoke(cli, [
            "apply", "--folio", "f01r",
            "--input-dir", str(tmp_path),
            "--output-dir", str(tmp_path),
            "--dry-run",
        ])
        after = set(tmp_path.iterdir())
        new_files = after - before
        assert not any(f.suffix == ".png" for f in new_files), (
            f"Dry-run wrote PNG files: {new_files}"
        )

    def test_apply_dry_run_reports_profile(self, runner, cli, tmp_path):
        import shutil
        src = Path(__file__).parent / "golden" / "f01r" / "folio.json"
        shutil.copy(src, tmp_path / "f01r.json")
        (tmp_path / "manifest.json").write_text(json.dumps({
            "folios": [{"id": "f01r", "file": "f01r.json", "line_count": 8}]
        }))

        result = runner.invoke(cli, [
            "apply", "--folio", "f01r",
            "--input-dir", str(tmp_path),
            "--output-dir", str(tmp_path),
            "--dry-run",
        ])
        assert "f01r" in result.output


# ---------------------------------------------------------------------------
# TestCatalog — catalog command reads manifest and reports folio metadata
# ---------------------------------------------------------------------------

class TestCatalog:
    def _make_manifest(self, tmp_path, folios: list[dict]) -> Path:
        manifest = {"folios": folios}
        p = tmp_path / "manifest.json"
        p.write_text(json.dumps(manifest))
        return p

    def test_catalog_lists_folios(self, runner, cli, tmp_path):
        self._make_manifest(tmp_path, [
            {"id": "f01r", "file": "f01r.json", "line_count": 8},
            {"id": "f04r", "file": "f04r.json", "line_count": 10,
             "damage": ["water_damage"]},
        ])
        result = runner.invoke(cli, [
            "catalog", "--input-dir", str(tmp_path)
        ])
        assert result.exit_code == 0, result.output
        assert "f01r" in result.output
        assert "f04r" in result.output

    def test_catalog_flags_water_damage_folios(self, runner, cli, tmp_path):
        self._make_manifest(tmp_path, [
            {"id": "f04r", "file": "f04r.json", "line_count": 10,
             "damage": ["water_damage"]},
            {"id": "f04v", "file": "f04v.json", "line_count": 10,
             "damage": ["water_damage", "missing_corner"]},
        ])
        result = runner.invoke(cli, [
            "catalog", "--input-dir", str(tmp_path)
        ])
        assert result.exit_code == 0
        assert "water" in result.output.lower()

    def test_catalog_shows_irregular_stock_for_late_folios(self, runner, cli, tmp_path):
        self._make_manifest(tmp_path, [
            {"id": "f14r", "file": "f14r.json", "line_count": 6,
             "vellum_stock": "irregular"},
        ])
        result = runner.invoke(cli, [
            "catalog", "--input-dir", str(tmp_path)
        ])
        assert result.exit_code == 0
        assert "irregular" in result.output.lower() or "f14r" in result.output

    def test_catalog_missing_manifest_exits_with_error(self, runner, cli, tmp_path):
        result = runner.invoke(cli, [
            "catalog", "--input-dir", str(tmp_path)
        ])
        assert result.exit_code != 0
