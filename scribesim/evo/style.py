"""Style memory for evo rendering.

Tracks per-folio scribal tendencies and recent same-word occurrences so new
evolutions can stay within one hand without degenerating into exact reuse.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from scribesim.evo.genome import WordGenome, GlyphGenome


_MINIM_FAMILY = set("iumnvt")
_ROUND_FAMILY = set("aocdegq")
_ASCENDER_FAMILY = set("bdfhklt")
_DESCENDER_FAMILY = set("gjpqy")


def _glyph_position_bucket(index: int, total: int) -> str:
    if total <= 1:
        return "single"
    if index == 0:
        return "start"
    if index == total - 1:
        return "end"
    return "middle"


def _neighbor_class(letter: str | None) -> str:
    if not letter:
        return "none"
    ch = letter.lower()
    if ch in _MINIM_FAMILY:
        return "minim"
    if ch in _ROUND_FAMILY:
        return "round"
    if ch in _ASCENDER_FAMILY:
        return "asc"
    if ch in _DESCENDER_FAMILY:
        return "desc"
    if ch.isalpha():
        return "other"
    return "mark"


def _context_key(letter: str, index: int, total: int, prev_letter: str | None, next_letter: str | None) -> str:
    return "|".join((
        letter.lower(),
        _glyph_position_bucket(index, total),
        _neighbor_class(prev_letter),
        _neighbor_class(next_letter),
    ))


@dataclass
class StylePrior:
    """Soft prior describing the current folio hand."""
    target_slant_deg: float | None = None
    width_mean_mm: float | None = None
    width_sigma_mm: float | None = None
    avg_advances: list[float] | None = None
    same_word_genomes: list[WordGenome] = field(default_factory=list)


@dataclass
class GlyphPrior:
    """Soft prior for a single letter across recent folio history."""
    letter: str
    advance_mean_mm: float | None = None
    advance_sigma_mm: float | None = None
    same_letter_glyphs: list[GlyphGenome] = field(default_factory=list)


@dataclass
class StyleMemory:
    """Running memory of the current folio's writing style."""
    max_same_word_history: int = 4
    max_same_letter_history: int = 12
    max_global_history: int = 48
    global_genomes: list[WordGenome] = field(default_factory=list)
    word_history: dict[str, list[WordGenome]] = field(default_factory=dict)
    glyph_history: dict[str, list[GlyphGenome]] = field(default_factory=dict)
    contextual_glyph_history: dict[str, list[GlyphGenome]] = field(default_factory=dict)

    def register(self, word: str, genome: WordGenome) -> None:
        word_key = word.lower()
        genome_copy = copy.deepcopy(genome)
        self.global_genomes.append(genome_copy)
        if len(self.global_genomes) > self.max_global_history:
            self.global_genomes = self.global_genomes[-self.max_global_history:]

        bucket = self.word_history.setdefault(word_key, [])
        bucket.append(genome_copy)
        if len(bucket) > self.max_same_word_history:
            self.word_history[word_key] = bucket[-self.max_same_word_history:]

        total = len(genome_copy.glyphs)
        for idx, glyph in enumerate(genome_copy.glyphs):
            letter_key = glyph.letter.lower()
            glyph_bucket = self.glyph_history.setdefault(letter_key, [])
            glyph_bucket.append(copy.deepcopy(glyph))
            if len(glyph_bucket) > self.max_same_letter_history:
                self.glyph_history[letter_key] = glyph_bucket[-self.max_same_letter_history:]
            prev_letter = genome_copy.glyphs[idx - 1].letter if idx > 0 else None
            next_letter = genome_copy.glyphs[idx + 1].letter if idx + 1 < total else None
            ctx_key = _context_key(glyph.letter, idx, total, prev_letter, next_letter)
            ctx_bucket = self.contextual_glyph_history.setdefault(ctx_key, [])
            ctx_bucket.append(copy.deepcopy(glyph))
            if len(ctx_bucket) > self.max_same_letter_history:
                self.contextual_glyph_history[ctx_key] = ctx_bucket[-self.max_same_letter_history:]

    def prior_for(self, word: str) -> StylePrior:
        word_key = word.lower()
        same_word = list(self.word_history.get(word_key, []))
        source = same_word if same_word else self.global_genomes
        if not source:
            return StylePrior()

        slants = [g.global_slant_deg for g in source]
        widths = [g.word_width_mm for g in source]
        target_slant = sum(slants) / len(slants)
        width_mean = sum(widths) / len(widths)
        if len(widths) > 1:
            variance = sum((w - width_mean) ** 2 for w in widths) / len(widths)
            width_sigma = max(0.4, variance ** 0.5)
        else:
            width_sigma = max(0.4, width_mean * 0.12)

        avg_advances: list[float] | None = None
        if same_word:
            same_len = [g for g in same_word if len(g.glyphs) > 0 and len(g.glyphs) == len(same_word[0].glyphs)]
            if same_len:
                avg_advances = []
                for idx in range(len(same_len[0].glyphs)):
                    avg_advances.append(
                        sum(g.glyphs[idx].x_advance for g in same_len) / len(same_len)
                    )

        return StylePrior(
            target_slant_deg=target_slant,
            width_mean_mm=width_mean,
            width_sigma_mm=width_sigma,
            avg_advances=avg_advances,
            same_word_genomes=[copy.deepcopy(g) for g in same_word],
        )

    def glyph_prior_for(
        self,
        letter: str,
        index: int | None = None,
        total: int | None = None,
        prev_letter: str | None = None,
        next_letter: str | None = None,
    ) -> GlyphPrior:
        letter_key = letter.lower()
        same_letter: list[GlyphGenome] = []
        if index is not None and total is not None:
            ctx_key = _context_key(letter_key, index, total, prev_letter, next_letter)
            same_letter = list(self.contextual_glyph_history.get(ctx_key, []))
        if len(same_letter) < 2:
            same_letter = list(self.glyph_history.get(letter_key, []))
        if not same_letter:
            return GlyphPrior(letter=letter_key)

        advances = [g.x_advance for g in same_letter]
        advance_mean = sum(advances) / len(advances)
        if len(advances) > 1:
            variance = sum((a - advance_mean) ** 2 for a in advances) / len(advances)
            advance_sigma = max(0.05, variance ** 0.5)
        else:
            advance_sigma = max(0.05, advance_mean * 0.08)

        return GlyphPrior(
            letter=letter_key,
            advance_mean_mm=advance_mean,
            advance_sigma_mm=advance_sigma,
            same_letter_glyphs=[copy.deepcopy(g) for g in same_letter],
        )
