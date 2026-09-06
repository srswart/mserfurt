import copy
import json
import subprocess
import sys
from dataclasses import asdict, replace

import numpy as np
import pytest

from scribesim.evofit.repertoire import compose, refresh_form, seed_repertoire
from scribesim.pathguide.repertoire import convert_word, load_bundle, save_bundle, require_g1
from scribesim.handvalidate.bridge import compare_bridge, run_bridge


def test_arc_length_orientation_lifts_and_exact_ownership(tmp_path):
    hand = seed_repertoire("sins")
    bundle = convert_word("sins", hand, step_mm=.05)
    guide = bundle.guide
    assert guide.kind == "word"
    assert bundle.metadata["plan"] == compose("sins", hand)
    assert guide.x_height_mm == hand["x_height_mm"]
    assert min(sample.y_mm for sample in guide.samples) < bundle.metadata["baseline_y_mm"]
    assert any(not sample.contact for sample in guide.samples)
    assert len(bundle.metadata["owners"]) == len(guide.samples)
    assert all(owner["spans"] for owner, sample in zip(bundle.metadata["owners"], guide.samples) if sample.contact)
    points = np.array([[sample.x_mm, sample.y_mm] for sample in guide.samples])
    assert np.linalg.norm(np.diff(points, axis=0), axis=1).max() <= .051
    save_bundle(bundle, tmp_path / "guide.json")
    assert asdict(load_bundle(tmp_path / "guide.json")) == asdict(bundle)
    payload = json.loads((tmp_path / "guide.json").read_text())
    del payload["metadata"]["owners"]
    (tmp_path / "guide.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        load_bundle(tmp_path / "guide.json")


def test_ligature_loop_crossing_and_contact_join_survive():
    hand = seed_repertoire("in", variants=False)
    form = copy.deepcopy(hand["forms"]["i:catalog"])
    form.update(logical="in", visible="in", mapping="ligature", advance=1)
    form["chains"] = [{"cubics": [[[0, 0], [1, 1], [-1, 1], [0, 0]]]}]
    refresh_form(form)
    hand["forms"]["in:loop"] = form
    hand["rules"] = [{"form_id": "in:loop", "position": "any", "previous": None, "next": None, "cost": -1}]
    hand["joins"] = [{"left": "in:loop", "right": "in:loop", "kind": "contact", "cost": -1}]
    bundle = convert_word("inin", hand)
    assert any(owner["spans"] == [[0, 2], [2, 4]] for owner in bundle.metadata["owners"])
    assert all(sample.contact for sample in bundle.guide.samples)


def test_actual_not_aligned_trajectory_is_authoritative():
    hand = seed_repertoire("in", variants=False)
    bundle = convert_word("in", hand)
    first = compare_bridge(bundle, hand)
    assert len(first["result"].trajectory_plan_indices) == len(first["result"].trajectory)
    shifted = replace(first["result"], trajectory=tuple(replace(sample, x_mm=sample.x_mm + 3)
                                                       for sample in first["result"].trajectory))
    second = compare_bridge(bundle, hand, result=shifted)
    assert second["metrics"]["actual_corridor_error_mm"] > first["metrics"]["actual_corridor_error_mm"] + 1
    assert second["metrics"]["actual_image_loss"] > first["metrics"]["actual_image_loss"]
    assert first["metrics"]["sampled_image_loss"] < .15
    assert first["metrics"]["coverage"] == 1


def test_gate_cannot_be_forged_with_a_summary(tmp_path):
    (tmp_path / "G1.json").write_text('{"gate":"G1","status":"pass"}')
    with pytest.raises(ValueError, match="G1"):
        require_g1(tmp_path)
    from scribesim.handvalidate.nominal import DEFAULT_DATASET, DEFAULT_BENCHMARK
    nominal = DEFAULT_BENCHMARK.parent / "nominal_specimen_v1"
    with pytest.raises(ValueError, match="G1"):
        require_g1(nominal, dataset_root=DEFAULT_DATASET, benchmark_root=DEFAULT_BENCHMARK)
    decision = run_bridge(tmp_path / "blocked", nominal_root=nominal)
    assert decision["status"] == "blocked"
    assert decision["executed"] is False


def test_clean_import_does_not_require_ignored_extraction_modules():
    script = """
import sys
class RejectExtraction:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('scribesim.refextract'):
            raise ImportError('ignored extraction dependency')
sys.meta_path.insert(0, RejectExtraction())
from scribesim.pathguide.repertoire import convert_word
from scribesim.handflow import GuidedHandFlowController
"""
    subprocess.run([sys.executable, "-c", script], check=True)
