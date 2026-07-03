"""Diagnostic bundles — the Mac ↔ review-environment feedback contract.

Every neural render or bench run can write a diagnostic directory:

    diag/
      run.json            environment, backend, checkpoint, seeds, params
      metrics.json        gate metrics (when produced by a bench run)
      report.json         per-folio composition report(s)
      sheets/*.png        proof sheets / page thumbnails
      words/*.png         sampled word strips (capped)
      provenance/*.json   per-word provenance (seed, retries, HTR scores)

`pack_bundle` zips the directory with a size cap (word images are sampled
down first, sheets are kept) so the bundle can be committed to `diagnostics/`
or attached for review. This is the data the cloud-side evaluation loop
consumes (TD-018 rollout: run on Mac → share bundle → evaluate → iterate).
"""

from __future__ import annotations

import json
import platform
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image


def _environment() -> dict:
    env = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:  # optional
        import torch  # type: ignore

        env["torch"] = torch.__version__
        env["mps_available"] = bool(getattr(torch.backends, "mps", None)
                                    and torch.backends.mps.is_available())
        env["cuda_available"] = torch.cuda.is_available()
    except ImportError:
        env["torch"] = None
    return env


def write_run_diagnostics(
    diag_dir: Path,
    run_info: dict,
    composed=None,
    max_word_images: int = 60,
) -> Path:
    """Write (or extend) a diagnostic directory for one run.

    ``composed`` is an optional ComposedFolio; when given, the page thumbnail,
    per-word provenance, and a sample of word crops are captured.
    """
    diag_dir = Path(diag_dir)
    (diag_dir / "sheets").mkdir(parents=True, exist_ok=True)
    (diag_dir / "provenance").mkdir(parents=True, exist_ok=True)
    (diag_dir / "words").mkdir(parents=True, exist_ok=True)

    run_path = diag_dir / "run.json"
    existing = json.loads(run_path.read_text()) if run_path.exists() else {
        "schema": 1, "environment": _environment(), "runs": [],
    }
    existing["runs"].append(run_info)
    run_path.write_text(json.dumps(existing, indent=1, ensure_ascii=False))

    if composed is not None:
        fid = composed.folio_id
        # page thumbnail sheet (max width 1200)
        page = composed.page
        scale = min(1.0, 1200 / page.shape[1])
        thumb = Image.fromarray(page, "RGB")
        if scale < 1.0:
            thumb = thumb.resize(
                (int(page.shape[1] * scale), int(page.shape[0] * scale)),
                Image.LANCZOS,
            )
        thumb.save(diag_dir / "sheets" / f"{fid}_page.png")

        # per-word provenance + sampled word crops
        prov = []
        crops_saved = 0
        for line in composed.lines:
            for w in line.words:
                prov.append({
                    "text": w.text, "x_px": w.x_px, "y_px": w.y_px,
                    "w_px": w.w_px, "h_px": w.h_px,
                    **{k: v for k, v in w.provenance.items() if k != "controls"},
                })
                if crops_saved < max_word_images:
                    crop = page[max(0, w.y_px):w.y_px + w.h_px,
                                max(0, w.x_px):w.x_px + w.w_px]
                    if crop.size:
                        Image.fromarray(crop, "RGB").save(
                            diag_dir / "words" /
                            f"{fid}_l{line.line_index:02d}_w{crops_saved:03d}.png"
                        )
                        crops_saved += 1
        (diag_dir / "provenance" / f"{fid}.json").write_text(
            json.dumps(prov, indent=1, ensure_ascii=False)
        )
        (diag_dir / "report.json").write_text(
            json.dumps(composed.report, indent=1, ensure_ascii=False)
        )

    return diag_dir


def pack_bundle(diag_dir: Path, out_zip: Path, max_mb: float = 25.0) -> Path:
    """Zip a diagnostic directory under a size cap.

    Priority order under the cap: run/metrics/report JSON, provenance,
    sheets, then word crops until the budget is exhausted.
    """
    diag_dir = Path(diag_dir)
    out_zip = Path(out_zip)
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    ordered: list[Path] = []
    for pattern in ("*.json", "provenance/*.json", "sheets/*", "words/*"):
        ordered.extend(sorted(diag_dir.glob(pattern)))

    budget = int(max_mb * 1024 * 1024)
    used = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in ordered:
            if not path.is_file():
                continue
            size = path.stat().st_size
            if used + size > budget:
                continue
            zf.write(path, path.relative_to(diag_dir))
            used += size
    return out_zip


def summarize_bundle(bundle_or_dir: Path) -> dict:
    """Quick machine-readable summary of a bundle (zip or directory)."""
    path = Path(bundle_or_dir)
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            run = json.loads(zf.read("run.json")) if "run.json" in names else {}
            metrics = (json.loads(zf.read("metrics.json"))
                       if "metrics.json" in names else None)
    else:
        run_path = path / "run.json"
        run = json.loads(run_path.read_text()) if run_path.exists() else {}
        metrics_path = path / "metrics.json"
        metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else None
        names = [str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()]

    return {
        "environment": run.get("environment", {}),
        "runs": len(run.get("runs", [])),
        "has_metrics": metrics is not None,
        "metrics": metrics,
        "files": len(names),
        "sheets": sorted(n for n in names if n.startswith("sheets/")),
    }
