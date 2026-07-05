#!/usr/bin/env python
"""Run transcribe-words in chunks (avoids huge single-batch payloads).

Usage:
    set -a && source .env && set +a
    uv run python scripts/scribehand/transcribe_words_chunked.py \\
        --words work/cgm628_anchor/words \\
        --output work/cgm628_anchor/transcription.txt \\
        --chunk-size 400 --retry-unknowns
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--chunk-size", type=int, default=400)
    ap.add_argument("--model", default="claude-opus-4-6")
    ap.add_argument("--retry-unknowns", action="store_true")
    ap.add_argument("--poll-interval", type=int, default=15)
    args = ap.parse_args()

    import anthropic
    from scribesim.transcribe.batch import (
        build_requests,
        collect_results,
        retry_unknowns,
    )

    crops = sorted(args.words.glob("*.png"))
    if not crops:
        raise SystemExit(f"No PNG files in {args.words}")

    client = anthropic.Anthropic()
    all_results: dict[str, str] = {}

    for i in range(0, len(crops), args.chunk_size):
        chunk = crops[i : i + args.chunk_size]
        n = i // args.chunk_size + 1
        total = (len(crops) + args.chunk_size - 1) // args.chunk_size
        print(f"[chunk {n}/{total}] submitting {len(chunk)} crops…")
        batch = client.messages.batches.create(
            requests=build_requests(chunk, [], model=args.model)
        )
        print(f"  batch id: {batch.id}")
        all_results.update(
            collect_results(
                batch.id, chunk, client, poll_interval=args.poll_interval
            )
        )

    if args.retry_unknowns:
        unknowns = {
            stem: args.words / f"{stem}.png"
            for stem, val in all_results.items()
            if val == "?"
        }
        if unknowns:
            print(f"[retry] {len(unknowns)} unknowns")
            all_results = retry_unknowns(
                unknowns=unknowns,
                initial_results=all_results,
                client=client,
                model=args.model,
                poll_interval=args.poll_interval,
            )

    lines = [all_results.get(c.stem, "?") for c in crops]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n")

    known = sum(1 for w in lines if w != "?")
    print(f"Wrote {args.output} — known {known}/{len(lines)} ({100 * known // len(lines)}%)")


if __name__ == "__main__":
    main()
