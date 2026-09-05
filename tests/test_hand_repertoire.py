import copy
import json
import os
import subprocess
import sys

import numpy as np
import pytest

from scribesim.evofit.repertoire import (
    compose, refresh_form, render_nominal, render_key, seed_repertoire, validate_repertoire,
)
from scribesim.handvalidate.specimen import object_digest


def test_roundtrip_exact_mapping_lifts_and_shared_occurrences():
    hand = seed_repertoire("sins")
    hand = json.loads(json.dumps(hand))
    validate_repertoire(hand)
    plan = compose("sins", hand)
    assert plan["text"] == "sins"
    assert plan["coverage"] == 1
    assert plan["occurrences"][0]["visible"] == "ſ"
    assert plan["occurrences"][-1]["visible"] == "s"
    assert all(transition["kind"] == "air" for transition in plan["transitions"])
    repeated = compose("nn", hand)
    assert repeated["occurrences"][0]["form_id"] == repeated["occurrences"][1]["form_id"]
    before = render_nominal("nn", hand)
    for form in hand["forms"].values():
        if form["logical"] == "n":
            for chain in form["chains"]:
                for cubic in chain["cubics"]:
                    for point in cubic:
                        point[0] *= 1.4
            refresh_form(form)
    assert not np.array_equal(before, render_nominal("nn", hand))
    assert hand["acceptance"] == "unaccepted"


@pytest.mark.parametrize("text", ["á", "a\u0301", "a\t", "", "   "])
def test_unsupported_or_implicit_normalization_fails(text):
    with pytest.raises(ValueError):
        compose(text, seed_repertoire("a"))


def test_alternate_loop_ligature_ownership_and_crossings():
    hand = seed_repertoire("in", variants=False)
    form = copy.deepcopy(hand["forms"]["i:catalog"])
    form.update(logical="in", visible="in", mapping="ligature", advance=1.0)
    form["chains"] = [{"cubics": [[[0, 0], [1, 1], [-1, 1], [0, 0]]]}]
    form["allow_intersections"] = True
    refresh_form(form)
    hand["forms"]["in:loop"] = form
    hand["rules"] = [{"form_id": "in:loop", "position": "any", "previous": None,
                      "next": None, "cost": -1.0}]
    plan = compose("inin", hand)
    assert [row["span"] for row in plan["occurrences"]] == [[0, 2], [2, 4]]
    assert plan["contact_ownership"] == [{"occurrence": 0, "chain": 0, "span": [0, 2]},
                                          {"occurrence": 1, "chain": 0, "span": [2, 4]}]
    assert form["chains"][0]["closed"]
    assert render_nominal("inin", hand).size


@pytest.mark.parametrize("mutation,match", [
    (lambda hand: hand["forms"]["a:catalog"].update(visible="o"), "mapping"),
    (lambda hand: hand["forms"]["a:catalog"].update(word_image="bad"), "fields"),
    (lambda hand: hand["forms"]["a:catalog"].update(chains=hand["forms"]["a:catalog"]["chains"] * 9), "chain limit"),
    (lambda hand: hand.update(rules=[{"form_id": "missing"}]), "rule"),
])
def test_invalid_models_fail_before_render(mutation, match):
    hand = seed_repertoire("a", variants=False)
    mutation(hand)
    with pytest.raises(ValueError, match=match):
        render_nominal("a", hand)


def test_form_limit_and_cubic_limit():
    hand = seed_repertoire("a", variants=False)
    for index in range(3):
        hand["forms"][f"a:{index}"] = copy.deepcopy(hand["forms"]["a:catalog"])
    with pytest.raises(ValueError, match="form limit"):
        validate_repertoire(hand)
    hand = seed_repertoire("a", variants=False)
    hand["forms"]["a:catalog"]["chains"] = [{"cubics": [[[0, 0]] * 4] * 33}]
    with pytest.raises(ValueError, match="cubic limit"):
        validate_repertoire(hand)


def test_fresh_process_replay_and_complete_cache_key(tmp_path):
    hand = seed_repertoire("rein")
    model = tmp_path / "hand.json"
    model.write_text(json.dumps(hand))
    script = "import json,sys,hashlib; from scribesim.evofit.repertoire import render_nominal; print(hashlib.sha256(render_nominal('rein',json.load(open(sys.argv[1]))).tobytes()).hexdigest())"
    outputs = [subprocess.check_output([sys.executable, "-c", script, str(model)],
               env={**os.environ, "PYTHONHASHSEED": str(seed)}) for seed in (1, 917)]
    assert outputs[0] == outputs[1]
    key = render_key("rein", hand, dpi=100)
    assert key != render_key("rein", hand, dpi=101)
    hand["nib_angle_deg"] += 1
    assert key != render_key("rein", hand, dpi=100)
    assert compose("rein", hand)["model_sha256"] == object_digest(hand)
