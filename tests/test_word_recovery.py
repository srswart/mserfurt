"""Behavioral safeguards for the exploratory whole-word recovery experiment."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest
from PIL import Image

from scribesim.evo.genome import genome_from_guides
from scribesim.evo.renderer import render_word_from_genome
from scribesim.evofit.word_recovery import (
    fit_shared_hand,
    render_shared_word,
    run_word_recovery,
    seed_hand,
    word_image_loss,
)


def _word_image(text: str, width_scale: float = 1.0) -> Image.Image:
    genome = copy.deepcopy(genome_from_guides(text, x_height_mm=3.8))
    for glyph in genome.glyphs:
        glyph.x_offset *= width_scale
        glyph.x_advance *= width_scale
        for stroke in glyph.segments:
            for name in ("p0", "p1", "p2", "p3"):
                x, y = getattr(stroke, name)
                setattr(stroke, name, (x * width_scale, y))
    genome.word_width_mm *= width_scale
    state = random.getstate()
    try:
        random.seed(123)
        rendered = render_word_from_genome(genome, dpi=100, variation=0)
    finally:
        random.setstate(state)
    return Image.fromarray(rendered).convert("RGB")


def _dataset(tmp_path: Path, heldout_text: str = "u") -> Path:
    training = _word_image("nn", width_scale=1.35)
    heldout = _word_image(heldout_text)
    image = Image.new("RGB", (max(training.width, heldout.width) + 20,
                              training.height + heldout.height + 40), "white")
    image.paste(training, (10, 10))
    image.paste(heldout, (10, training.height + 30))
    source = tmp_path / "source.png"
    image.save(source)
    payload = {
        "schema_version": 1,
        "hand_id": "synthetic-regression-fixture",
        "source": {
            "manuscript_id": "synthetic-not-historical",
            "image_path": str(source),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "canvas_id": "synthetic",
            "image_url": "",
            "hand_identity_status": "synthetic fixture only",
        },
        "label_policy": "Deliberately mismatched held-out label tests leakage.",
        "human_interventions": [],
        "samples": [
            {"id": "train", "text": "nn", "bbox": [10, 10, 10 + training.width,
              10 + training.height], "split": "train", "label_source": "synthetic",
             "confidence": 1.0, "notes": "Known widened stroke render."},
            {"id": "heldout", "text": "n", "bbox": [10, training.height + 30,
              10 + heldout.width, training.height + 30 + heldout.height],
             "split": "heldout", "label_source": "synthetic", "confidence": 1.0,
             "notes": "Its pixels must not influence fitting."},
        ],
        "generated_texts": ["nnn"],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_recovery_evaluates_rendered_candidates_without_global_random_side_effects(tmp_path: Path):
    manifest = _dataset(tmp_path)
    state = random.getstate()
    report = run_word_recovery(manifest, tmp_path / "out", iterations=8, seed=23, dpi=72)
    assert random.getstate() == state
    assert report["training"]["before"] > 0.01
    assert report["training"]["after"] <= report["training"]["before"]
    assert report["heldout"]["before"] > 0.01


def test_heldout_pixels_cannot_change_the_learned_hand(tmp_path: Path):
    manifest = _dataset(tmp_path)
    run_word_recovery(manifest, tmp_path / "first", iterations=8, seed=23, dpi=72)
    first = json.loads((tmp_path / "first" / "learned_hand.json").read_text())
    manifest = _dataset(tmp_path, heldout_text="m")
    run_word_recovery(manifest, tmp_path / "second", iterations=8, seed=23, dpi=72)
    second = json.loads((tmp_path / "second" / "learned_hand.json").read_text())
    assert first["glyphs"] == second["glyphs"]


def test_recovery_rejects_source_pixels_shared_between_splits(tmp_path: Path):
    manifest = _dataset(tmp_path)
    payload = json.loads(manifest.read_text())
    payload["samples"][1]["bbox"] = payload["samples"][0]["bbox"]
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="(?i)(overlap|duplicate)"):
        run_word_recovery(manifest, tmp_path / "out", iterations=0, seed=23, dpi=72)


def test_recovery_refuses_source_image_changed_since_labeling(tmp_path: Path):
    manifest = _dataset(tmp_path)
    payload = json.loads(manifest.read_text())
    payload["source"]["sha256"] = "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="(?i)(sha256|checksum|hash)"):
        run_word_recovery(manifest, tmp_path / "out", iterations=0, seed=23, dpi=72)


def test_training_improves_an_unseen_combination_of_shared_letters():
    target_hand = seed_hand("n")
    target_hand["glyphs"]["n"]["advance"] *= 0.75
    for segment in target_hand["glyphs"]["n"]["segments"]:
        for name in ("p0", "p1", "p2", "p3"):
            segment[name][0] *= 0.75
    training = render_shared_word("nn", target_hand, dpi=72)
    heldout = render_shared_word("nnn", target_hand, dpi=72)
    result = fit_shared_hand(
        [{"id": "paired-minims", "text": "nn", "image": training}],
        iterations=120, seed=23, dpi=72,
    )
    before = word_image_loss(heldout, render_shared_word("nnn", result["baseline_hand"], dpi=72))
    after = word_image_loss(heldout, render_shared_word("nnn", result["hand"], dpi=72))
    assert result["after"] < result["before"] * 0.8
    assert after < before * 0.8
