#!/usr/bin/env python
"""Local browser UI to review anchor word crops alongside transcriptions.

Keeps image and label aligned by index; edits write back to transcription.txt.

Usage:
    uv run python scripts/scribehand/review_transcriptions.py \\
        --dir work/cgm628_anchor

    # or explicit paths:
    uv run python scripts/scribehand/review_transcriptions.py \\
        --words work/cgm628_anchor/words \\
        --transcription work/cgm628_anchor/transcription.txt
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


_FILENAME_RE = re.compile(
    r"^(?P<page>\d{4})_line(?P<line>\d{4})_word(?P<word>\d{3})\.png$"
)


def _parse_name(stem: str) -> dict[str, int | str]:
    match = _FILENAME_RE.match(f"{stem}.png")
    if not match:
        return {"page": stem, "line": 0, "word": 0}
    return {
        "page": match.group("page"),
        "line": int(match.group("line")),
        "word": int(match.group("word")),
    }


class TranscriptionReviewSession:
    def __init__(
        self,
        words_dir: Path,
        transcription_path: Path,
        word_list_path: Path | None = None,
    ) -> None:
        self.words_dir = words_dir.resolve()
        self.transcription_path = transcription_path.resolve()
        self._lock = threading.Lock()

        if word_list_path and word_list_path.exists():
            names = [
                line.strip()
                for line in word_list_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            names = sorted(p.name for p in self.words_dir.glob("*.png"))

        lines = self.transcription_path.read_text(encoding="utf-8").splitlines()
        if len(lines) < len(names):
            lines.extend(["?"] * (len(names) - len(lines)))
        elif len(lines) > len(names):
            lines = lines[: len(names)]

        self.filenames = names
        self.lines = lines

    def stats(self) -> dict[str, int | str]:
        unknown = sum(1 for text in self.lines if text.strip() == "?")
        soft = sum(1 for text in self.lines if text.strip().startswith("~"))
        return {
            "total": len(self.lines),
            "unknown": unknown,
            "soft": soft,
            "known": len(self.lines) - unknown,
            "transcription_path": str(self.transcription_path),
            "words_dir": str(self.words_dir),
        }

    def entries_payload(self) -> dict:
        entries = []
        for index, (name, text) in enumerate(zip(self.filenames, self.lines, strict=True)):
            meta = _parse_name(Path(name).stem)
            entries.append(
                {
                    "index": index,
                    "file": name,
                    "page": meta["page"],
                    "line": meta["line"],
                    "word": meta["word"],
                    "text": text,
                }
            )
        pages = sorted({str(e["page"]) for e in entries})
        return {"entries": entries, "pages": pages, "stats": self.stats()}

    def get_entry(self, index: int) -> dict | None:
        if index < 0 or index >= len(self.filenames):
            return None
        meta = _parse_name(Path(self.filenames[index]).stem)
        return {
            "index": index,
            "file": self.filenames[index],
            "page": meta["page"],
            "line": meta["line"],
            "word": meta["word"],
            "text": self.lines[index],
        }

    def update_entry(self, index: int, text: str) -> dict:
        with self._lock:
            if index < 0 or index >= len(self.lines):
                raise IndexError(index)
            self.lines[index] = text.strip()
            self._write_transcription()
        entry = self.get_entry(index)
        assert entry is not None
        return entry

    def image_path_for(self, index: int) -> Path | None:
        if index < 0 or index >= len(self.filenames):
            return None
        return self.words_dir / self.filenames[index]

    def _write_transcription(self) -> None:
        content = "\n".join(self.lines)
        if content:
            content += "\n"
        tmp = self.transcription_path.with_suffix(".txt.tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(self.transcription_path)


class LineReviewSession:
    """Review whole-line strips against a TSV: page<TAB>line<TAB>relpath<TAB>text."""

    def __init__(self, tsv_path: Path, images_root: Path) -> None:
        self.tsv_path = tsv_path.resolve()
        self.images_root = images_root.resolve()
        self._lock = threading.Lock()
        self.rows: list[dict] = []
        for raw in self.tsv_path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            parts = raw.split("\t")
            page = parts[0] if len(parts) > 0 else ""
            line = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            relpath = parts[2] if len(parts) > 2 else ""
            text = parts[3] if len(parts) > 3 else "?"
            self.rows.append({"page": page, "line": line, "relpath": relpath, "text": text})

    def stats(self) -> dict:
        unknown = sum(1 for r in self.rows if r["text"].strip() == "?")
        soft = sum(1 for r in self.rows if r["text"].strip().startswith("~"))
        return {
            "total": len(self.rows),
            "unknown": unknown,
            "soft": soft,
            "known": len(self.rows) - unknown,
            "transcription_path": str(self.tsv_path),
            "words_dir": str(self.images_root),
        }

    def _entry(self, index: int) -> dict:
        r = self.rows[index]
        return {
            "index": index,
            "file": r["relpath"],
            "page": r["page"],
            "line": r["line"],
            "word": 0,
            "text": r["text"],
        }

    def entries_payload(self) -> dict:
        entries = [self._entry(i) for i in range(len(self.rows))]
        pages = sorted({str(r["page"]) for r in self.rows})
        return {"entries": entries, "pages": pages, "stats": self.stats()}

    def get_entry(self, index: int) -> dict | None:
        if index < 0 or index >= len(self.rows):
            return None
        return self._entry(index)

    def update_entry(self, index: int, text: str) -> dict:
        with self._lock:
            if index < 0 or index >= len(self.rows):
                raise IndexError(index)
            self.rows[index]["text"] = text.strip()
            self._write()
        return self._entry(index)

    def image_path_for(self, index: int) -> Path | None:
        if index < 0 or index >= len(self.rows):
            return None
        return self.images_root / self.rows[index]["relpath"]

    def _write(self) -> None:
        lines = [
            f"{r['page']}\t{r['line']}\t{r['relpath']}\t{r['text']}" for r in self.rows
        ]
        tmp = self.tsv_path.with_suffix(".tsv.tmp")
        tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        tmp.replace(self.tsv_path)


_APP_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Anchor Transcription Review</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4efe4;
      --panel: #fffdf8;
      --ink: #1f1a14;
      --muted: #6f6757;
      --accent: #7a4b2a;
      --accent-soft: #eadfce;
      --danger: #b91c1c;
      --warn: #b45309;
      --ok: #166534;
      --border: #d8cdb8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: var(--bg);
      color: var(--ink);
    }
    .app {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
      display: grid;
      gap: 16px;
    }
    header {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      justify-content: space-between;
    }
    h1 {
      margin: 0;
      font-size: 1.35rem;
      font-weight: normal;
    }
    .meta { color: var(--muted); font-size: 0.92rem; }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    select, input[type="text"], input[type="number"] {
      font: inherit;
      padding: 6px 10px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--panel);
    }
    button {
      font: inherit;
      padding: 8px 14px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--panel);
      cursor: pointer;
    }
    button.primary {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }
    button:disabled { opacity: 0.45; cursor: default; }
    .stats {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .pill {
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      font-size: 0.88rem;
    }
    .pill.bad { background: #fee2e2; color: var(--danger); }
    .pill.warn { background: #ffedd5; color: var(--warn); }
    .pill.ok { background: #dcfce7; color: var(--ok); }
    .card {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
      gap: 20px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
      min-height: 420px;
    }
    @media (max-width: 860px) {
      .card { grid-template-columns: 1fr; }
    }
    .image-wrap {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 320px;
      background:
        linear-gradient(45deg, #ece4d4 25%, transparent 25%) 0 0/16px 16px,
        linear-gradient(-45deg, #ece4d4 25%, transparent 25%) 0 8px/16px 16px,
        #f8f3e9;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 24px;
    }
    .image-wrap img {
      max-width: 100%;
      max-height: 520px;
      image-rendering: pixelated;
      background: #fff;
      box-shadow: 0 8px 24px rgba(31, 26, 20, 0.08);
    }
    .side { display: grid; gap: 14px; align-content: start; }
    .filename { font-size: 0.95rem; word-break: break-all; }
    label { display: grid; gap: 6px; font-size: 0.92rem; }
    .transcription-input {
      font-size: 1.6rem;
      padding: 12px 14px;
      letter-spacing: 0.02em;
    }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; }
    .status {
      min-height: 1.2em;
      color: var(--muted);
      font-size: 0.92rem;
    }
    .status.error { color: var(--danger); }
    .status.saved { color: var(--ok); }
    .hint {
      font-size: 0.85rem;
      color: var(--muted);
      line-height: 1.45;
    }
    kbd {
      display: inline-block;
      padding: 1px 6px;
      border: 1px solid var(--border);
      border-radius: 4px;
      background: #fff;
      font-size: 0.82rem;
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div>
        <h1>Anchor Transcription Review</h1>
        <div id="path-meta" class="meta"></div>
      </div>
      <div class="toolbar">
        <label>
          Page
          <select id="page-filter"><option value="">All pages</option></select>
        </label>
        <label>
          Show
          <select id="status-filter">
            <option value="all">All words</option>
            <option value="unknown">Unknown (?)</option>
            <option value="soft">Soft (~)</option>
            <option value="review">Needs review (? or ~)</option>
          </select>
        </label>
        <label>
          Jump #
          <input id="jump-index" type="number" min="1" step="1" placeholder="1">
        </label>
      </div>
    </header>

    <div class="stats" id="stats"></div>

    <div class="card">
      <div class="image-wrap">
        <img id="word-image" alt="Word crop">
      </div>
      <div class="side">
        <div>
          <div id="position" class="meta"></div>
          <div id="filename" class="filename"></div>
        </div>
        <label>
          Transcription
          <input id="transcription" class="transcription-input" type="text" autocomplete="off" spellcheck="false">
        </label>
        <div class="actions">
          <button id="prev-btn" type="button">← Prev</button>
          <button id="save-btn" class="primary" type="button">Save</button>
          <button id="next-btn" type="button">Next →</button>
          <button id="unknown-btn" type="button">Mark ?</button>
        </div>
        <div id="status" class="status"></div>
        <div class="hint">
          Keyboard: <kbd>←</kbd>/<kbd>→</kbd> prev/next,
          <kbd>S</kbd> save,
          <kbd>?</kbd> mark unknown,
          <kbd>N</kbd> save and next.
          Edits are written to <code>transcription.txt</code> on save.
        </div>
      </div>
    </div>
  </div>
  <script>
    const state = {
      entries: [],
      filtered: [],
      cursor: 0,
      dirty: false,
    };

    const dom = {
      pathMeta: document.getElementById('path-meta'),
      stats: document.getElementById('stats'),
      pageFilter: document.getElementById('page-filter'),
      statusFilter: document.getElementById('status-filter'),
      jumpIndex: document.getElementById('jump-index'),
      wordImage: document.getElementById('word-image'),
      position: document.getElementById('position'),
      filename: document.getElementById('filename'),
      transcription: document.getElementById('transcription'),
      prevBtn: document.getElementById('prev-btn'),
      saveBtn: document.getElementById('save-btn'),
      nextBtn: document.getElementById('next-btn'),
      unknownBtn: document.getElementById('unknown-btn'),
      status: document.getElementById('status'),
    };

    function setStatus(message, kind = '') {
      dom.status.textContent = message || '';
      dom.status.className = 'status' + (kind ? ` ${kind}` : '');
    }

    function needsReview(text) {
      const value = String(text || '').trim();
      return value === '?' || value.startsWith('~');
    }

    function applyFilters() {
      const page = dom.pageFilter.value;
      const status = dom.statusFilter.value;
      state.filtered = state.entries.filter((entry) => {
        if (page && entry.page !== page) return false;
        if (status === 'unknown') return entry.text.trim() === '?';
        if (status === 'soft') return entry.text.trim().startsWith('~');
        if (status === 'review') return needsReview(entry.text);
        return true;
      });
      state.cursor = Math.min(state.cursor, Math.max(0, state.filtered.length - 1));
      renderCurrent();
    }

    function renderStats(stats) {
      dom.stats.innerHTML = '';
      const pills = [
        ['total', `${stats.total} words`, ''],
        ['unknown', `${stats.unknown} unknown`, stats.unknown ? 'bad' : 'ok'],
        ['soft', `${stats.soft} soft (~)`, stats.soft ? 'warn' : ''],
        ['known', `${stats.known} known`, 'ok'],
      ];
      pills.forEach(([, label, cls]) => {
        const pill = document.createElement('span');
        pill.className = 'pill' + (cls ? ` ${cls}` : '');
        pill.textContent = label;
        dom.stats.appendChild(pill);
      });
      dom.pathMeta.textContent = `${stats.transcription_path}`;
    }

    function currentEntry() {
      return state.filtered[state.cursor] || null;
    }

    function renderCurrent() {
      const entry = currentEntry();
      dom.prevBtn.disabled = state.cursor <= 0;
      dom.nextBtn.disabled = state.cursor >= state.filtered.length - 1;
      if (!entry) {
        dom.wordImage.removeAttribute('src');
        dom.position.textContent = 'No entries match the current filter.';
        dom.filename.textContent = '';
        dom.transcription.value = '';
        dom.transcription.disabled = true;
        return;
      }
      dom.transcription.disabled = false;
      dom.wordImage.src = `/image/${entry.index}`;
      dom.position.textContent =
        `${state.cursor + 1} of ${state.filtered.length} shown · absolute #${entry.index + 1}` +
        ` · page ${entry.page} · line ${entry.line} · word ${entry.word}`;
      dom.filename.textContent = entry.file;
      if (!state.dirty) {
        dom.transcription.value = entry.text;
      }
      dom.jumpIndex.value = String(entry.index + 1);
    }

    async function saveCurrent({ advance = false } = {}) {
      const entry = currentEntry();
      if (!entry) return;
      const text = dom.transcription.value.trim();
      try {
        const response = await fetch(`/api/entry/${entry.index}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text }),
        });
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        entry.text = data.entry.text;
        const master = state.entries.find((item) => item.index === entry.index);
        if (master) master.text = data.entry.text;
        state.dirty = false;
        renderStats(data.stats);
        setStatus('Saved.', 'saved');
        const previousIndex = entry.index;
        applyFilters();
        if (advance) {
          const nextPos = state.filtered.findIndex((item) => item.index > previousIndex);
          state.cursor = nextPos === -1 ? Math.max(0, state.filtered.length - 1) : nextPos;
          renderCurrent();
        }
      } catch (error) {
        setStatus(String(error), 'error');
      }
    }

    function go(delta) {
      if (state.dirty) {
        setStatus('Save or revert before navigating.', 'error');
        return;
      }
      state.cursor = Math.max(0, Math.min(state.filtered.length - 1, state.cursor + delta));
      renderCurrent();
    }

    function jumpToAbsolute(indexOneBased) {
      const target = Number(indexOneBased);
      if (!Number.isFinite(target) || target < 1) return;
      const found = state.filtered.findIndex((entry) => entry.index + 1 === target);
      if (found === -1) {
        setStatus(`Word #${target} is not in the current filter.`, 'error');
        return;
      }
      if (state.dirty) {
        setStatus('Save or revert before jumping.', 'error');
        return;
      }
      state.cursor = found;
      renderCurrent();
    }

    dom.transcription.addEventListener('input', () => {
      state.dirty = true;
      setStatus('Unsaved changes.');
    });

    dom.prevBtn.addEventListener('click', () => go(-1));
    dom.nextBtn.addEventListener('click', () => go(1));
    dom.saveBtn.addEventListener('click', () => saveCurrent());
    dom.unknownBtn.addEventListener('click', () => {
      dom.transcription.value = '?';
      state.dirty = true;
      setStatus('Marked unknown — save to persist.');
    });
    dom.pageFilter.addEventListener('change', () => {
      state.cursor = 0;
      state.dirty = false;
      applyFilters();
    });
    dom.statusFilter.addEventListener('change', () => {
      state.cursor = 0;
      state.dirty = false;
      applyFilters();
    });
    dom.jumpIndex.addEventListener('change', () => jumpToAbsolute(dom.jumpIndex.value));
    dom.jumpIndex.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') jumpToAbsolute(dom.jumpIndex.value);
    });

    window.addEventListener('keydown', (event) => {
      const tag = document.activeElement?.tagName || '';
      const typing = tag === 'INPUT' || tag === 'TEXTAREA';
      if (event.key === 'ArrowLeft' && !typing) { event.preventDefault(); go(-1); }
      if (event.key === 'ArrowRight' && !typing) { event.preventDefault(); go(1); }
      if (!typing && event.key === '?') {
        event.preventDefault();
        dom.transcription.value = '?';
        state.dirty = true;
        setStatus('Marked unknown — save to persist.');
      }
      if (!typing && (event.key === 's' || event.key === 'S')) {
        event.preventDefault();
        void saveCurrent();
      }
      if (!typing && (event.key === 'n' || event.key === 'N')) {
        event.preventDefault();
        void saveCurrent({ advance: true });
      }
    });

    async function init() {
      const response = await fetch('/api/entries');
      const data = await response.json();
      state.entries = data.entries;
      renderStats(data.stats);
      data.pages.forEach((page) => {
        const option = document.createElement('option');
        option.value = page;
        option.textContent = `Page ${page}`;
        dom.pageFilter.appendChild(option);
      });
      applyFilters();
    }

    init().catch((error) => setStatus(String(error), 'error'));
  </script>
</body>
</html>
"""


class _ReviewHandler(BaseHTTPRequestHandler):
    server_version = "ScribeHandTranscriptionReview/0.1"

    @property
    def session(self) -> "TranscriptionReviewSession | LineReviewSession":
        return self.server.session  # type: ignore[attr-defined]

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, body: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path)
        if path.path in {"/", "/index.html"}:
            self._send_bytes(_APP_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path.path == "/api/entries":
            self._send_json(self.session.entries_payload())
            return
        if path.path.startswith("/api/entry/"):
            index = int(path.path.rsplit("/", 1)[-1])
            entry = self.session.get_entry(index)
            if entry is None:
                self._send_json({"error": "not found"}, status=404)
                return
            self._send_json({"entry": entry, "stats": self.session.stats()})
            return
        if path.path.startswith("/image/"):
            try:
                index = int(path.path.rsplit("/", 1)[-1])
            except ValueError:
                self.send_error(400)
                return
            image_path = self.session.image_path_for(index)
            if image_path is None or not image_path.is_file():
                self.send_error(404)
                return
            content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
            self._send_bytes(image_path.read_bytes(), content_type)
            return
        self.send_error(404)

    def do_PUT(self) -> None:  # noqa: N802
        path = urlparse(self.path)
        if not path.path.startswith("/api/entry/"):
            self.send_error(404)
            return
        index = int(path.path.rsplit("/", 1)[-1])
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
            text = str(payload.get("text", ""))
            entry = self.session.update_entry(index, text)
        except (json.JSONDecodeError, IndexError, ValueError) as exc:
            self._send_json({"error": str(exc)}, status=400)
            return
        self._send_json({"entry": entry, "stats": self.session.stats()})


def main() -> None:
    ap = argparse.ArgumentParser(description="Review anchor transcriptions in the browser.")
    ap.add_argument(
        "--dir",
        type=Path,
        help="Anchor work dir containing words/ and transcription.txt",
    )
    ap.add_argument("--words", type=Path, help="Directory of word PNG crops")
    ap.add_argument("--transcription", type=Path, help="Parallel transcription.txt")
    ap.add_argument("--word-list", type=Path, help="Optional explicit filename order")
    ap.add_argument("--tsv", type=Path,
                    help="Line-review mode: TSV of page<TAB>line<TAB>relpath<TAB>text")
    ap.add_argument("--images-root", type=Path,
                    help="Root dir for TSV relpaths (line strips)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true", help="Do not open a browser tab")
    args = ap.parse_args()

    if args.tsv:
        if not args.images_root:
            raise SystemExit("--tsv requires --images-root")
        if not args.tsv.is_file():
            raise SystemExit(f"TSV not found: {args.tsv}")
        if not args.images_root.is_dir():
            raise SystemExit(f"Images root not found: {args.images_root}")
        session = LineReviewSession(args.tsv, args.images_root)
        httpd = ThreadingHTTPServer((args.host, args.port), _ReviewHandler)
        httpd.session = session  # type: ignore[attr-defined]
        port = httpd.server_address[1]
        url = f"http://{args.host}:{port}/"
        stats = session.stats()
        print(f"Serving {stats['total']} line strips at {url}")
        print(f"  images: {stats['words_dir']}")
        print(f"  transcription: {stats['transcription_path']}")
        if not args.no_open:
            threading.Timer(0.4, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
        return

    if args.dir:
        words_dir = args.dir / "words"
        transcription_path = args.dir / "transcription.txt"
        word_list_path = args.dir / "word_list.txt"
    else:
        if not args.words or not args.transcription:
            raise SystemExit("Provide --dir or both --words and --transcription")
        words_dir = args.words
        transcription_path = args.transcription
        word_list_path = args.word_list

    if not words_dir.is_dir():
        raise SystemExit(f"Words directory not found: {words_dir}")
    if not transcription_path.is_file():
        raise SystemExit(f"Transcription file not found: {transcription_path}")

    session = TranscriptionReviewSession(
        words_dir=words_dir,
        transcription_path=transcription_path,
        word_list_path=word_list_path if word_list_path and word_list_path.exists() else None,
    )
    httpd = ThreadingHTTPServer((args.host, args.port), _ReviewHandler)
    httpd.session = session  # type: ignore[attr-defined]
    port = httpd.server_address[1]
    url = f"http://{args.host}:{port}/"
    stats = session.stats()
    print(f"Serving {stats['total']} word pairs at {url}")
    print(f"  words: {stats['words_dir']}")
    print(f"  transcription: {stats['transcription_path']}")
    if not args.no_open:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
