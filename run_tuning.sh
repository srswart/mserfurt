#!/usr/bin/env bash
# run_tuning.sh — run live parameter fitting with visual output per trial
#
# Renders a few lines per trial, compares against a manuscript sample,
# saves every iteration's output so you can watch convergence.
#
# Usage:
#   ./run_tuning.sh                                  # defaults: nib stage, 10 trials, Kaiserurkunde
#   ./run_tuning.sh --stages nib,coarse              # multiple stages
#   ./run_tuning.sh --trials 20                      # more trials
#   ./run_tuning.sh --lines 5                        # fewer lines (faster)
#   ./run_tuning.sh --target docs/samples/33125_werbeschreiben.jpg
#   ./run_tuning.sh --all-stages                     # run all 4 stages

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$REPO_DIR/.venv/bin/python"

STAGES="nib"
TRIALS=10
LINES=8
TARGET="$REPO_DIR/docs/samples/3365_StadtASG_Kaiserurkunde.jpg"
FOLIO_JSON="$REPO_DIR/output-live/f01r.json"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_DIR="$REPO_DIR/snapshots/tuning_${TIMESTAMP}"
DESKTOP_DIR="$HOME/Desktop/scribesim/tuning_${TIMESTAMP}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stages)      STAGES="$2"; shift 2 ;;
    --all-stages)  STAGES="coarse,nib,rhythm,ink"; shift ;;
    --trials)      TRIALS="$2"; shift 2 ;;
    --lines)       LINES="$2"; shift 2 ;;
    --target)      TARGET="$2"; shift 2 ;;
    --folio)       FOLIO_JSON="$REPO_DIR/output-live/$2.json"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

echo "=== ScribeSim Live Tuning ==="
echo "  stages  : $STAGES"
echo "  trials  : $TRIALS per stage"
echo "  lines   : $LINES (quick render)"
echo "  target  : $(basename "$TARGET")"
echo "  output  : $OUTPUT_DIR"
echo ""

mkdir -p "$OUTPUT_DIR" "$DESKTOP_DIR"

# Copy target for reference
cp "$TARGET" "$OUTPUT_DIR/target.jpg"
cp "$TARGET" "$DESKTOP_DIR/target.jpg"

# Run the fitting loop
"$PYTHON" -c "
from scribesim.tuning.fitting_loop import run_live_fitting
from pathlib import Path

trials = run_live_fitting(
    folio_json_path=Path('$FOLIO_JSON'),
    target_path=Path('$TARGET'),
    output_dir=Path('$OUTPUT_DIR'),
    stages='$STAGES'.split(','),
    max_iterations=$TRIALS,
    max_lines=$LINES,
)
"

# Copy results to desktop
echo ""
echo "=== Copying to Desktop ==="
cp -r "$OUTPUT_DIR"/* "$DESKTOP_DIR/"

# Create an index HTML for easy browsing
"$PYTHON" -c "
import json
from pathlib import Path

output_dir = Path('$OUTPUT_DIR')
log = json.loads((output_dir / 'fitting_log.json').read_text())

html = ['<html><head><style>']
html.append('body { font-family: sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; }')
html.append('.trial { display: inline-block; margin: 10px; text-align: center; }')
html.append('.trial img { width: 300px; border: 1px solid #ccc; }')
html.append('.score { font-weight: bold; }')
html.append('.good { color: green; } .okay { color: orange; } .bad { color: red; }')
html.append('</style></head><body>')
html.append('<h1>ScribeSim Tuning — Trial Gallery</h1>')
html.append(f'<p>Target: <img src=\"target.jpg\" style=\"width:400px\"></p>')

for t in log:
    rpath = Path(t['render_path']).name
    trial_dir = Path(t['render_path']).parent.name
    score = t['distance']
    cls = 'good' if score < 0.3 else 'okay' if score < 0.6 else 'bad'
    html.append(f'<div class=\"trial\">')
    html.append(f'<img src=\"{trial_dir}/{rpath}\">')
    html.append(f'<br>Trial {t[\"trial\"]} ({t[\"stage\"]})')
    html.append(f'<br><span class=\"score {cls}\">{score:.3f}</span>')
    html.append(f'</div>')

html.append('</body></html>')
(output_dir / 'gallery.html').write_text('\n'.join(html))
print('  gallery → gallery.html')
"

cp "$OUTPUT_DIR/gallery.html" "$DESKTOP_DIR/gallery.html"

echo ""
echo "=== Done ==="
echo "  Local:   $OUTPUT_DIR"
echo "  Desktop: $DESKTOP_DIR"
echo "  Open gallery.html in browser to compare all trials"
echo ""
echo "  Trial renders:"
ls -d "$OUTPUT_DIR"/trial_*/ 2>/dev/null | while read -r d; do
  echo "    $(basename "$d")"
done
