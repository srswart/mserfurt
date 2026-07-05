"""HTR scoring — CER utility and scorer implementations.

``StubScorer`` supports plumbing tests. ``TrOCRScorer`` wraps a fine-tuned
TrOCR checkpoint (transformers; optional dependency — runs on the Mac
workstation or any torch-capable host).
"""

from __future__ import annotations

import numpy as np


def cer(reference: str, hypothesis: str) -> float:
    """Character error rate: Levenshtein distance / len(reference)."""
    if not reference:
        return 0.0 if not hypothesis else 1.0
    m, n = len(reference), len(hypothesis)
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        for j in range(1, n + 1):
            cost = 0 if reference[i - 1] == hypothesis[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[n] / m


class StubScorer:
    """Test scorer. ``echo`` reads perfectly; ``garble`` always misreads."""

    def __init__(self, mode: str = "echo") -> None:
        if mode not in ("echo", "garble"):
            raise ValueError(f"unknown StubScorer mode {mode!r}")
        self.mode = mode

    def read(self, images: list[np.ndarray], expected: list[str] | None = None) -> list[str]:
        if expected is None:
            return ["" for _ in images]
        if self.mode == "echo":
            return list(expected)
        return ["#" * max(1, len(t)) for t in expected]


class TrOCRScorer:
    """Fine-tuned TrOCR word reader (optional heavy dependency).

    The real scorer must NOT see the expected text — it reads the image.
    ``expected`` is accepted for interface compatibility and ignored.
    """

    def __init__(self, checkpoint: str, device: str | None = None) -> None:
        try:
            import torch
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "TrOCRScorer requires torch + transformers — "
                "install the scribehand extra: uv sync --extra scribehand"
            ) from exc

        self.torch = torch
        self.device = device or (
            "mps" if torch.backends.mps.is_available()
            else ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.processor = TrOCRProcessor.from_pretrained(checkpoint)
        self.model = VisionEncoderDecoderModel.from_pretrained(checkpoint).to(self.device)
        self.model.eval()
        self.checkpoint = checkpoint

    def read(
        self,
        images: list[np.ndarray],
        expected: list[str] | None = None,
        *,
        from_ink_mask: bool = True,
    ) -> list[str]:  # pragma: no cover
        from PIL import Image

        pil: list[Image.Image] = []
        for img in images:
            if from_ink_mask:
                pil.append(Image.fromarray(255 - img).convert("RGB"))
            else:
                pil.append(Image.fromarray(img).convert("RGB"))
        with self.torch.no_grad():
            batch = self.processor(images=pil, return_tensors="pt").pixel_values.to(self.device)
            generated = self.model.generate(batch, max_new_tokens=32)
        return self.processor.batch_decode(generated, skip_special_tokens=True)
