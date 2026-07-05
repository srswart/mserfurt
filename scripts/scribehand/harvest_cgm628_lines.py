#!/usr/bin/env python
"""Download Cgm 628 folio pages and extract line strips for line-level training.

Fetches pages from the BSB IIIF manifest, skips pages already harvested,
downloads at extraction resolution, and runs extract-lines per page.

Usage:
    uv run python scripts/scribehand/harvest_cgm628_lines.py \\
        --target-pages 55 \\
        --lines-root work/cgm628_anchor/lines \\
        --folios-dir shared/training/handsim/exemplar_harvest_v1/folios/BSB_Cgm_628_Tauler._Mystische_Texte_u.a._Meister_Eckhart
"""

from __future__ import annotations

import argparse
import json
import random
import re
import time
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.refextract.segment import segment_lines
from scribesim.refselect.harvest import build_mdz_manifest_url
from scribesim.refselect.iiif import download_folio, fetch_manifest, sanitize_filename

CGM628_OBJECT_ID = "bsb00144295"
_PAGE_NUM_RE = re.compile(r"(\d{3,4})")


def _log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[harvest-cgm628 {ts}] {msg}", flush=True)


def _page_id(label: str) -> str:
    stem = sanitize_filename(label)
    match = _PAGE_NUM_RE.search(stem)
    return match.group(1).zfill(4) if match else stem


def _existing_page_ids(lines_root: Path) -> set[str]:
    if not lines_root.is_dir():
        return set()
    return {p.name for p in lines_root.iterdir() if p.is_dir()}


def _select_text_pages(
    canvases: list[dict],
    *,
    skip_front: int,
    skip_back: int,
    exclude: set[str],
    target: int,
    seed: int,
) -> list[dict]:
    """Stratified sample of text canvases, excluding already-harvested page ids."""
    lo = skip_front
    hi = max(lo + 1, len(canvases) - skip_back)
    pool: list[tuple[int, dict, str]] = []
    for idx in range(lo, hi):
        canvas = canvases[idx]
        pid = _page_id(canvas.get("label", ""))
        if pid in exclude:
            continue
        pool.append((idx, canvas, pid))

    if not pool:
        raise SystemExit("No candidate pages left after exclusions")

    n = min(target, len(pool))
    rng = random.Random(seed)
    if n >= len(pool):
        chosen = pool
    else:
        stride = len(pool) // n
        jitter = max(1, stride // 3)
        indices: list[int] = []
        for i in range(n):
            base = i * stride
            idx = min(base + rng.randint(0, jitter), len(pool) - 1)
            indices.append(idx)
        seen: set[int] = set()
        deduped: list[int] = []
        for idx in sorted(indices):
            if idx not in seen:
                seen.add(idx)
                deduped.append(idx)
        while len(deduped) < n:
            remaining = [i for i in range(len(pool)) if i not in seen]
            if not remaining:
                break
            extra = rng.choice(remaining)
            seen.add(extra)
            deduped.append(extra)
        chosen = [pool[i] for i in sorted(deduped)]

    return [c for _, c, _ in sorted(chosen, key=lambda t: t[0])]


def _extract_lines(page_jpg: Path, out_dir: Path, min_gap: int) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    img = np.array(Image.open(page_jpg).convert("L"))
    lines = segment_lines(img, min_gap_rows=min_gap)
    for i, strip in enumerate(lines):
        Image.fromarray(strip).save(str(out_dir / f"line_{i:04d}.png"))
    return len(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-pages", type=int, default=55,
                    help="How many NEW pages to download and segment")
    ap.add_argument("--lines-root", type=Path, default=Path("work/cgm628_anchor/lines"))
    ap.add_argument("--folios-dir", type=Path, required=True,
                    help="Where to store downloaded page JPGs")
    ap.add_argument("--object-id", default=CGM628_OBJECT_ID)
    ap.add_argument("--skip-front", type=int, default=8,
                    help="Skip first N canvases (covers/title)")
    ap.add_argument("--skip-back", type=int, default=4,
                    help="Skip last N canvases (back matter)")
    ap.add_argument("--resolution", choices=("analysis", "extraction"), default="extraction")
    ap.add_argument("--min-gap", type=int, default=3)
    ap.add_argument("--seed", type=int, default=628)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest_url = build_mdz_manifest_url(args.object_id)
    _log(f"fetching manifest {manifest_url}")
    manifest = fetch_manifest(manifest_url)
    canvases = manifest["canvases"]
    _log(f"manuscript: {manifest['title']!r} ({len(canvases)} canvases)")

    existing = _existing_page_ids(args.lines_root)
    _log(f"existing harvested pages: {len(existing)} → {sorted(existing)[:5]}…")

    selected = _select_text_pages(
        canvases,
        skip_front=args.skip_front,
        skip_back=args.skip_back,
        exclude=existing,
        target=args.target_pages,
        seed=args.seed,
    )
    page_ids = [_page_id(c.get("label", "")) for c in selected]
    _log(f"selected {len(selected)} new pages (target {args.target_pages})")
    _log(f"page ids: {', '.join(page_ids[:12])}{'…' if len(page_ids) > 12 else ''}")

    if args.dry_run:
        summary = {
            "dry_run": True,
            "selected_pages": page_ids,
            "existing_pages": sorted(existing),
            "resolution": args.resolution,
        }
        print(json.dumps(summary, indent=2))
        return

    args.folios_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    results: list[dict] = []
    total_lines = 0

    for i, canvas in enumerate(selected, 1):
        pid = _page_id(canvas.get("label", ""))
        _log(f"page {i}/{len(selected)} id={pid} label={canvas.get('label')!r}")

        t0 = time.monotonic()
        try:
            jpg = download_folio(canvas, args.folios_dir, resolution=args.resolution)
        except Exception as exc:
            _log(f"  download FAILED: {exc}")
            results.append({"page_id": pid, "status": "download_failed", "error": str(exc)})
            continue
        dl_sec = time.monotonic() - t0
        _log(f"  downloaded → {jpg.name} ({jpg.stat().st_size // 1024} KB, {dl_sec:.1f}s)")

        line_dir = args.lines_root / pid
        if line_dir.is_dir() and any(line_dir.glob("line_*.png")):
            n_lines = len(list(line_dir.glob("line_*.png")))
            _log(f"  lines already present ({n_lines}), skipping extract")
        else:
            try:
                n_lines = _extract_lines(jpg, line_dir, args.min_gap)
            except Exception as exc:
                _log(f"  extract FAILED: {exc}")
                results.append({"page_id": pid, "status": "extract_failed", "error": str(exc)})
                continue
            _log(f"  extracted {n_lines} line strips → {line_dir}")

        total_lines += n_lines
        elapsed = (time.monotonic() - started) / 60
        rate = i / max(elapsed, 0.01)
        eta = (len(selected) - i) / max(rate, 0.01)
        results.append({
            "page_id": pid,
            "status": "ok",
            "jpg": str(jpg),
            "lines": n_lines,
        })
        _log(f"  progress {i}/{len(selected)} pages, {total_lines} lines total "
             f"| elapsed {elapsed:.1f}m ETA {eta:.1f}m")

    ok = sum(1 for r in results if r.get("status") == "ok")
    summary = {
        "manifest_url": manifest_url,
        "title": manifest["title"],
        "resolution": args.resolution,
        "target_pages": args.target_pages,
        "selected_pages": page_ids,
        "existing_pages_before": sorted(existing),
        "completed_ok": ok,
        "failed": len(results) - ok,
        "total_new_lines": total_lines,
        "elapsed_min": round((time.monotonic() - started) / 60, 2),
        "results": results,
    }
    summary_path = args.lines_root.parent / "harvest_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _log(f"done — {ok}/{len(selected)} pages OK, {total_lines} new line strips "
         f"in {(time.monotonic() - started) / 60:.1f}m")
    _log(f"summary → {summary_path}")


if __name__ == "__main__":
    main()
