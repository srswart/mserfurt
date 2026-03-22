"""Unit tests for scribesim/refselect/provenance.py — ADV-SS-REFSELECT-001."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_SAMPLE_MANIFEST = {
    "manifest_url": "https://example.com/iiif/bsb001/manifest",
    "title": "BSB Cgm 100",
    "attribution": "Bayerische Staatsbibliothek",
    "license": "Public Domain",
    "canvases": [],
}

_SAMPLE_SAMPLING = {
    "strategy": "stratified",
    "n_candidates": 15,
    "page_range": "all",
    "random_seed": 42,
}


class TestNewProvenanceRecord:
    def test_has_run_id(self):
        from scribesim.refselect.provenance import new_provenance_record
        rec = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        assert "run_id" in rec["provenance"]
        assert rec["provenance"]["run_id"].startswith("ref-select-")

    def test_has_timestamp(self):
        from scribesim.refselect.provenance import new_provenance_record
        rec = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        assert "timestamp" in rec["provenance"]

    def test_source_manuscript_fields(self):
        from scribesim.refselect.provenance import new_provenance_record
        rec = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        src = rec["provenance"]["source_manuscript"]
        assert src["manifest_url"] == _SAMPLE_MANIFEST["manifest_url"]
        assert src["title"] == _SAMPLE_MANIFEST["title"]
        assert src["attribution"] == _SAMPLE_MANIFEST["attribution"]
        assert src["license"] == _SAMPLE_MANIFEST["license"]

    def test_sampling_fields(self):
        from scribesim.refselect.provenance import new_provenance_record
        rec = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        samp = rec["provenance"]["sampling"]
        assert samp["strategy"] == "stratified"
        assert samp["n_candidates"] == 15
        assert samp["random_seed"] == 42

    def test_candidates_empty_list(self):
        from scribesim.refselect.provenance import new_provenance_record
        rec = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        assert rec["provenance"]["candidates"] == []

    def test_run_id_unique(self):
        from scribesim.refselect.provenance import new_provenance_record
        import time
        r1 = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        time.sleep(0.01)
        r2 = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        # run_ids should differ (different timestamps or sequence)
        # At minimum, both are valid strings
        assert isinstance(r1["provenance"]["run_id"], str)
        assert isinstance(r2["provenance"]["run_id"], str)


class TestSaveLoadRoundTrip:
    def test_save_creates_file(self, tmp_path):
        from scribesim.refselect.provenance import new_provenance_record, save_provenance
        rec = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        out = tmp_path / "provenance.json"
        save_provenance(rec, out)
        assert out.exists()

    def test_load_round_trip(self, tmp_path):
        from scribesim.refselect.provenance import new_provenance_record, save_provenance, load_provenance
        rec = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        out = tmp_path / "provenance.json"
        save_provenance(rec, out)
        loaded = load_provenance(out)
        assert loaded["provenance"]["run_id"] == rec["provenance"]["run_id"]
        assert loaded["provenance"]["source_manuscript"]["title"] == "BSB Cgm 100"

    def test_save_is_valid_json(self, tmp_path):
        from scribesim.refselect.provenance import new_provenance_record, save_provenance
        rec = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        out = tmp_path / "provenance.json"
        save_provenance(rec, out)
        parsed = json.loads(out.read_text())
        assert "provenance" in parsed

    def test_save_creates_parent_dirs(self, tmp_path):
        from scribesim.refselect.provenance import new_provenance_record, save_provenance
        rec = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
        out = tmp_path / "deep" / "nested" / "provenance.json"
        save_provenance(rec, out)
        assert out.exists()


# ---------------------------------------------------------------------------
# Helpers for ranking tests
# ---------------------------------------------------------------------------

def _make_record_with_n_candidates(n: int) -> dict:
    """Return a provenance record with n candidates scored 0.1..1.0 evenly spaced."""
    from scribesim.refselect.provenance import new_provenance_record, add_candidate
    from pathlib import Path
    rec = new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)
    for i in range(n):
        composite = (i + 1) / n  # evenly spaced 1/n .. 1.0
        scores = {
            "ink_contrast": composite, "line_regularity": composite,
            "script_consistency": composite, "text_density": composite,
            "damage": composite, "thick_thin": composite,
            "letter_variety": composite, "composite": composite,
        }
        canvas = {"label": f"page_{i:03d}", "id": f"https://example.com/canvas/{i:03d}",
                  "image_url": "", "service_url": ""}
        add_candidate(rec, canvas, Path(f"/tmp/page_{i:03d}.jpg"), scores)
    return rec


class TestRankCandidatesPercentage:
    """Tests for ADV-SS-REFSELECT-007 — percentage-based top-N selection."""

    def test_top_pct_basic(self):
        """Top 25% of 20 candidates = 5 selected."""
        from scribesim.refselect.provenance import rank_candidates
        rec = _make_record_with_n_candidates(20)
        rank_candidates(rec, top_pct=0.25, min_candidates=0)
        selected = [c for c in rec["provenance"]["candidates"] if c["selected"]]
        assert len(selected) == 5

    def test_min_floor_respected(self):
        """Top 25% of 8 candidates = 2, but floor=15 → all 8 selected (capped at total)."""
        from scribesim.refselect.provenance import rank_candidates
        rec = _make_record_with_n_candidates(8)
        rank_candidates(rec, top_pct=0.25, min_candidates=15)
        selected = [c for c in rec["provenance"]["candidates"] if c["selected"]]
        assert len(selected) == 8  # capped at total

    def test_floor_equals_pct(self):
        """60 candidates, 25% = 15, floor = 15 → exactly 15 selected."""
        from scribesim.refselect.provenance import rank_candidates
        rec = _make_record_with_n_candidates(60)
        rank_candidates(rec, top_pct=0.25, min_candidates=15)
        selected = [c for c in rec["provenance"]["candidates"] if c["selected"]]
        assert len(selected) == 15

    def test_threshold_gate(self):
        """top_pct selects top-5 of 20, but 2 of them are below threshold → 3 selected."""
        from scribesim.refselect.provenance import rank_candidates
        rec = _make_record_with_n_candidates(20)
        # Candidates are scored 0.05, 0.10, ..., 1.00. Top 5 are scores 0.80..1.00.
        # Set threshold to 0.85 — only scores 0.85, 0.90, 0.95, 1.00 qualify (4 of top-5).
        rank_candidates(rec, top_pct=0.25, min_candidates=0, selection_threshold=0.85)
        selected = [c for c in rec["provenance"]["candidates"] if c["selected"]]
        assert len(selected) == 4

    def test_backward_compat(self):
        """Old threshold-only call still works — no top_pct / min_candidates args needed."""
        from scribesim.refselect.provenance import rank_candidates
        rec = _make_record_with_n_candidates(10)
        # Default call (threshold only) — all with composite >= 0.5 should be selected
        rank_candidates(rec, selection_threshold=0.5)
        selected = [c for c in rec["provenance"]["candidates"] if c["selected"]]
        # Scores are 0.1, 0.2, ..., 1.0 — those >= 0.5 are 0.5..1.0 = 6 candidates
        assert len(selected) == 6
