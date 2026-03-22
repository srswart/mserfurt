#!/usr/bin/env python3
"""
Transcribe manuscript word crops using Claude vision (Batches API).

Sends all word crop PNGs to claude-opus-4-6 in a single batch (50% cost),
polls until complete, then writes a transcription.txt with one word per line
in the same alphabetical order that `extract-letters --transcription` expects.

Usage:
    uv run python transcribe_words.py
    uv run python transcribe_words.py --words-dir reference/fullres_words --output reference/transcription.txt
"""

import argparse
import base64
import re
import time
from pathlib import Path

import anthropic

_REASONING_MARKERS = ("let me", "looking", "appears", "hmm", "wait", "careful", "i see", "i think")


def _clean_transcription(raw: str) -> str:
    """Extract the first clean word from a potentially noisy model response."""
    # Take only the first non-empty line to strip embedded reasoning
    first_line = next((l.strip() for l in raw.splitlines() if l.strip()), "?")
    # Keep only lowercase alpha + space
    cleaned = re.sub(r"[^a-z ]", "", first_line.lower()).strip()
    # Reject if it looks like reasoning leaked through
    if len(cleaned) > 20 or any(m in cleaned for m in _REASONING_MARKERS):
        return "?"
    return cleaned or "?"
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

SYSTEM_PROMPT = """\
You are transcribing 15th-century German Bastarda manuscript text (MS Erfurt, ca. 1457).

Rules:
- Output ONLY the transcribed word(s), lowercase Latin alphabet, nothing else
- Expand standard medieval abbreviations when confident (macron over vowel → omitted nasal n/m)
- Use ? for any character you cannot identify with confidence
- If the image is completely illegible, output a single ?
- Do not add punctuation, explanation, or commentary
"""


def encode_image(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode()


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe word crops via Claude vision batch")
    parser.add_argument("--words-dir", default="reference/fullres_words",
                        help="Directory of word crop PNGs (default: reference/fullres_words)")
    parser.add_argument("--output", default="reference/transcription.txt",
                        help="Output transcription file (default: reference/transcription.txt)")
    parser.add_argument("--poll-interval", type=int, default=15,
                        help="Seconds between batch status polls (default: 15)")
    args = parser.parse_args()

    words_dir = Path(args.words_dir)
    output_path = Path(args.output)

    crops = sorted(words_dir.glob("*.png"))
    if not crops:
        print(f"No PNG files found in {words_dir}")
        return

    print(f"Found {len(crops)} word crops in {words_dir}")

    client = anthropic.Anthropic()

    # Build one batch request per crop
    requests: list[Request] = []
    for crop in crops:
        img_data = encode_image(crop)
        requests.append(Request(
            custom_id=crop.stem,
            params=MessageCreateParamsNonStreaming(
                model="claude-opus-4-6",
                max_tokens=32,  # word transcription is short
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_data,
                            },
                        },
                        {"type": "text", "text": "Transcribe:"},
                    ],
                }],
            ),
        ))

    print(f"Submitting batch of {len(requests)} requests to claude-opus-4-6…")
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch ID : {batch.id}")
    print(f"Status   : {batch.processing_status}")

    # Poll until done
    while True:
        batch = client.messages.batches.retrieve(batch.id)
        c = batch.request_counts
        print(f"  [{batch.processing_status}] processing={c.processing}  "
              f"succeeded={c.succeeded}  errored={c.errored}")
        if batch.processing_status == "ended":
            break
        time.sleep(args.poll_interval)

    print(f"\nBatch complete — succeeded: {batch.request_counts.succeeded}/{len(requests)}")

    # Collect results keyed by custom_id (= crop stem)
    results: dict[str, str] = {}
    for result in client.messages.batches.results(batch.id):
        if result.result.type == "succeeded":
            raw = next(
                (b.text for b in result.result.message.content if b.type == "text"), "?"
            ).strip()
            results[result.custom_id] = _clean_transcription(raw)
        else:
            results[result.custom_id] = "?"

    # Write in the same alphabetical order that extract-letters will see
    lines = [results.get(crop.stem, "?") for crop in crops]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n")

    print(f"Transcription written → {output_path}")
    print("\nSample (first 15):")
    for crop, word in zip(crops[:15], lines[:15]):
        print(f"  {crop.name:<35}  {word}")


if __name__ == "__main__":
    main()
