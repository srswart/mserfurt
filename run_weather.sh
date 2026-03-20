#!/usr/bin/env bash
# run_weather.sh — apply 560-year weathering to ScribeSim render output
#
# Usage:
#   ./run_weather.sh                           # dry-run, all folios in manifest
#   ./run_weather.sh --folio f04v              # single folio, dry-run
#   ./run_weather.sh --live                    # weather all folios to PNG
#   ./run_weather.sh --live --folio f04v       # weather one folio
#   ./run_weather.sh --live --groundtruth      # weather + update PAGE XML
#   ./run_weather.sh --input /path/to/render   # custom ScribeSim output directory
#   ./run_weather.sh --output /path/to/out     # custom weather output directory
#   ./run_weather.sh --profile /path/to.toml   # custom weathering profile

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="$REPO_DIR/render-output"
OUTPUT_DIR="$REPO_DIR/weather-output"
FOLIO=""
DRY_RUN="--dry-run"
GROUNDTRUTH=0
PROFILE_OPT=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --live)        DRY_RUN=""; shift ;;
    --folio)       FOLIO="$2"; shift 2 ;;
    --groundtruth) GROUNDTRUTH=1; shift ;;
    --input)       INPUT_DIR="$2"; shift 2 ;;
    --output)      OUTPUT_DIR="$2"; shift 2 ;;
    --profile)     PROFILE_OPT="--profile $2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

PYTHON="$REPO_DIR/.venv/bin/python"

echo "=== Weather pipeline ==="
echo "input  : $INPUT_DIR"
echo "output : $OUTPUT_DIR"
echo "mode   : $([[ -n "$DRY_RUN" ]] && echo "dry-run" || echo "live")"
[[ -n "$FOLIO" ]]       && echo "folio  : $FOLIO"
[[ -n "$PROFILE_OPT" ]] && echo "profile: ${PROFILE_OPT#--profile }"
echo ""

cd "$REPO_DIR"

# ---------------------------------------------------------------------------
# Apply weathering
# ---------------------------------------------------------------------------

if [[ -n "$FOLIO" ]]; then
  # Single folio
  # shellcheck disable=SC2086
  "$PYTHON" -m weather $PROFILE_OPT apply \
    --folio "$FOLIO" \
    --input-dir "$INPUT_DIR" \
    --output-dir "$OUTPUT_DIR" \
    ${DRY_RUN:+--dry-run}
else
  # Batch — all folios in manifest
  # shellcheck disable=SC2086
  "$PYTHON" -m weather $PROFILE_OPT apply-batch \
    --input-dir "$INPUT_DIR" \
    --output-dir "$OUTPUT_DIR" \
    ${DRY_RUN:+--dry-run}
fi

# ---------------------------------------------------------------------------
# Groundtruth (PAGE XML) — only in live mode with --groundtruth
# ---------------------------------------------------------------------------

if [[ $GROUNDTRUTH -eq 1 && -z "$DRY_RUN" ]]; then
  echo ""
  echo "=== Updating PAGE XML ground truth ==="

  if [[ -n "$FOLIO" ]]; then
    # shellcheck disable=SC2086
    "$PYTHON" -m weather $PROFILE_OPT groundtruth-update \
      --folio "$FOLIO" \
      --input-dir "$INPUT_DIR" \
      --output-dir "$OUTPUT_DIR"
  else
    # Update ground truth for every folio in the manifest
    manifest="$INPUT_DIR/manifest.json"
    if [[ -f "$manifest" ]]; then
      "$PYTHON" -c "
import json, subprocess, sys
manifest = json.loads(open('$manifest').read())
profile_opt = '$PROFILE_OPT'.split() if '$PROFILE_OPT' else []
for entry in manifest.get('folios', []):
    fid = entry['id']
    cmd = ['$PYTHON', '-m', 'weather'] + profile_opt + [
        'groundtruth-update', '--folio', fid,
        '--input-dir', '$INPUT_DIR',
        '--output-dir', '$OUTPUT_DIR',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout, end='')
    if result.returncode != 0:
        print(result.stderr, end='', file=sys.stderr)
"
    else
      echo "warning: no manifest.json found in $INPUT_DIR — skipping groundtruth" >&2
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

if [[ -z "$DRY_RUN" ]]; then
  echo ""
  echo "=== Output ==="
  ls -lh "$OUTPUT_DIR"/*_weathered.png 2>/dev/null || echo "(no weathered PNGs written)"
  if [[ $GROUNDTRUTH -eq 1 ]]; then
    ls -lh "$OUTPUT_DIR"/*_weathered.xml 2>/dev/null || echo "(no weathered XMLs written)"
  fi
fi
