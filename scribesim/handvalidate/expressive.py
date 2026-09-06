"""Frozen multi-seed G3 sensitivity evidence for opt-in persistent execution."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.evofit.repertoire import render_nominal, seed_repertoire
from scribesim.evofit.recovery import image_objective
from scribesim.handflow.controls import RepertoireControls
from scribesim.handflow.execution import PersistentRepertoireSession, require_g2
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.model import TrajectorySample
from scribesim.handvalidate.specimen import ROOT, RUBRIC, _artifact, digest, object_digest, write_json, write_equal_scale_panel
from scribesim.pathguide.repertoire import convert_word


MODES = {"neutral": {}, "ink": {"ink": True}, "pressure": {"pressure": .15},
         "angle": {"angle_deg": 3}, "rhythm": {"rhythm": .15},
         "combined": {"ink": True, "pressure": .15, "angle_deg": 3, "rhythm": .15}}
LIMITS = {"image_loss": .35, "corridor_mm": .25, "angle_deg": 5, "pressure": 1.15}


def assess_session(payload):
    errors = []
    state = payload["state"]
    rows = state["execution_trace"]
    controls = RepertoireControls(**payload["controls"])
    if not rows or len(rows) != len(payload["trajectory"]) or len(rows) != len(payload["owners"]):
        errors.append("trajectory_state_ownership_length")
    dips = [event for event in state["events"] if event["kind"] == "dip"]
    previous = None
    for row, sample in zip(rows, payload["trajectory"]):
        fields = ("time_before", "time_s", "contact_mm", "consumed", "ink_before", "ink_after", "pressure", "angle_deg", "habit_phase", "fatigue")
        if any(not isinstance(row.get(name), (int, float)) or not math.isfinite(row[name]) for name in fields):
            errors.append("nonfinite_state")
            continue
        distance = math.dist(row["from_mm"], row["to_mm"]) if row["previous_contact"] and row["contact"] else 0.0
        consumed = min(row["ink_before"], distance * controls.ink_per_mm * row["pressure"] / .5) if controls.ink else 0.0
        if abs(distance - row["contact_mm"]) > 1e-9 or abs(consumed - row["consumed"]) > 1e-9:
            errors.append("contact_consumption_mismatch")
        if abs(row["ink_before"] - row["consumed"] - row["ink_after"]) > 1e-9:
            errors.append("ink_step_conservation")
        if row["habit_phase"] != state["habit_phase"]:
            errors.append("hidden_motor_reset")
        if abs(row["angle_deg"] - row["nominal_angle_deg"]) > controls.angle_deg + 1e-8:
            errors.append("unsafe_angle_excursion")
        if (row["contact"] != sample["contact"] or row["to_mm"] != [sample["x_mm"], sample["y_mm"]]
                or row["pressure"] != sample["pressure"] or row["width_mm"] != sample["width_mm"]
                or row["angle_deg"] != sample["nib_angle_deg"]):
            errors.append("reviewed_trajectory_not_actual_state")
        if row["time_s"] <= row["time_before"] or not 0 <= row["ink_after"] <= 1 or not 0 <= row["pressure"] <= 1.15:
            errors.append("state_bounds")
        if previous is not None:
            if row["time_before"] < previous["time_s"] - 1e-9 or math.dist(row["from_mm"], previous["to_mm"]) > 1e-9:
                errors.append("hidden_time_or_position_reset")
            between_dips = [event for event in dips if previous["time_s"] - 1e-9 <= event["time_s"] <= row["time_before"] + 1e-9]
            refill = sum(event["ink_after"] - event["ink_before"] for event in between_dips)
            if abs(previous["ink_after"] + refill - row["ink_before"]) > 1e-8:
                errors.append("unrecorded_ink_reset")
            sitting = any(event["kind"] == "sitting_break" and previous["time_s"] <= event["time_s"] <= row["time_before"]
                          for event in state["events"])
            if row["fatigue"] < previous["fatigue"] - 1e-10 and not sitting:
                errors.append("hidden_fatigue_reset")
        previous = row
    consumed = sum(row["consumed"] for row in rows)
    refill = sum(event["ink_after"] - event["ink_before"] for event in dips)
    if (abs(consumed - state["consumed_ink"]) > 1e-8 or abs(refill - state["refilled_ink"]) > 1e-8
            or abs(1 + refill - consumed - state["ink_reservoir"]) > 1e-8):
        errors.append("session_ink_conservation")
    covered = set()
    expected = {(text_id, index) for text_id, text in enumerate(payload["texts"]) for index, character in enumerate(text) if not character.isspace()}
    for owner, sample in zip(payload["owners"], payload["trajectory"]):
        if not sample["contact"]:
            continue
        for start, end in owner["spans"]:
            covered.update((owner.get("text_id", 0), index) for index in range(start, end))
    if covered != expected:
        errors.append("exact_text_ownership_missing")
    contact = [row for row in rows if row["contact"]]
    metrics = {"coverage": 1.0 if covered == expected and expected else 0.0,
               "pressure_mean": float(np.mean([row["pressure"] for row in contact])) if contact else 0,
               "pressure_max": max((row["pressure"] for row in contact), default=0),
               "width_mean_mm": float(np.mean([row["width_mm"] or 0 for row in contact])) if contact else 0,
               "angle_mean": float(np.mean([row["angle_deg"] for row in contact])) if contact else 0,
               "angle_excursion_deg": max((abs(row["angle_deg"] - row["nominal_angle_deg"]) for row in contact), default=0),
               "corridor_mm": max((math.dist(row["to_mm"], row["desired_mm"]) for row in contact), default=0),
               "contact_mm": sum(row["contact_mm"] for row in rows), "consumed_ink": consumed,
               "dip_count": len(dips), "duration_s": state["time_s"]}
    return {"errors": sorted(set(errors)), "metrics": metrics}


def classify_control(name, before, after, *, image_delta, safe):
    fields = {"ink": ["consumed_ink"], "pressure": ["pressure_mean"], "angle": ["angle_mean"],
              "rhythm": ["duration_s"], "combined": ["consumed_ink", "pressure_mean", "angle_mean", "duration_s"]}
    active = image_delta > 1e-6 and any(abs(after[field] - before[field]) > 1e-5 for field in fields[name])
    return "inactive" if not active else "active-safe" if safe else "active-unsafe"


def decide_g3(freeze, matrix, review=None):
    blocked, failures = [], []
    if freeze["scope"] != "real-candidate" or freeze["prerequisite"].get("status") != "pass":
        blocked.append("G1_G2_real_candidate_not_accepted")
    required = {(seed, name) for seed in (7, 19, 41) for name in MODES if name != "neutral"}
    if freeze["seeds"] != [7, 19, 41] or len(matrix) != len(required) or {(row["seed"], row["control"]) for row in matrix} != required:
        blocked.append("complete_three_seed_control_matrix_missing")
    for row in matrix:
        if row["classification"] != "active-safe" or row["errors"] or row["coverage"] != 1 or row["replay"] is not True:
            failures.append(f'{row["control"]}:{row["seed"]}:{row["classification"]}')
    if not review or not review.get("reviewer") or not review.get("date"):
        blocked.append("expressive_owner_review_missing")
    elif set(review.get("rubric", {})) != set(RUBRIC) or any(value != "acceptable" for value in review.get("rubric", {}).values()):
        failures.append("expressive_appearance_not_accepted")
    return {"gate": "G3", "status": "fail" if failures else "blocked" if blocked else "pass",
            "reasons": sorted(set(blocked + failures)), "promoted": False,
            "recommendation": "proceed_to_opt_in_folio_candidate" if not failures and not blocked else "retain_neutral_disable_offending_controls"}


def execute_case(freeze, hand, seed, control):
    session = PersistentRepertoireSession(hand, seed=seed, controls=RepertoireControls(**freeze["controls"][control]),
                                         session_id="td018-expressive", dt=freeze["dt"])
    session.write_text("\n".join(freeze["texts"]))
    payload = session.export()
    images, line_rows = [], []
    offset = 0
    for line_index, text in enumerate(freeze["texts"]):
        bundle = convert_word(text, hand, baseline_y_mm=10 + line_index * 10)
        trajectory = []
        word_boxes = {}
        for sample, owner in zip(session.state.trace, payload["owners"]):
            on_line = any(start >= offset and end <= offset + len(text) for start, end in owner["spans"])
            trajectory.append(sample if on_line else replace(sample, contact=False, pressure=0.0, width_mm=0.0))
            if sample.contact and on_line:
                for span in owner["spans"]:
                    start = span[0] - offset
                    word_start = text.rfind(" ", 0, max(0, start)) + 1
                    box = word_boxes.setdefault(word_start, [sample.x_mm, sample.x_mm])
                    box[0], box[1] = min(box[0], sample.x_mm), max(box[1], sample.x_mm)
        actual = paint_trajectory(tuple(trajectory), bundle.metadata["frame_mm"], dpi=freeze["dpi"])
        nominal = render_nominal(text, hand, dpi=freeze["dpi"])
        mask = np.where(np.asarray(Image.fromarray(nominal).convert("L")) < 180, 255, 0).astype(np.uint8)
        boxes = [word_boxes[key] for key in sorted(word_boxes)]
        spacing = [right[0] - left[1] for left, right in zip(boxes, boxes[1:])]
        line_rows.append({"text": text, "nominal_image_loss": image_objective(nominal, mask, actual)["total"],
                          "word_gaps_mm": spacing})
        images.append(actual)
        offset += len(text) + 1
    return payload, images, line_rows


def _worker(output, suffix):
    freeze = json.loads((output / "freeze.json").read_text())
    hand = json.loads((output / "model.json").read_text())
    for seed in freeze["seeds"]:
        for control in freeze["controls"]:
            prefix = f"{control}-{seed}-{suffix}"
            payload, images, lines = execute_case(freeze, hand, seed, control)
            path = output / f"{prefix}.json.gz"
            if path.exists():
                raise ValueError("Refusing to overwrite expressive evidence")
            path.write_bytes(gzip.compress(json.dumps({"session": payload, "lines": lines}, sort_keys=True, allow_nan=False).encode(), mtime=0))
            for index, image in enumerate(images):
                Image.fromarray(image).save(output / f"{prefix}-{index}.png")


def measure_matrix(output, freeze, *, replay_execution=False):
    hand = json.loads((output / "model.json").read_text())
    matrix, cases = [], []
    for seed in freeze["seeds"]:
        baseline = json.loads(gzip.decompress((output / f"neutral-{seed}-first.json.gz").read_bytes()))
        neutral_metrics = assess_session(baseline["session"])
        for control in freeze["controls"]:
            prefix = f"{control}-{seed}"
            data = json.loads(gzip.decompress((output / f"{prefix}-first.json.gz").read_bytes()))
            if replay_execution:
                payload, images, lines = execute_case(freeze, hand, seed, control)
                if data != {"session": payload, "lines": lines}:
                    raise ValueError("Frozen seeded execution does not reproduce the recorded state")
                for index, actual in enumerate(images):
                    if not np.array_equal(actual, np.asarray(Image.open(output / f"{prefix}-first-{index}.png"))):
                        raise ValueError("Reviewed image is not the actual seeded trajectory")
            audit = assess_session(data["session"])
            replay = digest(output / f"{prefix}-first.json.gz") == digest(output / f"{prefix}-replay.json.gz")
            image_deltas = []
            for index in range(len(freeze["texts"])):
                first = output / f"{prefix}-first-{index}.png"
                replay &= digest(first) == digest(output / f"{prefix}-replay-{index}.png")
                neutral = np.asarray(Image.open(output / f"neutral-{seed}-first-{index}.png")).astype(float)
                image_deltas.append(float(np.mean(np.abs(np.asarray(Image.open(first)).astype(float) - neutral))) / 255)
            safe = (not audit["errors"] and not neutral_metrics["errors"] and audit["metrics"]["coverage"] == 1
                    and audit["metrics"]["corridor_mm"] <= freeze["limits"]["corridor_mm"]
                    and audit["metrics"]["pressure_max"] <= freeze["limits"]["pressure"]
                    and audit["metrics"]["angle_excursion_deg"] <= freeze["limits"]["angle_deg"]
                    and all(row["nominal_image_loss"] <= freeze["limits"]["image_loss"] for row in data["lines"] + baseline["lines"]))
            if control == "neutral":
                cases.append({"seed": seed, "neutral_safe": safe, "replay": replay, "lines": data["lines"]})
                continue
            matrix.append({"seed": seed, "control": control,
                "classification": classify_control(control, neutral_metrics["metrics"], audit["metrics"], image_delta=max(image_deltas), safe=safe),
                "replay": bool(replay), "coverage": audit["metrics"]["coverage"], "errors": audit["errors"],
                "metrics": audit["metrics"], "neutral_metrics": neutral_metrics["metrics"], "image_deltas": image_deltas,
                "lines": data["lines"], "rollback": "neutral" if not safe else "not promoted pending gates/review"})
    return matrix, cases


def build_expressive(output, *, texts=None, bridge_root=None, nominal_root=None, limits=None, g1_review=None, **g1_options):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty expressive directory")
    output.mkdir(parents=True, exist_ok=True)
    scope, prerequisite = "synthetic-diagnostic", {"status": "blocked"}
    if bridge_root is not None:
        try:
            hand, bridge = require_g2(bridge_root, nominal_root=nominal_root, review=g1_review, **g1_options)
        except ValueError as error:
            gate = {"gate": "G3", "status": "blocked", "reasons": [str(error)], "executed": False, "promoted": False}
            write_json(output / "G3.json", gate)
            return gate
        if texts is not None or not limits or limits.get("bridge_freeze_sha256") != object_digest(bridge) or limits.get("status") != "frozen_development":
            raise ValueError("Use accepted proof inventory and bridge-bound development limits")
        texts = bridge["texts"]
        scope, prerequisite = "real-candidate", {"status": "pass", "bridge_freeze_sha256": object_digest(bridge)}
        limits = limits["limits"]
    else:
        if texts is None:
            contract = json.loads((ROOT / "shared/training/konrad_hand_recovery/benchmark_v1/contract.json").read_text())
            texts = [row["text"] for row in contract["proofs"]]
        hand = seed_repertoire("".join(texts))
        limits = dict(LIMITS)
    if len(texts) != 3 or any(not text.strip() or "\n" in text for text in texts):
        raise ValueError("Exactly three nonempty proof lines required")
    if set(limits) != set(LIMITS) or any(not math.isfinite(value) or value < 0 for value in limits.values()):
        raise ValueError("Finite complete expressive limits required")
    write_json(output / "model.json", hand)
    freeze = {"schema_version": 1, "scope": scope, "prerequisite": prerequisite, "texts": texts,
              "seeds": [7, 19, 41], "controls": {name: asdict(RepertoireControls(**values)) for name, values in MODES.items()},
              "dt": .002, "dpi": 180, "limits": limits, "model_sha256": object_digest(hand),
              "model_file_sha256": digest(output / "model.json"),
              "code": {str(path.relative_to(ROOT)): digest(path) for path in
                       (Path(__file__), ROOT / "scribesim/handflow/execution.py", ROOT / "scribesim/handflow/controller.py",
                        ROOT / "scribesim/handflow/model.py", ROOT / "scribesim/handflow/controls.py", ROOT / "scribesim/handflow/planning.py",
                        ROOT / "scribesim/pathguide/repertoire.py", ROOT / "scribesim/evofit/repertoire.py", ROOT / "scribesim/handvalidate/bridge.py")}}
    write_json(output / "freeze.json", freeze)
    commands = []
    for suffix, hash_seed in (("first", "7"), ("replay", "839")):
        command = [sys.executable, "-m", "scribesim.handvalidate.expressive", "worker", "--output", str(output.resolve()), "--suffix", suffix]
        subprocess.run(command, check=True, cwd=ROOT, env={**os.environ, "PYTHONHASHSEED": hash_seed})
        commands.append({"command": command, "PYTHONHASHSEED": hash_seed, "fresh_process": True})
    matrix, cases = measure_matrix(output, freeze)
    tiles = []
    for control in MODES:
        for index, text in enumerate(texts):
            tiles.append((f'{scope} | seed 7 | {control} | {text}', Image.open(output / f"{control}-7-first-{index}.png"), hand["x_height_mm"] * 180 / 25.4))
    write_equal_scale_panel(tiles, output / "comparison.png")
    source = ROOT / "shared/training/konrad_hand_recovery/benchmark_v1/target_sheet.png"
    (output / "reference-sheet.png").write_bytes(source.read_bytes())
    report = {"schema_version": 1, "freeze_sha256": object_digest(freeze), "matrix": matrix, "neutral_cases": cases,
              "commands": commands, "artifacts": {path.name: digest(path) for path in output.iterdir() if path.is_file()}}
    write_json(output / "report.json", report)
    write_json(output / "review-template.json", {"reviewer": None, "date": None, "freeze_sha256": object_digest(freeze),
               "report_sha256": object_digest(report), "rubric": {name: "pending" for name in RUBRIC}})
    gate = evaluate_expressive(output, bridge_root=bridge_root, nominal_root=nominal_root, g1_review=g1_review, **g1_options)
    write_json(output / "G3.json", gate)
    return gate


def evaluate_expressive(output, review=None, *, bridge_root=None, nominal_root=None, g1_review=None, **g1_options):
    output = Path(output)
    try:
        freeze = json.loads((output / "freeze.json").read_text())
        report = json.loads((output / "report.json").read_text())
        if report["freeze_sha256"] != object_digest(freeze):
            raise ValueError("Expressive freeze identity mismatch")
        hand = json.loads((output / "model.json").read_text())
        if (freeze["schema_version"] != 1 or len(freeze["texts"]) != 3
                or freeze["model_sha256"] != object_digest(hand) or freeze["model_file_sha256"] != digest(output / "model.json")
                or freeze["controls"] != {name: asdict(RepertoireControls(**values)) for name, values in MODES.items()}):
            raise ValueError("Expressive model/inventory/isolated control contract changed")
        if (len(report.get("commands", [])) != 2 or any(row.get("fresh_process") is not True for row in report["commands"])
                or len({row["PYTHONHASHSEED"] for row in report["commands"]}) != 2):
            raise ValueError("Fresh-process expressive provenance missing")
        for relative, checksum in report["artifacts"].items():
            if digest(_artifact(output, relative)) != checksum:
                raise ValueError(f"Expressive artifact changed: {relative}")
        for relative, checksum in freeze["code"].items():
            if digest(_artifact(ROOT, relative)) != checksum:
                raise ValueError(f"Expressive execution code changed: {relative}")
        matrix, cases = measure_matrix(output, freeze, replay_execution=True)
        if matrix != report["matrix"] or cases != report["neutral_cases"]:
            raise ValueError("Reported sensitivity differs from actual frozen execution")
        if review and (review.get("freeze_sha256") != object_digest(freeze) or review.get("report_sha256") != object_digest(report)):
            raise ValueError("Stale expressive owner review")
        gate = decide_g3(freeze, matrix, review)
        if any(not row["neutral_safe"] or not row["replay"] for row in cases):
            gate["status"] = "fail"
            gate["reasons"].append("neutral_G2_quality_or_replay_failed")
        changed = {digest(output / f"combined-{seed}-first-0.png") for seed in freeze["seeds"]}
        if len(changed) != 3:
            gate["status"] = "fail"
            gate["reasons"].append("changed_seed_variation_inactive")
        if freeze["scope"] == "real-candidate":
            hand, bridge = require_g2(bridge_root, nominal_root=nominal_root, review=g1_review, **g1_options)
            if object_digest(bridge) != freeze["prerequisite"]["bridge_freeze_sha256"] or object_digest(hand) != freeze["model_sha256"]:
                raise ValueError("Upstream hand or bridge changed")
            if freeze["texts"] != bridge["texts"]:
                raise ValueError("Expressive proof inventory differs from accepted bridge")
        return gate
    except (ValueError, KeyError, TypeError, OSError) as error:
        return {"gate": "G3", "status": "fail", "reasons": [str(error)], "promoted": False, "recommendation": "repair_evidence_or_retain_neutral"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "evaluate", "worker"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--suffix", choices=["first", "replay"])
    parser.add_argument("--bridge-root", type=Path)
    parser.add_argument("--nominal-root", type=Path)
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument("--benchmark-root", type=Path)
    parser.add_argument("--target-review", type=Path)
    parser.add_argument("--nominal-review", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--limits", type=Path)
    args = parser.parse_args()
    if args.action == "worker":
        if not args.suffix:
            parser.error("worker requires --suffix")
        _worker(args.output, args.suffix)
        return
    options = {"bridge_root": args.bridge_root, "nominal_root": args.nominal_root,
               "dataset_root": args.dataset_root, "benchmark_root": args.benchmark_root,
               "target_review": json.loads(args.target_review.read_text()) if args.target_review else None,
               "g1_review": json.loads(args.nominal_review.read_text()) if args.nominal_review else None}
    if args.action == "build":
        gate = build_expressive(args.output, limits=json.loads(args.limits.read_text()) if args.limits else None, **options)
    else:
        gate = evaluate_expressive(args.output, json.loads(args.review.read_text()) if args.review else None,
                                    **options)
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    main()
