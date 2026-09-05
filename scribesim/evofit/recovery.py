"""Bounded nominal inverse graphics, with train-only proposals and locked-test isolation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import random
import time
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from scribesim.evofit.repertoire import (
    compose, refresh_form, render_key, render_nominal, seed_repertoire, validate_repertoire,
)
from scribesim.handvalidate.specimen import digest, object_digest, write_json, write_equal_scale_panel


OBJECTIVE = {"version": "masked-native-multiscale-v1", "ink": .5, "contour": .2,
             "spacing": .15, "counters": .1, "mass": .05, "complexity": .001,
             "translation_px": 2, "isotropic_scales": [.95, 1.0, 1.05],
             "note": "Engineering synthetic-tested weights; real-source calibration remains required"}


class Budget:
    def __init__(self, evaluations=5000, seconds=1800, *, clock=time.monotonic):
        if not isinstance(evaluations, int) or not 1 <= evaluations <= 5000 or not 0 < seconds <= 1800:
            raise ValueError("Budget exceeds 5000 word renders or 30 minutes")
        self.maximum = evaluations
        self.seconds = seconds
        self.clock = clock
        self.started = clock()
        self.evaluations = 0

    def consume(self):
        if self.clock() - self.started >= self.seconds:
            raise StopIteration("wall_time")
        if self.evaluations >= self.maximum:
            raise StopIteration("evaluation_budget")
        self.evaluations += 1


class RenderCache:
    def __init__(self):
        self.entries = {}

    def render(self, text, hand, *, dpi=100):
        key = render_key(text, hand, dpi=dpi)
        if key not in self.entries:
            rendered = render_nominal(text, hand, dpi=dpi).copy()
            self.entries[key] = (rendered, hashlib.sha256(rendered.tobytes()).hexdigest())
        rendered, checksum = self.entries[key]
        if hashlib.sha256(rendered.tobytes()).hexdigest() != checksum:
            raise ValueError("Corrupt render cache entry")
        return rendered.copy()


def _gray(image):
    return np.asarray(Image.fromarray(np.asarray(image).astype(np.uint8)).convert("L"))


def _components(binary):
    unseen = set(zip(*np.nonzero(binary)))
    groups = []
    while unseen:
        pending = [min(unseen)]
        unseen.remove(pending[0])
        group = []
        while pending:
            row, column = pending.pop()
            group.append((int(row), int(column)))
            for neighbor in ((row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    pending.append(neighbor)
        groups.append(group)
    return groups


def _holes(ink, known):
    height, width = ink.shape
    return [group for group in _components(~ink) if len(group) >= 3 and all(
        row not in (0, height - 1) and column not in (0, width - 1) and known[row, column]
        for row, column in group)]


def _dilate(binary, radius=1):
    return np.asarray(Image.fromarray(binary.astype(np.uint8) * 255).filter(
        ImageFilter.MaxFilter(2 * radius + 1))) > 0


def image_objective(raw, mask, rendered) -> dict:
    target = _gray(raw)
    prediction = _gray(rendered)
    if target.shape != mask.shape or prediction.shape != mask.shape or not set(np.unique(mask)) <= {0, 128, 255}:
        raise ValueError("Objective needs aligned native pixels and three-state mask")
    known = mask != 128
    ink = (mask == 255) & (target < 210)
    predicted = (prediction < 180) & known
    if not ink.any():
        raise ValueError("No known target ink")
    losses = []
    for radius in (0, 1, 2):
        expected_scale = _dilate(ink, radius) if radius else ink
        predicted_scale = _dilate(predicted, radius) if radius else predicted
        valid = ~_dilate(~known, radius) if radius else known
        union = np.count_nonzero((expected_scale | predicted_scale) & valid)
        intersection = np.count_nonzero(expected_scale & predicted_scale & valid)
        losses.append(1 - intersection / max(1, union))
    contour = float(np.count_nonzero((ink & ~_dilate(predicted)) | (predicted & ~_dilate(ink)))
                    / max(1, np.count_nonzero(ink | predicted)))
    projections = sum(float(np.abs(ink.sum(axis=axis) - predicted.sum(axis=axis)).sum())
                      / max(1, float(ink.sum() + predicted.sum())) for axis in (0, 1)) / 2
    holes = abs(len(_holes(ink, known)) - len(_holes(predicted, known)))
    terms = {"ink": float(np.mean(losses)), "contour": contour, "spacing": projections,
             "counters": min(1, holes), "mass": abs(float(ink.sum() - predicted.sum())) / max(1, float(ink.sum() + predicted.sum()))}
    terms["total"] = sum(OBJECTIVE[name] * value for name, value in terms.items())
    return terms


def skeleton_graph(mask) -> dict:
    binary = mask == 255
    if binary.ndim != 2 or binary.size > 1_000_000:
        raise ValueError("Skeleton input exceeds native pixel budget")
    skeleton = np.pad(binary, 1)
    for iteration in range(128):
        changed = False
        for phase in (0, 1):
            neighbors = [np.roll(skeleton, shift, axis=(0, 1)) for shift in
                         ((1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1))]
            degree = sum(neighbor.astype(int) for neighbor in neighbors)
            crossings = sum((~neighbors[index] & neighbors[(index + 1) % 8]).astype(int) for index in range(8))
            first = (0, 2, 4) if phase == 0 else (0, 2, 6)
            second = (2, 4, 6) if phase == 0 else (0, 4, 6)
            remove = (skeleton & (degree >= 2) & (degree <= 6) & (crossings == 1)
                      & ~np.logical_and.reduce([neighbors[index] for index in first])
                      & ~np.logical_and.reduce([neighbors[index] for index in second]))
            changed |= bool(remove.any())
            skeleton[remove] = False
        if not changed:
            break
    vertices = set(zip(*np.nonzero(skeleton[1:-1, 1:-1])))
    adjacency = {}
    for row, column in vertices:
        adjacency[row, column] = sorted((row + vertical, column + horizontal)
            for vertical in (-1, 0, 1) for horizontal in (-1, 0, 1)
            if (vertical or horizontal) and (row + vertical, column + horizontal) in vertices
            and not (vertical and horizontal and ((row + vertical, column) in vertices or (row, column + horizontal) in vertices)))
    edges = {tuple(sorted((vertex, neighbor))) for vertex in vertices for neighbor in adjacency[vertex]}
    chains = []
    starts = sorted(vertices, key=lambda vertex: (len(adjacency[vertex]) == 2, vertex))
    for start in starts:
        for neighbor in adjacency[start]:
            edge = tuple(sorted((start, neighbor)))
            if edge not in edges:
                continue
            edges.remove(edge)
            chain = [start, neighbor]
            while len(adjacency[chain[-1]]) == 2 and chain[-1] != start:
                following = next(vertex for vertex in adjacency[chain[-1]] if vertex != chain[-2])
                edge = tuple(sorted((chain[-1], following)))
                if edge not in edges:
                    break
                edges.remove(edge)
                chain.append(following)
            if len(chain) >= 3:
                chains.append({"points": [[int(column), int(row)] for row, column in chain],
                               "closed": chain[0] == chain[-1]})
    return {"status": "hypothesis-not-ductus", "chains": chains[:32], "limit_hit": len(chains) > 32,
            "thinning_limit_hit": iteration == 127, "holes": len(_holes(binary, mask != 128))}


def alignment_lattice(text, mask, *, beam=32):
    if not text or any(character.isspace() for character in text) or not 1 <= beam <= 32:
        raise ValueError("Invalid alignment text/beam")
    width = mask.shape[1]
    if width < len(text):
        return []
    pitch = width / len(text)
    states = [{"cuts": [0], "cost": 0.0}]
    projection = (mask == 255).sum(axis=0) / max(1, mask.shape[0])
    for position in range(1, len(text)):
        candidates = []
        for state in states:
            lower = max(state["cuts"][-1] + 1, round((position - .5) * pitch))
            upper = min(width - (len(text) - position), round((position + .5) * pitch))
            stride = max(1, (upper - lower) // 32)
            for cut in range(lower, upper + 1, stride):
                cost = state["cost"] + float(projection[cut]) + .1 * abs(cut - position * pitch) / pitch
                candidates.append({"cuts": state["cuts"] + [cut], "cost": cost})
        states = sorted(candidates, key=lambda row: (row["cost"], row["cuts"]))[:beam]
    return [{**state, "cuts": state["cuts"] + [width]} for state in states]


def _ellipse(left=0.0, bottom=0.0, width=1.0, height=1.0):
    horizontal, vertical = width / 2, height / 2
    center = left + horizontal, bottom + vertical
    factor = .5522847498
    points = [((1, 0), (1, factor), (factor, 1), (0, 1)),
              ((0, 1), (-factor, 1), (-1, factor), (-1, 0)),
              ((-1, 0), (-1, -factor), (-factor, -1), (0, -1)),
              ((0, -1), (factor, -1), (1, -factor), (1, 0))]
    return {"cubics": [[[center[0] + point[0] * horizontal, center[1] + point[1] * vertical]
                        for point in cubic] for cubic in points]}


def structural_proposals(hand, samples):
    proposals = []
    for sample in samples:
        if sample["split"] != "train":
            continue
        text, mask = sample["text"], sample["mask"]
        lattice = alignment_lattice(text, mask)
        for alignment_rank, alignment in enumerate(lattice[:3]):
            for position, character in enumerate(text):
                forms = [(form_id, form) for form_id, form in sorted(hand["forms"].items()) if form["logical"] == character]
                if not forms:
                    continue
                form_id, prior = forms[0]
                left, right = alignment["cuts"][position:position + 2]
                cropped = mask[:, left:right]
                graph = skeleton_graph(cropped)
                provenance = {"sample_id": sample["id"], "split": "train", "alignment_rank": alignment_rank,
                              "cuts": alignment["cuts"], "cost": alignment["cost"], "graph_hypothesis": True}
                chains = []
                ink_rows, ink_columns = np.nonzero(cropped == 255)
                if not len(ink_rows):
                    continue
                xheight = sample["xheight_px"]
                for chain in graph["chains"][:8]:
                    raw_points = chain["points"]
                    selected = sorted(set(np.linspace(0, len(raw_points) - 1, min(5, len(raw_points))).astype(int)))
                    points = [[(raw_points[index][0] - float(ink_columns.min())) / xheight,
                               (float(ink_rows.max()) - raw_points[index][1]) / xheight] for index in selected]
                    chains.append({"cubics": [[start, start, end, end] for start, end in zip(points, points[1:])]})
                alternatives = [("skeleton-chain", chains)] if chains else []
                if graph["holes"]:
                    width = max(.15, (float(ink_columns.max() - ink_columns.min())) / xheight - hand["nib_width_mm"] / hand["x_height_mm"] * .7)
                    height = max(.15, (float(ink_rows.max() - ink_rows.min())) / xheight - hand["nib_width_mm"] / hand["x_height_mm"] * .7)
                    alternatives.append(("counter-loop", [_ellipse(width=width, height=height)]))
                for kind, proposed_chains in alternatives:
                    form = copy.deepcopy(prior)
                    form["chains"] = proposed_chains
                    form["provenance"] = {"kind": kind, "observation": provenance, "historical_ductus": "unknown"}
                    refresh_form(form)
                    candidate = copy.deepcopy(hand)
                    candidate["forms"][form_id] = form
                    try:
                        validate_repertoire(candidate)
                    except ValueError:
                        continue
                    proposals.append({"form_id": form_id, "form": form, "kind": kind, "provenance": [provenance]})
    return proposals


def _place(rendered, shape, alignment):
    image = Image.fromarray(rendered).convert("L")
    image = image.resize((max(1, round(image.width * alignment["scale"])),
                          max(1, round(image.height * alignment["scale"]))), Image.Resampling.LANCZOS)
    canvas = Image.new("L", (shape[1], shape[0]), 255)
    canvas.paste(image, (alignment["left"], alignment["top"]))
    return np.asarray(canvas)


def _split_cubic(cubic):
    points = np.asarray(cubic, dtype=float)
    first = (points[:-1] + points[1:]) / 2
    second = (first[:-1] + first[1:]) / 2
    center = (second[0] + second[1]) / 2
    return [[points[0].tolist(), first[0].tolist(), second[0].tolist(), center.tolist()],
            [center.tolist(), second[1].tolist(), first[2].tolist(), points[3].tolist()]]


def _mutate(hand, initial, rng, mode, step, proposals):
    candidate = copy.deepcopy(hand)
    if mode != "fixed" and proposals and step % 3 == 0:
        proposal = proposals[(step // 3) % len(proposals)]
        candidate["forms"][proposal["form_id"]] = copy.deepcopy(proposal["form"])
        return candidate, proposal["kind"]
    form_id = rng.choice(sorted(candidate["forms"]))
    form = candidate["forms"][form_id]
    if mode == "context" and step % 3 == 2:
        position = rng.choice(["initial", "medial", "final"])
        rule = {"form_id": form_id, "position": position, "previous": None, "next": None, "cost": -1.0}
        candidate["rules"] = [row for row in candidate["rules"] if not (row["position"] == position and
                              candidate["forms"][row["form_id"]]["logical"] == form["logical"])] + [rule]
        return candidate, "context-assignment"
    operation = rng.choice(["geometry", "advance", "nib", "spacing"] +
                           (["split", "merge", "short-branch", "lift", "join"] if mode != "fixed" else []))
    chain = rng.choice(form["chains"])
    cubic_index = rng.randrange(len(chain["cubics"]))
    if operation == "split":
        chain["cubics"][cubic_index:cubic_index + 1] = _split_cubic(chain["cubics"][cubic_index])
    elif operation == "merge" and len(chain["cubics"]) > 1:
        first, second = chain["cubics"][:2]
        chain["cubics"][:2] = [[first[0], first[1], second[2], second[3]]]
    elif operation == "short-branch":
        start = chain["cubics"][cubic_index][-1]
        end = [start[0] + rng.uniform(-.2, .2), start[1] + rng.uniform(-.2, .2)]
        form["chains"].append({"cubics": [[start[:], start[:], end[:], end[:]]]})
    elif operation == "lift" and len(chain["cubics"]) > 1:
        remainder = chain["cubics"][1:]
        chain["cubics"] = chain["cubics"][:1]
        form["chains"].append({"cubics": remainder})
    elif operation == "join" and mode == "context":
        right = rng.choice(sorted(candidate["forms"]))
        candidate["joins"] = [row for row in candidate["joins"] if (row["left"], row["right"]) != (form_id, right)]
        candidate["joins"].append({"left": form_id, "right": right, "kind": rng.choice(["air", "contact"]), "cost": -.1})
    elif operation == "advance":
        origin = initial["forms"][form_id]["advance"]
        form["advance"] = max(.05, min(origin * 1.3, max(origin * .7, form["advance"] + rng.uniform(-.04, .04))))
    elif operation == "nib":
        candidate["nib_width_mm"] = max(initial["nib_width_mm"] * .7, min(initial["nib_width_mm"] * 1.3,
                                    candidate["nib_width_mm"] + rng.uniform(-.04, .04)))
        candidate["nib_angle_deg"] = max(initial["nib_angle_deg"] - 10, min(initial["nib_angle_deg"] + 10,
                                     candidate["nib_angle_deg"] + rng.uniform(-2, 2)))
    elif operation == "spacing":
        candidate["letter_gap"] = max(0, min(.2, candidate["letter_gap"] + rng.uniform(-.02, .02)))
    else:
        cubic = chain["cubics"][cubic_index]
        point_index = rng.choice([1, 2])
        axis = rng.randrange(2)
        cubic[point_index][axis] = max(-3.9, min(3.9, cubic[point_index][axis] + rng.uniform(-.08, .08)))
    refresh_form(form)
    return candidate, operation


def fit_repertoire(samples, initial, *, seed=1, mode="context", max_evaluations=5000, seconds=1800, dpi=100):
    budget = Budget(max_evaluations, seconds)
    try:
        return _fit_repertoire(samples, initial, budget, seed=seed, mode=mode,
                               max_evaluations=max_evaluations, seconds=seconds, dpi=dpi)
    except StopIteration as error:
        return {"schema_version": 1, "status": "unresolved_initialization", "promoted": False,
                "model": None, "model_sha256": None, "mode": mode, "seed": seed,
                "development_loss": None, "trace": [], "evaluations": budget.evaluations,
                "runtime_seconds": budget.clock() - budget.started, "stop_reason": str(error)}


def _fit_repertoire(samples, initial, budget, *, seed, mode, max_evaluations, seconds, dpi):
    started = time.monotonic()
    if mode not in {"fixed", "structural", "context"}:
        raise ValueError("Unknown ablation")
    training = [sample for sample in samples if sample["split"] == "train"]
    development = [sample for sample in samples if sample["split"] == "development"]
    if not training or not development:
        raise ValueError("Nonempty training and development observations required")
    observations = training + development
    if len({sample["id"] for sample in observations}) != len(observations):
        raise ValueError("Duplicate train/development observation IDs")
    if max_evaluations < 2 * len(observations):
        raise ValueError("Budget cannot score the initial and one candidate checkpoint")
    for sample in observations:
        compose(sample["text"], initial)
        if sample["xheight_px"] <= 0:
            raise ValueError("Native x-height required")
    rng = random.Random(seed)
    alignments, initial_images = {}, {}
    for sample in observations:
        budget.consume()
        rendered = render_nominal(sample["text"], initial, dpi=dpi)
        initial_images[sample["id"]] = rendered
        nominal_scale = sample["xheight_px"] / (initial["x_height_mm"] * dpi / 25.4)
        candidates = []
        for multiplier in OBJECTIVE["isotropic_scales"]:
            scale = nominal_scale * multiplier
            center_left = round((sample["mask"].shape[1] - rendered.shape[1] * nominal_scale) / 2)
            center_top = round((sample["mask"].shape[0] - rendered.shape[0] * nominal_scale) / 2)
            for vertical in (-2, 0, 2):
                for horizontal in (-2, 0, 2):
                    alignment = {"scale": scale, "left": center_left + horizontal, "top": center_top + vertical}
                    loss = image_objective(sample["raw"], sample["mask"], _place(rendered, sample["mask"].shape, alignment))["total"]
                    candidates.append((loss, alignment))
        alignments[sample["id"]] = min(candidates, key=lambda row: row[0])[1]
    proposals = structural_proposals(initial, training) if mode != "fixed" else []
    current = copy.deepcopy(initial)
    current["acceptance"] = "candidate"
    selected = copy.deepcopy(current)
    trace = []
    best_train, best_dev = math.inf, math.inf
    selected_terms = None
    rejected = Counter()
    stop_reason = "attempt_budget"
    for step in range(max_evaluations * 4):
        candidate, operation = (copy.deepcopy(current), "initial") if step == 0 else _mutate(current, initial, rng, mode, step - 1, proposals)
        try:
            validate_repertoire(candidate)
            for sample in observations:
                compose(sample["text"], candidate)
        except ValueError as error:
            rejected[str(error)] += 1
            continue
        terms = {"train": [], "development": []}
        try:
            for sample in observations:
                if step == 0:
                    rendered = initial_images[sample["id"]]
                else:
                    budget.consume()
                    rendered = render_nominal(sample["text"], candidate, dpi=dpi)
                losses = image_objective(sample["raw"], sample["mask"], _place(rendered, sample["mask"].shape, alignments[sample["id"]]))
                terms[sample["split"]].append({"id": sample["id"], **losses})
        except StopIteration as error:
            stop_reason = str(error)
            break
        except ValueError as error:
            rejected[str(error)] += 1
            continue
        complexity = OBJECTIVE["complexity"] * sum(len(chain["cubics"]) for form in candidate["forms"].values() for chain in form["chains"])
        train_loss = float(np.mean([row["total"] for row in terms["train"]])) + complexity
        dev_loss = float(np.mean([row["total"] for row in terms["development"]])) + complexity
        accepted = train_loss < best_train
        checkpoint = accepted and dev_loss < best_dev
        if accepted:
            current, best_train = candidate, train_loss
        if checkpoint:
            selected, best_dev, selected_terms = copy.deepcopy(candidate), dev_loss, terms
        trace.append({"step": step, "operation": operation, "model_sha256": object_digest(candidate),
                      "training_loss": train_loss, "development_loss": dev_loss, "complexity": complexity,
                      "accepted_on_training": accepted, "selected_on_development": checkpoint,
                      "evaluations": budget.evaluations, "components": terms})
    support = {character: {"instances": sum(character in sample["text"] for sample in training),
                           "contexts": len({sample["text"] for sample in training if character in sample["text"]})}
               for character in sorted(set("".join(sample["text"] for sample in training)))}
    return {"schema_version": 1, "status": "synthetic_or_unaccepted_candidate", "promoted": False,
            "seed": seed, "mode": mode, "model": selected, "model_sha256": object_digest(selected),
            "development_loss": best_dev, "selected_components": selected_terms, "support": support,
            "evaluations": budget.evaluations, "runtime_seconds": time.monotonic() - started,
            "stop_reason": stop_reason, "trace": trace, "rejected": dict(rejected), "alignments": alignments,
            "proposals": proposals, "objective": OBJECTIVE, "config": {"max_evaluations": max_evaluations,
            "seconds": seconds, "dpi": dpi, "seed": seed, "mode": mode, "beam": 32}}


def synthetic_case():
    seed = seed_repertoire("o", variants=False)
    form = seed["forms"]["o:catalog"]
    form["advance"] = 1.0
    form["chains"] = [{"cubics": [[[0, 1], [0, 1], [0, 0], [0, 0]],
                                    [[0, 0], [0, 0], [1, 0], [1, 0]],
                                    [[1, 0], [1, 0], [1, 1], [1, 1]]]}]
    form["provenance"] = {"kind": "synthetic-missing-loop-not-historical"}
    refresh_form(form)
    target = copy.deepcopy(seed)
    target["forms"]["o:catalog"]["chains"] = [_ellipse()]
    refresh_form(target["forms"]["o:catalog"])
    samples = []
    for index, (text, split) in enumerate((("o", "train"), ("oo", "train"), ("o", "development"))):
        raw = render_nominal(text, target)
        mask = np.where(_gray(raw) < 180, 255, 0).astype(np.uint8)
        samples.append({"id": f"synthetic-{index}", "text": text, "split": split, "raw": raw,
                        "mask": mask, "xheight_px": seed["x_height_mm"] * 100 / 25.4})
    return seed, samples


def run_recovery(output, *, dataset_root=None, benchmark_root=None, review=None, max_evaluations=5000, seconds=1800):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty run directory")
    Budget(max_evaluations, seconds)
    output.mkdir(parents=True, exist_ok=True)
    if dataset_root is not None:
        from scribesim.handvalidate.specimen import evaluate_benchmark
        dataset_root, benchmark_root = Path(dataset_root), Path(benchmark_root)
        dataset = json.loads((dataset_root / "manifest.json").read_text())
        contract = json.loads((benchmark_root / "contract.json").read_text())
        baseline = json.loads((benchmark_root / "baseline_manifest.json").read_text())
        gate = evaluate_benchmark(contract, baseline, benchmark_root, dataset=dataset, review=review, dataset_root=dataset_root)
        write_json(output / "G0.json", gate)
        if gate["status"] != "pass":
            report = {"status": "blocked", "reason": "G0 did not pass; no fitting or locked-test scoring performed",
                      "dataset_sha256": digest(dataset_root / "manifest.json"), "contract_sha256": object_digest(contract),
                      "code_sha256": digest(Path(__file__)),
                      "evaluations": 0, "promoted": False, "gate": gate}
            write_json(output / "report.json", report)
            return report
        samples = [{"id": sample["id"], "text": sample["text"], "split": sample["split"],
                    "raw": np.asarray(Image.open(dataset_root / sample["raw_path"])),
                    "mask": np.asarray(Image.open(dataset_root / sample["mask_path"])),
                    "xheight_px": sample["xheight_native_px"]} for sample in dataset["samples"]
                   if sample["split"] in {"train", "development"} and sample["admission"] == "auto_admitted"]
        hand = seed_repertoire("".join(sample["text"] for sample in samples if sample["split"] == "train"))
        scope = "unaccepted-real-corpus-candidate"
    else:
        hand, samples = synthetic_case()
        scope = "synthetic-known-loop-only-not-Konrad"
    write_json(output / "initial.json", hand)
    write_json(output / "config.json", {"objective": OBJECTIVE, "seeds": [7, 19, 41], "modes": ["fixed", "structural", "context"],
                                       "max_evaluations": max_evaluations, "seconds": seconds, "scope": scope})
    smoke = fit_repertoire(samples, hand, seed=7, mode="structural", max_evaluations=max(2 * len(samples), min(24, max_evaluations)), seconds=seconds)
    write_json(output / "smoke.json", smoke)
    runs = []
    for mode in ("fixed", "structural", "context"):
        for seed in (7, 19, 41):
            result = fit_repertoire(samples, hand, seed=seed, mode=mode, max_evaluations=max_evaluations, seconds=seconds)
            write_json(output / f"{mode}-{seed}.json", result)
            runs.append({key: result[key] for key in ("mode", "seed", "development_loss", "model_sha256", "evaluations", "runtime_seconds", "stop_reason")})
    completed = [result for result in runs if result["development_loss"] is not None]
    if not completed:
        report = {"status": "blocked", "reason": "All runs exhausted their initialization budget", "runs": runs, "promoted": False}
        write_json(output / "report.json", report)
        return report
    best = min(completed, key=lambda result: result["development_loss"])
    selected = json.loads((output / f'{best["mode"]}-{best["seed"]}.json').read_text())
    write_json(output / "selected.json", selected["model"])
    rows = []
    for sample in samples:
        for label, rendered in (("reference", sample["raw"]), ("seed", render_nominal(sample["text"], hand)),
                                ("candidate", render_nominal(sample["text"], selected["model"]))):
            rows.append((f'{scope}: {sample["split"]} {sample["text"]} / {label}', Image.fromarray(rendered), sample["xheight_px"]))
    write_equal_scale_panel(rows, output / "train-development.png")
    report = {"status": scope, "promoted": False, "runs": runs, "selected": best,
              "selection": "development only; locked test not scored", "objective_sha256": object_digest(OBJECTIVE),
              "code_sha256": digest(Path(__file__)), "config_sha256": digest(output / "config.json"),
              "initial_sha256": digest(output / "initial.json"),
              "dataset_sha256": digest(dataset_root / "manifest.json") if dataset_root is not None else None,
              "contract_sha256": object_digest(contract) if dataset_root is not None else None,
              "selected_sha256": digest(output / "selected.json")}
    write_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument("--benchmark-root", type=Path, default=Path("shared/training/konrad_hand_recovery/benchmark_v1"))
    parser.add_argument("--review", type=Path)
    parser.add_argument("--evaluations", type=int, default=5000)
    parser.add_argument("--seconds", type=float, default=1800)
    args = parser.parse_args()
    run_recovery(args.output, dataset_root=args.dataset_root, benchmark_root=args.benchmark_root,
                 review=json.loads(args.review.read_text()) if args.review else None,
                 max_evaluations=args.evaluations, seconds=args.seconds)


if __name__ == "__main__":
    main()
