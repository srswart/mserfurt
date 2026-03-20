#!/usr/bin/env bash
# run_scribesim.sh — render ScribeSim output from XL folio JSON
#
# Usage:
#   ./run_scribesim.sh                        # dry-run, all folios in manifest
#   ./run_scribesim.sh --folio f01r           # single folio, dry-run
#   ./run_scribesim.sh --live                 # render all folios to PNG + heatmap
#   ./run_scribesim.sh --live --folio f01r    # render one folio
#   ./run_scribesim.sh --groundtruth          # also emit PAGE XML for each folio
#   ./run_scribesim.sh --input /path/to/json  # custom XL output directory
#   ./run_scribesim.sh --output /path/to/out  # custom render output directory

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="$REPO_DIR/output-live"
OUTPUT_DIR="$REPO_DIR/render-output"
FOLIO=""
DRY_RUN="--dry-run"
GROUNDTRUTH=0

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --live)        DRY_RUN=""; shift ;;
    --folio)       FOLIO="$2"; shift 2 ;;
    --groundtruth) GROUNDTRUTH=1; shift ;;
    --input)       INPUT_DIR="$2"; shift 2 ;;
    --output)      OUTPUT_DIR="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

PYTHON="$REPO_DIR/.venv/bin/python"

echo "=== ScribeSim pipeline ==="
echo "input  : $INPUT_DIR"
echo "output : $OUTPUT_DIR"
echo "mode   : $([[ -n "$DRY_RUN" ]] && echo "dry-run" || echo "live")"
[[ -n "$FOLIO" ]] && echo "folio  : $FOLIO"
echo ""

cd "$REPO_DIR"

# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

if [[ -n "$FOLIO" ]]; then
  # Single folio
  "$PYTHON" -m scribesim render "$FOLIO" \
    --input-dir "$INPUT_DIR" \
    --output-dir "$OUTPUT_DIR" \
    ${DRY_RUN:+--dry-run}
else
  # Batch — all folios in manifest
  "$PYTHON" -m scribesim render-batch \
    --input-dir "$INPUT_DIR" \
    --output-dir "$OUTPUT_DIR" \
    ${DRY_RUN:+--dry-run}
fi

# ---------------------------------------------------------------------------
# Ground truth (PAGE XML) — only in live mode with --groundtruth
# ---------------------------------------------------------------------------

if [[ $GROUNDTRUTH -eq 1 && -z "$DRY_RUN" ]]; then
  echo ""
  echo "=== Emitting PAGE XML ground truth ==="

  if [[ -n "$FOLIO" ]]; then
    "$PYTHON" -m scribesim groundtruth "$FOLIO" \
      --input-dir "$OUTPUT_DIR" \
      --output-dir "$OUTPUT_DIR"
  else
    # Emit ground truth for every folio that was rendered
    manifest="$INPUT_DIR/manifest.json"
    if [[ -f "$manifest" ]]; then
      python3 -c "
import json, subprocess, sys
manifest = json.loads(open('$manifest').read())
for entry in manifest.get('folios', []):
    fid = entry['id']
    result = subprocess.run(
        ['$PYTHON', '-m', 'scribesim', 'groundtruth', fid,
         '--input-dir', '$OUTPUT_DIR', '--output-dir', '$OUTPUT_DIR'],
        capture_output=True, text=True
    )
    print(result.stdout, end='')
    if result.returncode != 0:
        print(result.stderr, end='', file=sys.stderr)
"
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

if [[ -z "$DRY_RUN" ]]; then
  echo ""
  echo "=== Output ==="
  ls -lh "$OUTPUT_DIR"/*.png 2>/dev/null || echo "(no PNGs written)"
  [[ $GROUNDTRUTH -eq 1 ]] && ls -lh "$OUTPUT_DIR"/*.xml 2>/dev/null || true
fi
