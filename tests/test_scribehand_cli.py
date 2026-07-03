"""CLI tests for the TD-018 neural path and diagnostics.

Uses stub backends only (no torch / no network).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from scribesim.cli import main


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def input_dir(tmp_path: Path) -> Path:
    folio = {
        "id": "f01r",
        "recto_verso": "recto",
        "lines": [
            {"number": 1, "text": "und der schreiber", "register": "de", "annotations": []},
            {"number": 2, "text": "in dem jar", "register": "de", "annotations": []},
        ],
        "metadata": {"line_count": 2},
    }
    d = tmp_path / "in"
    d.mkdir()
    (d / "f01r.json").write_text(json.dumps(folio))
    (d / "manifest.json").write_text(json.dumps({
        "manuscript": {"shelfmark": "test", "folio_count": 1},
        "folios": [{"id": "f01r", "file": "f01r.json", "line_count": 2}],
        "gaps": [],
    }))
    return d


class TestGenerateWordCLI:
    def test_generates_png(self, runner, tmp_path: Path):
        out = tmp_path / "und.png"
        result = runner.invoke(main, [
            "generate-word", "und",
            "--backend", "stub-pil", "--seed", "3",
            "--out", str(out),
        ])
        assert result.exit_code == 0, result.output
        assert out.exists()
        assert (out.parent / "und_provenance.json").exists()

    def test_unknown_backend_fails(self, runner, tmp_path: Path):
        result = runner.invoke(main, [
            "generate-word", "und",
            "--backend", "no-such-backend",
            "--out", str(tmp_path / "x.png"),
        ])
        assert result.exit_code != 0


class TestRenderNeural:
    def test_render_neural_produces_outputs(self, runner, input_dir, tmp_path):
        out = tmp_path / "out"
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir),
            "--output-dir", str(out),
            "--approach", "neural",
            "--neural-backend", "stub-pil",
        ])
        assert result.exit_code == 0, result.output
        assert (out / "f01r.png").exists()
        assert (out / "f01r.xml").exists()
        assert (out / "f01r_render_report.json").exists()
        report = json.loads((out / "f01r_render_report.json").read_text())
        assert report["approach"] == "neural"
        assert report["neural"]["backend"] == "stub-pil"
        assert report["neural"]["words"] == 6

    def test_word_level_xml(self, runner, input_dir, tmp_path):
        out = tmp_path / "out"
        result = runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir), "--output-dir", str(out),
            "--approach", "neural", "--neural-backend", "stub-pil",
        ])
        assert result.exit_code == 0, result.output
        xml = (out / "f01r.xml").read_text()
        assert "<Word" in xml and "schreiber" in xml


class TestDiagPack:
    def test_packs_bundle(self, runner, input_dir, tmp_path):
        out = tmp_path / "out"
        runner.invoke(main, [
            "render", "f01r",
            "--input-dir", str(input_dir), "--output-dir", str(out),
            "--approach", "neural", "--neural-backend", "stub-pil",
            "--neural-diag-dir", str(tmp_path / "diag"),
        ])
        result = runner.invoke(main, [
            "diag-pack", str(tmp_path / "diag"),
            "--out", str(tmp_path / "bundle.zip"),
        ])
        assert result.exit_code == 0, result.output
        assert (tmp_path / "bundle.zip").exists()

        import zipfile
        names = zipfile.ZipFile(tmp_path / "bundle.zip").namelist()
        assert any(n.endswith("run.json") for n in names)


class TestCorpusCLI:
    def test_check_corpus_reports_gaps(self, runner, tmp_path, input_dir):
        # tiny corpus that cannot cover the XL inventory
        corpus = tmp_path / "corpus"
        from scribesim.handcorpus.manifest import CorpusManifest, CorpusSample
        m = CorpusManifest(samples=[CorpusSample(
            id="s1", image="images/s1.png", text="abc", tier="script_family",
            split="train", writer="w", source={},
        )])
        m.save(corpus / "manifest.json")
        charset = tmp_path / "charset_map.toml"
        charset.write_text("schema = 1\n[map]\n")

        result = runner.invoke(main, [
            "check-scribehand-corpus",
            "--manifest", str(corpus / "manifest.json"),
            "--charset-map", str(charset),
            "--folio-dir", str(input_dir),
            "--min-script-family", "1", "--min-anchor", "0",
        ])
        assert result.exit_code != 0        # charset gaps must fail loudly
        assert "missing" in result.output
