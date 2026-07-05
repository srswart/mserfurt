#!/usr/bin/env python
"""Transcribe whole line strips (not words) for line-level generator training.

Lines are readable where single-minim word crops were not, so this yields far
cleaner labels than re-joining the word review. Emits regular progress lines so
multi-minute/hour runs are observable.

Usage:
    set -a && source .env && set +a
    uv run python scripts/scribehand/transcribe_lines.py \\
        --lines work/cgm628_anchor/lines \\
        --output work/cgm628_anchor/line_transcription.tsv \\
        --chunk-size 200
"""

from __future__ import annotations

import argparse
import base64
import time
from pathlib import Path


_SYSTEM_PROMPT = """\
You are transcribing ONE line from a 15th-century German Bastarda manuscript \
(MS Erfurt, BSB Cgm 628, ca. 1457).

Rules:
- Output ONLY the transcribed text of this single line, lowercase Latin alphabet.
- Preserve word spacing using single spaces between words.
- Expand standard medieval abbreviations when confident (macron over a vowel = \
omitted nasal n/m; per/pro/prae marks; etc.).
- Use ? for an individual character you cannot read.
- If the whole strip is illegible, blank, a ruling line, header, or marginalia, \
output a single ? on its own.
- No punctuation you do not see, no explanation, no commentary.
"""


def _encode(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode()


def _log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[transcribe-lines {ts}] {msg}", flush=True)


def _collect_strips(lines_root: Path) -> list[Path]:
    strips = sorted(
        lines_root.glob("*/line_*.png"),
        key=lambda p: (p.parent.name, int(p.stem.split("_")[1])),
    )
    return strips


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True, type=Path,
                    help="Root dir with <page>/line_XXXX.png strips")
    ap.add_argument("--output", required=True, type=Path,
                    help="Output TSV: page<TAB>line<TAB>relpath<TAB>text")
    ap.add_argument("--chunk-size", type=int, default=200)
    ap.add_argument("--model", default="claude-opus-4-6")
    ap.add_argument("--poll-interval", type=int, default=15)
    ap.add_argument("--skip-existing", action="store_true",
                    help="If --output exists, skip page/line pairs already transcribed")
    args = ap.parse_args()

    import anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    strips = _collect_strips(args.lines)
    if not strips:
        raise SystemExit(f"No line strips found under {args.lines}")

    existing_rows: dict[tuple[str, int], str] = {}
    if args.skip_existing and args.output.is_file():
        for line in args.output.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            if len(parts) >= 4:
                existing_rows[(parts[0], int(parts[1]))] = line
        before = len(strips)
        strips = [
            p for p in strips
            if (p.parent.name, int(p.stem.split("_")[1])) not in existing_rows
        ]
        _log(f"skip-existing: {before - len(strips)} already in {args.output}, "
             f"{len(strips)} remaining")

    if not strips:
        _log("nothing new to transcribe")
        return

    _log(f"found {len(strips)} line strips under {args.lines}")

    client = anthropic.Anthropic()
    results: dict[str, str] = {}
    started = time.monotonic()

    total_chunks = (len(strips) + args.chunk_size - 1) // args.chunk_size
    for ci in range(0, len(strips), args.chunk_size):
        chunk = strips[ci : ci + args.chunk_size]
        cn = ci // args.chunk_size + 1
        _log(f"chunk {cn}/{total_chunks}: encoding {len(chunk)} strips…")
        requests = []
        for p in chunk:
            cid = f"{p.parent.name}_{p.stem}"
            requests.append(Request(
                custom_id=cid,
                params=MessageCreateParamsNonStreaming(
                    model=args.model,
                    max_tokens=256,
                    system=_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": [
                        {"type": "image", "source": {
                            "type": "base64", "media_type": "image/png",
                            "data": _encode(p)}},
                        {"type": "text", "text": "Transcribe this line:"},
                    ]}],
                ),
            ))
        batch = client.messages.batches.create(requests=requests)
        _log(f"chunk {cn}/{total_chunks}: submitted batch {batch.id}")

        while True:
            b = client.messages.batches.retrieve(batch.id)
            c = b.request_counts
            elapsed = (time.monotonic() - started) / 60
            _log(f"  chunk {cn}/{total_chunks} [{b.processing_status}] "
                 f"done={c.succeeded} err={c.errored} pending={c.processing} "
                 f"| elapsed {elapsed:.1f}m")
            if b.processing_status == "ended":
                break
            time.sleep(args.poll_interval)

        for r in client.messages.batches.results(batch.id):
            if r.result.type == "succeeded":
                raw = next((blk.text for blk in r.result.message.content
                            if blk.type == "text"), "?").strip()
                results[r.custom_id] = " ".join(raw.split())
            else:
                results[r.custom_id] = "?"
        known = sum(1 for v in results.values() if v and v != "?")
        _log(f"chunk {cn}/{total_chunks} done — cumulative known {known}/{len(results)}")

    new_rows: list[str] = []
    for p in strips:
        cid = f"{p.parent.name}_{p.stem}"
        text = results.get(cid, "?")
        rel = p.relative_to(args.lines)
        new_rows.append(f"{p.parent.name}\t{int(p.stem.split('_')[1])}\t{rel}\t{text}")

    merged: dict[tuple[str, int], str] = dict(existing_rows)
    for row in new_rows:
        parts = row.split("\t")
        merged[(parts[0], int(parts[1]))] = row

    all_rows = sorted(merged.values(), key=lambda r: (r.split("\t")[0], int(r.split("\t")[1])))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(all_rows) + "\n", encoding="utf-8")

    known = sum(1 for r in all_rows if not r.endswith("\t?"))
    total_min = (time.monotonic() - started) / 60
    _log(f"wrote {args.output} — {known}/{len(all_rows)} lines with text "
         f"({100 * known // max(len(all_rows), 1)}%) in {total_min:.1f}m "
         f"(+{len(new_rows)} new this run)")


if __name__ == "__main__":
    main()
