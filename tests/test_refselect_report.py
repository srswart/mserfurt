"""Unit tests for scribesim/refselect/report.py — ADV-SS-REFSELECT-004."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_jpeg(path: Path, color: int = 200) -> Path:
    arr = np.full((100, 80, 3), color, dtype=np.uint8)
    Image.fromarray(arr).save(path, format="JPEG")
    return path


def _sample_record(tmp_path: Path, n_candidates: int = 3) -> dict:
    from scribesim.refselect.provenance import new_provenance_record, add_candidate, rank_candidates

    manifest = {
        "manifest_url": "https://example.com/iiif/bsb001/manifest",
        "title": "BSB Cgm 100",
        "attribution": "Bayerische Staatsbibliothek",
        "license": "Public Domain",
        "canvases": [],
    }
    sampling = {"strategy": "stratified", "n_candidates": n_candidates,
                "page_range": "all", "random_seed": 42}
    rec = new_provenance_record(manifest, sampling)

    scores_good = {"ink_contrast": 0.9, "line_regularity": 0.85,
                   "script_consistency": 0.8, "text_density": 0.7,
                   "damage": 0.95, "thick_thin": 0.8, "letter_variety": 0.75,
                   "composite": 0.84}
    scores_bad = {"ink_contrast": 0.3, "line_regularity": 0.2,
                  "script_consistency": 0.4, "text_density": 0.1,
                  "damage": 0.3, "thick_thin": 0.2, "letter_variety": 0.15,
                  "composite": 0.25}

    for i in range(n_candidates):
        canvas = {"id": f"c{i}", "label": f"{i+1}r", "image_url": f"https://x/img{i}.jpg"}
        scores = scores_good if i == 0 else scores_bad
        img_path = _make_jpeg(tmp_path / f"{i+1}r.jpg")
        add_candidate(rec, canvas, img_path, scores)

    rank_candidates(rec, selection_threshold=0.75)
    return rec


# ---------------------------------------------------------------------------
# Tests: generate_html_report
# ---------------------------------------------------------------------------

class TestGenerateHtmlReport:
    def test_nonempty_html(self, tmp_path):
        from scribesim.refselect.report import generate_html_report
        rec = _sample_record(tmp_path)
        out = tmp_path / "report.html"
        generate_html_report(rec, tmp_path, out)
        html = out.read_text()
        assert len(html) > 100
        assert "<html" in html.lower()

    def test_contains_one_section_per_candidate(self, tmp_path):
        from scribesim.refselect.report import generate_html_report
        rec = _sample_record(tmp_path, n_candidates=3)
        out = tmp_path / "report.html"
        generate_html_report(rec, tmp_path, out)
        html = out.read_text()
        # Each candidate gets a card with its label
        assert "1r" in html
        assert "2r" in html
        assert "3r" in html

    def test_self_contained_no_external_urls(self, tmp_path):
        from scribesim.refselect.report import generate_html_report
        rec = _sample_record(tmp_path)
        out = tmp_path / "report.html"
        generate_html_report(rec, tmp_path, out)
        html = out.read_text()
        # No external http links (except manifest URL in metadata which is OK in text)
        import re
        # Check that src= and href= attributes don't point to http URLs
        external_srcs = re.findall(r'(?:src|href)=["\']https?://', html)
        assert len(external_srcs) == 0

    def test_contains_criterion_names(self, tmp_path):
        from scribesim.refselect.report import generate_html_report
        rec = _sample_record(tmp_path)
        out = tmp_path / "report.html"
        generate_html_report(rec, tmp_path, out)
        html = out.read_text()
        for criterion in ["ink_contrast", "line_regularity", "composite"]:
            assert criterion in html

    def test_selected_badge_present(self, tmp_path):
        from scribesim.refselect.report import generate_html_report
        rec = _sample_record(tmp_path)
        out = tmp_path / "report.html"
        generate_html_report(rec, tmp_path, out)
        html = out.read_text()
        assert "SELECTED" in html

    def test_rejected_badge_present(self, tmp_path):
        from scribesim.refselect.report import generate_html_report
        rec = _sample_record(tmp_path)
        out = tmp_path / "report.html"
        generate_html_report(rec, tmp_path, out)
        html = out.read_text()
        assert "REJECTED" in html

    def test_returns_path_and_file_exists(self, tmp_path):
        from scribesim.refselect.report import generate_html_report
        rec = _sample_record(tmp_path)
        out = tmp_path / "report.html"
        result = generate_html_report(rec, tmp_path, out)
        assert isinstance(result, Path)
        assert result.exists()

    def test_missing_image_handled_gracefully(self, tmp_path):
        from scribesim.refselect.report import generate_html_report
        rec = _sample_record(tmp_path)
        # Delete one image to simulate missing file
        for f in tmp_path.glob("*.jpg"):
            f.unlink()
            break
        out = tmp_path / "report.html"
        # Should not raise
        generate_html_report(rec, tmp_path, out)
        assert out.exists()
