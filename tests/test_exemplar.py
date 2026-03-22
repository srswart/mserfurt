"""Tests for scribesim/refextract/exemplar.py + fitness.py F1 update (ADV-SS-EXEMPLAR-002).

Red phase: tests/test_exemplar.py should fail until exemplar.py is implemented
and fitness.py is updated.
"""

import numpy as np
import pytest
from pathlib import Path

from scribesim.refextract.exemplar import (
    tight_crop,
    resize_and_pad,
    normalize_intensity,
    extract_exemplar,
    build_exemplar_set,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_letter_image(h=40, w=24, ink_h=30, ink_w=18, offset=(5, 3)):
    """Synthetic letter image: white background with a black ink rectangle."""
    img = np.full((h, w), 255, dtype=np.uint8)
    y0, x0 = offset
    img[y0:y0 + ink_h, x0:x0 + ink_w] = 10
    return img


# ---------------------------------------------------------------------------
# tight_crop
# ---------------------------------------------------------------------------

def test_tight_crop_isolates_ink():
    """tight_crop returns a region containing the ink bounding box + padding."""
    img = _make_letter_image(h=60, w=60, ink_h=20, ink_w=15, offset=(20, 25))
    cropped = tight_crop(img, padding=2)

    # Cropped should be smaller than original
    assert cropped.shape[0] < 60
    assert cropped.shape[1] < 60

    # Cropped should contain ink
    assert (cropped < 200).any()

    # Ink region should fill most of the crop
    ink_rows = (cropped < 200).any(axis=1).sum()
    assert ink_rows >= 18  # 20 ink rows - some tolerance for padding


def test_tight_crop_blank_returns_original():
    """tight_crop on a blank image returns the original (no ink to crop to)."""
    blank = np.full((40, 40), 255, dtype=np.uint8)
    result = tight_crop(blank, padding=2)
    assert result.shape == blank.shape


# ---------------------------------------------------------------------------
# resize_and_pad
# ---------------------------------------------------------------------------

def test_resize_and_pad_output_size():
    """resize_and_pad always outputs the target size."""
    img = np.full((30, 15), 128, dtype=np.uint8)
    out = resize_and_pad(img, target_size=(64, 64))
    assert out.shape == (64, 64)


def test_resize_and_pad_tall_image():
    """Tall image: height fills target, width is padded."""
    img = np.zeros((80, 20), dtype=np.uint8)  # tall narrow letter
    out = resize_and_pad(img, target_size=(64, 64))
    assert out.shape == (64, 64)
    # Background padding should be white
    assert out[0, 0] == 255  # corner should be background


def test_resize_and_pad_wide_image():
    """Wide image: width fills target, height is padded."""
    img = np.zeros((20, 80), dtype=np.uint8)  # wide short letter
    out = resize_and_pad(img, target_size=(64, 64))
    assert out.shape == (64, 64)


def test_resize_and_pad_preserves_aspect_ratio():
    """Ink bounding box aspect ratio is approximately preserved."""
    # 2:1 tall letter (height = 2 × width)
    img = np.full((64, 32), 255, dtype=np.uint8)
    img[8:56, 8:24] = 0  # ink: 48px tall × 16px wide = 3:1

    out = resize_and_pad(img, target_size=(64, 64))

    # Find ink extent in output
    ink = out < 128
    ink_rows = ink.any(axis=1).sum()
    ink_cols = ink.any(axis=0).sum()

    if ink_rows > 0 and ink_cols > 0:
        aspect = ink_rows / ink_cols
        # Original aspect ~3:1; should still be >1.5 after resize+pad
        assert aspect > 1.5, f"aspect ratio not preserved: {aspect:.2f}"


# ---------------------------------------------------------------------------
# normalize_intensity
# ---------------------------------------------------------------------------

def test_normalize_intensity_output_range():
    """Normalized output has values in [0, 255]."""
    img = np.random.randint(50, 200, (40, 40), dtype=np.uint8)
    out = normalize_intensity(img)
    assert out.min() >= 0
    assert out.max() <= 255


def test_normalize_intensity_background_near_255():
    """Background (bright) pixels should be mapped near 255."""
    img = _make_letter_image()
    out = normalize_intensity(img)
    # Most pixels are background; upper quartile should be near 255
    assert np.percentile(out, 90) >= 200


def test_normalize_intensity_ink_near_0():
    """Ink (dark) pixels should be mapped near 0."""
    img = _make_letter_image()
    out = normalize_intensity(img)
    # Ink pixels should be dark
    assert np.percentile(out, 5) <= 50


# ---------------------------------------------------------------------------
# extract_exemplar (full pipeline)
# ---------------------------------------------------------------------------

def test_extract_exemplar_output_size():
    """extract_exemplar always returns 64×64."""
    img = _make_letter_image()
    out = extract_exemplar(img)
    assert out.shape == (64, 64)
    assert out.dtype == np.uint8


def test_extract_exemplar_non_square_input():
    """extract_exemplar handles tall and wide inputs."""
    tall = _make_letter_image(h=80, w=30, ink_h=60, ink_w=20, offset=(10, 5))
    wide = _make_letter_image(h=30, w=80, ink_h=20, ink_w=60, offset=(5, 10))

    for img in (tall, wide):
        out = extract_exemplar(img)
        assert out.shape == (64, 64)


def test_extract_exemplar_custom_size():
    """extract_exemplar respects a custom target_size."""
    img = _make_letter_image()
    out = extract_exemplar(img, target_size=(32, 32))
    assert out.shape == (32, 32)


# ---------------------------------------------------------------------------
# build_exemplar_set
# ---------------------------------------------------------------------------

def test_build_exemplar_set_writes_normalized_pngs(tmp_path):
    """build_exemplar_set reads raw crops and writes normalized exemplars."""
    from PIL import Image

    # Write 3 synthetic letter crops
    letter_dir = tmp_path / "n"
    letter_dir.mkdir()
    for i in range(3):
        img = _make_letter_image()
        Image.fromarray(img).save(str(letter_dir / f"crop_{i:04d}.png"))

    out_dir = tmp_path / "out"
    build_exemplar_set(letter_dir, out_dir)

    pngs = list(out_dir.glob("*.png"))
    assert len(pngs) == 3

    # Each output should be 64×64
    for p in pngs:
        arr = np.array(Image.open(p).convert("L"))
        assert arr.shape == (64, 64)


def test_build_exemplar_set_empty_dir(tmp_path):
    """build_exemplar_set on empty dir writes nothing, no error."""
    letter_dir = tmp_path / "x"
    letter_dir.mkdir()
    out_dir = tmp_path / "out"
    build_exemplar_set(letter_dir, out_dir)

    # No output (or empty output dir)
    pngs = list(out_dir.glob("*.png")) if out_dir.exists() else []
    assert len(pngs) == 0


# ---------------------------------------------------------------------------
# F1 fitness: _load_exemplars + evaluate_fitness exemplar_root param
# ---------------------------------------------------------------------------

def test_load_exemplars_prefers_reference(tmp_path):
    """_load_exemplars prefers reference/exemplars/ over training/labeled_exemplars/."""
    from PIL import Image
    from scribesim.evo.fitness import _load_exemplars

    ref_dir = tmp_path / "reference" / "exemplars" / "n"
    ref_dir.mkdir(parents=True)
    train_dir = tmp_path / "training" / "labeled_exemplars" / "n"
    train_dir.mkdir(parents=True)

    # Write 2 exemplars to reference, 1 to training
    for i in range(2):
        Image.fromarray(np.full((64, 64), 100, dtype=np.uint8)).save(
            str(ref_dir / f"n_{i:04d}.png"))
    Image.fromarray(np.full((64, 64), 200, dtype=np.uint8)).save(
        str(train_dir / "n_0000.png"))

    exemplars = _load_exemplars(exemplar_root=tmp_path / "reference" / "exemplars")
    assert "n" in exemplars
    assert len(exemplars["n"]) == 2  # from reference, not training


def test_load_exemplars_fallback_to_training(tmp_path):
    """_load_exemplars falls back to training/labeled_exemplars/ when reference absent."""
    from PIL import Image
    from scribesim.evo.fitness import _load_exemplars

    train_dir = tmp_path / "training" / "labeled_exemplars" / "u"
    train_dir.mkdir(parents=True)
    Image.fromarray(np.full((64, 64), 50, dtype=np.uint8)).save(
        str(train_dir / "u_0000.png"))

    exemplars = _load_exemplars(
        exemplar_root=tmp_path / "reference" / "exemplars",  # does not exist
        fallback_root=tmp_path / "training" / "labeled_exemplars",
    )
    assert "u" in exemplars
    assert len(exemplars["u"]) == 1


def test_evaluate_fitness_accepts_exemplar_root():
    """evaluate_fitness() accepts exemplar_root without error (no exemplars = neutral F1)."""
    import tempfile
    from scribesim.evo.fitness import evaluate_fitness
    from scribesim.evo.genome import genome_from_guides

    genome = genome_from_guides("und")
    with tempfile.TemporaryDirectory() as tmpdir:
        result = evaluate_fitness(genome, exemplar_root=Path(tmpdir))
    assert 0.0 <= result.f1 <= 1.0
    assert 0.0 <= result.total <= 1.0
