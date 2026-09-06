"""Exact WordPlan to physical DensePathGuide conversion with mandatory attribution."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from scribesim.evo.genome import BezierSegment
from scribesim.evofit.repertoire import compose
from scribesim.handvalidate.specimen import object_digest, write_json
from scribesim.pathguide.model import DensePathGuide, GuideSample, GuideSource


@dataclass(frozen=True)
class RepertoireGuide:
    guide: DensePathGuide
    metadata: dict


def require_g1(nominal_root, *, dataset_root=None, benchmark_root=None, target_review=None, review=None):
    from scribesim.handvalidate.nominal import evaluate_nominal

    gate = evaluate_nominal(nominal_root, review, dataset_root=dataset_root,
                            benchmark_root=benchmark_root, target_review=target_review)
    if gate["status"] != "pass":
        raise ValueError(f'G1 prerequisite not passed: {gate["reasons"]}')
    root = Path(nominal_root)
    return json.loads((root / "candidate.json").read_text()), json.loads((root / "freeze.json").read_text())


def _sample_cubic(cubic, step_mm):
    segment = BezierSegment(*cubic)
    probe_count = max(128, math.ceil(sum(math.dist(left, right) for left, right in zip(cubic, cubic[1:])) / step_mm) * 8)
    if probe_count > 100000:
        raise ValueError("Arc-length sampling exceeds probe budget")
    parameters = np.linspace(0, 1, probe_count + 1)
    points = np.array([segment.evaluate(float(parameter)) for parameter in parameters])
    distance = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))))
    targets = np.linspace(0, distance[-1], max(2, math.ceil(distance[-1] / step_mm) + 1))
    selected = np.interp(targets, distance, parameters) if distance[-1] else [0.0, 1.0]
    samples = []
    for parameter in selected:
        tangent = segment.tangent(float(parameter))
        if math.hypot(*tangent) < 1e-12:
            tangent = segment.tangent(min(.999, max(.001, float(parameter))))
        norm = math.hypot(*tangent)
        tangent = (tangent[0] / norm, tangent[1] / norm) if norm else (1.0, 0.0)
        samples.append((*segment.evaluate(float(parameter)), *tangent))
    return samples


def convert_word(text, hand, *, step_mm=.05, baseline_y_mm=10.0, corridor_mm=.2):
    if not .005 <= step_mm <= .2 or not math.isfinite(baseline_y_mm) or not .01 <= corridor_mm <= 1:
        raise ValueError("Invalid physical sampling/corridor bounds")
    plan = compose(text, hand)
    scale = hand["x_height_mm"]
    samples, owners, control_points = [], [], []
    previous_key = None
    for occurrence_index, occurrence in enumerate(plan["occurrences"]):
        form = hand["forms"][occurrence["form_id"]]
        for chain_index, chain in enumerate(form["chains"]):
            key = [occurrence_index, chain_index]
            cubics = [[[(point[0] + occurrence["x"]) * scale, baseline_y_mm - point[1] * scale]
                        for point in cubic] for cubic in chain["cubics"]]
            control_points.extend(point for cubic in cubics for point in cubic)
            if previous_key is not None:
                transition = next(row for row in plan["transitions"] if row["from"] == previous_key and row["to"] == key)
                start = [samples[-1].x_mm, samples[-1].y_mm]
                end = cubics[0][0]
                contact = transition["kind"] == "contact"
                if contact and math.dist(start, end) > 1.5 * scale:
                    raise ValueError("Contact transition exceeds local join bound")
                spans = [plan["occurrences"][previous_key[0]]["span"], occurrence["span"]] if contact else []
                for horizontal, vertical, tangent_x, tangent_y in _sample_cubic([start, start, end, end], step_mm):
                    samples.append(GuideSample(horizontal, vertical, tangent_x, tangent_y, contact=contact,
                                               pressure_nominal=.5 if contact else 0, nib_angle_deg=hand["nib_angle_deg"],
                                               corridor_half_width_mm=corridor_mm))
                    owners.append({"kind": transition["kind"], "spans": spans, "from": previous_key, "to": key})
            for cubic_index, cubic in enumerate(cubics):
                for point_index, (horizontal, vertical, tangent_x, tangent_y) in enumerate(_sample_cubic(cubic, step_mm)):
                    if cubic_index and point_index == 0:
                        continue
                    samples.append(GuideSample(horizontal, vertical, tangent_x, tangent_y, pressure_nominal=.5,
                                               nib_angle_deg=hand["nib_angle_deg"], corridor_half_width_mm=corridor_mm))
                    owners.append({"kind": "form", "spans": [occurrence["span"]], "occurrence": occurrence_index,
                                   "form_id": occurrence["form_id"], "chain": chain_index, "cubic": cubic_index})
            previous_key = key
    if len(samples) > 100000:
        raise ValueError("Word guide exceeds 100000 sample budget")
    margin = hand["nib_width_mm"] + .5
    frame = [min(0, min(point[0] for point in control_points)) - margin,
             max(plan["width"] * scale, max(point[0] for point in control_points)) + margin,
             min(point[1] for point in control_points) - margin, max(point[1] for point in control_points) + margin]
    guide = DensePathGuide(text, tuple(samples), plan["width"] * scale, scale, kind="word",
                           entry_tangent=(samples[0].tangent_dx, samples[0].tangent_dy),
                           exit_tangent=(samples[-1].tangent_dx, samples[-1].tangent_dy),
                           sources=(GuideSource(object_digest(hand), confidence_tier="soft_accepted", split="unaccepted-conversion"),))
    metadata = {"schema_version": 1, "units": "millimetres-y-down", "baseline_y_mm": baseline_y_mm,
                "step_mm": step_mm, "corridor_mm": corridor_mm, "plan": plan, "owners": owners,
                "frame_mm": frame, "model_sha256": object_digest(hand), "guide_sha256": object_digest(asdict(guide)),
                "acceptance": "conversion-only; runtime gate is separate"}
    return RepertoireGuide(guide, metadata)


def save_bundle(bundle, path):
    if Path(path).exists():
        raise ValueError("Refusing to overwrite a guide bundle")
    write_json(Path(path), {"payload": asdict(bundle), "sha256": object_digest(asdict(bundle))})


def load_bundle(path):
    try:
        document = json.loads(Path(path).read_text())
        if set(document) != {"payload", "sha256"} or object_digest(document["payload"]) != document["sha256"]:
            raise ValueError("Guide bundle integrity mismatch")
        payload = document["payload"]
        if set(payload) != {"guide", "metadata"}:
            raise ValueError("Unknown required guide metadata")
        metadata = payload["metadata"]
        if set(metadata) != {"schema_version", "units", "baseline_y_mm", "step_mm", "corridor_mm", "plan", "owners", "frame_mm", "model_sha256", "guide_sha256", "acceptance"}:
            raise ValueError("Missing/unknown ownership metadata")
        raw = payload["guide"]
        guide = DensePathGuide(**{**raw, "samples": tuple(GuideSample(**row) for row in raw["samples"]),
                                 "sources": tuple(GuideSource(**row) for row in raw["sources"]),
                                 "entry_tangent": tuple(raw["entry_tangent"]), "exit_tangent": tuple(raw["exit_tangent"])})
        if (metadata["schema_version"] != 1 or metadata["units"] != "millimetres-y-down"
                or metadata["guide_sha256"] != object_digest(asdict(guide))
                or len(metadata["owners"]) != len(guide.samples)
                or guide.symbol != metadata["plan"]["text"]):
            raise ValueError("Guide ownership/physical identity mismatch")
        return RepertoireGuide(guide, metadata)
    except (KeyError, TypeError) as error:
        raise ValueError("Invalid attributed guide bundle") from error
