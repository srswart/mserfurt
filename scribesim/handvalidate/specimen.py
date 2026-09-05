"""Reproducible TD-018 baseline capture and benchmark readiness evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
V1 = Path("reference/konrad_word_recovery_v1")
BACKENDS = {
    "plain": "scribesim.render.pipeline._render_at_internal_dpi",
    "evo": "scribesim.evo.renderer.render_word_from_genome",
    "v1_fitted": "scribesim.evofit.word_recovery.render_shared_word",
}
MEASUREMENTS = {"image_similarity", "text_mapping_coverage", "appearance_review", "motion_diagnostics"}
RUBRIC = ("letterform_identity", "proportions", "joins_spacing", "hand_coherence", "distortions")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def _read(path: Path) -> dict:
    return json.loads(path.read_text())


def _artifact(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Missing or outside-root artifact: {relative}")
    return path


def validate_contract(contract: dict) -> None:
    if contract.get("schema_version") != 1:
        raise ValueError("Unsupported benchmark schema")
    measurements = contract.get("required_measurements")
    if not measurements or set(measurements) != MEASUREMENTS:
        raise ValueError("Required measurements must distinguish image, text, appearance and motion")
    backends = contract.get("required_backends", [])
    if not backends or len(set(backends)) != len(backends) or set(backends) - BACKENDS.keys():
        raise ValueError("Invalid required backends")
    proofs = contract.get("proofs", [])
    if len(proofs) != 3 or {proof.get("kind") for proof in proofs} != {
        "reconstruction", "unseen", "project_text"
    } or any(not proof.get("text", "").strip() for proof in proofs):
        raise ValueError("Three distinct nonempty proof lines are required")
    if contract.get("split_policy") != "source_line_disjoint_test_locked":
        raise ValueError("Split policy must reserve disjoint locked test material")
    if set(contract.get("rubric", [])) != set(RUBRIC):
        raise ValueError("Appearance rubric is incomplete")
    if not contract.get("calibration_protocol") or not contract.get("source_sha256"):
        raise ValueError("Source identity and calibration protocol required")


def verify_baseline(record: dict, output: Path) -> None:
    try:
        if BACKENDS.get(record["backend"]) != record["entrypoint"]:
            raise ValueError("Mislabeled baseline backend")
        for field in ("image", "model", "source", "code", "config"):
            relative = record[field + "_path"]
            if digest(_artifact(output, relative)) != record[field + "_sha256"]:
                raise ValueError(f"Baseline {field} hash mismatch")
        config = _read(_artifact(output, record["config_path"]))
        if config["backend"] != record["backend"] or config["model_sha256"] != record["model_sha256"]:
            raise ValueError("Baseline configuration identity mismatch")
        if not record["fresh_process"] or not record["command"] or not record["environment"]:
            raise ValueError("Baseline execution provenance missing")
        replay = _artifact(output, record["replay_path"])
        if (digest(replay) == record["image_sha256"]) != record["same_seed_replay"]:
            raise ValueError("Baseline replay claim mismatch")
    except (KeyError, TypeError) as error:
        raise ValueError("Incomplete baseline record") from error


def evaluate_benchmark(contract: dict, manifest: dict, output: Path,
                       dataset: dict | None = None, review: dict | None = None) -> dict:
    validate_contract(contract)
    blocked, failures = [], []
    records = manifest.get("baselines", [])
    if not records or {record.get("backend") for record in records} != set(contract["required_backends"]):
        blocked.append("required_baselines_missing")
    for record in records:
        try:
            verify_baseline(record, output)
        except ValueError as error:
            failures.append(str(error))
    if review is None or not review.get("reviewer") or not review.get("date"):
        blocked.append("target_review_missing")
    elif review.get("contract_sha256") != object_digest(contract):
        failures.append("target_review_identity_mismatch")
    elif review.get("decision") == "revise":
        failures.append("target_revision_requested")
    elif review.get("decision") != "acceptable":
        blocked.append("target_review_unresolved")
    if dataset is None:
        blocked.append("dataset_missing")
    else:
        if dataset.get("contract_sha256") != object_digest(contract):
            failures.append("dataset_contract_identity_mismatch")
        if not dataset.get("samples"):
            blocked.append("dataset_empty")
        if dataset.get("status") != "pass":
            blocked.extend(dataset.get("reasons") or ["dataset_not_ready"])
        if not all(dataset.get("split_counts", {}).get(split, 0) > 0 for split in ("train", "development", "test")):
            blocked.append("split_coverage_missing")
        if not dataset.get("calibration", {}).get("status") == "pass":
            blocked.append("calibration_missing")
    return {
        "gate": "G0", "status": "fail" if failures else "blocked" if blocked else "pass",
        "reasons": sorted(set(failures + blocked)), "promoted": False,
        "contract_sha256": object_digest(contract),
        "scope": "benchmark readiness; no model, readability or historical approval",
    }


def write_equal_scale_panel(tiles: list[tuple[str, Image.Image, float]], output: Path) -> dict:
    if not tiles or any(not math.isfinite(height) or height <= 0 for _, _, height in tiles):
        raise ValueError("A positive x-height estimate is required for every tile")
    target = max(height for _, _, height in tiles)
    sizes = [(max(1, round(image.width * target / height)), max(1, round(image.height * target / height)))
             for _, image, height in tiles]
    width = max(size[0] for size in sizes) + 40
    height = sum(size[1] + 50 for size in sizes) + 30
    panel = Image.new("RGB", (max(660, width), height), "white")
    draw = ImageDraw.Draw(panel)
    cursor = 15
    for (label, image, _), size in zip(tiles, sizes):
        draw.text((15, cursor), label, fill="black")
        panel.paste(image.convert("RGB").resize(size, Image.Resampling.LANCZOS), (15, cursor + 22))
        cursor += size[1] + 50
    panel.save(output)
    return {"pixels_per_xheight": target, "tile_sizes": [list(size) for size in sizes],
            "scaling": "one isotropic scale per declared x-height; no independent box fitting"}


def _code_identity() -> dict:
    names = subprocess.check_output(["git", "ls-files", "scribesim", "shared/hands"], cwd=ROOT, text=True).splitlines()
    names.append("scribesim/handvalidate/specimen.py")
    hashes = {name: digest(ROOT / name) for name in sorted(set(names)) if (ROOT / name).is_file()}
    return {"files": hashes, "sha256": object_digest(hashes)}


def render_worker(backend: str, output: Path) -> None:
    from scribesim.evofit.word_recovery import assemble_word, render_shared_word, seed_hand

    random.seed(42)
    model = _read(output / "model.json")
    text = "und"
    if backend == "v1_fitted":
        image = Image.fromarray(render_shared_word(text, model, dpi=180))
        xheight = model["x_height_mm"] * 180 / 25.4
    elif backend == "evo":
        from scribesim.evo.renderer import render_word_from_genome

        genome = assemble_word(text, model)
        genome.baseline_y = 10.0
        for glyph in genome.glyphs:
            for segment in glyph.segments:
                for name in ("p0", "p1", "p2", "p3"):
                    coordinate = getattr(segment, name)
                    setattr(segment, name, (coordinate[0], coordinate[1] + genome.baseline_y))
        image = Image.fromarray(render_word_from_genome(
            genome, dpi=180, nib_width_mm=model["nib_width_mm"], variation=0,
        ))
        xheight = model["x_height_mm"] * 180 / 25.4
    else:
        from scribesim.glyphs.catalog import GLYPH_CATALOG
        from scribesim.hand.params import HandParams
        from scribesim.layout.geometry import PageGeometry
        from scribesim.layout.positioned import LineLayout, PageLayout, PositionedGlyph
        from scribesim.render.pipeline import _INTERNAL_DPI, _render_at_internal_dpi

        geometry = PageGeometry(24, 16, 3, 3, 3, 3, 8, 3.8, "benchmark")
        cursor, glyphs = 3.0, []
        for character in text:
            glyph = GLYPH_CATALOG[character]
            advance = glyph.advance_width * geometry.x_height_mm
            glyphs.append(PositionedGlyph(character, cursor, 4.2, 8.0, advance))
            cursor += advance + 0.08 * geometry.x_height_mm
        layout = PageLayout("td018-und", geometry, [LineLayout(0, 8, glyphs)])
        image, _ = _render_at_internal_dpi(layout, HandParams(**model["hand_params"]))
        image = image.resize((round(image.width * 180 / _INTERNAL_DPI),
                              round(image.height * 180 / _INTERNAL_DPI)), Image.Resampling.LANCZOS)
        xheight = geometry.x_height_mm * 180 / 25.4
    image.save(output / "image.png", dpi=(180, 180))
    write_json(output / "worker.json", {
        "backend": backend, "entrypoint": BACKENDS[backend], "xheight_px": xheight,
        "pid": os.getpid(), "python": platform.python_version(),
        "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
        "scope": "word raster smoke, not full default CLI/folio or optimization run",
    })


def _capture(backend: str, output: Path) -> dict:
    from scribesim.evofit.word_recovery import seed_hand
    from scribesim.hand.params import HandParams

    folder = output / backend
    folder.mkdir()
    model = (_read(ROOT / V1 / "evidence/learned_hand.json") if backend == "v1_fitted"
             else {"hand_params": HandParams(nib_width_mm=0.6).to_dict()} if backend == "plain"
             else seed_hand("und"))
    write_json(folder / "model.json", model)
    write_json(folder / "code.json", _code_identity())
    config = {"backend": backend, "text": "und", "seed": 42, "dpi": 180,
              "model_sha256": digest(folder / "model.json"), "python_hash_seed": "42",
              "baseline_y_mm": 10.0 if backend == "evo" else 8.0 if backend == "plain" else 0.0}
    write_json(folder / "config.json", config)
    source = ROOT / V1 / "source_bsb00144295_00029.jpg"
    (folder / "source.jpg").write_bytes(source.read_bytes())
    command = [sys.executable, "-m", "scribesim.handvalidate.specimen", "worker",
               "--backend", backend, "--output", str(folder)]
    for iteration, hash_seed in enumerate(("42", "42", "43")):
        subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONHASHSEED": hash_seed},
                       check=True, capture_output=True, text=True, timeout=120)
        if iteration == 0:
            (folder / "original.png").write_bytes((folder / "image.png").read_bytes())
            first_worker = _read(folder / "worker.json")
        elif iteration == 1:
            (folder / "replay.png").write_bytes((folder / "image.png").read_bytes())
        else:
            (folder / "alternate_hash_seed.png").write_bytes((folder / "image.png").read_bytes())
    (folder / "image.png").write_bytes((folder / "original.png").read_bytes())
    write_json(folder / "worker.json", first_worker)
    record = {"backend": backend, "entrypoint": first_worker["entrypoint"], "fresh_process": True,
              "command": command, "environment": {"PYTHONHASHSEED": "42", "random_seed": 42,
              "python": first_worker["python"], "numpy": np.__version__},
              "xheight_px": first_worker["xheight_px"], "scope": first_worker["scope"],
              "replay_path": f"{backend}/replay.png",
              "same_seed_replay": digest(folder / "image.png") == digest(folder / "replay.png"),
              "hash_seed_independent": digest(folder / "image.png") == digest(folder / "alternate_hash_seed.png")}
    for field, filename in (("image", "image.png"), ("model", "model.json"), ("source", "source.jpg"),
                            ("code", "code.json"), ("config", "config.json")):
        record[field + "_path"] = f"{backend}/{filename}"
        record[field + "_sha256"] = digest(folder / filename)
    return record


def build_benchmark(output: Path, backends: tuple[str, ...] = tuple(BACKENDS)) -> dict:
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Benchmark output must be empty; use a new immutable run directory")
    output.mkdir(parents=True, exist_ok=True)
    report = _read(ROOT / V1 / "evidence/report.json")
    source_manifest = _read(ROOT / V1 / "manifest.json")
    contract = {
        "schema_version": 1, "id": "konrad-benchmark-v1", "required_backends": list(backends),
        "required_measurements": sorted(MEASUREMENTS), "rubric": list(RUBRIC),
        "split_policy": "source_line_disjoint_test_locked",
        "source_sha256": digest(ROOT / V1 / "source_bsb00144295_00029.jpg"),
        "source_manifest_sha256": digest(ROOT / V1 / "manifest.json"),
        "proofs": [
            {"kind": "reconstruction", "text": "alle das ist", "label_status": "machine_hypotheses"},
            {"kind": "unseen", "text": "dein lied deine hand rein", "label_status": "synthetic_unscored"},
            {"kind": "project_text", "text": "Hie hebt sich an, das ein schreiber nit mag laßen zu",
             "source": "output-live/f01r.json:line1", "label_status": "project_text"},
        ],
        "calibration_protocol": {
            "status": "pending_clean_dataset", "tune_on": ["train", "development"],
            "controls": ["correct", "wrong_letter", "filled_counter", "extra_stroke", "distorted_aspect"],
            "freeze_before_test": True, "unknown_fraction_max": 0.35,
            "symbol_training_instances_min": 3, "symbol_training_word_contexts_min": 2,
            "initial_instance_target": [30, 60],
            "note": "Mask/support limits are engineering admission rules, not calibrated image-quality thresholds.",
        },
        "target_review": "pending", "independent_reading": "unverified",
        "locked_test_reservation": {"status": "unfilled", "exclude": "all inspected v1 source lines"},
    }
    validate_contract(contract)
    write_json(output / "contract.json", contract)
    records = [_capture(backend, output) for backend in backends]
    identity = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    diff = subprocess.check_output(["git", "diff", "HEAD"], cwd=ROOT)
    manifest = {"schema_version": 1, "baselines": records, "commit": identity,
                "dirty_patch_sha256": hashlib.sha256(diff).hexdigest(),
                "code_identity_includes_working_files": True}
    (output / "working.patch").write_bytes(diff)
    write_json(output / "baseline_manifest.json", manifest)
    prior = {
        "advance_status": "in_progress", "decision": report["decision"],
        "report_path": str(V1 / "evidence/report.json"),
        "report_sha256": digest(ROOT / V1 / "evidence/report.json"),
        "counts": {"training": report["training"]["count"], "heldout": report["heldout"]["count"]},
        "image_losses": {key: report[key] for key in ("training", "heldout", "heldout_novel_word")},
        "exclusions": [{"id": row["id"], "reason": row["exclusion"]} for row in report["samples"] if row["exclusion"]],
        "heldout_reuse_policy": "development_only", "historical_readability_evidence": "none",
        "remaining_work": ["Reconcile EVOFIT-004 checklist and implementation status with owner workflow",
                           "Machine readings and apparent-hand attribution are still unverified",
                           "Archive actual focused test commands; no provider CI or owner approval inferred"],
    }
    write_json(output / "prior_experiment.json", prior)
    page = Image.open(ROOT / V1 / "source_bsb00144295_00029.jpg").convert("RGB")
    samples = {sample["text"]: sample for sample in source_manifest["samples"]}
    tiles = []
    for word in ("und", "alle", "das", "ist"):
        crop = page.crop(samples[word]["bbox"])
        tiles.append((f"Source hypothesis: {word}; x-height estimate 18 native px, unreviewed", crop, 18.0))
    for record in records:
        tiles.append((f"{record['backend']}: und; fresh word-raster smoke", Image.open(output / record["image_path"]),
                      record["xheight_px"]))
    panel = write_equal_scale_panel(tiles, output / "target_sheet.png")
    write_json(output / "target_sheet.json", {**panel, "source_xheight_status": "provisional_visual_estimate",
               "target_sheet_sha256": digest(output / "target_sheet.png"), "review": "pending"})
    train_alphabet = set(_read(ROOT / V1 / "evidence/learned_hand.json")["glyphs"])
    write_json(output / "coverage_debt.json", {
        "scope": "v1 logical inventory only; graphic forms and correct reading unverified",
        "proofs": [{"kind": proof["kind"], "unsupported": sorted(set(proof["text"]) - train_alphabet - {" "})}
                   for proof in contract["proofs"]],
        "fresh_test_material": "required; v1 held-out images have already been inspected",
    })
    decision = evaluate_benchmark(contract, manifest, output)
    write_json(output / "G0.json", decision)
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "worker"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=tuple(BACKENDS))
    args = parser.parse_args()
    if args.action == "worker":
        if not args.backend:
            parser.error("worker requires --backend")
        render_worker(args.backend, args.output)
    else:
        print(json.dumps(build_benchmark(args.output), indent=2))


if __name__ == "__main__":
    main()
