import copy
import json

import numpy as np
import pytest
from PIL import Image, ImageDraw

from scribesim.evofit.reference_repair import apply_reviews, repair_dataset, review_template
from scribesim.evofit.reference_dataset import _assign_components
from scribesim.handvalidate.specimen import object_digest


def observation(split="train"):
    return {"id": "word", "split": split, "source_id": "page", "bbox": [0, 0, 20, 20],
            "raw_sha256": "a" * 64, "text": "in", "mapping_status": "unverified",
            "visible_mapping": [], "label_status": "machine_hypothesis"}


def test_review_queue_never_exposes_locked_test():
    dataset = {"samples": [observation(), {**observation("test"), "id": "locked"}]}
    queue = review_template(dataset)
    assert [row["sample_id"] for row in queue["entries"]] == ["word"]
    assert queue["entries"][0]["decision"] == "pending"


def test_pending_review_cannot_admit_or_mutate_a_label():
    dataset = {"samples": [observation()]}
    assert apply_reviews(dataset, review_template(dataset), {}) == dataset["samples"]


@pytest.mark.parametrize("fault", ["approval", "pixels", "split", "mapping", "duplicate"])
def test_invalid_attestation_is_rejected(fault):
    dataset = {"samples": [observation()]}
    queue = review_template(dataset)
    entry = queue["entries"][0]
    entry.update(decision="confirm", reviewer="fixture-reviewer", reviewed_at="2026-09-06T00:00:00Z",
                 text="in", visible_mapping=[{"logical": "i", "visible": "i"}, {"logical": "n", "visible": "n"}])
    approvals = {object_digest(entry): "fixture-reviewer"}
    if fault == "approval":
        approvals = {}
    elif fault == "pixels":
        entry["raw_sha256"] = "b" * 64
    elif fault == "split":
        dataset["samples"][0]["split"] = "test"
    elif fault == "mapping":
        entry["visible_mapping"] = [{"logical": "i", "visible": "i"}]
        approvals = {object_digest(entry): "fixture-reviewer"}
    else:
        queue["entries"].append(copy.deepcopy(entry))
    with pytest.raises(ValueError):
        apply_reviews(dataset, queue, approvals)


def test_confirmed_mapping_is_bound_to_attested_entry():
    dataset = {"samples": [observation()]}
    queue = review_template(dataset)
    entry = queue["entries"][0]
    entry.update(decision="confirm", reviewer="fixture-reviewer", reviewed_at="2026-09-06T00:00:00Z",
                 text="in", visible_mapping=[{"logical": "in", "visible": "in"}])
    samples = apply_reviews(dataset, queue, {object_digest(entry): "fixture-reviewer"})
    assert samples[0]["mapping_status"] == "declared"
    assert samples[0]["review_entry_sha256"] == object_digest(entry)
    assert dataset["samples"][0]["mapping_status"] == "unverified"


def test_seeded_cleanup_breaks_weak_bridges_but_not_strong_ambiguity():
    image = Image.new("L", (40, 45), 245)
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 5, 15, 10), fill=25)
    draw.rectangle((10, 30, 15, 35), fill=25)
    draw.line((12, 10, 12, 30), fill=180, width=1)
    lines = [{"core_top": 5, "core_bottom": 10, "center_y": 7},
             {"core_top": 30, "core_bottom": 35, "center_y": 32}]
    owners, uncertain = _assign_components(image, lines, version="strong-seeds-v2")
    assert owners[7, 12] == 0 and owners[32, 12] == 1
    assert uncertain[20, 12]
    draw.line((12, 10, 12, 30), fill=25, width=1)
    owners, uncertain = _assign_components(image, lines, version="strong-seeds-v2")
    assert uncertain[20, 12] and owners[20, 12] == -1


def test_repair_refuses_overwrite_before_reading_source(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    (output / "preserve").write_text("existing")
    with pytest.raises(ValueError, match="empty"):
        repair_dataset(tmp_path / "missing", output)
