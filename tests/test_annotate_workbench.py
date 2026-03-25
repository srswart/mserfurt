"""Tests for the TD-014 reviewed annotation workbench."""

from __future__ import annotations

import json
import threading
import tomllib
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

from scribesim.annotate.workbench import AnnotationWorkbenchServer, ReviewedAnnotationWorkbench


def _write_fixture_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    image_path = tmp_path / "folio.jpg"
    Image.new("RGB", (320, 240), color=(250, 247, 240)).save(image_path)

    selection_manifest = tmp_path / "selection_manifest.toml"
    selection_manifest.write_text(
        f"""
schema_version = 1

[[folios]]
rank = 1
canvas_label = "(0029)"
source_manuscript_label = "MS A"
source_object_id = "msa001"
local_path = "{image_path.as_posix()}"
"""
    )

    corpus_manifest = tmp_path / "corpus_manifest.toml"
    corpus_manifest.write_text(
        f"""
schema_version = 1
selection_manifest_path = "{selection_manifest.as_posix()}"
required_symbols = ["e"]
priority_joins = ["d->e"]
"""
    )

    ledger_path = tmp_path / "coverage_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "corpus_manifest_path": corpus_manifest.as_posix(),
                "summary": {
                    "glyph_reviewed_coverage": 0.0,
                    "join_reviewed_coverage": 0.0,
                    "glyph_promoted_coverage": 0.0,
                    "join_promoted_coverage": 0.0,
                },
                "entries": [
                    {
                        "kind": "glyph",
                        "symbol": "e",
                        "auto_admitted_count": 0,
                        "promoted_count": 0,
                        "reviewed_count": 0,
                        "missing_reviewed": 1,
                    },
                    {
                        "kind": "join",
                        "symbol": "d->e",
                        "auto_admitted_count": 0,
                        "promoted_count": 0,
                        "reviewed_count": 0,
                        "missing_reviewed": 1,
                    },
                ],
            }
        )
    )
    return selection_manifest, corpus_manifest, ledger_path


def test_reviewed_annotation_workbench_saves_glyph_and_join_annotations(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    workbench = ReviewedAnnotationWorkbench(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
    )

    saved_glyph = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "trusted",
            "notes": "clear body letter",
            "bounds_px": {"x": 10, "y": 20, "width": 30, "height": 40},
            "cleanup_strokes": [
                {
                    "mode": "erase",
                    "size_px": 6,
                    "points": [{"x": 4, "y": 6}, {"x": 10, "y": 8}],
                }
            ],
        }
    )
    saved_join = workbench.save_annotation(
        {
            "folio_id": "1",
            "kind": "join",
            "symbol": "d->e",
            "quality": "usable",
            "notes": "entry join",
            "bounds_px": {"x": 60, "y": 80, "width": 45, "height": 18},
        }
    )

    manifest = tomllib.loads((output_root / "reviewed_manifest.toml").read_text(encoding="utf-8"))
    state = workbench.get_state()
    assert len(state["annotations"]) == 2
    assert saved_glyph["kind"] == "glyph"
    assert saved_glyph["symbol"] == "e"
    assert saved_glyph["cleanup_strokes"][0]["mode"] == "erase"
    assert saved_join["kind"] == "join"
    assert saved_join["symbol"] == "d->e"
    assert saved_join["bounds_px"]["width"] == 45
    assert state["reviewed_manifest_path"].endswith("reviewed_manifest.toml")
    assert manifest["entry_count"] == 2
    assert manifest["entries"][0]["kind"] == "glyph"
    assert manifest["entries"][0]["cleanup_strokes"][0]["size_px"] == 6
    assert manifest["entries"][1]["kind"] == "join"


def test_annotation_workbench_server_serves_state_and_saves_annotations(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    server = AnnotationWorkbenchServer(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
        host="127.0.0.1",
        port=0,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        state = json.loads(urlopen(f"{server.url}/api/state", timeout=2).read().decode("utf-8"))
        assert state["folios"][0]["canvas_label"] == "(0029)"
        assert state["coverage_debt"][0]["symbol"] == "e"

        payload = {
            "folio_id": "1",
            "kind": "glyph",
            "symbol": "e",
            "quality": "trusted",
            "notes": "manual review",
            "bounds_px": {"x": 12, "y": 14, "width": 22, "height": 28},
            "cleanup_strokes": [
                {
                    "mode": "erase",
                    "size_px": 4,
                    "points": [{"x": 2, "y": 3}],
                }
            ],
        }
        request = Request(
            f"{server.url}/api/annotations",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        response = json.loads(urlopen(request, timeout=2).read().decode("utf-8"))
        assert response["saved"]["symbol"] == "e"
        assert response["saved"]["cleanup_strokes"][0]["size_px"] == 4
        assert len(response["annotations"]) == 1

        delete_request = Request(
            f"{server.url}/api/annotations/{response['saved']['id']}",
            method="DELETE",
        )
        deleted = json.loads(urlopen(delete_request, timeout=2).read().decode("utf-8"))
        assert deleted["deleted"] == response["saved"]["id"]
        assert deleted["annotations"] == []
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_annotation_workbench_root_html_exposes_500_percent_zoom(tmp_path: Path):
    selection_manifest, _, ledger_path = _write_fixture_inputs(tmp_path)
    output_root = tmp_path / "reviewed"

    server = AnnotationWorkbenchServer(
        coverage_ledger_path=ledger_path,
        output_root=output_root,
        selection_manifest_path=selection_manifest,
        host="127.0.0.1",
        port=0,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        html = urlopen(f"{server.url}/", timeout=2).read().decode("utf-8")
        assert 'id="zoom"' in html
        assert 'max="500"' in html
        assert 'id="magnifier-canvas"' in html
        assert 'id="zoom-in"' in html
        assert 'id="zoom-out"' in html
        assert 'id="zoom-reset"' in html
        assert 'id="pan-toggle"' in html
        assert 'id="cleanup-raw-canvas"' in html
        assert 'id="cleanup-clean-canvas"' in html
        assert 'id="cleanup-mode-erase"' in html
        assert 'id="cleanup-mode-restore"' in html
        assert html.index("Magnifier") < html.index("Reviewed manifest")
        assert html.index("Cleanup Editor") > html.index("Save Annotation")
    finally:
        server.shutdown()
        thread.join(timeout=2)
