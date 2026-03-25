"""Tests for TD-014 exemplar corpus construction."""

from __future__ import annotations

import tomllib
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

from scribesim.refextract.corpus import (
    AUTO_ADMITTED_TIER,
    CandidateRecord,
    _refine_template_bank,
    _select_promoted_exemplars_with_validation,
    build_exemplar_corpus,
    build_join_template_bank,
    build_priority_join_inventory,
    build_symbol_template_bank,
    build_symbol_templates,
    load_selection_manifest,
)


def _make_line_image(words: list[str], templates: dict[str, np.ndarray]) -> np.ndarray:
    height = 110
    width = 1400
    canvas = np.full((height, width), 255, dtype=np.uint8)
    cursor_x = 30
    baseline_y = 20
    for word in words:
        for symbol in word:
            glyph = Image.fromarray(templates[symbol]).resize((48, 48), Image.Resampling.LANCZOS)
            arr = np.array(glyph, dtype=np.uint8)
            h, w = arr.shape
            canvas[baseline_y:baseline_y + h, cursor_x:cursor_x + w] = np.minimum(
                canvas[baseline_y:baseline_y + h, cursor_x:cursor_x + w],
                arr,
            )
            cursor_x += max(w - 4, 8)
        cursor_x += 24
    return canvas


def _make_page_image(lines: list[list[str]], templates: dict[str, np.ndarray], output_path: Path) -> None:
    line_images = [_make_line_image(words, templates) for words in lines]
    height = len(line_images) * 150 + 40
    width = max(line.shape[1] for line in line_images) + 40
    page = np.full((height, width), 255, dtype=np.uint8)
    cursor_y = 20
    for line in line_images:
        h, w = line.shape
        page[cursor_y:cursor_y + h, 20:20 + w] = np.minimum(page[cursor_y:cursor_y + h, 20:20 + w], line)
        cursor_y += 140
    Image.fromarray(page).save(output_path)


def _make_word_image(word: str, templates: dict[str, np.ndarray]) -> np.ndarray:
    canvas = np.full((110, 400), 255, dtype=np.uint8)
    cursor_x = 10
    baseline_y = 20
    for symbol in word:
        glyph = Image.fromarray(templates[symbol]).resize((48, 48), Image.Resampling.LANCZOS)
        arr = np.array(glyph, dtype=np.uint8)
        h, w = arr.shape
        canvas[baseline_y:baseline_y + h, cursor_x:cursor_x + w] = np.minimum(
            canvas[baseline_y:baseline_y + h, cursor_x:cursor_x + w],
            arr,
        )
        cursor_x += max(w - 4, 8)
    rows = np.where((canvas < 250).any(axis=1))[0]
    cols = np.where((canvas < 250).any(axis=0))[0]
    return canvas[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]


def test_build_priority_join_inventory_includes_word_internal_pairs():
    joins = build_priority_join_inventory(["und", "der"], boundary_joins=("r->space", "space->d"))
    assert joins == ("d->e", "e->r", "n->d", "r->space", "space->d", "u->n")


def test_load_selection_manifest_reads_frozen_manifest(tmp_path):
    manifest_path = tmp_path / "selection_manifest.toml"
    manifest_path.write_text(
        """
schema_version = 1
manifest_path = "shared/training/handsim/exemplar_harvest_v1/manifest.toml"

[[folios]]
canvas_label = "001r"
source_manuscript_label = "Fixture"
local_path = "folio1.png"
"""
    )
    manifest = load_selection_manifest(manifest_path)
    assert manifest["manifest_path"].endswith("manifest.toml")
    assert len(manifest["folios"]) == 1


def test_build_symbol_template_bank_returns_multiple_variants_per_symbol():
    bank = build_symbol_template_bank(required_symbols=("u", "n"))
    assert set(bank) == {"u", "n"}
    assert len(bank["u"]) > 1
    assert all(template.shape == (64, 64) for template in bank["u"])


def test_build_join_template_bank_returns_join_variants():
    bank = build_join_template_bank(priority_joins=("u->n", "n->d"))
    assert set(bank) == {"u->n", "n->d"}
    assert len(bank["u->n"]) > 1
    assert all(template.shape == (64, 64) for template in bank["u->n"])


def test_refine_template_bank_rejects_centroids_that_match_competing_symbol():
    base_bank = build_symbol_template_bank(required_symbols=("u", "n"))
    wrong_symbol_template = build_symbol_templates(required_symbols=("u", "n"))["n"]
    refined = _refine_template_bank(
        base_bank,
        glyph_candidates={},
        refinement_candidates={"u": [wrong_symbol_template]},
        max_candidates_per_symbol=1,
        max_centroids=1,
    )
    assert len(refined["u"]) == len(base_bank["u"])


def test_build_exemplar_corpus_writes_frozen_bundle(tmp_path):
    selection_manifest_path = tmp_path / "selection_manifest.toml"
    output_root = tmp_path / "corpus"
    templates = build_symbol_templates(required_symbols=("u", "n", "d", "e", "r"))

    folio1 = tmp_path / "folio1.png"
    folio2 = tmp_path / "folio2.png"
    Image.fromarray(np.full((128, 128), 255, dtype=np.uint8)).save(folio1)
    Image.fromarray(np.full((128, 128), 255, dtype=np.uint8)).save(folio2)
    under = _make_word_image("under", templates)
    line_stub = np.full((90, 600), 255, dtype=np.uint8)

    selection_manifest_path.write_text(
        f"""
schema_version = 1
manifest_path = "shared/training/handsim/exemplar_harvest_v1/manifest.toml"

[[folios]]
canvas_label = "001r"
source_manuscript_label = "Fixture A"
local_path = "{folio1.as_posix()}"

[[folios]]
canvas_label = "002r"
source_manuscript_label = "Fixture B"
local_path = "{folio2.as_posix()}"
"""
    )

    splits = ["train", "validation", "test"]
    with patch("scribesim.refextract.corpus._deterministic_split", side_effect=lambda key: splits[hash(key) % 3]), patch(
        "scribesim.refextract.corpus.segment_lines", return_value=[line_stub, line_stub]
    ), patch(
        "scribesim.refextract.corpus.segment_words", return_value=[under, under]
    ):
        result = build_exemplar_corpus(
            selection_manifest_path,
            output_root=output_root,
            required_symbols=("u", "n", "d", "e", "r"),
            priority_joins=("u->n", "n->d", "d->e", "e->r"),
            tier_limits={"accepted": 4, "soft_accepted": 2, "rejected": 1},
        )

    summary = result["summary"]
    manifest = tomllib.loads(result["manifest_path"].read_text())

    assert summary["auto_admitted_glyph_coverage"] == 1.0
    assert summary["auto_admitted_join_coverage"] == 1.0
    assert summary["promoted_exemplar_glyph_coverage"] == 1.0
    assert summary["promoted_exemplar_join_coverage"] == 1.0
    assert summary["heldout_symbol_coverage"] == 1.0
    assert summary["gate"]["passed"] is True
    assert result["summary_json_path"].exists()
    assert result["summary_md_path"].exists()
    assert result["dataset_summary_path"].exists()
    assert result["promoted_manifest_path"].exists()
    assert result["promotion_gate_report_json_path"].exists()
    assert result["promotion_gate_report_md_path"].exists()
    assert (output_root / "glyph_panel.png").exists()
    assert (output_root / "join_panel.png").exists()
    assert (output_root / "promoted_glyph_panel.png").exists()
    assert (output_root / "promoted_join_panel.png").exists()
    assert (output_root / "glyphs" / "auto_admitted").exists()
    assert (output_root / "glyphs" / "promoted_exemplars").exists()
    assert manifest["dataset_id"] == "active-review-exemplars-v1"
    assert len(manifest["entries"]) >= 9
    assert manifest["entries"][0]["auto_admitted_count"] >= 0
    assert "auto_admitted_paths" in manifest["entries"][0]
    assert "quarantined_paths" in manifest["entries"][0]
    assert "accepted_paths" in manifest["entries"][0]
    promoted_manifest = tomllib.loads(result["promoted_manifest_path"].read_text())
    assert promoted_manifest["manifest_kind"] == "promoted_exemplars"
    assert promoted_manifest["entries"][0]["promoted_exemplar_count"] >= 0
    assert "promoted_exemplar_paths" in promoted_manifest["entries"][0]
    assert "u->n" not in summary["missing_joins"]
    assert "n->d" not in summary["missing_joins"]
    assert "d->e" not in summary["missing_joins"]
    assert "e->r" not in summary["missing_joins"]


def test_build_exemplar_corpus_emits_progress_updates(tmp_path):
    selection_manifest_path = tmp_path / "selection_manifest.toml"
    output_root = tmp_path / "corpus"
    templates = build_symbol_templates(required_symbols=("u", "n", "d", "e", "r"))

    folio1 = tmp_path / "folio1.png"
    folio2 = tmp_path / "folio2.png"
    Image.fromarray(np.full((128, 128), 255, dtype=np.uint8)).save(folio1)
    Image.fromarray(np.full((128, 128), 255, dtype=np.uint8)).save(folio2)
    under = _make_word_image("under", templates)
    line_stub = np.full((90, 600), 255, dtype=np.uint8)

    selection_manifest_path.write_text(
        f"""
schema_version = 1
manifest_path = "shared/training/handsim/exemplar_harvest_v1/manifest.toml"

[[folios]]
canvas_label = "001r"
source_manuscript_label = "Fixture A"
local_path = "{folio1.as_posix()}"

[[folios]]
canvas_label = "002r"
source_manuscript_label = "Fixture B"
local_path = "{folio2.as_posix()}"
"""
    )

    updates: list[dict[str, object]] = []
    with patch("scribesim.refextract.corpus.segment_lines", return_value=[line_stub]), patch(
        "scribesim.refextract.corpus.segment_words", return_value=[under, under]
    ):
        build_exemplar_corpus(
            selection_manifest_path,
            output_root=output_root,
            required_symbols=("u", "n", "d", "e", "r"),
            priority_joins=("u->n", "n->d", "d->e", "e->r"),
            progress_callback=updates.append,
        )

    assert updates
    assert updates[0]["stage"] == "setup"
    assert any(update["stage"] == "initial_scan" for update in updates)
    assert updates[-1]["stage"] == "write_reports"
    assert updates[-1]["percent_complete"] == 100.0


def test_promoted_exemplar_gate_rejects_competing_symbol_candidate(tmp_path):
    template_bank = build_symbol_template_bank(required_symbols=("u", "n"))
    output_root = tmp_path / "corpus"
    output_root.mkdir(parents=True, exist_ok=True)
    u_dir = output_root / "glyphs" / "auto_admitted" / "u"
    n_dir = output_root / "glyphs" / "auto_admitted" / "n"
    u_dir.mkdir(parents=True, exist_ok=True)
    n_dir.mkdir(parents=True, exist_ok=True)

    mislabeled_path = u_dir / "u_bad.png"
    true_n_path = n_dir / "n_true.png"
    Image.fromarray(template_bank["n"][0]).save(mislabeled_path)
    Image.fromarray(template_bank["n"][0]).save(true_n_path)

    grouped = {
        "u": {
            AUTO_ADMITTED_TIER: [
                CandidateRecord(
                    kind="glyphs",
                    symbol="u",
                    confidence_tier=AUTO_ADMITTED_TIER,
                    split="validation",
                    score=0.9,
                    margin=0.1,
                    source_path="source-u.png",
                    source_manuscript_label="Fixture",
                    canvas_label="001r",
                    line_index=0,
                    word_index=0,
                    candidate_index=0,
                    path=mislabeled_path.as_posix(),
                )
            ]
        },
        "n": {
            AUTO_ADMITTED_TIER: [
                CandidateRecord(
                    kind="glyphs",
                    symbol="n",
                    confidence_tier=AUTO_ADMITTED_TIER,
                    split="validation",
                    score=0.9,
                    margin=0.1,
                    source_path="source-n.png",
                    source_manuscript_label="Fixture",
                    canvas_label="001r",
                    line_index=0,
                    word_index=0,
                    candidate_index=0,
                    path=true_n_path.as_posix(),
                )
            ]
        },
    }

    promoted, decisions = _select_promoted_exemplars_with_validation(
        grouped,
        template_bank=template_bank,
        gate_stage="exemplar_promotion_glyph",
    )

    assert "u" not in promoted
    assert decisions["u"][0]["passed"] is False
    assert any("competitor_margin" in reason or "cluster_separation" in reason for reason in decisions["u"][0]["failures"])


def test_build_exemplar_corpus_mines_boundary_joins_from_transcribed_words(tmp_path):
    selection_manifest_path = tmp_path / "selection_manifest.toml"
    output_root = tmp_path / "corpus"
    templates = build_symbol_templates(required_symbols=("d", "e", "r"))

    folio1 = tmp_path / "folio1.png"
    Image.fromarray(np.full((128, 128), 255, dtype=np.uint8)).save(folio1)
    der = _make_word_image("der", templates)
    line_stub = np.full((90, 600), 255, dtype=np.uint8)

    selection_manifest_path.write_text(
        f"""
schema_version = 1
manifest_path = "shared/training/handsim/exemplar_harvest_v1/manifest.toml"

[[folios]]
canvas_label = "001r"
source_manuscript_label = "Fixture A"
local_path = "{folio1.as_posix()}"
"""
    )

    with patch("scribesim.refextract.corpus.segment_lines", return_value=[line_stub]), patch(
        "scribesim.refextract.corpus.segment_words", return_value=[der, der]
    ):
        result = build_exemplar_corpus(
            selection_manifest_path,
            output_root=output_root,
            required_symbols=("d", "e", "r"),
            priority_joins=("d->e", "e->r", "r->space", "space->d"),
            transcription_lexicon=("der",),
            tier_limits={"accepted": 4, "soft_accepted": 2, "rejected": 1},
        )

    summary = result["summary"]
    assert "r->space" not in summary["missing_joins"]
    assert "space->d" not in summary["missing_joins"]


def test_committed_exemplar_harvest_selection_manifest_exists():
    manifest_path = Path("shared/training/handsim/exemplar_harvest_v1/selection_manifest.toml")
    manifest = tomllib.loads(manifest_path.read_text())
    assert manifest["harvest_id"] == "td014-exemplar-harvest-v1"
    assert manifest["selected_folio_count"] == 36
