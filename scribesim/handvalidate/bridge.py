"""G2 bridge diagnostics. Only actual controller output is an acceptance image."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scribesim.evo.renderer import _draw_nib_sweep
from scribesim.evofit.repertoire import render_nominal, seed_repertoire
from scribesim.evofit.recovery import image_objective
from scribesim.hand.profile import HandProfile
from scribesim.handflow.controller import GuidedHandFlowController
from scribesim.handflow.controls import RepertoireControls
from scribesim.handvalidate.model import TrajectorySample
from scribesim.handvalidate.specimen import digest, object_digest, write_json, write_equal_scale_panel
from scribesim.pathguide.repertoire import convert_word, require_g1, save_bundle


SYNTHETIC_BOUNDS = {"sampled_image_loss": .15, "actual_image_loss": .35,
                    "actual_corridor_error_mm": .25, "width_delta_mm": .5}


def neutral_profile(hand):
    profile = HandProfile()
    profile.nib.width_mm = hand["nib_width_mm"]
    profile.nib.angle_deg = hand["nib_angle_deg"]
    profile.letterform.x_height_mm = hand["x_height_mm"]
    profile.dynamics.rhythm_strength = 0
    profile.ink.depletion_rate = 0
    profile.ink.fresh_dip_darkness_boost = 0
    profile.fatigue_rate = 0
    return profile


def paint_trajectory(trajectory, frame, *, dpi=180, contact_version=None):
    from scribesim.evo.nib_contact import ContactSample, VERSION, contact_corners

    trajectory = tuple(trajectory)
    if contact_version not in (None, VERSION):
        raise ValueError('Unsupported trajectory contact version')
    if any(isinstance(sample, ContactSample) != (contact_version == VERSION) for sample in trajectory):
        raise ValueError('Explicit matching trajectory contact version required')
    if contact_version == VERSION:
        for sample in trajectory:
            contact_corners(sample)
    left, right, top, bottom = frame
    pixels = dpi * 3 / 25.4
    size = max(3, math.ceil((right - left) * pixels)), max(3, math.ceil((bottom - top) * pixels))
    if size[0] * size[1] > 30000000:
        raise ValueError("Bridge canvas exceeds pixel budget")
    image = Image.new("RGB", size, (245, 238, 220))
    draw = ImageDraw.Draw(image)
    run = []
    for sample in (*trajectory, TrajectorySample(0, 0, False)):
        if not sample.contact:
            if run:
                if contact_version == VERSION:
                    _draw_nib_sweep(draw, [], contact_samples=run, pixels_per_mm=pixels, origin_mm=(left, top))
                else:
                    _draw_nib_sweep(draw, run)
            run = []
            continue
        if contact_version == VERSION:
            run.append(sample)
            continue
        half = (sample.width_mm or 0) * pixels / 2
        angle = math.radians(sample.nib_angle_deg or 0)
        darkness = min(.98, max(0.0, .84 * (sample.pressure or 0) / .5))
        run.append(((sample.x_mm - left) * pixels, (sample.y_mm - top) * pixels,
                    darkness, half * math.cos(angle), half * math.sin(angle)))
    return np.asarray(image.resize((size[0] // 3, size[1] // 3), Image.Resampling.LANCZOS))


def compare_bridge(bundle, hand, *, result=None, dpi=180, controller_controls=None):
    if bundle.metadata["model_sha256"] != object_digest(hand):
        raise ValueError("Bridge model identity mismatch")
    if result is None:
        result = GuidedHandFlowController(neutral_profile(hand), repertoire_controls=controller_controls).simulate_guide(bundle.guide, base_speed_mm_s=12)
    if len(result.trajectory_plan_indices) != len(result.trajectory):
        raise ValueError("Actual trajectory lacks plan ownership")
    playback = tuple(TrajectorySample(sample.x_mm, sample.y_mm, sample.contact,
                                      hand["nib_width_mm"], sample.pressure_nominal, sample.nib_angle_deg)
                     for sample in bundle.guide.samples)
    nominal = render_nominal(bundle.guide.symbol, hand, dpi=dpi)
    sampled = paint_trajectory(playback, bundle.metadata["frame_mm"], dpi=dpi)
    actual = paint_trajectory(result.trajectory, bundle.metadata["frame_mm"], dpi=dpi)
    mask = np.where(np.asarray(Image.fromarray(nominal).convert("L")) < 180, 255, 0).astype(np.uint8)
    errors, width_deltas = [], []
    owners = []
    for sample, index in zip(result.trajectory, result.trajectory_plan_indices):
        desired = result.plan.samples[index]
        owners.append(bundle.metadata["owners"][index])
        if sample.contact:
            errors.append(math.dist((sample.x_mm, sample.y_mm), (desired.x_mm, desired.y_mm)))
            width_deltas.append(abs((sample.width_mm or 0) - hand["nib_width_mm"]))
    metrics = {"sampled_image_loss": image_objective(nominal, mask, sampled)["total"],
               "actual_image_loss": image_objective(nominal, mask, actual)["total"],
               "actual_corridor_error_mm": max(errors, default=0), "width_delta_mm": max(width_deltas, default=0),
               "coverage": bundle.metadata["plan"]["coverage"],
               "contact_schedule_preserved": all(sample.contact == result.plan.samples[index].contact
                   for sample, index in zip(result.trajectory, result.trajectory_plan_indices))}
    return {"metrics": metrics, "result": result, "actual_owners": owners,
            "images": {"nominal": nominal, "sampled": sampled, "actual": actual}}


def decide_g2(rows, *, prerequisite, scope, tolerances):
    reasons = []
    if prerequisite.get("status") != "pass":
        reasons.append("G1_not_passed")
    if scope != "real-candidate":
        reasons.append("synthetic_diagnostic_not_candidate")
    if (not tolerances or set(tolerances) != set(SYNTHETIC_BOUNDS) or any(
            not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 for value in tolerances.values())):
        reasons.append("development_frozen_tolerances_missing")
        tolerances = None
    if not rows:
        reasons.append("bridge_cases_missing")
    failures = []
    for row in rows:
        metrics = row["metrics"]
        if metrics.get("coverage") != 1 or metrics.get("contact_schedule_preserved") is not True:
            failures.append("text_or_contact_changed")
        if tolerances:
            for name, bound in tolerances.items():
                value = metrics.get(name)
                if not isinstance(value, (int, float)) or not math.isfinite(value) or value > bound:
                    failures.append(f'{row["text"]}:{name}')
    return {"gate": "G2", "status": "fail" if failures else "blocked" if reasons else "pass",
            "reasons": sorted(set(reasons + failures)), "promoted": False, "executed": bool(rows)}


def run_bridge(output, *, nominal_root=None, dataset_root=None, benchmark_root=None, target_review=None, review=None, tolerances=None, repertoire_mode=False):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty bridge directory")
    output.mkdir(parents=True, exist_ok=True)
    scope = "synthetic-diagnostic"
    prerequisite = {"status": "blocked", "reason": "no accepted nominal hand"}
    if nominal_root is not None:
        try:
            hand, nominal_freeze = require_g1(nominal_root, dataset_root=dataset_root, benchmark_root=benchmark_root,
                                             target_review=target_review, review=review)
        except ValueError as error:
            gate = {"gate": "G2", "status": "blocked", "reasons": [str(error)], "promoted": False, "executed": False}
            write_json(output / "G2.json", gate)
            return gate
        texts = [row["text"] for row in nominal_freeze["proofs"]]
        scope, prerequisite = "real-candidate", {"status": "pass", "freeze_sha256": object_digest(nominal_freeze)}
        if (not tolerances or tolerances.get("nominal_freeze_sha256") != object_digest(nominal_freeze)
                or tolerances.get("status") != "frozen_development"):
            gate = {"gate": "G2", "status": "blocked", "reasons": ["development_frozen_tolerances_missing"], "promoted": False, "executed": False}
            write_json(output / "G2.json", gate)
            return gate
        tolerances = tolerances["limits"]
    else:
        texts = ["sins", "in rein", "deine hand"]
        hand = seed_repertoire("".join(texts))
        tolerances = dict(SYNTHETIC_BOUNDS)
    write_json(output / "model.json", hand)
    freeze = {"schema_version": 1, "scope": scope, "texts": texts, "model_sha256": object_digest(hand),
              "prerequisite": prerequisite, "tolerances": tolerances, "profile": asdict(neutral_profile(hand)),
              "controller_controls": asdict(RepertoireControls()) if repertoire_mode else None,
              "sampling_mm": .05, "dpi": 180, "base_speed_mm_s": 12}
    write_json(output / "freeze.json", freeze)
    rows, tiles = [], []
    for index, text in enumerate(texts):
        bundle = convert_word(text, hand)
        save_bundle(bundle, output / f"guide-{index}.json")
        comparison = compare_bridge(bundle, hand, controller_controls=RepertoireControls() if repertoire_mode else None)
        row = {"text": text, "metrics": comparison["metrics"]}
        rows.append(row)
        write_json(output / f"actual-{index}.json", {"trajectory": [asdict(sample) for sample in comparison["result"].trajectory],
                    "owners": comparison["actual_owners"], "plan_indices": comparison["result"].trajectory_plan_indices})
        for name, array in comparison["images"].items():
            Image.fromarray(array).save(output / f"{name}-{index}.png")
            tiles.append((f'{scope} | {text} | {name}', Image.fromarray(array), hand["x_height_mm"] * 180 / 25.4))
    write_equal_scale_panel(tiles, output / "comparison.png")
    gate = decide_g2(rows, prerequisite=prerequisite, scope=scope, tolerances=tolerances)
    write_json(output / "report.json", {"freeze_sha256": object_digest(freeze), "rows": rows, "gate": gate,
               "artifacts": {path.name: digest(path) for path in output.iterdir() if path.is_file()}})
    write_json(output / "G2.json", gate)
    return gate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--nominal-root", type=Path)
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument("--benchmark-root", type=Path)
    parser.add_argument("--target-review", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--tolerances", type=Path)
    parser.add_argument("--repertoire-mode", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run_bridge(args.output, nominal_root=args.nominal_root, dataset_root=args.dataset_root,
        benchmark_root=args.benchmark_root, target_review=json.loads(args.target_review.read_text()) if args.target_review else None,
        review=json.loads(args.review.read_text()) if args.review else None,
        tolerances=json.loads(args.tolerances.read_text()) if args.tolerances else None, repertoire_mode=args.repertoire_mode), indent=2))


if __name__ == "__main__":
    main()
