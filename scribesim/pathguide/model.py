"""Dense path guide data structures for TD-014.

These guides are the dense, corridor-constrained replacement for sparse
LetterformGuide keypoints. Coordinates are stored in physical millimetres so
controllers can operate independently of source pixel resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field


VALID_CONFIDENCE_TIERS = {"accepted", "soft_accepted", "rejected"}
VALID_GUIDE_KINDS = {"glyph", "join", "word", "transition", "line"}


@dataclass(frozen=True)
class GuideSource:
    """Provenance for one guide input."""

    source_id: str
    source_path: str | None = None
    extraction_run: str | None = None
    confidence_tier: str = "accepted"
    split: str = "train"
    source_resolution_ppmm: float | None = None


@dataclass(frozen=True)
class GuideSample:
    """One dense sample along the nominal writing path."""

    x_mm: float
    y_mm: float
    tangent_dx: float
    tangent_dy: float
    contact: bool = True
    speed_nominal: float = 1.0
    pressure_nominal: float = 0.5
    nib_angle_deg: float = 40.0
    nib_angle_confidence: float = 0.0
    corridor_half_width_mm: float = 0.2


@dataclass(frozen=True)
class DensePathGuide:
    """Dense nominal path plus corridor and provenance metadata."""

    symbol: str
    samples: tuple[GuideSample, ...]
    x_advance_mm: float
    x_height_mm: float
    kind: str = "glyph"
    entry_tangent: tuple[float, float] = (1.0, 0.0)
    exit_tangent: tuple[float, float] = (1.0, 0.0)
    sources: tuple[GuideSource, ...] = field(default_factory=tuple)

    @property
    def accepted_only(self) -> bool:
        return all(src.confidence_tier == "accepted" for src in self.sources)

    @property
    def contact_samples(self) -> tuple[GuideSample, ...]:
        return tuple(sample for sample in self.samples if sample.contact)
