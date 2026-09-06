"""Bounded shared-primitive learning with staged, source-qualified evidence."""

import argparse
import copy
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from scribesim.evofit.stroke_language import (
    compile_text, execute_language, render_language, seed_language, validate_language,
)
from scribesim.handvalidate.specimen import ROOT, digest, evaluate_benchmark, object_digest, write_json


LIMITS = {"heldout_improvement_ratio": .75, "actual_image_loss": .35, "corridor_error_mm": .25,
          "minimum_parameter_change": .01}
SEEDS = [7, 19, 41]
FRAME = [-2.0, 12.0, 2.0, 14.0]
DPI = 150


def exercise_model(model, exercise):
    if exercise.get("kind") == "word":
        return model, exercise["text"]
    candidate = copy.deepcopy(model)
    strokes = [{"primitive": name, "offset": [exercise["offset"][0] + index * 1.2, exercise["offset"][1]],
                "scale": exercise["scale"], "rotation_deg": 0, "transition": "start" if index == 0 else "lift"}
               for index, name in enumerate(exercise["primitives"])]
    candidate["recipes"] = {"exercise": {"logical": "i", "visible": "i", "advance": 3.0,
                                          "strokes": strokes, "allow_crossings": True}}
    candidate["letter_rules"], candidate["word_rules"] = [], []
    return candidate, "i"


def render_exercise(model, exercise, *, dpi=None):
    candidate, text = exercise_model(model, exercise)
    return render_language(text, candidate, dpi=dpi or exercise.get("dpi", DPI), frame=exercise.get("frame", FRAME))


def _ink(image):
    gray = np.asarray(Image.fromarray(np.asarray(image, dtype=np.uint8)).convert("L"), dtype=float)
    return np.clip((235 - gray) / 190, 0, 1)


def stroke_loss(raw, rendered, mask=None):
    if raw.shape != rendered.shape:
        raise ValueError("Native target and rendered physical frame disagree")
    target, candidate = _ink(raw), _ink(rendered)
    if mask is not None:
        target = target * (mask != 128)
        candidate = candidate * (mask != 128)
    return float(np.abs(target - candidate).sum() / max(1.0, target.sum() + candidate.sum()))


def synthetic_exercises(*, families=None):
    initial = seed_language()
    target = copy.deepcopy(initial)
    controls = {
        "stem": [[0, .72], [0, .28]], "rise": [[.12, .32], [.35, .72]],
        "bowl": [[.62, .99], [.92, .34]], "turn": [[.3, .16], [.5, .65]],
        "loop": [[-.65, 1.3], [.85, 1.3]], "exit": [[.12, .01], [.32, .1]],
    }
    for name, points in controls.items():
        target["primitives"][name]["cubics"][0][1:3] = points
    validate_language(target)
    selected = sorted(families or initial["primitives"])
    if not selected or not set(selected) <= set(initial["primitives"]):
        raise ValueError("Unknown primitive exercise family")
    samples = []
    for name in selected:
        for suffix, split, scale, offset, count in (
                ("base", "train", 1.0, [0, 0], 1), ("small", "train", .85, [.1, .1], 1),
                ("large", "development", 1.1, [-.1, 0], 1), ("unseen-scale", "test", .7, [.25, .2], 1),
                ("unseen-pair", "test", 1.0, [0, 0], 2)):
            exercise = {"id": f"{name}-{suffix}", "split": split, "primitives": [name] * count,
                        "scale": scale, "offset": offset, "frame": FRAME, "dpi": DPI}
            samples.append({**exercise, "raw": render_exercise(target, exercise)})
    return initial, target, samples


class RenderBudget:
    def __init__(self, maximum, seconds):
        if isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= 5000:
            raise ValueError("Render budget must be 1..5000")
        if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 0 < seconds <= 1800:
            raise ValueError("Time budget must be within 1800 seconds")
        self.maximum, self.seconds = maximum, seconds
        self.started, self.used = time.monotonic(), 0

    def render(self, model, sample):
        if self.used >= self.maximum or time.monotonic() - self.started >= self.seconds:
            raise StopIteration
        self.used += 1
        return render_exercise(model, sample)


def fit_primitives(initial, samples, *, seed=7, max_evaluations=5000, seconds=1800):
    validate_language(initial)
    budget = RenderBudget(max_evaluations, seconds)
    if not samples or len({row["id"] for row in samples}) != len(samples):
        raise ValueError("Unique nonempty exercise set required")
    if any(row["split"] not in {"train", "development", "test"} for row in samples):
        raise ValueError("Unknown exercise split")
    training = [row for row in samples if row["split"] == "train"]
    development = [row for row in samples if row["split"] == "development"]
    if not training or not development:
        raise ValueError("Separate training/development exercises required")
    families = sorted({name for row in training for name in row["primitives"]})
    if any(not any(name in row["primitives"] for row in development) for name in families):
        raise ValueError("Each fitted family requires development support")
    candidate = copy.deepcopy(initial)
    rng, ledger = random.Random(seed), []
    before, after = {}, {}
    def score(model, rows):
        return float(np.mean([stroke_loss(row["raw"], budget.render(model, row), row.get("mask")) for row in rows]))
    status, stop = "complete", "bounded coordinate sweeps completed"
    try:
        for sample in training + development:
            before[sample["id"]] = score(initial, [sample])
        for name in families:
            train_rows = [row for row in training if name in row["primitives"]]
            dev_rows = [row for row in development if name in row["primitives"]]
            best = copy.deepcopy(candidate)
            best_development = score(best, dev_rows)
            train_loss = score(candidate, train_rows)
            coordinates = [(cubic, point, axis) for cubic in range(len(candidate["primitives"][name]["cubics"]))
                           for point in (1, 2) for axis in (0, 1)]
            for step in (.16, .08, .04, .02, .01):
                rng.shuffle(coordinates)
                for cubic, point, axis in coordinates:
                    winner, winner_loss = None, train_loss
                    for direction in (-1, 1):
                        proposed = copy.deepcopy(candidate)
                        proposed["primitives"][name]["cubics"][cubic][point][axis] += direction * step
                        if abs(proposed["primitives"][name]["cubics"][cubic][point][axis]
                               - initial["primitives"][name]["cubics"][cubic][point][axis]) > .65:
                            continue
                        try:
                            validate_language(proposed)
                        except ValueError:
                            continue
                        loss = score(proposed, train_rows)
                        if loss < winner_loss:
                            winner, winner_loss = proposed, loss
                    if winner is not None:
                        candidate, train_loss = winner, winner_loss
                        ledger.append({"primitive": name, "coordinate": [cubic, point, axis], "step": step,
                                       "train_loss": train_loss, "model_sha256": object_digest(candidate)})
                dev_loss = score(candidate, dev_rows)
                if dev_loss < best_development:
                    best, best_development = copy.deepcopy(candidate), dev_loss
            candidate = best
        for sample in samples:
            if sample["split"] == "test":
                before[sample["id"]] = score(initial, [sample])
            after[sample["id"]] = score(candidate, [sample])
    except StopIteration:
        status, stop = "blocked", "render/time budget exhausted; no accepted checkpoint"
    metrics = {}
    for split in ("train", "development", "test"):
        selected = [row for row in samples if row["split"] == split]
        if selected and all(row["id"] in before and row["id"] in after for row in selected):
            metrics[split] = {"before": float(np.mean([before[row["id"]] for row in selected])),
                              "after": float(np.mean([after[row["id"]] for row in selected]))}
    return {"status": status, "stop_reason": stop, "model": candidate, "model_sha256": object_digest(candidate),
            "seed": seed, "evaluations": budget.used, "selection_split": "development", "ledger": ledger,
            "metrics": metrics, "per_exercise": {identifier: {"before": loss, "after": after.get(identifier)} for identifier, loss in before.items()},
            "runtime_seconds": time.monotonic() - budget.started, "promoted": False}


def _font(size):
    for path in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def practice_sheet(output, initial, target, learned, samples):
    names = sorted({name for sample in samples for name in sample["primitives"]})
    panel = Image.new("RGB", (1440, 160 + 210 * len(names)), "#faf8f1")
    draw = ImageDraw.Draw(panel)
    draw.text((30, 20), "STROKE PRACTICE  /  shared primitive learning", font=_font(30), fill="#24302e")
    draw.text((30, 64), "Synthetic targets - actual fitted geometry - not recovered Konrad handwriting", font=_font(19), fill="#59655d")
    headers = ["Primitive", "Starting shape", "Synthetic target", "Learned nominal", "Actual neutral pen"]
    for horizontal, title in zip((30, 220, 520, 820, 1120), headers):
        draw.text((horizontal, 110), title, font=_font(18), fill="#24302e")
    actual_records = {}
    for index, name in enumerate(names):
        top = 155 + index * 210
        sample = next(row for row in samples if row["id"] == f"{name}-base")
        candidate, text = exercise_model(learned, sample)
        actual = execute_language(text, candidate, dpi=240)
        actual_records[name] = {key: value for key, value in actual.items() if key != "images"}
        draw.text((30, top + 65), name.upper(), font=_font(22), fill="#24302e")
        images = [render_exercise(model, sample, dpi=240) for model in (initial, target, learned)]
        from scribesim.handvalidate.bridge import paint_trajectory
        from scribesim.handflow.model import TrajectorySample

        images.append(paint_trajectory(tuple(TrajectorySample(**row) for row in actual["trajectory"]), FRAME, dpi=240))
        for column, pixels in enumerate(images):
            image = Image.fromarray(pixels)
            image.thumbnail((252, 180), Image.Resampling.LANCZOS)
            panel.paste(image, (210 + column * 300 + (252 - image.width) // 2, top + (180 - image.height) // 2))
        draw.line((25, top + 196, 1405, top + 196), fill="#dddcd4")
    panel.save(output / "practice-sheet.png")
    (output / "actual-traces.json.gz").write_bytes(gzip.compress(json.dumps(actual_records, sort_keys=True).encode(), mtime=0))
    return {name: row["metrics"] for name, row in actual_records.items()}


def _reference_samples(dataset, root, assignments, model):
    if assignments.get("dataset_sha256") != object_digest(dataset) or assignments.get("model_sha256") != object_digest(model):
        raise ValueError("Native exercise assignments require matching model/dataset identities")
    samples = []
    by_id = {row["id"]: row for row in dataset["samples"]}
    for assignment in assignments["entries"]:
        source = by_id[assignment["sample_id"]]
        if source["split"] == "test" or source["admission"] != "auto_admitted":
            raise ValueError("Reference training cannot consume test/quarantined observations")
        plan = compile_text(source["text"], model)
        frame = assignment["frame_mm"]
        dpi = source["xheight_native_px"] / model["x_height_mm"] * 25.4
        exercise = {"id": source["id"], "kind": "word", "text": source["text"], "split": source["split"],
                    "primitives": sorted({row["primitive"] for row in plan["strokes"]}), "frame": frame, "dpi": dpi,
                    "raw": np.asarray(Image.open(root / source["raw_path"]).convert("RGB")),
                    "mask": np.asarray(Image.open(root / source["mask_path"]))}
        if len(frame) != 4 or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in frame):
            raise ValueError("Native physical frame required")
        if render_exercise(model, exercise).shape != exercise["raw"].shape:
            raise ValueError("Assignment frame must preserve native image dimensions")
        samples.append(exercise)
    return samples


def _freeze_samples(samples):
    return [{**{key: value for key, value in sample.items() if key not in {"raw", "mask"}},
             "raw_sha256": hashlib.sha256(sample["raw"].tobytes()).hexdigest()} for sample in samples]


def _worker(output, *, seed, evaluations):
    initial, target, samples = synthetic_exercises()
    result = fit_primitives(initial, samples, seed=seed, max_evaluations=evaluations)
    result.pop("runtime_seconds")
    write_json(Path(output), result)


def run_stroke_learning(output, *, dataset_root=None, model=None, assignments=None, target_review=None, evaluations=5000):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty stroke-learning directory")
    output.mkdir(parents=True, exist_ok=True)
    if dataset_root is not None:
        root = Path(dataset_root)
        dataset = json.loads((root / "manifest.json").read_text())
        benchmark = ROOT / "shared/training/konrad_hand_recovery/benchmark_v1"
        gate = evaluate_benchmark(dataset["contract"], json.loads((benchmark / "baseline_manifest.json").read_text()),
                                  benchmark, dataset=dataset, dataset_root=root, review=target_review)
        write_json(output / "G0.json", gate)
        if gate["status"] != "pass" or model is None or assignments is None:
            report = {"status": "blocked", "scope": "real-reference", "evaluations": 0, "promoted": False,
                      "reasons": gate["reasons"] + ([] if model is not None and assignments is not None else ["shared-model/native-exercise-assignments missing"])}
            write_json(output / "report.json", report)
            return report
        samples = _reference_samples(dataset, root, assignments, model)
        write_json(output / "freeze.json", {"scope": "real-reference", "initial": model, "samples": _freeze_samples(samples),
                                            "dataset_sha256": object_digest(dataset), "assignments": assignments,
                                            "seeds": SEEDS, "max_evaluations": evaluations, "limits": LIMITS})
        results = [fit_primitives(model, samples, seed=seed, max_evaluations=evaluations) for seed in SEEDS]
        for result in results:
            write_json(output / f"seed-{result['seed']}.json", result)
        report = {"status": "blocked", "scope": "real-reference", "promoted": False,
                  "evaluations": sum(result["evaluations"] for result in results),
                  "reasons": ["real-source stage review and held-out transfer required before acceptance"]}
        write_json(output / "report.json", report)
        return report
    initial, target, samples = synthetic_exercises()
    freeze = {"scope": "synthetic-known-strokes-not-Konrad", "initial": initial, "target": target,
              "samples": _freeze_samples(samples), "seeds": SEEDS, "max_evaluations": evaluations,
              "max_seconds_per_seed": 1800, "ablations": ["frozen-prior", "learned-shared-primitives"],
              "environment": {"python": sys.version, "numpy": np.__version__, "pillow": Image.__version__},
              "limits": LIMITS, "code_sha256": {str(path.relative_to(ROOT)): digest(path) for path in
                  (Path(__file__), *(ROOT / relative for relative in (
                      "scribesim/evofit/stroke_language.py", "scribesim/handflow/controller.py", "scribesim/handflow/planning.py",
                      "scribesim/handflow/model.py", "scribesim/handflow/controls.py", "scribesim/pathguide/repertoire.py",
                      "scribesim/handvalidate/bridge.py", "scribesim/evofit/recovery.py", "scribesim/evo/renderer.py",
                      "scribesim/evo/genome.py", "scribesim/hand/profile.py")))}}
    write_json(output / "freeze.json", freeze)
    for seed in SEEDS:
        for label, hash_seed in (("first", "7"), ("replay", "839")):
            subprocess.run([sys.executable, "-m", "scribesim.curriculum.stroke_learning", "worker", "--output",
                            str(output / f"{seed}-{label}.json"), "--seed", str(seed), "--evaluations", str(evaluations)],
                           check=True, env={**os.environ, "PYTHONHASHSEED": hash_seed})
    results = [json.loads((output / f"{seed}-first.json").read_text()) for seed in SEEDS]
    complete = [result for result in results if result["status"] == "complete"]
    chosen = min(complete, key=lambda result: result["metrics"]["development"]["after"]) if complete else results[0]
    write_json(output / "candidate.json", chosen["model"])
    actual = practice_sheet(output, initial, target, chosen["model"], samples)
    for name, model_state in (("initial", initial), ("target", target), ("learned", chosen["model"])):
        Image.fromarray(render_language("i u ii ui", model_state, dpi=240)).save(output / f"transfer-{name}.png")
    report = {"freeze_sha256": object_digest(freeze), "scope": freeze["scope"], "selected_seed": chosen["seed"],
              "selection_split": "development", "rows": [{key: result[key] for key in ("seed", "status", "evaluations", "metrics", "model_sha256")} for result in results],
              "actual": actual, "promoted": False,
              "replay": all((output / f"{seed}-first.json").read_bytes() == (output / f"{seed}-replay.json").read_bytes() for seed in SEEDS)}
    report["artifacts"] = {path.name: digest(path) for path in output.iterdir() if path.is_file() and path.name != "freeze.json"}
    write_json(output / "report.json", report)
    decision = evaluate_learning(output, replay=False)
    write_json(output / "S1.json", decision)
    return decision


def evaluate_learning(output, *, replay=True):
    output = Path(output)
    try:
        freeze = json.loads((output / "freeze.json").read_text())
        report = json.loads((output / "report.json").read_text())
        if freeze["scope"] != "synthetic-known-strokes-not-Konrad" or report["freeze_sha256"] != object_digest(freeze):
            raise ValueError("Unfrozen or non-synthetic evaluation bundle")
        if freeze["limits"] != LIMITS or freeze["seeds"] != SEEDS:
            raise ValueError("Changed evaluation contract")
        for relative, checksum in freeze["code_sha256"].items():
            if digest(ROOT / relative) != checksum:
                raise ValueError("Evaluation code identity changed")
        for relative, checksum in report["artifacts"].items():
            path = (output / relative).resolve()
            if not path.is_relative_to(output.resolve()) or digest(path) != checksum:
                raise ValueError("Learning artifact identity mismatch")
        initial, target, samples = synthetic_exercises()
        if object_digest(initial) != object_digest(freeze["initial"]) or object_digest(target) != object_digest(freeze["target"]) or _freeze_samples(samples) != freeze["samples"]:
            raise ValueError("Frozen targets/exercises changed")
        failures = []
        results = []
        for seed in SEEDS:
            saved = json.loads((output / f"{seed}-first.json").read_text())
            results.append(saved)
            if replay:
                repeated = fit_primitives(initial, samples, seed=seed, max_evaluations=freeze["max_evaluations"])
                repeated.pop("runtime_seconds")
                if repeated != saved:
                    failures.append(f"seed-{seed}:replay")
            if (output / f"{seed}-first.json").read_bytes() != (output / f"{seed}-replay.json").read_bytes():
                failures.append(f"seed-{seed}:fresh-process-replay")
            if saved["status"] != "complete" or "test" not in saved["metrics"]:
                failures.append(f"seed-{seed}:incomplete")
            elif saved["metrics"]["test"]["after"] >= saved["metrics"]["test"]["before"] * LIMITS["heldout_improvement_ratio"]:
                failures.append(f"seed-{seed}:transfer")
            if object_digest(saved["model"]["recipes"]) != object_digest(initial["recipes"]) or saved["model_sha256"] != object_digest(saved["model"]):
                failures.append(f"seed-{seed}:shared-checkpoint")
            for name in initial["primitives"]:
                change = sum(math.dist(first, second)
                             for first_cubic, second_cubic in zip(initial["primitives"][name]["cubics"], saved["model"]["primitives"][name]["cubics"])
                             for first, second in zip(first_cubic, second_cubic))
                if change < LIMITS["minimum_parameter_change"]:
                    failures.append(f"seed-{seed}:{name}:inactive-learning")
        expected_rows = [{key: result[key] for key in ("seed", "status", "evaluations", "metrics", "model_sha256")} for result in results]
        if report["rows"] != expected_rows:
            raise ValueError("Summary differs from actual training records")
        complete = [result for result in results if result["status"] == "complete"]
        selected = min(complete, key=lambda result: result["metrics"]["development"]["after"]) if complete else results[0]
        candidate = json.loads((output / "candidate.json").read_text())
        if report["selected_seed"] != selected["seed"] or object_digest(candidate) != object_digest(selected["model"]):
            raise ValueError("Candidate is not the frozen development-selected checkpoint")
        if set(report["actual"]) != set(initial["primitives"]):
            raise ValueError("Missing actual primitive evidence")
        if replay:
            traces = json.loads(gzip.decompress((output / "actual-traces.json.gz").read_bytes()))
            for name in initial["primitives"]:
                exercise = next(row for row in samples if row["id"] == f"{name}-base")
                candidate_exercise, text = exercise_model(candidate, exercise)
                actual = execute_language(text, candidate_exercise, dpi=240)
                expected = {key: value for key, value in actual.items() if key != "images"}
                if object_digest(traces[name]) != object_digest(expected) or report["actual"][name] != actual["metrics"]:
                    raise ValueError("Actual trace/ownership/metric replay mismatch")
            for name, state in (("initial", initial), ("target", target), ("learned", candidate)):
                if not np.array_equal(np.asarray(Image.open(output / f"transfer-{name}.png")), render_language("i u ii ui", state, dpi=240)):
                    raise ValueError("Transfer pixels differ from shared checkpoint")
        for name, metrics in report["actual"].items():
            if metrics["image_loss"] > LIMITS["actual_image_loss"] or metrics["corridor_error_mm"] > LIMITS["corridor_error_mm"] or not metrics["contact_schedule_preserved"]:
                failures.append(f"{name}:neutral-execution")
        return {"gate": "S1", "status": "fail" if failures else "pass", "scope": freeze["scope"],
                "reasons": failures, "promoted": False, "real_hand_status": "blocked; G0 and real-source review missing",
                "freeze_sha256": object_digest(freeze), "report_sha256": object_digest(report)}
    except (OSError, KeyError, TypeError) as error:
        raise ValueError("Incomplete learning evidence") from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "evaluate", "worker"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--evaluations", type=int, default=5000)
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--assignments", type=Path)
    parser.add_argument("--target-review", type=Path)
    args = parser.parse_args()
    read = lambda path: json.loads(path.read_text()) if path else None
    if args.command == "worker":
        _worker(args.output, seed=args.seed, evaluations=args.evaluations)
    elif args.command == "evaluate":
        print(json.dumps(evaluate_learning(args.output), indent=2))
    else:
        print(json.dumps(run_stroke_learning(args.output, dataset_root=args.dataset_root, evaluations=args.evaluations,
                                             model=read(args.model), assignments=read(args.assignments), target_review=read(args.target_review)), indent=2))


if __name__ == "__main__":
    main()
