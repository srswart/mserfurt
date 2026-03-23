"""AI Weathering Prompt Generator — TD-011 Parts 3 + Addendum A.

Translates a FolioWeatherSpec (from the codex weathering map) into a
structured text prompt for the AI image model.  Also builds the
CoherenceContext (adjacent-folio descriptions + reference images) and
generates word-level text-degradation instructions from CLIO-7 annotations.

Public API:
    generate_background_prompt(folio_spec, context) -> str
    generate_weathering_prompt(folio_spec, context, word_damage_map, ...) -> str
    generate_text_degradation_prompt(word_damage_map, page_width, page_height) -> str
    build_coherence_context(folio_id, weathering_map, weathered_so_far) -> CoherenceContext
    summarize_weathering(folio_spec) -> str
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class WaterDamageSpec:
    severity: float          # 0.0–1.0
    origin: str              # e.g. "top_right"
    penetration: float       # fraction of page height (0.0–1.0)


@dataclass
class MissingCornerSpec:
    corner: str              # e.g. "bottom_left"
    depth_fraction: float    # fraction of page height
    width_fraction: float    # fraction of page width


@dataclass
class FoxingSpot:
    position: tuple[float, float]   # (x, y) as fractions of page
    intensity: float
    radius: float                   # fraction of page


@dataclass
class TextDegradationZone:
    lines: tuple[int, int]     # inclusive line range
    confidence: float
    description: str


@dataclass
class FolioWeatherSpec:
    """Complete weathering specification for one folio, from the codex map."""
    folio_id: str
    vellum_stock: str                              # "standard" or "irregular"
    edge_darkening: float                          # 0.0–1.0
    gutter_side: str                               # "left" or "right"
    water_damage: Optional[WaterDamageSpec] = None
    missing_corner: Optional[MissingCornerSpec] = None
    foxing_spots: list[FoxingSpot] = field(default_factory=list)
    text_degradation: Optional[list[TextDegradationZone]] = None
    overall_aging: str = "standard"


@dataclass
class WordDamageEntry:
    """Word-level damage annotation from CLIO-7 mapped to pixel coordinates."""
    word_text: str
    bbox: tuple[int, int, int, int]   # (left, top, right, bottom) in pixels
    center: tuple[float, float]        # (x, y) in pixels
    confidence: float                  # 0.0–1.0
    category: str                      # "lacuna", "trace", "partial", "clear"
    line_number: int
    specific_note: Optional[str] = None


@dataclass
class AdjacentFolioContext:
    folio_id: str
    relation: str          # "verso", "recto", "facing"
    same_leaf: bool
    description: str
    severity_here: float   # expected damage severity on the current folio from this neighbor
    reference_image: Any = None   # PIL Image or np.ndarray if already weathered


@dataclass
class CoherenceContext:
    adjacent_folios: list[AdjacentFolioContext] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PRESERVATION = (
    "This image shows a manuscript page rendered in clean modern calligraphy. "
    "Your task is to age the surface of this exact image — treating it like a photograph "
    "of a real 15th-century manuscript that has survived 500 years of storage. "
    "CRITICAL RULES — these override everything else: "
    "(1) Every letterform already on the page must remain exactly where it is. "
    "Do not redraw, regenerate, move, or alter any letter, stroke, or punctuation mark. "
    "The text content is FIXED — treat it as physically printed onto the surface you are aging. "
    "(2) Apply weathering effects AS OVERLAYS on top of the existing image: "
    "vellum tone shifts, ink oxidation, staining, soiling, edge darkening. "
    "These are surface-level effects only — like applying aged paper and ink filters. "
    "(3) Text should only become distorted or faded in the specific damage zones described below. "
    "Everywhere else the text must remain fully legible after aging — darker ink fading to warm "
    "iron-gall brown, but the strokes intact. "
    "The manuscript is from 1457, Erfurt, kept in an Augustinian archive. "
    "It has been undisturbed for approximately 500 years."
)


def _vellum_section(spec: FolioWeatherSpec) -> str:
    if spec.vellum_stock == "irregular":
        return (
            "VELLUM: Irregular calfskin stock — thinner and slightly less refined than the "
            "main gathering. After 500 years the surface has developed an uneven warm ochre tone, "
            "slightly darker than the standard leaves, with faint translucent patches at the "
            "thinnest points. The grain structure of the skin is more visible than on standard leaves. "
            "Scattered dark flecks from the original preparation process."
        )
    return (
        "VELLUM: Standard calfskin parchment, approximately 500 years old. "
        "The surface color has shifted from its original pale cream to a warm honey-yellow with "
        "subtle spatial variation — slightly darker toward the edges and near any moisture damage. "
        "There is a faint surface texture from 500 years of very slow contraction and relaxation "
        "of the skin fibers. The vellum has a slight translucency at its thinner areas."
    )


def _ink_section() -> str:
    return (
        "INK: Iron gall ink written in 1457, now approximately 500 years old. "
        "Iron gall oxidizes over centuries: the original jet black has shifted to a warm dark "
        "reddish-brown — the color of old dried blood or aged walnut ink. "
        "Apply this color shift uniformly across all letterforms by tinting the existing "
        "black strokes toward a deep brown (RGB approximately 60, 30, 10). "
        "The ink also bites slightly into the vellum surface over centuries — there is a "
        "very faint halo or shadow around each stroke where the acid has darkened the fiber. "
        "Do not change the shape or position of any stroke — only shift its color."
    )


def _edge_section(spec: FolioWeatherSpec) -> str:
    severity = spec.edge_darkening
    if severity > 0.8:
        level = "strong"
    elif severity > 0.5:
        level = "moderate"
    else:
        level = "light"
    gutter = "left" if spec.gutter_side == "left" else "right"
    return (
        f"Edge darkening at {level} intensity on all four edges, darkest at the corners. "
        f"The {gutter} edge has additional binding shadow from the book's spine."
    )


def _water_section(wd: WaterDamageSpec) -> str:
    if wd.severity > 0.7:
        severity_word = "severe"
        ink_effect = (
            "In the wetted zone the ink has heavily dissolved and re-deposited — "
            "letterforms are badly faded, many strokes reduced to ghosts. "
            "Only the deepest biting strokes survive as faint traces."
        )
    elif wd.severity > 0.3:
        severity_word = "moderate"
        ink_effect = (
            "In the wetted zone the ink has partially dissolved — strokes are visibly faded "
            "and some fine details of letterforms are lost, but most words remain identifiable."
        )
    else:
        severity_word = "light"
        ink_effect = (
            "In the wetted zone the ink is only very slightly affected — a subtle lightening "
            "of the darkest strokes but letterforms remain fully legible."
        )
    pct = int(wd.penetration * 100)
    return (
        f"WATER DAMAGE: A moisture event at some point in the past 500 years introduced water "
        f"from the {wd.origin} corner. The stain affects the top {pct}% of the page measured "
        f"from the edge nearest that corner. "
        f"Severity: {severity_word}. "
        f"Render the tide line — a brown ring at the boundary of the wetted area — as the most "
        f"visually prominent feature of the water damage. The vellum inside the tide line is "
        f"darker and slightly cockled (faint ripple texture from drying). "
        f"{ink_effect} "
        f"Text OUTSIDE the tide line boundary must not be faded or distorted by this effect."
    )


def _corner_section(mc: MissingCornerSpec) -> str:
    depth_pct = int(mc.depth_fraction * 100)
    width_pct = int(mc.width_fraction * 100)
    return (
        f"The {mc.corner} corner of the page is physically missing — torn away. "
        f"The tear extends approximately {depth_pct}% of the page height "
        f"and {width_pct}% of the page width. "
        f"The tear edge should look like torn vellum — irregular, slightly fibrous, not a clean cut. "
        f"Behind the missing corner, show a dark background (the shelf or conservation board)."
    )


def _foxing_section(spots: list[FoxingSpot]) -> str:
    n = len(spots)
    return (
        f"FOXING: Add {n} foxing spots — small brown biological stains that develop on "
        f"aged organic material over centuries. Each spot should be 1–4mm in diameter, "
        f"roughly circular but slightly irregular, with a concentrated brown center fading "
        f"to a lighter tan ring at the edge. "
        f"The spots appear OVER the existing surface — they sit on top of vellum and ink alike, "
        f"slightly obscuring any text beneath them. "
        f"This archive was relatively dry, so the foxing is light; do not let any single spot "
        f"fully obliterate a letterform."
    )


def _coherence_section(context: CoherenceContext) -> str:
    if not context.adjacent_folios:
        return ""
    parts = ["IMPORTANT — maintain visual coherence with adjacent pages:"]
    for adj in context.adjacent_folios:
        relation_word = "preceding" if adj.relation in ("recto", "facing") else "following"
        match_word = "similar" if adj.severity_here > 0.3 else "diminishing"
        position_word = "matching" if adj.same_leaf else "corresponding"
        parts.append(
            f"The {relation_word} page ({adj.folio_id}) has {adj.description}. "
            f"This page should show {match_word} effects in {position_word} positions."
        )
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_text_degradation_prompt(
    word_damage_map: list[WordDamageEntry],
    page_width: int,
    page_height: int,
) -> str:
    """Generate word-level text degradation instructions (TD-011 Addendum A).

    Groups words by confidence bucket and emits per-word position percentages.
    Returns an empty string if word_damage_map is empty.
    """
    if not word_damage_map:
        return ""

    parts: list[str] = []
    parts.append(
        "TEXT DEGRADATION ZONES — these are the ONLY locations where letterforms may be "
        "faded, dissolved, or distorted. Every word outside these zones must remain fully "
        "legible (ink aged to brown but strokes intact). "
        "Page coordinates are given as percentages from top-left (0%,0%) to bottom-right (100%,100%)."
    )

    clear_zones  = [w for w in word_damage_map if w.confidence >= 0.8]
    faded_zones  = [w for w in word_damage_map if 0.6 <= w.confidence < 0.8]
    trace_zones  = [w for w in word_damage_map if 0.0 < w.confidence < 0.6]
    lost_zones   = [w for w in word_damage_map if w.confidence == 0.0]

    if clear_zones:
        parts.append(
            f"LEGIBLE TEXT ({len(clear_zones)} regions): The following areas contain text that "
            f"should remain fully legible — ink faded to brown with age but clearly readable. "
            f"Do not degrade these regions beyond normal aging."
        )

    if faded_zones:
        parts.append(
            f"PARTIALLY LEGIBLE TEXT ({len(faded_zones)} regions): The following text has been "
            f"damaged by water exposure. The ink is faded and partially dissolved. A careful reader "
            f"can make out most words but some letters are ambiguous."
        )
        for w in faded_zones:
            x_pct = w.center[0] / page_width * 100
            y_pct = w.center[1] / page_height * 100
            width_pct = (w.bbox[2] - w.bbox[0]) / page_width * 100
            parts.append(
                f"  - At position ({x_pct:.0f}%, {y_pct:.0f}%), width ~{width_pct:.0f}%: "
                f"the word '{w.word_text}' — fade ink to approximately {int(w.confidence * 100)}% "
                f"of normal darkness. Some letters should be partially dissolved but the overall "
                f"word shape remains recognizable."
            )

    if trace_zones:
        parts.append(
            f"BARELY LEGIBLE TEXT ({len(trace_zones)} regions): The following text is heavily "
            f"damaged. Only faint ink traces remain — isolated fragments of letter strokes. "
            f"A scholar might reconstruct some words but most are speculative."
        )
        for w in trace_zones:
            x_pct = w.center[0] / page_width * 100
            y_pct = w.center[1] / page_height * 100
            width_pct = (w.bbox[2] - w.bbox[0]) / page_width * 100
            if w.specific_note:
                parts.append(
                    f"SPECIFIC DAMAGE NOTE: At position ({x_pct:.0f}%, {y_pct:.0f}%): "
                    f"{w.specific_note} — partially obscure this word so that the first "
                    f"and last letters are faintly visible but the middle letters are ambiguous. "
                    f"A reader should be able to see that a word exists here but should NOT be "
                    f"certain what it says."
                )
            else:
                parts.append(
                    f"  - At position ({x_pct:.0f}%, {y_pct:.0f}%), width ~{width_pct:.0f}%: "
                    f"reduce ink to faint traces — {int(w.confidence * 100)}% of normal darkness. "
                    f"Only isolated vertical strokes and fragments should be visible. "
                    f"The word shape should NOT be clearly recognizable."
                )

    if lost_zones:
        parts.append(
            f"COMPLETELY LOST TEXT ({len(lost_zones)} regions): The following areas have no "
            f"surviving ink. The text is entirely gone — these are lacunae where the water "
            f"(or physical damage) has completely removed the writing."
        )
        for w in lost_zones:
            x_pct = w.center[0] / page_width * 100
            y_pct = w.center[1] / page_height * 100
            width_pct = (w.bbox[2] - w.bbox[0]) / page_width * 100
            parts.append(
                f"  - At position ({x_pct:.0f}%, {y_pct:.0f}%), width ~{width_pct:.0f}%: "
                f"no ink whatsoever. Bare vellum surface (with water staining if in the "
                f"water-damaged zone). This should look like a gap in the text where "
                f"writing once existed but has been completely erased by damage."
            )

    return "\n".join(parts)


_BACKGROUND_PREAMBLE = (
    "Generate a blank aged calfskin vellum page with NO text, NO writing, and NO letterforms. "
    "The vellum has been stored in an Augustinian archive in Erfurt for approximately 500 years "
    "since 1457. Apply only the following physical aging and damage effects to the blank surface. "
    "The output must show bare parchment with stains, discoloration, and damage — "
    "but absolutely no writing of any kind."
)


def generate_background_prompt(
    folio_spec: "FolioWeatherSpec",
    context: "CoherenceContext",
) -> str:
    """Generate a prompt for a BLANK aged parchment background (no text).

    Used for the two-step weathering approach: AI generates aged background,
    then the rendered text is darken-blended on top to guarantee letterform
    preservation.
    """
    sections: list[str] = [_BACKGROUND_PREAMBLE]
    sections.append(_vellum_section(folio_spec))
    sections.append(_edge_section(folio_spec))

    if folio_spec.water_damage:
        sections.append(_water_section(folio_spec.water_damage))

    if folio_spec.missing_corner:
        sections.append(_corner_section(folio_spec.missing_corner))

    if folio_spec.foxing_spots:
        sections.append(_foxing_section(folio_spec.foxing_spots))

    coherence = _coherence_section(context)
    if coherence:
        sections.append(coherence)

    return " ".join(sections)


def generate_weathering_prompt(
    folio_spec: FolioWeatherSpec,
    context: CoherenceContext,
    word_damage_map: Optional[list[WordDamageEntry]] = None,
    page_width: Optional[int] = None,
    page_height: Optional[int] = None,
) -> str:
    """Generate the complete AI weathering prompt for a single folio.

    Sections are assembled in canonical order:
        base → vellum → ink → edges → water → corner → foxing
        → text-degradation → coherence
    """
    sections: list[str] = []

    sections.append(_PRESERVATION)
    sections.append(_vellum_section(folio_spec))
    sections.append(_ink_section())
    sections.append(_edge_section(folio_spec))

    if folio_spec.water_damage:
        sections.append(_water_section(folio_spec.water_damage))

    if folio_spec.missing_corner:
        sections.append(_corner_section(folio_spec.missing_corner))

    if folio_spec.foxing_spots:
        sections.append(_foxing_section(folio_spec.foxing_spots))

    if word_damage_map and page_width and page_height:
        td = generate_text_degradation_prompt(word_damage_map, page_width, page_height)
        if td:
            sections.append(td)
    elif folio_spec.text_degradation:
        # Fallback: line-level degradation from the codex map (TD-011 Part 3)
        for zone in folio_spec.text_degradation:
            if zone.confidence == 0.0:
                sections.append(
                    f"Lines {zone.lines[0]}-{zone.lines[1]}: text completely absent "
                    f"({zone.description}). No ink visible in this region."
                )
            elif zone.confidence < 0.5:
                sections.append(
                    f"Lines {zone.lines[0]}-{zone.lines[1]}: text barely visible — "
                    f"only faint traces of ink remain ({zone.description}). "
                    f"A reader would struggle to make out more than isolated words."
                )
            elif zone.confidence < 0.8:
                sections.append(
                    f"Lines {zone.lines[0]}-{zone.lines[1]}: text partially legible — "
                    f"ink is faded but most words can still be read with difficulty "
                    f"({zone.description})."
                )

    coherence = _coherence_section(context)
    if coherence:
        sections.append(coherence)

    return " ".join(sections)


def summarize_weathering(spec: FolioWeatherSpec) -> str:
    """Return a one-line summary of a folio's weathering spec for coherence descriptions."""
    parts: list[str] = []

    if spec.water_damage:
        wd = spec.water_damage
        level = "severe" if wd.severity > 0.7 else "moderate" if wd.severity > 0.3 else "light"
        parts.append(f"{level} water damage from {wd.origin}")

    if spec.missing_corner:
        parts.append(f"missing {spec.missing_corner.corner} corner")

    if spec.foxing_spots:
        parts.append(f"{len(spec.foxing_spots)} foxing spot(s)")

    stock = "irregular vellum stock" if spec.vellum_stock == "irregular" else "standard vellum"
    parts.append(stock)

    edge_level = "heavy" if spec.edge_darkening > 0.8 else "moderate" if spec.edge_darkening > 0.5 else "light"
    parts.append(f"{edge_level} edge darkening")

    return ", ".join(parts)


def build_coherence_context(
    folio_id: str,
    weathering_map: dict[str, FolioWeatherSpec],
    weathered_so_far: Optional[dict[str, Any]] = None,
) -> CoherenceContext:
    """Build coherence context for a folio from its same-leaf partner and facing page.

    Args:
        folio_id:        e.g. "f04v"
        weathering_map:  full codex map keyed by folio_id
        weathered_so_far: dict of already-weathered images keyed by folio_id
    """
    weathered_so_far = weathered_so_far or {}
    folio_num = int(folio_id[1:3])
    side = folio_id[3]
    adjacent: list[AdjacentFolioContext] = []

    # Same leaf, other side
    other_side = "v" if side == "r" else "r"
    other_id = f"f{folio_num:02d}{other_side}"
    if other_id in weathering_map:
        other_spec = weathering_map[other_id]
        wd_severity = other_spec.water_damage.severity if other_spec.water_damage else 0.0
        relation = "verso" if side == "r" else "recto"
        adjacent.append(AdjacentFolioContext(
            folio_id=other_id,
            relation=relation,
            same_leaf=True,
            description=summarize_weathering(other_spec),
            severity_here=wd_severity * 0.85,
            reference_image=weathered_so_far.get(other_id),
        ))

    # Facing page (the page that touches this one when the book is closed)
    if side == "r" and folio_num > 1:
        facing_id = f"f{folio_num - 1:02d}v"
    elif side == "v" and folio_num < 17:
        facing_id = f"f{folio_num + 1:02d}r"
    else:
        facing_id = None

    if facing_id and facing_id in weathering_map:
        facing_spec = weathering_map[facing_id]
        wd_severity = facing_spec.water_damage.severity if facing_spec.water_damage else 0.0
        adjacent.append(AdjacentFolioContext(
            folio_id=facing_id,
            relation="facing",
            same_leaf=False,
            description=summarize_weathering(facing_spec),
            severity_here=wd_severity * 0.4,
            reference_image=weathered_so_far.get(facing_id),
        ))

    return CoherenceContext(adjacent_folios=adjacent)
