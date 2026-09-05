import copy

import numpy as np
import pytest

from scribesim.evofit.repertoire import compose, refresh_form, render_nominal, seed_repertoire
from scribesim.evofit.recovery import (
    Budget, RenderCache, alignment_lattice, fit_repertoire, image_objective,
    skeleton_graph, structural_proposals, synthetic_case,
)
from scribesim.handvalidate.specimen import object_digest


def test_training_structure_recovers_a_missing_loop():
    seed, samples = synthetic_case()
    proposals = structural_proposals(seed, samples)
    assert proposals
    assert all(row["split"] == "train" for proposal in proposals for row in proposal["provenance"])
    assert any(chain["closed"] for proposal in proposals for chain in proposal["form"]["chains"])
    fixed = fit_repertoire(samples, seed, seed=7, mode="fixed", max_evaluations=100)
    structural = fit_repertoire(samples, seed, seed=7, mode="structural", max_evaluations=100)
    assert structural["development_loss"] < fixed["development_loss"]
    assert any(chain["closed"] for form in structural["model"]["forms"].values() for chain in form["chains"])
    assert compose("ooo", structural["model"])["coverage"] == 1


def test_locked_pixels_and_labels_never_enter_search():
    seed, samples = synthetic_case()
    class Locked(dict):
        def __getitem__(self, key):
            if key != "split":
                raise AssertionError("locked test opened during fitting")
            return "test"
    first = fit_repertoire(samples + [Locked()], seed, seed=11, max_evaluations=24)
    second = fit_repertoire(samples, seed, seed=11, max_evaluations=24)
    assert first["model"] == second["model"]
    assert first["trace"] == second["trace"]
    altered = copy.deepcopy(samples)
    altered[-1]["mask"][:] = 0
    assert object_digest(structural_proposals(seed, samples)) == object_digest(structural_proposals(seed, altered))


def test_controls_mask_unknown_and_actual_render_sensitivity():
    target = np.zeros((40, 60), dtype=np.uint8)
    target[8:32, 10:40] = 255
    target[13:27, 15:35] = 0
    correct = np.where(target == 255, 0, 255).astype(np.uint8)
    baseline = image_objective(correct, target, correct)
    assert baseline["total"] == 0
    filled = correct.copy()
    filled[13:27, 15:35] = 0
    wrong = np.full_like(correct, 255)
    wrong[10:30, 28:32] = 0
    distorted = np.full_like(correct, 255)
    distorted[:, :30] = correct[:, ::2]
    for control in (filled, wrong, distorted):
        assert image_objective(correct, target, control)["total"] > baseline["total"]
    mask = target.copy()
    mask[:5] = 128
    corrupted = correct.copy()
    corrupted[:5] = 0
    assert image_objective(corrupted, mask, corrupted)["total"] == 0
    seed, samples = synthetic_case()
    altered = copy.deepcopy(seed)
    altered["nib_width_mm"] *= 1.5
    assert not np.array_equal(render_nominal("o", seed), render_nominal("o", altered))


def test_skeleton_graph_and_alignment_are_bounded_and_ambiguous():
    mask = np.zeros((30, 50), dtype=np.uint8)
    mask[5:25, 8:12] = 255
    mask[5:25, 35:39] = 255
    graph = skeleton_graph(mask)
    assert graph["chains"]
    assert graph["status"] == "hypothesis-not-ductus"
    lattice = alignment_lattice("ii", mask, beam=3)
    assert 1 <= len(lattice) <= 3
    assert all(row["cuts"][0] == 0 and row["cuts"][-1] == 50 for row in lattice)
    assert all(row["cuts"] == sorted(set(row["cuts"])) for row in lattice)
    with pytest.raises(ValueError, match="beam"):
        alignment_lattice("ii", mask, beam=33)


def test_budget_and_cache_cannot_hide_actual_work_or_stale_models():
    budget = Budget(2, 30)
    budget.consume()
    budget.consume()
    with pytest.raises(StopIteration, match="evaluation_budget"):
        budget.consume()
    with pytest.raises(ValueError):
        Budget(5001, 30)
    timed = Budget(2, 1, clock=lambda: 10)
    timed.started = 0
    with pytest.raises(StopIteration, match="wall_time"):
        timed.consume()
    cache = RenderCache()
    hand = seed_repertoire("o", variants=False)
    first = cache.render("o", hand)
    cache.entries[next(iter(cache.entries))][0][:] = 255
    with pytest.raises(ValueError, match="cache"):
        cache.render("o", hand)
    other = copy.deepcopy(hand)
    other["nib_angle_deg"] += 15
    assert not np.array_equal(first, RenderCache().render("o", other))
    seed, samples = synthetic_case()
    result = fit_repertoire(samples, seed, max_evaluations=10)
    assert result["evaluations"] <= 10
    assert result["stop_reason"] == "evaluation_budget"
    assert result["promoted"] is False


def test_invalid_and_unsupported_inputs_do_not_get_silently_dropped():
    seed, samples = synthetic_case()
    samples[0]["text"] = "x"
    with pytest.raises(ValueError, match="Unsupported"):
        fit_repertoire(samples, seed, max_evaluations=10)
    with pytest.raises(ValueError, match="development"):
        fit_repertoire(samples[:1], seed, max_evaluations=10)
