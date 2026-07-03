"""Tests for scribesim.handcorpus — TD-018 training corpus assembly.

Covers: manifest schema + roundtrip, deterministic splits, charset coverage
gates, record-based corpus building (CATMuS-shaped records without the
`datasets` dependency), anchor-tier ingestion, and training-format export.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scribesim.handcorpus.manifest import (
    CorpusManifest,
    CorpusSample,
    assign_split,
)
from scribesim.handcorpus.charset import (
    check_charset_coverage,
    load_charset_map,
    xl_character_inventory,
)
from scribesim.handcorpus.builder import build_from_records
from scribesim.handcorpus.anchor import ingest_anchor_dir
from scribesim.handcorpus.gates import run_corpus_gates
from scribesim.handcorpus.export import export_training_format


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_png(path: Path, w: int = 40, h: int = 16) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.full((h, w), 255, dtype=np.uint8)
    arr[h // 2, :] = 0
    Image.fromarray(arr, "L").save(path)


def _sample(i: int, tier: str = "script_family", text: str = "und der",
            writer: str = "w1") -> CorpusSample:
    return CorpusSample(
        id=f"s{i:04d}",
        image=f"images/s{i:04d}.png",
        text=text,
        tier=tier,
        split=assign_split(f"s{i:04d}"),
        writer=writer,
        source={"dataset": "test"},
    )


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------

class TestManifest:
    def test_roundtrip(self, tmp_path: Path):
        m = CorpusManifest(samples=[_sample(i) for i in range(10)])
        p = tmp_path / "manifest.json"
        m.save(p)
        m2 = CorpusManifest.load(p)
        assert len(m2.samples) == 10
        assert m2.samples[0].text == "und der"
        assert m2.samples[0].tier == "script_family"

    def test_training_charset_derived(self):
        m = CorpusManifest(samples=[_sample(0, text="abc"), _sample(1, text="cde")])
        assert set(m.training_charset()) == {"a", "b", "c", "d", "e"}

    def test_split_deterministic(self):
        assert assign_split("sample-1") == assign_split("sample-1")

    def test_split_distribution(self):
        splits = [assign_split(f"s{i}") for i in range(2000)]
        train = splits.count("train") / len(splits)
        assert 0.80 < train < 0.97
        assert splits.count("val") > 0
        assert splits.count("heldout") > 0

    def test_rejects_unknown_tier(self):
        with pytest.raises(ValueError):
            CorpusSample(
                id="x", image="x.png", text="a", tier="bogus",
                split="train", writer="w", source={},
            )


# ---------------------------------------------------------------------------
# charset
# ---------------------------------------------------------------------------

class TestCharset:
    def test_xl_inventory_scans_folio_json(self, tmp_path: Path):
        folio = {"id": "f01r", "lines": [{"text": "ab ßc"}, {"text": "de"}]}
        (tmp_path / "f01r.json").write_text(json.dumps(folio))
        inv = xl_character_inventory(tmp_path)
        assert inv == {"a", "b", "c", "d", "e", "ß"}  # space excluded

    def test_charset_map_load(self, tmp_path: Path):
        p = tmp_path / "charset_map.toml"
        p.write_text('schema = 1\n[map]\n"\u00df" = "sz"\n')
        table = load_charset_map(p)
        assert table.map["ß"] == "sz"

    def test_coverage_pass(self, tmp_path: Path):
        p = tmp_path / "charset_map.toml"
        p.write_text('schema = 1\n[map]\n"\u00df" = "sz"\n')
        table = load_charset_map(p)
        report = check_charset_coverage(
            inventory={"a", "ß"}, table=table, training_charset="asz",
        )
        assert report.ok
        assert report.missing == []

    def test_coverage_fails_loudly_on_gap(self, tmp_path: Path):
        p = tmp_path / "charset_map.toml"
        p.write_text("schema = 1\n[map]\n")
        table = load_charset_map(p)
        report = check_charset_coverage(
            inventory={"a", "ø"}, table=table, training_charset="a",
        )
        assert not report.ok
        assert "ø" in report.missing

    def test_mapped_string_must_be_covered(self, tmp_path: Path):
        p = tmp_path / "charset_map.toml"
        p.write_text('schema = 1\n[map]\n"\u00df" = "sz"\n')
        table = load_charset_map(p)
        report = check_charset_coverage(
            inventory={"ß"}, table=table, training_charset="s",  # 'z' missing
        )
        assert not report.ok


# ---------------------------------------------------------------------------
# record-based building (CATMuS-shaped, no `datasets` dependency)
# ---------------------------------------------------------------------------

class TestBuildFromRecords:
    def _records(self):
        img = Image.fromarray(np.full((16, 64), 200, dtype=np.uint8), "L")
        return [
            {"im": img, "text": "und der schreiber",
             "script_type": "Bastarda", "century": 15,
             "language": "Middle High German", "shelfmark": "Cgm 100"},
            {"im": img, "text": "in dem jar",
             "script_type": "Cursiva", "century": 15,
             "language": "Latin", "shelfmark": "Cgm 628"},
            {"im": img, "text": "textualis line",
             "script_type": "Textualis", "century": 13,
             "language": "Latin", "shelfmark": "Clm 1"},
        ]

    def test_filters_by_script_and_century(self, tmp_path: Path):
        manifest = build_from_records(
            self._records(), out_dir=tmp_path,
            scripts=("bastarda", "cursiva", "hybrida"),
            centuries=(14, 15, 16),
        )
        assert len(manifest.samples) == 2
        texts = {s.text for s in manifest.samples}
        assert "textualis line" not in texts

    def test_writes_images_and_manifest(self, tmp_path: Path):
        manifest = build_from_records(
            self._records(), out_dir=tmp_path,
            scripts=("bastarda",), centuries=(15,),
        )
        assert len(manifest.samples) == 1
        s = manifest.samples[0]
        assert (tmp_path / s.image).exists()
        assert (tmp_path / "manifest.json").exists()
        assert s.tier == "script_family"
        assert s.writer == "Cgm 100"

    def test_max_lines_cap(self, tmp_path: Path):
        manifest = build_from_records(
            self._records(), out_dir=tmp_path,
            scripts=("bastarda", "cursiva"), centuries=(15,),
            max_lines=1,
        )
        assert len(manifest.samples) == 1


# ---------------------------------------------------------------------------
# anchor ingestion
# ---------------------------------------------------------------------------

class TestAnchorIngest:
    def test_ingest_labels_tsv(self, tmp_path: Path):
        src = tmp_path / "reviewed"
        _write_png(src / "w1.png")
        _write_png(src / "w2.png")
        (src / "labels.tsv").write_text(
            "w1.png\tund\tanchor_hand\nw2.png\tder\tanchor_hand\n"
        )
        out = tmp_path / "corpus"
        manifest = ingest_anchor_dir(src, out_dir=out)
        assert len(manifest.samples) == 2
        assert all(s.tier == "anchor" for s in manifest.samples)
        assert all((out / s.image).exists() for s in manifest.samples)

    def test_missing_image_fails(self, tmp_path: Path):
        src = tmp_path / "reviewed"
        src.mkdir()
        (src / "labels.tsv").write_text("missing.png\tund\tw\n")
        with pytest.raises(FileNotFoundError):
            ingest_anchor_dir(src, out_dir=tmp_path / "corpus")


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------

class TestGates:
    def test_gate_report_pass(self, tmp_path: Path):
        p = tmp_path / "charset_map.toml"
        p.write_text("schema = 1\n[map]\n")
        table = load_charset_map(p)
        m = CorpusManifest(samples=[
            _sample(i, text="und der ab") for i in range(20)
        ] + [_sample(100 + i, tier="anchor", text="und der ab") for i in range(5)])
        report = run_corpus_gates(
            m, table, xl_inventory={"u", "n", "d"},
            min_script_family=10, min_anchor=3,
        )
        assert report.ok
        d = report.to_dict()
        assert d["charset"]["ok"] and d["counts"]["ok"]

    def test_gate_fails_on_low_counts_and_charset(self, tmp_path: Path):
        p = tmp_path / "charset_map.toml"
        p.write_text("schema = 1\n[map]\n")
        table = load_charset_map(p)
        m = CorpusManifest(samples=[_sample(0, text="und")])
        report = run_corpus_gates(
            m, table, xl_inventory={"u", "ø"},
            min_script_family=10, min_anchor=3,
        )
        assert not report.ok
        assert not report.charset.ok
        assert not report.counts_ok


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

class TestExport:
    def test_generic_export(self, tmp_path: Path):
        corpus = tmp_path / "corpus"
        for i in range(3):
            _write_png(corpus / f"images/s{i:04d}.png")
        m = CorpusManifest(samples=[_sample(i) for i in range(3)])
        m.save(corpus / "manifest.json")

        out = tmp_path / "export"
        export_training_format(corpus / "manifest.json", out, fmt="generic")
        labels = (out / "labels.tsv").read_text().strip().splitlines()
        assert len(labels) == 3
        cols = labels[0].split("\t")
        assert len(cols) == 5  # id, image path, text, writer, split
        assert (out / "charset.txt").exists()
