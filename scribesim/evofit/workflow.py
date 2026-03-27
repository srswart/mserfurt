"""Evofit workflows for exemplar-driven nominal form recovery."""

from __future__ import annotations

import json
import math
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image as PILImage, ImageDraw

from scribesim.evo.engine import EvolutionConfig, evolve_word, initialize_population
from scribesim.evo.fitness import _ncc_score
from scribesim.evo.genome import BezierSegment, GlyphGenome, WordGenome
from scribesim.evo.renderer import render_word_from_genome
from scribesim.pathguide.catalog import (
    STARTER_ALPHABET_V1_JOINS,
    build_active_folio_alphabet_v1_guides,
    build_starter_alphabet_v1_guides,
)
from scribesim.pathguide.io import write_pathguides_toml
from scribesim.pathguide.model import DensePathGuide, GuideSample, GuideSource
from scribesim.pathguide.validate import validate_dense_path_guide
from scribesim.refextract.exemplar import extract_exemplar


DEFAULT_EVOFIT_CORPUS_MANIFEST_PATH = Path("shared/training/handsim/active_review_exemplars_v1/promoted_manifest.toml")
DEFAULT_EVOFIT_OUTPUT_ROOT = Path("shared/training/handsim/evofit_active_review_v1")
DEFAULT_REVIEWED_EVOFIT_MANIFEST_PATH = Path(
    "shared/training/handsim/reviewed_annotations/reviewed_exemplars_v1/reviewed_exemplar_manifest.toml"
)
DEFAULT_REVIEWED_EVOFIT_OUTPUT_ROOT = Path("shared/training/handsim/reviewed_annotations/reviewed_evofit_v1")
DEFAULT_AUTOMATIC_EVOFIT_BASELINE_SUMMARY_PATH = Path("shared/training/handsim/evofit_active_review_v1/summary.json")
_TARGET_SIZE = (64, 64)
_DEFAULT_ALLOWED_TIERS = ("accepted", "soft_accepted")
_PROMOTED_EXEMPLAR_TIER = "promoted_exemplars"
_REVIEWED_EXEMPLAR_TIER = "reviewed_exemplars"
_REPAIR_ONLY_TIER = "repair_only"


@dataclass(frozen=True)
class EvofitConfig:
    """Configuration for one exploratory evofit run."""

    pop_size: int = 14
    generations: int = 12
    eval_dpi: float = 700.0
    render_dpi: float = 300.0
    nib_width_mm: float = 1.0
    x_height_mm: float = 3.8
    max_candidates_per_symbol: int = 3
    allowed_tiers: tuple[str, ...] = _DEFAULT_ALLOWED_TIERS

    def to_engine_config(self) -> EvolutionConfig:
        return EvolutionConfig(
            pop_size=self.pop_size,
            generations=self.generations,
            eval_dpi=self.eval_dpi,
            nib_width_mm=self.nib_width_mm,
        )


@dataclass(frozen=True)
class EvofitTarget:
    """One symbol/join fit-source bundle built from the exemplar corpus."""

    kind: str
    symbol: str
    text: str
    candidate_paths: tuple[Path, ...]
    candidate_tiers: tuple[str, ...]
    candidate_source_paths: tuple[str, ...] = ()
    candidate_quality_tiers: tuple[str, ...] = ()
    candidate_source_manuscripts: tuple[str, ...] = ()
    candidate_source_object_ids: tuple[str, ...] = ()
    candidate_raw_paths: tuple[str, ...] = ()
    candidate_cleaned_paths: tuple[str, ...] = ()
    candidate_source_variants: tuple[str, ...] = ()
    candidate_cleanup_stroke_counts: tuple[int, ...] = ()
    coverage_promoted: bool = False


@dataclass(frozen=True)
class EvofitCandidateSummary:
    """Summary for one evolved candidate run."""

    source_path: str
    source_tier: str
    best_fitness: float
    nominal_ncc: float
    evofit_ncc: float
    beats_prior_nominal: bool
    structurally_convertible: bool
    validation_errors: tuple[str, ...] = field(default_factory=tuple)
    fitness_history: tuple[float, ...] = field(default_factory=tuple)
    best_render_path: str | None = None
    fit_source_copy_path: str | None = None
    prior_render_path: str | None = None
    comparison_path: str | None = None
    source_manuscript_label: str | None = None
    source_quality_tier: str | None = None
    source_object_id: str | None = None
    source_document_path: str | None = None
    source_raw_path: str | None = None
    source_cleaned_path: str | None = None
    source_variant: str | None = None
    source_cleanup_stroke_count: int = 0


def _slug(symbol: str) -> str:
    return (
        symbol.replace("->", "_to_")
        .replace("/", "_")
        .replace(" ", "_")
        .replace(":", "_")
    )


def _load_manifest(path: Path | str) -> dict[str, Any]:
    raw = tomllib.loads(Path(path).read_text())
    if raw.get("schema_version") != 1:
        raise ValueError("evofit corpus manifest must declare schema_version = 1")
    if not raw.get("entries"):
        raise ValueError("evofit corpus manifest must contain entries")
    return raw


def _manifest_kind(manifest: dict[str, Any]) -> str:
    return str(manifest.get("manifest_kind", "")).strip() or "unknown"


def _candidate_list(
    entry: dict[str, Any],
    allowed_tiers: tuple[str, ...],
    limit: int,
    *,
    reviewed_source_mode: str = "prefer_cleaned",
) -> tuple[
    tuple[Path, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[int, ...],
]:
    if _REPAIR_ONLY_TIER in {str(tier) for tier in allowed_tiers}:
        raise ValueError("repair_only tier is non-reviewable and cannot be used as an evofit input")
    if entry.get("reviewed_exemplar_paths"):
        reviewed_paths = [str(raw_path) for raw_path in (entry.get("reviewed_exemplar_paths") or [])]
        reviewed_raw_paths = [str(value) for value in (entry.get("reviewed_raw_exemplar_paths") or [])]
        reviewed_cleaned_paths = [str(value) for value in (entry.get("reviewed_cleaned_exemplar_paths") or [])]
        cleanup_counts_full = [int(value) for value in (entry.get("reviewed_cleanup_stroke_counts") or [])]
        selected_paths_raw: list[str] = []
        selected_raw_paths: list[str] = []
        selected_cleaned_paths: list[str] = []
        selected_variants: list[str] = []
        selected_cleanup_counts: list[int] = []
        for idx, preferred_path in enumerate(reviewed_paths):
            raw_path = reviewed_raw_paths[idx] if idx < len(reviewed_raw_paths) and reviewed_raw_paths[idx] else preferred_path
            cleaned_path = (
                reviewed_cleaned_paths[idx]
                if idx < len(reviewed_cleaned_paths) and reviewed_cleaned_paths[idx]
                else ""
            )
            cleanup_count = cleanup_counts_full[idx] if idx < len(cleanup_counts_full) else 0
            if reviewed_source_mode == "raw_only":
                selected_path = raw_path
                variant = "raw"
            else:
                selected_path = cleaned_path or preferred_path or raw_path
                variant = "cleaned" if cleaned_path and selected_path == cleaned_path else "raw"
            selected_paths_raw.append(selected_path)
            selected_raw_paths.append(raw_path)
            selected_cleaned_paths.append(cleaned_path)
            selected_variants.append(variant)
            selected_cleanup_counts.append(cleanup_count)
            if len(selected_paths_raw) >= limit:
                break

        selected_paths = [Path(raw_path) for raw_path in selected_paths_raw]
        selected_count = len(selected_paths)
        source_paths = tuple(str(value) for value in (entry.get("reviewed_exemplar_source_paths") or [])[:selected_count])
        qualities = tuple(str(value) for value in (entry.get("reviewed_quality_tiers") or [])[:selected_count])
        source_manuscripts = tuple(
            str(value) for value in (entry.get("reviewed_exemplar_source_manuscripts") or [])[:selected_count]
        )
        source_object_ids = tuple(
            str(value) for value in (entry.get("reviewed_exemplar_source_object_ids") or [])[:selected_count]
        )
        return (
            tuple(selected_paths),
            tuple(_REVIEWED_EXEMPLAR_TIER for _ in selected_paths),
            source_paths,
            qualities,
            source_manuscripts,
            source_object_ids,
            tuple(selected_raw_paths[:selected_count]),
            tuple(selected_cleaned_paths[:selected_count]),
            tuple(selected_variants[:selected_count]),
            tuple(selected_cleanup_counts[:selected_count]),
        )
    if entry.get("promoted_exemplar_paths"):
        selected = [Path(raw_path) for raw_path in (entry.get("promoted_exemplar_paths") or [])[:limit]]
        source_paths = tuple(str(value) for value in (entry.get("promoted_exemplar_source_paths") or [])[: len(selected)])
        return (
            tuple(selected),
            tuple(_PROMOTED_EXEMPLAR_TIER for _ in selected),
            source_paths,
            tuple("" for _ in selected),
            tuple("" for _ in selected),
            tuple("" for _ in selected),
            tuple(str(path) for path in selected),
            tuple("" for _ in selected),
            tuple("raw" for _ in selected),
            tuple(0 for _ in selected),
        )
    ordered: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for tier in allowed_tiers:
        key = f"{tier}_paths"
        for raw_path in entry.get(key, []) or []:
            raw_key = str(raw_path)
            if raw_key in seen:
                continue
            seen.add(raw_key)
            ordered.append((Path(raw_path), tier))
    selected = ordered[:limit]
    return (
        tuple(path for path, _ in selected),
        tuple(tier for _, tier in selected),
        tuple("" for _ in selected),
        tuple("" for _ in selected),
        tuple("" for _ in selected),
        tuple("" for _ in selected),
        tuple(str(path) for path, _ in selected),
        tuple("" for _ in selected),
        tuple("raw" for _ in selected),
        tuple(0 for _ in selected),
    )


def build_evofit_targets(
    corpus_manifest_path: Path | str,
    *,
    kind: str = "all",
    symbols: tuple[str, ...] | list[str] | None = None,
    allowed_tiers: tuple[str, ...] = _DEFAULT_ALLOWED_TIERS,
    max_candidates_per_symbol: int = 3,
    reviewed_source_mode: str = "prefer_cleaned",
) -> tuple[EvofitTarget, ...]:
    """Build evofit fit-source bundles from a frozen exemplar corpus manifest."""

    manifest = _load_manifest(corpus_manifest_path)
    requested = set(symbols or ())
    targets: list[EvofitTarget] = []

    for entry in manifest["entries"]:
        entry_kind = str(entry["kind"])
        if kind != "all" and entry_kind != kind:
            continue
        symbol = str(entry["symbol"])
        if requested and symbol not in requested:
            continue
        (
            candidate_paths,
            candidate_tiers,
            candidate_source_paths,
            candidate_quality_tiers,
            candidate_source_manuscripts,
            candidate_source_object_ids,
            candidate_raw_paths,
            candidate_cleaned_paths,
            candidate_source_variants,
            candidate_cleanup_stroke_counts,
        ) = _candidate_list(entry, allowed_tiers, max_candidates_per_symbol, reviewed_source_mode=reviewed_source_mode)
        if not candidate_paths:
            continue
        text = symbol if entry_kind == "glyph" else symbol.replace("->", "")
        targets.append(
            EvofitTarget(
                kind=entry_kind,
                symbol=symbol,
                text=text,
                candidate_paths=candidate_paths,
                candidate_tiers=candidate_tiers,
                candidate_source_paths=candidate_source_paths,
                candidate_quality_tiers=candidate_quality_tiers,
                candidate_source_manuscripts=candidate_source_manuscripts,
                candidate_source_object_ids=candidate_source_object_ids,
                candidate_raw_paths=candidate_raw_paths,
                candidate_cleaned_paths=candidate_cleaned_paths,
                candidate_source_variants=candidate_source_variants,
                candidate_cleanup_stroke_counts=candidate_cleanup_stroke_counts,
                coverage_promoted=bool(entry.get("coverage_promoted", False)),
            )
        )

    return tuple(targets)


def _normalize_image(arr: np.ndarray) -> np.ndarray:
    if arr.ndim == 3:
        return np.array(PILImage.fromarray(arr).convert("L"))
    return arr.astype(np.uint8)


def _render_dense_guide_template(guide: DensePathGuide, target_size: tuple[int, int] = _TARGET_SIZE) -> np.ndarray:
    min_x = min(sample.x_mm - sample.corridor_half_width_mm for sample in guide.samples)
    min_y = min(sample.y_mm - sample.corridor_half_width_mm for sample in guide.samples)
    max_x = max(sample.x_mm + sample.corridor_half_width_mm for sample in guide.samples)
    max_y = max(sample.y_mm + sample.corridor_half_width_mm for sample in guide.samples)

    width_mm = max(max_x - min_x, 0.1)
    height_mm = max(max_y - min_y, 0.1)
    inner_w = target_size[1] - 12
    inner_h = target_size[0] - 12
    px_per_mm = min(inner_w / width_mm, inner_h / height_mm)

    canvas = PILImage.new("L", (target_size[1], target_size[0]), 255)
    draw = ImageDraw.Draw(canvas)

    def to_px(x_mm: float, y_mm: float) -> tuple[int, int]:
        x_px = 6 + int(round((x_mm - min_x) * px_per_mm))
        y_px = target_size[0] - 6 - int(round((y_mm - min_y) * px_per_mm))
        return x_px, y_px

    for idx in range(len(guide.samples) - 1):
        a = guide.samples[idx]
        b = guide.samples[idx + 1]
        width = max(1, int(round((a.corridor_half_width_mm + b.corridor_half_width_mm) * 0.5 * px_per_mm * 0.9)))
        draw.line((*to_px(a.x_mm, a.y_mm), *to_px(b.x_mm, b.y_mm)), fill=0, width=width)
    return np.array(canvas, dtype=np.uint8)


def _norm(dx: float, dy: float) -> tuple[float, float]:
    magnitude = math.hypot(dx, dy)
    if magnitude <= 1e-9:
        return (1.0, 0.0)
    return (dx / magnitude, dy / magnitude)


def _sample_segment(
    segment: BezierSegment,
    *,
    corridor_half_width_mm: float,
    pressure_scale: float = 1.0,
    max_step_mm: float = 0.12,
) -> list[GuideSample]:
    length_mm = max(segment.length(), max_step_mm)
    sample_count = max(12, math.ceil(length_mm / max_step_mm))
    samples: list[GuideSample] = []
    for idx in range(sample_count + 1):
        t = idx / sample_count
        x_mm, y_mm = segment.evaluate(t)
        dx, dy = _norm(*segment.tangent(t))
        samples.append(
            GuideSample(
                x_mm=x_mm,
                y_mm=y_mm,
                tangent_dx=dx,
                tangent_dy=dy,
                contact=segment.contact,
                speed_nominal=float(segment.speed_at(t)),
                pressure_nominal=float(max(0.0, min(1.5, segment.pressure_at(t) * pressure_scale))),
                corridor_half_width_mm=corridor_half_width_mm,
            )
        )
    return samples


def _join_bridge(left: GlyphGenome, right: GlyphGenome) -> BezierSegment:
    start = left.exit_point
    end = right.entry_point
    exit_dx, exit_dy = _norm(*left.exit_tangent())
    entry_dx, entry_dy = _norm(*right.entry_tangent())
    gap = math.hypot(end[0] - start[0], end[1] - start[1])
    handle = max(0.18, min(gap * 0.45, 1.4))
    p1 = (start[0] + exit_dx * handle, start[1] + exit_dy * handle * 0.35)
    p2 = (end[0] - entry_dx * handle, end[1] - entry_dy * handle * 0.35)
    return BezierSegment(
        p0=start,
        p1=p1,
        p2=p2,
        p3=end,
        contact=True,
        pressure_curve=[0.22, 0.28, 0.28, 0.22],
        speed_curve=[1.05, 1.1, 1.1, 1.05],
        nib_angle_drift=0.0,
    )


def genome_to_dense_guide(
    genome: WordGenome,
    *,
    symbol: str,
    kind: str,
    x_height_mm: float,
    source_id: str,
    source_path: str | None = None,
    confidence_tier: str = "soft_accepted",
    split: str = "validation",
    source_resolution_ppmm: float | None = None,
) -> DensePathGuide:
    """Convert an evolved genome into a dense nominal path guide."""

    sampled: list[GuideSample] = []

    if kind == "join":
        if len(genome.glyphs) < 2:
            raise ValueError("join proposals require at least two glyphs")
        bridge = _join_bridge(genome.glyphs[0], genome.glyphs[1])
        segments = [bridge]
        x_advance_mm = max(0.1, bridge.p3[0] - bridge.p0[0])
        corridor_half_width_mm = 0.14
    elif kind == "glyph":
        if not genome.glyphs:
            raise ValueError("glyph proposal requires at least one glyph")
        segments = list(genome.glyphs[0].segments)
        x_advance_mm = genome.glyphs[0].x_advance
        corridor_half_width_mm = 0.20
    else:
        segments = []
        for idx, glyph in enumerate(genome.glyphs):
            segments.extend(glyph.segments)
            if idx + 1 < len(genome.glyphs):
                segments.append(_join_bridge(glyph, genome.glyphs[idx + 1]))
        x_advance_mm = genome.word_width_mm
        corridor_half_width_mm = 0.18

    for segment in segments:
        part = _sample_segment(segment, corridor_half_width_mm=corridor_half_width_mm)
        if sampled and part:
            part = part[1:]
        sampled.extend(part)

    if len(sampled) < 2:
        raise ValueError(f"{symbol!r} produced no guide samples")

    min_x = min(sample.x_mm for sample in sampled)
    min_y = min(sample.y_mm for sample in sampled)
    normalized = tuple(
        GuideSample(
            x_mm=sample.x_mm - min_x,
            y_mm=sample.y_mm - min_y,
            tangent_dx=sample.tangent_dx,
            tangent_dy=sample.tangent_dy,
            contact=sample.contact,
            speed_nominal=sample.speed_nominal,
            pressure_nominal=sample.pressure_nominal,
            corridor_half_width_mm=sample.corridor_half_width_mm,
        )
        for sample in sampled
    )

    return DensePathGuide(
        symbol=symbol,
        kind=kind,
        samples=normalized,
        x_advance_mm=max(0.1, x_advance_mm),
        x_height_mm=x_height_mm,
        entry_tangent=(normalized[0].tangent_dx, normalized[0].tangent_dy),
        exit_tangent=(normalized[-1].tangent_dx, normalized[-1].tangent_dy),
        sources=(
            GuideSource(
                source_id=source_id,
                source_path=source_path,
                extraction_run="ADV-SS-EVOFIT-001",
                confidence_tier=confidence_tier,
                split=split,
                source_resolution_ppmm=source_resolution_ppmm,
            ),
        ),
    )


def _lookup_prior_guide(symbol: str, kind: str, *, x_height_mm: float) -> DensePathGuide | None:
    if kind == "glyph":
        return build_active_folio_alphabet_v1_guides(x_height_mm=x_height_mm).get(symbol)
    starter = build_starter_alphabet_v1_guides(x_height_mm=x_height_mm)
    if symbol in starter:
        return starter[symbol]
    if symbol in STARTER_ALPHABET_V1_JOINS:
        return starter.get(symbol)
    return None


def _copy_image(source: Path, destination: Path) -> None:
    arr = np.array(PILImage.open(source).convert("L"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    PILImage.fromarray(arr).save(destination)


def _write_comparison_panel(fit_source: np.ndarray, prior: np.ndarray | None, evolved: np.ndarray, output_path: Path) -> None:
    fit_source_img = PILImage.fromarray(extract_exemplar(_normalize_image(fit_source), target_size=_TARGET_SIZE))
    prior_img = PILImage.fromarray(extract_exemplar(_normalize_image(prior), target_size=_TARGET_SIZE)) if prior is not None else PILImage.new("L", _TARGET_SIZE[::-1], 255)
    evolved_img = PILImage.fromarray(extract_exemplar(_normalize_image(evolved), target_size=_TARGET_SIZE))
    panel = PILImage.new("L", (_TARGET_SIZE[1] * 3 + 24, _TARGET_SIZE[0] + 12), 255)
    panel.paste(fit_source_img, (4, 6))
    panel.paste(prior_img, (_TARGET_SIZE[1] + 10, 6))
    panel.paste(evolved_img, (_TARGET_SIZE[1] * 2 + 16, 6))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.save(output_path)


def _best_seed_nominal(
    text: str,
    *,
    guides_path: str | None,
    x_height_mm: float,
) -> WordGenome:
    return initialize_population(text, pop_size=1, x_height_mm=x_height_mm, guides_path=guides_path)[0]


def _write_manifest(
    *,
    output_root: Path,
    corpus_manifest_path: Path,
    proposal_catalog_path: Path,
    payload: dict[str, Any],
    manifest_title: str = "# TD-014 exploratory evofit bundle",
) -> Path:
    manifest_path = output_root / "manifest.toml"
    lines = [
        manifest_title,
        "schema_version = 1",
        f"corpus_manifest_path = {json.dumps(str(corpus_manifest_path))}",
        f"proposal_catalog_path = {json.dumps(str(proposal_catalog_path))}",
        f"summary_json_path = {json.dumps(str(output_root / 'summary.json'))}",
        f"summary_md_path = {json.dumps(str(output_root / 'summary.md'))}",
        "",
    ]
    for fit_source in payload["fit_sources"]:
        lines.extend(
            [
                "[[fit_sources]]",
                f"kind = {json.dumps(fit_source['kind'])}",
                f"symbol = {json.dumps(fit_source['symbol'])}",
                f"text = {json.dumps(fit_source['text'])}",
                f"selected_source_path = {json.dumps(fit_source['selected_source_path'])}",
                f"selected_source_document_path = {json.dumps(fit_source.get('selected_source_document_path', ''))}",
                f"selected_source_tier = {json.dumps(fit_source['selected_source_tier'])}",
                f"selected_source_variant = {json.dumps(fit_source.get('selected_source_variant', 'raw'))}",
                f"selected_source_raw_path = {json.dumps(fit_source.get('selected_source_raw_path', ''))}",
                f"selected_source_cleaned_path = {json.dumps(fit_source.get('selected_source_cleaned_path', ''))}",
                f"selected_source_cleanup_stroke_count = {int(fit_source.get('selected_source_cleanup_stroke_count', 0))}",
                f"selected_source_manuscript = {json.dumps(fit_source.get('selected_source_manuscript', ''))}",
                f"selected_source_quality_tier = {json.dumps(fit_source.get('selected_source_quality_tier', ''))}",
                f"selected_source_object_id = {json.dumps(fit_source.get('selected_source_object_id', ''))}",
                f"best_fitness = {fit_source['best_fitness']:.6f}",
                f"evofit_ncc = {fit_source['evofit_ncc']:.6f}",
                f"nominal_ncc = {fit_source['nominal_ncc']:.6f}",
                f"structurally_convertible = {str(fit_source['structurally_convertible']).lower()}",
                "",
            ]
        )
    manifest_path.write_text("\n".join(lines))
    return manifest_path


def _write_summary_markdown(payload: dict[str, Any], output_path: Path, *, note: str) -> None:
    lines = [
        "# TD-014 Evofit Summary",
        "",
        f"- note: {note}",
        f"- fit-source count: {payload['fit_source_count']}",
        f"- converted guides: {payload['converted_guide_count']}",
        f"- convertible rate: {payload['convertible_rate']:.4f}",
        f"- beats prior nominal rate: {payload['beats_prior_rate']:.4f}",
        f"- mean evofit NCC: {payload['mean_evofit_ncc']:.4f}",
        f"- mean nominal NCC: {payload['mean_nominal_ncc']:.4f}",
        f"- baseline comparison: {payload['baseline_comparison']['status']}",
        f"- raw reviewed baseline comparison: {payload.get('raw_reviewed_baseline_comparison', {}).get('status', 'not-run')}",
        "",
        "## Fit Sources",
        "",
    ]
    for fit_source in payload["fit_sources"]:
        lines.extend(
            [
                f"- `{fit_source['symbol']}` ({fit_source['kind']}): "
                f"fitness={fit_source['best_fitness']:.4f}, "
                f"ncc={fit_source['evofit_ncc']:.4f}, "
                f"prior={fit_source['nominal_ncc']:.4f}, "
                f"tier={fit_source['selected_source_tier']}, "
                f"variant={fit_source.get('selected_source_variant', 'raw')}, "
                f"cleanup={fit_source.get('selected_source_cleanup_stroke_count', 0)}, "
                f"quality={fit_source.get('selected_source_quality_tier', '') or 'n/a'}, "
                f"manuscript={fit_source.get('selected_source_manuscript', '') or 'unknown'}, "
                f"convertible={fit_source['structurally_convertible']}",
            ]
        )
    output_path.write_text("\n".join(lines) + "\n")


def _compare_baseline(
    payload: dict[str, Any],
    *,
    baseline_summary_path: Path | str | None,
) -> dict[str, Any]:
    if baseline_summary_path is None:
        return {
            "status": "not-requested",
            "baseline_summary_path": "",
            "beats_prior_rate_delta": None,
            "mean_evofit_ncc_delta": None,
            "improved_vs_baseline": None,
        }
    path = Path(baseline_summary_path)
    if not path.exists():
        return {
            "status": "missing",
            "baseline_summary_path": path.as_posix(),
            "beats_prior_rate_delta": None,
            "mean_evofit_ncc_delta": None,
            "improved_vs_baseline": None,
        }
    baseline = json.loads(path.read_text(encoding="utf-8"))
    beats_delta = float(payload["beats_prior_rate"]) - float(baseline.get("beats_prior_rate", 0.0))
    evofit_delta = float(payload["mean_evofit_ncc"]) - float(baseline.get("mean_evofit_ncc", 0.0))
    improved = beats_delta > 0.0 or evofit_delta > 0.0
    return {
        "status": "compared",
        "baseline_summary_path": path.as_posix(),
        "beats_prior_rate_delta": beats_delta,
        "mean_evofit_ncc_delta": evofit_delta,
        "improved_vs_baseline": improved,
    }


def _write_provenance_report(payload: dict[str, Any], output_root: Path) -> tuple[Path, Path]:
    json_path = output_root / "provenance_report.json"
    md_path = output_root / "provenance_report.md"
    report = {
        "fit_sources": [
            {
                "symbol": item["symbol"],
                "kind": item["kind"],
                "selected_source_path": item["selected_source_path"],
                "selected_source_document_path": item.get("selected_source_document_path", ""),
                "selected_source_tier": item["selected_source_tier"],
                "selected_source_variant": item.get("selected_source_variant", "raw"),
                "selected_source_raw_path": item.get("selected_source_raw_path", ""),
                "selected_source_cleaned_path": item.get("selected_source_cleaned_path", ""),
                "selected_source_cleanup_stroke_count": item.get("selected_source_cleanup_stroke_count", 0),
                "selected_source_quality_tier": item.get("selected_source_quality_tier", ""),
                "selected_source_manuscript": item.get("selected_source_manuscript", ""),
                "selected_source_object_id": item.get("selected_source_object_id", ""),
            }
            for item in payload["fit_sources"]
        ]
    }
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# TD-014 Evofit Provenance Report",
        "",
    ]
    for item in report["fit_sources"]:
        lines.append(
            f"- `{item['symbol']}` ({item['kind']}): "
            f"tier={item['selected_source_tier']}, "
            f"variant={item['selected_source_variant']}, "
            f"cleanup={item['selected_source_cleanup_stroke_count']}, "
            f"quality={item['selected_source_quality_tier'] or 'n/a'}, "
            f"manuscript={item['selected_source_manuscript'] or 'unknown'}, "
            f"object_id={item['selected_source_object_id'] or 'n/a'}, "
            f"document=`{item['selected_source_document_path'] or 'n/a'}` "
            f"path=`{item['selected_source_path']}` "
            f"raw=`{item['selected_source_raw_path'] or 'n/a'}` "
            f"cleaned=`{item['selected_source_cleaned_path'] or 'n/a'}`"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def _compare_raw_reviewed_baseline(
    cleaned_payload: dict[str, Any],
    raw_baseline_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    if raw_baseline_payload is None:
        return {
            "status": "not-run",
            "beats_prior_rate_delta": None,
            "mean_evofit_ncc_delta": None,
            "cleaned_fit_source_count": len(cleaned_payload.get("fit_sources", [])),
            "raw_fit_source_count": 0,
            "symbols_compared": [],
            "improved_vs_raw": None,
        }

    cleaned_by_symbol = {item["symbol"]: item for item in cleaned_payload.get("fit_sources", [])}
    raw_by_symbol = {item["symbol"]: item for item in raw_baseline_payload.get("fit_sources", [])}
    shared_symbols = sorted(set(cleaned_by_symbol) & set(raw_by_symbol))
    if not shared_symbols:
        return {
            "status": "no-overlap",
            "beats_prior_rate_delta": None,
            "mean_evofit_ncc_delta": None,
            "cleaned_fit_source_count": len(cleaned_payload.get("fit_sources", [])),
            "raw_fit_source_count": len(raw_baseline_payload.get("fit_sources", [])),
            "symbols_compared": [],
            "improved_vs_raw": None,
        }

    cleaned_mean = sum(float(cleaned_by_symbol[symbol]["evofit_ncc"]) for symbol in shared_symbols) / len(shared_symbols)
    raw_mean = sum(float(raw_by_symbol[symbol]["evofit_ncc"]) for symbol in shared_symbols) / len(shared_symbols)
    cleaned_beats = sum(1 for symbol in shared_symbols if cleaned_by_symbol[symbol]["beats_prior_nominal"]) / len(shared_symbols)
    raw_beats = sum(1 for symbol in shared_symbols if raw_by_symbol[symbol]["beats_prior_nominal"]) / len(shared_symbols)
    return {
        "status": "compared",
        "beats_prior_rate_delta": cleaned_beats - raw_beats,
        "mean_evofit_ncc_delta": cleaned_mean - raw_mean,
        "cleaned_fit_source_count": len(cleaned_payload.get("fit_sources", [])),
        "raw_fit_source_count": len(raw_baseline_payload.get("fit_sources", [])),
        "symbols_compared": shared_symbols,
        "improved_vs_raw": cleaned_mean > raw_mean or cleaned_beats > raw_beats,
    }


def run_evofit_from_corpus(
    corpus_manifest_path: Path | str,
    *,
    output_root: Path | str = DEFAULT_EVOFIT_OUTPUT_ROOT,
    config: EvofitConfig | None = None,
    kind: str = "all",
    symbols: tuple[str, ...] | list[str] | None = None,
    guides_path: str | None = None,
    expected_manifest_kind: str | None = None,
    summary_note: str = "each fit source is an automatically admitted corpus crop, not a promoted exemplar or trusted character truth sample.",
    bundle_title: str = "# TD-014 exploratory evofit bundle",
    baseline_summary_path: Path | str | None = None,
    reviewed_source_mode: str = "prefer_cleaned",
) -> dict[str, Any]:
    """Run exploratory evo fitting from a frozen exemplar corpus."""

    config = config or EvofitConfig()
    corpus_manifest_path = Path(corpus_manifest_path)
    manifest = _load_manifest(corpus_manifest_path)
    manifest_kind = _manifest_kind(manifest)
    if expected_manifest_kind is not None and manifest_kind != expected_manifest_kind:
        raise ValueError(
            f"expected manifest_kind {expected_manifest_kind!r}, got {manifest_kind!r}"
        )
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    targets = build_evofit_targets(
        corpus_manifest_path,
        kind=kind,
        symbols=symbols,
        allowed_tiers=config.allowed_tiers,
        max_candidates_per_symbol=config.max_candidates_per_symbol,
        reviewed_source_mode=reviewed_source_mode,
    )
    if not targets:
        raise ValueError("no evofit targets resolved from corpus manifest")

    exemplar_root = corpus_manifest_path.parent / "glyphs" / "accepted"
    engine_config = config.to_engine_config()
    proposal_guides: dict[str, DensePathGuide] = {}
    fit_source_payloads: list[dict[str, Any]] = []

    for target in targets:
        best_summary: EvofitCandidateSummary | None = None
        best_guide: DensePathGuide | None = None
        symbol_dir = output_root / target.kind / _slug(target.symbol)
        symbol_dir.mkdir(parents=True, exist_ok=True)

        prior_guide = _lookup_prior_guide(target.symbol, target.kind, x_height_mm=config.x_height_mm)
        prior_render = _render_dense_guide_template(prior_guide) if prior_guide is not None else None

        for candidate_index, candidate_path in enumerate(target.candidate_paths):
            fit_source_crop = np.array(PILImage.open(candidate_path).convert("L"))
            seed = _best_seed_nominal(target.text, guides_path=guides_path, x_height_mm=config.x_height_mm)
            seed_render = render_word_from_genome(seed, dpi=config.render_dpi, nib_width_mm=config.nib_width_mm)
            nominal_ncc = float(_ncc_score(_normalize_image(seed_render), fit_source_crop))
            if prior_render is not None:
                nominal_ncc = max(nominal_ncc, float(_ncc_score(prior_render, fit_source_crop)))

            result = evolve_word(
                target.text,
                target_crop=fit_source_crop,
                config=engine_config,
                verbose=False,
                guides_path=guides_path,
                x_height_mm=config.x_height_mm,
                exemplar_root=exemplar_root if exemplar_root.exists() else None,
            )
            rendered = render_word_from_genome(
                result.best_genome,
                dpi=config.render_dpi,
                nib_width_mm=config.nib_width_mm,
            )
            evofit_ncc = float(_ncc_score(_normalize_image(rendered), fit_source_crop))

            guide: DensePathGuide | None = None
            validation_errors: tuple[str, ...] = ()
            try:
                guide = genome_to_dense_guide(
                    result.best_genome,
                    symbol=target.symbol,
                    kind=target.kind,
                    x_height_mm=config.x_height_mm,
                    source_id=f"evofit:{target.symbol}",
                    source_path=str(candidate_path),
                )
                validation_errors = tuple(validate_dense_path_guide(guide))
            except Exception as exc:
                validation_errors = (str(exc),)

            candidate_dir = symbol_dir / f"candidate_{candidate_index:02d}"
            candidate_dir.mkdir(parents=True, exist_ok=True)
            best_render_path = candidate_dir / "best_render.png"
            PILImage.fromarray(_normalize_image(rendered)).save(best_render_path)
            fit_source_copy_path = candidate_dir / "fit_source.png"
            _copy_image(candidate_path, fit_source_copy_path)
            prior_render_path = candidate_dir / "prior_nominal.png" if prior_render is not None else None
            if prior_render is not None and prior_render_path is not None:
                PILImage.fromarray(prior_render).save(prior_render_path)
            comparison_path = candidate_dir / "comparison.png"
            _write_comparison_panel(fit_source_crop, prior_render, rendered, comparison_path)
            (candidate_dir / "fitness_history.json").write_text(
                json.dumps(
                    {
                        "fitness_history": result.fitness_history,
                        "best_fitness": result.best_fitness,
                        "generations_run": result.generations_run,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

            summary = EvofitCandidateSummary(
                source_path=str(candidate_path),
                source_tier=target.candidate_tiers[candidate_index],
                best_fitness=float(result.best_fitness),
                nominal_ncc=nominal_ncc,
                evofit_ncc=evofit_ncc,
                beats_prior_nominal=evofit_ncc > nominal_ncc + 1e-6,
                structurally_convertible=guide is not None and not validation_errors,
                validation_errors=validation_errors,
                fitness_history=tuple(float(value) for value in result.fitness_history),
                best_render_path=str(best_render_path),
                fit_source_copy_path=str(fit_source_copy_path),
                prior_render_path=str(prior_render_path) if prior_render_path is not None else None,
                comparison_path=str(comparison_path),
                source_manuscript_label=(
                    target.candidate_source_manuscripts[candidate_index]
                    if candidate_index < len(target.candidate_source_manuscripts)
                    else None
                ),
                source_quality_tier=(
                    target.candidate_quality_tiers[candidate_index]
                    if candidate_index < len(target.candidate_quality_tiers)
                    else None
                ),
                source_object_id=(
                    target.candidate_source_object_ids[candidate_index]
                    if candidate_index < len(target.candidate_source_object_ids)
                    else None
                ),
                source_document_path=(
                    target.candidate_source_paths[candidate_index]
                    if candidate_index < len(target.candidate_source_paths)
                    else None
                ),
                source_raw_path=(
                    target.candidate_raw_paths[candidate_index]
                    if candidate_index < len(target.candidate_raw_paths)
                    else None
                ),
                source_cleaned_path=(
                    target.candidate_cleaned_paths[candidate_index]
                    if candidate_index < len(target.candidate_cleaned_paths)
                    else None
                ),
                source_variant=(
                    target.candidate_source_variants[candidate_index]
                    if candidate_index < len(target.candidate_source_variants)
                    else None
                ),
                source_cleanup_stroke_count=(
                    target.candidate_cleanup_stroke_counts[candidate_index]
                    if candidate_index < len(target.candidate_cleanup_stroke_counts)
                    else 0
                ),
            )

            if best_summary is None:
                best_summary = summary
                best_guide = guide if summary.structurally_convertible else None
                continue
            if summary.evofit_ncc > best_summary.evofit_ncc + 1e-6 or (
                math.isclose(summary.evofit_ncc, best_summary.evofit_ncc, abs_tol=1e-6)
                and summary.best_fitness > best_summary.best_fitness
            ):
                best_summary = summary
                best_guide = guide if summary.structurally_convertible else None

        if best_summary is None:
            continue
        if best_guide is not None:
            proposal_guides[target.symbol] = best_guide
        fit_source_payloads.append(
            {
                "kind": target.kind,
                "symbol": target.symbol,
                "text": target.text,
                "selected_source_path": best_summary.source_path,
                "selected_source_tier": best_summary.source_tier,
                "selected_source_manuscript": best_summary.source_manuscript_label,
                "selected_source_quality_tier": best_summary.source_quality_tier,
                "selected_source_object_id": best_summary.source_object_id,
                "selected_source_document_path": best_summary.source_document_path,
                "selected_source_raw_path": best_summary.source_raw_path,
                "selected_source_cleaned_path": best_summary.source_cleaned_path,
                "selected_source_variant": best_summary.source_variant,
                "selected_source_cleanup_stroke_count": best_summary.source_cleanup_stroke_count,
                "best_fitness": best_summary.best_fitness,
                "nominal_ncc": best_summary.nominal_ncc,
                "evofit_ncc": best_summary.evofit_ncc,
                "beats_prior_nominal": best_summary.beats_prior_nominal,
                "structurally_convertible": best_summary.structurally_convertible,
                "validation_errors": list(best_summary.validation_errors),
                "fitness_history": list(best_summary.fitness_history),
                "best_render_path": best_summary.best_render_path,
                "fit_source_copy_path": best_summary.fit_source_copy_path,
                "prior_render_path": best_summary.prior_render_path,
                "comparison_path": best_summary.comparison_path,
            }
        )

    proposal_catalog_path = output_root / "proposal_guides.toml"
    if proposal_guides:
        write_pathguides_toml(proposal_guides, proposal_catalog_path)

    fit_source_count = len(fit_source_payloads)
    converted_guide_count = len(proposal_guides)
    beats_prior_count = sum(1 for payload in fit_source_payloads if payload["beats_prior_nominal"])
    mean_evofit_ncc = (
        sum(float(item["evofit_ncc"]) for item in fit_source_payloads) / max(fit_source_count, 1)
    )
    mean_nominal_ncc = (
        sum(float(item["nominal_ncc"]) for item in fit_source_payloads) / max(fit_source_count, 1)
    )
    payload = {
        "corpus_manifest_path": str(corpus_manifest_path),
        "corpus_manifest_kind": manifest_kind,
        "output_root": str(output_root),
        "config": asdict(config),
        "fit_source_count": fit_source_count,
        "converted_guide_count": converted_guide_count,
        "convertible_rate": converted_guide_count / max(fit_source_count, 1),
        "beats_prior_rate": beats_prior_count / max(fit_source_count, 1),
        "mean_evofit_ncc": mean_evofit_ncc,
        "mean_nominal_ncc": mean_nominal_ncc,
        "fit_sources": fit_source_payloads,
    }
    payload["baseline_comparison"] = _compare_baseline(payload, baseline_summary_path=baseline_summary_path)
    summary_json_path = output_root / "summary.json"
    summary_json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    summary_md_path = output_root / "summary.md"
    _write_summary_markdown(payload, summary_md_path, note=summary_note)
    provenance_report_json_path, provenance_report_md_path = _write_provenance_report(payload, output_root)
    manifest_path = _write_manifest(
        output_root=output_root,
        corpus_manifest_path=corpus_manifest_path,
        proposal_catalog_path=proposal_catalog_path,
        payload=payload,
        manifest_title=bundle_title,
    )
    return {
        "manifest_path": manifest_path,
        "summary_json_path": summary_json_path,
        "summary_md_path": summary_md_path,
        "proposal_catalog_path": proposal_catalog_path,
        "provenance_report_json_path": provenance_report_json_path,
        "provenance_report_md_path": provenance_report_md_path,
        "summary": payload,
    }


def run_reviewed_evofit(
    reviewed_manifest_path: Path | str = DEFAULT_REVIEWED_EVOFIT_MANIFEST_PATH,
    *,
    output_root: Path | str = DEFAULT_REVIEWED_EVOFIT_OUTPUT_ROOT,
    config: EvofitConfig | None = None,
    kind: str = "all",
    symbols: tuple[str, ...] | list[str] | None = None,
    guides_path: str | None = None,
    baseline_summary_path: Path | str | None = DEFAULT_AUTOMATIC_EVOFIT_BASELINE_SUMMARY_PATH,
) -> dict[str, Any]:
    """Run reviewed-only evofit from the frozen reviewed exemplar dataset."""

    reviewed_manifest_path = Path(reviewed_manifest_path)
    output_root = Path(output_root)
    result = run_evofit_from_corpus(
        reviewed_manifest_path,
        output_root=output_root,
        config=config,
        kind=kind,
        symbols=symbols,
        guides_path=guides_path,
        expected_manifest_kind="reviewed_exemplars",
        summary_note=(
            "each fit source is a human-reviewed exemplar crop from the reviewed annotation freeze; "
            "cleaned reviewed crops are preferred when present, automatic corpus tiers are not consumed in this stage."
        ),
        bundle_title="# TD-014 reviewed evofit bundle",
        baseline_summary_path=baseline_summary_path,
        reviewed_source_mode="prefer_cleaned",
    )
    raw_baseline_result = run_evofit_from_corpus(
        reviewed_manifest_path,
        output_root=output_root / "raw_reviewed_baseline",
        config=config,
        kind=kind,
        symbols=symbols,
        guides_path=guides_path,
        expected_manifest_kind="reviewed_exemplars",
        summary_note=(
            "raw reviewed baseline for comparison against cleanup-aware reviewed evofit; "
            "only raw reviewed crops are consumed in this stage."
        ),
        bundle_title="# TD-014 reviewed evofit raw baseline bundle",
        baseline_summary_path=None,
        reviewed_source_mode="raw_only",
    )

    summary = dict(result["summary"])
    summary["raw_reviewed_baseline_comparison"] = _compare_raw_reviewed_baseline(
        summary,
        raw_baseline_result["summary"],
    )
    summary["raw_reviewed_baseline_summary_path"] = str(raw_baseline_result["summary_json_path"])
    summary["raw_reviewed_baseline_manifest_path"] = str(raw_baseline_result["manifest_path"])

    summary_json_path = Path(result["summary_json_path"])
    summary_md_path = Path(result["summary_md_path"])
    summary_json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_summary_markdown(
        summary,
        summary_md_path,
        note=(
            "each fit source is a human-reviewed exemplar crop from the reviewed annotation freeze; "
            "cleaned reviewed crops are preferred when present, automatic corpus tiers are not consumed in this stage."
        ),
    )
    provenance_report_json_path, provenance_report_md_path = _write_provenance_report(summary, output_root)
    result["provenance_report_json_path"] = provenance_report_json_path
    result["provenance_report_md_path"] = provenance_report_md_path
    result["summary"] = summary
    return result
