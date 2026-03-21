#!/usr/bin/env bash
# run_evolution.sh — run the evolutionary scribe with configurable parameters
#
# Usage:
#   ./run_evolution.sh                              # defaults: 3 lines, 100 gen, pop 40
#   ./run_evolution.sh --generations 200            # more generations
#   ./run_evolution.sh --lines 5                    # more lines
#   ./run_evolution.sh --target docs/samples/v2_bsb00052961_00005_full_full_0_default.jpg

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GENERATIONS=100
POP_SIZE=40
LINES=5
DPI=300
TARGET=""
OUTPUT="$REPO_DIR/snapshots/evolved_output.png"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --generations) GENERATIONS="$2"; shift 2 ;;
    --pop-size)    POP_SIZE="$2"; shift 2 ;;
    --lines)       LINES="$2"; shift 2 ;;
    --dpi)         DPI="$2"; shift 2 ;;
    --target)      TARGET="$2"; shift 2 ;;
    --output)      OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown: $1" >&2; exit 1 ;;
  esac
done

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT="$REPO_DIR/snapshots/evolved_${TIMESTAMP}.png"

echo "=== Evolutionary Scribe ==="
echo "  generations : $GENERATIONS"
echo "  pop_size    : $POP_SIZE"
echo "  lines       : $LINES"
echo "  dpi         : $DPI"
echo "  output      : $OUTPUT"
echo ""

export PYTHONPATH="$REPO_DIR:$REPO_DIR/.venv/lib/python3.13/site-packages"

python3 -c "
import time, shutil
from pathlib import Path
import numpy as np
from PIL import Image

from scribesim.evo.compose import evolve_line, FolioState, EvolvedFolio, render_folio
from scribesim.evo.engine import EvolutionConfig

# Sample lines from MS Erfurt text
sample_lines = [
    'Hie hebt sich an das ein schreiber mit mir',
    'la an zu schreiben in dem drey und viertzigsten',
    'jar eines babest anno Domini MCCCC LVII',
    'in der stat Erfurdt eine bredite',
    'ist eine excusatione',
    'Der strom des glaubens ist nicht mein eigen',
    'Das wil ich eegen zuerst vor allen andern',
    'was alles das hernach volget damal hengest',
]

lines_to_evolve = sample_lines[:$LINES]

config = EvolutionConfig(
    pop_size=$POP_SIZE,
    generations=$GENERATIONS,
    eval_dpi=72.0,
    early_stop_fitness=0.92,
)

state = FolioState(
    page_width_mm=70.0,
    page_height_mm=10.0 + len(lines_to_evolve) * 9.5,
)

t0 = time.time()
evolved_lines = []
for i, text in enumerate(lines_to_evolve):
    print(f'--- Line {i+1}/{len(lines_to_evolve)}: \"{text[:40]}...\" ---')
    line = evolve_line(text, i, state, config=config, verbose=True)
    evolved_lines.append(line)

elapsed = time.time() - t0
print(f'\\nTotal evolution time: {elapsed:.1f}s ({elapsed/len(lines_to_evolve):.1f}s/line)')

folio = EvolvedFolio(
    folio_id='evolved',
    lines=evolved_lines,
    page_width_mm=state.page_width_mm,
    page_height_mm=state.page_height_mm,
)

print(f'Rendering at $DPI DPI...')
arr = render_folio(folio, dpi=$DPI)

out = Path('$OUTPUT')
out.parent.mkdir(parents=True, exist_ok=True)
Image.fromarray(arr).save(str(out), dpi=($DPI, $DPI))

desktop = Path.home() / 'Desktop' / 'scribesim'
desktop.mkdir(parents=True, exist_ok=True)
shutil.copy(str(out), str(desktop / out.name))

print(f'Saved: {out} ({arr.shape[1]}x{arr.shape[0]}px)')
print(f'Copied to Desktop')
"

echo ""
echo "=== Done ==="
echo "  Output: $OUTPUT"
echo "  Desktop: ~/Desktop/scribesim/$(basename $OUTPUT)"
