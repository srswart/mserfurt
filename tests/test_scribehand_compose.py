"""Tests for neural page composition — TD-018 §2.5–§2.6.

Covers: folio composition geometry, determinism, unverified-word refusal,
word-level PAGE XML emission, overflow gap compression, and lacuna opacity.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

from scribesim.hand.profile import load_profile
from scribesim.scribehand.backends.stub import PILStubBackend
from scribesim.scribehand.generate import WordGenerator
from scribesim.scribehand.htr import StubScorer
from scribesim.scribehand.compose import compose_folio, ComposeError
from scribesim.scribehand.pagexml import generate_word_level


def _folio(lines: list[str], fid: str = "f01r") -> dict:
    return {
        "id": fid,
        "recto_verso": "recto" if fid.endswith("r") else "verso",
        "lines": [
            {"number": i + 1, "text": t, "register": "de", "annotations": []}
            for i, t in enumerate(lines)
        ],
        "metadata": {"line_count": len(lines)},
    }


@pytest.fixture()
def generator(tmp_path: Path) -> WordGenerator:
    return WordGenerator(PILStubBackend(), cache_dir=tmp_path / "cache")


class TestComposeFolio:
    def test_page_dimensions_standard(self, generator):
        result = compose_folio(
            _folio(["und der schreiber", "in dem jar"]),
            load_profile(None), generator, scorer=StubScorer("echo"), dpi=300,
        )
        h, w, _ = result.page.shape
        assert w == int(185.0 * 300 / 25.4)
        assert h == int(250.0 * 300 / 25.4)

    def test_ink_present_and_words_recorded(self, generator):
        result = compose_folio(
            _folio(["und der", "in"]), load_profile(None), generator,
            scorer=StubScorer("echo"), dpi=300,
        )
        assert result.page.min() < 200          # some ink darker than parchment
        assert len(result.lines) == 2
        assert [w.text for w in result.lines[0].words] == ["und", "der"]
        w0 = result.lines[0].words[0]
        assert w0.x_px >= 0 and w0.w_px > 0 and w0.h_px > 0

    def test_deterministic_for_fixed_seed(self, generator):
        folio = _folio(["und der"])
        profile = load_profile(None)
        a = compose_folio(folio, profile, generator, scorer=StubScorer("echo"),
                          dpi=300, base_seed=99)
        b = compose_folio(folio, profile, generator, scorer=StubScorer("echo"),
                          dpi=300, base_seed=99)
        assert np.array_equal(a.page, b.page)

    def test_refuses_unverified_words_by_default(self, generator):
        with pytest.raises(ComposeError):
            compose_folio(
                _folio(["und"]), load_profile(None), generator,
                scorer=StubScorer("garble"), dpi=300,
            )

    def test_allow_unverified_flag(self, generator):
        result = compose_folio(
            _folio(["und"]), load_profile(None), generator,
            scorer=StubScorer("garble"), dpi=300, allow_unverified=True,
        )
        assert result.report["unverified_words"] == 1

    def test_no_scorer_marks_unscored(self, generator):
        result = compose_folio(
            _folio(["und der"]), load_profile(None), generator,
            scorer=None, dpi=300,
        )
        assert result.report["scored"] is False

    def test_long_line_compresses_gaps_to_fit(self, generator):
        text = " ".join(["schreiber"] * 6)   # ~15% wider than the text block
        result = compose_folio(
            _folio([text]), load_profile(None), generator,
            scorer=StubScorer("echo"), dpi=300,
        )
        geom = result.geometry
        right_edge_mm = geom.page_w_mm - geom.margin_outer
        last = result.lines[0].words[-1]
        px_per_mm = 300 / 25.4
        assert (last.x_px + last.w_px) / px_per_mm <= right_edge_mm + 1.0

    def test_lacuna_annotation_fades_line(self, generator):
        folio = _folio(["und der", "und der"])
        folio["lines"][1]["annotations"] = [{
            "type": "lacuna",
            "span": {"char_start": 0, "char_end": 7},
            "detail": {"reason": "water_damage"},
        }]
        result = compose_folio(folio, load_profile(None), generator,
                               scorer=StubScorer("echo"), dpi=300)
        # Ink coverage on the faded line should be lighter than the intact line.
        def line_min(idx):
            words = result.lines[idx].words
            y0 = min(w.y_px for w in words); y1 = max(w.y_px + w.h_px for w in words)
            return result.page[y0:y1].min()
        assert line_min(1) > line_min(0)

    def test_verso_uses_outer_left_margin(self, generator):
        recto = compose_folio(_folio(["und"], fid="f01r"), load_profile(None),
                              generator, scorer=None, dpi=300)
        verso = compose_folio(_folio(["und"], fid="f01v"), load_profile(None),
                              generator, scorer=None, dpi=300)
        assert verso.lines[0].words[0].x_px > recto.lines[0].words[0].x_px


class TestWordLevelPageXML:
    def test_generates_valid_page_xml(self, generator, tmp_path: Path):
        result = compose_folio(_folio(["und der", "in"]), load_profile(None),
                               generator, scorer=StubScorer("echo"), dpi=300)
        out = tmp_path / "f01r.xml"
        generate_word_level(result, out)
        tree = ET.parse(out)
        ns = {"pc": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"}
        words = tree.getroot().findall(".//pc:Word", ns)
        assert len(words) == 3
        texts = [w.find(".//pc:Unicode", ns).text for w in words]
        assert texts == ["und", "der", "in"]
        # every word has a coords polygon
        assert all(w.find("pc:Coords", ns) is not None for w in words)

    def test_line_text_equivalence(self, generator, tmp_path: Path):
        result = compose_folio(_folio(["und der"]), load_profile(None),
                               generator, scorer=StubScorer("echo"), dpi=300)
        out = tmp_path / "f.xml"
        generate_word_level(result, out)
        ns = {"pc": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"}
        tree = ET.parse(out)
        line = tree.getroot().find(".//pc:TextLine", ns)
        line_text = line.find("pc:TextEquiv/pc:Unicode", ns).text
        assert line_text == "und der"
