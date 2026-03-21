"""Unit tests for parameter tuning CLI — ADV-SS-TUNING-001."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from click.testing import CliRunner

from scribesim.cli import main
from scribesim.tuning.compare import compare_images, format_report
from scribesim.tuning.diff import generate_diff
from scribesim.tuning.report import generate_report
from scribesim.hand.profile import load_profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BG = np.array([245, 238, 220], dtype=np.uint8)
_INK = np.array([18, 12, 8], dtype=np.uint8)


def _make_test_png(path: Path, h: int = 100, w: int = 150, stripe_y: int = 40) -> Path:
    img = np.full((h, w, 3), _BG, dtype=np.uint8)
    img[stripe_y:stripe_y + 10, 15:w - 15, :] = _INK
    Image.fromarray(img, "RGB").save(str(path), format="PNG")
    return path


def _make_different_png(path: Path, h: int = 100, w: int = 150) -> Path:
    img = np.full((h, w, 3), _BG, dtype=np.uint8)
    img[50:65, 20:w - 20, :] = _INK  # different position and thickness
    Image.fromarray(img, "RGB").save(str(path), format="PNG")
    return path


@pytest.fixture
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# TestCompare
# ---------------------------------------------------------------------------

class TestCompare:
    def test_compare_identical(self, tmp_path):
        img = _make_test_png(tmp_path / "a.png")
        results, score = compare_images(img, img)
        assert len(results) == 9
        assert score < 0.05

    def test_compare_different(self, tmp_path):
        a = _make_test_png(tmp_path / "a.png")
        b = _make_different_png(tmp_path / "b.png")
        results, score = compare_images(a, b)
        assert score > 0.01

    def test_format_report_has_all_ids(self, tmp_path):
        img = _make_test_png(tmp_path / "a.png")
        results, score = compare_images(img, img)
        text = format_report(results, score)
        for mid in ("M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9"):
            assert mid in text
        assert "COMPOSITE" in text

    def test_compare_cli_exits_0(self, runner, tmp_path):
        a = _make_test_png(tmp_path / "a.png")
        b = _make_test_png(tmp_path / "b.png")
        result = runner.invoke(main, ["compare", str(a), "--target", str(b)])
        assert result.exit_code == 0, result.output
        assert "M1" in result.output
        assert "COMPOSITE" in result.output


# ---------------------------------------------------------------------------
# TestDiff
# ---------------------------------------------------------------------------

class TestDiff:
    def test_diff_produces_image(self, tmp_path):
        a = _make_test_png(tmp_path / "a.png")
        b = _make_different_png(tmp_path / "b.png")
        out = generate_diff(a, b, tmp_path / "diff.png")
        assert out.exists()

    def test_diff_correct_dimensions(self, tmp_path):
        a = _make_test_png(tmp_path / "a.png")
        b = _make_different_png(tmp_path / "b.png")
        out = generate_diff(a, b, tmp_path / "diff.png")
        img = Image.open(out)
        assert img.size == (150, 100)

    def test_diff_identical_is_blue(self, tmp_path):
        a = _make_test_png(tmp_path / "a.png")
        out = generate_diff(a, a, tmp_path / "diff.png")
        img = np.array(Image.open(out))
        # All blue (no difference)
        assert img[:, :, 0].max() == 0  # no red
        assert img[:, :, 2].min() == 255  # all blue

    def test_diff_cli_exits_0(self, runner, tmp_path):
        a = _make_test_png(tmp_path / "a.png")
        b = _make_different_png(tmp_path / "b.png")
        out = tmp_path / "diff.png"
        result = runner.invoke(main, ["diff", str(a), str(b), "-o", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()


# ---------------------------------------------------------------------------
# TestReport
# ---------------------------------------------------------------------------

class TestReport:
    def test_report_produces_html(self, tmp_path):
        a = _make_test_png(tmp_path / "a.png")
        b = _make_test_png(tmp_path / "b.png")
        results, score = compare_images(a, b)
        out = generate_report(a, b, results, score, tmp_path / "report.html")
        assert out.exists()
        html = out.read_text()
        assert "ScribeSim Comparison Report" in html
        assert "M1" in html
        assert "Composite Score" in html

    def test_report_contains_images(self, tmp_path):
        a = _make_test_png(tmp_path / "a.png")
        b = _make_test_png(tmp_path / "b.png")
        results, score = compare_images(a, b)
        out = generate_report(a, b, results, score, tmp_path / "report.html")
        html = out.read_text()
        assert "data:image/png;base64," in html

    def test_report_cli_exits_0(self, runner, tmp_path):
        a = _make_test_png(tmp_path / "a.png")
        b = _make_test_png(tmp_path / "b.png")
        out = tmp_path / "report.html"
        result = runner.invoke(main, ["report", str(a), "--target", str(b),
                                      "-o", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()


# ---------------------------------------------------------------------------
# TestPresets
# ---------------------------------------------------------------------------

class TestPresets:
    def test_formal_preset_loads(self):
        preset_path = Path(__file__).parent.parent / "shared" / "hands" / "presets" / "bastarda_formal.toml"
        profile = load_profile(preset_path)
        assert profile.nib.angle_deg == pytest.approx(40.0)
        assert profile.folio.tremor_amplitude == pytest.approx(0.0)

    def test_hasty_preset_loads(self):
        preset_path = Path(__file__).parent.parent / "shared" / "hands" / "presets" / "bastarda_hasty.toml"
        profile = load_profile(preset_path)
        assert profile.nib.angle_deg == pytest.approx(42.0)

    def test_fatigued_preset_loads(self):
        preset_path = Path(__file__).parent.parent / "shared" / "hands" / "presets" / "bastarda_fatigued.toml"
        profile = load_profile(preset_path)
        assert profile.folio.tremor_amplitude > 0.0

    def test_presets_differ(self):
        base = Path(__file__).parent.parent / "shared" / "hands" / "presets"
        formal = load_profile(base / "bastarda_formal.toml")
        hasty = load_profile(base / "bastarda_hasty.toml")
        assert formal.folio.base_pressure != hasty.folio.base_pressure
