"""Diagnostic rendering — single glyph, word, and glyph-sheet isolation.

These functions bypass the page compositor entirely. They exist only for
visual verification during renderer development (TD-015). Not part of the
scribesim output contract.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


_DEFAULT_NIB_WIDTH_MM = 0.85
_DEFAULT_NIB_ANGLE_DEG = 42.0
_DEFAULT_X_HEIGHT_MM = 3.8
_GRID_COLS = 10


def render_single_glyph(
    glyph_id: str,
    dpi: float = 150.0,
    nib_width_mm: float = _DEFAULT_NIB_WIDTH_MM,
    nib_angle_deg: float = _DEFAULT_NIB_ANGLE_DEG,
    x_height_mm: float = _DEFAULT_X_HEIGHT_MM,
) -> np.ndarray:
    """Render one glyph from GLYPH_CATALOG in isolation.

    Returns an RGB uint8 ndarray sized to fit the glyph with margins.
    Raises KeyError if glyph_id is not in the catalog.
    """
    from scribesim.glyphs.catalog import GLYPH_CATALOG
    from scribesim.evo.genome import BezierSegment, GlyphGenome, WordGenome
    from scribesim.evo.renderer import render_word_from_genome

    glyph = GLYPH_CATALOG.get(glyph_id)
    if glyph is None:
        available = sorted(GLYPH_CATALOG.keys())
        raise KeyError(
            f"Glyph {glyph_id!r} not in catalog. "
            f"Available ({len(available)}): {available}"
        )

    margin_mm = x_height_mm * 1.2
    # baseline_y_mm positions the baseline so ascenders (up to 1.8×xh) fit above
    baseline_y_mm = margin_mm + x_height_mm * 1.9
    x_start = 0.0  # renderer adds left_margin via x_offset_px

    segments = []
    for stroke in glyph.strokes:
        pts = stroke.control_points
        seg = BezierSegment(
            p0=(x_start + pts[0][0] * x_height_mm,
                baseline_y_mm - pts[0][1] * x_height_mm),
            p1=(x_start + pts[1][0] * x_height_mm,
                baseline_y_mm - pts[1][1] * x_height_mm),
            p2=(x_start + pts[2][0] * x_height_mm,
                baseline_y_mm - pts[2][1] * x_height_mm),
            p3=(x_start + pts[3][0] * x_height_mm,
                baseline_y_mm - pts[3][1] * x_height_mm),
            contact=True,
            pressure_curve=list(stroke.pressure_profile),
        )
        segments.append(seg)

    glyph_genome = GlyphGenome(
        letter=glyph_id,
        segments=segments,
        x_offset=x_start,
        x_advance=glyph.advance_width * x_height_mm,
    )
    genome = WordGenome(
        text=glyph_id,
        glyphs=[glyph_genome],
        baseline_y=baseline_y_mm,
        word_width_mm=glyph.advance_width * x_height_mm,
    )

    # Canvas: glyph advance + side margins; height covers ascenders + descenders
    canvas_w_mm = glyph.advance_width * x_height_mm + 2.0 * margin_mm
    canvas_h_mm = baseline_y_mm + x_height_mm * 0.85 + margin_mm

    result = render_word_from_genome(
        genome,
        dpi=dpi,
        nib_width_mm=nib_width_mm,
        nib_angle_deg=nib_angle_deg,
        canvas_width_mm=canvas_w_mm,
        canvas_height_mm=canvas_h_mm,
    )
    # render_word_from_genome may return (img, heatmap) tuple; unwrap if so
    if isinstance(result, tuple):
        return result[0]
    return result


def render_word_diagnostic(
    text: str,
    dpi: float = 150.0,
    nib_width_mm: float = _DEFAULT_NIB_WIDTH_MM,
    nib_angle_deg: float = _DEFAULT_NIB_ANGLE_DEG,
    x_height_mm: float = _DEFAULT_X_HEIGHT_MM,
) -> np.ndarray:
    """Render a word (≤20 chars) in isolation using the evo genome renderer.

    Returns an RGB uint8 ndarray. No page compositor involved.
    """
    from scribesim.evo.genome import genome_from_guides
    from scribesim.evo.renderer import render_word_from_genome

    if len(text) > 20:
        raise ValueError(f"render_word_diagnostic: text too long ({len(text)} chars, max 20)")

    margin_mm = x_height_mm * 1.2
    baseline_y_mm = margin_mm + x_height_mm * 1.9

    genome = genome_from_guides(
        text,
        baseline_y_mm=baseline_y_mm,
        x_height_mm=x_height_mm,
    )

    canvas_w_mm = genome.word_width_mm + 2.0 * margin_mm
    canvas_h_mm = baseline_y_mm + x_height_mm * 0.85 + margin_mm

    result = render_word_from_genome(
        genome,
        dpi=dpi,
        nib_width_mm=nib_width_mm,
        nib_angle_deg=nib_angle_deg,
        canvas_width_mm=canvas_w_mm,
        canvas_height_mm=canvas_h_mm,
    )
    if isinstance(result, tuple):
        return result[0]
    return result


def render_glyph_sheet(
    dpi: float = 120.0,
    nib_width_mm: float = _DEFAULT_NIB_WIDTH_MM,
    nib_angle_deg: float = _DEFAULT_NIB_ANGLE_DEG,
    x_height_mm: float = _DEFAULT_X_HEIGHT_MM,
) -> np.ndarray:
    """Render every glyph in GLYPH_CATALOG as a labeled grid (10 per row).

    Returns an RGB uint8 ndarray of the full sheet.
    """
    from PIL import Image, ImageDraw
    from scribesim.glyphs.catalog import GLYPH_CATALOG

    glyph_ids = sorted(GLYPH_CATALOG.keys())

    # Render all glyphs to find the maximum cell size
    cells: list[np.ndarray] = []
    max_w = 0
    max_h = 0
    for gid in glyph_ids:
        try:
            img = render_single_glyph(
                gid, dpi=dpi,
                nib_width_mm=nib_width_mm,
                nib_angle_deg=nib_angle_deg,
                x_height_mm=x_height_mm,
            )
        except Exception:
            # Produce a blank placeholder on any render failure
            img = np.full((20, 20, 3), 245, dtype=np.uint8)
        cells.append(img)
        max_w = max(max_w, img.shape[1])
        max_h = max(max_h, img.shape[0])

    label_px = max(12, int(dpi * 0.12))  # ~12% of an inch for the label row
    cell_h = max_h + label_px
    cell_w = max_w

    n = len(cells)
    cols = _GRID_COLS
    rows = (n + cols - 1) // cols

    sheet_w = cols * cell_w
    sheet_h = rows * cell_h

    parchment = (245, 238, 220)
    sheet = Image.new("RGB", (sheet_w, sheet_h), parchment)
    draw = ImageDraw.Draw(sheet)

    for idx, (gid, cell_arr) in enumerate(zip(glyph_ids, cells)):
        row = idx // cols
        col = idx % cols
        x0 = col * cell_w
        y0 = row * cell_h

        # Paste glyph image (pad to cell size if smaller)
        cell_img = Image.fromarray(cell_arr, "RGB")
        padded = Image.new("RGB", (cell_w, max_h), parchment)
        paste_x = (cell_w - cell_arr.shape[1]) // 2
        paste_y = (max_h - cell_arr.shape[0]) // 2
        padded.paste(cell_img, (paste_x, paste_y))
        sheet.paste(padded, (x0, y0))

        # Label below
        label = gid if len(gid) <= 8 else gid[:7] + "…"
        draw.text((x0 + 2, y0 + max_h + 1), label, fill=(60, 40, 20))

    return np.array(sheet)


def save_png(arr: np.ndarray, path: Path | str, dpi: float = 150.0) -> Path:
    """Save an RGB ndarray as a PNG with DPI metadata."""
    from PIL import Image

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr, "RGB").save(str(path), format="PNG", dpi=(dpi, dpi))
    return path
