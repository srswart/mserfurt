import copy
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from scribesim.evofit.reference_dataset import (
    build_dataset,
    detect_lines,
    line_mask,
    validate_dataset,
    prepare_v1_manifest,
    calibrate_observations,
)
from scribesim.handvalidate.specimen import digest, object_digest


def page_fixture():
    image = Image.new("L", (140, 130), 245)
    draw = ImageDraw.Draw(image)
    for top in (15, 55, 95):
        for left in (12, 28, 44, 85, 101):
            draw.rectangle((left, top, left + 7, top + 11), fill=25)
    return image


def test_lines_are_detected_before_word_cleanup():
    lines = detect_lines(page_fixture())
    assert len(lines) == 3
    assert [line["center_y"] for line in lines] == sorted(line["center_y"] for line in lines)


def test_target_descender_is_retained_and_neighbour_is_removed():
    image = page_fixture()
    ImageDraw.Draw(image).rectangle((15, 26, 18, 42), fill=25)
    lines = detect_lines(image)
    mask = line_mask(image, lines, 0)
    assert mask[35, 16] == 255
    assert mask[59, 14] == 0


def test_touching_lines_and_pale_strokes_remain_unknown():
    image = page_fixture()
    draw = ImageDraw.Draw(image)
    draw.rectangle((14, 25, 17, 56), fill=25)
    draw.rectangle((55, 17, 58, 25), fill=155)
    lines = detect_lines(image)
    mask = line_mask(image, lines, 0)
    assert mask[39, 15] == 128
    assert mask[20, 56] == 128


def test_pale_ink_connected_to_a_strong_target_is_preserved():
    image = page_fixture()
    ImageDraw.Draw(image).rectangle((19, 17, 24, 24), fill=155)
    mask = line_mask(image, detect_lines(image), 0)
    assert mask[20, 22] == 255


@pytest.fixture
def manifest(tmp_path):
    source = tmp_path / "page.png"
    page_fixture().save(source)
    payload = {
        "schema_version": 2,
        "hand_id": "synthetic",
        "sources": [{"id": "page", "path": str(source), "sha256": digest(source),
                     "url": "synthetic", "apparent_hand": "fixture", "region": [0, 0, 140, 130]}],
        "samples": [],
        "human_interventions": [],
    }
    for index, split in enumerate(("train", "development", "test")):
        top = (15, 55, 95)[index]
        payload["samples"].append({
            "id": f"word-{index}", "source_id": "page", "line_index": index,
            "bbox": [5, top - 5, 65, top + 20], "split": split,
            "text": "in", "label_status": "machine_hypothesis", "confidence": 0.9,
            "label_origin": "synthetic fixture", "mapping_status": "declared",
            "visible_mapping": [{"logical": "i", "visible": "i"}, {"logical": "n", "visible": "n"}],
            "previously_inspected": False,
        })
    path = tmp_path / "input.json"
    path.write_text(json.dumps(payload))
    return path


def build_fixture(manifest, tmp_path):
    return build_dataset(manifest, tmp_path / "dataset", contract={"id": "fixture"})


def test_build_preserves_raw_pixels_and_reversible_transform(manifest, tmp_path):
    result = build_fixture(manifest, tmp_path)
    output = tmp_path / "dataset"
    validate_dataset(result, output)
    sample = result["samples"][0]
    raw = np.asarray(Image.open(output / sample["raw_path"]))
    assert np.array_equal(raw, np.asarray(page_fixture().crop((5, 10, 65, 35))))
    assert sample["source_to_crop"] == [1, 0, -5, 0, 1, -10]
    assert sample["label_status"] == "machine_hypothesis"
    assert result["contract_sha256"] == object_digest({"id": "fixture"})
    assert result["status"] == "blocked"
    assert "insufficient_training_support" in result["reasons"]


@pytest.mark.parametrize("problem", ["source_hash", "shared_line", "shared_pixels", "inspected_test", "duplicate_id", "duplicate_pixels"])
def test_dataset_rejects_integrity_and_split_errors(manifest, tmp_path, problem):
    payload = json.loads(manifest.read_text())
    if problem == "source_hash":
        payload["sources"][0]["sha256"] = "0" * 64
    elif problem == "shared_line":
        payload["samples"][1]["line_index"] = 0
    elif problem == "shared_pixels":
        payload["samples"][1]["bbox"] = [20, 20, 60, 70]
    elif problem == "inspected_test":
        payload["samples"][2]["previously_inspected"] = True
    elif problem == "duplicate_id":
        payload["samples"][1]["id"] = payload["samples"][0]["id"]
    else:
        duplicate = copy.deepcopy(payload["samples"][0])
        duplicate["id"] = "duplicate-pixels"
        payload["samples"].append(duplicate)
    manifest.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        build_fixture(manifest, tmp_path)


@pytest.mark.parametrize("problem", ["uncertain_label", "unsupported_mapping", "excess_unknown", "empty_ink"])
def test_bad_observations_are_quarantined(manifest, tmp_path, problem):
    payload = json.loads(manifest.read_text())
    if problem == "uncertain_label":
        payload["samples"][0]["confidence"] = 0.2
    elif problem == "unsupported_mapping":
        payload["samples"][0]["visible_mapping"] = [{"logical": "in", "visible": "?"}]
    elif problem == "empty_ink":
        payload["samples"][0]["bbox"] = [65, 0, 75, 12]
    else:
        source = Path(payload["sources"][0]["path"])
        image = page_fixture()
        draw = ImageDraw.Draw(image)
        draw.rectangle((5, 10, 64, 34), fill=155)
        draw.rectangle((12, 15, 19, 26), fill=25)
        image.save(source)
        payload["sources"][0]["sha256"] = digest(source)
    manifest.write_text(json.dumps(payload))
    result = build_fixture(manifest, tmp_path)
    assert result["samples"][0]["admission"] == "quarantined"
    assert result["samples"][0]["exclusions"]


def test_modified_export_and_forged_admission_are_detected(manifest, tmp_path):
    result = build_fixture(manifest, tmp_path)
    altered = copy.deepcopy(result)
    altered["samples"][0]["raw_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        validate_dataset(altered, tmp_path / "dataset")
    altered = copy.deepcopy(result)
    altered["samples"][0]["visible_mapping"] = []
    with pytest.raises(ValueError, match="admission"):
        validate_dataset(altered, tmp_path / "dataset")


def test_transform_and_same_hash_source_aliases_cannot_hide_errors(manifest, tmp_path):
    result = build_fixture(manifest, tmp_path)
    altered = copy.deepcopy(result)
    altered["samples"][0]["source_to_crop"][2] = 300
    with pytest.raises(ValueError, match="transform"):
        validate_dataset(altered, tmp_path / "dataset")
    altered = copy.deepcopy(result)
    source = copy.deepcopy(altered["sources"][0])
    source["id"] = "alias"
    altered["sources"].append(source)
    altered["samples"][1]["source_id"] = "alias"
    altered["samples"][1]["line_index"] = 0
    with pytest.raises(ValueError, match="line shared"):
        validate_dataset(altered, tmp_path / "dataset")


def test_v1_heldout_lines_cannot_reenter_training_or_locked_test():
    manifest = prepare_v1_manifest()
    samples = manifest["samples"]
    heldout_lines = {sample["line_index"] for sample in samples if sample.get("v1_split") == "heldout"}
    assert heldout_lines
    assert all(sample["split"] == "development" for sample in samples if sample["line_index"] in heldout_lines)
    assert all(sample["split"] != "test" for sample in samples if sample.get("v1_split"))
    assert all(sample["mapping_status"] == "unverified" for sample in samples if sample.get("v1_split"))


def test_calibration_uses_only_admitted_non_test_repeats(manifest, tmp_path):
    result = build_fixture(manifest, tmp_path)
    calibration = calibrate_observations(result["samples"], tmp_path / "dataset")
    assert calibration["status"] == "pass"
    assert calibration["repeat_pair_count"] == 1
    assert "word-2" not in calibration["used_sample_ids"]
    assert all(control["passed"] for control in calibration["controls"])
    changed = copy.deepcopy(result["samples"])
    changed[2]["text"] = "anything"
    assert calibrate_observations(changed, tmp_path / "dataset") == calibration
    assert calibrate_observations([], tmp_path / "dataset")["status"] == "blocked"


def test_usable_independent_corpus_can_pass_dataset_readiness(manifest, tmp_path):
    payload = json.loads(manifest.read_text())
    image = Image.new("L", (140, 1600), 245)
    draw = ImageDraw.Draw(image)
    payload["samples"] = []
    for index in range(40):
        top = 15 + 40 * index
        for left in (12, 28, 44):
            draw.rectangle((left, top, left + 7, top + 11), fill=25)
        text = "in" if index % 2 else "ni"
        payload["samples"].append({
            "id": f"independent-{index}", "source_id": "page", "line_index": index,
            "bbox": [5, top - 5, 65, top + 20],
            "split": "train" if index < 30 else "development" if index < 35 else "test",
            "text": text, "label_status": "machine_hypothesis", "confidence": 0.9,
            "label_origin": "synthetic admission fixture", "mapping_status": "declared",
            "visible_mapping": [{"logical": character, "visible": character} for character in text],
            "previously_inspected": False,
        })
    source = Path(payload["sources"][0]["path"])
    image.save(source)
    payload["sources"][0].update(sha256=digest(source), region=[0, 0, 140, 1600])
    manifest.write_text(json.dumps(payload))
    result = build_fixture(manifest, tmp_path)
    assert result["status"] == "pass"
    assert result["admitted_count"] == 40
    assert result["calibration"]["status"] == "pass"
    assert result["support_debt"] == {}
    assert all(sample["id"] not in result["calibration"]["used_sample_ids"]
               for sample in result["samples"] if sample["split"] == "test")
