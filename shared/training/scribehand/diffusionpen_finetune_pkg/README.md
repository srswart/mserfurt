# DiffusionPen fine-tune on Nebius AI Cloud

This runs the **real** step-4 generator fine-tune on the Cgm 628 line dataset —
the step that was skipped locally (the current checkpoints are IAM bootstrap,
`epochs: 0`). It must run on a **raw CUDA GPU VM** (Nebius **AI Cloud**, *not*
Token Factory, which is inference/LLM-only and cannot run this).

The training script (`train_diffusionpen_finetune.py`) is verified end-to-end on
MPS locally (dataset → VAE encode → style encoder → Canine text → UNet
forward/backward → checkpoint save). Only real training remains, which needs the
GPU.

---

## 1. Provision a GPU VM (Nebius AI Cloud)

- One GPU is enough: **H100 80GB** (fastest) or **L40S 48GB** (cheaper).
- Ubuntu 22.04 image with recent NVIDIA driver + CUDA. Confirm with `nvidia-smi`.
- ~30 GB disk is plenty.

## 2. Upload the four inputs

From your Mac (replace `USER@VM`):

```bash
# a) the training script
scp scripts/scribehand/train_diffusionpen_finetune.py USER@VM:~/

# b) the line dataset (~few MB)
rsync -avz shared/training/scribehand/lines_v1 USER@VM:~/

# c) the DiffusionPen repo CODE + pretrained weights
#    (code for imports: unet.py, feature_extractor.py, utils/;
#     weights: ckpt/diffusionpen_bastarda_v1/{models/ckpt.pt,style_models/style_encoder.pth})
rsync -avz --exclude '.git' ~/Projects/DiffusionPen USER@VM:~/

# d) this package (requirements + run script)
rsync -avz shared/training/scribehand/diffusionpen_finetune_pkg USER@VM:~/
```

## 3. Set up the environment on the VM

```bash
python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip

# torch matched to the box CUDA (check nvidia-smi). Example for CUDA 12.1:
pip install torch==2.12.1 torchvision==0.27.1 --index-url https://download.pytorch.org/whl/cu121

pip install -r diffusionpen_finetune_pkg/requirements.txt
```

**Hugging Face assets** (downloaded on first run):
- `google/canine-c` (text encoder) — public.
- `stable-diffusion-v1-5/stable-diffusion-v1-5` (VAE + scheduler) — if it prompts
  for auth, run `huggingface-cli login` with a token, or set
  `--stable-dif-path` to a local/alternate SD-1.5 path.

## 4. Run the fine-tune

```bash
cd ~
# quick sanity check first (3 steps, ~1 min):
python train_diffusionpen_finetune.py \
  --diffusionpen-root ~/DiffusionPen --data ~/lines_v1 \
  --checkpoint ~/DiffusionPen/ckpt/diffusionpen_bastarda_v1/models/ckpt.pt \
  --out ~/dp_smoke --device cuda --smoke

# then the real run (logs progress + ETA; saves every 10 epochs):
nohup bash diffusionpen_finetune_pkg/run_finetune.sh > finetune.log 2>&1 &
tail -f finetune.log
```

Expected progress lines:

```
[dp-finetune HH:MM:SS] epoch 12/150 step 756/9450 loss=0.043 3.10 it/s eta=47m
```

**Rough runtime** (251 lines, batch 4, 150 epochs, ~63 steps/epoch ≈ 9,450 steps):
- H100: ~30–50 min
- L40S: ~1–1.5 h

Tune `EPOCHS`, `BATCH_SIZE`, `IMG_WIDTH` via env vars (see `run_finetune.sh`).
With only 251 lines, watch for over-fitting; 100–200 epochs is a reasonable band.

## 5. Bring the checkpoint back

The output dir is self-contained for the inference runner:

```
diffusionpen_cgm628_v1/
  models/ckpt.pt
  style_models/style_encoder.pth
  training_report.json
```

```bash
rsync -avz USER@VM:~/diffusionpen_cgm628_v1 \
  shared/models/scribehand/weights/
```

## 6. Back on the Mac — re-render with the fine-tuned hand

Point the DiffusionPen backend at the new checkpoint and re-render f01r:

```bash
# in shared/models/scribehand/backends.toml, set:
#   [backends.diffusionpen] checkpoint = ".../weights/diffusionpen_cgm628_v1"

uv run scribesim render f01r --approach neural \
  --neural-backend diffusionpen \
  --neural-htr shared/models/scribehand/weights/htr_trocr_v1 \
  --neural-allow-unverified \
  --neural-diag-dir diagnostics/dp_cgm628_f01r \
  --output-dir diagnostics/dp_cgm628_f01r
```

Compare `diagnostics/dp_cgm628_f01r/f01r.png` against the current IAM-bootstrap
`diagnostics/diffusionpen_f01r/f01r.png` — this is where you should finally see a
bastarda-styled hand instead of generic English cursive.

---

## Notes / knobs

- **Data is thin (251 lines).** Expect a clear jump from "English hand" to
  "recognizably bastarda", but for *great* quality, harvest more Cgm 628 folios
  (same flow: `transcribe_lines.py` → review → `build_line_dataset.py`) and
  re-run.
- The UNet is size-agnostic (no spatial position embeddings), so `IMG_WIDTH` can
  be raised (e.g. 1536) if long lines look compressed; costs more memory.
- Training uses the style-conditioned path, so the 339-writer `label_emb` is
  bypassed — no writer-count surgery needed.
