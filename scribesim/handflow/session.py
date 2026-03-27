"""Stateful word/session composition for TD-014."""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from dataclasses import replace
from pathlib import Path

from scribesim.hand.profile import HandProfile
from scribesim.handvalidate import (
    StageReport,
    continuity_score,
    evaluate_gate,
    forced_lift_count,
    ink_state_determinism,
    ink_state_monotonicity,
    ocr_proxy_score,
    write_stage_report,
)
from scribesim.pathguide import (
    DEFAULT_REVIEWED_PROMOTED_GUIDE_CATALOG_PATH,
    build_active_folio_alphabet_v1_guides,
    build_starter_alphabet_v1_guides,
    DensePathGuide,
    EXTRACTED_GUIDES_PATH,
    GuideSample,
    GuideSource,
    STARTER_ALPHABET_V1_JOIN_SCHEDULES,
    load_legacy_guides_toml_as_dense,
    load_pathguides_toml,
)

from .controller import GuidedHandFlowController
from .model import SessionGuide, SessionResult, SessionWordGuide
from .render import render_trajectory_proof


PROOF_WORDS = ("und", "der", "wir", "in", "mir")
_DEFAULT_SOURCE_RESOLUTION_PPMM = 16.0
_GUIDE_ALIASES = {
    "v": "u",
    "s": "r",
    "z": "r",
    "ů": "u",
}


def describe_guide_catalog(
    guide_catalog: dict[str, DensePathGuide],
    *,
    source_label: str,
    guide_catalog_path: Path | str | None = None,
) -> dict[str, object]:
    """Summarize the nominal guide catalog used by handflow."""

    glyph_count = sum(1 for guide in guide_catalog.values() if guide.kind == "glyph")
    join_count = sum(1 for guide in guide_catalog.values() if guide.kind == "join")
    cleaned_count = 0
    raw_count = 0
    source_ids: set[str] = set()
    for guide in guide_catalog.values():
        for source in guide.sources:
            source_ids.add(source.source_id)
            if source.source_id.startswith("reviewed-cleaned:"):
                cleaned_count += 1
            if source.source_id.startswith("reviewed-raw:"):
                raw_count += 1
    return {
        "source_label": source_label,
        "guide_catalog_path": str(guide_catalog_path) if guide_catalog_path else "",
        "guide_count": len(guide_catalog),
        "glyph_count": glyph_count,
        "join_count": join_count,
        "reviewed_cleaned_source_count": cleaned_count,
        "reviewed_raw_source_count": raw_count,
        "source_id_count": len(source_ids),
    }


def guide_catalog_source_label(
    *,
    exact_symbols: bool,
    guide_catalog_path: Path | str | None = None,
) -> str:
    """Describe which nominal guide lane handflow resolved."""

    if guide_catalog_path is not None:
        return "override"
    if exact_symbols and DEFAULT_REVIEWED_PROMOTED_GUIDE_CATALOG_PATH.exists():
        return "reviewed_promoted"
    if exact_symbols:
        return "active_folio_exact"
    return "starter_plus_extracted"


def _resolved_entry(
    guide: DensePathGuide,
    *,
    requested_symbol: str,
    resolution_kind: str,
) -> tuple[DensePathGuide, str, str]:
    return guide, requested_symbol, resolution_kind


def _translate_guide(
    guide: DensePathGuide,
    *,
    dx_mm: float,
    dy_mm: float = 0.0,
) -> DensePathGuide:
    samples = tuple(
        replace(sample, x_mm=sample.x_mm + dx_mm, y_mm=sample.y_mm + dy_mm)
        for sample in guide.samples
    )
    return replace(guide, samples=samples)


def _stable_fraction(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha1(payload).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64)


def _baseline_offset_mm(
    profile: HandProfile | None,
    *,
    enabled: bool,
    word: str,
    word_index: int,
    char_index: int,
    symbol: str,
) -> float:
    if not enabled:
        return 0.0
    if profile is None:
        return 0.0
    jitter = profile.glyph.baseline_jitter_mm
    if jitter <= 0.0:
        return 0.0
    centered = _stable_fraction("baseline-jitter", word, word_index, char_index, symbol) * 2.0 - 1.0
    return centered * jitter


def _warp_join_vertical_offsets(
    guide: DensePathGuide,
    *,
    start_offset_mm: float,
    end_offset_mm: float,
) -> DensePathGuide:
    if math.isclose(start_offset_mm, 0.0, abs_tol=1e-9) and math.isclose(end_offset_mm, 0.0, abs_tol=1e-9):
        return guide
    x0 = guide.samples[0].x_mm
    x1 = guide.samples[-1].x_mm
    span = x1 - x0
    count = max(len(guide.samples) - 1, 1)
    samples = []
    for idx, sample in enumerate(guide.samples):
        if abs(span) > 1e-9:
            alpha = (sample.x_mm - x0) / span
        else:
            alpha = idx / count
        alpha = max(0.0, min(1.0, alpha))
        dy_mm = start_offset_mm * (1.0 - alpha) + end_offset_mm * alpha
        samples.append(replace(sample, y_mm=sample.y_mm + dy_mm))
    return replace(guide, samples=tuple(samples))


def _merge_guides(symbol: str, guides: list[DensePathGuide], *, kind: str) -> DensePathGuide:
    if not guides:
        raise ValueError("guides must be non-empty")
    merged_samples: list[GuideSample] = []
    merged_sources: list[GuideSource] = []
    for guide in guides:
        merged_sources.extend(guide.sources)
        for sample in guide.samples:
            if merged_samples:
                prev = merged_samples[-1]
                if (
                    math.isclose(prev.x_mm, sample.x_mm, abs_tol=1e-9)
                    and math.isclose(prev.y_mm, sample.y_mm, abs_tol=1e-9)
                    and prev.contact == sample.contact
                ):
                    continue
            merged_samples.append(sample)
    start_x = merged_samples[0].x_mm
    end_x = max(sample.x_mm for sample in merged_samples)
    return DensePathGuide(
        symbol=symbol,
        kind=kind,
        samples=tuple(merged_samples),
        x_advance_mm=end_x - start_x,
        x_height_mm=guides[0].x_height_mm,
        entry_tangent=guides[0].entry_tangent,
        exit_tangent=guides[-1].exit_tangent,
        sources=tuple(merged_sources),
    )


def _build_transition(
    *,
    symbol: str,
    start: tuple[float, float],
    end: tuple[float, float],
    x_height_mm: float,
    contact: bool,
    x_advance_mm: float,
) -> DensePathGuide:
    mid_x = (start[0] + end[0]) * 0.5
    if contact:
        crest_y = max(start[1], end[1], x_height_mm * 0.82)
        samples = (
            GuideSample(start[0], start[1], 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.15),
            GuideSample(mid_x, crest_y, 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.15),
            GuideSample(end[0], end[1], 1.0, 0.0, contact=True, pressure_nominal=0.34, corridor_half_width_mm=0.15),
        )
    else:
        lift_y = max(start[1], end[1]) + x_height_mm * 0.28
        samples = (
            GuideSample(start[0], start[1], 1.0, 0.0, contact=False, pressure_nominal=0.0, corridor_half_width_mm=0.14),
            GuideSample(mid_x, lift_y, 1.0, 0.0, contact=False, pressure_nominal=0.0, corridor_half_width_mm=0.14),
            GuideSample(end[0], end[1], 1.0, 0.0, contact=False, pressure_nominal=0.0, corridor_half_width_mm=0.14),
        )
    return DensePathGuide(
        symbol=symbol,
        kind="transition",
        samples=samples,
        x_advance_mm=x_advance_mm,
        x_height_mm=x_height_mm,
        entry_tangent=(samples[0].tangent_dx, samples[0].tangent_dy),
        exit_tangent=(samples[-1].tangent_dx, samples[-1].tangent_dy),
        sources=(
            GuideSource(
                source_id=f"stateful-session:{symbol}",
                source_path="scribesim/handflow/session.py",
                confidence_tier="accepted",
                split="validation",
                source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
            ),
        ),
    )


def load_word_guide_catalog(
    *,
    x_height_mm: float = 3.5,
    exact_symbols: bool = False,
    guide_catalog_path: Path | str | None = None,
) -> dict[str, DensePathGuide]:
    """Load the guide catalog for guided handwriting sessions."""

    if guide_catalog_path is not None:
        return load_pathguides_toml(guide_catalog_path)

    if exact_symbols:
        if DEFAULT_REVIEWED_PROMOTED_GUIDE_CATALOG_PATH.exists():
            return load_pathguides_toml(DEFAULT_REVIEWED_PROMOTED_GUIDE_CATALOG_PATH)
        return build_active_folio_alphabet_v1_guides(x_height_mm=x_height_mm)

    guides = build_starter_alphabet_v1_guides(x_height_mm=x_height_mm)
    extracted = load_legacy_guides_toml_as_dense(
        EXTRACTED_GUIDES_PATH,
        x_height_mm=x_height_mm,
        split="validation",
        source_resolution_ppmm=_DEFAULT_SOURCE_RESOLUTION_PPMM,
    )
    for symbol, guide in extracted.items():
        guides.setdefault(symbol, guide)
    return guides


def resolve_character_guide(
    char: str,
    guide_catalog: dict[str, DensePathGuide],
) -> tuple[DensePathGuide, str, str]:
    if char in guide_catalog:
        return _resolved_entry(guide_catalog[char], requested_symbol=char, resolution_kind="exact")
    lowered = char.lower()
    if lowered in guide_catalog:
        kind = "exact" if lowered == char else "normalized"
        return _resolved_entry(guide_catalog[lowered], requested_symbol=char, resolution_kind=kind)
    normalized = unicodedata.normalize("NFKD", lowered).encode("ascii", "ignore").decode("ascii")
    if normalized in guide_catalog:
        kind = "exact" if normalized == char else "normalized"
        return _resolved_entry(guide_catalog[normalized], requested_symbol=char, resolution_kind=kind)
    alias = _GUIDE_ALIASES.get(lowered) or _GUIDE_ALIASES.get(normalized)
    if alias and alias in guide_catalog:
        return _resolved_entry(guide_catalog[alias], requested_symbol=char, resolution_kind="alias")
    raise KeyError(f"missing guide for character: {char}")


def _resolve_character_guide(char: str, guide_catalog: dict[str, DensePathGuide]) -> DensePathGuide:
    guide, _, _ = resolve_character_guide(char, guide_catalog)
    return guide


def build_word_session(
    word: str,
    *,
    guide_catalog: dict[str, DensePathGuide],
    start_x_mm: float = 0.0,
    profile: HandProfile | None = None,
    word_index: int = 0,
    activate_baseline_jitter: bool = False,
) -> tuple[tuple[SessionGuide, ...], DensePathGuide]:
    """Compose a word into glyph/join session guides and a merged reference guide."""

    if not word:
        raise ValueError("word must be non-empty")

    guides: list[SessionGuide] = []
    merged: list[DensePathGuide] = []
    cursor_x = start_x_mm
    x_height_mm = next(iter(guide_catalog.values())).x_height_mm

    offsets_mm = [
        _baseline_offset_mm(
            profile,
            enabled=activate_baseline_jitter,
            word=word,
            word_index=word_index,
            char_index=idx,
            symbol=char,
        )
        for idx, char in enumerate(word)
    ]

    for idx, char in enumerate(word):
        base_glyph, requested_symbol, resolution_kind = resolve_character_guide(char, guide_catalog)
        glyph = _translate_guide(
            base_glyph,
            dx_mm=cursor_x - base_glyph.samples[0].x_mm,
            dy_mm=offsets_mm[idx],
        )
        guides.append(
            SessionGuide(
                symbol=char,
                guide=glyph,
                kind="glyph",
                word=word,
                word_index=0,
                requested_symbol=requested_symbol,
                resolved_symbol=base_glyph.symbol,
                resolution_kind=resolution_kind,
            )
        )
        merged.append(glyph)
        cursor_x += base_glyph.x_advance_mm

        if idx + 1 >= len(word):
            continue
        nxt = word[idx + 1]
        join_symbol = f"{char}->{nxt}"
        if join_symbol in guide_catalog:
            base_join = guide_catalog[join_symbol]
            join = _translate_guide(
                base_join,
                dx_mm=glyph.samples[-1].x_mm - base_join.samples[0].x_mm,
                dy_mm=0.0,
            )
            join = _warp_join_vertical_offsets(
                join,
                start_offset_mm=offsets_mm[idx],
                end_offset_mm=offsets_mm[idx + 1],
            )
            cursor_x = join.samples[0].x_mm + base_join.x_advance_mm
        else:
            next_glyph, _, _ = resolve_character_guide(nxt, guide_catalog)
            join_advance = x_height_mm * 0.14
            next_entry_x = cursor_x + join_advance
            next_entry_y = next_glyph.samples[0].y_mm + offsets_mm[idx + 1]
            join = _build_transition(
                symbol=join_symbol,
                start=(glyph.samples[-1].x_mm, glyph.samples[-1].y_mm),
                end=(next_entry_x, next_entry_y),
                x_height_mm=x_height_mm,
                contact=True,
                x_advance_mm=join_advance,
            )
            cursor_x += join_advance
        guides.append(
            SessionGuide(
                symbol=join_symbol,
                guide=join,
                kind="join",
                word=word,
                word_index=0,
                requested_symbol=join_symbol,
                resolved_symbol=join.symbol,
                resolution_kind="exact" if join_symbol in guide_catalog else "derived",
            )
        )
        merged.append(join)

    composite = _merge_guides(word, merged, kind="word")
    composite = replace(composite, x_advance_mm=cursor_x - start_x_mm)
    return tuple(guides), composite


def build_proof_vocabulary_session(
    words: tuple[str, ...] = PROOF_WORDS,
    *,
    guide_catalog: dict[str, DensePathGuide],
    profile: HandProfile | None = None,
    activate_baseline_jitter: bool = False,
) -> tuple[tuple[SessionGuide, ...], dict[str, DensePathGuide]]:
    """Compose a persistent proof-word session with air transitions between words."""

    session: list[SessionGuide] = []
    word_guides: dict[str, DensePathGuide] = {}
    cursor_x = 0.0
    x_height_mm = next(iter(guide_catalog.values())).x_height_mm

    for word_index, word in enumerate(words):
        word_items, word_guide = build_word_session(
            word,
            guide_catalog=guide_catalog,
            start_x_mm=cursor_x,
            profile=profile,
            word_index=word_index,
            activate_baseline_jitter=activate_baseline_jitter,
        )
        word_guides[word] = word_guide
        for item in word_items:
            session.append(replace(item, word_index=word_index))
        cursor_x += word_guide.x_advance_mm

        if word_index + 1 >= len(words):
            continue
        next_word = words[word_index + 1]
        next_start = cursor_x + x_height_mm * 0.55
        boundary = _build_transition(
            symbol=f"{word}->space->{next_word}",
            start=(word_guide.samples[-1].x_mm, word_guide.samples[-1].y_mm),
            end=(
                next_start,
                _resolve_character_guide(next_word[0], guide_catalog).samples[0].y_mm
                + _baseline_offset_mm(
                    profile,
                    enabled=activate_baseline_jitter,
                    word=next_word,
                    word_index=word_index + 1,
                    char_index=0,
                    symbol=next_word[0],
                ),
            ),
            x_height_mm=x_height_mm,
            contact=False,
            x_advance_mm=x_height_mm * 0.55,
        )
        session.append(
            SessionGuide(
                symbol=boundary.symbol,
                guide=boundary,
                kind="transition",
                word=next_word,
                word_index=word_index + 1,
            )
        )
        cursor_x = next_start

    return tuple(session), word_guides


def build_line_session(
    line_text: str,
    *,
    guide_catalog: dict[str, DensePathGuide],
    start_x_mm: float = 0.0,
    profile: HandProfile | None = None,
    activate_baseline_jitter: bool = False,
) -> tuple[tuple[SessionGuide, ...], DensePathGuide, tuple[SessionWordGuide, ...]]:
    """Compose a text line into a persistent multi-word session."""

    words = tuple(part for part in line_text.split() if part)
    if not words:
        raise ValueError("line_text must contain at least one word")

    session: list[SessionGuide] = []
    line_parts: list[DensePathGuide] = []
    word_guides: list[SessionWordGuide] = []
    cursor_x = start_x_mm
    x_height_mm = next(iter(guide_catalog.values())).x_height_mm

    for word_index, word in enumerate(words):
        word_items, word_guide = build_word_session(
            word,
            guide_catalog=guide_catalog,
            start_x_mm=cursor_x,
            profile=profile,
            word_index=word_index,
            activate_baseline_jitter=activate_baseline_jitter,
        )
        word_guides.append(SessionWordGuide(text=word, word_index=word_index, guide=word_guide))
        line_parts.append(word_guide)
        for item in word_items:
            session.append(replace(item, word_index=word_index))
        cursor_x += word_guide.x_advance_mm

        if word_index + 1 >= len(words):
            continue
        next_word = words[word_index + 1]
        next_start = cursor_x + x_height_mm * 0.55
        boundary = _build_transition(
            symbol=f"{word}->space->{next_word}",
            start=(word_guide.samples[-1].x_mm, word_guide.samples[-1].y_mm),
            end=(
                next_start,
                _resolve_character_guide(next_word[0], guide_catalog).samples[0].y_mm
                + _baseline_offset_mm(
                    profile,
                    enabled=activate_baseline_jitter,
                    word=next_word,
                    word_index=word_index + 1,
                    char_index=0,
                    symbol=next_word[0],
                ),
            ),
            x_height_mm=x_height_mm,
            contact=False,
            x_advance_mm=x_height_mm * 0.55,
        )
        session.append(
            SessionGuide(
                symbol=boundary.symbol,
                guide=boundary,
                kind="transition",
                word=next_word,
                word_index=word_index + 1,
            )
        )
        line_parts.append(boundary)
        cursor_x = next_start

    line_guide = _merge_guides(line_text, line_parts, kind="line")
    line_guide = replace(line_guide, x_advance_mm=cursor_x - start_x_mm)
    return tuple(session), line_guide, tuple(word_guides)


def _guide_bounds(guide: DensePathGuide, *, margin_mm: float = 1.0) -> tuple[float, float, float, float]:
    contact = [sample for sample in guide.samples if sample.contact]
    x_min = min(sample.x_mm for sample in contact) - margin_mm
    x_max = max(sample.x_mm for sample in contact) + margin_mm
    y_min = min(sample.y_mm for sample in contact) - margin_mm
    y_max = max(sample.y_mm for sample in contact) + margin_mm
    return (x_min, x_max, y_min, y_max)


def _session_levels(result: SessionResult, *, word: str) -> list[float]:
    return [
        entry.end_ink_reservoir
        for entry in result.state_trace
        if entry.word == word and entry.kind in {"glyph", "join"}
    ]


def _guide_residual_baseline_drift(result: SessionResult, guide: DensePathGuide) -> float:
    contact_refs = [sample for sample in guide.samples if sample.contact]
    if not contact_refs:
        return 0.0

    baseline_y = min(sample.y_mm for sample in contact_refs)
    baseline_band_limit = baseline_y + guide.x_height_mm * 0.35
    residuals = [
        observed.y_mm - reference.y_mm
        for observed, reference in zip(result.guide_aligned_trajectory, guide.samples, strict=False)
        if reference.contact and reference.y_mm <= baseline_band_limit
    ]
    if len(residuals) < 2:
        residuals = [
            observed.y_mm - reference.y_mm
            for observed, reference in zip(result.guide_aligned_trajectory, guide.samples, strict=False)
            if reference.contact
        ]
    if len(residuals) < 2:
        return 0.0
    mean = sum(residuals) / len(residuals)
    variance = sum((value - mean) ** 2 for value in residuals) / len(residuals)
    return math.sqrt(variance) / max(guide.x_height_mm, 1e-6)


def run_stateful_word_proof(
    output_dir: Path | str,
    *,
    profile: HandProfile,
    words: tuple[str, ...] = PROOF_WORDS,
    dpi: int = 220,
    supersample: int = 3,
    dt: float = 0.002,
    guide_catalog_path: Path | str | None = None,
    exact_symbols: bool = False,
) -> dict[str, StageReport]:
    """Render proof words with persistent state and emit gate reports."""

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    guide_catalog = load_word_guide_catalog(
        x_height_mm=profile.letterform.x_height_mm,
        exact_symbols=exact_symbols,
        guide_catalog_path=guide_catalog_path,
    )
    controller = GuidedHandFlowController(profile)
    reports: dict[str, StageReport] = {}

    for word in words:
        word_items, word_guide = build_word_session(
            word,
            guide_catalog=guide_catalog,
            start_x_mm=0.0,
            profile=profile,
        )
        result = controller.simulate_session(word_items, dt=dt)
        rerun = controller.simulate_session(word_items, dt=dt)
        image_path = output_root / f"{word}.png"
        rendered = render_trajectory_proof(
            result.trajectory,
            profile=profile,
            output_path=image_path,
            dpi=dpi,
            supersample=supersample,
            bounds_mm=_guide_bounds(word_guide),
        )
        reference = render_trajectory_proof(
            result.guide_aligned_trajectory,
            profile=profile,
            dpi=dpi,
            supersample=supersample,
            bounds_mm=_guide_bounds(word_guide),
        )
        metrics = {
            "continuity_score": (
                sum(
                    continuity_score(segment.guide_aligned_trajectory, entry.guide)
                    for entry, segment in zip(word_items, result.segments, strict=False)
                    if entry.kind == "join"
                )
                / max(sum(1 for entry in word_items if entry.kind == "join"), 1)
            ),
            "forced_lift_count": float(
                sum(
                    int(
                        entry.kind == "join"
                        and STARTER_ALPHABET_V1_JOIN_SCHEDULES.get(entry.symbol, "contact_only") == "contact_only"
                        and forced_lift_count(segment.guide_aligned_trajectory, entry.guide) > 0
                    )
                    for entry, segment in zip(word_items, result.segments, strict=False)
                )
            ),
            "ocr_proxy_score": ocr_proxy_score(rendered, reference),
            "baseline_drift_ratio": _guide_residual_baseline_drift(result, word_guide),
            "ink_state_monotonicity": ink_state_monotonicity(_session_levels(result, word=word)),
            "ink_state_determinism": ink_state_determinism(
                _session_levels(result, word=word),
                _session_levels(rerun, word=word),
            ),
        }
        gate = evaluate_gate("stateful_word", metrics)
        report = StageReport(
            stage=f"stateful_word:{word}",
            metrics=metrics,
            gate=gate,
            notes=(f"segments={len(word_items)}",),
        )
        write_stage_report(report, output_root)
        reports[word] = report

    session_items, _ = build_proof_vocabulary_session(words, guide_catalog=guide_catalog, profile=profile)
    session_result = controller.simulate_session(session_items, dt=dt)
    state_trace_payload = [
        {
            "symbol": entry.symbol,
            "kind": entry.kind,
            "word": entry.word,
            "word_index": entry.word_index,
            "start_time_s": entry.start_time_s,
            "end_time_s": entry.end_time_s,
            "start_speed_mm_s": entry.start_speed_mm_s,
            "end_speed_mm_s": entry.end_speed_mm_s,
            "start_pressure": entry.start_pressure,
            "end_pressure": entry.end_pressure,
            "start_ink_reservoir": entry.start_ink_reservoir,
            "end_ink_reservoir": entry.end_ink_reservoir,
            "dip_before": entry.dip_before,
        }
        for entry in session_result.state_trace
    ]
    (output_root / "state_trace.json").write_text(json.dumps(state_trace_payload, indent=2, sort_keys=True) + "\n")

    summary = {
        "words": {word: {"passed": report.gate.passed, "metrics": report.metrics} for word, report in reports.items()},
        "all_passed": all(report.gate.passed for report in reports.values()),
        "guide_catalog": describe_guide_catalog(
            guide_catalog,
            source_label=guide_catalog_source_label(
                exact_symbols=exact_symbols,
                guide_catalog_path=guide_catalog_path,
            ),
            guide_catalog_path=guide_catalog_path,
        ),
    }
    (output_root / "proof_vocabulary_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    return reports
