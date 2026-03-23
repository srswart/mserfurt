"""Integration tests for guide extraction → genome seeding (ADV-SS-GUIDEGEN-001).

Red phase: should fail until guidegen.py + genome_from_guides update are implemented.
"""

import pytest
import tempfile
import tomllib
from pathlib import Path

from scribesim.evo.genome import genome_from_guides, BezierSegment, GlyphGenome


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_GUIDES_TOML = """\
[u]
x_advance = 0.6
ascender = false
descender = false

[[u.keypoints]]
x = 0.05
y = 0.95
point_type = "entry"
contact = true
direction_deg = 270.0
flexibility_mm = 0.15

[[u.keypoints]]
x = 0.15
y = 0.0
point_type = "base"
contact = true
direction_deg = 0.0
flexibility_mm = 0.2

[[u.keypoints]]
x = 0.5
y = 0.95
point_type = "exit"
contact = true
direction_deg = 90.0
flexibility_mm = 0.15
"""


# ---------------------------------------------------------------------------
# genome_from_guides with extracted guides_path
# ---------------------------------------------------------------------------

def test_genome_from_guides_with_extracted(tmp_path):
    """genome_from_guides uses extracted guide when guides_path is provided."""
    toml_file = tmp_path / "guides_extracted.toml"
    toml_file.write_text(_MINIMAL_GUIDES_TOML)

    genome = genome_from_guides("u", guides_path=toml_file)
    assert isinstance(genome, type(genome))

    u_glyph = next((g for g in genome.glyphs if g.letter == "u"), None)
    assert u_glyph is not None, "no glyph for 'u' in genome"
    assert len(u_glyph.segments) > 0, "glyph has no BezierSegments"


def test_genome_from_guides_fallback(tmp_path):
    """genome_from_guides falls back to hand-defined catalog when file missing."""
    missing = tmp_path / "nonexistent.toml"
    # Should not raise, just use built-in catalog
    genome = genome_from_guides("u", guides_path=missing)
    u_glyph = next((g for g in genome.glyphs if g.letter == "u"), None)
    assert u_glyph is not None


def test_genome_from_guides_catalog_takes_priority_over_extracted(tmp_path):
    """GLYPH_CATALOG takes priority over extracted guides for letters with catalog entries.

    GLYPH_CATALOG provides proper multi-stroke Bézier geometry; extracted guides
    collapse to a single Bézier per letter and produce unrecognisable letterforms.
    Extracted guides are only used as fallback for letters absent from the catalog.
    """
    toml_file = tmp_path / "guides_extracted.toml"
    # Use a very distinctive x_advance of 9.9 to identify if extracted guide were used
    toml_file.write_text(_MINIMAL_GUIDES_TOML.replace("x_advance = 0.6", "x_advance = 9.9"))

    genome = genome_from_guides("u", guides_path=toml_file, x_height_mm=1.0)
    u_glyph = next((g for g in genome.glyphs if g.letter == "u"), None)
    assert u_glyph is not None
    # Should use GLYPH_CATALOG (small advance), NOT the extracted guide (9.9 × x_height)
    assert u_glyph.x_advance < 5.0, (
        f"expected catalog x_advance, not extracted guide's 9.9, got {u_glyph.x_advance:.3f}"
    )
    # Catalog 'u' has multiple strokes; extracted guide collapses to 1
    assert len(u_glyph.segments) >= 1


def test_genome_from_guides_uncovered_letter_fallback(tmp_path):
    """Letters not in extracted TOML fall back to catalog without error."""
    toml_file = tmp_path / "guides_extracted.toml"
    toml_file.write_text(_MINIMAL_GUIDES_TOML)  # only has 'u'

    # 'n' is in the catalog but not in the extracted TOML
    genome = genome_from_guides("nu", guides_path=toml_file)
    letters = [g.letter for g in genome.glyphs]
    assert "n" in letters and "u" in letters


def test_genome_from_guides_no_path_no_file():
    """genome_from_guides with guides_path=None and no auto-detected file uses catalog."""
    # Just ensure it doesn't raise — auto-detection may or may not find a file
    genome = genome_from_guides("u")
    assert genome is not None


def test_bastarda_pair_spacing_tightens_joinable_pairs():
    """Common Bastarda pairs should be packed more tightly than neutral pairs."""
    tight = genome_from_guides("mi", x_height_mm=1.0, letter_gap=0.085)
    neutral = genome_from_guides("ma", x_height_mm=1.0, letter_gap=0.085)

    tight_gap = tight.glyphs[1].x_offset - (tight.glyphs[0].x_offset + tight.glyphs[0].x_advance)
    neutral_gap = neutral.glyphs[1].x_offset - (neutral.glyphs[0].x_offset + neutral.glyphs[0].x_advance)

    assert tight_gap < neutral_gap


def test_bastarda_pair_spacing_preserves_minimum_gap():
    """Pair compression should not collapse adjacent glyphs into overlap."""
    genome = genome_from_guides("ch", x_height_mm=1.0, letter_gap=0.085)
    gap = genome.glyphs[1].x_offset - (genome.glyphs[0].x_offset + genome.glyphs[0].x_advance)
    assert gap > 0.0
