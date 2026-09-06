import copy
import json

import pytest

from scribesim.evofit.repertoire import seed_repertoire
from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.execution import PersistentRepertoireSession
from scribesim.handvalidate.expressive import (
    assess_session, classify_control, build_expressive, evaluate_expressive, decide_g3,
)


def session_payload():
    session = PersistentRepertoireSession(seed_repertoire("in"), seed=7, controls=RepertoireControls(ink=True))
    session.write_text("in in\nin")
    return session.export()


def test_state_audit_rejects_double_consumption_hidden_resets_and_angle_excursions():
    payload = session_payload()
    assert assess_session(payload)["errors"] == []
    for change in ("double", "reset", "angle", "habit"):
        broken = copy.deepcopy(payload)
        row = next(row for row in broken["state"]["execution_trace"] if row["consumed"] > 0)
        if change == "double":
            row["consumed"] *= 2
        elif change == "reset":
            row["ink_before"] = 1
        elif change == "angle":
            row["angle_deg"] += 30
        else:
            row["habit_phase"] += 1
        assert assess_session(broken)["errors"]


def test_control_classification_requires_causal_and_visible_effects():
    before = {"pressure_mean": .5, "angle_mean": 42, "duration_s": 1, "consumed_ink": 0}
    assert classify_control("pressure", before, before, image_delta=.1, safe=True) == "inactive"
    after = {**before, "pressure_mean": .6}
    assert classify_control("pressure", before, after, image_delta=.01, safe=True) == "active-safe"
    assert classify_control("pressure", before, after, image_delta=.01, safe=False) == "active-unsafe"
    assert classify_control("pressure", before, after, image_delta=0, safe=True) == "inactive"


def test_g3_missing_review_and_incomplete_seed_matrix_never_pass():
    freeze = {"scope": "real-candidate", "prerequisite": {"status": "pass"}, "seeds": [7, 19, 41]}
    matrix = [{"seed": seed, "control": control, "classification": "active-safe", "replay": True,
               "errors": [], "coverage": 1} for seed in freeze["seeds"] for control in ("ink", "pressure", "angle", "rhythm", "combined")]
    assert decide_g3(freeze, matrix, None)["status"] == "blocked"
    matrix[0]["classification"] = "inactive"
    assert decide_g3(freeze, matrix, None)["status"] == "fail"
    assert decide_g3(freeze, matrix[1:], None)["status"] != "pass"


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    output = tmp_path_factory.mktemp("expressive")
    build_expressive(output, texts=["in", "rein", "deine hand"])
    return output


def test_actual_multiseed_artifacts_and_stale_summary_detection(bundle, tmp_path):
    import shutil
    report = json.loads((bundle / "report.json").read_text())
    assert len(report["matrix"]) == 15
    assert all(row["replay"] for row in report["matrix"])
    assert evaluate_expressive(bundle)["status"] in {"blocked", "fail"}
    assert (bundle / "comparison.png").is_file()
    shutil.copytree(bundle, tmp_path / "copy")
    report["matrix"][0]["coverage"] = .5
    (tmp_path / "copy" / "report.json").write_text(json.dumps(report))
    assert evaluate_expressive(tmp_path / "copy")["status"] == "fail"
