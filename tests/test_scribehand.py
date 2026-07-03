"""Tests for scribesim.scribehand core — TD-018 learned hand synthesis wrapper.

Covers: deterministic seed policy, word strips, PIL stub backend, generation
cache + provenance, CER, stub HTR scorer, rejection-sampling verification,
command backend protocol (fake runner), style anchor loading, and modifier
mapping. No torch / no network — heavyweight backends are exercised on the
Mac workstation via the same contracts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from scribesim.scribehand.types import WordRequest, WordStrip
from scribesim.scribehand.seeds import word_seed
from scribesim.scribehand.backends.stub import PILStubBackend
from scribesim.scribehand.backends.command import CommandBackend
from scribesim.scribehand.generate import WordGenerator
from scribesim.scribehand.htr import cer, StubScorer
from scribesim.scribehand.verify import verify_words
from scribesim.scribehand.style import StyleAnchor, load_style_anchor
from scribesim.scribehand.modifiers import controls_from_profile
from scribesim.hand.profile import load_profile


# ---------------------------------------------------------------------------
# seeds
# ---------------------------------------------------------------------------

class TestSeeds:
    def test_deterministic(self):
        assert word_seed(1457, "f01r", 3, 2) == word_seed(1457, "f01r", 3, 2)

    def test_distinct_by_position(self):
        seeds = {
            word_seed(1457, "f01r", li, wi)
            for li in range(5) for wi in range(5)
        }
        assert len(seeds) == 25

    def test_distinct_by_folio(self):
        assert word_seed(1457, "f01r", 0, 0) != word_seed(1457, "f01v", 0, 0)


# ---------------------------------------------------------------------------
# stub backend
# ---------------------------------------------------------------------------

class TestPILStubBackend:
    def test_generates_strip(self):
        be = PILStubBackend()
        req = WordRequest(text="und", seed=42)
        strip = be.generate_batch([req])[0]
        assert isinstance(strip, WordStrip)
        assert strip.ink.dtype == np.uint8
        assert strip.ink.ndim == 2
        assert strip.ink.max() > 0            # some ink present
        assert 0.0 < strip.baseline_frac <= 1.0
        assert 0.0 < strip.xheight_frac < 1.0

    def test_deterministic(self):
        be = PILStubBackend()
        a = be.generate_batch([WordRequest(text="der", seed=7)])[0]
        b = be.generate_batch([WordRequest(text="der", seed=7)])[0]
        assert np.array_equal(a.ink, b.ink)

    def test_wider_text_wider_strip(self):
        be = PILStubBackend()
        short = be.generate_batch([WordRequest(text="in", seed=1)])[0]
        long = be.generate_batch([WordRequest(text="schreiber", seed=1)])[0]
        assert long.ink.shape[1] > short.ink.shape[1]


# ---------------------------------------------------------------------------
# generator + cache
# ---------------------------------------------------------------------------

class TestWordGenerator:
    def test_generate_returns_provenance(self, tmp_path: Path):
        gen = WordGenerator(PILStubBackend(), cache_dir=tmp_path / "cache")
        res = gen.generate([WordRequest(text="und", seed=3)])[0]
        assert res.strip.ink.max() > 0
        assert res.provenance["backend"] == "stub-pil"
        assert res.provenance["seed"] == 3
        assert res.provenance["cache_hit"] is False

    def test_cache_hit_on_repeat(self, tmp_path: Path):
        gen = WordGenerator(PILStubBackend(), cache_dir=tmp_path / "cache")
        first = gen.generate([WordRequest(text="und", seed=3)])[0]
        second = gen.generate([WordRequest(text="und", seed=3)])[0]
        assert second.provenance["cache_hit"] is True
        assert np.array_equal(first.strip.ink, second.strip.ink)

    def test_different_seed_misses_cache(self, tmp_path: Path):
        gen = WordGenerator(PILStubBackend(), cache_dir=tmp_path / "cache")
        gen.generate([WordRequest(text="und", seed=3)])
        res = gen.generate([WordRequest(text="und", seed=4)])[0]
        assert res.provenance["cache_hit"] is False


# ---------------------------------------------------------------------------
# HTR: cer + stub scorer + verification loop
# ---------------------------------------------------------------------------

class TestCER:
    def test_exact(self):
        assert cer("und", "und") == 0.0

    def test_substitution(self):
        assert cer("und", "unt") == pytest.approx(1 / 3)

    def test_empty_ref(self):
        assert cer("", "") == 0.0
        assert cer("", "x") == 1.0


class TestVerify:
    def test_all_pass_with_echo_scorer(self, tmp_path: Path):
        gen = WordGenerator(PILStubBackend(), cache_dir=tmp_path / "c")
        scorer = StubScorer(mode="echo")
        results = verify_words(
            gen, scorer,
            [WordRequest(text="und", seed=1), WordRequest(text="der", seed=2)],
            cer_threshold=0.05, max_retries=2,
        )
        assert all(r.provenance["verified"] for r in results)
        assert all(r.provenance["htr_cer"] == 0.0 for r in results)
        assert all(r.provenance["retries"] == 0 for r in results)

    def test_garble_scorer_exhausts_retries(self, tmp_path: Path):
        gen = WordGenerator(PILStubBackend(), cache_dir=tmp_path / "c")
        scorer = StubScorer(mode="garble")
        results = verify_words(
            gen, scorer, [WordRequest(text="und", seed=1)],
            cer_threshold=0.05, max_retries=2,
        )
        r = results[0]
        assert r.provenance["verified"] is False
        assert r.provenance["retries"] == 2
        assert r.provenance["htr_cer"] > 0.05

    def test_flaky_scorer_recovers_on_retry(self, tmp_path: Path):
        gen = WordGenerator(PILStubBackend(), cache_dir=tmp_path / "c")

        class FlakyScorer:
            calls = 0
            def read(self, images, expected=None):
                out = []
                for _ in images:
                    self.calls += 1
                    out.append("xxx" if self.calls == 1 else (expected or [""])[0])
                return out

        results = verify_words(
            gen, FlakyScorer(), [WordRequest(text="und", seed=1)],
            cer_threshold=0.05, max_retries=2,
        )
        r = results[0]
        assert r.provenance["verified"] is True
        assert r.provenance["retries"] == 1
        # retry must have used a different seed
        assert r.provenance["seed"] != 1


# ---------------------------------------------------------------------------
# command backend (Mac runner protocol) with a fake runner
# ---------------------------------------------------------------------------

_FAKE_RUNNER = '''
import json, sys
from PIL import Image, ImageDraw

def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    req = json.load(open(args["--request"]))
    results = []
    for w in req["words"]:
        img = Image.new("L", (16 * max(1, len(w["text"])), 48), 0)
        d = ImageDraw.Draw(img)
        d.text((2, 10), w["text"], fill=255)
        img.save(w["out"])
        results.append({"id": w["id"], "image": w["out"],
                        "baseline_frac": 0.72, "xheight_frac": 0.33})
    json.dump({"schema": 1, "results": results,
               "runner": {"name": "fake", "device": "cpu"}},
              open(args["--response"], "w"))

main()
'''


class TestCommandBackend:
    def test_roundtrip_with_fake_runner(self, tmp_path: Path):
        runner = tmp_path / "fake_runner.py"
        runner.write_text(_FAKE_RUNNER)
        be = CommandBackend(
            name="fake",
            argv=[sys.executable, str(runner)],
            workdir=tmp_path,
        )
        reqs = [WordRequest(text="und", seed=1), WordRequest(text="der", seed=2)]
        strips = be.generate_batch(reqs)
        assert len(strips) == 2
        assert strips[0].ink.max() > 0
        assert strips[0].baseline_frac == pytest.approx(0.72)

    def test_missing_result_raises(self, tmp_path: Path):
        bad = tmp_path / "bad_runner.py"
        bad.write_text(
            "import json,sys\n"
            "args=dict(zip(sys.argv[1::2],sys.argv[2::2]))\n"
            "json.dump({'schema':1,'results':[]},open(args['--response'],'w'))\n"
        )
        be = CommandBackend(name="bad", argv=[sys.executable, str(bad)], workdir=tmp_path)
        with pytest.raises(RuntimeError):
            be.generate_batch([WordRequest(text="und", seed=1)])


# ---------------------------------------------------------------------------
# style anchor
# ---------------------------------------------------------------------------

class TestStyleAnchor:
    def test_load(self, tmp_path: Path):
        d = tmp_path / "style_anchor_v1"
        d.mkdir()
        from PIL import Image
        Image.new("L", (32, 32), 128).save(d / "ex1.png")
        (d / "style.json").write_text(json.dumps({
            "id": "anchor_v1",
            "description": "test anchor",
            "exemplars": ["ex1.png"],
            "source": {"shelfmark": "Cgm 628"},
        }))
        anchor = load_style_anchor(d)
        assert isinstance(anchor, StyleAnchor)
        assert anchor.id == "anchor_v1"
        assert len(anchor.exemplar_paths) == 1
        assert anchor.exemplar_paths[0].exists()

    def test_missing_exemplar_fails(self, tmp_path: Path):
        d = tmp_path / "style"
        d.mkdir()
        (d / "style.json").write_text(json.dumps({
            "id": "x", "exemplars": ["nope.png"], "source": {},
        }))
        with pytest.raises(FileNotFoundError):
            load_style_anchor(d)


# ---------------------------------------------------------------------------
# CLIO-7 modifier mapping
# ---------------------------------------------------------------------------

class TestModifierMapping:
    def test_baseline_profile_maps_to_neutral_controls(self):
        profile = load_profile(None)
        c = controls_from_profile(profile)
        assert 0.0 <= c.style_noise <= 1.0
        assert c.x_height_scale == pytest.approx(1.0, abs=0.2)
        assert 0.5 <= c.ink_darkness <= 1.2

    def test_pressure_shift_changes_ink_darkness(self):
        profile = load_profile(None)
        heavy = profile.apply_delta({"folio.base_pressure": profile.folio.base_pressure + 0.3})
        c0 = controls_from_profile(profile)
        c1 = controls_from_profile(heavy)
        assert c1.ink_darkness > c0.ink_darkness

    def test_controls_serialize(self):
        profile = load_profile(None)
        d = controls_from_profile(profile).to_dict()
        assert set(d) >= {"style_noise", "guidance_scale", "x_height_scale", "ink_darkness"}
