"""Corpus manifest — sample schema, deterministic splits, JSON persistence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

TIERS = ("script_family", "anchor")
SPLITS = ("train", "val", "heldout")

# Deterministic split fractions (train gets the remainder).
_VAL_FRACTION = 0.05
_HELDOUT_FRACTION = 0.05


def assign_split(sample_id: str) -> str:
    """Deterministic split from a stable hash of the sample id.

    Python's builtin ``hash()`` is salted per process, so we use sha256.
    """
    digest = hashlib.sha256(sample_id.encode("utf-8")).digest()
    u = int.from_bytes(digest[:8], "big") / 2**64
    if u < _HELDOUT_FRACTION:
        return "heldout"
    if u < _HELDOUT_FRACTION + _VAL_FRACTION:
        return "val"
    return "train"


@dataclass
class CorpusSample:
    """One image/transcription pair with provenance."""

    id: str
    image: str            # path relative to the corpus root
    text: str
    tier: str             # script_family | anchor
    split: str            # train | val | heldout
    writer: str           # writer/hand identifier (shelfmark for CATMuS)
    source: dict          # provenance (dataset, shelfmark, canvas, etc.)

    def __post_init__(self) -> None:
        if self.tier not in TIERS:
            raise ValueError(f"unknown tier {self.tier!r} — expected one of {TIERS}")
        if self.split not in SPLITS:
            raise ValueError(f"unknown split {self.split!r} — expected one of {SPLITS}")


@dataclass
class CorpusManifest:
    """The full corpus: samples plus derived views."""

    samples: list[CorpusSample] = field(default_factory=list)
    schema: int = 1

    # -- derived -----------------------------------------------------------

    def training_charset(self) -> str:
        """Sorted string of every character appearing in sample texts (no space)."""
        chars: set[str] = set()
        for s in self.samples:
            chars.update(s.text)
        chars.discard(" ")
        return "".join(sorted(chars))

    def tier_counts(self) -> dict[str, int]:
        counts = {t: 0 for t in TIERS}
        for s in self.samples:
            counts[s.tier] += 1
        return counts

    def split_counts(self) -> dict[str, int]:
        counts = {sp: 0 for sp in SPLITS}
        for s in self.samples:
            counts[s.split] += 1
        return counts

    # -- persistence --------------------------------------------------------

    def save(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": self.schema,
            "tier_counts": self.tier_counts(),
            "split_counts": self.split_counts(),
            "training_charset": self.training_charset(),
            "samples": [asdict(s) for s in self.samples],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
        return path

    @classmethod
    def load(cls, path: Path) -> "CorpusManifest":
        payload = json.loads(Path(path).read_text())
        samples = [CorpusSample(**s) for s in payload["samples"]]
        return cls(samples=samples, schema=payload.get("schema", 1))
