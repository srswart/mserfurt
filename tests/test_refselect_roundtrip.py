"""Tests for analyze-reference / download-selected canvas ID round-trip (ADV-SS-REFSELECT-006)."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scribesim.refselect.provenance import new_provenance_record, save_provenance, add_candidate
from scribesim.refselect.iiif import sanitize_filename


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provenance_with_real_canvas(tmp_path: Path) -> tuple[Path, list[dict]]:
    """Write a provenance.json with two candidates that have real IIIF canvas IDs."""
    manifest = {
        "label": "Test Manuscript",
        "id": "https://example.com/manifest",
        "canvases": [],
    }
    sampling = {"n_candidates": 2, "strategy": "stratified", "seed": 42}
    record = new_provenance_record(manifest, sampling)

    canvases = [
        {
            "id": "https://example.com/canvas/v0100",
            "label": "47r (0100)",
            "image_url": "https://example.com/image/v0100/full/1500,/0/default.jpg",
            "service_url": "https://example.com/image/v0100",
        },
        {
            "id": "https://example.com/canvas/v0200",
            "label": "95r (0200)",
            "image_url": "https://example.com/image/v0200/full/1500,/0/default.jpg",
            "service_url": "https://example.com/image/v0200",
        },
    ]
    # Add dummy scores (zeros) so candidates exist in provenance
    dummy_scores = {
        "ink_contrast": 0.0, "line_regularity": 0.0, "script_consistency": 0.0,
        "text_density": 0.0, "damage": 0.0, "thick_thin": 0.0,
        "letter_variety": 0.0, "composite": 0.0,
    }
    for canvas in canvases:
        img_path = tmp_path / (sanitize_filename(canvas["label"]) + ".jpg")
        add_candidate(record, canvas, img_path, dummy_scores)

    prov_path = tmp_path / "provenance.json"
    save_provenance(record, prov_path)
    return prov_path, canvases


def _make_gray_jpg(path: Path) -> None:
    """Write a small grayscale JPG with ink-like pixels for analysis."""
    arr = np.full((80, 120), 220, dtype=np.uint8)
    arr[20:60, 30:90] = 30  # dark ink block
    Image.fromarray(arr).save(path, format="JPEG")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_analyze_reference_preserves_canvas_ids(tmp_path):
    """After analyze-reference, real canvas IDs must still be present in provenance."""
    from click.testing import CliRunner
    from scribesim.cli import main

    prov_path, canvases = _make_provenance_with_real_canvas(tmp_path)

    # Create matching JPGs so analyze-reference can score them
    for canvas in canvases:
        jpg = tmp_path / (sanitize_filename(canvas["label"]) + ".jpg")
        _make_gray_jpg(jpg)

    runner = CliRunner()
    result = runner.invoke(main, [
        "analyze-reference",
        "--input", str(tmp_path),
        "--selection-threshold", "0.0",
    ])
    assert result.exit_code == 0, result.output

    updated = json.loads(prov_path.read_text())
    candidates = updated["provenance"]["candidates"]

    canvas_ids = {c["canvas_id"] for c in candidates}
    assert "https://example.com/canvas/v0100" in canvas_ids
    assert "https://example.com/canvas/v0200" in canvas_ids

    for c in candidates:
        assert c["image_url"] != "", f"image_url wiped on {c['canvas_label']}"
        assert c["image_url"].startswith("https://"), f"image_url corrupted: {c['image_url']}"


def test_analyze_reference_scores_merged_into_existing(tmp_path):
    """Analysis scores are written into existing candidate records, not appended as new ones."""
    from click.testing import CliRunner
    from scribesim.cli import main

    prov_path, canvases = _make_provenance_with_real_canvas(tmp_path)

    for canvas in canvases:
        jpg = tmp_path / (sanitize_filename(canvas["label"]) + ".jpg")
        _make_gray_jpg(jpg)

    runner = CliRunner()
    result = runner.invoke(main, [
        "analyze-reference",
        "--input", str(tmp_path),
        "--selection-threshold", "0.0",
    ])
    assert result.exit_code == 0, result.output

    updated = json.loads(prov_path.read_text())
    candidates = updated["provenance"]["candidates"]

    for c in candidates:
        assert "ink_contrast" in c["scores"], f"ink_contrast missing on {c['canvas_label']}"
        assert "composite" in c["scores"], f"composite missing on {c['canvas_label']}"
        assert c["scores"]["composite"] > 0.0, f"composite not updated on {c['canvas_label']}"


def test_analyze_reference_no_duplicate_candidates(tmp_path):
    """Candidate count equals JPG count — no doubling from clear+re-add."""
    from click.testing import CliRunner
    from scribesim.cli import main

    prov_path, canvases = _make_provenance_with_real_canvas(tmp_path)

    for canvas in canvases:
        jpg = tmp_path / (sanitize_filename(canvas["label"]) + ".jpg")
        _make_gray_jpg(jpg)

    runner = CliRunner()
    result = runner.invoke(main, [
        "analyze-reference",
        "--input", str(tmp_path),
        "--selection-threshold", "0.0",
    ])
    assert result.exit_code == 0, result.output

    updated = json.loads(prov_path.read_text())
    candidates = updated["provenance"]["candidates"]
    assert len(candidates) == len(canvases)


def test_analyze_reference_unmatched_jpg_appended_with_warn_flag(tmp_path):
    """A JPG not in provenance is appended as a synthetic stub with warn_no_canvas_id=True."""
    from click.testing import CliRunner
    from scribesim.cli import main

    prov_path, canvases = _make_provenance_with_real_canvas(tmp_path)

    # Create the known JPGs
    for canvas in canvases:
        jpg = tmp_path / (sanitize_filename(canvas["label"]) + ".jpg")
        _make_gray_jpg(jpg)

    # Add an extra JPG not in provenance
    extra_jpg = tmp_path / "extra_folio_9999.jpg"
    _make_gray_jpg(extra_jpg)

    runner = CliRunner()
    result = runner.invoke(main, [
        "analyze-reference",
        "--input", str(tmp_path),
        "--selection-threshold", "0.0",
    ])
    assert result.exit_code == 0, result.output

    updated = json.loads(prov_path.read_text())
    candidates = updated["provenance"]["candidates"]

    # Should have original 2 + 1 extra
    assert len(candidates) == 3

    extra = next((c for c in candidates if c["canvas_label"] == "extra_folio_9999"), None)
    assert extra is not None, "Extra JPG not appended"
    assert extra.get("warn_no_canvas_id") is True
