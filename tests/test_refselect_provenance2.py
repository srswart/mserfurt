"""Unit tests for extended provenance functions — ADV-SS-REFSELECT-002."""

from __future__ import annotations

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

_CANVAS = {
    "id": "https://example.com/iiif/bsb001/canvas/p5",
    "label": "5r",
    "image_url": "https://example.com/images/bsb001_p5.jpg",
    "service_url": "https://example.com/iiif/image/bsb001_p5",
}

_SCORES_LOW = {"ink_contrast": 0.4, "line_regularity": 0.5, "composite": 0.45}
_SCORES_HIGH = {"ink_contrast": 0.9, "line_regularity": 0.85, "composite": 0.875}


def _fresh_record():
    from scribesim.refselect.provenance import new_provenance_record
    return new_provenance_record(_SAMPLE_MANIFEST, _SAMPLE_SAMPLING)


class TestAddCandidate:
    def test_appends_to_candidates(self, tmp_path):
        from scribesim.refselect.provenance import add_candidate
        rec = _fresh_record()
        add_candidate(rec, _CANVAS, tmp_path / "5r.jpg", _SCORES_LOW)
        assert len(rec["provenance"]["candidates"]) == 1

    def test_candidate_has_required_fields(self, tmp_path):
        from scribesim.refselect.provenance import add_candidate
        rec = _fresh_record()
        add_candidate(rec, _CANVAS, tmp_path / "5r.jpg", _SCORES_LOW)
        entry = rec["provenance"]["candidates"][0]
        assert "canvas_label" in entry
        assert "canvas_id" in entry
        assert "scores" in entry
        assert "rank" in entry
        assert "selected" in entry

    def test_rank_and_selected_initially_null(self, tmp_path):
        from scribesim.refselect.provenance import add_candidate
        rec = _fresh_record()
        add_candidate(rec, _CANVAS, tmp_path / "5r.jpg", _SCORES_LOW)
        entry = rec["provenance"]["candidates"][0]
        assert entry["rank"] is None
        assert entry["selected"] is None

    def test_scores_stored(self, tmp_path):
        from scribesim.refselect.provenance import add_candidate
        rec = _fresh_record()
        add_candidate(rec, _CANVAS, tmp_path / "5r.jpg", _SCORES_LOW)
        assert rec["provenance"]["candidates"][0]["scores"]["composite"] == _SCORES_LOW["composite"]


class TestRankCandidates:
    def _record_with_two(self, tmp_path):
        from scribesim.refselect.provenance import add_candidate
        rec = _fresh_record()
        canvas_a = dict(_CANVAS, id="c1", label="1r")
        canvas_b = dict(_CANVAS, id="c2", label="2r")
        add_candidate(rec, canvas_a, tmp_path / "1r.jpg", _SCORES_LOW)
        add_candidate(rec, canvas_b, tmp_path / "2r.jpg", _SCORES_HIGH)
        return rec

    def test_rank_values_are_sequential(self, tmp_path):
        from scribesim.refselect.provenance import rank_candidates
        rec = self._record_with_two(tmp_path)
        rank_candidates(rec)
        ranks = sorted(c["rank"] for c in rec["provenance"]["candidates"])
        assert ranks == [1, 2]

    def test_highest_composite_gets_rank_1(self, tmp_path):
        from scribesim.refselect.provenance import rank_candidates
        rec = self._record_with_two(tmp_path)
        rank_candidates(rec)
        top = next(c for c in rec["provenance"]["candidates"] if c["rank"] == 1)
        assert top["scores"]["composite"] == _SCORES_HIGH["composite"]

    def test_selection_flag_above_threshold(self, tmp_path):
        from scribesim.refselect.provenance import rank_candidates
        rec = self._record_with_two(tmp_path)
        rank_candidates(rec, selection_threshold=0.75)
        high = next(c for c in rec["provenance"]["candidates"]
                    if c["scores"]["composite"] == _SCORES_HIGH["composite"])
        assert high["selected"] is True

    def test_selection_flag_below_threshold(self, tmp_path):
        from scribesim.refselect.provenance import rank_candidates
        rec = self._record_with_two(tmp_path)
        rank_candidates(rec, selection_threshold=0.75)
        low = next(c for c in rec["provenance"]["candidates"]
                   if c["scores"]["composite"] == _SCORES_LOW["composite"])
        assert low["selected"] is False


class TestUpdateProvenance:
    def test_round_trip(self, tmp_path):
        from scribesim.refselect.provenance import (
            add_candidate, rank_candidates, update_provenance, load_provenance,
        )
        rec = _fresh_record()
        add_candidate(rec, _CANVAS, tmp_path / "5r.jpg", _SCORES_HIGH)
        rank_candidates(rec)
        out = tmp_path / "provenance.json"
        update_provenance(rec, out)
        loaded = load_provenance(out)
        assert loaded["provenance"]["candidates"][0]["rank"] == 1

    def test_overwrites_existing_file(self, tmp_path):
        from scribesim.refselect.provenance import (
            add_candidate, rank_candidates, update_provenance, load_provenance, save_provenance,
        )
        rec = _fresh_record()
        out = tmp_path / "provenance.json"
        save_provenance(rec, out)
        add_candidate(rec, _CANVAS, tmp_path / "5r.jpg", _SCORES_HIGH)
        rank_candidates(rec)
        update_provenance(rec, out)
        loaded = load_provenance(out)
        assert len(loaded["provenance"]["candidates"]) == 1
