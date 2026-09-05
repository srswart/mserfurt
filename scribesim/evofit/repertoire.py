"""Opt-in shared contact programs. Catalog seeds are not recovered handwriting."""

from __future__ import annotations

import argparse
import copy
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from scribesim.evo.allograph import _apply_variant
from scribesim.evo.genome import BezierSegment, GlyphGenome
from scribesim.evo.renderer import _draw_nib_sweep
from scribesim.evofit.word_recovery import seed_hand
from scribesim.handvalidate.specimen import digest, object_digest


LIMITS = {"forms_per_symbol": 3, "chains_per_form": 8, "cubics_per_form": 32,
          "context_beam": 32, "coordinate_abs": 4.0}
FORM_FIELDS = {"logical", "visible", "mapping", "advance", "chains", "landmarks",
               "tangents", "allow_intersections", "provenance"}
MODEL_FIELDS = {"schema_version", "units", "acceptance", "forms", "rules", "joins",
                "x_height_mm", "nib_width_mm", "nib_angle_deg", "letter_gap", "space_advance"}


def refresh_form(form: dict) -> None:
    for chain in form["chains"]:
        chain["closed"] = chain["cubics"][0][0] == chain["cubics"][-1][-1]
    first = form["chains"][0]["cubics"][0]
    last = form["chains"][-1]["cubics"][-1]
    form["landmarks"] = {"entry": copy.deepcopy(first[0]), "exit": copy.deepcopy(last[-1])}
    form["tangents"] = {"entry": [first[1][axis] - first[0][axis] for axis in (0, 1)],
                        "exit": [last[3][axis] - last[2][axis] for axis in (0, 1)]}


def validate_repertoire(hand: dict) -> None:
    if set(hand) != MODEL_FIELDS or hand["schema_version"] != 2 or hand["units"] != "local-xheight-y-up":
        raise ValueError("Invalid repertoire schema/fields/units")
    if hand["acceptance"] not in {"unaccepted", "candidate"}:
        raise ValueError("Acceptance belongs to a separate gate, not this model")
    for name, lower, upper in (("x_height_mm", .5, 10), ("nib_width_mm", .05, 2),
                               ("nib_angle_deg", -180, 180), ("letter_gap", 0, .5),
                               ("space_advance", .1, 2)):
        if not isinstance(hand[name], (float, int)) or not lower <= hand[name] <= upper:
            raise ValueError(f"Invalid bound: {name}")
    if not hand["forms"]:
        raise ValueError("Empty repertoire")
    counts = Counter(form["logical"] for form in hand["forms"].values())
    if max(counts.values()) > LIMITS["forms_per_symbol"]:
        raise ValueError("form limit: at most three per logical symbol/span")
    for form_id, form in hand["forms"].items():
        if not isinstance(form_id, str) or not form_id or set(form) != FORM_FIELDS:
            raise ValueError("Invalid form fields")
        logical, visible = form["logical"], form["visible"]
        if not logical or len(logical) > 3 or any(character.isspace() for character in logical):
            raise ValueError("Logical span must be one to three nonspace symbols")
        legal = ((form["mapping"] == "identity" and len(logical) == 1 and visible == logical)
                 or (form["mapping"] == "long-s" and logical == "s" and visible == "ſ")
                 or (form["mapping"] == "ligature" and len(logical) > 1 and visible == logical))
        if not legal:
            raise ValueError("Undeclared logical-to-visible mapping")
        if not .05 <= form["advance"] <= 4 or not form["provenance"] or not isinstance(form["allow_intersections"], bool):
            raise ValueError("Invalid form bounds/provenance")
        if not 1 <= len(form["chains"]) <= LIMITS["chains_per_form"]:
            raise ValueError("chain limit: one to eight contact chains")
        if sum(len(chain["cubics"]) for chain in form["chains"]) > LIMITS["cubics_per_form"]:
            raise ValueError("cubic limit: at most 32 per form")
        for chain in form["chains"]:
            if set(chain) != {"cubics", "closed"} or not chain["cubics"]:
                raise ValueError("Invalid contact chain")
            previous = None
            for cubic in chain["cubics"]:
                if len(cubic) != 4 or any(len(point) != 2 or any(
                        not math.isfinite(value) or abs(value) > LIMITS["coordinate_abs"]
                        for value in point) for point in cubic):
                    raise ValueError("Invalid cubic coordinate bounds")
                if previous is not None and previous != cubic[0]:
                    raise ValueError("Discontinuous contact chain; declare a lift instead")
                previous = cubic[-1]
        derived = copy.deepcopy(form)
        refresh_form(derived)
        if any(derived[field] != form[field] for field in ("chains", "landmarks", "tangents")):
            raise ValueError("Stale topology/landmarks/tangents")
    for rule in hand["rules"]:
        if (set(rule) != {"form_id", "position", "previous", "next", "cost"}
                or rule["form_id"] not in hand["forms"] or rule["position"] not in {"any", "final", "medial", "initial"}
                or any(value is not None and (not isinstance(value, str) or len(value) != 1)
                       for value in (rule["previous"], rule["next"]))
                or not math.isfinite(rule["cost"]) or abs(rule["cost"]) > 10):
            raise ValueError("Invalid text-only context rule")
    for join in hand["joins"]:
        if (set(join) != {"left", "right", "kind", "cost"}
                or join["left"] not in hand["forms"] or join["right"] not in hand["forms"]
                or join["kind"] not in {"air", "contact"} or not math.isfinite(join["cost"])):
            raise ValueError("Invalid transition rule")
    object_digest(hand)


def seed_repertoire(alphabet, *, variants: bool = True) -> dict:
    seed = seed_hand(character for character in set(alphabet) if character != " ")
    hand = {"schema_version": 2, "units": "local-xheight-y-up", "acceptance": "unaccepted",
            "forms": {}, "rules": [], "joins": [], **{name: seed[name] for name in
            ("x_height_mm", "nib_width_mm", "nib_angle_deg", "letter_gap", "space_advance")}}
    families = {"s": ["long_medial", "round_final"], "i": ["plain", "lean", "compact"],
                "n": ["plain", "tight", "open"], "e": ["plain", "closed", "open"],
                "r": ["plain", "hooked", "flat"]}
    for character, local in seed["glyphs"].items():
        glyph = GlyphGenome(character, [BezierSegment(**segment) for segment in local["segments"]],
                            x_advance=local["advance"])
        for variant in families.get(character, ["catalog"]) if variants else ["catalog"]:
            world = copy.deepcopy(glyph)
            for segment in world.segments:
                for name in ("p0", "p1", "p2", "p3"):
                    point = getattr(segment, name)
                    setattr(segment, name, (point[0], -point[1]))
            world = _apply_variant(world, character, variant, 1.0, 0.0)
            chains = [{"cubics": [[[getattr(segment, name)[0], -getattr(segment, name)[1]]
                                   for name in ("p0", "p1", "p2", "p3")]]}
                      for segment in world.segments if segment.contact]
            form = {"logical": character, "visible": "ſ" if variant == "long_medial" else character,
                    "mapping": "long-s" if variant == "long_medial" else "identity",
                    "advance": world.x_advance, "chains": chains, "allow_intersections": True,
                    "provenance": {"kind": "unaccepted-catalog-prior", "catalog_id": local["catalog_id"],
                                   "allograph": variant}}
            refresh_form(form)
            form_id = f"{character}:{variant}"
            hand["forms"][form_id] = form
            if variant in {"long_medial", "round_final"}:
                hand["rules"].append({"form_id": form_id, "position": "medial" if variant == "long_medial" else "final",
                                      "previous": None, "next": None, "cost": -1.0})
    validate_repertoire(hand)
    return hand


def compose(text: str, hand: dict, *, beam: int = 32) -> dict:
    validate_repertoire(hand)
    if not text or not text.strip() or len(text) > 2000 or not 1 <= beam <= LIMITS["context_beam"]:
        raise ValueError("Invalid text or context beam limit")
    states = {0: [(0.0, [], 0.0)]}
    pruned = 0
    for position in range(len(text)):
        active = sorted(states.pop(position, []), key=lambda row: (row[0], object_digest(row[1])))
        pruned += max(0, len(active) - beam)
        for cost, occurrences, cursor in active[:beam]:
            if text[position] == " ":
                states.setdefault(position + 1, []).append((cost, occurrences, cursor + hand["space_advance"]))
                continue
            for form_id, form in sorted(hand["forms"].items()):
                if not text.startswith(form["logical"], position):
                    continue
                end = position + len(form["logical"])
                previous = text[position - 1] if position else None
                following = text[end] if end < len(text) else None
                final = following in (None, " ")
                initial = previous in (None, " ")
                extra = 0.0
                for rule in hand["rules"]:
                    if (rule["form_id"] == form_id and (rule["position"] == "any" or
                            rule["position"] == "final" and final or rule["position"] == "medial" and not final
                            or rule["position"] == "initial" and initial)
                            and (rule["previous"] is None or rule["previous"] == previous)
                            and (rule["next"] is None or rule["next"] == following)):
                        extra += rule["cost"]
                if occurrences and occurrences[-1]["span"][1] == position:
                    extra += sum(join["cost"] for join in hand["joins"] if
                                 join["left"] == occurrences[-1]["form_id"] and join["right"] == form_id)
                occurrence = {"form_id": form_id, "span": [position, end], "logical": form["logical"],
                              "visible": form["visible"], "x": cursor}
                states.setdefault(end, []).append((cost + extra, occurrences + [occurrence],
                                                    cursor + form["advance"] + (0 if final else hand["letter_gap"])))
    final_states = sorted(states.get(len(text), []), key=lambda row: (row[0], object_digest(row[1])))
    if not final_states:
        raise ValueError(f"Unsupported exact text: {text!r}; no complete logical mapping")
    _, occurrences, width = final_states[0]
    ownership, transitions = [], []
    for index, occurrence in enumerate(occurrences):
        form = hand["forms"][occurrence["form_id"]]
        for chain_index in range(len(form["chains"])):
            ownership.append({"occurrence": index, "chain": chain_index, "span": occurrence["span"]})
            if chain_index:
                transitions.append({"from": [index, chain_index - 1], "to": [index, chain_index], "kind": "air"})
        if index:
            previous = occurrences[index - 1]
            previous_form = hand["forms"][previous["form_id"]]
            joins = [join for join in hand["joins"] if join["left"] == previous["form_id"]
                     and join["right"] == occurrence["form_id"] and previous["span"][1] == occurrence["span"][0]]
            kind = min(joins, key=lambda join: join["cost"])["kind"] if joins else "air"
            transitions.append({"from": [index - 1, len(previous_form["chains"]) - 1],
                                "to": [index, 0], "kind": kind})
    return {"schema_version": 2, "text": text, "model_sha256": object_digest(hand), "coverage": 1.0,
            "occurrences": occurrences, "contact_ownership": ownership, "transitions": transitions,
            "width": width, "beam": beam, "pruned_states": pruned}


def render_key(text: str, hand: dict, *, dpi: float = 100) -> str:
    return object_digest({"text": text, "model": hand, "dpi": dpi,
                          "code": {str(path.name): digest(path) for path in
                                   (Path(__file__), Path(__file__).parents[1] / "evo/renderer.py",
                                    Path(__file__).parents[1] / "evo/genome.py")},
                          "numpy": np.__version__, "pillow": Image.__version__})


def render_nominal(text: str, hand: dict, *, dpi: float = 100) -> np.ndarray:
    plan = compose(text, hand)
    if not math.isfinite(dpi) or not 36 <= dpi <= 300:
        raise ValueError("dpi must be between 36 and 300")
    chains = {}
    scale = hand["x_height_mm"]
    for index, occurrence in enumerate(plan["occurrences"]):
        for chain_index, chain in enumerate(hand["forms"][occurrence["form_id"]]["chains"]):
            chains[index, chain_index] = [BezierSegment(*[(scale * (point[0] + occurrence["x"]),
                                                          -scale * point[1]) for point in cubic])
                                          for cubic in chain["cubics"]]
    segments = [segment for chain in chains.values() for segment in chain]
    for transition in plan["transitions"]:
        if transition["kind"] == "contact":
            start = chains[tuple(transition["from"])][-1].p3
            end = chains[tuple(transition["to"])][0].p0
            if math.dist(start, end) > 1.5 * scale:
                raise ValueError("Contact transition exceeds local join bound")
            segments.append(BezierSegment(start, start, end, end))
    points = [getattr(segment, name) for segment in segments for name in ("p0", "p1", "p2", "p3")]
    margin = hand["nib_width_mm"] + .5
    left = min(0, min(point[0] for point in points)) - margin
    right = max(plan["width"] * scale, max(point[0] for point in points)) + margin
    top = min(point[1] for point in points) - margin
    bottom = max(point[1] for point in points) + margin
    pixels = dpi * 3 / 25.4
    size = (max(3, math.ceil((right - left) * pixels)), max(3, math.ceil((bottom - top) * pixels)))
    if size[0] * size[1] > 30_000_000:
        raise ValueError("Nominal canvas exceeds pixel budget")
    canvas = Image.new("RGB", size, (245, 238, 220))
    draw = ImageDraw.Draw(canvas)
    angle = math.radians(hand["nib_angle_deg"])
    half = hand["nib_width_mm"] * pixels / 2
    for segment in segments:
        samples = []
        for step in range(33):
            horizontal, vertical = segment.evaluate(step / 32)
            samples.append(((horizontal - left) * pixels, (vertical - top) * pixels,
                            .84, half * math.cos(angle), half * math.sin(angle)))
        _draw_nib_sweep(draw, samples)
    return np.asarray(canvas.resize((size[0] // 3, size[1] // 3), Image.Resampling.LANCZOS))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dpi", type=float, default=100)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Refusing to overwrite an existing render")
    hand = json.loads(args.model.read_text())
    Image.fromarray(render_nominal(args.text, hand, dpi=args.dpi)).save(args.output)


if __name__ == "__main__":
    main()
