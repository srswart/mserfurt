"""Unit tests for multi-manifest support — ADV-SS-REFSELECT-005 Part A."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixture manifests (reuse shapes from test_refselect_iiif.py)
# ---------------------------------------------------------------------------

def _make_v2_manifest(label: str, n_canvases: int = 5) -> dict:
    return {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@id": f"https://example.com/iiif/{label}/manifest",
        "label": label,
        "attribution": "Test Institution",
        "license": "Public Domain",
        "sequences": [{
            "canvases": [
                {
                    "@id": f"https://example.com/iiif/{label}/canvas/p{i}",
                    "label": f"{i}r",
                    "images": [{"resource": {
                        "@id": f"https://example.com/images/{label}_p{i}.jpg",
                        "service": {"@id": f"https://example.com/iiif/image/{label}_p{i}"},
                    }}],
                }
                for i in range(1, n_canvases + 1)
            ],
        }],
    }


def _mock_get(manifest_dict):
    resp = MagicMock()
    resp.json.return_value = manifest_dict
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# Tests: fetch_all_manifests
# ---------------------------------------------------------------------------

class TestFetchAllManifests:
    def test_returns_all_on_success(self):
        from scribesim.refselect.iiif import fetch_all_manifests
        m1 = _make_v2_manifest("bsb001", 5)
        m2 = _make_v2_manifest("bsb002", 4)
        with patch("requests.get", side_effect=[_mock_get(m1), _mock_get(m2)]):
            results = fetch_all_manifests(
                ["https://x/m1", "https://x/m2"],
                labels=["Cgm 100", "Cgm 452"],
            )
        assert len(results) == 2

    def test_skips_failed_manifest(self):
        from scribesim.refselect.iiif import fetch_all_manifests
        import requests
        m1 = _make_v2_manifest("bsb001", 5)
        err_resp = MagicMock()
        err_resp.raise_for_status.side_effect = requests.HTTPError("404")
        with patch("requests.get", side_effect=[_mock_get(m1), err_resp]):
            results = fetch_all_manifests(
                ["https://x/m1", "https://x/m2"],
                labels=["Cgm 100", "Cgm 452"],
            )
        assert len(results) == 1

    def test_attaches_label(self):
        from scribesim.refselect.iiif import fetch_all_manifests
        m1 = _make_v2_manifest("bsb001", 3)
        with patch("requests.get", return_value=_mock_get(m1)):
            results = fetch_all_manifests(["https://x/m1"], labels=["Cgm 100"])
        assert results[0].get("label") == "Cgm 100"


# ---------------------------------------------------------------------------
# Tests: select_candidates_multi
# ---------------------------------------------------------------------------

class TestSelectCandidatesMulti:
    def _manifests(self):
        from scribesim.refselect.iiif import fetch_manifest
        manifests = []
        for label, n in [("bsb001", 6), ("bsb002", 6)]:
            m = _make_v2_manifest(label, n)
            with patch("requests.get", return_value=_mock_get(m)):
                manifest = fetch_manifest(f"https://x/{label}")
                manifest["label"] = label
            manifests.append(manifest)
        return manifests

    def test_count_respects_n_per_manuscript(self):
        from scribesim.refselect.iiif import select_candidates_multi
        manifests = self._manifests()
        result = select_candidates_multi(manifests, n_per_manuscript=3)
        assert len(result) <= 6  # 3 per manuscript × 2 manifests

    def test_candidates_from_both_sources(self):
        from scribesim.refselect.iiif import select_candidates_multi
        manifests = self._manifests()
        result = select_candidates_multi(manifests, n_per_manuscript=3)
        labels = {c.get("source_manuscript_label") for c in result}
        assert len(labels) == 2  # candidates from both manifests

    def test_no_duplicate_canvas_ids(self):
        from scribesim.refselect.iiif import select_candidates_multi
        manifests = self._manifests()
        result = select_candidates_multi(manifests, n_per_manuscript=5)
        ids = [c["id"] for c in result]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Tests: new_multi_provenance_record
# ---------------------------------------------------------------------------

class TestMultiProvenanceRecord:
    def _manifests_with_labels(self):
        return [
            {"manifest_url": "https://x/m1", "title": "Cgm 100",
             "attribution": "BSB", "license": "PD", "label": "Cgm 100", "canvases": []},
            {"manifest_url": "https://x/m2", "title": "Cgm 452",
             "attribution": "BSB", "license": "PD", "label": "Cgm 452", "canvases": []},
        ]

    def test_has_source_manuscripts_list(self):
        from scribesim.refselect.provenance import new_multi_provenance_record
        sampling = {"strategy": "stratified", "n_per_manuscript": 5,
                    "page_range": "all", "random_seed": 42}
        rec = new_multi_provenance_record(self._manifests_with_labels(), sampling)
        assert "source_manuscripts" in rec["provenance"]
        assert isinstance(rec["provenance"]["source_manuscripts"], list)

    def test_source_manuscripts_count(self):
        from scribesim.refselect.provenance import new_multi_provenance_record
        sampling = {"strategy": "stratified", "n_per_manuscript": 5,
                    "page_range": "all", "random_seed": 42}
        rec = new_multi_provenance_record(self._manifests_with_labels(), sampling)
        assert len(rec["provenance"]["source_manuscripts"]) == 2


# ---------------------------------------------------------------------------
# Tests: schema migration shim
# ---------------------------------------------------------------------------

class TestSchemaMigrationShim:
    def test_v1_record_gets_source_manuscripts(self, tmp_path):
        from scribesim.refselect.provenance import save_provenance, load_provenance
        # Write a v1-style record (single source_manuscript)
        v1 = {
            "provenance": {
                "run_id": "ref-select-20260101-000000-000000",
                "timestamp": "2026-01-01T00:00:00Z",
                "source_manuscript": {
                    "manifest_url": "https://x/m1",
                    "title": "Cgm 100",
                    "attribution": "BSB",
                    "license": "PD",
                },
                "sampling": {"strategy": "stratified", "n_candidates": 5,
                             "page_range": "all", "random_seed": 42},
                "candidates": [],
            }
        }
        p = tmp_path / "prov.json"
        save_provenance(v1, p)
        loaded = load_provenance(p)
        # Shim: source_manuscripts should be present
        assert "source_manuscripts" in loaded["provenance"]
        assert len(loaded["provenance"]["source_manuscripts"]) == 1

    def test_v1_source_manuscript_still_present(self, tmp_path):
        from scribesim.refselect.provenance import save_provenance, load_provenance
        v1 = {
            "provenance": {
                "run_id": "ref-select-x",
                "timestamp": "2026-01-01T00:00:00Z",
                "source_manuscript": {"manifest_url": "https://x",
                                      "title": "T", "attribution": "A", "license": "L"},
                "sampling": {}, "candidates": [],
            }
        }
        p = tmp_path / "prov.json"
        save_provenance(v1, p)
        loaded = load_provenance(p)
        # Original key preserved for backward compatibility
        assert "source_manuscript" in loaded["provenance"]
