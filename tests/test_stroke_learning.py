import copy
import json

import numpy as np
import pytest

from scribesim.curriculum.stroke_learning import (
    evaluate_learning, fit_primitives, render_exercise, run_stroke_learning, synthetic_exercises,
)
from scribesim.handvalidate.specimen import object_digest


def test_fit_changes_shared_geometry_and_improves_heldout_strokes():
    initial, target, samples = synthetic_exercises(families=["stem"])
    frozen_recipes = copy.deepcopy(initial["recipes"])
    result = fit_primitives(initial, samples, seed=7, max_evaluations=250)
    assert result["evaluations"] <= 250
    assert result["model"]["recipes"] == frozen_recipes
    assert object_digest(result["model"]["primitives"]) != object_digest(initial["primitives"])
    assert result["metrics"]["test"]["after"] < result["metrics"]["test"]["before"] * .75
    assert result["selection_split"] == "development"


def test_test_targets_do_not_change_fitting_or_checkpoint_selection():
    initial, target, samples = synthetic_exercises(families=["stem"])
    changed = copy.deepcopy(samples)
    for sample in changed:
        if sample["split"] == "test":
            sample["raw"] = np.zeros_like(sample["raw"])
    first = fit_primitives(initial, samples, seed=7, max_evaluations=180)
    second = fit_primitives(initial, changed, seed=7, max_evaluations=180)
    assert object_digest(first["model"]) == object_digest(second["model"])
    assert first["ledger"] == second["ledger"]


def test_budget_cannot_be_exceeded_during_initialization():
    initial, target, samples = synthetic_exercises(families=["stem"])
    result = fit_primitives(initial, samples, max_evaluations=1)
    assert result["evaluations"] <= 1
    assert result["status"] == "blocked"


def test_real_corpus_blocks_before_training_or_reference_pixel_scoring(tmp_path):
    result = run_stroke_learning(tmp_path / "real", dataset_root="reference/konrad_hand_recovery_v3")
    assert result["status"] == "blocked" and result["evaluations"] == 0
    assert result["scope"] == "real-reference"
    assert not (tmp_path / "real" / "candidate.json").exists()


def test_repair_learning_refuses_overwrite(tmp_path):
    (tmp_path / "keep").write_text("preserve")
    with pytest.raises(ValueError, match="empty"):
        run_stroke_learning(tmp_path)


def test_evaluation_rejects_unfrozen_pass_summary(tmp_path):
    (tmp_path / "report.json").write_text(json.dumps({"status": "pass"}))
    with pytest.raises(ValueError):
        evaluate_learning(tmp_path)
