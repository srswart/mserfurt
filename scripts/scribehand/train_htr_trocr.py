#!/usr/bin/env python
"""Fine-tune a TrOCR word/line reader on the generic corpus export (TD-018).

The resulting checkpoint powers the HTR fidelity gate
(`--neural-htr <checkpoint>` / `TrOCRScorer`). Runs on MPS or CUDA.

Usage:
    python scripts/scribehand/train_htr_trocr.py \
        --data shared/training/scribehand/exports/generic_v1 \
        --out  shared/models/scribehand/weights/htr_trocr_v1 \
        --base microsoft/trocr-base-handwritten \
        --epochs 8
"""

from __future__ import annotations

import argparse
from pathlib import Path


def load_rows(data_dir: Path) -> list[dict]:
    rows = []
    for raw in (data_dir / "labels.tsv").read_text().strip().splitlines():
        sid, image, text, writer, split = raw.split("\t")
        rows.append({"id": sid, "image": str(data_dir / image),
                     "text": text, "writer": writer, "split": split})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="generic corpus export dir")
    ap.add_argument("--out", required=True, help="output checkpoint dir")
    ap.add_argument("--base", default="microsoft/trocr-base-handwritten")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--max-target-len", type=int, default=64)
    ap.add_argument("--num-workers", type=int, default=0,
                    help="DataLoader workers (use 0 on macOS spawn)")
    args = ap.parse_args()

    import torch
    from PIL import Image
    from torch.utils.data import DataLoader, Dataset
    from transformers import (
        TrOCRProcessor,
        VisionEncoderDecoderModel,
        get_linear_schedule_with_warmup,
    )

    device = ("mps" if torch.backends.mps.is_available()
              else ("cuda" if torch.cuda.is_available() else "cpu"))
    print(f"[train-htr] device={device} base={args.base}")

    processor = TrOCRProcessor.from_pretrained(args.base)
    model = VisionEncoderDecoderModel.from_pretrained(args.base).to(device)
    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id or \
        processor.tokenizer.bos_token_id
    model.config.pad_token_id = processor.tokenizer.pad_token_id

    rows = load_rows(Path(args.data))
    train_rows = [r for r in rows if r["split"] == "train"]
    val_rows = [r for r in rows if r["split"] == "val"] or rows[: max(1, len(rows) // 20)]
    print(f"[train-htr] train={len(train_rows)} val={len(val_rows)}")

    class WordDataset(Dataset):
        def __init__(self, items): self.items = items
        def __len__(self): return len(self.items)
        def __getitem__(self, i):
            r = self.items[i]
            image = Image.open(r["image"]).convert("RGB")
            pixel_values = processor(images=image, return_tensors="pt").pixel_values[0]
            labels = processor.tokenizer(
                r["text"], max_length=args.max_target_len,
                padding="max_length", truncation=True, return_tensors="pt",
            ).input_ids[0]
            labels[labels == processor.tokenizer.pad_token_id] = -100
            return {"pixel_values": pixel_values, "labels": labels}

    train_dl = DataLoader(WordDataset(train_rows), batch_size=args.batch_size,
                          shuffle=True, num_workers=args.num_workers)
    val_dl = DataLoader(WordDataset(val_rows), batch_size=args.batch_size,
                        num_workers=args.num_workers)

    optim = torch.optim.AdamW(model.parameters(), lr=args.lr)
    steps = args.epochs * max(1, len(train_dl))
    sched = get_linear_schedule_with_warmup(optim, int(steps * 0.05), steps)

    def evaluate() -> float:
        from scribesim.scribehand.htr import cer
        model.eval()
        total, n = 0.0, 0
        with torch.no_grad():
            for batch in val_dl:
                pv = batch["pixel_values"].to(device)
                generated = model.generate(pv, max_new_tokens=args.max_target_len)
                texts = processor.batch_decode(generated, skip_special_tokens=True)
                labels = batch["labels"].clone()
                labels[labels == -100] = processor.tokenizer.pad_token_id
                refs = processor.batch_decode(labels, skip_special_tokens=True)
                for ref, hyp in zip(refs, texts):
                    total += cer(ref.strip(), hyp.strip()); n += 1
        model.train()
        return total / max(1, n)

    best = float("inf")
    out = Path(args.out)
    model.train()
    for epoch in range(args.epochs):
        running = 0.0
        for step, batch in enumerate(train_dl):
            optim.zero_grad()
            outputs = model(pixel_values=batch["pixel_values"].to(device),
                            labels=batch["labels"].to(device))
            outputs.loss.backward()
            optim.step(); sched.step()
            running += float(outputs.loss)
            if step % 50 == 0:
                print(f"[train-htr] epoch={epoch} step={step} "
                      f"loss={running / (step + 1):.4f}")
        val_cer = evaluate()
        print(f"[train-htr] epoch={epoch} val_cer={val_cer:.4f}")
        if val_cer < best:
            best = val_cer
            out.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(out)
            processor.save_pretrained(out)
            (out / "training_report.json").write_text(
                __import__("json").dumps({
                    "base": args.base, "epochs_completed": epoch + 1,
                    "best_val_cer": best, "train_rows": len(train_rows),
                }, indent=1))
            print(f"[train-htr] saved best → {out}")

    print(f"[train-htr] done — best val CER {best:.4f}")
    print("Calibrate the gate threshold: real held-out anchor words must pass "
          "(see docs/scribehand-mac-runbook.md §5).")


if __name__ == "__main__":
    main()
