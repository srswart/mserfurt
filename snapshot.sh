#!/usr/bin/env bash
# snapshot.sh — render checkpoint folios and copy to review locations
#
# Renders f01r (clean baseline), f04v (water + corner damage), and f14r
# (irregular vellum) through the full ScribeSim + Weather pipeline, then
# copies all outputs to the project directory and ~/Desktop/scribesim
# with a labeled subdirectory for side-by-side comparison across advances.
#
# Usage:
#   ./snapshot.sh <label>                    # e.g. ./snapshot.sh hand-002
#   ./snapshot.sh <label> --folio f01r       # single folio only
#   ./snapshot.sh <label> --scribesim-only   # skip weather pass
#   ./snapshot.sh <label> --quick            # f01r only, scribesim only

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$REPO_DIR/.venv/bin/python"

DESKTOP_DIR="$HOME/Desktop/scribesim"
SNAPSHOT_DIR="$REPO_DIR/snapshots"

LABEL="${1:?Usage: ./snapshot.sh <label> [--folio <id>] [--scribesim-only] [--quick]}"
shift

FOLIOS="f01r"
WEATHER=1
QUICK=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --folio)          FOLIOS="$2"; shift 2 ;;
    --scribesim-only) WEATHER=0; shift ;;
    --quick)          FOLIOS="f01r"; WEATHER=0; QUICK=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT_LABEL="${TIMESTAMP}_${LABEL}"

# Output directories
LOCAL_OUT="$SNAPSHOT_DIR/$OUT_LABEL"
DESKTOP_OUT="$DESKTOP_DIR/$OUT_LABEL"

mkdir -p "$LOCAL_OUT"
mkdir -p "$DESKTOP_OUT"

echo "=== Snapshot: $LABEL ==="
echo "timestamp : $TIMESTAMP"
echo "folios    : $FOLIOS"
echo "weather   : $([[ $WEATHER -eq 1 ]] && echo "yes" || echo "skip")"
echo "local     : $LOCAL_OUT"
echo "desktop   : $DESKTOP_OUT"
echo ""

cd "$REPO_DIR"

# ---------------------------------------------------------------------------
# ScribeSim render
# ---------------------------------------------------------------------------

RENDER_OUT="$LOCAL_OUT/render"
mkdir -p "$RENDER_OUT"

for fid in $FOLIOS; do
  echo "--- ScribeSim: $fid ---"
  "$PYTHON" -m scribesim render "$fid" \
    --input-dir "$REPO_DIR/output-live" \
    --output-dir "$RENDER_OUT" 2>&1 || {
      echo "  [warn] scribesim render failed for $fid — skipping"
      continue
    }

  # Also produce ground truth
  "$PYTHON" -m scribesim groundtruth "$fid" \
    --input-dir "$RENDER_OUT" \
    --output-dir "$RENDER_OUT" 2>&1 || true
done

# ---------------------------------------------------------------------------
# Weather pass (optional)
# ---------------------------------------------------------------------------

if [[ $WEATHER -eq 1 ]]; then
  WEATHER_OUT="$LOCAL_OUT/weathered"
  mkdir -p "$WEATHER_OUT"

  for fid in $FOLIOS; do
    echo "--- Weather: $fid ---"
    "$PYTHON" -m weather apply \
      --folio "$fid" \
      --input-dir "$RENDER_OUT" \
      --output-dir "$WEATHER_OUT" 2>&1 || {
        echo "  [warn] weather apply failed for $fid — skipping"
        continue
      }

    "$PYTHON" -m weather groundtruth-update \
      --folio "$fid" \
      --input-dir "$RENDER_OUT" \
      --output-dir "$WEATHER_OUT" 2>&1 || true
  done
fi

# ---------------------------------------------------------------------------
# Copy to desktop
# ---------------------------------------------------------------------------

echo ""
echo "=== Copying to desktop ==="
cp -r "$LOCAL_OUT"/* "$DESKTOP_OUT/"

# ---------------------------------------------------------------------------
# Write manifest
# ---------------------------------------------------------------------------

cat > "$LOCAL_OUT/SNAPSHOT.md" <<EOF
# Snapshot: $LABEL

- **Timestamp:** $TIMESTAMP
- **Folios:** $FOLIOS
- **Weather:** $([[ $WEATHER -eq 1 ]] && echo "yes" || echo "no")
- **Branch:** $(git branch --show-current 2>/dev/null || echo "unknown")
- **Commit:** $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

## What to look for

Check the rendered PNGs for the changes introduced by this advance.
Compare against the previous snapshot to see the visual delta.
EOF

cp "$LOCAL_OUT/SNAPSHOT.md" "$DESKTOP_OUT/SNAPSHOT.md"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "=== Snapshot complete ==="
echo ""
echo "Local:   $LOCAL_OUT"
echo "Desktop: $DESKTOP_OUT"
echo ""
echo "Files:"
find "$LOCAL_OUT" -name "*.png" -o -name "*.xml" | sort | while read -r f; do
  echo "  $(basename "$f")  ($(du -h "$f" | cut -f1))"
done
echo ""
echo "Previous snapshots:"
ls -1d "$SNAPSHOT_DIR"/*/ 2>/dev/null | tail -5 | while read -r d; do
  echo "  $(basename "$d")"
done
