"""Neural promotion gates — TD-018 §2.7 / ADV-SS-HANDVALIDATE-007.

Gate families:

- **CER bands**: folio-level aggregation of the per-word HTR scores.
- **Anti-font**: no two same-text word instances may be near pixel-identical.
- **Style distance**: HOG-embedding distance between generated words and the
  anchor exemplar population (deep writer-ID embeddings can substitute on
  torch-capable hosts; the HOG baseline runs anywhere).
- **Acceptance bands**: the existing metrics suite (M1–M9) against an anchor
  reference page — acceptance ranges, not optimization targets.

Thresholds load from ``shared/hands/validation/neural_gates.toml``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_DEFAULT_GATES_PATH = Path("shared/hands/validation/neural_gates.toml")


# ---------------------------------------------------------------------------
# gate thresholds
# ---------------------------------------------------------------------------

@dataclass
class NeuralGates:
    cer_mean_max: float = 0.05
    cer_verified_fraction_min: float = 0.98
    anti_font_max_ncc: float = 0.995
    style_distance_max: float = 0.35
    acceptance_mean_distance_max: float = 0.35

    @classmethod
    def from_toml(cls, path: Path) -> "NeuralGates":
        import tomllib

        data = tomllib.loads(Path(path).read_text()).get("gates", {})
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def load_neural_gates(path: Path | None) -> NeuralGates:
    p = path or _DEFAULT_GATES_PATH
    if Path(p).exists():
        return NeuralGates.from_toml(p)
    return NeuralGates()


# ---------------------------------------------------------------------------
# style embedding (HOG baseline — dependency-free)
# ---------------------------------------------------------------------------

def hog_embedding(image: np.ndarray, cells: int = 4, bins: int = 9) -> np.ndarray:
    """Histogram-of-oriented-gradients embedding of a grayscale image.

    Deterministic, torch-free style descriptor: the image is resized to a
    fixed grid, gradients are binned by orientation per cell, and the
    concatenated histograms are L2-normalized.
    """
    from PIL import Image

    size = 64
    img = np.asarray(
        Image.fromarray(image.astype(np.uint8), "L").resize((size, size), Image.BILINEAR),
        dtype=np.float32,
    ) / 255.0

    gy, gx = np.gradient(img)
    magnitude = np.hypot(gx, gy)
    orientation = (np.arctan2(gy, gx) + np.pi) % np.pi   # unsigned [0, pi)

    cell = size // cells
    feats: list[np.ndarray] = []
    for cy in range(cells):
        for cx in range(cells):
            sl = (slice(cy * cell, (cy + 1) * cell), slice(cx * cell, (cx + 1) * cell))
            hist, _ = np.histogram(
                orientation[sl], bins=bins, range=(0, np.pi), weights=magnitude[sl],
            )
            feats.append(hist)
    vec = np.concatenate(feats).astype(np.float64)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def style_distance(generated: list[np.ndarray], anchor: list[np.ndarray]) -> float:
    """Distance between the mean embeddings of two word-image populations."""
    g = np.mean([hog_embedding(im) for im in generated], axis=0)
    a = np.mean([hog_embedding(im) for im in anchor], axis=0)
    return float(np.linalg.norm(g - a))


# ---------------------------------------------------------------------------
# anti-font check
# ---------------------------------------------------------------------------

def _ncc(a: np.ndarray, b: np.ndarray) -> float:
    from PIL import Image

    size = (64, 32)
    fa = np.asarray(Image.fromarray(a.astype(np.uint8), "L").resize(size), dtype=np.float64)
    fb = np.asarray(Image.fromarray(b.astype(np.uint8), "L").resize(size), dtype=np.float64)
    fa -= fa.mean(); fb -= fb.mean()
    denom = np.sqrt((fa ** 2).sum() * (fb ** 2).sum())
    if denom == 0:
        return 1.0
    return float((fa * fb).sum() / denom)


def anti_font_check(
    words_by_text: dict[str, list[np.ndarray]],
    max_ncc: float = 0.995,
) -> dict:
    """No two same-text instances on a folio may be near pixel-identical."""
    worst = -1.0
    pairs = 0
    offenders: list[str] = []
    for text, instances in words_by_text.items():
        for i in range(len(instances)):
            for j in range(i + 1, len(instances)):
                score = _ncc(instances[i], instances[j])
                pairs += 1
                if score > worst:
                    worst = score
                if score > max_ncc:
                    offenders.append(text)
    return {
        "ok": not offenders,
        "max_ncc": worst if pairs else 0.0,
        "threshold": max_ncc,
        "pairs_checked": pairs,
        "offending_texts": sorted(set(offenders)),
    }


# ---------------------------------------------------------------------------
# CER bands
# ---------------------------------------------------------------------------

def cer_bands(provenances: list[dict]) -> dict:
    scored = [p for p in provenances if "htr_cer" in p]
    if not scored:
        return {"scored_words": 0, "verified_fraction": 0.0,
                "cer_mean": None, "cer_max": None}
    cers = [p["htr_cer"] for p in scored]
    verified = [p for p in scored if p.get("verified")]
    return {
        "scored_words": len(scored),
        "verified_fraction": len(verified) / len(scored),
        "cer_mean": float(np.mean(cers)),
        "cer_max": float(np.max(cers)),
        "retries_total": int(sum(p.get("retries", 0) for p in scored)),
    }


# ---------------------------------------------------------------------------
# acceptance bands (existing metrics suite)
# ---------------------------------------------------------------------------

def acceptance_bands(
    page: np.ndarray,
    reference: np.ndarray,
    max_mean_distance: float = 0.35,
) -> dict:
    """Run the M1–M9 metrics suite as acceptance ranges against a reference page."""
    from scribesim.metrics.suite import run_metrics

    results = run_metrics(page, reference)
    distances = {r.id: r.distance for r in results}
    mean_distance = float(np.mean(list(distances.values()))) if distances else 1.0
    return {
        "ok": mean_distance <= max_mean_distance,
        "mean_distance": mean_distance,
        "threshold": max_mean_distance,
        "per_metric": distances,
    }


# ---------------------------------------------------------------------------
# bench driver
# ---------------------------------------------------------------------------

@dataclass
class BenchReport:
    folio_id: str
    cer: dict
    anti_font: dict
    style: dict
    acceptance: dict
    gates: NeuralGates

    @property
    def ok(self) -> bool:
        checks = [self.anti_font.get("ok", False)]
        if self.cer.get("scored_words"):
            cer_mean = self.cer["cer_mean"]
            checks.append(
                cer_mean is not None and cer_mean <= self.gates.cer_mean_max
                and self.cer["verified_fraction"] >= self.gates.cer_verified_fraction_min
            )
        if self.style.get("distance") is not None:
            checks.append(self.style["distance"] <= self.gates.style_distance_max)
        if self.acceptance.get("mean_distance") is not None:
            checks.append(self.acceptance["ok"])
        return all(checks)

    def to_dict(self) -> dict:
        cer = dict(self.cer)
        if cer.get("scored_words"):
            cer["ok"] = (
                cer["cer_mean"] is not None
                and cer["cer_mean"] <= self.gates.cer_mean_max
                and cer["verified_fraction"] >= self.gates.cer_verified_fraction_min
            )
        else:
            cer["ok"] = None
        return {
            "folio_id": self.folio_id,
            "ok": self.ok,
            "cer": cer,
            "anti_font": self.anti_font,
            "style": self.style,
            "acceptance": self.acceptance,
            "gates": self.gates.__dict__,
        }


def run_neural_bench(
    composed,
    gates: NeuralGates,
    anchor_word_images: list[np.ndarray] | None = None,
    reference_page: np.ndarray | None = None,
    out_dir: Path | None = None,
) -> BenchReport:
    """Evaluate a composed folio against the TD-018 promotion gates.

    ``anchor_word_images`` and ``reference_page`` are optional — the affected
    gate reports ``distance: None`` when its reference data is absent (the
    Mac runbook supplies both for promotion runs).
    """
    provs: list[dict] = []
    words_by_text: dict[str, list[np.ndarray]] = {}
    generated_images: list[np.ndarray] = []

    page = composed.page
    for line in composed.lines:
        for w in line.words:
            provs.append(w.provenance)
            crop = page[max(0, w.y_px):w.y_px + w.h_px,
                        max(0, w.x_px):w.x_px + w.w_px]
            if crop.size:
                gray = 255 - crop.mean(axis=2).astype(np.uint8)
                words_by_text.setdefault(w.text, []).append(gray)
                generated_images.append(gray)

    cer = cer_bands(provs)
    anti = anti_font_check(words_by_text, max_ncc=gates.anti_font_max_ncc)

    if anchor_word_images:
        distance = style_distance(generated_images, anchor_word_images)
        style = {"distance": distance, "threshold": gates.style_distance_max,
                 "ok": distance <= gates.style_distance_max,
                 "embedder": "hog-v1"}
    else:
        style = {"distance": None, "threshold": gates.style_distance_max,
                 "ok": None, "embedder": "hog-v1",
                 "note": "no anchor exemplars supplied"}

    if reference_page is not None:
        acceptance = acceptance_bands(
            page, reference_page,
            max_mean_distance=gates.acceptance_mean_distance_max,
        )
    else:
        acceptance = {"ok": None, "mean_distance": None,
                      "threshold": gates.acceptance_mean_distance_max,
                      "note": "no reference page supplied"}

    report = BenchReport(
        folio_id=composed.folio_id,
        cer=cer, anti_font=anti, style=style, acceptance=acceptance,
        gates=gates,
    )

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "metrics.json").write_text(
            json.dumps(report.to_dict(), indent=1, ensure_ascii=False)
        )
    return report
