#!/usr/bin/env python
"""ScribeHand TD-018 workflow orchestrator for local agents.

Reads docs/scribehand-orchestration.yaml, tracks progress in
diagnostics/.scribehand-orchestration-state.json, and validates step
artifacts so an agent can run everything except human visual review.

Usage:
    python scripts/scribehand/orchestrate.py status [--json]
    python scripts/scribehand/orchestrate.py next [--json]
    python scripts/scribehand/orchestrate.py validate <step_id> [--json]
    python scripts/scribehand/orchestrate.py record <step_id> --status passed|failed [--json]
    python scripts/scribehand/orchestrate.py env-check [--json]
    python scripts/scribehand/orchestrate.py env-export
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "docs" / "scribehand-orchestration.yaml"
ENV_FILE = REPO_ROOT / "diagnostics" / "scribehand.env"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_manifest() -> dict:
    if yaml is None:
        raise SystemExit("PyYAML required: uv sync --extra scribehand")
    return yaml.safe_load(MANIFEST.read_text())


def _expand(value: str, env: dict[str, str]) -> str:
    """Expand ${VAR} and $HOME from env dict + os.environ."""

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in env:
            return env[key]
        return os.environ.get(key, match.group(0))

    out = re.sub(r"\$\{([^}]+)\}", repl, value)
    out = os.path.expandvars(out)
    return out


def _load_env_file() -> dict[str, str]:
    merged = dict(os.environ)
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            merged[key.strip()] = val.strip().strip('"').strip("'")
    manifest = _load_manifest()
    for key, val in manifest.get("env", {}).items():
        merged.setdefault(key, _expand(str(val), merged))
    merged.setdefault("REPO_ROOT", str(REPO_ROOT))
    return merged


def _state_path(manifest: dict) -> Path:
    rel = manifest.get("state_file", "diagnostics/.scribehand-orchestration-state.json")
    return REPO_ROOT / rel


def _load_state(manifest: dict) -> dict:
    path = _state_path(manifest)
    if path.exists():
        return json.loads(path.read_text())
    return {
        "schema": 1,
        "manifest": str(MANIFEST.relative_to(REPO_ROOT)),
        "started_at": _utc_now(),
        "steps": {},
        "env": {},
    }


def _save_state(manifest: dict, state: dict) -> None:
    path = _state_path(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def _step_status(state: dict, step_id: str) -> str:
    return state.get("steps", {}).get(step_id, {}).get("status", "pending")


def _deps_satisfied(manifest: dict, state: dict, step_id: str) -> bool:
    step = manifest["steps"][step_id]
    for dep in step.get("depends_on", []):
        if _step_status(state, dep) != "passed":
            return False
    return True


def _missing_env(step: dict, env: dict[str, str]) -> list[str]:
    missing = []
    for key in step.get("requires_env", []):
        if not env.get(key, "").strip():
            missing.append(key)
    return missing


def _resolve_path(spec: str, env: dict[str, str]) -> Path:
    expanded = _expand(spec, env)
    p = Path(expanded)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p


def _json_get(data: dict, dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _check_artifact(spec: dict, env: dict[str, str]) -> tuple[bool, str]:
    path_spec = spec.get("path", "")
    p = _resolve_path(path_spec, env)
    if not p.exists():
        return False, f"missing: {p}"

    if "json" in spec:
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError as exc:
            return False, f"invalid JSON in {p}: {exc}"
        for key, expected in spec["json"].items():
            actual = _json_get(data, key) if "." in key else data.get(key)
            if actual != expected:
                return False, f"{p}: expected {key}={expected!r}, got {actual!r}"

    if "contains" in spec:
        text = p.read_text()
        needle = spec["contains"]
        if needle not in text:
            return False, f"{p}: does not contain {needle!r}"

    return True, f"ok: {p}"


def validate_step(step_id: str, env: dict[str, str] | None = None) -> dict:
    manifest = _load_manifest()
    env = env or _load_env_file()
    step = manifest["steps"].get(step_id)
    if step is None:
        raise SystemExit(f"unknown step: {step_id}")

    missing = _missing_env(step, env)
    if missing:
        return {
            "step_id": step_id,
            "ok": False,
            "reason": "missing_env",
            "missing_env": missing,
        }

    if step.get("executor") == "human":
        reviews = []
        all_ok = True
        for spec in step.get("artifacts_required", []):
            p = _resolve_path(spec, env)
            ok = p.exists()
            reviews.append({"path": str(p), "exists": ok})
            all_ok = all_ok and ok
        return {
            "step_id": step_id,
            "ok": all_ok,
            "executor": "human",
            "human_reviews": reviews,
            "message": "awaiting human_review.md" if not all_ok else "human review complete",
        }

    checks: list[dict] = []
    all_ok = True
    for spec in step.get("success", {}).get("artifacts", []):
        ok, detail = _check_artifact(spec, env)
        checks.append({"ok": ok, "detail": detail})
        all_ok = all_ok and ok

    return {"step_id": step_id, "ok": all_ok, "checks": checks}


def cmd_status(args: argparse.Namespace) -> dict:
    manifest = _load_manifest()
    state = _load_state(manifest)
    steps_summary = []
    for sid, step in manifest["steps"].items():
        steps_summary.append({
            "id": sid,
            "title": step["title"],
            "executor": step.get("executor", "agent"),
            "status": _step_status(state, sid),
        })
    passed = sum(1 for s in steps_summary if s["status"] == "passed")
    out = {
        "manifest": str(MANIFEST),
        "state_file": str(_state_path(manifest)),
        "steps_total": len(steps_summary),
        "steps_passed": passed,
        "steps": steps_summary,
    }
    return out


def cmd_next(args: argparse.Namespace) -> dict:
    manifest = _load_manifest()
    state = _load_state(manifest)
    env = _load_env_file()

    for sid, step in manifest["steps"].items():
        status = _step_status(state, sid)
        if status == "passed":
            continue
        if not _deps_satisfied(manifest, state, sid):
            continue

        missing = _missing_env(step, env)
        validation = validate_step(sid, env)

        return {
            "step_id": sid,
            "title": step["title"],
            "executor": step.get("executor", "agent"),
            "status": status,
            "commands": [_expand(c, env) for c in step.get("commands", [])],
            "missing_env": missing,
            "manual": step.get("manual", False),
            "notes": step.get("notes", step.get("on_failure", "")),
            "validation_preview": validation,
            "human_required": step.get("executor") == "human",
        }

    return {"step_id": None, "message": "all steps passed"}


def cmd_record(args: argparse.Namespace) -> dict:
    manifest = _load_manifest()
    state = _load_state(manifest)
    if args.step_id not in manifest["steps"]:
        raise SystemExit(f"unknown step: {args.step_id}")

    state.setdefault("steps", {})[args.step_id] = {
        "status": args.status,
        "completed_at": _utc_now(),
    }
    state["updated_at"] = _utc_now()
    _save_state(manifest, state)
    return {"recorded": args.step_id, "status": args.status}


def cmd_env_check(args: argparse.Namespace) -> dict:
    manifest = _load_manifest()
    env = _load_env_file()
    required = set()
    for step in manifest["steps"].values():
        required.update(step.get("requires_env", []))
    missing = sorted(k for k in required if not env.get(k, "").strip())
    return {"env_file": str(ENV_FILE), "missing": missing, "ok": not missing}


def cmd_env_export(_args: argparse.Namespace) -> None:
    if not ENV_FILE.exists():
        print(f"# create {ENV_FILE} from docs/scribehand-orchestration.env.example", file=sys.stderr)
        raise SystemExit(1)
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.startswith("export "):
            line = f"export {line}"
        print(line)
    return None


def _emit(data: dict | None, as_json: bool) -> None:
    if data is None:
        return
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        for key, val in data.items():
            if isinstance(val, list):
                print(f"{key}:")
                for item in val:
                    print(f"  - {item}")
            else:
                print(f"{key}: {val}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    def add_json(p: argparse.ArgumentParser) -> None:
        p.add_argument("--json", action="store_true", help="JSON output")

    add_json(sub.add_parser("status", help="Show pipeline progress"))
    add_json(sub.add_parser("next", help="Next actionable step"))
    p_val = sub.add_parser("validate", help="Validate step artifacts")
    add_json(p_val)
    p_val.add_argument("step_id")
    p_rec = sub.add_parser("record", help="Record step outcome")
    add_json(p_rec)
    p_rec.add_argument("step_id")
    p_rec.add_argument("--status", choices=["passed", "failed"], required=True)
    add_json(sub.add_parser("env-check", help="List unset required env vars"))
    sub.add_parser("env-export", help="Print shell exports from scribehand.env")

    args = ap.parse_args()
    handlers = {
        "status": cmd_status,
        "next": cmd_next,
        "validate": lambda a: validate_step(a.step_id),
        "record": cmd_record,
        "env-check": cmd_env_check,
        "env-export": cmd_env_export,
    }
    result = handlers[args.command](args)
    if args.command == "env-export":
        return
    _emit(result, args.json)
    if isinstance(result, dict) and result.get("ok") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
