"""Unit tests for extended provenance functions (human approval + citation) — ADV-SS-REFSELECT-004."""

from __future__ import annotations

from pathlib import Path

import pytest


def _record_with_candidates():
    from scribesim.refselect.provenance import new_provenance_record, add_candidate, rank_candidates

    manifest = {
        "manifest_url": "https://daten.digitale-sammlungen.de/bsb001/manifest",
        "title": "BSB Cgm 100",
        "attribution": "Bayerische Staatsbibliothek München",
        "license": "Public Domain",
        "canvases": [],
    }
    sampling = {"strategy": "stratified", "n_candidates": 4,
                "page_range": "all", "random_seed": 42}
    rec = new_provenance_record(manifest, sampling)

    for i, composite in enumerate([0.85, 0.30, 0.78, 0.20]):
        canvas = {"id": f"c{i}", "label": f"{i+1}r", "image_url": ""}
        scores = {"ink_contrast": composite, "line_regularity": composite,
                  "composite": composite}
        add_candidate(rec, canvas, Path(f"{i+1}r.jpg"), scores)

    rank_candidates(rec, selection_threshold=0.75)
    return rec


class TestApplyHumanApproval:
    def test_sets_selected_true_for_approved(self):
        from scribesim.refselect.provenance import apply_human_approval
        rec = _record_with_candidates()
        apply_human_approval(rec, approved=["2r"], notes="Good page despite low score")
        c2 = next(c for c in rec["provenance"]["candidates"] if c["canvas_label"] == "2r")
        assert c2["selected"] is True

    def test_overrides_auto_rejection(self):
        from scribesim.refselect.provenance import apply_human_approval
        rec = _record_with_candidates()
        # 2r was rejected automatically (composite=0.30)
        c2_before = next(c for c in rec["provenance"]["candidates"] if c["canvas_label"] == "2r")
        assert c2_before["selected"] is False
        apply_human_approval(rec, approved=["2r"], notes="Override")
        c2_after = next(c for c in rec["provenance"]["candidates"] if c["canvas_label"] == "2r")
        assert c2_after["selected"] is True

    def test_records_human_approved_flag(self):
        from scribesim.refselect.provenance import apply_human_approval
        rec = _record_with_candidates()
        apply_human_approval(rec, approved=["1r"], notes="")
        c1 = next(c for c in rec["provenance"]["candidates"] if c["canvas_label"] == "1r")
        assert c1.get("human_approved") is True

    def test_records_notes(self):
        from scribesim.refselect.provenance import apply_human_approval
        rec = _record_with_candidates()
        apply_human_approval(rec, approved=["1r"], notes="Excellent contrast")
        c1 = next(c for c in rec["provenance"]["candidates"] if c["canvas_label"] == "1r")
        assert c1.get("human_notes") == "Excellent contrast"

    def test_non_approved_candidates_deselected(self):
        from scribesim.refselect.provenance import apply_human_approval
        rec = _record_with_candidates()
        # 1r and 3r were auto-selected; explicitly approve only 1r
        apply_human_approval(rec, approved=["1r"], notes="")
        c3 = next(c for c in rec["provenance"]["candidates"] if c["canvas_label"] == "3r")
        # 3r not in approved list → human override sets to False
        assert c3["selected"] is False


class TestCiteProvenance:
    def test_bibtex_contains_title(self):
        from scribesim.refselect.provenance import cite_provenance
        rec = _record_with_candidates()
        citation = cite_provenance(rec, fmt="bibtex")
        assert "BSB Cgm 100" in citation

    def test_bibtex_contains_url(self):
        from scribesim.refselect.provenance import cite_provenance
        rec = _record_with_candidates()
        citation = cite_provenance(rec, fmt="bibtex")
        assert "daten.digitale-sammlungen.de" in citation

    def test_bibtex_format_markers(self):
        from scribesim.refselect.provenance import cite_provenance
        rec = _record_with_candidates()
        citation = cite_provenance(rec, fmt="bibtex")
        assert citation.strip().startswith("@")
        assert "title" in citation.lower()

    def test_chicago_contains_attribution(self):
        from scribesim.refselect.provenance import cite_provenance
        rec = _record_with_candidates()
        citation = cite_provenance(rec, fmt="chicago")
        assert "Bayerische Staatsbibliothek" in citation

    def test_chicago_contains_title(self):
        from scribesim.refselect.provenance import cite_provenance
        rec = _record_with_candidates()
        citation = cite_provenance(rec, fmt="chicago")
        assert "BSB Cgm 100" in citation

    def test_unknown_format_raises(self):
        from scribesim.refselect.provenance import cite_provenance
        rec = _record_with_candidates()
        with pytest.raises(ValueError):
            cite_provenance(rec, fmt="mla")
