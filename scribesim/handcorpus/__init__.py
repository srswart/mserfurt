"""handcorpus — TD-018 training corpus assembly for learned scribal hand synthesis.

Builds the two-tier corpus described in TD-018 §2.3:

- ``script_family`` tier: transcribed medieval line images filtered from
  CATMuS Medieval (cursiva / bastarda / hybrida).
- ``anchor`` tier: reviewed word/line crops from the selected BSB anchor hand.

All samples flow into a single :class:`~scribesim.handcorpus.manifest.CorpusManifest`
with provenance, tier, and deterministic split assignment, guarded by charset
and count gates before any training export.
"""

from scribesim.handcorpus.manifest import CorpusManifest, CorpusSample, assign_split

__all__ = ["CorpusManifest", "CorpusSample", "assign_split"]
