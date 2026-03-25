"""Tests for TD-014 reviewed coverage ledger."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from scribesim.annotate import build_reviewed_coverage_ledger


def test_build_reviewed_coverage_ledger_writes_bundle(tmp_path):
    selection_manifest = tmp_path / "selection_manifest.toml"
    selection_manifest.write_text(
        """
schema_version = 1
manifest_path = "shared/training/handsim/exemplar_harvest_v1/manifest.toml"

[[folios]]
canvas_label = "(0029)"
source_manuscript_label = "MS A"
local_path = "ms_a/0029.jpg"

[[folios]]
canvas_label = "(0036)"
source_manuscript_label = "MS B"
local_path = "ms_b/0036.jpg"
"""
    )

    promoted_manifest = tmp_path / "promoted_manifest.toml"
    promoted_manifest.write_text(
        """
schema_version = 1
manifest_kind = "promoted_exemplars"
dataset_id = "fixture-promoted"

[[entries]]
kind = "glyph"
symbol = "k"
promoted_exemplar_count = 1
promoted_exemplar_paths = ["out/glyphs/promoted_exemplars/k.png"]
promoted_exemplar_source_paths = ["shared/training/handsim/exemplar_harvest_v1/folios/MS_A/0029.jpg"]

[[entries]]
kind = "join"
symbol = "d->e"
promoted_exemplar_count = 1
promoted_exemplar_paths = ["out/joins/promoted_exemplars/d_to_e.png"]
promoted_exemplar_source_paths = ["shared/training/handsim/exemplar_harvest_v1/folios/MS_B/0036.jpg"]
"""
    )

    corpus_manifest = tmp_path / "manifest.toml"
    corpus_manifest.write_text(
        f"""
schema_version = 1
dataset_id = "fixture"
selection_manifest_path = "{selection_manifest.as_posix()}"
promoted_manifest_path = "{promoted_manifest.as_posix()}"
required_symbols = ["k", "l", "x"]
priority_joins = ["d->e", "x->y"]

[[entries]]
kind = "glyph"
symbol = "k"
auto_admitted_count = 1
auto_admitted_paths = ["out/glyphs/auto_admitted/k/k_000_0029_l00_w00_c00.png"]
quarantined_count = 1
quarantined_paths = ["out/glyphs/quarantined/k/k_000_0036_l00_w00_c00.png"]
rejected_count = 0
rejected_paths = []
coverage_promoted = false

[[entries]]
kind = "glyph"
symbol = "l"
auto_admitted_count = 0
auto_admitted_paths = []
quarantined_count = 0
quarantined_paths = []
rejected_count = 1
rejected_paths = ["out/glyphs/rejected/l/l_000_0036_l00_w00_c00.png"]
coverage_promoted = false

[[entries]]
kind = "join"
symbol = "d->e"
auto_admitted_count = 1
auto_admitted_paths = ["out/joins/auto_admitted/d_to_e/d_to_e_000_0036_l00_w00_c00.png"]
quarantined_count = 0
quarantined_paths = []
rejected_count = 0
rejected_paths = []
coverage_promoted = false
"""
    )

    result = build_reviewed_coverage_ledger(corpus_manifest, output_root=tmp_path / "ledger")

    assert result["ledger_json_path"].exists()
    assert result["ledger_md_path"].exists()
    assert result["ledger_manifest_path"].exists()
    assert result["summary"]["glyph_promoted_coverage"] == pytest.approx(1 / 3)
    assert result["summary"]["join_promoted_coverage"] == pytest.approx(0.5)
    assert result["summary"]["glyph_reviewed_coverage"] == 0.0
    assert "l" in result["summary"]["glyph_missing_promoted"]
    assert "x" in result["summary"]["glyph_missing_promoted"]
    assert "x->y" in result["summary"]["join_missing_promoted"]

    manifest = tomllib.loads(result["ledger_manifest_path"].read_text())
    assert manifest["stage_id"] == "reviewed-coverage-ledger"
    assert len(manifest["entries"]) == 5
    first = manifest["entries"][0]
    assert "auto_admitted_count" in first
    assert "promoted_count" in first
