"""Unit tests for scribesim/refselect/iiif.py — ADV-SS-REFSELECT-001.

All tests use in-process fixture manifests — no live network calls.
Network integration tests are marked @pytest.mark.network and skipped by default.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixture manifests
# ---------------------------------------------------------------------------

# Minimal IIIF Presentation v2 manifest (BSB-style)
_MANIFEST_V2 = {
    "@context": "http://iiif.io/api/presentation/2/context.json",
    "@id": "https://example.com/iiif/bsb001/manifest",
    "@type": "sc:Manifest",
    "label": "BSB Cgm 100",
    "attribution": "Bayerische Staatsbibliothek",
    "license": "Public Domain",
    "sequences": [
        {
            "@type": "sc:Sequence",
            "canvases": [
                {
                    "@id": f"https://example.com/iiif/bsb001/canvas/p{i}",
                    "label": f"{i}r",
                    "images": [
                        {
                            "resource": {
                                "@id": f"https://example.com/images/bsb001_p{i}.jpg",
                                "service": {
                                    "@id": f"https://example.com/iiif/image/bsb001_p{i}",
                                },
                            }
                        }
                    ],
                }
                for i in range(1, 21)  # 20 pages
            ],
        }
    ],
}

# Minimal IIIF Presentation v3 manifest
_MANIFEST_V3 = {
    "@context": "http://iiif.io/api/presentation/3/context.json",
    "id": "https://example.com/iiif/bsb002/manifest",
    "type": "Manifest",
    "label": {"en": ["BSB Cgm 200"]},
    "rights": "http://creativecommons.org/licenses/publicdomain/",
    "items": [
        {
            "id": f"https://example.com/iiif/bsb002/canvas/p{i}",
            "type": "Canvas",
            "label": {"none": [f"{i}v"]},
            "items": [
                {
                    "type": "AnnotationPage",
                    "items": [
                        {
                            "type": "Annotation",
                            "motivation": "painting",
                            "body": {
                                "id": f"https://example.com/images/bsb002_p{i}.jpg",
                                "type": "Image",
                                "service": [
                                    {
                                        "id": f"https://example.com/iiif/image/bsb002_p{i}",
                                        "type": "ImageService3",
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }
        for i in range(1, 16)  # 15 pages
    ],
}


# ---------------------------------------------------------------------------
# Tests: fetch_manifest
# ---------------------------------------------------------------------------

class TestFetchManifest:
    def _mock_get(self, manifest_dict):
        mock_resp = MagicMock()
        mock_resp.json.return_value = manifest_dict
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def test_fetch_manifest_v2_canvas_count(self):
        from scribesim.refselect.iiif import fetch_manifest
        with patch("requests.get", return_value=self._mock_get(_MANIFEST_V2)):
            result = fetch_manifest("https://example.com/iiif/bsb001/manifest")
        assert len(result["canvases"]) == 20

    def test_fetch_manifest_v2_title(self):
        from scribesim.refselect.iiif import fetch_manifest
        with patch("requests.get", return_value=self._mock_get(_MANIFEST_V2)):
            result = fetch_manifest("https://example.com/iiif/bsb001/manifest")
        assert result["title"] == "BSB Cgm 100"

    def test_fetch_manifest_v2_attribution(self):
        from scribesim.refselect.iiif import fetch_manifest
        with patch("requests.get", return_value=self._mock_get(_MANIFEST_V2)):
            result = fetch_manifest("https://example.com/iiif/bsb001/manifest")
        assert result["attribution"] == "Bayerische Staatsbibliothek"

    def test_fetch_manifest_v2_service_url(self):
        from scribesim.refselect.iiif import fetch_manifest
        with patch("requests.get", return_value=self._mock_get(_MANIFEST_V2)):
            result = fetch_manifest("https://example.com/iiif/bsb001/manifest")
        canvas = result["canvases"][0]
        assert "service_url" in canvas
        assert "bsb001_p1" in canvas["service_url"]

    def test_fetch_manifest_v2_canvas_label(self):
        from scribesim.refselect.iiif import fetch_manifest
        with patch("requests.get", return_value=self._mock_get(_MANIFEST_V2)):
            result = fetch_manifest("https://example.com/iiif/bsb001/manifest")
        assert result["canvases"][0]["label"] == "1r"

    def test_fetch_manifest_v3_canvas_count(self):
        from scribesim.refselect.iiif import fetch_manifest
        with patch("requests.get", return_value=self._mock_get(_MANIFEST_V3)):
            result = fetch_manifest("https://example.com/iiif/bsb002/manifest")
        assert len(result["canvases"]) == 15

    def test_fetch_manifest_v3_title(self):
        from scribesim.refselect.iiif import fetch_manifest
        with patch("requests.get", return_value=self._mock_get(_MANIFEST_V3)):
            result = fetch_manifest("https://example.com/iiif/bsb002/manifest")
        assert result["title"] == "BSB Cgm 200"

    def test_fetch_manifest_v3_service_url(self):
        from scribesim.refselect.iiif import fetch_manifest
        with patch("requests.get", return_value=self._mock_get(_MANIFEST_V3)):
            result = fetch_manifest("https://example.com/iiif/bsb002/manifest")
        canvas = result["canvases"][0]
        assert "service_url" in canvas
        assert "bsb002_p1" in canvas["service_url"]

    def test_fetch_manifest_stores_manifest_url(self):
        from scribesim.refselect.iiif import fetch_manifest
        url = "https://example.com/iiif/bsb001/manifest"
        with patch("requests.get", return_value=self._mock_get(_MANIFEST_V2)):
            result = fetch_manifest(url)
        assert result["manifest_url"] == url


# ---------------------------------------------------------------------------
# Tests: select_candidate_pages
# ---------------------------------------------------------------------------

class TestSelectCandidatePages:
    def _manifest(self, n=20):
        m = dict(_MANIFEST_V2)
        m["sequences"][0]["canvases"] = [
            {"@id": f"c{i}", "label": f"{i}r", "images": [{"resource": {"@id": f"img{i}", "service": {}}}]}
            for i in range(1, n + 1)
        ]
        return m

    def _normalised(self, n=20):
        from scribesim.refselect.iiif import fetch_manifest
        raw = self._manifest(n)
        with patch("requests.get", return_value=MagicMock(json=MagicMock(return_value=raw), raise_for_status=MagicMock())):
            return fetch_manifest("http://x")

    def test_stratified_count(self):
        from scribesim.refselect.iiif import select_candidate_pages
        manifest = self._normalised(20)
        result = select_candidate_pages(manifest, n_candidates=5, strategy="stratified")
        assert len(result) == 5

    def test_stratified_in_bounds(self):
        from scribesim.refselect.iiif import select_candidate_pages
        manifest = self._normalised(20)
        result = select_candidate_pages(manifest, n_candidates=5, strategy="stratified")
        labels = {c["label"] for c in manifest["canvases"]}
        for c in result:
            assert c["label"] in labels

    def test_stratified_no_duplicates(self):
        from scribesim.refselect.iiif import select_candidate_pages
        manifest = self._normalised(20)
        result = select_candidate_pages(manifest, n_candidates=10, strategy="stratified")
        ids = [c["id"] for c in result]
        assert len(ids) == len(set(ids))

    def test_random_reproducible(self):
        from scribesim.refselect.iiif import select_candidate_pages
        manifest = self._normalised(20)
        r1 = select_candidate_pages(manifest, n_candidates=5, strategy="random", seed=42)
        r2 = select_candidate_pages(manifest, n_candidates=5, strategy="random", seed=42)
        assert [c["label"] for c in r1] == [c["label"] for c in r2]

    def test_random_different_seeds(self):
        from scribesim.refselect.iiif import select_candidate_pages
        manifest = self._normalised(20)
        r1 = select_candidate_pages(manifest, n_candidates=5, strategy="random", seed=1)
        r2 = select_candidate_pages(manifest, n_candidates=5, strategy="random", seed=99)
        # With 20 pages and 5 samples, different seeds almost certainly differ
        assert [c["label"] for c in r1] != [c["label"] for c in r2]

    def test_text_pages_only_skips_ends(self):
        from scribesim.refselect.iiif import select_candidate_pages
        manifest = self._normalised(20)
        result = select_candidate_pages(manifest, n_candidates=5, strategy="text_pages_only")
        all_labels = [c["label"] for c in manifest["canvases"]]
        skip_labels = set(all_labels[:3] + all_labels[-3:])
        for c in result:
            assert c["label"] not in skip_labels

    def test_n_candidates_capped_at_total(self):
        from scribesim.refselect.iiif import select_candidate_pages
        manifest = self._normalised(5)
        result = select_candidate_pages(manifest, n_candidates=20, strategy="random")
        assert len(result) == 5


# ---------------------------------------------------------------------------
# Tests: sanitize_filename
# ---------------------------------------------------------------------------

class TestSanitizeFilename:
    def test_strips_slashes(self):
        from scribesim.refselect.iiif import sanitize_filename
        assert "/" not in sanitize_filename("f01/r")

    def test_strips_spaces(self):
        from scribesim.refselect.iiif import sanitize_filename
        result = sanitize_filename("folio 5r")
        assert " " not in result

    def test_max_64_chars(self):
        from scribesim.refselect.iiif import sanitize_filename
        assert len(sanitize_filename("x" * 100)) <= 64

    def test_non_empty(self):
        from scribesim.refselect.iiif import sanitize_filename
        assert len(sanitize_filename("5r")) > 0

    def test_unicode_normalised(self):
        from scribesim.refselect.iiif import sanitize_filename
        # Should not crash on accented chars
        result = sanitize_filename("Fölïo 5r")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests: download_folio URL construction
# ---------------------------------------------------------------------------

class TestDownloadFolioURL:
    def _canvas(self, service_url="https://example.com/iiif/image/p1",
                image_url="https://example.com/images/p1.jpg"):
        return {"id": "c1", "label": "1r", "image_url": image_url, "service_url": service_url}

    def test_analysis_url_uses_iiif_size(self, tmp_path):
        from scribesim.refselect.iiif import download_folio
        captured = {}

        def fake_get(url, **kwargs):
            captured["url"] = url
            resp = MagicMock()
            resp.content = b"FAKEJPEG"
            resp.raise_for_status = MagicMock()
            return resp

        with patch("requests.get", side_effect=fake_get):
            download_folio(self._canvas(), tmp_path, resolution="analysis")

        assert "/full/1500,/0/default.jpg" in captured["url"]

    def test_extraction_url_uses_max(self, tmp_path):
        from scribesim.refselect.iiif import download_folio
        captured = {}

        def fake_get(url, **kwargs):
            captured["url"] = url
            resp = MagicMock()
            resp.content = b"FAKEJPEG"
            resp.raise_for_status = MagicMock()
            return resp

        with patch("requests.get", side_effect=fake_get):
            download_folio(self._canvas(), tmp_path, resolution="extraction")

        assert "/full/max/0/default.jpg" in captured["url"]

    def test_direct_fallback_when_no_service(self, tmp_path):
        from scribesim.refselect.iiif import download_folio
        captured = {}
        canvas = self._canvas(service_url="")

        def fake_get(url, **kwargs):
            captured["url"] = url
            resp = MagicMock()
            resp.content = b"FAKEJPEG"
            resp.raise_for_status = MagicMock()
            return resp

        with patch("requests.get", side_effect=fake_get):
            download_folio(canvas, tmp_path, resolution="analysis")

        assert captured["url"] == canvas["image_url"]

    def test_returns_path(self, tmp_path):
        from scribesim.refselect.iiif import download_folio

        with patch("requests.get", return_value=MagicMock(
            content=b"FAKEJPEG", raise_for_status=MagicMock()
        )):
            result = download_folio(self._canvas(), tmp_path, resolution="analysis")

        assert isinstance(result, Path)
        assert result.exists()
