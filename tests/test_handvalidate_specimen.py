import copy
import json
from pathlib import Path

import pytest
from PIL import Image
import numpy as np

from scribesim.handvalidate.specimen import (
    build_benchmark,
    evaluate_benchmark,
    validate_contract,
    verify_baseline,
    write_equal_scale_panel,
    render_worker,
)


@pytest.fixture(scope="module")
def benchmark(tmp_path_factory):
    output = tmp_path_factory.mktemp("benchmark")
    build_benchmark(output, backends=("v1_fitted",))
    return output


def test_missing_review_and_dataset_block_benchmark(benchmark):
    contract = json.loads((benchmark / "contract.json").read_text())
    baselines = json.loads((benchmark / "baseline_manifest.json").read_text())
    decision = evaluate_benchmark(contract, baselines, benchmark)
    assert decision["status"] == "blocked"
    assert "target_review_missing" in decision["reasons"]
    assert "dataset_missing" in decision["reasons"]
    assert decision["promoted"] is False


def test_empty_measurements_and_unreviewed_target_never_pass(benchmark):
    contract = json.loads((benchmark / "contract.json").read_text())
    baselines = json.loads((benchmark / "baseline_manifest.json").read_text())
    contract["required_measurements"] = []
    with pytest.raises(ValueError, match="measurements"):
        validate_contract(contract)
    contract["required_measurements"] = ["ocr_accuracy"]
    with pytest.raises(ValueError, match="measurement"):
        validate_contract(contract)
    assert baselines["baselines"]


@pytest.mark.parametrize("mutation", ["backend", "hash", "artifact", "model", "source"])
def test_baseline_identity_is_verified_against_real_artifacts(benchmark, mutation):
    manifest = json.loads((benchmark / "baseline_manifest.json").read_text())
    record = copy.deepcopy(manifest["baselines"][0])
    if mutation == "backend":
        record["backend"] = "plain"
    elif mutation == "hash":
        del record["image_sha256"]
    elif mutation == "artifact":
        record["image_sha256"] = "0" * 64
    elif mutation == "model":
        record["model_sha256"] = "0" * 64
    else:
        record["source_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        verify_baseline(record, benchmark)


def test_fresh_worker_renders_declared_model_and_records_replay(benchmark):
    manifest = json.loads((benchmark / "baseline_manifest.json").read_text())
    record = manifest["baselines"][0]
    verify_baseline(record, benchmark)
    assert record["backend"] == "v1_fitted"
    assert record["entrypoint"].endswith("render_shared_word")
    assert record["fresh_process"] is True
    assert record["same_seed_replay"] is True
    assert record["command"]
    assert record["code_sha256"]
    assert record["source_sha256"]


def test_equal_scale_panel_does_not_resize_each_tile_independently(tmp_path):
    output = tmp_path / "panel.png"
    metadata = write_equal_scale_panel(
        [("short", Image.new("RGB", (20, 30)), 10.0),
         ("long", Image.new("RGB", (40, 60)), 20.0)], output,
    )
    assert metadata["tile_sizes"] == [[40, 60], [40, 60]]
    assert metadata["pixels_per_xheight"] == 20
    assert output.is_file()


def test_legacy_results_are_reconciled_without_promotion(benchmark):
    record = json.loads((benchmark / "prior_experiment.json").read_text())
    assert record["advance_status"] == "in_progress"
    assert record["decision"] == "not_promoted"
    assert record["counts"]["training"] == 14
    assert record["heldout_reuse_policy"] == "development_only"
    assert record["remaining_work"]


def test_evo_smoke_places_catalog_strokes_inside_its_canvas(tmp_path):
    from scribesim.evofit.word_recovery import seed_hand

    (tmp_path / "model.json").write_text(json.dumps(seed_hand("und")))
    render_worker("evo", tmp_path)
    pixels = np.asarray(Image.open(tmp_path / "image.png").convert("L"))
    ink_rows = np.nonzero(pixels < 100)[0]
    assert len(ink_rows) > 50
    assert ink_rows.min() > 0
    assert ink_rows.max() < pixels.shape[0] - 1
