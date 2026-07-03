"""Corpus gates — charset coverage and tier-count thresholds (TD-018 §2.3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribesim.handcorpus.charset import CharsetTable, CoverageReport, check_charset_coverage
from scribesim.handcorpus.manifest import CorpusManifest


@dataclass
class CorpusGateReport:
    charset: CoverageReport
    tier_counts: dict[str, int]
    split_counts: dict[str, int]
    counts_ok: bool
    min_script_family: int
    min_anchor: int

    @property
    def ok(self) -> bool:
        return self.charset.ok and self.counts_ok

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "charset": self.charset.to_dict(),
            "counts": {
                "ok": self.counts_ok,
                "tiers": self.tier_counts,
                "splits": self.split_counts,
                "min_script_family": self.min_script_family,
                "min_anchor": self.min_anchor,
            },
        }


def run_corpus_gates(
    manifest: CorpusManifest,
    charset_table: CharsetTable,
    xl_inventory: set[str],
    min_script_family: int = 5000,
    min_anchor: int = 300,
) -> CorpusGateReport:
    """Gate the corpus: XL charset must be covered, tiers must meet minimums."""
    charset_report = check_charset_coverage(
        inventory=xl_inventory,
        table=charset_table,
        training_charset=manifest.training_charset(),
    )
    tiers = manifest.tier_counts()
    counts_ok = (
        tiers.get("script_family", 0) >= min_script_family
        and tiers.get("anchor", 0) >= min_anchor
    )
    return CorpusGateReport(
        charset=charset_report,
        tier_counts=tiers,
        split_counts=manifest.split_counts(),
        counts_ok=counts_ok,
        min_script_family=min_script_family,
        min_anchor=min_anchor,
    )
