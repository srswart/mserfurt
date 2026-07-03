#!/usr/bin/env python
"""Print a JSON environment report for TD-018 diagnostic bundles."""

from __future__ import annotations

import json
import platform
import sys


def main() -> None:
    report: dict = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
    }
    try:
        import torch

        report["torch"] = torch.__version__
        report["mps_available"] = bool(
            getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()
        )
        report["cuda_available"] = torch.cuda.is_available()
        device = "mps" if report["mps_available"] else (
            "cuda" if report["cuda_available"] else "cpu"
        )
        report["recommended_device"] = device
        # tiny smoke op on the recommended device
        x = torch.ones(64, 64, device=device)
        report["device_smoke_ok"] = bool(float((x @ x).sum()) > 0)
    except Exception as exc:  # noqa: BLE001 - report anything, this is diagnostics
        report["torch_error"] = f"{type(exc).__name__}: {exc}"

    for mod in ("transformers", "datasets", "diffusers"):
        try:
            report[mod] = __import__(mod).__version__
        except Exception:
            report[mod] = None

    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
