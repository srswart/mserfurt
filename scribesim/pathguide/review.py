"""Dataset review helpers for starter alphabet pathguides."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from scribesim.handvalidate.model import StageReport
from scribesim.handvalidate.report import stage_report_markdown, stage_report_to_dict
from scribesim.pathguide.model import DensePathGuide
from scribesim.pathguide.validate import validate_dense_path_guide


def starter_dataset_metrics(
    guides: dict[str, DensePathGuide],
    *,
    required_symbols: tuple[str, ...],
    join_schedules: dict[str, str],
) -> dict[str, float]:
    """Compute deterministic dataset-level metrics for pathguide promotion."""

    from scribesim.handvalidate.metrics import dataset_admission_metrics

    total = max(len(guides), 1)
    glyph_count = sum(1 for guide in guides.values() if guide.kind == "glyph")
    join_count = sum(1 for guide in guides.values() if guide.kind == "join")
    structurally_valid = 0
    self_intersection_free = 0
    accepted_only = 0
    join_schedule_count = 0

    for symbol, guide in guides.items():
        errors = validate_dense_path_guide(guide)
        if not errors:
            structurally_valid += 1
        if not any("self-intersect" in error for error in errors):
            self_intersection_free += 1
        if guide.accepted_only:
            accepted_only += 1
        if guide.kind == "join" and join_schedules.get(symbol):
            join_schedule_count += 1

    admission = dataset_admission_metrics(guides.values())
    required_present = len(set(required_symbols) & set(guides))

    metrics = {
        "guide_count": float(len(guides)),
        "glyph_count": float(glyph_count),
        "join_count": float(join_count),
        "required_symbol_coverage": required_present / max(len(required_symbols), 1),
        "structural_validity_ratio": structurally_valid / total,
        "self_intersection_free_ratio": self_intersection_free / total,
        "accepted_source_ratio": accepted_only / total,
        "join_schedule_ratio": 1.0 if join_count == 0 else join_schedule_count / join_count,
    }
    metrics.update(admission)
    return metrics


def build_starter_dataset_report(
    guides: dict[str, DensePathGuide],
    *,
    required_symbols: tuple[str, ...],
    join_schedules: dict[str, str],
    dataset_policy_name: str = "promotion",
    gate_stage: str = "pathguide_dataset",
) -> StageReport:
    """Build a starter-alphabet validation report."""

    from scribesim.handvalidate.gates import evaluate_dataset_policy, evaluate_gate

    metrics = starter_dataset_metrics(
        guides,
        required_symbols=required_symbols,
        join_schedules=join_schedules,
    )
    gate = evaluate_gate(gate_stage, metrics)
    dataset_policy = evaluate_dataset_policy(list(guides.values()), policy_name=dataset_policy_name)
    return StageReport(
        stage=gate_stage,
        metrics=metrics,
        gate=gate,
        dataset_policy=dataset_policy_name,
        dataset_policy_passed=dataset_policy.passed,
        dataset_policy_reasons=dataset_policy.reasons,
    )


def write_dataset_report_bundle(
    report: StageReport,
    output_dir: Path | str,
    *,
    stem: str = "validation_report",
) -> tuple[Path, Path]:
    """Write JSON and Markdown validation reports with stable filenames."""

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / f"{stem}.json"
    markdown_path = output_root / f"{stem}.md"
    rendered = StageReport(
        stage=stem,
        metrics=report.metrics,
        gate=report.gate,
        dataset_policy=report.dataset_policy,
        dataset_policy_passed=report.dataset_policy_passed,
        dataset_policy_reasons=report.dataset_policy_reasons,
        notes=report.notes,
    )
    json_path.write_text(json.dumps(stage_report_to_dict(rendered), indent=2, sort_keys=True) + "\n")
    markdown_path.write_text(stage_report_markdown(rendered))
    return json_path, markdown_path


def _guide_bounds(guide: DensePathGuide) -> tuple[float, float, float, float]:
    min_x = min(sample.x_mm - sample.corridor_half_width_mm for sample in guide.samples)
    min_y = min(sample.y_mm - sample.corridor_half_width_mm for sample in guide.samples)
    max_x = max(sample.x_mm + sample.corridor_half_width_mm for sample in guide.samples)
    max_y = max(sample.y_mm + sample.corridor_half_width_mm for sample in guide.samples)
    return min_x, min_y, max_x, max_y


def write_guide_overlay_snapshot(
    guide: DensePathGuide,
    output_path: Path | str,
    *,
    px_per_mm: int = 120,
    padding_px: int = 28,
) -> Path:
    """Write a human-reviewable corridor and centerline overlay snapshot."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    min_x, min_y, max_x, max_y = _guide_bounds(guide)
    width_px = max(int((max_x - min_x) * px_per_mm) + padding_px * 2, 220)
    height_px = max(int((max_y - min_y) * px_per_mm) + padding_px * 2 + 24, 180)
    image = Image.new("RGBA", (width_px, height_px), (247, 241, 229, 255))
    draw = ImageDraw.Draw(image, "RGBA")

    def to_px(x_mm: float, y_mm: float) -> tuple[int, int]:
        x_px = padding_px + int(round((x_mm - min_x) * px_per_mm))
        y_px = height_px - padding_px - int(round((y_mm - min_y) * px_per_mm))
        return x_px, y_px

    for sample in guide.samples:
        x_px, y_px = to_px(sample.x_mm, sample.y_mm)
        radius_px = max(int(round(sample.corridor_half_width_mm * px_per_mm)), 4)
        fill = (186, 168, 139, 62) if sample.contact else (158, 168, 184, 48)
        outline = (160, 140, 110, 120) if sample.contact else (130, 140, 155, 90)
        draw.ellipse(
            (x_px - radius_px, y_px - radius_px, x_px + radius_px, y_px + radius_px),
            fill=fill,
            outline=outline,
            width=1,
        )

    for idx in range(len(guide.samples) - 1):
        a = guide.samples[idx]
        b = guide.samples[idx + 1]
        color = (62, 38, 18, 255) if a.contact and b.contact else (102, 115, 126, 220)
        width = 4 if a.contact and b.contact else 2
        draw.line((*to_px(a.x_mm, a.y_mm), *to_px(b.x_mm, b.y_mm)), fill=color, width=width)

    if guide.samples:
        first = to_px(guide.samples[0].x_mm, guide.samples[0].y_mm)
        last = to_px(guide.samples[-1].x_mm, guide.samples[-1].y_mm)
        draw.ellipse((first[0] - 5, first[1] - 5, first[0] + 5, first[1] + 5), fill=(25, 112, 65, 255))
        draw.ellipse((last[0] - 5, last[1] - 5, last[0] + 5, last[1] + 5), fill=(157, 44, 44, 255))

    draw.text((padding_px, 8), f"{guide.symbol} [{guide.kind}]", fill=(46, 34, 22, 255))
    image.convert("RGB").save(output_path, format="PNG")
    return output_path


def write_nominal_guide_snapshot(
    guide: DensePathGuide,
    output_path: Path | str,
    *,
    target_size: tuple[int, int] = (160, 160),
    padding_px: int = 14,
) -> Path:
    """Write a direct nominal-render snapshot without corridor overlays."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    min_x, min_y, max_x, max_y = _guide_bounds(guide)
    width_mm = max(max_x - min_x, 0.1)
    height_mm = max(max_y - min_y, 0.1)
    inner_w = max(20, target_size[0] - padding_px * 2)
    inner_h = max(20, target_size[1] - padding_px * 2)
    px_per_mm = min(inner_w / width_mm, inner_h / height_mm)

    image = Image.new("RGB", target_size, (255, 255, 255))
    draw = ImageDraw.Draw(image)

    def to_px(x_mm: float, y_mm: float) -> tuple[int, int]:
        x_px = padding_px + int(round((x_mm - min_x) * px_per_mm))
        y_px = target_size[1] - padding_px - int(round((y_mm - min_y) * px_per_mm))
        return x_px, y_px

    for idx in range(len(guide.samples) - 1):
        a = guide.samples[idx]
        b = guide.samples[idx + 1]
        color = (0, 0, 0) if a.contact and b.contact else (160, 160, 160)
        width = max(1, int(round((a.corridor_half_width_mm + b.corridor_half_width_mm) * 0.5 * px_per_mm * 0.7)))
        draw.line((*to_px(a.x_mm, a.y_mm), *to_px(b.x_mm, b.y_mm)), fill=color, width=width)

    image.save(output_path, format="PNG")
    return output_path


def write_snapshot_panel(
    image_paths: list[Path],
    output_path: Path | str,
    *,
    columns: int = 4,
    cell_padding: int = 14,
    title_height: int = 22,
) -> Path:
    """Assemble per-symbol overlay snapshots into one review panel."""

    if not image_paths:
        raise ValueError("image_paths must be non-empty")

    opened = [(path.stem, Image.open(path).convert("RGB")) for path in image_paths]
    cell_w = max(image.width for _, image in opened)
    cell_h = max(image.height for _, image in opened)
    rows = (len(opened) + columns - 1) // columns
    panel = Image.new(
        "RGB",
        (
            columns * (cell_w + cell_padding) + cell_padding,
            rows * (cell_h + title_height + cell_padding) + cell_padding,
        ),
        (247, 241, 229),
    )
    draw = ImageDraw.Draw(panel)

    for idx, (label, image) in enumerate(opened):
        row = idx // columns
        col = idx % columns
        x = cell_padding + col * (cell_w + cell_padding)
        y = cell_padding + row * (cell_h + title_height + cell_padding)
        draw.text((x, y), label, fill=(40, 30, 20))
        panel.paste(image, (x, y + title_height))

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.save(output_path, format="PNG")
    for _, image in opened:
        image.close()
    return output_path


def _quoted_list(values: tuple[str, ...] | list[str]) -> str:
    return "[" + ", ".join(f'"{value}"' for value in values) + "]"


def _snapshot_stem(symbol: str) -> str:
    return symbol.replace("->", "_to_").replace(" ", "_")


def build_active_folio_inventory_report(
    guides: dict[str, DensePathGuide],
    *,
    required_symbols: tuple[str, ...],
    review_folios: tuple[dict[str, object], ...],
) -> dict[str, object]:
    """Build a review-slice coverage report for the active folio dataset."""

    present = [symbol for symbol in required_symbols if symbol in guides]
    missing = [symbol for symbol in required_symbols if symbol not in guides]
    return {
        "review_folios": [
            {
                "folio_id": str(spec["folio_id"]),
                "folio_path": str(spec["folio_path"]),
                "line_numbers": list(spec["line_numbers"]),
            }
            for spec in review_folios
        ],
        "required_symbols": list(required_symbols),
        "present_symbols": present,
        "missing_symbols": missing,
        "exact_character_coverage": len(present) / max(len(required_symbols), 1),
    }


def write_active_folio_inventory_report_bundle(
    report: dict[str, object],
    output_dir: Path | str,
    *,
    stem: str = "coverage_report",
) -> tuple[Path, Path]:
    """Write JSON and Markdown review-slice coverage reports."""

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / f"{stem}.json"
    markdown_path = output_root / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = [
        f"# {stem.replace('_', ' ').title()}",
        "",
        f"- exact_character_coverage: {report['exact_character_coverage']:.4f}",
        f"- required_symbol_count: {len(report['required_symbols'])}",
        f"- missing_symbol_count: {len(report['missing_symbols'])}",
        "",
        "## Review folios",
    ]
    for spec in report["review_folios"]:
        lines.append(
            f"- {spec['folio_id']}: {spec['folio_path']} lines {', '.join(str(v) for v in spec['line_numbers'])}"
        )
    lines.extend(
        [
            "",
            "## Required symbols",
            "",
            ", ".join(report["required_symbols"]),
            "",
            "## Missing symbols",
            "",
            ", ".join(report["missing_symbols"]) if report["missing_symbols"] else "(none)",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines))
    return json_path, markdown_path


def write_starter_alphabet_v1_bundle(
    output_root: Path | str = "shared/training/handsim/starter_alphabet_v1",
) -> dict[str, Path]:
    """Write the canonical starter-alphabet-v1 dataset assets."""

    from scribesim.pathguide.catalog import (
        STARTER_ALPHABET_V1_GLYPHS,
        STARTER_ALPHABET_V1_JOIN_SCHEDULES,
        STARTER_ALPHABET_V1_JOINS,
        STARTER_ALPHABET_V1_PATH,
        STARTER_ALPHABET_V1_PROOF_WORDS,
        STARTER_ALPHABET_V1_REQUIRED_SYMBOLS,
        STARTER_ALPHABET_V1_SOURCE_MODES,
        STARTER_ALPHABET_V1_SPLITS,
        build_starter_alphabet_v1_confidence_manifest,
        build_starter_alphabet_v1_guides,
    )
    from scribesim.pathguide.io import write_pathguides_toml

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    snapshots_dir = output_root / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    guides = build_starter_alphabet_v1_guides()
    write_pathguides_toml(guides, STARTER_ALPHABET_V1_PATH)

    snapshot_paths: dict[str, Path] = {}
    for symbol in STARTER_ALPHABET_V1_REQUIRED_SYMBOLS:
        path = snapshots_dir / f"{_snapshot_stem(symbol)}.png"
        snapshot_paths[symbol] = write_guide_overlay_snapshot(guides[symbol], path)
    panel_path = write_snapshot_panel(
        [snapshot_paths[symbol] for symbol in STARTER_ALPHABET_V1_REQUIRED_SYMBOLS],
        snapshots_dir / "panel.png",
    )

    report = build_starter_dataset_report(
        guides,
        required_symbols=STARTER_ALPHABET_V1_REQUIRED_SYMBOLS,
        join_schedules=STARTER_ALPHABET_V1_JOIN_SCHEDULES,
    )
    report_json, report_md = write_dataset_report_bundle(report, output_root)

    confidence_manifest = build_starter_alphabet_v1_confidence_manifest()
    confidence_lines = [
        "# TD-014 starter alphabet confidence manifest",
        "",
    ]
    for symbol in STARTER_ALPHABET_V1_REQUIRED_SYMBOLS:
        entry = confidence_manifest[symbol]
        confidence_lines.append(f'[symbols."{symbol}"]')
        confidence_lines.append(f'kind = "{entry["kind"]}"')
        confidence_lines.append(f'split = "{entry["split"]}"')
        confidence_lines.append(f'source_mode = "{entry["source_mode"]}"')
        if entry["contact_schedule"] is not None:
            confidence_lines.append(f'contact_schedule = "{entry["contact_schedule"]}"')
        counts = entry["counts"]
        confidence_lines.append(f'accepted = {counts["accepted"]}')
        confidence_lines.append(f'soft_accepted = {counts["soft_accepted"]}')
        confidence_lines.append(f'rejected = {counts["rejected"]}')
        confidence_lines.append("")
    confidence_path = output_root / "confidence_manifest.toml"
    confidence_path.write_text("\n".join(confidence_lines))

    manifest_lines = [
        "# TD-014 starter alphabet dataset manifest",
        'dataset_id = "starter-alphabet-v1"',
        'source_policy = "automatic-first"',
        f'guide_catalog_path = "{STARTER_ALPHABET_V1_PATH.as_posix()}"',
        f'validation_report_json_path = "{report_json.as_posix()}"',
        f'validation_report_md_path = "{report_md.as_posix()}"',
        f'confidence_manifest_path = "{confidence_path.as_posix()}"',
        f'snapshot_panel_path = "{panel_path.as_posix()}"',
        f"glyphs = {_quoted_list(list(STARTER_ALPHABET_V1_GLYPHS))}",
        f"joins = {_quoted_list(list(STARTER_ALPHABET_V1_JOINS))}",
        "",
        "[proof_words]",
        f"train = {_quoted_list(list(STARTER_ALPHABET_V1_PROOF_WORDS['train']))}",
        f"validation = {_quoted_list(list(STARTER_ALPHABET_V1_PROOF_WORDS['validation']))}",
        f"test = {_quoted_list(list(STARTER_ALPHABET_V1_PROOF_WORDS['test']))}",
        "",
    ]
    for symbol in STARTER_ALPHABET_V1_REQUIRED_SYMBOLS:
        manifest_lines.append("[[symbols]]")
        manifest_lines.append(f'symbol = "{symbol}"')
        manifest_lines.append(f'kind = "{guides[symbol].kind}"')
        manifest_lines.append(f'split = "{STARTER_ALPHABET_V1_SPLITS[symbol]}"')
        manifest_lines.append(f'source_mode = "{STARTER_ALPHABET_V1_SOURCE_MODES[symbol]}"')
        if symbol in STARTER_ALPHABET_V1_JOIN_SCHEDULES:
            manifest_lines.append(f'contact_schedule = "{STARTER_ALPHABET_V1_JOIN_SCHEDULES[symbol]}"')
        manifest_lines.append(f'snapshot_path = "{snapshot_paths[symbol].as_posix()}"')
        manifest_lines.append("")
    manifest_path = output_root / "manifest.toml"
    manifest_path.write_text("\n".join(manifest_lines))

    return {
        "guide_catalog_path": STARTER_ALPHABET_V1_PATH,
        "manifest_path": manifest_path,
        "confidence_manifest_path": confidence_path,
        "report_json_path": report_json,
        "report_md_path": report_md,
        "snapshot_panel_path": panel_path,
    }


def write_active_folio_alphabet_v1_bundle(
    output_root: Path | str = "shared/training/handsim/active_folio_alphabet_v1",
) -> dict[str, Path]:
    """Write the canonical active-folio-alphabet-v1 dataset assets."""

    from scribesim.pathguide.catalog import (
        ACTIVE_FOLIO_ALPHABET_V1_GLYPHS,
        ACTIVE_FOLIO_ALPHABET_V1_NEW_GLYPHS,
        ACTIVE_FOLIO_ALPHABET_V1_PATH,
        ACTIVE_FOLIO_ALPHABET_V1_PROOF_WORDS,
        ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS,
        ACTIVE_FOLIO_ALPHABET_V1_REVIEW_FOLIOS,
        ACTIVE_FOLIO_ALPHABET_V1_SOURCE_MODES,
        ACTIVE_FOLIO_ALPHABET_V1_SPLITS,
        build_active_folio_alphabet_v1_confidence_manifest,
        build_active_folio_alphabet_v1_guides,
    )
    from scribesim.pathguide.io import write_pathguides_toml

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    snapshots_dir = output_root / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    guides = build_active_folio_alphabet_v1_guides()
    write_pathguides_toml(guides, ACTIVE_FOLIO_ALPHABET_V1_PATH)

    snapshot_paths: dict[str, Path] = {}
    for symbol in ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS:
        path = snapshots_dir / f"{_snapshot_stem(symbol)}.png"
        snapshot_paths[symbol] = write_guide_overlay_snapshot(guides[symbol], path)
    panel_path = write_snapshot_panel(
        [snapshot_paths[symbol] for symbol in ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS],
        snapshots_dir / "panel.png",
        columns=5,
    )

    report = build_starter_dataset_report(
        guides,
        required_symbols=ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS,
        join_schedules={},
    )
    report_json, report_md = write_dataset_report_bundle(report, output_root)
    coverage = build_active_folio_inventory_report(
        guides,
        required_symbols=ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS,
        review_folios=ACTIVE_FOLIO_ALPHABET_V1_REVIEW_FOLIOS,
    )
    coverage_json, coverage_md = write_active_folio_inventory_report_bundle(coverage, output_root)

    confidence_manifest = build_active_folio_alphabet_v1_confidence_manifest()
    confidence_lines = [
        "# TD-014 active folio alphabet confidence manifest",
        "",
    ]
    for symbol in ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS:
        entry = confidence_manifest[symbol]
        confidence_lines.append(f'[symbols."{symbol}"]')
        confidence_lines.append(f'kind = "{entry["kind"]}"')
        confidence_lines.append(f'split = "{entry["split"]}"')
        confidence_lines.append(f'source_mode = "{entry["source_mode"]}"')
        counts = entry["counts"]
        confidence_lines.append(f'accepted = {counts["accepted"]}')
        confidence_lines.append(f'soft_accepted = {counts["soft_accepted"]}')
        confidence_lines.append(f'rejected = {counts["rejected"]}')
        confidence_lines.append("")
    confidence_path = output_root / "confidence_manifest.toml"
    confidence_path.write_text("\n".join(confidence_lines))

    manifest_lines = [
        "# TD-014 active folio alphabet dataset manifest",
        'dataset_id = "active-folio-alphabet-v1"',
        'source_policy = "automatic-first"',
        f'guide_catalog_path = "{ACTIVE_FOLIO_ALPHABET_V1_PATH.as_posix()}"',
        f'validation_report_json_path = "{report_json.as_posix()}"',
        f'validation_report_md_path = "{report_md.as_posix()}"',
        f'coverage_report_json_path = "{coverage_json.as_posix()}"',
        f'coverage_report_md_path = "{coverage_md.as_posix()}"',
        f'confidence_manifest_path = "{confidence_path.as_posix()}"',
        f'snapshot_panel_path = "{panel_path.as_posix()}"',
        f"glyphs = {_quoted_list(list(ACTIVE_FOLIO_ALPHABET_V1_GLYPHS))}",
        f"new_glyphs = {_quoted_list(list(ACTIVE_FOLIO_ALPHABET_V1_NEW_GLYPHS))}",
        "",
        "[proof_words]",
        f"train = {_quoted_list(list(ACTIVE_FOLIO_ALPHABET_V1_PROOF_WORDS['train']))}",
        f"validation = {_quoted_list(list(ACTIVE_FOLIO_ALPHABET_V1_PROOF_WORDS['validation']))}",
        f"test = {_quoted_list(list(ACTIVE_FOLIO_ALPHABET_V1_PROOF_WORDS['test']))}",
        "",
    ]
    for spec in ACTIVE_FOLIO_ALPHABET_V1_REVIEW_FOLIOS:
        manifest_lines.append("[[review_folios]]")
        manifest_lines.append(f'folio_id = "{spec["folio_id"]}"')
        manifest_lines.append(f'folio_path = "{spec["folio_path"]}"')
        manifest_lines.append(f'line_numbers = [{", ".join(str(value) for value in spec["line_numbers"])}]')
        manifest_lines.append("")
    for symbol in ACTIVE_FOLIO_ALPHABET_V1_REQUIRED_SYMBOLS:
        manifest_lines.append("[[symbols]]")
        manifest_lines.append(f'symbol = "{symbol}"')
        manifest_lines.append(f'kind = "{guides[symbol].kind}"')
        manifest_lines.append(f'split = "{ACTIVE_FOLIO_ALPHABET_V1_SPLITS[symbol]}"')
        manifest_lines.append(f'source_mode = "{ACTIVE_FOLIO_ALPHABET_V1_SOURCE_MODES[symbol]}"')
        manifest_lines.append(f'snapshot_path = "{snapshot_paths[symbol].as_posix()}"')
        manifest_lines.append("")
    manifest_path = output_root / "manifest.toml"
    manifest_path.write_text("\n".join(manifest_lines))

    return {
        "guide_catalog_path": ACTIVE_FOLIO_ALPHABET_V1_PATH,
        "manifest_path": manifest_path,
        "confidence_manifest_path": confidence_path,
        "report_json_path": report_json,
        "report_md_path": report_md,
        "coverage_json_path": coverage_json,
        "coverage_md_path": coverage_md,
        "snapshot_panel_path": panel_path,
    }
