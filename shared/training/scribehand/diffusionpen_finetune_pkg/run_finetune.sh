#!/usr/bin/env bash
# Launch the DiffusionPen fine-tune on a CUDA GPU VM.
# Edit the paths below to match where you uploaded things, then:
#   bash run_finetune.sh
# For a long unattended run:
#   nohup bash run_finetune.sh > finetune.log 2>&1 &  ;  tail -f finetune.log
set -euo pipefail

# --- paths (edit these) ------------------------------------------------------
DIFFUSIONPEN_ROOT="${DIFFUSIONPEN_ROOT:-$HOME/DiffusionPen}"
DATA="${DATA:-$HOME/lines_v3}"
CHECKPOINT="${CHECKPOINT:-$DIFFUSIONPEN_ROOT/ckpt/diffusionpen_bastarda_v1/models/ckpt.pt}"
OUT="${OUT:-$HOME/diffusionpen_cgm628_v3}"
TRAIN_SCRIPT="${TRAIN_SCRIPT:-$HOME/train_diffusionpen_finetune.py}"

# --- hyperparameters (~2.2k lines on one H100/L40S) ---------------------------
# IMG_WIDTH 2048: lines are height-normalized to 64px (full canvas height,
# no letterbox) — median Cgm 628 line is ~2170px wide at that scale.
EPOCHS="${EPOCHS:-80}"
BATCH_SIZE="${BATCH_SIZE:-4}"
IMG_WIDTH="${IMG_WIDTH:-2048}"
LR="${LR:-1e-5}"
SAVE_EVERY="${SAVE_EVERY:-10}"
LOG_EVERY="${LOG_EVERY:-20}"

echo "== GPU =="; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

python "$TRAIN_SCRIPT" \
  --diffusionpen-root "$DIFFUSIONPEN_ROOT" \
  --data "$DATA" \
  --checkpoint "$CHECKPOINT" \
  --out "$OUT" \
  --epochs "$EPOCHS" \
  --batch-size "$BATCH_SIZE" \
  --img-width "$IMG_WIDTH" \
  --lr "$LR" \
  --save-every "$SAVE_EVERY" \
  --log-every "$LOG_EVERY" \
  --device cuda

echo "== done =="
echo "checkpoint: $OUT/models/ckpt.pt"
echo "report:     $OUT/training_report.json"
