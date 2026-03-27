"""Experimental folio integration for TD-014 guided handflow."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

import numpy as np

from scribesim.hand.profile import HandProfile
from scribesim.handvalidate import TrajectorySample
from scribesim.pathguide import DensePathGuide

from .controller import GuidedHandFlowController
from .model import (
    GuidedFolioLineStatus,
    GuidedFolioResolutionError,
    GuidedFolioSimulation,
    SessionGuide,
)
from .render import render_trajectory_canvas
from .session import build_line_session, describe_guide_catalog, guide_catalog_source_label, load_word_guide_catalog


def _translate_dense_guide(guide: DensePathGuide, *, dy_mm: float = 0.0) -> DensePathGuide:
    return replace(
        guide,
        samples=tuple(replace(sample, y_mm=sample.y_mm + dy_mm) for sample in guide.samples),
    )


def _translate_session_guides(
    items: tuple[SessionGuide, ...],
    *,
    dy_mm: float = 0.0,
) -> tuple[SessionGuide, ...]:
    return tuple(replace(item, guide=_translate_dense_guide(item.guide, dy_mm=dy_mm)) for item in items)


def _line_resolution_status(
    line_index: int,
    line_text: str,
    line_items: tuple[SessionGuide, ...],
    *,
    resolution_error: str | None = None,
) -> GuidedFolioLineStatus:
    glyphs = [item for item in line_items if item.kind == "glyph"]
    glyph_count = len(glyphs)
    alias_count = sum(1 for item in glyphs if item.resolution_kind == "alias")
    normalized_count = sum(1 for item in glyphs if item.resolution_kind == "normalized")
    exact_count = sum(1 for item in glyphs if item.resolution_kind == "exact")
    non_exact_symbols = tuple(
        f"{item.requested_symbol}->{item.resolved_symbol} ({item.resolution_kind})"
        for item in glyphs
        if item.resolution_kind != "exact"
    )
    coverage = exact_count / max(glyph_count, 1)
    return GuidedFolioLineStatus(
        line_index=line_index,
        line_text=line_text,
        glyph_count=glyph_count,
        exact_character_coverage=coverage,
        alias_substitution_count=alias_count,
        normalized_substitution_count=normalized_count,
        exact_only_passed=(glyph_count > 0 and exact_count == glyph_count and resolution_error is None),
        non_exact_symbols=non_exact_symbols,
        resolution_error=resolution_error,
    )


def _resolution_summary(line_statuses: tuple[GuidedFolioLineStatus, ...]) -> dict[str, object]:
    glyph_count = sum(status.glyph_count for status in line_statuses)
    exact_glyphs = sum(round(status.exact_character_coverage * status.glyph_count) for status in line_statuses)
    alias_count = sum(status.alias_substitution_count for status in line_statuses)
    normalized_count = sum(status.normalized_substitution_count for status in line_statuses)
    return {
        "glyph_count": glyph_count,
        "exact_character_coverage": exact_glyphs / max(glyph_count, 1),
        "alias_substitution_count": alias_count,
        "normalized_substitution_count": normalized_count,
        "exact_only_passed": all(status.exact_only_passed for status in line_statuses),
        "line_statuses": [
            {
                "line_index": status.line_index,
                "line_text": status.line_text,
                "glyph_count": status.glyph_count,
                "exact_character_coverage": status.exact_character_coverage,
                "alias_substitution_count": status.alias_substitution_count,
                "normalized_substitution_count": status.normalized_substitution_count,
                "exact_only_passed": status.exact_only_passed,
                "non_exact_symbols": list(status.non_exact_symbols),
                "resolution_error": status.resolution_error,
            }
            for status in line_statuses
        ],
    }


def simulate_guided_folio_lines(
    lines: list[str],
    *,
    profile: HandProfile,
    x_height_mm: float = 3.8,
    line_spacing_mm: float = 12.0,
    margin_left_mm: float = 5.0,
    margin_top_mm: float = 5.0,
    exact_symbols: bool = True,
    guide_catalog_path: Path | str | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> GuidedFolioSimulation:
    """Simulate guided folio trajectories before rasterization."""

    guide_catalog = load_word_guide_catalog(
        x_height_mm=x_height_mm,
        exact_symbols=exact_symbols,
        guide_catalog_path=guide_catalog_path,
    )
    page_trajectory: list[TrajectorySample] = []
    aligned_page_trajectory: list[TrajectorySample] = []
    line_statuses: list[GuidedFolioLineStatus] = []
    total_lines = len(lines)

    for li, line_text in enumerate(lines):
        if progress_callback is not None:
            progress_callback(
                {
                    "stage": "line_start",
                    "line_index": li,
                    "total_lines": total_lines,
                    "line_text": line_text,
                }
            )
        if not line_text.strip():
            if progress_callback is not None:
                progress_callback(
                    {
                        "stage": "line_complete",
                        "line_index": li,
                        "total_lines": total_lines,
                        "line_text": line_text,
                    }
                )
            continue

        controller = GuidedHandFlowController(profile, activate_base_pressure=True)
        try:
            line_items, _, _ = build_line_session(
                line_text,
                guide_catalog=guide_catalog,
                start_x_mm=margin_left_mm,
                profile=profile,
                activate_baseline_jitter=True,
            )
        except KeyError as exc:
            status = _line_resolution_status(li, line_text, tuple(), resolution_error=str(exc))
            line_statuses.append(status)
            if exact_symbols:
                raise GuidedFolioResolutionError(
                    f"exact-symbol guided folio render failed on line {li + 1}: {exc}",
                    line_statuses=tuple(line_statuses),
                ) from exc
            continue

        status = _line_resolution_status(li, line_text, line_items)
        line_statuses.append(status)
        if exact_symbols and not status.exact_only_passed:
            raise GuidedFolioResolutionError(
                f"exact-symbol guided folio render refused non-exact glyphs on line {li + 1}: "
                + ", ".join(status.non_exact_symbols),
                line_statuses=tuple(line_statuses),
            )

        line_offset_y = margin_top_mm + li * line_spacing_mm
        shifted_items = _translate_session_guides(line_items, dy_mm=line_offset_y)
        result = controller.simulate_session(shifted_items, dt=0.002)
        if page_trajectory:
            prev = page_trajectory[-1]
            gap_sample = TrajectorySample(
                x_mm=prev.x_mm,
                y_mm=prev.y_mm,
                contact=False,
                width_mm=None,
                pressure=0.0,
            )
            page_trajectory.append(gap_sample)
            aligned_page_trajectory.append(gap_sample)
        page_trajectory.extend(result.trajectory)
        aligned_page_trajectory.extend(result.guide_aligned_trajectory)
        if progress_callback is not None:
            progress_callback(
                {
                    "stage": "line_complete",
                    "line_index": li,
                    "total_lines": total_lines,
                    "line_text": line_text,
                }
            )

    if not page_trajectory:
        raise ValueError("no non-empty lines to render")

    return GuidedFolioSimulation(
        trajectory=tuple(page_trajectory),
        guide_aligned_trajectory=tuple(aligned_page_trajectory),
        line_statuses=tuple(line_statuses),
        exact_symbols=exact_symbols,
    )


def render_guided_folio_lines(
    lines: list[str],
    *,
    profile: HandProfile,
    dpi: int = 300,
    supersample: int = 4,
    x_height_mm: float = 3.8,
    line_spacing_mm: float = 12.0,
    page_width_mm: float = 80.0,
    page_height_mm: float | None = None,
    margin_left_mm: float = 5.0,
    margin_top_mm: float = 5.0,
    exact_symbols: bool = True,
    guide_catalog_path: Path | str | None = None,
    return_metadata: bool = False,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[np.ndarray, np.ndarray] | tuple[np.ndarray, np.ndarray, dict[str, object]]:
    """Render a folio page using the guided handflow controller."""

    if page_height_mm is None:
        page_height_mm = margin_top_mm * 2 + max(1, len(lines)) * line_spacing_mm

    simulation = simulate_guided_folio_lines(
        lines,
        profile=profile,
        x_height_mm=x_height_mm,
        line_spacing_mm=line_spacing_mm,
        margin_left_mm=margin_left_mm,
        margin_top_mm=margin_top_mm,
        exact_symbols=exact_symbols,
        guide_catalog_path=guide_catalog_path,
        progress_callback=progress_callback,
    )

    page_arr, heat_arr = render_trajectory_canvas(
        simulation.trajectory,
        profile=profile,
        dpi=dpi,
        supersample=supersample,
        bounds_mm=(0.0, page_width_mm, 0.0, page_height_mm),
        return_heatmap=True,
    )
    if not return_metadata:
        return page_arr, heat_arr
    aligned_page_arr, aligned_heat_arr = render_trajectory_canvas(
        simulation.guide_aligned_trajectory,
        profile=profile,
        dpi=dpi,
        supersample=supersample,
        bounds_mm=(0.0, page_width_mm, 0.0, page_height_mm),
        return_heatmap=True,
    )
    catalog = load_word_guide_catalog(
        x_height_mm=x_height_mm,
        exact_symbols=exact_symbols,
        guide_catalog_path=guide_catalog_path,
    )
    return page_arr, heat_arr, {
        "render_trajectory_mode": "actual",
        "exact_symbols": exact_symbols,
        "activated_parameters": {
            "folio.base_pressure": profile.folio.base_pressure,
            "glyph.baseline_jitter_mm": profile.glyph.baseline_jitter_mm,
        },
        "guide_catalog": describe_guide_catalog(
            catalog,
            source_label=guide_catalog_source_label(
                exact_symbols=exact_symbols,
                guide_catalog_path=guide_catalog_path,
            ),
            guide_catalog_path=guide_catalog_path,
        ),
        "resolution": _resolution_summary(simulation.line_statuses),
        "aligned_page": aligned_page_arr,
        "aligned_heat": aligned_heat_arr,
    }
