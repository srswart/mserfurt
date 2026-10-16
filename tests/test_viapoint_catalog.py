"""Unit tests for ADV-SS-GUIDES-002: Full Bastarda Via-Point Alphabet,
TD-012 Contextual Allograph Selection, 1.0 Exact Corpus Coverage,
and Tier-1 A4-TOPOLOGY Open-Counter & Collision Gate.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from scribesim.guides.viapoint_catalog import (
    COUNTER_LETTERS,
    VIAPOINT_CATALOG,
    check_corpus_exact_coverage,
    select_contextual_viapoint_recipe,
)
from scribesim.hand.profile import bastarda_nib_calibrated_profile
from scribesim.handflow.coarticulate import solve_word_coarticulation
from scribesim.handvalidate.kinematic_gates import evaluate_a4_topology


def test_full_bastarda_viapoint_catalog_and_corpus_coverage() -> None:
    """VIAPOINT_CATALOG covers all lowercase, uppercase, Bastarda specials, and 100% of output-live."""
    for ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        assert ch in VIAPOINT_CATALOG, f"Missing {ch!r}"
    for special in ("ſ", "ß", "ä", "ö", "ü", "Ä", "Ö", "Ü", "ê", "î", "⁊", "✦", "¶"):
        assert special in VIAPOINT_CATALOG, f"Missing special {special!r}"

    cov = check_corpus_exact_coverage(Path("output-live"))
    assert cov["exact_coverage"] == 1.0, f"Missing chars: {cov['missing_characters']}"
    assert cov["alias_substitutions"] == 0
    assert cov["missing_characters"] == []


def test_contextual_allograph_selection_rules() -> None:
    """TD-012 contextual selector picks long-s initially/medially, round-s finally, and adapts entries."""
    # "seines": index 0 ('s') -> long_s ('ſ'), index 5 ('s') -> round 's'
    r_init = select_contextual_viapoint_recipe("seines", 0)
    r_final = select_contextual_viapoint_recipe("seines", 5)
    assert r_init.letter == "ſ"
    assert r_final.letter == "s"

    # High-exit predecessor ('r' exits high at ~3.45 w_nib) vs baseline-exit predecessor ('n' exits at ~0.85 w_nib)
    e_after_r = select_contextual_viapoint_recipe("re", 1)
    e_after_n = select_contextual_viapoint_recipe("ne", 1)
    assert e_after_r.via_points[0].y_wnib > e_after_n.via_points[0].y_wnib


def test_tier1_a4_topology_open_counters_and_collision_check() -> None:
    """Tier-1 A4-TOPOLOGY verifies open counters in (a, o, d, e, g, b, p) and zero non-adjacent collisions."""
    profile = bastarda_nib_calibrated_profile()
    assert set(COUNTER_LETTERS) == {"a", "o", "d", "e", "g", "b", "p"}

    verdict = evaluate_a4_topology(
        profile=profile,
        words=("und", "glauben", "schreiber"),
    )
    assert verdict["gate"] == "A4-TOPOLOGY"
    assert verdict["passed"] is True, f"A4-TOPOLOGY failed: {verdict}"
    for ch in COUNTER_LETTERS:
        assert verdict["letter_counters"][ch]["open_counter_count"] >= 1
    assert verdict["non_adjacent_collisions"] == 0

    # Solving words with umlauts, capitals, and punctuation works cleanly
    res = solve_word_coarticulation("Brüder", profile=profile)
    assert len(res.samples) > 30
