"""Word generator — backend dispatch, on-disk cache, provenance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.scribehand.types import WordRequest, WordResult, WordStrip


class WordGenerator:
    """Generates word strips through a backend with an image cache.

    Cache key: backend name + checkpoint + text + seed + controls. Same
    manuscript inputs therefore re-render for free (TD-018 §2.8).
    """

    def __init__(self, backend, cache_dir: Path | None = None) -> None:
        self.backend = backend
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- cache ---------------------------------------------------------------

    def _cache_key(self, req: WordRequest) -> str:
        checkpoint = getattr(self.backend, "checkpoint", None) or ""
        payload = json.dumps(
            [self.backend.name, checkpoint, req.text, req.seed, req.controls],
            sort_keys=True, ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]

    def _cache_load(self, key: str) -> WordStrip | None:
        if not self.cache_dir:
            return None
        meta_path = self.cache_dir / f"{key}.json"
        img_path = self.cache_dir / f"{key}.png"
        if not (meta_path.exists() and img_path.exists()):
            return None
        meta = json.loads(meta_path.read_text())
        ink = np.asarray(Image.open(img_path).convert("L"), dtype=np.uint8)
        return WordStrip(
            ink=ink,
            baseline_frac=meta["baseline_frac"],
            xheight_frac=meta["xheight_frac"],
        )

    def _cache_store(self, key: str, strip: WordStrip) -> None:
        if not self.cache_dir:
            return
        Image.fromarray(strip.ink, "L").save(self.cache_dir / f"{key}.png")
        (self.cache_dir / f"{key}.json").write_text(json.dumps({
            "baseline_frac": strip.baseline_frac,
            "xheight_frac": strip.xheight_frac,
        }))

    # -- generation ------------------------------------------------------------

    def generate(self, requests: list[WordRequest]) -> list[WordResult]:
        keys = [self._cache_key(r) for r in requests]
        results: list[WordResult | None] = [None] * len(requests)

        misses: list[int] = []
        for i, (req, key) in enumerate(zip(requests, keys)):
            cached = self._cache_load(key)
            if cached is not None:
                results[i] = WordResult(strip=cached, provenance=self._prov(req, cache_hit=True))
            else:
                misses.append(i)

        if misses:
            strips = self.backend.generate_batch([requests[i] for i in misses])
            for i, strip in zip(misses, strips):
                self._cache_store(keys[i], strip)
                results[i] = WordResult(
                    strip=strip, provenance=self._prov(requests[i], cache_hit=False),
                )

        return [r for r in results if r is not None]

    def _prov(self, req: WordRequest, cache_hit: bool) -> dict:
        return {
            "backend": self.backend.name,
            "checkpoint": getattr(self.backend, "checkpoint", None),
            "text": req.text,
            "seed": req.seed,
            "folio_id": req.folio_id,
            "line_index": req.line_index,
            "word_index": req.word_index,
            "controls": req.controls,
            "cache_hit": cache_hit,
        }
