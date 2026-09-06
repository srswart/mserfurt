"""Bounded non-test admission repair with explicit externally attested reviews."""

import argparse
from collections import Counter
import copy
from datetime import datetime
import json
from pathlib import Path
import tempfile

from scribesim.evofit.reference_dataset import build_dataset, validate_dataset
from scribesim.handvalidate.specimen import ROOT, digest, evaluate_benchmark, object_digest, write_json


def review_template(dataset):
    return {"schema_version": 1, "dataset_sha256": object_digest(dataset), "entries": [
        {"sample_id": sample["id"], "source_id": sample["source_id"], "bbox": sample["bbox"],
         "raw_sha256": sample["raw_sha256"], "decision": "pending", "reviewer": "",
         "reviewed_at": "", "text": sample.get("text", ""), "visible_mapping": []}
        for sample in dataset["samples"] if sample["split"] != "test"]}


def apply_reviews(dataset, queue, approvals):
    if queue.get("schema_version") != 1 or queue.get("dataset_sha256") != object_digest(dataset):
        raise ValueError("Review dataset identity mismatch")
    samples = copy.deepcopy(dataset["samples"])
    indexed = {sample["id"]: sample for sample in samples}
    seen = set()
    for entry in queue["entries"]:
        identifier = entry["sample_id"]
        if identifier in seen or identifier not in indexed:
            raise ValueError("Duplicate or missing review sample")
        seen.add(identifier)
        sample = indexed[identifier]
        if sample["split"] == "test" or any(entry[key] != sample[key] for key in ("source_id", "bbox", "raw_sha256")):
            raise ValueError("Review cannot change source pixels or locked test")
        if entry["decision"] == "pending":
            continue
        if entry["decision"] not in {"confirm", "quarantine"}:
            raise ValueError("Unknown review decision")
        checksum = object_digest(entry)
        if not entry["reviewer"] or approvals.get(checksum) != entry["reviewer"]:
            raise ValueError("Separate trusted approval of exact review entry required")
        if datetime.fromisoformat(entry["reviewed_at"].replace("Z", "+00:00")).tzinfo is None:
            raise ValueError("Review timestamp must include timezone")
        mapping = entry["visible_mapping"]
        if (not entry["text"] or "".join(row.get("logical", "") for row in mapping) != entry["text"]
                or any(set(row) != {"logical", "visible"} or not row["logical"].isalpha()
                       or not (row["visible"] == row["logical"] or (row["logical"], row["visible"]) == ("s", "ſ")) for row in mapping)):
            raise ValueError("Incomplete or unsupported exact visible mapping")
        sample.update(text=entry["text"], visible_mapping=mapping, mapping_status="declared",
                      label_status="reviewed", confidence=1.0 if entry["decision"] == "confirm" else 0.0,
                      label_origin=f"externally-attested:{entry['reviewer']}", review_entry_sha256=checksum)
    return samples


def verify_review_lineage(dataset):
    bundle = dataset.get("review_bundle")
    if not isinstance(bundle, dict) or set(bundle) != {"prior", "queue", "approvals"}:
        raise ValueError("Repair requires source-bound review lineage")
    reviewed = apply_reviews(bundle["prior"], bundle["queue"], bundle["approvals"])
    for before, after in zip(reviewed, dataset["samples"], strict=True):
        for key in ("id", "source_id", "bbox", "line_index", "split", "text", "confidence", "label_origin",
                    "label_status", "mapping_status", "visible_mapping", "review_entry_sha256"):
            if before.get(key) != after.get(key):
                raise ValueError("Admission changed outside recorded review")
        if before["split"] == "test" and any(before[key] != after[key] for key in ("raw_sha256", "mask_sha256", "cleaned_sha256")):
            raise ValueError("Locked test artifacts changed")


def validate_repair(root):
    root = Path(root)
    dataset = json.loads((root / "manifest.json").read_text())
    validate_dataset(dataset, root)
    lineage = json.loads((root / "lineage.json").read_text())
    prior = json.loads((root / "prior_manifest.json").read_text())
    queue = json.loads((root / "review.json").read_text())
    approvals = json.loads((root / "approvals.json").read_text())
    if lineage["prior_sha256"] != object_digest(prior):
        raise ValueError("Prior identity mismatch")
    reviewed = apply_reviews(prior, queue, approvals)
    for before, after in zip(reviewed, dataset["samples"], strict=True):
        for key in ("id", "source_id", "bbox", "line_index", "split", "text", "label_status", "mapping_status", "visible_mapping"):
            if before.get(key) != after.get(key):
                raise ValueError("Admission changed outside recorded review")
        if before["split"] == "test" and any(before[key] != after[key] for key in ("raw_sha256", "mask_sha256", "cleaned_sha256")):
            raise ValueError("Locked test artifacts changed")
    return dataset


def repair_dataset(prior_root, output, *, review=None, approvals=None, benchmark=None, target_review=None):
    prior_root, output = Path(prior_root).resolve(), Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty repair directory")
    prior = json.loads((prior_root / "manifest.json").read_text())
    validate_dataset(prior, prior_root)
    queue = review if review is not None else review_template(prior)
    approvals = approvals or {}
    samples = apply_reviews(prior, queue, approvals)
    payload = json.loads((prior_root / "input_manifest.json").read_text())
    by_id = {sample["id"]: sample for sample in samples}
    for sample in payload["samples"]:
        for key in ("text", "label_status", "confidence", "label_origin", "mapping_status", "visible_mapping", "review_entry_sha256"):
            if key in by_id[sample["id"]]:
                sample[key] = by_id[sample["id"]][key]
    for source in payload["sources"]:
        source["path"] = str(prior_root / next(row["path"] for row in prior["sources"] if row["id"] == source["id"]))
    payload["human_interventions"] = [entry for entry in queue["entries"] if entry["decision"] != "pending"]
    payload["review_bundle"] = {"prior": prior, "queue": queue, "approvals": approvals}
    with tempfile.TemporaryDirectory() as temporary:
        incoming = Path(temporary) / "input.json"
        write_json(incoming, payload)
        dataset = build_dataset(incoming, output, contract=prior["contract"], extraction_version="strong-seeds-v2")
    write_json(output / "prior_manifest.json", prior)
    write_json(output / "review.json", queue)
    write_json(output / "approvals.json", approvals)
    write_json(output / "lineage.json", {"prior_sha256": object_digest(prior), "prior_directory": str(prior_root),
                                        "repair_code_sha256": digest(Path(__file__)), "test_policy": "unchanged sealed reservations"})
    validate_repair(output)
    rows = [{"id": before["id"], "split": before["split"], "before": before["exclusions"], "after": after["exclusions"],
             "target_before": before["target_ink_pixels"], "target_after": after["target_ink_pixels"]}
            for before, after in zip(prior["samples"], dataset["samples"]) if before["split"] != "test"]
    report = {"scope": "bounded non-test repair; no automatic human approval", "admitted_before": prior["admitted_count"],
              "admitted_after": dataset["admitted_count"], "rows": rows, "promoted": False,
              "exclusions_before": dict(Counter(reason for row in rows for reason in row["before"])),
              "exclusions_after": dict(Counter(reason for row in rows for reason in row["after"])),
              "approval_boundary": "approvals are externally supplied trust inputs, not cryptographic proof of reviewer identity"}
    write_json(output / "repair_report.json", report)
    if benchmark:
        benchmark = Path(benchmark)
        gate = evaluate_benchmark(prior["contract"], json.loads((benchmark / "baseline_manifest.json").read_text()),
                                  benchmark, dataset=dataset, dataset_root=output, review=target_review)
        write_json(output / "G0.json", gate)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior", type=Path, default=ROOT / "reference/konrad_hand_recovery_v2")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--approvals", type=Path)
    parser.add_argument("--target-review", type=Path)
    parser.add_argument("--benchmark", type=Path, default=ROOT / "shared/training/konrad_hand_recovery/benchmark_v1")
    args = parser.parse_args()
    read = lambda path: json.loads(path.read_text()) if path else None
    print(json.dumps(repair_dataset(args.prior, args.output, review=read(args.review), approvals=read(args.approvals),
                                    benchmark=args.benchmark, target_review=read(args.target_review)), indent=2))


if __name__ == "__main__":
    main()
