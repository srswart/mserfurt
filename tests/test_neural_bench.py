"""Tests for the TD-018 neural promotion gates (ADV-SS-HANDVALIDATE-007)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scribesim.handvalidate.neural_bench import (
    hog_embedding,
    style_distance,
    anti_font_check,
    cer_bands,
    acceptance_bands,
    load_neural_gates,
    run_neural_bench,
)
from scribesim.hand.profile import load_profile
from scribesim.scribehand.backends.stub import PILStubBackend
from scribesim.scribehand.generate import WordGenerator
from scribesim.scribehand.htr import StubScorer
from scribesim.scribehand.compose import compose_folio


def _blob(seed: int, w: int = 40, h: int = 24) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w), dtype=np.uint8)
    for _ in range(6):
        x, y = rng.integers(2, w - 6), rng.integers(2, h - 6)
        img[y:y + 4, x:x + 4] = 255
    return img


class TestHOGEmbedding:
    def test_identical_zero_distance(self):
        a = _blob(1)
        e1, e2 = hog_embedding(a), hog_embedding(a.copy())
        assert np.allclose(e1, e2)

    def test_distinct_images_nonzero_distance(self):
        d = style_distance([_blob(1)], [_blob(99)])
        assert d > 0.0

    def test_same_population_small_distance(self):
        gen = [_blob(i) for i in range(8)]
        d_same = style_distance(gen, gen)
        d_diff = style_distance(gen, [255 - _blob(i) for i in range(8)])
        assert d_same < d_diff


class TestAntiFont:
    def test_identical_instances_fail(self):
        words = {"und": [_blob(5), _blob(5)]}   # pixel-identical
        report = anti_font_check(words, max_ncc=0.995)
        assert not report["ok"]
        assert report["max_ncc"] >= 0.999

    def test_varied_instances_pass(self):
        words = {"und": [_blob(5), _blob(6)]}
        report = anti_font_check(words, max_ncc=0.995)
        assert report["ok"]

    def test_single_instances_skipped(self):
        report = anti_font_check({"und": [_blob(1)]}, max_ncc=0.995)
        assert report["ok"]
        assert report["pairs_checked"] == 0


class TestCERBands:
    def test_bands(self):
        provs = [
            {"htr_cer": 0.0, "verified": True},
            {"htr_cer": 0.04, "verified": True},
            {"htr_cer": 0.5, "verified": False},
        ]
        b = cer_bands(provs)
        assert b["verified_fraction"] == pytest.approx(2 / 3)
        assert b["cer_max"] == 0.5

    def test_unscored(self):
        b = cer_bands([{"text": "und"}])
        assert b["scored_words"] == 0


class TestAcceptanceBands:
    def test_self_reference_within_bands(self):
        page = np.full((400, 300, 3), 240, dtype=np.uint8)
        page[100:110, 50:250] = 30
        report = acceptance_bands(page, page, max_mean_distance=0.5)
        assert report["ok"]
        assert report["mean_distance"] <= 0.05


class TestBenchEndToEnd:
    def test_run_neural_bench_report(self, tmp_path: Path):
        folio = {
            "id": "f01r", "recto_verso": "recto",
            "lines": [
                {"number": 1, "text": "und der und", "register": "de", "annotations": []},
            ],
            "metadata": {"line_count": 1},
        }
        gen = WordGenerator(PILStubBackend(), cache_dir=tmp_path / "c")
        composed = compose_folio(folio, load_profile(None), gen,
                                 scorer=StubScorer("echo"), dpi=300)
        gates = load_neural_gates(None)
        report = run_neural_bench(
            composed, gates=gates,
            anchor_word_images=None, reference_page=None,
            out_dir=tmp_path / "bench",
        )
        d = report.to_dict()
        assert "cer" in d and "anti_font" in d and "style" in d and "acceptance" in d
        assert (tmp_path / "bench" / "metrics.json").exists()
        # CER gate passes with the echo scorer
        assert d["cer"]["ok"]

    def test_gates_toml_loads_defaults(self):
        gates = load_neural_gates(None)
        assert gates.cer_mean_max > 0
        assert gates.anti_font_max_ncc < 1.0


class TestBenchCLI:
    def test_bench_neural_cli(self, tmp_path: Path):
        import json as _json
        from click.testing import CliRunner
        from scribesim.cli import main

        folio = {
            "id": "f01r", "recto_verso": "recto",
            "lines": [{"number": 1, "text": "und der und", "register": "de",
                       "annotations": []}],
            "metadata": {"line_count": 1},
        }
        d = tmp_path / "in"
        d.mkdir()
        (d / "f01r.json").write_text(_json.dumps(folio))

        runner = CliRunner()
        result = runner.invoke(main, [
            "bench-neural", "f01r",
            "--input-dir", str(d),
            "--backend", "stub-pil",
            "--htr", "stub-echo",
            "--out-dir", str(tmp_path / "bench"),
        ])
        assert result.exit_code == 0, result.output
        metrics = _json.loads((tmp_path / "bench" / "metrics.json").read_text())
        assert metrics["cer"]["ok"] is True
        assert (tmp_path / "bench" / "run.json").exists()
        assert (tmp_path / "bench" / "sheets" / "f01r_page.png").exists()
