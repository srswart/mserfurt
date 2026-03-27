#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="127.0.0.1"
PORT="8765"
AUTO_OPEN=1
ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST="${2:?missing value for --host}"
      shift 2
      ;;
    --port)
      PORT="${2:?missing value for --port}"
      shift 2
      ;;
    --no-open)
      AUTO_OPEN=0
      shift
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

URL="http://${HOST}:${PORT}"
PYTHON="$REPO_DIR/.venv/bin/python"

if [[ $AUTO_OPEN -eq 1 ]]; then
  (
    for _ in {1..30}; do
      if curl -fsS "$URL" >/dev/null 2>&1; then
        open "$URL" >/dev/null 2>&1 || true
        exit 0
      fi
      sleep 1
    done
  ) &
fi

cd "$REPO_DIR"

if [[ -x "$PYTHON" ]]; then
  if (( ${#ARGS[@]} > 0 )); then
    exec "$PYTHON" -m scribesim annotate-reviewed-exemplars --host "$HOST" --port "$PORT" "${ARGS[@]}"
  fi
  exec "$PYTHON" -m scribesim annotate-reviewed-exemplars --host "$HOST" --port "$PORT"
fi

if (( ${#ARGS[@]} > 0 )); then
  exec uv run scribesim annotate-reviewed-exemplars --host "$HOST" --port "$PORT" "${ARGS[@]}"
fi

exec uv run scribesim annotate-reviewed-exemplars --host "$HOST" --port "$PORT"
