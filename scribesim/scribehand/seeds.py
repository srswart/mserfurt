"""Deterministic seed policy (TD-018 §2.4).

Seeds derive from (base seed, folio, line, word index) via sha256 so a fixed
manuscript re-renders identically, while every word position gets its own
generation seed. Retries during HTR verification advance a retry counter.
"""

from __future__ import annotations

import hashlib


def word_seed(
    base_seed: int,
    folio_id: str,
    line_index: int,
    word_index: int,
    retry: int = 0,
) -> int:
    key = f"{base_seed}|{folio_id}|{line_index}|{word_index}|{retry}"
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % (2**31 - 1)
