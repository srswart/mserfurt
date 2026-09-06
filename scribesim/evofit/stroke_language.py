"""Versioned shared stroke vocabulary and deterministic layered compilation."""

import argparse
from collections import Counter
import copy
from dataclasses import asdict
import json
import math
from pathlib import Path
import re

import numpy as np
from PIL import Image, ImageDraw

from scribesim.handflow.model import TrajectorySample
from scribesim.handvalidate.bridge import paint_trajectory
from scribesim.handvalidate.specimen import object_digest, write_json
from scribesim.pathguide.model import DensePathGuide, GuideSample, GuideSource
from scribesim.pathguide.repertoire import RepertoireGuide, _sample_cubic


SCHEMA = "shared-stroke-language-v1"
MODEL_FIELDS = {"schema_version", "units", "scope", "primitives", "recipes", "letter_rules", "word_rules",
                "x_height_mm", "nib_width_mm", "nib_angle_deg", "letter_gap", "word_gap", "line_pitch"}
PRIMITIVE_FIELDS = {"cubics", "entry", "exit", "closed", "provenance"}
RECIPE_FIELDS = {"logical", "visible", "advance", "strokes", "allow_crossings"}
STROKE_FIELDS = {"primitive", "offset", "scale", "rotation_deg", "transition"}
RULE_FIELDS = {"id", "logical", "previous", "next", "position", "stroke", "dx", "dy", "advance"}


def _number(value, lower, upper):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and lower <= value <= upper


def _direction(start, end):
    length = math.dist(start, end)
    if length < .001:
        raise ValueError("Degenerate primitive port")
    return [(end[0] - start[0]) / length, (end[1] - start[1]) / length]


def seed_language():
    geometry = {
        "stem": [[[0, 1], [.22, .78], [-.18, .3], [0, 0]]],
        "rise": [[[0, 0], [-.2, .5], [.1, .8], [.5, 1]]],
        "bowl": [[[0, 1], [1.2, .9], [1.1, .1], [.65, 0]]],
        "turn": [[[0, 0], [-.2, .6], [.75, .1], [.5, 1]]],
        "loop": [[[0, 0], [-.3, 1.6], [1, 1.6], [0, 0]]],
        "exit": [[[0, 0], [.1, -.18], [.3, .35], [.45, .15]]],
    }
    primitives = {name: {"cubics": cubics, "entry": _direction(cubics[0][0], cubics[0][1]),
                         "exit": _direction(cubics[-1][2], cubics[-1][3]), "closed": name == "loop",
                         "provenance": "unaccepted synthetic stroke prior; not historical ductus"}
                  for name, cubics in geometry.items()}
    def stroke(name, offset, transition):
        return {"primitive": name, "offset": offset, "scale": 1.0, "rotation_deg": 0.0, "transition": transition}
    recipes = {
        "i": {"logical": "i", "visible": "i", "advance": .65, "allow_crossings": False,
              "strokes": [stroke("stem", [0, 0], "start"), stroke("exit", [0, 0], "corner")]},
        "u": {"logical": "u", "visible": "u", "advance": 1.2, "allow_crossings": False,
              "strokes": [stroke("stem", [0, 0], "start"), stroke("exit", [0, 0], "corner"),
                          stroke("stem", [.55, 0], "lift"), stroke("exit", [.55, 0], "corner")]},
    }
    return {"schema_version": SCHEMA, "units": "local-xheight-y-up", "scope": "unaccepted-synthetic",
            "primitives": primitives, "recipes": recipes, "letter_rules": [], "word_rules": [],
            "x_height_mm": 3.5, "nib_width_mm": .45, "nib_angle_deg": 40.0,
            "letter_gap": .15, "word_gap": .8, "line_pitch": 3.0}


def _transform(cubics, stroke):
    angle = math.radians(stroke["rotation_deg"])
    cosine, sine = math.cos(angle), math.sin(angle)
    return [[[stroke["offset"][0] + stroke["scale"] * (point[0] * cosine - point[1] * sine),
               stroke["offset"][1] + stroke["scale"] * (point[0] * sine + point[1] * cosine)]
              for point in cubic] for cubic in cubics]


def _recipe_strokes(recipe, model):
    expanded = []
    for index, stroke in enumerate(recipe["strokes"]):
        cubics = _transform(model["primitives"][stroke["primitive"]]["cubics"], stroke)
        if index and stroke["transition"] in {"smooth", "corner"}:
            prior = expanded[-1]["cubics"][-1]
            if math.dist(prior[-1], cubics[0][0]) > .001:
                raise ValueError("Contact ports do not coincide; declare a lift")
            if stroke["transition"] == "smooth":
                before, after = _direction(prior[-2], prior[-1]), _direction(cubics[0][0], cubics[0][1])
                if sum(left * right for left, right in zip(before, after)) < math.cos(math.radians(45)):
                    raise ValueError("Smooth contact exceeds tangent guardrail")
        expanded.append({**stroke, "cubics": cubics, "primitive_index": index})
    if any(abs(value) > 4 for row in expanded for cubic in row["cubics"] for point in cubic for value in point):
        raise ValueError("Assembled letter exceeds local geometry bounds")
    return expanded


def _has_crossings(expanded):
    segments = []
    parameters = np.linspace(0, 1, 17)[:, None]
    for row in expanded:
        for cubic in row["cubics"]:
            points = ((1 - parameters) ** 3 * cubic[0] + 3 * (1 - parameters) ** 2 * parameters * cubic[1]
                      + 3 * (1 - parameters) * parameters ** 2 * cubic[2] + parameters ** 3 * cubic[3])
            segments.extend(zip(points[:-1], points[1:]))
    def side(start, end, point):
        return (end[0] - start[0]) * (point[1] - start[1]) - (end[1] - start[1]) * (point[0] - start[0])
    return any(side(first, second, third) * side(first, second, fourth) < -1e-12
               and side(third, fourth, first) * side(third, fourth, second) < -1e-12
               for index, (first, second) in enumerate(segments) for third, fourth in segments[index + 1:])


def validate_language(model):
    try:
        if set(model) != MODEL_FIELDS or model["schema_version"] != SCHEMA or model["units"] != "local-xheight-y-up":
            raise ValueError("Explicit stroke-language schema required")
        for key, lower, upper in (("x_height_mm", .5, 10), ("nib_width_mm", .05, 2), ("nib_angle_deg", -180, 180),
                                   ("letter_gap", 0, .5), ("word_gap", .1, 2), ("line_pitch", 2, 6)):
            if not _number(model[key], lower, upper):
                raise ValueError(f"Invalid model bound: {key}")
        if not isinstance(model["scope"], str) or not model["scope"] or not 1 <= len(model["primitives"]) <= 8:
            raise ValueError("Invalid scope or primitive budget")
        for name, primitive in model["primitives"].items():
            if not isinstance(name, str) or not name or set(primitive) != PRIMITIVE_FIELDS or not primitive["provenance"]:
                raise ValueError("Primitive must own geometry; references/cycles are forbidden")
            cubics = primitive["cubics"]
            if not isinstance(primitive["closed"], bool) or not 1 <= len(cubics) <= 4:
                raise ValueError("Primitive topology budget")
            for index, cubic in enumerate(cubics):
                if len(cubic) != 4 or any(len(point) != 2 or not all(_number(value, -2, 2) for value in point) for point in cubic):
                    raise ValueError("Invalid primitive coordinate")
                if sum(math.dist(first, second) for first, second in zip(cubic, cubic[1:])) > 6:
                    raise ValueError("Primitive control-polygon length guardrail")
                if index and cubics[index - 1][-1] != cubic[0]:
                    raise ValueError("Primitive chain must be continuous")
            if primitive["closed"] and cubics[0][0] != cubics[-1][-1]:
                raise ValueError("Closed primitive endpoints differ")
            for port, actual in (("entry", _direction(cubics[0][0], cubics[0][1])),
                                 ("exit", _direction(cubics[-1][2], cubics[-1][3]))):
                declared = primitive[port]
                if len(declared) != 2 or not all(_number(value, -1, 1) for value in declared) or abs(math.hypot(*declared) - 1) > .001:
                    raise ValueError("Invalid declared port direction")
                if sum(first * second for first, second in zip(declared, actual)) < 0:
                    raise ValueError("Primitive tangent outside declared port half-plane")
        counts = Counter(recipe["logical"] for recipe in model["recipes"].values())
        inventory = set("".join(counts))
        if not counts or max(counts.values()) > 2 or len(inventory) > 12:
            raise ValueError("Letter inventory/recipe budget")
        for name, recipe in model["recipes"].items():
            if not isinstance(name, str) or not name or set(recipe) != RECIPE_FIELDS:
                raise ValueError("Letter recipes reference strokes; no residual curves")
            logical = recipe["logical"]
            if not 1 <= len(logical) <= 3 or not all(character.isalpha() and character.islower() for character in logical):
                raise ValueError("Exact lowercase logical span required")
            if recipe["visible"] != logical and (logical, recipe["visible"]) != ("s", "ſ"):
                raise ValueError("Undeclared visible mapping")
            if not _number(recipe["advance"], .1, 4) or not isinstance(recipe["allow_crossings"], bool) or not 1 <= len(recipe["strokes"]) <= 4:
                raise ValueError("Recipe bounds")
            for index, stroke in enumerate(recipe["strokes"]):
                if set(stroke) != STROKE_FIELDS or stroke["primitive"] not in model["primitives"]:
                    raise ValueError("Missing primitive or unknown stroke fields")
                if (len(stroke["offset"]) != 2 or not all(_number(value, -2, 2) for value in stroke["offset"])
                        or not _number(stroke["scale"], .5, 1.5) or not _number(stroke["rotation_deg"], -20, 20)):
                    raise ValueError("Unbounded recipe transform")
                if stroke["transition"] not in ({"start"} if index == 0 else {"lift", "smooth", "corner"}):
                    raise ValueError("Undeclared stroke transition")
            expanded = _recipe_strokes(recipe, model)
            if not recipe["allow_crossings"] and _has_crossings(expanded):
                raise ValueError("Undeclared recipe crossing")
        for layer, limit in (("letter_rules", 16), ("word_rules", 8)):
            seen = set()
            if len(model[layer]) > limit:
                raise ValueError("Context rule budget")
            for rule in model[layer]:
                if set(rule) != RULE_FIELDS or not rule["id"] or rule["id"] in seen or rule["logical"] not in counts:
                    raise ValueError("Invalid/duplicate context rule")
                seen.add(rule["id"])
                if rule["position"] not in {"any", "initial", "final"} or not isinstance(rule["stroke"], int) or isinstance(rule["stroke"], bool):
                    raise ValueError("Invalid context selector")
                if any(rule[key] is not None and rule[key] not in inventory for key in ("previous", "next")):
                    raise ValueError("Context uses undeclared neighbor")
                if not all(_number(rule[key], -.15, .15) for key in ("dx", "dy", "advance")):
                    raise ValueError("Context deformation bound")
                if any(not 0 <= rule["stroke"] < len(recipe["strokes"]) for recipe in model["recipes"].values() if recipe["logical"] == rule["logical"]):
                    raise ValueError("Context stroke selector outside recipe")
        object_digest(model)
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Malformed stroke language") from error


def compile_text(text, model):
    validate_language(model)
    if not isinstance(text, str) or not text or len(text) > 300:
        raise ValueError("Text requires one to 300 exact characters")
    strokes, letters, words, lines = [], [], [], []
    horizontal, line, cursor = 0.0, 0, 0
    for match in re.finditer(r"[^ \n]+| +|\n", text):
        token = match.group()
        if token == "\n":
            lines.append({"line": line, "end": match.start(), "width": horizontal})
            horizontal, line = 0.0, line + 1
            continue
        if token.isspace():
            horizontal += len(token) * model["word_gap"]
            continue
        word = len(words)
        words.append({"word": word, "line": line, "text": token, "span": [match.start(), match.end()]})
        offset = 0
        while offset < len(token):
            candidates = [(identifier, recipe) for identifier, recipe in model["recipes"].items() if token.startswith(recipe["logical"], offset)]
            if not candidates:
                raise ValueError(f"Unsupported exact text at {match.start() + offset}: {token[offset]}")
            identifier, canonical = min(candidates, key=lambda pair: (-len(pair[1]["logical"]), pair[0]))
            recipe = copy.deepcopy(canonical)
            count = len(recipe["logical"])
            span = [match.start() + offset, match.start() + offset + count]
            previous = token[offset - 1] if offset else None
            following = token[offset + count] if offset + count < len(token) else None
            applied = []
            for layer in ("letter_rules", "word_rules"):
                if layer == "word_rules" and offset and offset + count != len(token):
                    continue
                for rule in model[layer]:
                    before, after = previous, following
                    if layer == "word_rules":
                        before = text[:match.start()].rstrip(" ").split("\n")[-1][-1:] or None
                        after = text[match.end():].lstrip(" ").split("\n")[0][:1] or None
                    if (rule["logical"] == recipe["logical"] and (rule["previous"] is None or rule["previous"] == before)
                            and (rule["next"] is None or rule["next"] == after)
                            and (rule["position"] == "any" or rule["position"] == "initial" and offset == 0
                                 or rule["position"] == "final" and offset + count == len(token))):
                        selected = recipe["strokes"][rule["stroke"]]
                        selected["offset"][0] += rule["dx"]
                        selected["offset"][1] += rule["dy"]
                        recipe["advance"] += rule["advance"]
                        applied.append(rule["id"])
                        break
            for original, changed in zip(canonical["strokes"], recipe["strokes"]):
                if any(abs(first - second) > .15 + 1e-12 for first, second in zip(original["offset"], changed["offset"])):
                    raise ValueError("Combined context exceeds deformation bound")
            if abs(recipe["advance"] - canonical["advance"]) > .15 + 1e-12 or recipe["advance"] <= 0:
                raise ValueError("Combined context exceeds advance bound")
            letter = len(letters)
            letters.append({"recipe": identifier, "span": span, "word": word, "line": line, "rules": applied})
            expanded = _recipe_strokes(recipe, model)
            if not recipe["allow_crossings"] and _has_crossings(expanded):
                raise ValueError("Context creates undeclared crossing")
            for row in expanded:
                cubics = [[[point[0] + horizontal, point[1] - line * model["line_pitch"]] for point in cubic] for cubic in row["cubics"]]
                strokes.append({**row, "cubics": cubics, "recipe": identifier, "letter": letter, "span": span,
                                "word": word, "line": line, "occurrence_id": f"{letter}:{row['primitive_index']}", "rules": applied})
            horizontal += recipe["advance"] + model["letter_gap"]
            offset += count
            cursor += count
    if cursor != sum(character not in " \n" for character in text) or not strokes:
        raise ValueError("Exact coverage failure or no ink program")
    lines.append({"line": line, "end": len(text), "width": horizontal})
    return {"schema_version": SCHEMA, "text": text, "model_sha256": object_digest(model), "coverage": 1.0,
            "strokes": strokes, "letters": letters, "words": words, "lines": lines}


def language_guide(text, model, *, step_mm=.05, include_curve_positions=False):
    if not _number(step_mm, .005, .2):
        raise ValueError("Physical sampling bound")
    plan = compile_text(text, model)
    scale = model["x_height_mm"]
    samples, owners, points = [], [], []
    for row in plan["strokes"]:
        cubics = [[[point[0] * scale, 10 - point[1] * scale] for point in cubic] for cubic in row["cubics"]]
        points.extend(point for cubic in cubics for point in cubic)
        owner = {key: row[key] for key in ("primitive", "primitive_index", "occurrence_id", "recipe", "letter", "word", "line", "span", "rules")}
        owner.update(kind="stroke", spans=[row["span"]])
        if samples and row["transition"] in {"start", "lift"}:
            start, end = [samples[-1].x_mm, samples[-1].y_mm], cubics[0][0]
            for horizontal, vertical, tangent_x, tangent_y in _sample_cubic([start, start, end, end], step_mm):
                samples.append(GuideSample(horizontal, vertical, tangent_x, tangent_y, contact=False, pressure_nominal=0,
                                           nib_angle_deg=model["nib_angle_deg"], corridor_half_width_mm=.2))
                owners.append({"kind": "air", "spans": [], "from": owners[-1].get("occurrence_id"), "to": row["occurrence_id"]})
        for cubic_index, cubic in enumerate(cubics):
            for point in _sample_cubic(cubic, step_mm, include_parameters=include_curve_positions):
                horizontal, vertical, tangent_x, tangent_y = point[:4]
                samples.append(GuideSample(horizontal, vertical, tangent_x, tangent_y, pressure_nominal=.5,
                                           nib_angle_deg=model["nib_angle_deg"], corridor_half_width_mm=.2))
                marked = copy.deepcopy(owner)
                if include_curve_positions:
                    marked['curve_position'] = {'cubic_index': cubic_index, 'parameter': point[4], 'representation': 'cubic'}
                owners.append(marked)
    if len(samples) > 100000:
        raise ValueError("Guide sample budget")
    margin = model["nib_width_mm"] + .5
    frame = [min(point[0] for point in points) - margin, max(point[0] for point in points) + margin,
             min(point[1] for point in points) - margin, max(point[1] for point in points) + margin]
    guide = DensePathGuide(text, tuple(samples), max(row["width"] for row in plan["lines"]) * scale, scale, kind="word",
                           entry_tangent=(samples[0].tangent_dx, samples[0].tangent_dy),
                           exit_tangent=(samples[-1].tangent_dx, samples[-1].tangent_dy),
                           sources=(GuideSource(object_digest(model), confidence_tier="soft_accepted", split="unaccepted-stroke-language"),))
    return RepertoireGuide(guide, {"schema_version": SCHEMA, "owners": owners, "frame_mm": frame, "plan": plan,
                                  "model_sha256": object_digest(model), "guide_sha256": object_digest(asdict(guide)),
                                  "acceptance": "compiler diagnostic; S0 is not G1/G2 acceptance"})


def render_language(text, model, *, dpi=180, frame=None):
    bundle = language_guide(text, model)
    trajectory = tuple(TrajectorySample(sample.x_mm, sample.y_mm, sample.contact, model["nib_width_mm"],
                                        sample.pressure_nominal, sample.nib_angle_deg) for sample in bundle.guide.samples)
    return paint_trajectory(trajectory, frame or bundle.metadata["frame_mm"], dpi=dpi)


def load_language_bundle(path, model):
    try:
        document = json.loads(Path(path).read_text())
        if set(document) != {"payload", "sha256"} or object_digest(document["payload"]) != document["sha256"]:
            raise ValueError("Language bundle hash mismatch")
        expected = language_guide(document["payload"]["guide"]["symbol"], model)
        if object_digest(asdict(expected)) != document["sha256"]:
            raise ValueError("Language ownership/model/guide differs from compiled source")
        return expected
    except (KeyError, TypeError) as error:
        raise ValueError("Malformed language bundle") from error


def execute_language(text, model, *, dpi=180):
    from scribesim.evofit.recovery import image_objective
    from scribesim.handflow.controller import GuidedHandFlowController
    from scribesim.handflow.controls import RepertoireControls
    from scribesim.handvalidate.bridge import neutral_profile

    bundle = language_guide(text, model)
    result = GuidedHandFlowController(neutral_profile(model), repertoire_controls=RepertoireControls()).simulate_guide(
        bundle.guide, base_speed_mm_s=12)
    owners = [copy.deepcopy(bundle.metadata["owners"][index]) for index in result.trajectory_plan_indices]
    nominal = render_language(text, model, dpi=dpi)
    actual = paint_trajectory(result.trajectory, bundle.metadata["frame_mm"], dpi=dpi)
    mask = np.where(np.asarray(Image.fromarray(nominal).convert("L")) < 180, 255, 0).astype(np.uint8)
    metrics = {"image_loss": image_objective(nominal, mask, actual)["total"],
               "corridor_error_mm": max((math.dist((sample.x_mm, sample.y_mm),
                                         (result.plan.samples[index].x_mm, result.plan.samples[index].y_mm))
                                         for sample, index in zip(result.trajectory, result.trajectory_plan_indices) if sample.contact), default=0),
               "contact_schedule_preserved": all(sample.contact == result.plan.samples[index].contact
                                                  for sample, index in zip(result.trajectory, result.trajectory_plan_indices)),
               "coverage": bundle.metadata["plan"]["coverage"]}
    return {"metrics": metrics, "owners": owners, "trajectory": [asdict(sample) for sample in result.trajectory],
            "plan_indices": list(result.trajectory_plan_indices), "images": {"nominal": nominal, "actual": actual},
            "scope": "neutral compiler diagnostic, not accepted real G2"}


def write_language_proof(output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty language proof directory")
    output.mkdir(parents=True, exist_ok=True)
    model = seed_language()
    text = "i u ii ui"
    bundle = language_guide(text, model)
    write_json(output / "model.json", model)
    write_json(output / "program.json", bundle.metadata["plan"])
    write_json(output / "guide.json", {"payload": asdict(bundle), "sha256": object_digest(asdict(bundle))})
    Image.fromarray(render_language(text, model, dpi=240)).save(output / "nominal.png")
    panel = Image.new("RGB", (1200, 420), "white")
    draw = ImageDraw.Draw(panel)
    draw.text((24, 20), "S0 SHARED STROKE LANGUAGE - synthetic recipes, not learned letters", fill="black")
    draw.text((24, 48), "i = stem + exit     u = stem + exit / lift / stem + exit", fill="black")
    colors = {"stem": "#2463b4", "exit": "#b94727"}
    for row in bundle.metadata["plan"]["strokes"]:
        for cubic in row["cubics"]:
            points = [(35 + horizontal * 125, 275 - vertical * 125) for horizontal, vertical, *_ in _sample_cubic(cubic, .02)]
            draw.line(points, fill=colors.get(row["primitive"], "#32844d"), width=7)
        draw.text((35 + row["cubics"][0][0][0] * 125, 310 + row["primitive_index"] % 2 * 20),
                  f"{row['occurrence_id']} {row['primitive']}", fill=colors.get(row["primitive"], "black"))
    panel.save(output / "decomposition.png")
    write_json(output / "S0.json", {"gate": "S0", "scope": "synthetic compiler mechanics", "status": "pass",
                                   "model_sha256": object_digest(model), "coverage": bundle.metadata["plan"]["coverage"],
                                   "promoted": False, "real_hand": "blocked; no real training or review"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_language_proof(args.output)


if __name__ == "__main__":
    main()
