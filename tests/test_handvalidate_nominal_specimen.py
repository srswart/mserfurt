import json

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
    freeze, report, review = gate_fixture()
    freeze["criteria"]["per_case_max_loss"] = None
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


def test_frozen_locked_scoring_path_with_explicit_synthetic_readiness_stub(tmp_path, monkeypatch):
    import numpy as np
    from PIL import Image
    import scribesim.handvalidate.nominal as nominal
    from scribesim.evofit.repertoire import render_nominal, seed_repertoire
    from scribesim.handvalidate.specimen import digest, write_json

    hand = seed_repertoire("o", variants=False)
    dataset_root, benchmark_root, recovery_root = [tmp_path / name for name in ("data", "benchmark", "recovery")]
    for directory in (dataset_root, benchmark_root, recovery_root):
        directory.mkdir()
    proofs = [{"kind": kind, "text": text} for kind, text in
              [("reconstruction", "o"), ("unseen", "ooo oooo ooooo oooooo ooooooo"), ("project_text", "oo")]]
    contract = {"proofs": proofs}
    dataset = {"calibration": {"status": "synthetic-test-stub"}, "samples": []}
    for index, (text, split) in enumerate((("o", "train"), ("o", "test"), ("oo", "test"))):
        raw = render_nominal(text, hand, dpi=180)
        mask = np.where(np.asarray(Image.fromarray(raw).convert("L")) < 180, 255, 0).astype(np.uint8)
        Image.fromarray(raw).save(dataset_root / f"{index}-raw.png")
        Image.fromarray(mask).save(dataset_root / f"{index}-mask.png")
        dataset["samples"].append({"id": str(index), "text": text, "split": split, "admission": "auto_admitted",
            "raw_path": f"{index}-raw.png", "mask_path": f"{index}-mask.png", "exclusions": [],
            "raw_sha256": digest(dataset_root / f"{index}-raw.png"), "mask_sha256": digest(dataset_root / f"{index}-mask.png"),
            "xheight_native_px": hand["x_height_mm"] * 180 / 25.4})
    write_json(dataset_root / "manifest.json", dataset)
    write_json(recovery_root / "selected.json", hand)
    write_json(recovery_root / "initial.json", hand)
    write_json(recovery_root / "config.json", {"scope": "synthetic-unit-fixture"})
    write_json(recovery_root / "report.json", {"status": "unaccepted-real-corpus-candidate",
        "dataset_sha256": digest(dataset_root / "manifest.json"), "contract_sha256": object_digest(contract),
        "selected_sha256": digest(recovery_root / "selected.json"), "initial_sha256": digest(recovery_root / "initial.json"),
        "config_sha256": digest(recovery_root / "config.json")})
    Image.new("RGB", (20, 20), "white").save(benchmark_root / "target_sheet.png")
    monkeypatch.setattr(nominal, "_readiness", lambda *args: (dataset, contract, {"status": "pass"}))
    criteria = {"status": "frozen_train_development", "per_case_max_loss": .1,
                "per_case_max_regression": .01, "unseen_mean_min_gain": 0,
                "source_calibration_sha256": object_digest(dataset["calibration"])}
    output = tmp_path / "bundle"
    original_score = nominal._score_locked
    def check_freeze_first(*args):
        assert json.loads((output / "freeze.json").read_text()) == args[0]
        return original_score(*args)
    monkeypatch.setattr(nominal, "_score_locked", check_freeze_first)
    build_nominal(output, dataset_root=dataset_root, benchmark_root=benchmark_root,
                  recovery_root=recovery_root, criteria=criteria)
    report = json.loads((output / "report.json").read_text())
    assert report["test_scored"]
    assert {row["group"] for row in report["word_results"]} == {"repeated", "unseen"}
    review = json.loads((output / "review-template.json").read_text())
    review.update(reviewer="synthetic-owner-fixture", date="2026-09-05", preference="candidate",
                  rubric={name: "acceptable" for name in RUBRIC}, independent_reading={
                  "reviewer": "synthetic-reader-fixture", "date": "2026-09-05",
                  "transcriptions": [row["text"] for row in report["proofs"]]})
    assert evaluate_nominal(output, review, dataset_root=dataset_root, benchmark_root=benchmark_root)["status"] == "pass"
    report["word_results"][0]["candidate_loss"] = .01
    write_json(output / "report.json", report)
    assert evaluate_nominal(output, None, dataset_root=dataset_root, benchmark_root=benchmark_root)["status"] == "fail"
