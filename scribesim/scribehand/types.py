"""Core datatypes for learned word generation."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class WordRequest:
    """One text span to generate — a single word or a whole line.

    ``mode`` is "word" (default) or "line". Line requests carry the full line
    text; the backend renders one wide strip with natural word spacing.
    """

    text: str
    seed: int
    folio_id: str = ""
    line_index: int = 0
    word_index: int = 0
    mode: str = "word"
    controls: dict = field(default_factory=dict)   # GenControls.to_dict()


@dataclass
class WordStrip:
    """A generated word image as an ink mask.

    ``ink`` is a (H, W) uint8 array where 0 = no ink and 255 = full ink.
    ``baseline_frac`` is the baseline y position as a fraction of H;
    ``xheight_frac`` is the x-height (baseline minus x-height top) as a
    fraction of H, used to scale strips to physical page units.
    """

    ink: np.ndarray
    baseline_frac: float = 0.75
    xheight_frac: float = 0.35

    @property
    def height(self) -> int:
        return int(self.ink.shape[0])

    @property
    def width(self) -> int:
        return int(self.ink.shape[1])


@dataclass
class WordResult:
    """A generated word plus its provenance record.

    Provenance keys (always present after generation): ``backend``, ``seed``,
    ``text``, ``cache_hit``. After verification: ``verified``, ``htr_text``,
    ``htr_cer``, ``retries``.
    """

    strip: WordStrip
    provenance: dict = field(default_factory=dict)
