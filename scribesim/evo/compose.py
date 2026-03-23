"""Line and folio composition for the evolutionary scribe (TD-007 Part 5+7).

Chains words into lines and folios. Each word genome is rendered in its own
coordinate space then composited onto the line/page canvas. A progress image
is saved (and fitness printed) after each word so you can watch the line fill.
"""

from __future__ import annotations

import copy
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Any

import numpy as np
from PIL import Image

from scribesim.evo.genome import WordGenome, genome_from_guides, preprocess_roman_numerals
from scribesim.evo.allograph import AllographConfig, apply_contextual_allographs
from scribesim.evo.engine import evolve_word, EvolutionConfig
from scribesim.evo.renderer import render_word_from_genome, _PARCHMENT
from scribesim.evo.style import StyleMemory
from scribesim.ink.cycle import DipEvent, InkState

if TYPE_CHECKING:
    from scribesim.hand.profile import HandProfile


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@dataclass
class WordContext:
    """Context passed between consecutive words."""
    cursor_x_mm: float = 0.0
    baseline_y_mm: float = 0.0
    ink_reservoir: float = 0.85
    fatigue: float = 0.0
    emotional_state: str = "normal"


@dataclass
class FolioState:
    """Per-folio layout and scribe state."""
    folio_id: str = "f01r"
    lines: list[str] = field(default_factory=list)
    margin_left_mm: float = 3.0
    margin_top_mm: float = 5.0
    line_spacing_mm: float = 9.5
    x_height_mm: float = 3.8
    page_width_mm: float = 70.0
    page_height_mm: float = 100.0
    ink_reservoir: float = 0.85
    fatigue: float = 0.0
    emotional_state: str = "normal"
    dip_cycle_words: int = 35

    @classmethod
    def from_folio_json(cls, folio_path: Path) -> "FolioState":
        data = json.loads(Path(folio_path).read_text())
        lines = [line.get("text", "") for line in data.get("lines", [])]
        return cls(folio_id=data.get("id", "f01r"), lines=lines)


# ---------------------------------------------------------------------------
# Word genome cache
# ---------------------------------------------------------------------------

_GENOME_CACHE: dict[str, WordGenome] = {}


def _get_genome(
    word: str,
    context: WordContext,
    config: EvolutionConfig | None,
    evolve: bool = True,
    x_height_mm: float = 3.8,
    guides_path=None,
    exemplar_root=None,
    nib_width_mm: float = 0.65,
    letter_gap: float = 0.12,
    use_cache: bool = True,
    style_prior=None,
) -> tuple[WordGenome, float]:
    """Return (genome, fitness). Evolves if evolve=True and not cached."""
    if evolve and config is None:
        config = EvolutionConfig()

    guides_key = str(Path(guides_path).resolve()) if guides_path else "default-guides"
    mode_key = (
        f"evolved_{config.pop_size}_{config.generations}_{round(config.eval_dpi, 1)}"
        if evolve and config is not None
        else "seed"
    )
    cache_key = (
        f"{word}_{context.emotional_state}_"
        f"{round(x_height_mm, 3)}_{round(letter_gap, 3)}_{round(nib_width_mm, 3)}_"
        f"{round(context.fatigue, 3)}_{guides_key}_{mode_key}"
    )

    if use_cache and cache_key in _GENOME_CACHE:
        g = copy.deepcopy(_GENOME_CACHE[cache_key])
        # Small per-instance variation
        for i in range(len(g.baseline_drift)):
            g.baseline_drift[i] += random.gauss(0, 0.02)
        return g, 0.0

    if evolve and config is not None:
        result = evolve_word(
            word,
            config=config,
            fatigue=context.fatigue,
            emotional_state=context.emotional_state,
            verbose=False,
            guides_path=guides_path,
            x_height_mm=x_height_mm,
            exemplar_root=exemplar_root,
            style_prior=style_prior,
        )
        genome = result.best_genome
        fitness = result.best_fitness
        if use_cache:
            _GENOME_CACHE[cache_key] = copy.deepcopy(genome)
        return genome, fitness
    else:
        genome = genome_from_guides(word, x_height_mm=x_height_mm, guides_path=guides_path, letter_gap=letter_gap)
        if use_cache:
            _GENOME_CACHE[cache_key] = copy.deepcopy(genome)
        return genome, 0.0


# ---------------------------------------------------------------------------
# Line canvas helpers
# ---------------------------------------------------------------------------

def _make_line_canvas(width_mm: float, height_mm: float, dpi: float) -> Image.Image:
    px_per_mm = dpi / 25.4
    w = max(10, int(width_mm * px_per_mm))
    h = max(10, int(height_mm * px_per_mm))
    return Image.new("RGB", (w, h), _PARCHMENT)


def _paste_word(
    canvas: Image.Image,
    word_img: np.ndarray,
    x_offset_px: int,
    baseline_px: int,
    word_baseline_px: int,
) -> None:
    """Paste a word image onto the line canvas, aligning baselines."""
    wimg = Image.fromarray(word_img, "RGB")
    # Align so word_baseline_px in word image = baseline_px in canvas
    y_paste = baseline_px - word_baseline_px
    canvas.paste(wimg, (x_offset_px, y_paste))


def _paste_heatmap(canvas: Image.Image, heat_img: np.ndarray, x_offset_px: int) -> None:
    himg = Image.fromarray(heat_img, "L")
    canvas.paste(himg, (x_offset_px, 0))


# ---------------------------------------------------------------------------
# render_line — word-by-word with progress
# ---------------------------------------------------------------------------

def _render_ink_graph(
    reservoir_snapshots: list[tuple[int, float]],
    dip_events: list[int],
    width: int = 600,
    height: int = 150,
) -> Image.Image:
    """Render a PIL-based ink reservoir sawtooth graph.

    Args:
        reservoir_snapshots: List of (word_index, reservoir_level) at start of each word.
        dip_events: Word indices where a dip occurred.
        width, height: Canvas dimensions in pixels.
    """
    from PIL import ImageDraw as _ImageDraw
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = _ImageDraw.Draw(img)

    # Margins
    mx, my = 40, 15
    plot_w = width - mx * 2
    plot_h = height - my * 2

    # Axes
    draw.rectangle([mx, my, mx + plot_w, my + plot_h], outline=(180, 180, 180))

    if len(reservoir_snapshots) < 2:
        return img

    n_words = reservoir_snapshots[-1][0] + 1

    def to_xy(word_idx: int, reservoir: float) -> tuple[int, int]:
        x = mx + int(word_idx / max(1, n_words - 1) * plot_w)
        y = my + plot_h - int(reservoir * plot_h)
        return x, y

    # Dip event vertical lines (blue)
    for di in dip_events:
        x, _ = to_xy(di, 1.0)
        draw.line([(x, my), (x, my + plot_h)], fill=(100, 160, 220), width=1)

    # Reservoir polyline (dark brown — ink colour)
    pts = [to_xy(wi, r) for wi, r in reservoir_snapshots]
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=(60, 35, 15), width=2)

    # Threshold lines
    for level, colour in [(0.22, (200, 180, 60)), (0.15, (200, 80, 60))]:
        _, ty = to_xy(0, level)
        draw.line([(mx, ty), (mx + plot_w, ty)], fill=colour, width=1)

    # Axis labels (minimal — PIL default font)
    draw.text((2, my), "1.0", fill=(100, 100, 100))
    draw.text((2, my + plot_h - 10), "0.0", fill=(100, 100, 100))
    draw.text((mx, height - 12), "word →", fill=(100, 100, 100))

    return img


def render_line(
    line_text: str,
    dpi: float = 300.0,
    nib_width_mm: float = 0.65,
    nib_angle_deg: float = 42.0,
    x_height_mm: float = 3.8,
    word_gap_mm: float | None = None,
    line_height_mm: float = 14.0,
    evolve: bool = False,
    config: EvolutionConfig | None = None,
    guides_path=None,
    exemplar_root=None,
    progress_dir: Path | None = None,
    verbose: bool = True,
    variation: float = 1.0,
    show_ink_state: bool = False,
    ink_graph_path: Path | None = None,
    letter_gap: float = 0.12,
    profile: "HandProfile | None" = None,
    use_cache: bool = True,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
    progress_granularity: str = "line",
    line_index: int | None = None,
    total_lines: int | None = None,
    return_heatmap: bool = False,
    character_model: str = "standard",
    character_model_config: AllographConfig | None = None,
) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    """Render a line of text word by word.

    Saves a running composite PNG after each word when progress_dir is set.
    Prints per-word stats (letter count, width, fitness if evolved).

    Args:
        line_text: Space-separated words.
        dpi: Output resolution.
        nib_width_mm: Nib width for rendering.
        nib_angle_deg: Nib angle.
        x_height_mm: X-height in mm (scales all letterforms).
        word_gap_mm: Space between words (default = 0.8 × x_height).
        line_height_mm: Canvas height for the line.
        evolve: Run evolutionary optimisation per word (slow).
        config: Evolution config (used only when evolve=True).
        progress_dir: Directory to save progress images. Images are named
            line_w001.png, line_w002.png … each showing the line so far.
        verbose: Print per-word progress to stdout.

    Returns:
        RGB numpy array of the full composed line, or `(page, heatmap)` when
        `return_heatmap=True`.
    """
    if profile is not None and letter_gap == 0.12:
        letter_gap = max(0.04, min(0.18, 0.085 * profile.letter_spacing_norm))

    if word_gap_mm is None:
        if profile is not None:
            word_gap_mm = max(
                x_height_mm * 0.14,
                x_height_mm * 0.14 * profile.word.spacing_mean_ratio,
            )
        else:
            word_gap_mm = x_height_mm * 0.20  # ~0.75mm — Gothic inter-word gap

    # Preprocess Roman numeral tokens → scribal lowercase + interpuncts
    processed_text, numeral_word_indices = preprocess_roman_numerals(line_text)
    numeral_set = set(numeral_word_indices)

    px_per_mm = dpi / 25.4
    words = processed_text.split()
    if not words:
        h = int(line_height_mm * px_per_mm)
        w = int(20 * px_per_mm)
        return np.full((h, w, 3), _PARCHMENT, dtype=np.uint8)

    if progress_dir is not None:
        Path(progress_dir).mkdir(parents=True, exist_ok=True)

    context = WordContext(
        ink_reservoir=(
            profile.ink.reservoir_capacity if profile is not None else 1.0
        )
    )
    if profile is not None:
        capacity = profile.ink.reservoir_capacity
        base_depletion = 0.002 * (profile.ink.depletion_rate / 0.02)
        dip_threshold = profile.ink.dry_threshold
        preferred_threshold = min(capacity * 0.88, dip_threshold + 0.02)
        ink_state = InkState(
            capacity=capacity,
            base_depletion=base_depletion,
            dip_threshold=dip_threshold,
            preferred_dip_threshold=preferred_threshold,
        )
    else:
        ink_state = InkState()

    # Diagnostic tracking
    reservoir_snapshots: list[tuple[int, float]] = []
    dip_word_indices: list[int] = []
    style_memory = StyleMemory()

    # ------------------------------------------------------------------ pass 1
    # Render each word in its own coordinate space and record word images.
    word_images: list[np.ndarray] = []
    word_widths_mm: list[float] = []
    fitnesses: list[float] = []
    word_heatmaps: list[np.ndarray] = []

    total_width_mm = 0.0

    for wi, word in enumerate(words):
        reservoir_at_start = ink_state.reservoir
        reservoir_snapshots.append((wi, reservoir_at_start))
        style_prior = style_memory.prior_for(word) if evolve else None

        genome, fitness = _get_genome(
            word, context, config if evolve else None,
            evolve=evolve,
            x_height_mm=x_height_mm,
            guides_path=guides_path,
            exemplar_root=exemplar_root,
            nib_width_mm=nib_width_mm,
            letter_gap=letter_gap,
            use_cache=use_cache,
            style_prior=style_prior,
        )
        if profile is not None:
            genome.global_slant_deg = (
                profile.slant_deg
                + random.gauss(0.0, profile.word.slant_drift_per_word_deg * max(0.2, variation))
            )
            baseline_sigma = (
                profile.glyph.baseline_jitter_mm
                + profile.line.baseline_undulation_amplitude_mm * 0.15
            ) * max(0.2, variation)
            genome.baseline_drift = [
                drift + random.gauss(0.0, baseline_sigma)
                for drift in genome.baseline_drift
            ]
            genome.tempo = profile.writing_speed
            genome.ink_state_start = reservoir_at_start
        if wi in numeral_set:
            genome.overline = True

        if evolve and character_model == "deep":
            genome = apply_contextual_allographs(
                genome,
                style_memory=style_memory,
                word_text=word,
                x_height_mm=x_height_mm,
                config=character_model_config,
            )

        rendered = render_word_from_genome(
            genome,
            dpi=dpi,
            nib_width_mm=nib_width_mm,
            nib_angle_deg=nib_angle_deg,
            canvas_height_mm=line_height_mm,
            variation=variation,
            ink_state=ink_state,
            profile=profile,
            return_heatmap=return_heatmap,
        )
        if return_heatmap:
            word_img, word_heat = rendered
            word_heatmaps.append(word_heat)
        else:
            word_img = rendered

        # Ink state overlay: tint word image by reservoir level at start of word
        if show_ink_state:
            word_img = _apply_ink_overlay(word_img, reservoir_at_start)

        word_images.append(word_img)
        word_widths_mm.append(genome.word_width_mm)
        fitnesses.append(fitness)
        total_width_mm += genome.word_width_mm + word_gap_mm

        dip_event = ink_state.process_word_boundary()
        if dip_event != DipEvent.NoDip:
            dip_word_indices.append(wi)
        context.ink_reservoir = ink_state.reservoir
        if profile is not None:
            context.fatigue += max(0.0, profile.fatigue_rate) * 0.1
        if evolve:
            style_memory.register(word, genome)

        if verbose:
            evo_tag = f" fit={fitness:.3f}" if evolve and fitness > 0 else ""
            reservoir_tag = f" ink={ink_state.reservoir:.2f}"
            dip_tag = f" [DIP#{ink_state.total_dips}]" if dip_event != DipEvent.NoDip else ""
            print(f"  word {wi+1:2d}/{len(words)}  {word!r:15s}  "
                  f"{len(word):2d} letters  {genome.word_width_mm:.1f}mm"
                  f"{reservoir_tag}{dip_tag}{evo_tag}",
                  flush=True)
        if progress_callback is not None and progress_granularity == "word":
            progress_callback({
                "stage": "word_complete",
                "line_index": line_index,
                "total_lines": total_lines,
                "word_index": wi,
                "total_words": len(words),
                "word": word,
                "fitness": fitness,
                "reservoir": ink_state.reservoir,
                "dip_count": ink_state.total_dips,
            })

        # -------------------------------------------------- progress image
        if progress_dir is not None:
            # Build composite of words placed so far
            canvas_w_mm = total_width_mm + 4.0
            canvas = _make_line_canvas(canvas_w_mm, line_height_mm, dpi)
            px_cursor = 0
            for j in range(wi + 1):
                canvas.paste(Image.fromarray(word_images[j], "RGB"), (px_cursor, 0))
                px_cursor += word_images[j].shape[1] + int(word_gap_mm * px_per_mm)
            prog_path = Path(progress_dir) / f"line_w{wi+1:03d}.png"
            canvas.save(str(prog_path))
            if verbose:
                print(f"             → {prog_path}", flush=True)

    # ------------------------------------------------------------------ pass 2
    # Composite all words into final line image.
    total_px = sum(img.shape[1] for img in word_images) + int(word_gap_mm * px_per_mm) * (len(words) - 1) + int(4 * px_per_mm)
    h_px = int(line_height_mm * px_per_mm)
    canvas = Image.new("RGB", (total_px, h_px), _PARCHMENT)
    heat_canvas = Image.new("L", (total_px, h_px), 0) if return_heatmap else None

    x_px = 0
    for idx, img in enumerate(word_images):
        canvas.paste(Image.fromarray(img, "RGB"), (x_px, 0))
        if heat_canvas is not None:
            _paste_heatmap(heat_canvas, word_heatmaps[idx], x_px)
        x_px += img.shape[1] + int(word_gap_mm * px_per_mm)

    if verbose:
        print(f"  line complete: {len(words)} words, "
              f"total={total_width_mm:.1f}mm", flush=True)

    # Save ink cycle graph if requested
    if ink_graph_path is not None:
        graph_img = _render_ink_graph(reservoir_snapshots, dip_word_indices)
        Path(ink_graph_path).parent.mkdir(parents=True, exist_ok=True)
        graph_img.save(str(ink_graph_path))
        if verbose:
            print(f"  ink graph → {ink_graph_path}", flush=True)

    page_arr = np.array(canvas)
    if heat_canvas is None:
        return page_arr
    return page_arr, np.array(heat_canvas)


def _apply_ink_overlay(word_img: np.ndarray, reservoir: float) -> np.ndarray:
    """Composite a semi-transparent colour tint over a word image based on reservoir.

    Green (> 0.7): fresh ink.  Yellow (0.15–0.3): getting low.  Red (< 0.15): critical.
    No tint in the normal range (0.3–0.7).  30% opacity so letterforms remain visible.
    """
    if 0.30 <= reservoir <= 0.70:
        return word_img  # normal range — no tint

    if reservoir > 0.70:
        tint = np.array([180, 230, 180], dtype=np.float32)   # green
    elif reservoir >= 0.15:
        tint = np.array([240, 220, 120], dtype=np.float32)   # yellow
    else:
        tint = np.array([230, 140, 130], dtype=np.float32)   # red

    alpha = 0.30
    out = word_img.astype(np.float32)
    out = out * (1.0 - alpha) + tint * alpha
    return np.clip(out, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# render_folio — uses new nib renderer
# ---------------------------------------------------------------------------

@dataclass
class EvolvedLine:
    line_index: int
    words: list[WordGenome]
    baseline_y_mm: float
    total_width_mm: float


@dataclass
class EvolvedFolio:
    folio_id: str
    lines: list[EvolvedLine]
    page_width_mm: float
    page_height_mm: float


def render_folio_lines(
    lines: list[str],
    dpi: float = 200.0,
    nib_width_mm: float = 0.65,
    nib_angle_deg: float = 42.0,
    x_height_mm: float = 3.8,
    line_spacing_mm: float = 12.0,
    line_height_mm: float = 14.0,
    margin_mm: float = 5.0,
    page_width_mm: float = 80.0,
    page_height_mm: float | None = None,
    margin_left_mm: float | None = None,
    margin_top_mm: float | None = None,
    word_gap_mm: float | None = None,
    guides_path=None,
    progress_dir: Path | None = None,
    verbose: bool = True,
    variation: float = 1.0,
    letter_gap: float = 0.12,
    profile: "HandProfile | None" = None,
    evolve: bool = False,
    config: EvolutionConfig | None = None,
    use_cache: bool = True,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
    progress_granularity: str = "line",
    return_heatmap: bool = False,
    character_model: str = "standard",
    character_model_config: AllographConfig | None = None,
) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    """Render multiple lines onto a page canvas."""
    px_per_mm = dpi / 25.4
    margin_left_mm = margin_mm if margin_left_mm is None else margin_left_mm
    margin_top_mm = margin_mm if margin_top_mm is None else margin_top_mm
    w_px = int(page_width_mm * px_per_mm)
    if page_height_mm is None:
        page_height_mm = margin_top_mm * 2 + len(lines) * line_spacing_mm
    h_px = int(page_height_mm * px_per_mm)

    canvas = Image.new("RGB", (w_px, h_px), _PARCHMENT)
    heat_canvas = Image.new("L", (w_px, h_px), 0) if return_heatmap else None

    for li, line_text in enumerate(lines):
        if not line_text.strip():
            continue
        if verbose:
            print(f"\nLine {li+1}/{len(lines)}: {line_text!r}", flush=True)
        if progress_callback is not None:
            progress_callback({
                "stage": "line_start",
                "line_index": li,
                "total_lines": len(lines),
                "line_text": line_text,
            })

        rendered_line = render_line(
            line_text,
            dpi=dpi,
            nib_width_mm=nib_width_mm,
            nib_angle_deg=nib_angle_deg,
            x_height_mm=x_height_mm,
            line_height_mm=line_height_mm,
            guides_path=guides_path,
            progress_dir=progress_dir,
            verbose=verbose,
            variation=variation,
            word_gap_mm=word_gap_mm,
            letter_gap=letter_gap,
            profile=profile,
            evolve=evolve,
            config=config,
            use_cache=use_cache,
            progress_callback=progress_callback,
            progress_granularity=progress_granularity,
            line_index=li,
            total_lines=len(lines),
            return_heatmap=return_heatmap,
            character_model=character_model,
            character_model_config=character_model_config,
        )
        if return_heatmap:
            line_img, line_heat = rendered_line
        else:
            line_img = rendered_line

        y_px = int((margin_top_mm + li * line_spacing_mm) * px_per_mm)
        x_px = int(margin_left_mm * px_per_mm)
        line_pil = Image.fromarray(line_img, "RGB")
        line_arr = np.array(line_img)
        mask = np.any(line_arr != np.array(_PARCHMENT, dtype=np.uint8), axis=2)
        if not mask.any():
            continue
        rows, cols = np.where(mask)
        pad = 2
        left = max(0, int(cols.min()) - pad)
        top = max(0, int(rows.min()) - pad)
        right = min(line_pil.width, int(cols.max()) + pad + 1)
        bottom = min(line_pil.height, int(rows.max()) + pad + 1)
        cropped = line_pil.crop((left, top, right, bottom))
        cropped_mask = Image.fromarray((mask[top:bottom, left:right] * 255).astype(np.uint8), "L")
        if x_px < w_px and y_px < h_px:
            canvas.paste(cropped, (x_px + left, y_px + top), cropped_mask)
            if heat_canvas is not None:
                heat_pil = Image.fromarray(line_heat, "L")
                heat_cropped = heat_pil.crop((left, top, right, bottom))
                heat_canvas.paste(heat_cropped, (x_px + left, y_px + top))

        if progress_dir is not None:
            page_path = Path(progress_dir) / f"page_line{li+1:03d}.png"
            canvas.save(str(page_path))
            if verbose:
                print(f"  page snapshot → {page_path}", flush=True)
        if progress_callback is not None:
            progress_callback({
                "stage": "line_complete",
                "line_index": li,
                "total_lines": len(lines),
                "line_text": line_text,
            })

    page_arr = np.array(canvas)
    if heat_canvas is None:
        return page_arr
    return page_arr, np.array(heat_canvas)
