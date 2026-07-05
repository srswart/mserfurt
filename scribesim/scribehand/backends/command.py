"""Command backend — batch subprocess protocol for Mac-side model runners.

Request/response contract (schema 1):

request.json::

    {"schema": 1,
     "style_dir": "/path/to/style_anchor_v1" | null,
     "checkpoint": "/path/to/ckpt" | null,
     "words": [{"id": "w0", "text": "und", "seed": 123,
                "controls": {...}, "out": "/tmp/.../w0.png"}, ...]}

response.json::

    {"schema": 1,
     "runner": {"name": "...", "device": "mps", ...},
     "results": [{"id": "w0", "image": "/tmp/.../w0.png",
                  "baseline_frac": 0.72, "xheight_frac": 0.33}, ...]}

The runner writes grayscale ink masks (0 = no ink). Runners for One-DM and
DiffusionPen live in scripts/scribehand/ and run inside the user's clone of
the upstream repos.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from scribesim.scribehand.types import WordRequest, WordStrip


class CommandBackend:
    def __init__(
        self,
        name: str,
        argv: list[str],
        workdir: Path,
        style_dir: Path | None = None,
        checkpoint: str | None = None,
        timeout_s: float = 3600.0,
    ) -> None:
        self.name = name
        self.argv = argv
        self.workdir = Path(workdir)
        self.style_dir = style_dir
        self.checkpoint = checkpoint
        self.timeout_s = timeout_s

    def generate_batch(self, requests: list[WordRequest]) -> list[WordStrip]:
        with tempfile.TemporaryDirectory(prefix="scribehand-") as td:
            tmp = Path(td)
            words = []
            for i, req in enumerate(requests):
                words.append({
                    "id": f"w{i}",
                    "text": req.text,
                    "seed": req.seed,
                    "mode": req.mode,
                    "controls": req.controls,
                    "out": str(tmp / f"w{i}.png"),
                })
            request_path = tmp / "request.json"
            response_path = tmp / "response.json"
            request_path.write_text(json.dumps({
                "schema": 1,
                "style_dir": str(self.style_dir) if self.style_dir else None,
                "checkpoint": self.checkpoint,
                "words": words,
            }, ensure_ascii=False))

            proc = subprocess.run(
                [*self.argv, "--request", str(request_path),
                 "--response", str(response_path)],
                cwd=self.workdir,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"backend {self.name!r} runner failed "
                    f"(exit {proc.returncode}):\n{proc.stderr[-2000:]}"
                )
            if not response_path.exists():
                raise RuntimeError(f"backend {self.name!r} wrote no response file")

            response = json.loads(response_path.read_text())
            by_id = {r["id"]: r for r in response.get("results", [])}

            strips: list[WordStrip] = []
            for i, req in enumerate(requests):
                entry = by_id.get(f"w{i}")
                if entry is None:
                    raise RuntimeError(
                        f"backend {self.name!r}: no result for word {i} ({req.text!r})"
                    )
                img = Image.open(entry["image"]).convert("L")
                strips.append(WordStrip(
                    ink=np.asarray(img, dtype=np.uint8),
                    baseline_frac=float(entry.get("baseline_frac", 0.75)),
                    xheight_frac=float(entry.get("xheight_frac", 0.35)),
                ))
            return strips
