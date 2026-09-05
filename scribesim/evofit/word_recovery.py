"""Bounded, exploratory whole-word inverse graphics; never a promotion path.

A hand contains ONE local cubic program per exact Unicode character. Training
words share that program, including repeated letters. No letter segmentation,
per-word geometry, transcription correction, or held-out model selection occurs.
The renderer reuses evo's polygon nib sweep but deliberately omits stochastic ink
and weathering. This recovers fixed-topology image geometry, not historical ductus.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import random
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from scribesim.evo.genome import BezierSegment, GlyphGenome, WordGenome
from scribesim.evo.renderer import _draw_nib_sweep
from scribesim.glyphs.catalog import GLYPH_CATALOG

MAX_ITERATIONS = 2000
MIN_LABEL_CONFIDENCE = 0.8
_MASK_HEIGHT = 48
_POINT_NAMES = ("p0", "p1", "p2", "p3")
_COORDINATE_BOUND = 0.4  # local x-height units, relative to the catalog seed


def _exact_glyph(character: str):
    if len(character) != 1 or character.isspace() or unicodedata.category(character).startswith("M"):
        raise ValueError(f"Unsupported standalone character: {character!r}")
    direct = GLYPH_CATALOG.get(character)
    if direct is not None and direct.unicode_codepoint == ord(character):
        return direct
    matches = [g for g in GLYPH_CATALOG.values() if g.unicode_codepoint == ord(character)]
    if len(matches) != 1:
        raise ValueError(f"Unsupported or ambiguous exact Unicode character: {character!r}")
    return matches[0]


def seed_hand(alphabet: Iterable[str]) -> dict[str, Any]:
    """Seed exact characters from catalog Unicode metadata, without period fallback.

    JSON coordinates are local x-height units, positive y above the baseline.
    ``assemble_word`` alone converts them into world-space millimetres.
    """
    glyphs = {}
    for character in sorted(set(alphabet)):
        glyph = _exact_glyph(character)
        segments = []
        for stroke in glyph.strokes:
            points = [list(point) for point in stroke.control_points]
            segment = BezierSegment(*points, pressure_curve=list(stroke.pressure_profile))
            segments.append(asdict(segment))
        glyphs[character] = {
            "catalog_id": glyph.id,
            "unicode_codepoint": glyph.unicode_codepoint,
            "advance": float(glyph.advance_width),
            "segments": segments,
        }
    if not glyphs:
        raise ValueError("A shared hand needs at least one supported character")
    return {
        "schema_version": 1,
        "representation": "shared-local-cubic-fixed-topology-v1",
        "coordinate_system": "x-height units; x right, y above baseline",
        "x_height_mm": 3.8,
        "letter_gap": 0.08,
        "space_advance": 0.6,
        "nib_width_mm": 0.6,
        "nib_angle_deg": 42.0,
        "glyphs": glyphs,
    }


def assemble_word(text: str, hand: dict[str, Any]) -> WordGenome:
    """Compose every occurrence from the same reusable local character program."""
    if not text or not text.strip():
        raise ValueError("Cannot render empty text")
    scale = hand["x_height_mm"]
    cursor = 0.0
    glyphs = []
    for index, character in enumerate(text):
        if character == " ":
            cursor += hand["space_advance"] * scale
            continue
        if character not in hand["glyphs"]:
            raise ValueError(f"Character absent from learned alphabet: {character!r}")
        local = hand["glyphs"][character]
        segments = []
        for stroke in local["segments"]:
            points = [(cursor + stroke[name][0] * scale, -stroke[name][1] * scale)
                      for name in _POINT_NAMES]
            segments.append(BezierSegment(
                *points, contact=stroke["contact"],
                pressure_curve=list(stroke["pressure_curve"]),
                speed_curve=list(stroke["speed_curve"]),
                nib_angle_drift=stroke["nib_angle_drift"],
            ))
        advance = local["advance"] * scale
        glyphs.append(GlyphGenome(character, segments, x_offset=cursor, x_advance=advance))
        cursor += advance
        if index + 1 < len(text) and text[index + 1] != " ":
            cursor += hand["letter_gap"] * scale
    return WordGenome(text=text, glyphs=glyphs, word_width_mm=cursor, global_slant_deg=0.0)


def render_shared_word(text: str, hand: dict[str, Any], *, dpi: float = 100) -> np.ndarray:
    """Render shared cubics with the existing polygon-sweep primitive, without RNG.

    This geometry-only observation model has constant ink, no post-dip blob,
    artificial joining strokes, per-instance jitter, or global random-state swap.
    The cubic control hull determines a padded canvas, so proposals cannot improve
    the loss merely by moving strokes outside a fixed rendering window.
    """
    if not math.isfinite(dpi) or not 36 <= dpi <= 300:
        raise ValueError("dpi must be finite and between 36 and 300")
    genome = assemble_word(text, hand)
    segments = [segment for glyph in genome.glyphs for segment in glyph.segments if segment.contact]
    points = [getattr(segment, name) for segment in segments for name in _POINT_NAMES]
    if not points:
        raise ValueError("Hand has no contact geometry")
    margin = hand["nib_width_mm"] + 0.5
    left = min(point[0] for point in points) - margin
    top = min(point[1] for point in points) - margin
    width = max(point[0] for point in points) - left + margin
    height = max(point[1] for point in points) - top + margin
    supersample = 3
    pixels_per_mm = dpi * supersample / 25.4
    size = (max(3, math.ceil(width * pixels_per_mm)), max(3, math.ceil(height * pixels_per_mm)))
    canvas = Image.new("RGB", size, (245, 238, 220))
    draw = ImageDraw.Draw(canvas)
    for segment in segments:
        angle = math.radians(hand["nib_angle_deg"] + segment.nib_angle_drift)
        samples = []
        for index in range(33):
            t = index / 32
            x, y = segment.evaluate(t)
            pressure = segment.pressure_at(t)
            half = hand["nib_width_mm"] * (1 + 0.08 * (pressure - 0.5)) * pixels_per_mm / 2
            samples.append(((x - left) * pixels_per_mm, (y - top) * pixels_per_mm,
                            0.84, half * math.cos(angle), half * math.sin(angle)))
        _draw_nib_sweep(draw, samples)
    return np.asarray(canvas.resize((max(1, size[0] // supersample), max(1, size[1] // supersample)),
                                    Image.Resampling.LANCZOS))


def normalize_word_mask(image: Image.Image | np.ndarray) -> np.ndarray:
    """Per-image Otsu foreground with a tight bounding box; True means ink.

    No thresholds or statistics are estimated across samples or splits. Blank
    images become one false pixel, not a self-matching reference template.
    """
    array = np.asarray(image)
    if array.dtype == np.bool_:
        mask = array
    else:
        gray = np.asarray(Image.fromarray(array.astype(np.uint8)).convert("L"))
        histogram = np.bincount(gray.ravel(), minlength=256).astype(float)
        if np.count_nonzero(histogram) <= 1:
            mask = gray < 128
        else:
            weights = np.cumsum(histogram)
            sums = np.cumsum(histogram * np.arange(256))
            denominator = weights * (weights[-1] - weights)
            variance = np.divide((sums[-1] * weights - sums * weights[-1]) ** 2,
                                 denominator, out=np.zeros(256), where=denominator > 0)
            mask = gray <= int(np.argmax(variance))
    if mask.ndim != 2:
        raise ValueError("A word mask must be a two-dimensional image")
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return np.zeros((1, 1), dtype=bool)
    return mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def _canonical_mask(image: Image.Image | np.ndarray) -> np.ndarray:
    mask = normalize_word_mask(image)
    if not mask.any():
        return mask
    # One scale for both axes: aspect is preserved, never stretched to a square.
    width = max(1, round(mask.shape[1] * _MASK_HEIGHT / mask.shape[0]))
    return np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).resize(
        (width, _MASK_HEIGHT), Image.Resampling.LANCZOS)) >= 128


def _mask_loss(target: np.ndarray, rendered: np.ndarray) -> float:
    if not target.any() or not rendered.any():
        return 1.0
    width = max(target.shape[1], rendered.shape[1]) + 8
    height = max(target.shape[0], rendered.shape[0]) + 8
    aligned = []
    for mask in (target, rendered):
        canvas = np.zeros((height, width), dtype=bool)
        y, x = (height - mask.shape[0]) // 2, (width - mask.shape[1]) // 2
        canvas[y:y + mask.shape[0], x:x + mask.shape[1]] = mask
        aligned.append(canvas)
    a, b = aligned
    iou_loss = 1.0 - float(np.count_nonzero(a & b)) / np.count_nonzero(a | b)
    # Symmetric two-pixel proximity softens small registration errors; undilated
    # IoU remains dominant, penalizing filled counters and extra/missing strokes.
    near_a = np.asarray(Image.fromarray(a.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    near_b = np.asarray(Image.fromarray(b.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    proximity_loss = 1.0 - 0.5 * (np.count_nonzero(a & near_b) / np.count_nonzero(a)
                                + np.count_nonzero(b & near_a) / np.count_nonzero(b))
    aspect_loss = min(1.0, abs(math.log((target.shape[1] / target.shape[0])
                                      / (rendered.shape[1] / rendered.shape[0]))))
    return float(0.65 * iou_loss + 0.20 * proximity_loss + 0.15 * aspect_loss)


def word_image_loss(target_image: Image.Image | np.ndarray,
                    rendered_image: Image.Image | np.ndarray) -> float:
    """Lower is better: shape/proximity/aspect loss, not OCR or legibility."""
    return _mask_loss(_canonical_mask(target_image), _canonical_mask(rendered_image))


def _propose(hand: dict, baseline: dict, alphabet: list[str], rng: random.Random,
             iteration: int, iterations: int) -> tuple[dict, str | None, str]:
    # Copy only the changed character, not every stroke in the hand.
    candidate = dict(hand)
    step = 0.10 * (1.0 - 0.7 * iteration / max(1, iterations))
    sign = rng.choice((-1, 1))
    mode = rng.randrange(10)
    if mode == 0:
        key = rng.choice(("nib_width_mm", "nib_angle_deg"))
        low, high, delta = (0.3, 0.9, step) if key == "nib_width_mm" else (20.0, 65.0, step * 30)
        candidate[key] = max(low, min(high, hand[key] + sign * delta))
        return candidate, None, key
    character = rng.choice(alphabet)
    candidate["glyphs"] = dict(hand["glyphs"])
    local = copy.deepcopy(hand["glyphs"][character])
    candidate["glyphs"][character] = local
    original = baseline["glyphs"][character]
    if mode <= 2:
        local["advance"] = max(original["advance"] * 0.5, min(original["advance"] * 1.5,
                                                            local["advance"] + sign * step))
        return candidate, character, "advance"
    axis = rng.randrange(2)
    if mode <= 5:
        for segment in local["segments"]:
            for name in _POINT_NAMES:
                segment[name][axis] *= 1 + sign * step
        parameter = "scale_x" if axis == 0 else "scale_y"
    else:
        segment_index = rng.randrange(len(local["segments"]))
        point_name = rng.choice(_POINT_NAMES)
        # Coincident catalog endpoints form one coordinate, preserving junctions.
        anchor = original["segments"][segment_index][point_name]
        for index, segment in enumerate(local["segments"]):
            for name in _POINT_NAMES:
                same_endpoint = (point_name in ("p0", "p3") and name in ("p0", "p3")
                                 and original["segments"][index][name] == anchor)
                if (index == segment_index and name == point_name) or same_endpoint:
                    segment[name][axis] += sign * step
        parameter = f"segment_{segment_index}_{point_name}_{axis}"
    for index, segment in enumerate(local["segments"]):
        for name in _POINT_NAMES:
            origin = original["segments"][index][name][axis]
            segment[name][axis] = max(origin - _COORDINATE_BOUND,
                                      min(origin + _COORDINATE_BOUND, segment[name][axis]))
    return candidate, character, parameter


def fit_shared_hand(train_samples: Sequence[dict[str, Any]], *, iterations: int = 240,
                    seed: int = 0, dpi: float = 100,
                    initial_hand: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fit only ``{id, text, image}`` training records; held-out data has no API slot.

    Every proposal re-renders all affected training words. Identical strings share
    render work, but all independent crop losses contribute equally to selection.
    Unaffected words retain cached losses. ``iterations`` counts candidates, not
    generations or an unbounded convergence loop.
    """
    if isinstance(iterations, bool) or not isinstance(iterations, int) or not 0 <= iterations <= MAX_ITERATIONS:
        raise ValueError(f"iterations must be an integer between 0 and {MAX_ITERATIONS}")
    if not train_samples:
        raise ValueError("No eligible training words")
    ids = [sample["id"] for sample in train_samples]
    if len(set(ids)) != len(ids):
        raise ValueError("Training sample ids must be unique")
    alphabet = sorted({character for sample in train_samples for character in sample["text"]})
    baseline = copy.deepcopy(initial_hand) if initial_hand is not None else seed_hand(alphabet)
    if set(alphabet) - baseline["glyphs"].keys():
        raise ValueError("Training alphabet is absent from initial hand")
    hand = baseline
    targets = {sample["id"]: _canonical_mask(sample["image"]) for sample in train_samples}
    if any(not mask.any() for mask in targets.values()):
        raise ValueError("Training target contains no foreground ink")
    words: dict[str, list[str]] = defaultdict(list)
    for sample in train_samples:
        words[sample["text"]].append(sample["id"])
    affected = {character: [text for text in words if character in text] for character in alphabet}
    losses = {}
    for text, sample_ids in words.items():
        mask = _canonical_mask(render_shared_word(text, hand, dpi=dpi))
        for sample_id in sample_ids:
            losses[sample_id] = _mask_loss(targets[sample_id], mask)
    baseline_losses = dict(losses)
    best_loss = sum(losses.values()) / len(losses)
    render_evaluations = len(words)
    rng = random.Random(seed)
    history = []
    for iteration in range(iterations):
        candidate, character, parameter = _propose(hand, baseline, alphabet, rng, iteration, iterations)
        changed_words = list(words) if character is None else affected[character]
        changed_losses = {}
        for text in changed_words:
            mask = _canonical_mask(render_shared_word(text, candidate, dpi=dpi))
            render_evaluations += 1
            for sample_id in words[text]:
                changed_losses[sample_id] = _mask_loss(targets[sample_id], mask)
        candidate_loss = sum(changed_losses.get(sample_id, losses[sample_id]) for sample_id in ids) / len(ids)
        accepted = candidate_loss < best_loss - 1e-12
        if accepted:
            hand = candidate
            losses.update(changed_losses)
            best_loss = candidate_loss
        history.append({"iteration": iteration + 1, "character": character, "parameter": parameter,
                        "accepted": accepted, "candidate_loss": candidate_loss, "best_loss": best_loss,
                        "affected_training_ids": list(changed_losses)})
    return {"hand": hand, "baseline_hand": baseline, "before_losses": baseline_losses,
            "after_losses": losses, "before": sum(baseline_losses.values()) / len(ids),
            "after": best_loss, "history": history, "training_ids": ids,
            "render_evaluations": render_evaluations}


def _load_dataset(manifest_path: Path, repo_root: Path) -> tuple[dict, Image.Image, str]:
    content = manifest_path.read_bytes()
    manifest = json.loads(content)
    if manifest.get("schema_version") != 1:
        raise ValueError("Dataset schema_version must be 1")
    for key in ("hand_id", "source", "label_policy", "human_interventions", "samples", "generated_texts"):
        if key not in manifest:
            raise ValueError(f"Dataset missing {key}")
    if not isinstance(manifest["human_interventions"], list):
        raise ValueError("human_interventions must be a list")
    source = manifest["source"]
    for key in ("manuscript_id", "image_path", "sha256", "canvas_id", "image_url", "hand_identity_status"):
        if key not in source:
            raise ValueError(f"Dataset source missing {key}")
    path = Path(source["image_path"])
    if not path.is_absolute():
        path = repo_root / path
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != source["sha256"].lower():
        raise ValueError("Source image SHA256 mismatch: coordinates/labels refer to different pixels")
    with Image.open(path) as image:
        page = image.convert("RGB")
    seen = set()
    for sample in manifest["samples"]:
        for key in ("id", "text", "bbox", "split", "label_source", "confidence", "notes"):
            if key not in sample:
                raise ValueError(f"Dataset sample missing {key}")
        if sample["id"] in seen:
            raise ValueError("Duplicate sample id")
        seen.add(sample["id"])
        if sample["split"] not in ("train", "heldout"):
            raise ValueError("Sample split must be train or heldout")
        bbox = sample["bbox"]
        if len(bbox) != 4 or any(isinstance(v, bool) or not isinstance(v, int) for v in bbox):
            raise ValueError("bbox must contain four native integer pixel coordinates")
        x0, y0, x1, y1 = bbox
        if not (0 <= x0 < x1 <= page.width and 0 <= y0 < y1 <= page.height):
            raise ValueError(f"Invalid/out-of-bounds bbox for {sample['id']}")
        confidence = sample["confidence"]
        if not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Sample confidence must be finite and between 0 and 1")
    train = [s for s in manifest["samples"] if s["split"] == "train"]
    heldout = [s for s in manifest["samples"] if s["split"] == "heldout"]
    for a in train:
        for b in heldout:
            if (max(a["bbox"][0], b["bbox"][0]) < min(a["bbox"][2], b["bbox"][2])
                    and max(a["bbox"][1], b["bbox"][1]) < min(a["bbox"][3], b["bbox"][3])):
                raise ValueError(f"Cross-split bbox overlap: {a['id']} and {b['id']}")
    return manifest, page, hashlib.sha256(content).hexdigest()


def _exclusion(sample: dict) -> str | None:
    if not isinstance(sample["text"], str) or not sample["text"] or any(c.isspace() for c in sample["text"]):
        return "not_one_literal_word"
    if sample["confidence"] < MIN_LABEL_CONFIDENCE:
        return "uncertain_machine_label"
    unsupported = []
    for character in sorted(set(sample["text"])):
        try:
            _exact_glyph(character)
        except ValueError:
            unsupported.append(character)
    if unsupported:
        return "unsupported_or_ambiguous_characters:" + "".join(unsupported)
    return None


def _font():
    for name in ("DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                 "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try:
            return ImageFont.truetype(name, 13)
        except OSError:
            continue
    return ImageFont.load_default()


def _paste_fit(canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int]) -> None:
    x, y, width, height = box
    thumb = image.copy()
    thumb.thumbnail((width, height), Image.Resampling.LANCZOS)
    canvas.paste(thumb, (x + (width - thumb.width) // 2, y + (height - thumb.height) // 2))


def _write_comparison(rows: list[dict], crops: dict[str, Image.Image], baseline: dict,
                      hand: dict, output: Path, dpi: float) -> None:
    label_width, column_width, row_height = 200, 300, 115
    sheet = Image.new("RGB", (label_width + column_width * 3, 70 + row_height * len(rows)), "white")
    draw, font = ImageDraw.Draw(sheet), _font()
    draw.text((8, 6), "EXPERIMENTAL / NOT PROMOTED -- image similarity is not legibility or label truth", fill="black", font=font)
    for column, title in enumerate(("SOURCE (unaltered word crop)", "CATALOG BASELINE", "SHARED FIT")):
        draw.text((label_width + column * column_width + 8, 37), title, fill="black", font=font)
    for index, row in enumerate(rows):
        y = 70 + index * row_height
        label = f"{row['id']}  [{row['split']}]\n{row['text']}\n"
        if row["before"] is not None:
            label += f"loss {row['before']:.4f} -> {row['after']:.4f}"
        else:
            label += "EXCLUDED (see report)"
        draw.multiline_text((8, y + 8), label, fill="black", font=font, spacing=5)
        images = [crops[row["id"]]]
        if row["before"] is not None:
            images.extend(Image.fromarray(render_shared_word(row["text"], model, dpi=dpi)) for model in (baseline, hand))
        for column, image in enumerate(images):
            _paste_fit(sheet, image, (label_width + column * column_width + 5, y + 5, column_width - 10, row_height - 10))
        draw.line((0, y + row_height - 1, sheet.width, y + row_height - 1), fill=(210, 210, 210))
    sheet.save(output)


def _write_generated(texts: list[str], training_words: set[str], hand: dict,
                     output: Path, dpi: float) -> list[dict]:
    rows = []
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            rows.append({"text": text, "status": "excluded_empty_text", "absent_alphabet": []})
            continue
        absent = sorted(set(text) - set(hand["glyphs"]) - {" "})
        rows.append({"text": text, "status": "excluded_absent_alphabet" if absent else "rendered",
                     "absent_alphabet": absent,
                     "novel_words": [word for word in text.split(" ") if word and word not in training_words]})
    sheet = Image.new("RGB", (1100, max(150, 65 + 120 * len(rows))), "white")
    draw, font = ImageDraw.Draw(sheet), _font()
    draw.text((10, 10), "GENERATED FROM SHARED LETTERS -- unscored / no OCR or historical-legibility claim", fill="black", font=font)
    if not rows:
        draw.text((10, 55), "No generated texts requested by the dataset.", fill="black", font=font)
    for index, row in enumerate(rows):
        y = 55 + 120 * index
        draw.text((10, y), f"{row['text']}  [{row['status']}]", fill="black", font=font)
        if row["status"] == "rendered":
            image = Image.fromarray(render_shared_word(row["text"], hand, dpi=dpi))
            _paste_fit(sheet, image, (10, y + 25, 1080, 85))
        else:
            draw.text((10, y + 28), f"Absent training alphabet: {''.join(row['absent_alphabet'])}", fill="black", font=font)
    sheet.save(output)
    return rows


def _summary(rows: list[dict]) -> dict | None:
    eligible = [row for row in rows if row["before"] is not None]
    if not eligible:
        return None
    return {"count": len(eligible), "before": sum(row["before"] for row in eligible) / len(eligible),
            "after": sum(row["after"] for row in eligible) / len(eligible)}


def run_word_recovery(manifest_path: str | Path, output_dir: str | Path, *,
                      iterations: int = 240, seed: int = 0, dpi: float = 100,
                      repo_root: str | Path | None = None) -> dict[str, Any]:
    """Run a fingerprinted, split-isolated experiment and write auditable artifacts."""
    manifest_path, output_dir = Path(manifest_path), Path(output_dir)
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
    manifest, page, manifest_hash = _load_dataset(manifest_path, root)
    exclusions = {sample["id"]: _exclusion(sample) for sample in manifest["samples"]}
    training_samples = [sample for sample in manifest["samples"]
                        if sample["split"] == "train" and exclusions[sample["id"]] is None]
    # Held-out crops are deliberately not opened/normalized until fitting returns.
    train_crops = {sample["id"]: page.crop(sample["bbox"]) for sample in training_samples}
    usable = []
    for sample in training_samples:
        if not normalize_word_mask(train_crops[sample["id"]]).any():
            exclusions[sample["id"]] = "no_foreground_ink"
        else:
            usable.append({"id": sample["id"], "text": sample["text"], "image": train_crops[sample["id"]]})
    fit = fit_shared_hand(usable, iterations=iterations, seed=seed, dpi=dpi)
    hand, baseline = fit["hand"], fit["baseline_hand"]
    training_words = {sample["text"] for sample in usable}
    crops = {}
    rows = []
    for sample in manifest["samples"]:
        sample_id, text = sample["id"], sample["text"]
        crop = train_crops.get(sample_id)
        if crop is None:
            crop = page.crop(sample["bbox"])
        crops[sample_id] = crop
        row = {**sample, "before": None, "after": None,
               "crop_rgb_sha256": hashlib.sha256(crop.tobytes()).hexdigest(),
               "exclusion": exclusions[sample_id], "absent_alphabet": []}
        if row["exclusion"] is None:
            absent = sorted(set(text) - set(hand["glyphs"]))
            row["absent_alphabet"] = absent
            if absent:
                row["exclusion"] = "absent_training_alphabet"
            elif not normalize_word_mask(crop).any():
                row["exclusion"] = "no_foreground_ink"
            elif sample["split"] == "train":
                row["before"], row["after"] = fit["before_losses"][sample_id], fit["after_losses"][sample_id]
            else:
                row["before"] = word_image_loss(crop, render_shared_word(text, baseline, dpi=dpi))
                row["after"] = word_image_loss(crop, render_shared_word(text, hand, dpi=dpi))
        if sample["split"] == "heldout":
            row["generalization"] = "exact_repeat" if text in training_words else "novel_word"
        rows.append(row)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_comparison(rows, crops, baseline, hand, output_dir / "comparison.png", dpi)
    generated = _write_generated(manifest["generated_texts"], training_words, hand,
                                 output_dir / "generated.png", dpi)
    config = {"iterations": iterations, "max_iterations": MAX_ITERATIONS, "seed": seed, "dpi": dpi,
              "min_label_confidence": MIN_LABEL_CONFIDENCE, "canonical_height_px": _MASK_HEIGHT,
              "coordinate_bound_xheight": _COORDINATE_BOUND, "advance_bounds_seed_ratio": [0.5, 1.5],
              "nib_width_bounds_mm": [0.3, 0.9], "nib_angle_bounds_deg": [20, 65],
              "renderer": "evo polygon nib sweep; 32 intervals; 3x supersampling; constant ink; no RNG"}
    provenance = {"manifest_path": str(manifest_path), "manifest_sha256": manifest_hash,
                  "source": manifest["source"], "label_policy": manifest["label_policy"],
                  "human_interventions": manifest["human_interventions"],
                  "human_intervention_count": len(manifest["human_interventions"])}
    learned = {**hand, "hand_id": manifest["hand_id"], "experimental": True, "promoted": False,
               "provenance": provenance, "config": config, "training_ids": fit["training_ids"]}
    heldout_rows = [row for row in rows if row["split"] == "heldout"]
    report = {
        "schema_version": 1, "hand_id": manifest["hand_id"], "experimental": True, "promoted": False,
        "decision": "not_promoted", "provenance": provenance, "config": config,
        "human_intervention_count": len(manifest["human_interventions"]),
        "training": _summary([row for row in rows if row["split"] == "train"]),
        "heldout": _summary(heldout_rows),
        "heldout_exact_repeat": _summary([row for row in heldout_rows if row["generalization"] == "exact_repeat"]),
        "heldout_novel_word": _summary([row for row in heldout_rows if row["generalization"] == "novel_word"]),
        "samples": rows, "generated": generated, "training_alphabet": sorted(hand["glyphs"]),
        "fit": {"accepted_proposals": sum(item["accepted"] for item in fit["history"]),
                "render_evaluations": fit["render_evaluations"], "training_ids": fit["training_ids"],
                "history": fit["history"]},
        "objective": {"direction": "lower_is_better", "weights": {"binary_iou": 0.65, "proximity": 0.2, "aspect": 0.15},
                      "normalization": "Independent per-crop Otsu; tight foreground; uniform scale to 48px height; centered alignment",
                      "selection": "Mean training-image loss only; all heldout metrics computed after fitting"},
        "limitations": [
            "Fixed catalog topology and stroke count; bounded coordinates cannot discover missing strokes or new allographs.",
            "One geometry per exact Unicode character; no contextual allographs or learned joins.",
            "Machine transcription hypotheses and unverified hand identity are not historical ground truth.",
            "Image similarity is not OCR accuracy, legibility, or evidence of recovered historical ductus.",
            "Per-crop thresholding may retain bleed-through or marginal noise; no letter segmentation or manual tracing.",
            "Geometry-only rendering excludes stochastic ink, paper, weathering, and scribal motion dynamics.",
            "Single-page heldout crops measure local transfer only, not independent-manuscript generalization.",
        ],
        "artifacts": {"report": "report.json", "learned_hand": "learned_hand.json", "baseline_hand": "baseline_hand.json",
                      "comparison": "comparison.png", "generated": "generated.png"},
    }
    for filename, payload in (("learned_hand.json", learned), ("baseline_hand.json", baseline), ("report.json", report)):
        (output_dir / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=240)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dpi", type=float, default=100)
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args()
    report = run_word_recovery(args.manifest, args.output_dir, iterations=args.iterations,
                               seed=args.seed, dpi=args.dpi, repo_root=args.repo_root)
    print(json.dumps({key: report[key] for key in ("decision", "training", "heldout", "heldout_exact_repeat",
                                                  "heldout_novel_word", "human_intervention_count")}, indent=2))


if __name__ == "__main__":
    main()
