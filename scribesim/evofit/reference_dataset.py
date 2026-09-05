"""Line-aware, uncertainty-preserving TD-018 word observation preparation."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import platform
import re

import numpy as np
from PIL import Image, ImageDraw

from scribesim.handvalidate.specimen import (
    ROOT, V1, digest, evaluate_benchmark, object_digest, write_json,
)


CONFIG = {
    "version": "line-components-v1", "strong_ink_max": 128, "weak_ink_max": 210,
    "minimum_line_pitch_px": 20, "projection_smoothing_px": 5,
    "minimum_component_strong_fraction": 0.15,
    "unknown_fraction_max": 0.35, "minimum_label_confidence": 0.8,
    "minimum_training_instances": 3, "minimum_training_contexts": 2,
}
SPLITS = {"train", "development", "test"}


def _gray(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("L"))


def detect_lines(image: Image.Image) -> list[dict]:
    projection = (_gray(image) <= CONFIG["strong_ink_max"]).sum(axis=1).astype(float)
    if not projection.any():
        return []
    smooth = np.convolve(projection, np.ones(5) / 5, mode="same")
    threshold = max(2.0, float(smooth.max()) * 0.12)
    local = np.nonzero((smooth >= np.roll(smooth, 1)) & (smooth >= np.roll(smooth, -1)) & (smooth >= threshold))[0]
    groups = np.split(local, np.nonzero(np.diff(local) > 1)[0] + 1)
    proposals = [int(np.median(group)) for group in groups if len(group)]
    chosen = []
    for center in sorted(proposals, key=lambda value: (-smooth[value], value)):
        if all(abs(center - previous) >= CONFIG["minimum_line_pitch_px"] for previous in chosen):
            chosen.append(center)
    lines = []
    for center in sorted(chosen):
        top = bottom = center
        while top > 0 and smooth[top - 1] >= smooth[center] * 0.65:
            top -= 1
        while bottom + 1 < len(smooth) and smooth[bottom + 1] >= smooth[center] * 0.65:
            bottom += 1
        xheight = max(3, bottom - top + 1)
        lines.append({"center_y": center, "core_top": top, "core_bottom": bottom,
                      "baseline_y": bottom, "xheight_px": xheight,
                      "estimate_status": "automatic_unreviewed", "uncertainty_px": max(2, xheight * 0.25)})
    return lines


def _components(binary: np.ndarray) -> list[np.ndarray]:
    remaining = binary.copy()
    height, width = remaining.shape
    components = []
    for row, column in zip(*np.nonzero(binary)):
        if not remaining[row, column]:
            continue
        pending, pixels = [(int(row), int(column))], []
        remaining[row, column] = False
        while pending:
            current_row, current_column = pending.pop()
            pixels.append((current_row, current_column))
            for next_row in range(max(0, current_row - 1), min(height, current_row + 2)):
                for next_column in range(max(0, current_column - 1), min(width, current_column + 2)):
                    if remaining[next_row, next_column]:
                        remaining[next_row, next_column] = False
                        pending.append((next_row, next_column))
        components.append(np.asarray(pixels, dtype=int))
    return components


def _assign_components(image: Image.Image, lines: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    gray = _gray(image)
    owners = np.full(gray.shape, -1, dtype=np.int32)
    uncertain = (gray > CONFIG["strong_ink_max"]) & (gray < CONFIG["weak_ink_max"])
    centers = np.asarray([line["center_y"] for line in lines])
    for pixels in _components(gray < CONFIG["weak_ink_max"]):
        rows, columns = pixels[:, 0], pixels[:, 1]
        strong_rows = rows[gray[rows, columns] <= CONFIG["strong_ink_max"]]
        touched = [index for index, line in enumerate(lines)
                   if np.count_nonzero((strong_rows >= line["core_top"]) & (strong_rows <= line["core_bottom"])) >= 2]
        if (len(touched) > 1 or not len(centers)
                or len(strong_rows) / len(rows) < CONFIG["minimum_component_strong_fraction"]):
            uncertain[rows, columns] = True
        else:
            owner = touched[0] if touched else int(np.argmin(abs(centers - np.median(strong_rows))))
            owners[rows, columns] = owner
            uncertain[rows, columns] = False
    return owners, uncertain


def line_mask(image: Image.Image, lines: list[dict], line_index: int) -> np.ndarray:
    if not 0 <= line_index < len(lines):
        raise ValueError("Invalid target line")
    owners, uncertain = _assign_components(image, lines)
    return _mask_for_line(owners, uncertain, line_index)


def _mask_for_line(owners: np.ndarray, uncertain: np.ndarray, line_index: int) -> np.ndarray:
    mask = np.zeros(owners.shape, dtype=np.uint8)
    mask[owners == line_index] = 255
    mask[uncertain] = 128
    return mask


def _bounds(bounds: list[int], width: int, height: int) -> None:
    if len(bounds) != 4 or any(isinstance(value, bool) or not isinstance(value, int) for value in bounds):
        raise ValueError("Bounds require four integer source coordinates")
    left, top, right, bottom = bounds
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError("Bounds outside source image")


def _overlap(first: list[int], second: list[int]) -> bool:
    return max(first[0], second[0]) < min(first[2], second[2]) and max(first[1], second[1]) < min(first[3], second[3])


def _validate_splits(samples: list[dict], source_hashes: dict[str, str]) -> None:
    identifiers, groups, observations = set(), {}, set()
    for sample in samples:
        if sample["id"] in identifiers:
            raise ValueError("Duplicate sample id")
        identifiers.add(sample["id"])
        if sample["split"] not in SPLITS:
            raise ValueError("Unknown split")
        if sample.get("previously_inspected") and sample["split"] == "test":
            raise ValueError("Previously inspected pixels cannot enter locked test")
        group = (source_hashes[sample["source_id"]], sample["line_index"])
        observation = (source_hashes[sample["source_id"]], tuple(sample["bbox"]))
        if observation in observations:
            raise ValueError("Duplicate source pixel observation")
        observations.add(observation)
        if group in groups and groups[group] != sample["split"]:
            raise ValueError("Source line shared across splits")
        groups[group] = sample["split"]
    for index, sample in enumerate(samples):
        for other in samples[index + 1:]:
            if (source_hashes[sample["source_id"]] == source_hashes[other["source_id"]]
                    and sample["split"] != other["split"] and _overlap(sample["bbox"], other["bbox"])):
                raise ValueError("Source pixels shared across splits")


def _exclusions(sample: dict, mask: np.ndarray) -> list[str]:
    reasons = []
    text = sample.get("text", "")
    confidence = sample.get("confidence", 0)
    if (not text or not isinstance(confidence, (int, float)) or not math.isfinite(confidence)
            or not CONFIG["minimum_label_confidence"] <= confidence <= 1
            or sample.get("label_status") not in {"machine_hypothesis", "reviewed"}
            or not sample.get("label_origin")):
        reasons.append("uncertain_or_missing_label")
    mapping = sample.get("visible_mapping", [])
    if (sample.get("mapping_status") != "declared" or not mapping
            or "".join(item.get("logical", "") for item in mapping) != text
            or any(not item.get("visible") or not item["visible"].isalpha()
                   or not (item["visible"] == item.get("logical") or (item.get("logical"), item["visible"]) == ("s", "ſ"))
                   for item in mapping)):
        reasons.append("unsupported_or_unverified_visible_mapping")
    target = np.count_nonzero(mask == 255)
    unknown = np.count_nonzero(mask == 128)
    if not target:
        reasons.append("no_target_ink")
    if unknown / max(1, target + unknown) > CONFIG["unknown_fraction_max"]:
        reasons.append("excess_unknown_ink")
    if sample.get("line_assignment_status") == "ambiguous":
        reasons.append("ambiguous_line_assignment")
    return reasons


def _readiness(samples: list[dict], contract: dict) -> dict:
    admitted = [sample for sample in samples if sample["admission"] == "auto_admitted"]
    counts = {split: sum(sample["split"] == split for sample in admitted) for split in sorted(SPLITS)}
    required = set("".join(proof["text"] for proof in contract.get("proofs", []))) - {" "}
    if not required:
        required = set("".join(sample.get("text", "") for sample in samples)) - {" "}
    support, contexts = Counter(), defaultdict(set)
    for sample in admitted:
        if sample["split"] == "train":
            for symbol in set(sample["text"]):
                support[symbol] += 1
                contexts[symbol].add(sample["text"])
    debt = {symbol: {"instances": support[symbol], "contexts": len(contexts[symbol])}
            for symbol in sorted(required) if support[symbol] < CONFIG["minimum_training_instances"]
            or len(contexts[symbol]) < CONFIG["minimum_training_contexts"]}
    reasons = []
    if debt:
        reasons.append("insufficient_training_support")
    if not all(counts.values()):
        reasons.append("admitted_split_coverage_missing")
    if len(admitted) < 30:
        reasons.append("fewer_than_30_usable_instances")
    return {"status": "blocked" if reasons else "pass", "reasons": reasons,
            "split_counts": counts, "support_debt": debt,
            "candidate_counts": dict(Counter(sample["split"] for sample in samples)),
            "admitted_count": len(admitted), "quarantined_count": len(samples) - len(admitted)}


def _contained(output: Path, relative: str) -> Path:
    path = (output / relative).resolve()
    if not path.is_relative_to(output.resolve()) or not path.is_file():
        raise ValueError("Artifact missing or outside dataset")
    return path


def calibrate_observations(samples: list[dict], output: Path) -> dict:
    from scribesim.evofit.word_recovery import word_image_loss

    groups = defaultdict(list)
    for sample in samples:
        if sample["admission"] == "auto_admitted" and sample["split"] in {"train", "development"}:
            groups[sample["text"]].append(sample)
    pairs, used = [], set()
    for group in groups.values():
        for index, first in enumerate(group):
            for second in group[index + 1:]:
                if first["source_id"] == second["source_id"] and _overlap(first["bbox"], second["bbox"]):
                    continue
                first_mask = np.asarray(Image.open(output / first["mask_path"])) == 255
                second_mask = np.asarray(Image.open(output / second["mask_path"])) == 255
                pairs.append(word_image_loss(first_mask, second_mask))
                used.update((first["id"], second["id"]))
    target = Image.new("L", (48, 48), 0)
    draw = ImageDraw.Draw(target)
    draw.ellipse((8, 8, 38, 38), fill=255)
    draw.ellipse((15, 15, 31, 31), fill=0)
    filled = target.copy()
    ImageDraw.Draw(filled).ellipse((8, 8, 38, 38), fill=255)
    extra = target.copy()
    ImageDraw.Draw(extra).line((0, 2, 45, 45), fill=255, width=4)
    wrong = Image.new("L", target.size, 0)
    ImageDraw.Draw(wrong).line((8, 8, 38, 38, 38, 8), fill=255, width=5)
    alternatives = {"correct": target, "wrong_form": wrong, "filled_counter": filled,
                    "extra_stroke": extra, "distorted_aspect": target.resize((96, 48))}
    controls = []
    for name, candidate in alternatives.items():
        loss = word_image_loss(np.asarray(target) > 0, np.asarray(candidate) > 0)
        controls.append({"name": name, "image_loss": loss, "passed": loss == 0 if name == "correct" else loss > 0})
    status = "fail" if not all(control["passed"] for control in controls) else "pass" if pairs else "blocked"
    return {"status": status, "repeat_pair_count": len(pairs), "used_sample_ids": sorted(used),
            "repeat_image_loss": {"median": float(np.median(pairs)), "maximum": max(pairs)} if pairs else None,
            "controls": controls, "controls_scope": "synthetic topology/ink controls, not transcription accuracy",
            "readings": "same-label hypotheses; independent correctness remains a separate review",
            "threshold_status": "descriptive development calibration; future recovery weights must be frozen separately",
            "reason": "non-test repeated-source observations available" if pairs else "no admitted non-test independent repeats"}


def validate_dataset(dataset: dict, output: Path) -> None:
    if dataset.get("schema_version") != 2 or dataset.get("config") != CONFIG:
        raise ValueError("Unsupported dataset/configuration")
    if dataset.get("config_sha256") != object_digest(CONFIG) or dataset.get("contract_sha256") != object_digest(dataset["contract"]):
        raise ValueError("Dataset contract/configuration hash mismatch")
    source_hashes, source_contexts = {}, {}
    for source in dataset["sources"]:
        path = _contained(output, source["path"])
        if digest(path) != source["sha256"]:
            raise ValueError("Source hash mismatch")
        source_hashes[source["id"]] = source["sha256"]
        with Image.open(path) as image:
            region = source["region"]
            source_contexts[source["id"]] = (region, *_assign_components(image.crop(region), source["lines"]))
    _validate_splits(dataset["samples"], source_hashes)
    for sample in dataset["samples"]:
        for kind in ("raw", "mask", "cleaned"):
            if digest(_contained(output, sample[kind + "_path"])) != sample[kind + "_sha256"]:
                raise ValueError(f"{kind} hash mismatch")
        source = next(source for source in dataset["sources"] if source["id"] == sample["source_id"])
        with Image.open(output / source["path"]) as image:
            _bounds(sample["bbox"], image.width, image.height)
            raw = np.asarray(Image.open(output / sample["raw_path"]))
            if not np.array_equal(raw, np.asarray(image.crop(sample["bbox"]))):
                raise ValueError("Raw pixels differ from original source")
        mask = np.asarray(Image.open(output / sample["mask_path"]))
        if mask.shape != raw.shape[:2] or not set(np.unique(mask)) <= {0, 128, 255}:
            raise ValueError("Invalid three-state mask")
        left, top, right, bottom = sample["bbox"]
        if sample["source_to_crop"] != [1, 0, -left, 0, 1, -top]:
            raise ValueError("Invalid source-to-crop transform")
        region, owners, uncertain = source_contexts[sample["source_id"]]
        expected_mask = _mask_for_line(owners, uncertain, sample["line_index"])[
            top - region[1]:bottom - region[1], left - region[0]:right - region[0]]
        if not np.array_equal(mask, expected_mask):
            raise ValueError("Mask differs from declared extraction/configuration")
        reasons = _exclusions(sample, mask)
        if reasons != sample["exclusions"] or sample["admission"] != ("quarantined" if reasons else "auto_admitted"):
            raise ValueError("Inconsistent admission claim")
    readiness = _readiness(dataset["samples"], dataset["contract"])
    if any(dataset[key] != readiness[key] for key in readiness):
        raise ValueError("Inconsistent dataset readiness/support claim")
    if dataset["calibration"] != calibrate_observations(dataset["samples"], output):
        raise ValueError("Inconsistent calibration claim")


def _write_contact_sheet(samples: list[dict], output: Path) -> None:
    panel = Image.new("RGB", (1100, 45 + 145 * len(samples)), "white")
    draw = ImageDraw.Draw(panel)
    draw.text((12, 10), "TD-018 observations: raw | mask overlay | cleaned. Locked-test pixels withheld.", fill="black")
    for index, sample in enumerate(samples):
        top = 40 + index * 145
        label = f"{sample['id']} {sample['split']} {sample['admission']} {sample.get('text') or '[unlabeled]'}"
        draw.text((12, top), label, fill="black")
        draw.text((12, top + 16), ", ".join(sample["exclusions"]) or "Machine admission is not verified reading", fill="black")
        if sample["split"] == "test":
            draw.text((12, top + 45), "LOCKED TEST: inspect only after model/configuration freeze", fill="black")
            continue
        raw = Image.open(output / sample["raw_path"]).convert("RGB")
        mask = np.asarray(Image.open(output / sample["mask_path"]))
        overlay = np.asarray(raw).copy()
        overlay[mask == 128] = (230, 135, 20)
        overlay[(mask == 0) & (_gray(raw) < CONFIG["weak_ink_max"])] = (210, 60, 120)
        images = [raw, Image.fromarray(overlay), Image.open(output / sample["cleaned_path"]).convert("RGB")]
        scale = min(1.5, 310 / raw.width, 100 / raw.height)
        size = (max(1, round(raw.width * scale)), max(1, round(raw.height * scale)))
        for column, image in enumerate(images):
            panel.paste(image.resize(size, Image.Resampling.NEAREST), (12 + column * 360, top + 35))
    panel.save(output / "contact_sheet.png")
    for start in range(0, len(samples), 10):
        top = 40 + start * 145
        page = Image.new("RGB", (1100, min(10, len(samples) - start) * 145 + 45), "white")
        page.paste(panel.crop((0, 0, 1100, 40)), (0, 0))
        page.paste(panel.crop((0, top, 1100, min(panel.height, top + 1450))), (0, 40))
        page.save(output / f"contact_sheet_{start // 10 + 1:02d}.png")


def build_dataset(input_path: Path, output: Path, *, contract: dict) -> dict:
    payload = json.loads(Path(input_path).read_text())
    if payload.get("schema_version") != 2 or not payload.get("sources") or not payload.get("samples"):
        raise ValueError("Nonempty v2 sources and samples required")
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty dataset directory")
    sources, images, contexts, hashes = [], {}, {}, {}
    for source in payload["sources"]:
        if source["id"] in hashes:
            raise ValueError("Duplicate source id")
        path = Path(source["path"])
        if not path.is_absolute():
            path = ROOT / path
        if digest(path) != source["sha256"]:
            raise ValueError("Source hash mismatch")
        image = Image.open(path).copy()
        region = source.get("region", [0, 0, image.width, image.height])
        _bounds(region, image.width, image.height)
        crop = image.crop(region)
        lines = source.get("lines") or detect_lines(crop)
        owners, uncertain = _assign_components(crop, lines)
        contexts[source["id"]] = (region, lines, owners, uncertain)
        hashes[source["id"]] = source["sha256"]
        images[source["id"]] = image
        sources.append({**source, "original_path": source["path"], "region": region, "lines": lines,
                        "path": f"sources/{len(sources):03d}{path.suffix}"})
    if len({source.get("apparent_hand") for source in sources}) != 1 or not sources[0].get("apparent_hand"):
        raise ValueError("Mixed or unidentified apparent source hands require separate datasets")
    _validate_splits(payload["samples"], hashes)
    output.mkdir(parents=True, exist_ok=True)
    (output / "sources").mkdir()
    (output / "words").mkdir()
    for source in sources:
        path = Path(source["original_path"])
        if not path.is_absolute():
            path = ROOT / path
        (output / source["path"]).write_bytes(path.read_bytes())
    samples = []
    for index, incoming in enumerate(payload["samples"]):
        sample = dict(incoming)
        image = images[sample["source_id"]]
        _bounds(sample["bbox"], image.width, image.height)
        region, lines, owners, uncertain = contexts[sample["source_id"]]
        if not isinstance(sample["line_index"], int) or not 0 <= sample["line_index"] < len(lines):
            raise ValueError("Invalid line index")
        left, top, right, bottom = sample["bbox"]
        if left < region[0] or top < region[1] or right > region[2] or bottom > region[3]:
            raise ValueError("Word bounds outside its source column")
        full_mask = _mask_for_line(owners, uncertain, sample["line_index"])
        mask = full_mask[top - region[1]:bottom - region[1], left - region[0]:right - region[0]].copy()
        raw = image.crop(sample["bbox"])
        clean = np.asarray(raw).copy()
        clean[mask != 255] = 255
        line = lines[sample["line_index"]]
        sample.update({"source_to_crop": [1, 0, -left, 0, 1, -top],
                       "normalization": "none; native source pixels and aspect retained",
                       "baseline_native_y": line["baseline_y"] + region[1],
                       "xheight_native_px": line["xheight_px"],
                       "estimate_uncertainty_px": line["uncertainty_px"],
                       "line_assignment_status": sample.get("line_assignment_status", "automatic_unreviewed"),
                       "unknown_fraction": float(np.count_nonzero(mask == 128) / max(1, np.count_nonzero(mask))),
                       "target_ink_pixels": int(np.count_nonzero(mask == 255))})
        for kind, artifact in (("raw", raw), ("mask", Image.fromarray(mask)), ("cleaned", Image.fromarray(clean))):
            relative = f"words/{index:03d}_{kind}.png"
            artifact.save(output / relative)
            sample[kind + "_path"] = relative
            sample[kind + "_sha256"] = digest(output / relative)
        sample["exclusions"] = _exclusions(sample, mask)
        sample["admission"] = "quarantined" if sample["exclusions"] else "auto_admitted"
        samples.append(sample)
    readiness = _readiness(samples, contract)
    dataset = {"schema_version": 2, "hand_id": payload["hand_id"], "sources": sources, "samples": samples,
               "config": CONFIG, "config_sha256": object_digest(CONFIG), "input_sha256": digest(Path(input_path)),
               "extraction_code_sha256": digest(Path(__file__)),
               "environment": {"python": platform.python_version(), "numpy": np.__version__, "pillow": Image.__version__},
               "mask_legend": {"0": "known_background", "128": "unknown", "255": "target_ink"},
               "training_image_policy": "Use raw pixels with the three-state mask; cleaned PNG is a preview only",
               "contract": contract, "contract_sha256": object_digest(contract),
               "human_interventions": payload.get("human_interventions", []),
               "attribution": "apparent hand only; source identity is not historical scribe attribution",
               "admission_semantics": "automatic proposal admission is not verified reading or model promotion",
               "calibration": calibrate_observations(samples, output), **readiness}
    validate_dataset(dataset, output)
    write_json(output / "input_manifest.json", payload)
    write_json(output / "manifest.json", dataset)
    write_json(output / "coverage.json", readiness)
    write_json(output / "calibration.json", dataset["calibration"])
    _write_contact_sheet(samples, output)
    return dataset


def prepare_v1_manifest() -> dict:
    prior = json.loads((ROOT / V1 / "manifest.json").read_text())
    path = ROOT / V1 / "source_bsb00144295_00029.jpg"
    page = Image.open(path)
    region = [680, 210, 1130, min(page.height, 1300)]
    crop = page.crop(region)
    lines = detect_lines(crop)
    old_line_ids = sorted({int(re.search(r"projection line (\d+)", sample["notes"]).group(1)) for sample in prior["samples"]})
    assignments = {}
    for line_id in old_line_ids:
        group = [sample for sample in prior["samples"] if f"projection line {line_id};" in sample["notes"]]
        center = float(np.median([(sample["bbox"][1] + sample["bbox"][3]) / 2 for sample in group])) - region[1]
        assignments[line_id] = min(range(len(lines)), key=lambda index: abs(lines[index]["center_y"] - center))
    heldout = {assignments[int(re.search(r"projection line (\d+)", sample["notes"]).group(1))]
               for sample in prior["samples"] if sample["split"] == "heldout"}
    samples = []
    for original in prior["samples"]:
        old_line = int(re.search(r"projection line (\d+)", original["notes"]).group(1))
        index = assignments[old_line]
        samples.append({"id": original["id"], "source_id": "native29-right", "line_index": index,
                        "bbox": original["bbox"], "split": "development" if index in heldout else "train",
                        "v1_split": original["split"], "text": original["text"],
                        "confidence": original["confidence"], "label_status": "machine_hypothesis",
                        "label_origin": original["label_source"], "mapping_status": "unverified",
                        "visible_mapping": [], "previously_inspected": True,
                        "line_assignment_status": "automatic_unreviewed", "legacy_line_hint": old_line})
    changed = True
    while changed:
        changed = False
        development = {sample["line_index"] for sample in samples if sample["split"] == "development"}
        for sample in samples:
            if sample["split"] == "train" and (sample["line_index"] in development or any(
                    other["split"] == "development" and _overlap(sample["bbox"], other["bbox"]) for other in samples)):
                sample["split"] = "development"
                changed = True
    proposal_mask = _gray(crop) <= CONFIG["strong_ink_max"]
    lower_bound = max(sample["bbox"][3] for sample in samples) + 20
    new_lines = [index for index, line in enumerate(lines) if line["core_top"] + region[1] > lower_bound]
    for line_index in new_lines:
        line = lines[line_index]
        top = max(lower_bound, round(line["center_y"] + region[1] - 13))
        bottom = min(region[3], round(line["center_y"] + region[1] + 14))
        occupied = proposal_mask[top - region[1]:bottom - region[1]].any(axis=0)
        bridged = np.convolve(occupied.astype(int), np.ones(7), mode="same") > 0
        columns = np.nonzero(bridged)[0]
        groups = np.split(columns, np.nonzero(np.diff(columns) > 1)[0] + 1)
        for group in groups:
            if len(group) < 10 or len(samples) >= 60:
                continue
            bounds = [int(group[0]) + region[0], top, int(group[-1]) + region[0] + 1, bottom]
            samples.append({"id": f"native29-proposal-{len(samples):03d}", "source_id": "native29-right",
                            "line_index": line_index, "bbox": bounds,
                            "split": "test" if line_index in new_lines[-2:] else "train",
                            "text": "", "confidence": 0.0, "label_status": "unlabeled",
                            "label_origin": "automatic_projection_proposal", "mapping_status": "unverified",
                            "visible_mapping": [], "previously_inspected": False,
                            "line_assignment_status": "automatic_unreviewed"})
    return {"schema_version": 2, "hand_id": prior["hand_id"], "sources": [{
        "id": "native29-right", "path": str(V1 / path.name), "sha256": digest(path),
        "url": prior["source"]["image_url"], "apparent_hand": prior["hand_id"], "region": region,
        "lines": lines}], "samples": samples, "human_interventions": [],
        "limitations": ["Legacy normalized labels do not specify exact visible forms",
                        "New unlabeled lower-column proposals are quarantined",
                        "Locked test reservations are same-page only; no across-page generalization claim"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, default=ROOT / "shared/training/konrad_hand_recovery/benchmark_v1")
    args = parser.parse_args()
    contract = json.loads((args.benchmark / "contract.json").read_text())
    if args.input is None:
        prepared = args.output.parent / (args.output.name + "_input.json")
        if prepared.exists():
            raise ValueError("Prepared input already exists; select a new version")
        write_json(prepared, prepare_v1_manifest())
        args.input = prepared
    dataset = build_dataset(args.input, args.output, contract=contract)
    baseline = json.loads((args.benchmark / "baseline_manifest.json").read_text())
    decision = evaluate_benchmark(contract, baseline, args.benchmark, dataset=dataset, dataset_root=args.output)
    write_json(args.output / "G0.json", decision)
    print(json.dumps({"samples": len(dataset["samples"]), "admitted": dataset["admitted_count"],
                      "candidate_splits": dataset["candidate_counts"], "G0": decision}, indent=2))


if __name__ == "__main__":
    main()
