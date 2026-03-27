#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$REPO_DIR/.venv/bin/python"

REVIEWED_MANIFEST="$REPO_DIR/shared/training/handsim/reviewed_annotations/workbench_v1/reviewed_manifest.toml"
FREEZE_OUTPUT="$REPO_DIR/shared/training/handsim/reviewed_annotations/reviewed_exemplars_v1"
EVOFIT_OUTPUT="$REPO_DIR/shared/training/handsim/reviewed_annotations/reviewed_evofit_v1"
GUIDES_OUTPUT="$REPO_DIR/shared/training/handsim/reviewed_annotations/reviewed_promoted_guides_v1"
GUIDE_CATALOG="$REPO_DIR/shared/hands/pathguides/reviewed_promoted_v1.toml"
KIND="all"
SYMBOLS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reviewed-manifest)
      REVIEWED_MANIFEST="${2:?missing value for --reviewed-manifest}"
      shift 2
      ;;
    --freeze-output)
      FREEZE_OUTPUT="${2:?missing value for --freeze-output}"
      shift 2
      ;;
    --evofit-output)
      EVOFIT_OUTPUT="${2:?missing value for --evofit-output}"
      shift 2
      ;;
    --guides-output)
      GUIDES_OUTPUT="${2:?missing value for --guides-output}"
      shift 2
      ;;
    --guide-catalog)
      GUIDE_CATALOG="${2:?missing value for --guide-catalog}"
      shift 2
      ;;
    --kind)
      KIND="${2:?missing value for --kind}"
      shift 2
      ;;
    --symbols)
      SYMBOLS="${2:?missing value for --symbols}"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

run_scribesim() {
  if [[ -x "$PYTHON" ]]; then
    "$PYTHON" -m scribesim "$@"
    return
  fi
  uv run scribesim "$@"
}

echo "=== Reviewed Catalog Pipeline ==="
echo "reviewed manifest : $REVIEWED_MANIFEST"
echo "freeze output     : $FREEZE_OUTPUT"
echo "evofit output     : $EVOFIT_OUTPUT"
echo "guides output     : $GUIDES_OUTPUT"
echo "guide catalog     : $GUIDE_CATALOG"
echo "kind              : $KIND"
[[ -n "$SYMBOLS" ]] && echo "symbols           : $SYMBOLS"
echo ""

cd "$REPO_DIR"

echo "=== Step 1/3: Freeze reviewed exemplars ==="
run_scribesim freeze-reviewed-exemplars \
  --reviewed-manifest "$REVIEWED_MANIFEST" \
  --output "$FREEZE_OUTPUT"

echo ""
echo "=== Step 2/3: Reviewed evofit ==="
EVOFIT_ARGS=(
  evofit-reviewed-exemplars
  --reviewed-manifest "$FREEZE_OUTPUT/reviewed_exemplar_manifest.toml"
  --output "$EVOFIT_OUTPUT"
  --kind "$KIND"
)
if [[ -n "$SYMBOLS" ]]; then
  EVOFIT_ARGS+=(--symbols "$SYMBOLS")
fi
run_scribesim "${EVOFIT_ARGS[@]}"

echo ""
echo "=== Step 3/3: Freeze reviewed evofit guides ==="
run_scribesim freeze-reviewed-evofit-guides \
  --evofit-manifest "$EVOFIT_OUTPUT/manifest.toml" \
  --output "$GUIDES_OUTPUT" \
  --guide-catalog "$GUIDE_CATALOG"

echo ""
echo "=== Drop Report ==="
if [[ -x "$PYTHON" ]]; then
  "$PYTHON" - "$EVOFIT_OUTPUT/summary.json" "$GUIDE_CATALOG" <<'PY'
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
catalog_path = Path(sys.argv[2])
summary = json.loads(summary_path.read_text(encoding="utf-8"))
fit_sources = summary.get("fit_sources", [])
dropped = [item for item in fit_sources if not bool(item.get("structurally_convertible", True))]

print(f"guide catalog: {catalog_path}")
print(f"fit sources: {len(fit_sources)}")
print(f"converted guides: {summary.get('converted_guide_count', 0)}")
if not dropped:
    print("all reviewed symbols were structurally convertible")
    raise SystemExit(0)

print("dropped symbols:")
for item in dropped:
    reasons = item.get("validation_errors") or ["no validation error recorded"]
    print(f"  - {item.get('symbol', '?')}: " + "; ".join(str(reason) for reason in reasons))
PY
else
  uv run python3 - "$EVOFIT_OUTPUT/summary.json" "$GUIDE_CATALOG" <<'PY'
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
catalog_path = Path(sys.argv[2])
summary = json.loads(summary_path.read_text(encoding="utf-8"))
fit_sources = summary.get("fit_sources", [])
dropped = [item for item in fit_sources if not bool(item.get("structurally_convertible", True))]

print(f"guide catalog: {catalog_path}")
print(f"fit sources: {len(fit_sources)}")
print(f"converted guides: {summary.get('converted_guide_count', 0)}")
if not dropped:
    print("all reviewed symbols were structurally convertible")
    raise SystemExit(0)

print("dropped symbols:")
for item in dropped:
    reasons = item.get("validation_errors") or ["no validation error recorded"]
    print(f"  - {item.get('symbol', '?')}: " + "; ".join(str(reason) for reason in reasons))
PY
fi
