"""Unit tests for provenance chain writer — ADV-SS-REFSELECT-005 Part B."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest


def _sample_record():
    from scribesim.refselect.provenance import new_provenance_record, add_candidate, rank_candidates
    manifest = {"manifest_url": "https://x", "title": "Cgm 100",
                "attribution": "BSB", "license": "PD", "canvases": []}
    sampling = {"strategy": "stratified", "n_candidates": 3,
                "page_range": "all", "random_seed": 42}
    rec = new_provenance_record(manifest, sampling)
    for i, composite in enumerate([0.85, 0.90]):
        canvas = {"id": f"c{i}", "label": f"{i+1}r", "image_url": f"https://x/img{i}.jpg"}
        scores = {"ink_contrast": composite, "composite": composite}
        add_candidate(rec, canvas, Path(f"{i+1}r.jpg"), scores)
    rank_candidates(rec, selection_threshold=0.75)
    return rec


class TestWriteProvenanceChain:
    def test_creates_jsonl_file(self, tmp_path):
        from scribesim.refselect.provenance import write_provenance_chain
        rec = _sample_record()
        crops = [
            {"char": "a", "index": 0, "canvas_label": "1r", "filename": "bsb001_1r_a_000.png"},
            {"char": "b", "index": 1, "canvas_label": "2r", "filename": "bsb001_2r_b_001.png"},
        ]
        out = tmp_path / "provenance_chain.jsonl"
        write_provenance_chain(crops, rec, out)
        assert out.exists()

    def test_each_line_is_valid_json(self, tmp_path):
        from scribesim.refselect.provenance import write_provenance_chain
        rec = _sample_record()
        crops = [
            {"char": "a", "index": 0, "canvas_label": "1r", "filename": "f_1r_a_000.png"},
        ]
        out = tmp_path / "chain.jsonl"
        write_provenance_chain(crops, rec, out)
        lines = out.read_text().strip().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert isinstance(parsed, dict)

    def test_required_fields_present(self, tmp_path):
        from scribesim.refselect.provenance import write_provenance_chain
        rec = _sample_record()
        crops = [
            {"char": "a", "index": 0, "canvas_label": "1r", "filename": "f_1r_a_000.png"},
        ]
        out = tmp_path / "chain.jsonl"
        write_provenance_chain(crops, rec, out)
        entry = json.loads(out.read_text().strip())
        assert "crop_file" in entry
        assert "canvas_label" in entry
        assert "run_id" in entry
        assert "composite_score" in entry

    def test_run_id_matches_record(self, tmp_path):
        from scribesim.refselect.provenance import write_provenance_chain
        rec = _sample_record()
        crops = [{"char": "x", "index": 0, "canvas_label": "1r", "filename": "f.png"}]
        out = tmp_path / "chain.jsonl"
        write_provenance_chain(crops, rec, out)
        entry = json.loads(out.read_text().strip())
        assert entry["run_id"] == rec["provenance"]["run_id"]


class TestTaggedCropName:
    def test_contains_canvas_label(self):
        from scribesim.refselect.provenance import tagged_crop_name
        name = tagged_crop_name(canvas_label="5r", char="a", index=3)
        assert "5r" in name

    def test_contains_char(self):
        from scribesim.refselect.provenance import tagged_crop_name
        name = tagged_crop_name(canvas_label="5r", char="m", index=0)
        assert "m" in name

    def test_ends_with_png(self):
        from scribesim.refselect.provenance import tagged_crop_name
        name = tagged_crop_name(canvas_label="1r", char="a", index=0)
        assert name.endswith(".png")

    def test_index_zero_padded(self):
        from scribesim.refselect.provenance import tagged_crop_name
        name = tagged_crop_name(canvas_label="1r", char="a", index=7)
        assert "007" in name
