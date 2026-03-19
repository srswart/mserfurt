"""Tests for xl.annotate.annotator — CLIO-7 apparatus overlay on FolioPage objects.

TDD discipline: tests written before implementation.
All tests must fail (red) until xl/annotate/annotator.py is written.
"""

from __future__ import annotations

import pytest
from xl.models import Annotation, FolioPage, Line, DamageType
from xl.annotate.annotator import annotate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_page(folio_id: str, line_texts: list[str], register: str = "de") -> FolioPage:
    folio_num = int(folio_id[1:3])
    lines = [Line(number=i + 1, text=t, register=register) for i, t in enumerate(line_texts)]
    return FolioPage(
        id=folio_id,
        recto_verso="recto" if folio_id.endswith("r") else "verso",
        gathering_position=folio_num,
        lines=lines,
        damage=None,
        hand_notes=None,
    )


def _damaged_page(folio_id: str, line_texts: list[str], damage: dict) -> FolioPage:
    page = _clean_page(folio_id, line_texts)
    page.damage = damage
    return page


def _confidence_score(line: Line) -> float | None:
    """Return the confidence score annotation on a line, or None if absent."""
    for ann in line.annotations:
        if ann.type == "confidence":
            return ann.detail.get("score")
    return None


def _has_annotation_type(line: Line, ann_type: str) -> bool:
    return any(a.type == ann_type for a in line.annotations)


# ---------------------------------------------------------------------------
# Test: clean page confidence
# ---------------------------------------------------------------------------

class TestCleanPageConfidence:
    def test_all_lines_get_confidence_annotation(self):
        """Every line on every page must receive a confidence annotation after annotate()."""
        page = _clean_page("f01r", ["Wort eins", "Wort zwei", "Wort drei"])
        [annotated] = annotate([page])
        for line in annotated.lines:
            assert _has_annotation_type(line, "confidence"), (
                f"Line {line.number} on {annotated.id} has no confidence annotation"
            )

    def test_clean_page_high_confidence(self):
        """Clean page (no damage) must have confidence ≥ 0.95 on all lines."""
        page = _clean_page("f01r", ["Incipit text", "More text", "Final line"])
        [annotated] = annotate([page])
        for line in annotated.lines:
            score = _confidence_score(line)
            assert score is not None
            assert score >= 0.95, f"Line {line.number}: expected ≥ 0.95, got {score}"

    def test_f06r_clean_after_gap(self):
        """f06r (workshop resumption, no damage) should also carry high confidence."""
        page = _clean_page("f06r", ["Und so kehrte ich wieder zurück"])
        [annotated] = annotate([page])
        score = _confidence_score(annotated.lines[0])
        assert score is not None and score >= 0.95


# ---------------------------------------------------------------------------
# Test: damaged page confidence
# ---------------------------------------------------------------------------

class TestDamagedPageConfidence:
    def test_f04r_reduced_confidence(self):
        """f04r (water, partial) → confidence ≤ 0.70."""
        damage = {"type": DamageType.WATER, "extent": "partial", "direction": "from_above"}
        page = _damaged_page("f04r", ["Damaged text here", "More damaged text"], damage)
        [annotated] = annotate([page])
        for line in annotated.lines:
            score = _confidence_score(line)
            assert score is not None and score <= 0.70, (
                f"f04r line {line.number}: expected ≤ 0.70, got {score}"
            )

    def test_f04v_severely_reduced_confidence(self):
        """f04v (water severe + missing corner) → confidence ≤ 0.45."""
        damage = {
            "type": DamageType.WATER, "extent": "severe",
            "direction": "from_above", "corner": "bottom_right",
        }
        page = _damaged_page("f04v", ["Severely damaged text", "Partial words here"], damage)
        [annotated] = annotate([page])
        for line in annotated.lines:
            score = _confidence_score(line)
            assert score is not None and score <= 0.45, (
                f"f04v line {line.number}: expected ≤ 0.45, got {score}"
            )

    def test_partial_damage_lower_than_clean(self):
        """Partial damage confidence must be lower than clean page confidence."""
        clean = _clean_page("f01r", ["Clean line"])
        damaged = _damaged_page("f04r", ["Damaged line"],
                                {"type": DamageType.WATER, "extent": "partial"})
        [ann_clean], [ann_damaged] = annotate([clean]), annotate([damaged])
        clean_score = _confidence_score(ann_clean.lines[0])
        damaged_score = _confidence_score(ann_damaged.lines[0])
        assert damaged_score < clean_score, (
            f"Expected damaged ({damaged_score}) < clean ({clean_score})"
        )

    def test_severe_damage_lower_than_partial(self):
        """Severe damage confidence must be lower than partial damage."""
        partial = _damaged_page("f04r", ["Partial line"],
                                {"type": DamageType.WATER, "extent": "partial"})
        severe = _damaged_page("f04v", ["Severe line"],
                               {"type": DamageType.WATER, "extent": "severe", "corner": "bottom_right"})
        [ann_partial], [ann_severe] = annotate([partial]), annotate([severe])
        partial_score = _confidence_score(ann_partial.lines[0])
        severe_score = _confidence_score(ann_severe.lines[0])
        assert severe_score < partial_score, (
            f"Expected severe ({severe_score}) < partial ({partial_score})"
        )


# ---------------------------------------------------------------------------
# Test: lacuna detection
# ---------------------------------------------------------------------------

class TestLacunaDetection:
    def test_lacuna_marker_gets_lacuna_annotation(self):
        """A line containing '[—]' must receive a lacuna annotation."""
        page = _clean_page("f04r", ["He told me [—] the light was good"])
        page.damage = {"type": DamageType.WATER, "extent": "partial"}
        [annotated] = annotate([page])
        assert _has_annotation_type(annotated.lines[0], "lacuna"), (
            "Line with '[—]' must have a lacuna annotation"
        )

    def test_lacuna_line_confidence_is_zero(self):
        """A line with '[—]' must have confidence 0.0 (text is lost)."""
        page = _clean_page("f04r", ["I said [—] and then walked away"])
        [annotated] = annotate([page])
        score = _confidence_score(annotated.lines[0])
        assert score == 0.0, f"Lacuna line should have confidence 0.0, got {score}"

    def test_non_lacuna_line_unaffected(self):
        """Lines without '[—]' must not have a lacuna annotation."""
        page = _clean_page("f01r", ["This line has no lacuna", "Nor does this one"])
        [annotated] = annotate([page])
        for line in annotated.lines:
            assert not _has_annotation_type(line, "lacuna"), (
                f"Line {line.number} falsely marked as lacuna: '{line.text}'"
            )

    def test_lacuna_annotation_placed_on_correct_line(self):
        """Lacuna annotation should only appear on the line that contains '[—]', not neighbours."""
        page = _clean_page("f04r", [
            "Clean first line",
            "The missing part [—] goes here",
            "Clean third line",
        ])
        [annotated] = annotate([page])
        assert not _has_annotation_type(annotated.lines[0], "lacuna")
        assert _has_annotation_type(annotated.lines[1], "lacuna")
        assert not _has_annotation_type(annotated.lines[2], "lacuna")


# ---------------------------------------------------------------------------
# Test: exactly one confidence annotation per line
# ---------------------------------------------------------------------------

class TestSingleConfidenceAnnotation:
    def test_each_line_has_exactly_one_confidence_annotation(self):
        """Each line must have exactly one confidence annotation."""
        page = _clean_page("f01r", ["Line one", "Line two", "Line three"])
        [annotated] = annotate([page])
        for line in annotated.lines:
            conf_anns = [a for a in line.annotations if a.type == "confidence"]
            assert len(conf_anns) == 1, (
                f"Line {line.number}: expected 1 confidence annotation, got {len(conf_anns)}"
            )


# ---------------------------------------------------------------------------
# Test: idempotency
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_annotating_twice_does_not_double_annotate(self):
        """Calling annotate() on an already-annotated page must not add duplicate annotations."""
        page = _clean_page("f01r", ["Already annotated line"])
        [first_pass] = annotate([page])
        # Feed the already-annotated page through again
        [second_pass] = annotate([first_pass])
        for line in second_pass.lines:
            conf_anns = [a for a in line.annotations if a.type == "confidence"]
            assert len(conf_anns) == 1, (
                f"Double-annotated: {len(conf_anns)} confidence annotations on line {line.number}"
            )

    def test_annotate_returns_same_page_objects(self):
        """annotate() should return the same FolioPage objects (mutated in place)."""
        page = _clean_page("f01r", ["Some text"])
        [result] = annotate([page])
        assert result is page, "annotate() should mutate pages in place and return them"


# ---------------------------------------------------------------------------
# Test: empty pages
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_page_returns_no_annotations(self):
        """A page with no lines should not raise and should return an empty page."""
        page = FolioPage(id="f01r", recto_verso="recto", gathering_position=1)
        [result] = annotate([page])
        assert result.lines == []

    def test_multiple_pages_all_annotated(self):
        """All pages in the input list must be returned with confidence annotations."""
        pages = [
            _clean_page("f01r", ["Line on f01r"]),
            _damaged_page("f04r", ["Line on f04r"],
                          {"type": DamageType.WATER, "extent": "partial"}),
        ]
        results = annotate(pages)
        assert len(results) == 2
        for p in results:
            for line in p.lines:
                assert _has_annotation_type(line, "confidence")
