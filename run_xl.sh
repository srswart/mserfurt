#!/usr/bin/env bash
# run_xl.sh — execute the XL pipeline on the annotated source manuscript
#
# Usage:
#   ./run_xl.sh                         # dry-run (no LLM calls), all folios
#   ./run_xl.sh --live                  # live translation (requires API keys)
#   ./run_xl.sh --folio 1r              # restrict output to a single folio
#   ./run_xl.sh --sections 1,2          # only translate sections 1 and 2
#   ./run_xl.sh --live --folio 1r --sections 1,2   # fast dev run (~30 passages)
#   ./run_xl.sh --formats json,jsonl    # choose output formats
#   ./run_xl.sh --output /tmp/myout     # custom output directory

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="$REPO_DIR/source/ms-erfurt-source-annotated.md"
DRY_RUN="--dry-run"
OUTPUT="$REPO_DIR/output"  # overridden to output-live/ when --live is set
FOLIO=""
SECTIONS=""
FORMATS="json,manifest,xml"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --live)        DRY_RUN=""; OUTPUT="$REPO_DIR/output-live"; shift ;;
    --folio)       FOLIO="--folio $2"; shift 2 ;;
    --sections)    SECTIONS="--sections $2"; shift 2 ;;
    --output)      OUTPUT="$2"; shift 2 ;;
    --formats)     FORMATS="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

mkdir -p "$OUTPUT"

echo "=== XL pipeline ==="
echo "input  : $INPUT"
echo "output : $OUTPUT"
echo "mode   : ${DRY_RUN:---live}"
echo ""

cd "$REPO_DIR"
# shellcheck disable=SC2086
.venv/bin/python -m xl translate \
  --input "$INPUT" \
  --output "$OUTPUT" \
  --formats "$FORMATS" \
  $DRY_RUN \
  $FOLIO \
  $SECTIONS
