import copy
import json
import os
import subprocess
import sys

import numpy as np
import pytest

from scribesim.evofit.stroke_language import (
    compile_text, execute_language, language_guide, load_language_bundle, render_language, seed_language, validate_language,
)
from scribesim.handvalidate.specimen import object_digest


@pytest.mark.parametrize("fault", ["cycle", "missing", "scale", "nan", "port", "residual", "alias", "unknown", "budget"])
def test_language_rejects_bypasses_and_invalid_constraints(fault):
    model = seed_language()
    if fault == "cycle":
        model["primitives"]["stem"]["references"] = ["stem"]
    elif fault == "missing":
        model["recipes"]["i"]["strokes"][0]["primitive"] = "missing"
    elif fault == "scale":
        model["recipes"]["i"]["strokes"][0]["scale"] = 10
    elif fault == "nan":
        model["primitives"]["stem"]["cubics"][0][1][0] = float("nan")
    elif fault == "port":
        model["recipes"]["i"]["strokes"][1]["offset"] = [1, 1]
    elif fault == "residual":
        model["recipes"]["i"]["cubics"] = []
    elif fault == "alias":
        model["recipes"]["i"]["visible"] = "x"
    elif fault == "unknown":
        model["schema_version"] = 2
    else:
        for index in range(8):
            model["primitives"][f"extra-{index}"] = copy.deepcopy(model["primitives"]["stem"])
    with pytest.raises(ValueError):
        validate_language(model)


def test_shared_primitive_changes_every_user_without_copying_curves():
    model = seed_language()
    before = compile_text("i u ii", model)
    model["primitives"]["stem"]["cubics"][0][1][0] += .1
    after = compile_text("i u ii", model)
    assert before["model_sha256"] != after["model_sha256"]
    old = [row["cubics"] for row in before["strokes"] if row["primitive"] == "stem"]
    new = [row["cubics"] for row in after["strokes"] if row["primitive"] == "stem"]
    assert len(old) >= 4 and all(first != second for first, second in zip(old, new))
    assert all("cubics" not in recipe for recipe in model["recipes"].values())


def test_exact_text_and_word_line_stroke_ownership():
    model = seed_language()
    text = "ii  u\ni"
    plan = compile_text(text, model)
    bundle = language_guide(text, model)
    assert plan["text"] == text and plan["coverage"] == 1
    assert len(plan["words"]) == 3 and len(plan["lines"]) == 2
    assert {row["line"] for row in plan["strokes"]} == {0, 1}
    assert len(bundle.metadata["owners"]) == len(bundle.guide.samples)
    assert all("primitive" in owner for owner in bundle.metadata["owners"] if owner["kind"] == "stroke")
    assert any(not sample.contact for sample in bundle.guide.samples)
    with pytest.raises(ValueError, match="Unsupported"):
        compile_text("I", model)


def test_context_overlay_is_bounded_and_never_mutates_checkpoint():
    model = seed_language()
    model["letter_rules"] = [{"id": "next-i", "logical": "i", "previous": None, "next": "i",
                              "position": "any", "stroke": 0, "dx": 0, "dy": 0, "advance": .08}]
    frozen = object_digest(model)
    plan = compile_text("ii", model)
    assert object_digest(model) == frozen
    assert plan["letters"][0]["rules"] == ["next-i"]
    assert plan["letters"][1]["rules"] == []
    model["letter_rules"][0]["advance"] = 9
    with pytest.raises(ValueError):
        compile_text("ii", model)


def test_ligature_mapping_retains_shared_text_span():
    model = seed_language()
    recipe = copy.deepcopy(model["recipes"]["u"])
    recipe.update(logical="ii", visible="ii")
    model["recipes"]["double"] = recipe
    plan = compile_text("ii", model)
    assert len(plan["letters"]) == 1
    assert all(row["span"] == [0, 2] for row in plan["strokes"])


def test_fresh_process_language_pixels_and_plan_replay():
    code = "from scribesim.evofit.stroke_language import *; from scribesim.handvalidate.specimen import object_digest; import hashlib; model=seed_language(); print(object_digest(compile_text('ii u', model)), hashlib.sha256(render_language('ii u', model).tobytes()).hexdigest())"
    outputs = [subprocess.check_output([sys.executable, "-c", code], env={**os.environ, "PYTHONHASHSEED": seed})
               for seed in ("7", "839")]
    assert outputs[0] == outputs[1]


def test_actual_neutral_trajectory_has_complete_stroke_ownership():
    result = execute_language("i u", seed_language())
    assert result["metrics"]["contact_schedule_preserved"]
    assert result["metrics"]["corridor_error_mm"] <= .25
    assert len(result["owners"]) == len(result["trajectory"])
    assert all("primitive" in owner for sample, owner in zip(result["trajectory"], result["owners"]) if sample["contact"])


def test_language_bundle_rejects_changed_ownership(tmp_path):
    from dataclasses import asdict
    model = seed_language()
    payload = asdict(language_guide("i", model))
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps({"payload": payload, "sha256": object_digest(payload)}))
    assert load_language_bundle(path, model).guide.symbol == "i"
    payload["metadata"]["owners"][0]["primitive"] = "forged"
    path.write_text(json.dumps({"payload": payload, "sha256": object_digest(payload)}))
    with pytest.raises(ValueError):
        load_language_bundle(path, model)
