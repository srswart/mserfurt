"""Frozen TD-018 nominal specimens. A seed diagnostic is never a G1 candidate."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.evofit.recovery import OBJECTIVE, _gray, _place, image_objective
from scribesim.evofit.repertoire import compose, render_nominal, seed_repertoire
from scribesim.handvalidate.specimen import (
    ROOT, RUBRIC, _artifact, digest, evaluate_benchmark, object_digest, write_equal_scale_panel, write_json,
)


DEFAULT_BENCHMARK = ROOT / "shared/training/konrad_hand_recovery/benchmark_v1"
DEFAULT_DATASET = ROOT / "reference/konrad_hand_recovery_v2"
CONTROLS = {"correct", "wrong_letter", "filled_counter", "extra_stroke", "distorted_aspect"}


def _texts(freeze):
    return [proof["text"] for proof in freeze["proofs"]] + freeze["synthetic_unseen"]


def _criteria_ready(criteria):
    return (criteria.get("status") == "frozen_train_development" and all(
        isinstance(criteria.get(name), (int, float)) and not isinstance(criteria[name], bool)
        and math.isfinite(criteria[name]) and 0 <= criteria[name] <= 1
        for name in ("per_case_max_loss", "per_case_max_regression", "unseen_mean_min_gain")))


def decide_g1(freeze, report, review=None):
    """Pure decision logic; evaluate_nominal additionally verifies actual artifacts/readiness."""
    failures, blocked = [], []
    if report.get("freeze_sha256") != object_digest(freeze) or report.get("model_sha256") != freeze["model_sha256"]:
        failures.append("stale_model_or_freeze_identity")
    if freeze["g0"]["status"] != "pass":
        blocked.append("G0_not_passed")
    if freeze["scope"] != "real-corpus-candidate":
        blocked.append("no_recovered_real_corpus_candidate")
    if not _criteria_ready(freeze["criteria"]):
        blocked.append("calibrated_tolerances_not_frozen")
    if freeze.get("revision") not in (0, 1):
        failures.append("test_reuse_requires_new_reservation")
    expected = _texts(freeze)
    proofs = report.get("proofs", [])
    if len(freeze["proofs"]) != 3 or {row["kind"] for row in freeze["proofs"]} != {"reconstruction", "unseen", "project_text"}:
        failures.append("three_line_inventory_invalid")
    if len(set(freeze["synthetic_unseen"])) < 5:
        failures.append("five_unseen_strings_required")
    if set(freeze["synthetic_unseen"]) & set(freeze.get("training_texts", [])):
        failures.append("synthetic_unseen_inventory_contains_training_words")
    if [row.get("text") for row in proofs] != expected:
        failures.append("proof_text_omission_or_substitution")
    for proof in proofs:
        if proof.get("coverage") != 1 or proof.get("aliases") != 0 or proof.get("normalizations") != 0:
            failures.append("exact_mapping_failed")
        if proof.get("replay") is not True:
            failures.append("fresh_process_replay_failed")
    if set(report.get("controls", {})) != CONTROLS or any(value is not True for value in report.get("controls", {}).values()):
        failures.append("objective_controls_failed_or_missing")
    rows = report.get("word_results", [])
    required = [row for row in freeze["test_inventory"] if row["admission"] == "auto_admitted"]
    if not report.get("test_scored"):
        blocked.append("locked_test_not_scored")
        if rows:
            failures.append("unscored_test_has_measurements")
    else:
        if sorted(row.get("id", "") for row in rows) != sorted(row["id"] for row in required):
            failures.append("missing_or_duplicate_locked_cases")
        for group in ("repeated", "unseen"):
            if not any(row.get("group") == group for row in rows):
                blocked.append(f"empty_{group}_test_group")
        for row in rows:
            if not any(sample["id"] == row.get("id") and sample["group"] == row.get("group") for sample in required):
                failures.append("incorrect_test_group")
            if row.get("coverage") != 1:
                failures.append("locked_text_coverage_failed")
            if any(not isinstance(row.get(name), (int, float)) or not math.isfinite(row[name]) or not 0 <= row[name] <= 1
                   for name in ("candidate_loss", "baseline_loss")):
                failures.append("invalid_per_case_measurement")
                continue
            if _criteria_ready(freeze["criteria"]):
                if row["candidate_loss"] > freeze["criteria"]["per_case_max_loss"]:
                    failures.append(f'per_case_loss_failed:{row["id"]}')
                if row["candidate_loss"] - row["baseline_loss"] > freeze["criteria"]["per_case_max_regression"]:
                    failures.append(f'per_case_regression:{row["id"]}')
        unseen = [row for row in rows if row.get("group") == "unseen"]
        if unseen and not failures and _criteria_ready(freeze["criteria"]):
            if float(np.mean([row["baseline_loss"] - row["candidate_loss"] for row in unseen])) < freeze["criteria"]["unseen_mean_min_gain"]:
                failures.append("unseen_mean_gain_failed")
    if not review or not review.get("reviewer") or not review.get("date"):
        blocked.append("owner_appearance_review_missing")
        blocked.append("independent_reading_missing")
    else:
        if review.get("freeze_sha256") != object_digest(freeze) or review.get("report_sha256") != object_digest(report):
            failures.append("stale_review_identity")
        if set(review.get("rubric", {})) != set(RUBRIC) or any(value != "acceptable" for value in review.get("rubric", {}).values()):
            blocked.append("appearance_rubric_not_accepted")
        if any(value in {"unacceptable", "revise", "reject"} for value in review.get("rubric", {}).values()):
            failures.append("appearance_rejected")
        if review.get("preference") != "candidate":
            blocked.append("candidate_not_preferred_to_baseline")
        if review.get("preference") == "baseline":
            failures.append("baseline_preferred")
        reading = review.get("independent_reading")
        if not reading or not reading.get("reviewer") or not reading.get("date"):
            blocked.append("independent_reading_missing")
        elif reading.get("transcriptions") != expected:
            failures.append("independent_reading_text_mismatch")
    status = "fail" if failures else "blocked" if blocked else "pass"
    return {"gate": "G1", "status": status, "reasons": sorted(set(failures + blocked)), "promoted": False,
            "recommendation": "proceed_to_guided_candidate" if status == "pass" else "stop_and_repair_prerequisites" if blocked else "revise_once_or_stop",
            "scope": "Nominal appearance/text milestone, not historical ductus or production promotion"}


def objective_controls():
    mask = np.zeros((40, 60), dtype=np.uint8)
    mask[8:32, 10:40] = 255
    mask[13:27, 15:35] = 0
    correct = np.where(mask == 255, 0, 255).astype(np.uint8)
    filled = correct.copy()
    filled[13:27, 15:35] = 0
    extra = correct.copy()
    extra[3:6, 3:55] = 0
    wrong = np.full_like(correct, 255)
    wrong[10:30, 28:32] = 0
    distorted = np.full_like(correct, 255)
    distorted[:, :30] = correct[:, ::2]
    losses = {name: image_objective(correct, mask, image)["total"] for name, image in
              (("correct", correct), ("wrong_letter", wrong), ("filled_counter", filled),
               ("extra_stroke", extra), ("distorted_aspect", distorted))}
    return {name: loss == 0 if name == "correct" else loss > losses["correct"] for name, loss in losses.items()}, losses


def _readiness(dataset_root, benchmark_root, review):
    dataset = json.loads((dataset_root / "manifest.json").read_text())
    contract = json.loads((benchmark_root / "contract.json").read_text())
    baselines = json.loads((benchmark_root / "baseline_manifest.json").read_text())
    gate = evaluate_benchmark(contract, baselines, benchmark_root, dataset=dataset, review=review, dataset_root=dataset_root)
    return dataset, contract, gate


def _worker(output, suffix):
    freeze = json.loads((output / "freeze.json").read_text())
    for backend in ("candidate", "baseline"):
        hand = json.loads((output / f"{backend}.json").read_text())
        for index, text in enumerate(_texts(freeze)):
            path = output / f"{backend}-{index}-{suffix}.png"
            if path.exists():
                raise ValueError("Refusing to overwrite an existing worker render")
            Image.fromarray(render_nominal(text, hand, dpi=freeze["dpi"])).save(path)


def _score_locked(freeze, dataset, dataset_root, candidate, baseline):
    results = []
    for sample in dataset["samples"]:
        if sample["split"] != "test" or sample["admission"] != "auto_admitted":
            continue
        raw = np.asarray(Image.open(dataset_root / sample["raw_path"]))
        mask = np.asarray(Image.open(dataset_root / sample["mask_path"]))
        baseline_image = render_nominal(sample["text"], baseline, dpi=freeze["dpi"])
        scale = sample["xheight_native_px"] / (baseline["x_height_mm"] * freeze["dpi"] / 25.4)
        alignment = {"scale": scale, "left": round((mask.shape[1] - baseline_image.shape[1] * scale) / 2),
                     "top": round((mask.shape[0] - baseline_image.shape[0] * scale) / 2)}
        candidate_image = render_nominal(sample["text"], candidate, dpi=freeze["dpi"])
        baseline_terms = image_objective(raw, mask, _place(baseline_image, mask.shape, alignment))
        candidate_terms = image_objective(raw, mask, _place(candidate_image, mask.shape, alignment))
        inventory = next(row for row in freeze["test_inventory"] if row["id"] == sample["id"])
        results.append({"id": sample["id"], "text": sample["text"], "group": inventory["group"],
                        "coverage": compose(sample["text"], candidate)["coverage"], "reference_status": "real-native-locked-test",
                        "candidate_loss": candidate_terms["total"], "baseline_loss": baseline_terms["total"],
                        "candidate_components": candidate_terms, "baseline_components": baseline_terms,
                        "alignment": alignment, "raw_sha256": sample["raw_sha256"], "mask_sha256": sample["mask_sha256"]})
    return results


def build_nominal(output, *, dataset_root=DEFAULT_DATASET, benchmark_root=DEFAULT_BENCHMARK,
                  recovery_root=None, criteria=None, target_review=None):
    output, dataset_root, benchmark_root = Path(output), Path(dataset_root), Path(benchmark_root)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty specimen directory")
    dataset, contract, gate = _readiness(dataset_root, benchmark_root, target_review)
    proofs = contract["proofs"]
    unseen = next(row["text"] for row in proofs if row["kind"] == "unseen").split()
    alphabet = "".join(row["text"] for row in proofs)
    candidate = seed_repertoire(alphabet)
    baseline = seed_repertoire(alphabet, variants=False)
    scope = "unaccepted-seed-diagnostic"
    recovery_identity = None
    if recovery_root is not None:
        recovery_root = Path(recovery_root)
        recovered = json.loads((recovery_root / "report.json").read_text())
        if (recovered.get("status") != "unaccepted-real-corpus-candidate" or
                recovered.get("dataset_sha256") != digest(dataset_root / "manifest.json") or
                recovered.get("contract_sha256") != object_digest(contract) or
                recovered.get("selected_sha256") != digest(recovery_root / "selected.json") or
                recovered.get("initial_sha256") != digest(recovery_root / "initial.json") or
                recovered.get("config_sha256") != digest(recovery_root / "config.json")):
            raise ValueError("Recovery checkpoint is stale, synthetic or unrelated to this dataset/contract")
        candidate = json.loads((recovery_root / "selected.json").read_text())
        baseline = json.loads((recovery_root / "initial.json").read_text())
        scope = "real-corpus-candidate"
        recovery_identity = digest(recovery_root / "report.json")
    criteria = criteria or {"status": "pending_real_source_calibration", "per_case_max_loss": None,
                            "per_case_max_regression": None, "unseen_mean_min_gain": None}
    if _criteria_ready(criteria) and criteria.get("source_calibration_sha256") != object_digest(dataset["calibration"]):
        raise ValueError("Tolerances must identify the train/development source calibration")
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "candidate.json", candidate)
    write_json(output / "baseline.json", baseline)
    write_json(output / "contract.json", contract)
    write_json(output / "criteria.json", criteria)
    shutil.copyfile(benchmark_root / "target_sheet.png", output / "reference-sheet.png")
    training_texts = {row["text"] for row in dataset["samples"] if row["split"] == "train" and row["admission"] == "auto_admitted"}
    inventory = [{"id": row["id"], "text": row.get("text"), "admission": row["admission"],
                  "group": "repeated" if row.get("text") in training_texts else "unseen", "exclusions": row["exclusions"],
                  "raw_sha256": row["raw_sha256"], "mask_sha256": row["mask_sha256"]}
                 for row in dataset["samples"] if row["split"] == "test"]
    freeze = {"schema_version": 1, "scope": scope, "g0": gate, "criteria": criteria, "proofs": proofs,
              "training_texts": sorted(training_texts),
              "synthetic_unseen": unseen, "test_inventory": inventory, "model_sha256": object_digest(candidate),
              "baseline_sha256": object_digest(baseline), "revision": 0, "recovery_report_sha256": recovery_identity,
              "dataset_sha256": digest(dataset_root / "manifest.json"), "contract_sha256": object_digest(contract),
              "dpi": 180, "objective": OBJECTIVE, "nuisance_policy": "native xheight scale; baseline-centered placement frozen for both candidates",
              "baseline_identity": "recovery initial repertoire" if recovery_root else "neutral catalog repertoire adapter; not the production CLI",
              "files": {name: digest(output / name) for name in ("candidate.json", "baseline.json", "contract.json", "criteria.json", "reference-sheet.png")},
              "code": {str(path.relative_to(ROOT)): digest(path) for path in
                       (Path(__file__), ROOT / "scribesim/evofit/repertoire.py", ROOT / "scribesim/evofit/recovery.py",
                        ROOT / "scribesim/evo/renderer.py", ROOT / "scribesim/evo/genome.py")}}
    write_json(output / "freeze.json", freeze)
    commands = []
    for suffix, hash_seed in (("first", "7"), ("replay", "917")):
        command = [sys.executable, "-m", "scribesim.handvalidate.nominal", "worker", "--output", str(output.resolve()), "--suffix", suffix]
        subprocess.run(command, check=True, cwd=ROOT, env={**os.environ, "PYTHONHASHSEED": hash_seed})
        commands.append({"command": command, "PYTHONHASHSEED": hash_seed, "fresh_process": True})
    records, comparison, unblinding = [], [], []
    rng = random.Random(18018)
    for index, text in enumerate(_texts(freeze)):
        plan = compose(text, candidate)
        row = {"text": text, "coverage": plan["coverage"], "aliases": 0, "normalizations": 0,
               "plan": plan, "reference_status": "unscored-synthetic-combination" if index >= 3 or proofs[index]["kind"] == "unseen" else "unscored-proof-line"}
        for backend in ("candidate", "baseline"):
            row[backend + "_path"] = f"{backend}-{index}-first.png"
            row[backend + "_sha256"] = digest(output / row[backend + "_path"])
            row[backend + "_replay_path"] = f"{backend}-{index}-replay.png"
            row[backend + "_replay_sha256"] = digest(output / row[backend + "_replay_path"])
        row["replay"] = all(row[backend + "_sha256"] == row[backend + "_replay_sha256"] for backend in ("candidate", "baseline"))
        records.append(row)
        order = ["candidate", "baseline"]
        rng.shuffle(order)
        for label, backend in zip(("A", "B"), order):
            hand = candidate if backend == "candidate" else baseline
            comparison.append((f'{scope} | {text} | {label}', Image.open(output / row[backend + "_path"]), hand["x_height_mm"] * freeze["dpi"] / 25.4))
        unblinding.append({"text": text, "A": order[0], "B": order[1]})
    write_equal_scale_panel(comparison, output / "comparison.png")
    write_equal_scale_panel([(f'{scope} | {proofs[index]["kind"]}: {records[index]["text"]}',
                             Image.open(output / records[index]["candidate_path"]), candidate["x_height_mm"] * freeze["dpi"] / 25.4)
                            for index in range(3)], output / "three-line.png")
    write_json(output / "unblinding.json", unblinding)
    eligible = gate["status"] == "pass" and scope == "real-corpus-candidate" and _criteria_ready(criteria)
    results = _score_locked(freeze, dataset, dataset_root, candidate, baseline) if eligible else []
    controls, control_losses = objective_controls()
    report = {"schema_version": 1, "freeze_sha256": object_digest(freeze), "model_sha256": object_digest(candidate),
              "proofs": records, "test_scored": eligible, "word_results": results,
              "worst_cases": sorted(results, key=lambda row: row["candidate_loss"], reverse=True),
              "exclusions": [row for row in inventory if row["admission"] != "auto_admitted"],
              "controls": controls, "control_losses": control_losses, "commands": commands,
              "environment": {"python": platform.python_version(), "numpy": np.__version__, "pillow": Image.__version__},
              "motion_diagnostics": "not measured: nominal geometry-only milestone", "independent_reading": "pending",
              "artifacts": {name: digest(output / name) for name in ("comparison.png", "three-line.png", "unblinding.json")}}
    write_json(output / "report.json", report)
    write_json(output / "review-template.json", {"reviewer": None, "date": None, "freeze_sha256": object_digest(freeze),
               "report_sha256": object_digest(report), "rubric": {name: "pending" for name in RUBRIC},
               "preference": "pending", "independent_reading": None})
    result = evaluate_nominal(output, dataset_root=dataset_root, benchmark_root=benchmark_root, target_review=target_review)
    write_json(output / "G1.json", result)
    return result


def evaluate_nominal(output, review=None, *, dataset_root=None, benchmark_root=None, target_review=None):
    output = Path(output)
    try:
        freeze = json.loads((output / "freeze.json").read_text())
        report = json.loads((output / "report.json").read_text())
        for name, checksum in {**freeze["files"], **report["artifacts"]}.items():
            if digest(_artifact(output, name)) != checksum:
                raise ValueError(f"Artifact hash mismatch: {name}")
        for relative, checksum in freeze["code"].items():
            if digest(_artifact(ROOT, relative)) != checksum:
                raise ValueError(f"Stale evaluator/renderer code: {relative}")
        candidate = json.loads((output / "candidate.json").read_text())
        baseline = json.loads((output / "baseline.json").read_text())
        if object_digest(candidate) != freeze["model_sha256"]:
            raise ValueError("Candidate identity mismatch")
        if object_digest(baseline) != freeze["baseline_sha256"]:
            raise ValueError("Baseline identity mismatch")
        if freeze["objective"] != OBJECTIVE or report["controls"] != objective_controls()[0]:
            raise ValueError("Objective configuration/controls differ from actual evaluator")
        if len(report.get("commands", [])) != 2 or any(row.get("fresh_process") is not True for row in report["commands"]):
            raise ValueError("Fresh-process execution provenance missing")
        for row in report["proofs"]:
            if compose(row["text"], candidate) != row["plan"]:
                raise ValueError("Stored exact word plan does not match actual model")
            for backend in ("candidate", "baseline"):
                for suffix in ("", "_replay"):
                    if digest(_artifact(output, row[backend + suffix + "_path"])) != row[backend + suffix + "_sha256"]:
                        raise ValueError("Proof/replay image hash mismatch")
                if row[backend + "_sha256"] != row[backend + "_replay_sha256"]:
                    raise ValueError("Actual fresh-process replay differs")
                rendered = render_nominal(row["text"], candidate if backend == "candidate" else baseline, dpi=freeze["dpi"])
                if not np.array_equal(rendered, np.asarray(Image.open(output / row[backend + "_path"]))):
                    raise ValueError("Proof pixels do not come from declared model")
        result = decide_g1(freeze, report, review)
        if freeze["g0"]["status"] == "pass":
            if dataset_root is None or benchmark_root is None:
                result["reasons"].append("live_readiness_integrity_unverified")
                if result["status"] != "fail":
                    result["status"] = "blocked"
            else:
                dataset_root, benchmark_root = Path(dataset_root), Path(benchmark_root)
                dataset, contract, gate = _readiness(dataset_root, benchmark_root, target_review)
                if (digest(dataset_root / "manifest.json") != freeze["dataset_sha256"]
                        or object_digest(contract) != freeze["contract_sha256"] or gate != freeze["g0"]):
                    raise ValueError("Stale dataset, split, calibration or target-review identity")
                if report["test_scored"] and report["word_results"] != _score_locked(freeze, dataset, dataset_root, candidate, baseline):
                    raise ValueError("Reported locked losses differ from actual frozen checkpoint")
        if result["status"] != "pass":
            result["recommendation"] = "stop_and_repair_prerequisites"
        return result
    except (ValueError, KeyError, TypeError, OSError) as error:
        return {"gate": "G1", "status": "fail", "reasons": [str(error)], "promoted": False, "recommendation": "repair_evidence_integrity"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "evaluate", "worker"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--suffix", choices=["first", "replay"])
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--benchmark-root", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--recovery-root", type=Path)
    parser.add_argument("--criteria", type=Path)
    parser.add_argument("--target-review", type=Path)
    parser.add_argument("--review", type=Path)
    args = parser.parse_args()
    if args.action == "worker":
        if not args.suffix:
            parser.error("worker requires --suffix")
        _worker(args.output, args.suffix)
        return
    target_review = json.loads(args.target_review.read_text()) if args.target_review else None
    if args.action == "build":
        result = build_nominal(args.output, dataset_root=args.dataset_root, benchmark_root=args.benchmark_root,
                               recovery_root=args.recovery_root, target_review=target_review,
                               criteria=json.loads(args.criteria.read_text()) if args.criteria else None)
    else:
        result = evaluate_nominal(args.output, json.loads(args.review.read_text()) if args.review else None,
                                  dataset_root=args.dataset_root, benchmark_root=args.benchmark_root, target_review=target_review)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
