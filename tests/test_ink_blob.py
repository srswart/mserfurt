"""Tests for the post-dip blob effect (ADV-SS-INK-005 / TD-010 Part 2.4)."""

import pytest
from scribesim.ink.cycle import BlobParams, post_dip_blob


# ---------------------------------------------------------------------------
# Preconditions — blob only at first stroke after fresh dip
# ---------------------------------------------------------------------------

def test_no_blob_when_not_first_stroke():
    """Blob never appears after strokes_since_dip > 0."""
    for _ in range(100):
        result = post_dip_blob(reservoir=1.0, strokes_since_dip=1)
        assert result is None

    for _ in range(100):
        result = post_dip_blob(reservoir=1.0, strokes_since_dip=5)
        assert result is None


def test_no_blob_when_reservoir_low():
    """Blob never appears when reservoir < 0.90 (not a fresh dip)."""
    for _ in range(100):
        result = post_dip_blob(reservoir=0.89, strokes_since_dip=0)
        assert result is None

    for _ in range(100):
        result = post_dip_blob(reservoir=0.50, strokes_since_dip=0)
        assert result is None

    for _ in range(100):
        result = post_dip_blob(reservoir=0.0, strokes_since_dip=0)
        assert result is None


# ---------------------------------------------------------------------------
# Probability — approximately 15% at nominal conditions
# ---------------------------------------------------------------------------

def test_blob_probability_approximately_15_percent():
    """Over 500 trials, blob appears ~15% of the time (±7% tolerance)."""
    hits = sum(
        1 for _ in range(500)
        if post_dip_blob(reservoir=1.0, strokes_since_dip=0) is not None
    )
    rate = hits / 500
    assert 0.08 <= rate <= 0.22, (
        f"Expected blob probability ~0.15, got {rate:.3f} over 500 trials"
    )


def test_custom_probability_zero():
    """probability=0.0 never produces a blob."""
    for _ in range(100):
        result = post_dip_blob(reservoir=1.0, strokes_since_dip=0, probability=0.0)
        assert result is None


def test_custom_probability_one():
    """probability=1.0 always produces a blob when conditions are met."""
    for _ in range(20):
        result = post_dip_blob(reservoir=1.0, strokes_since_dip=0, probability=1.0)
        assert result is not None


# ---------------------------------------------------------------------------
# BlobParams values
# ---------------------------------------------------------------------------

def test_blob_radius_in_range():
    """radius_mm is always in [0.2, 0.5]."""
    for _ in range(200):
        result = post_dip_blob(reservoir=1.0, strokes_since_dip=0, probability=1.0)
        assert result is not None
        assert 0.2 <= result.radius_mm <= 0.5, (
            f"radius_mm {result.radius_mm:.3f} out of range [0.2, 0.5]"
        )


def test_blob_darkness_boost():
    """darkness_boost is exactly 0.20."""
    result = post_dip_blob(reservoir=1.0, strokes_since_dip=0, probability=1.0)
    assert result is not None
    assert result.darkness_boost == pytest.approx(0.20)


def test_blob_elongation_greater_than_one():
    """elongation is always > 1.0 (slightly elongated, not a perfect circle)."""
    for _ in range(50):
        result = post_dip_blob(reservoir=1.0, strokes_since_dip=0, probability=1.0)
        assert result is not None
        assert result.elongation > 1.0


def test_blob_elongation_upper_bound():
    """elongation stays reasonable (< 2.0)."""
    for _ in range(50):
        result = post_dip_blob(reservoir=1.0, strokes_since_dip=0, probability=1.0)
        assert result is not None
        assert result.elongation < 2.0


def test_blob_returns_blobparams_instance():
    """post_dip_blob returns a BlobParams instance when triggered."""
    result = post_dip_blob(reservoir=1.0, strokes_since_dip=0, probability=1.0)
    assert isinstance(result, BlobParams)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_reservoir_exactly_at_boundary():
    """reservoir=0.90 is below threshold — no blob."""
    for _ in range(50):
        result = post_dip_blob(reservoir=0.90, strokes_since_dip=0)
        assert result is None


def test_reservoir_just_above_boundary():
    """reservoir=0.91 is above threshold — blob possible."""
    seen_blob = False
    for _ in range(200):
        result = post_dip_blob(reservoir=0.91, strokes_since_dip=0, probability=1.0)
        if result is not None:
            seen_blob = True
            break
    assert seen_blob
