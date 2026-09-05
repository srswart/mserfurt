import copy
import json
from pathlib import Path

import pytest

from scribesim.handvalidate.nominal import build_nominal, decide_g1, evaluate_nominal
from scribesim.handvalidate.specimen import RUBRIC, object_digest


def gate_fixture():
    freeze = {"scope": "real-corpus-candidate", "g0": {"status": "pass"},
              "criteria": {"status": "frozen_train_development", "per_case_max_loss": .5,
                           "per_case_max_regression": .03, "unseen_mean_min_gain": 0.0},
              "proofs": [{"kind": kind, "text": text} for kind, text in
                         [("reconstruction", "alle das ist"), ("unseen", "dein lied deine hand rein"),
                          ("project_text", "Hie hebt sich an")]],
              "synthetic_unseen": ["dein", "lied", "deine", "hand", "rein"],
              "test_inventory": [{"id": "repeated", "group": "repeated", "admission": "auto_admitted"},
                                 {"id": "novel", "group": "unseen", "admission": "auto_admitted"}],
              "model_sha256": "model", "revision": 0}
    texts = [row["text"] for row in freeze["proofs"]] + freeze["synthetic_unseen"]
    report = {"freeze_sha256": object_digest(freeze), "model_sha256": "model",
              "proofs": [{"text": text, "coverage": 1.0, "aliases": 0, "normalizations": 0,
                          "replay": True} for text in texts],
              "word_results": [{"id": sample["id"], "group": sample["group"], "candidate_loss": .2,
                                "baseline_loss": .3, "coverage": 1.0} for sample in freeze["test_inventory"]],
              "controls": {name: True for name in ["correct", "wrong_letter", "filled_counter", "extra_stroke", "distorted_aspect"]},
              "test_scored": True}
    review = {"reviewer": "unit-fixture-owner", "date": "2026-09-05", "freeze_sha256": object_digest(freeze),
              "report_sha256": object_digest(report), "rubric": {name: "acceptable" for name in RUBRIC},
              "preference": "candidate", "independent_reading": {"reviewer": "unit-fixture-reader", "date": "2026-09-05",
              "transcriptions": texts}}
    return freeze, report, review


def test_complete_gate_fixture_passes_but_missing_review_blocks():
    freeze, report, review = gate_fixture()
    assert decide_g1(freeze, report, review)["status"] == "pass"
    assert decide_g1(freeze, report, None)["status"] == "blocked"
    review["independent_reading"] = None
    assert decide_g1(freeze, report, review)["status"] == "blocked"


@pytest.mark.parametrize("mutation", [
    lambda freeze, report: report.update(model_sha256="stale"),
    lambda freeze, report: report["proofs"].pop(),
    lambda freeze, report: report["proofs"][0].update(coverage=.99),
    lambda freeze, report: report["proofs"][0].update(aliases=1),
    lambda freeze, report: report["proofs"][0].update(replay=False),
    lambda freeze, report: report["word_results"].pop(),
    lambda freeze, report: report["word_results"][0].update(candidate_loss=.8),
    lambda freeze, report: report["word_results"][0].update(candidate_loss=float("nan")),
    lambda freeze, report: report["controls"].update(wrong_letter=False),
])
def test_required_cases_cannot_hide_behind_an_aggregate(mutation):
    freeze, report, _ = gate_fixture()
    mutation(freeze, report)
    assert decide_g1(freeze, report, None)["status"] == "fail"


def test_seed_diagnostic_or_unfrozen_tolerances_cannot_pass():
    freeze, report, review = gate_fixture()
    freeze["scope"] = "unaccepted-seed-diagnostic"
    report["freeze_sha256"] = object_digest(freeze)
    assert decide_g1(freeze, report, None)["status"] == "blocked"


def test_explicit_visual_rejection_is_failure_not_missing_evidence():
    freeze, report, review = gate_fixture()
    review["rubric"]["letterform_identity"] = "unacceptable"
    assert decide_g1(freeze, report, review)["status"] == "fail"


def test_reusing_training_words_as_synthetic_unseen_is_rejected():
    freeze, report, _ = gate_fixture()
    freeze["training_texts"] = ["dein"]
    report["freeze_sha256"] = object_digest(freeze)
    assert decide_g1(freeze, report, None)["status"] == "fail"
    freeze, report, review = gate_fixture()
    freeze["criteria"]["per_case_max_loss"] = None
    report["freeze_sha256"] = object_digest(freeze)
    assert decide_g1(freeze, report, None)["status"] == "blocked"


@pytest.fixture(scope="module")
def actual_bundle(tmp_path_factory):
    output = tmp_path_factory.mktemp("nominal")
    build_nominal(output)
    return output


def test_actual_three_line_seed_bundle_is_replayable_and_explicitly_blocked(actual_bundle):
    freeze = json.loads((actual_bundle / "freeze.json").read_text())
    report = json.loads((actual_bundle / "report.json").read_text())
    gate = evaluate_nominal(actual_bundle)
    assert freeze["scope"] == "unaccepted-seed-diagnostic"
    assert gate["status"] == "blocked"
    assert not gate["promoted"]
    assert len(report["proofs"]) == 8
    assert all(row["coverage"] == 1 and row["replay"] for row in report["proofs"])
    assert report["test_scored"] is False
    assert report["word_results"] == []
    assert (actual_bundle / "three-line.png").is_file()
    assert (actual_bundle / "comparison.png").is_file()
    assert (actual_bundle / "reference-sheet.png").is_file()


def test_stale_artifacts_are_rejected(actual_bundle, tmp_path):
    import shutil
    shutil.copytree(actual_bundle, tmp_path / "copy")
    output = tmp_path / "copy"
    with (output / "candidate.json").open("a") as stream:
        stream.write(" ")
    assert evaluate_nominal(output)["status"] == "fail"
    with pytest.raises(ValueError, match="empty"):
        build_nominal(actual_bundle)
