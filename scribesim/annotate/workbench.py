"""Local reviewed-annotation workbench for TD-014."""

from __future__ import annotations

import json
import threading
import tomllib
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from PIL import Image

DEFAULT_COVERAGE_LEDGER_PATH = Path(
    "shared/training/handsim/reviewed_annotations/coverage_ledger_v1/coverage_ledger.json"
)
DEFAULT_REVIEWED_ANNOTATION_OUTPUT_ROOT = Path("shared/training/handsim/reviewed_annotations/workbench_v1")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_toml(path: Path | str) -> dict[str, Any]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def _load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _resolve_path(path: str | Path, *, relative_to: Path | None = None) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    if candidate.exists():
        return candidate.resolve()
    if relative_to is not None:
        resolved = (relative_to / candidate).resolve()
        if resolved.exists() or not candidate.exists():
            return resolved
    return candidate.resolve()


def _safe_id(prefix: str, value: str) -> str:
    sanitized = "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower()
    sanitized = "_".join(part for part in sanitized.split("_") if part)
    return f"{prefix}_{sanitized or 'item'}"


def _toml_string(value: str) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _ensure_bounds(bounds: dict[str, Any]) -> dict[str, int]:
    required = ("x", "y", "width", "height")
    missing = [key for key in required if key not in bounds]
    if missing:
        raise ValueError(f"annotation bounds missing keys: {', '.join(missing)}")
    parsed = {key: int(round(float(bounds[key]))) for key in required}
    if parsed["width"] <= 0 or parsed["height"] <= 0:
        raise ValueError("annotation bounds must have positive width and height")
    if parsed["x"] < 0 or parsed["y"] < 0:
        raise ValueError("annotation bounds must be non-negative")
    return parsed


def _normalize_cleanup_strokes(strokes: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    if not strokes:
        return normalized
    for stroke in strokes:
        mode = str(stroke.get("mode", "")).strip()
        if mode not in {"erase", "restore"}:
            raise ValueError("cleanup stroke mode must be erase or restore")
        size_px = int(round(float(stroke.get("size_px", 0))))
        if size_px <= 0:
            raise ValueError("cleanup stroke size_px must be positive")
        points = []
        for point in stroke.get("points", []):
            points.append(
                {
                    "x": int(round(float(point["x"]))),
                    "y": int(round(float(point["y"]))),
                }
            )
        if not points:
            raise ValueError("cleanup stroke must include at least one point")
        normalized.append(
            {
                "mode": mode,
                "size_px": size_px,
                "points": points,
            }
        )
    return normalized


def _entry_to_payload(entry: dict[str, Any]) -> dict[str, Any]:
    payload = dict(entry)
    payload["bounds_px"] = dict(entry.get("bounds_px", {}))
    payload["reviewed_source_paths"] = list(entry.get("reviewed_source_paths", []))
    payload["cleanup_strokes"] = _normalize_cleanup_strokes(entry.get("cleanup_strokes", []))
    return payload


def _reviewed_manifest_template(
    *,
    reviewed_manifest_path: Path,
    coverage_ledger_path: Path,
    selection_manifest_path: Path,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "manifest_kind": "reviewed_annotations",
        "dataset_id": reviewed_manifest_path.parent.name or "reviewed_annotations_v1",
        "coverage_ledger_path": coverage_ledger_path.as_posix(),
        "selection_manifest_path": selection_manifest_path.as_posix(),
        "created_by": "annotate-workbench",
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "entry_count": 0,
        "entries": [],
    }


def _format_reviewed_manifest(manifest: dict[str, Any]) -> str:
    lines = [
        "# TD-014 reviewed annotation manifest",
        f"schema_version = {int(manifest.get('schema_version', 1))}",
        f"manifest_kind = {_toml_string(manifest.get('manifest_kind', 'reviewed_annotations'))}",
        f"dataset_id = {_toml_string(manifest.get('dataset_id', 'reviewed_annotations_v1'))}",
        f"coverage_ledger_path = {_toml_string(manifest.get('coverage_ledger_path', ''))}",
        f"selection_manifest_path = {_toml_string(manifest.get('selection_manifest_path', ''))}",
        f"created_by = {_toml_string(manifest.get('created_by', 'annotate-workbench'))}",
        f"created_at = {_toml_string(manifest.get('created_at', ''))}",
        f"updated_at = {_toml_string(manifest.get('updated_at', ''))}",
        f"entry_count = {int(manifest.get('entry_count', 0))}",
        "",
    ]
    for entry in manifest.get("entries", []):
        bounds = entry.get("bounds_px", {})
        lines.extend(
            [
                "[[entries]]",
                f"id = {_toml_string(entry.get('id', ''))}",
                f"kind = {_toml_string(entry.get('kind', 'glyph'))}",
                f"symbol = {_toml_string(entry.get('symbol', ''))}",
                f"quality = {_toml_string(entry.get('quality', 'usable'))}",
                f"notes = {_toml_string(entry.get('notes', ''))}",
                f"source_path = {_toml_string(entry.get('source_path', ''))}",
                f"source_manuscript_label = {_toml_string(entry.get('source_manuscript_label', ''))}",
                f"canvas_label = {_toml_string(entry.get('canvas_label', ''))}",
                f"source_object_id = {_toml_string(entry.get('source_object_id', ''))}",
                f"image_width_px = {int(entry.get('image_width_px', 0))}",
                f"image_height_px = {int(entry.get('image_height_px', 0))}",
                "bounds_px = { "
                f"x = {int(bounds.get('x', 0))}, "
                f"y = {int(bounds.get('y', 0))}, "
                f"width = {int(bounds.get('width', 0))}, "
                f"height = {int(bounds.get('height', 0))} "
                "}",
                "reviewed_source_paths = ["
                + ", ".join(_toml_string(item) for item in entry.get("reviewed_source_paths", []))
                + "]",
                f"created_at = {_toml_string(entry.get('created_at', ''))}",
                f"updated_at = {_toml_string(entry.get('updated_at', ''))}",
            ]
        )
        for stroke in entry.get("cleanup_strokes", []):
            points = stroke.get("points", [])
            point_list = ", ".join(
                "{ " + f"x = {int(point.get('x', 0))}, y = {int(point.get('y', 0))}" + " }"
                for point in points
            )
            lines.extend(
                [
                    "[[entries.cleanup_strokes]]",
                    f"mode = {_toml_string(stroke.get('mode', 'erase'))}",
                    f"size_px = {int(stroke.get('size_px', 1))}",
                    f"points = [{point_list}]",
                ]
            )
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _build_folio_index(selection_manifest: dict[str, Any], *, relative_to: Path | None = None) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    folios: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for index, folio in enumerate(selection_manifest.get("folios", []), start=1):
        folio_id = str(folio.get("rank", index))
        local_path = _resolve_path(str(folio.get("local_path", "")), relative_to=relative_to)
        item = {
            "id": folio_id,
            "rank": int(folio.get("rank", index)),
            "canvas_label": str(folio.get("canvas_label", folio_id)),
            "source_manuscript_label": str(folio.get("source_manuscript_label", "unknown")),
            "source_object_id": str(folio.get("source_object_id", "")),
            "local_path": local_path.as_posix(),
        }
        folios.append(item)
        by_id[folio_id] = item
    folios.sort(key=lambda item: item["rank"])
    return folios, by_id


class ReviewedAnnotationWorkbench:
    """Stateful reviewed-annotation workbench store."""

    def __init__(
        self,
        *,
        coverage_ledger_path: Path | str,
        output_root: Path | str,
        reviewed_manifest_path: Path | str | None = None,
        selection_manifest_path: Path | str | None = None,
    ) -> None:
        self.coverage_ledger_path = _resolve_path(coverage_ledger_path)
        self.output_root = Path(output_root).resolve()
        self.output_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

        self.ledger = _load_json(self.coverage_ledger_path)
        self.corpus_manifest_path = _resolve_path(self.ledger["corpus_manifest_path"])
        corpus_manifest = _load_toml(self.corpus_manifest_path)

        if selection_manifest_path is not None:
            self.selection_manifest_path = _resolve_path(selection_manifest_path)
        else:
            raw_selection_path = corpus_manifest.get("selection_manifest_path")
            if not raw_selection_path:
                raise ValueError("corpus manifest missing selection_manifest_path")
            self.selection_manifest_path = _resolve_path(raw_selection_path, relative_to=self.corpus_manifest_path.parent)

        self.selection_manifest = _load_toml(self.selection_manifest_path)
        self.folios, self._folios_by_id = _build_folio_index(
            self.selection_manifest,
            relative_to=self.selection_manifest_path.parent,
        )

        self.reviewed_manifest_path = (
            Path(reviewed_manifest_path).resolve()
            if reviewed_manifest_path is not None
            else (self.output_root / "reviewed_manifest.toml").resolve()
        )
        if self.reviewed_manifest_path.exists():
            self.reviewed_manifest = _load_toml(self.reviewed_manifest_path)
        else:
            self.reviewed_manifest = _reviewed_manifest_template(
                reviewed_manifest_path=self.reviewed_manifest_path,
                coverage_ledger_path=self.coverage_ledger_path,
                selection_manifest_path=self.selection_manifest_path,
            )
            self._write_manifest()

    def _write_manifest(self) -> None:
        self.reviewed_manifest["entry_count"] = len(self.reviewed_manifest.get("entries", []))
        self.reviewed_manifest["updated_at"] = _utc_now()
        self.reviewed_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.reviewed_manifest_path.write_text(_format_reviewed_manifest(self.reviewed_manifest), encoding="utf-8")

    def get_folio(self, folio_id: str) -> dict[str, Any]:
        try:
            return self._folios_by_id[str(folio_id)]
        except KeyError as exc:
            raise KeyError(f"unknown folio id: {folio_id}") from exc

    def list_annotations(self) -> list[dict[str, Any]]:
        return [_entry_to_payload(entry) for entry in self.reviewed_manifest.get("entries", [])]

    def get_state(self) -> dict[str, Any]:
        summary = dict(self.ledger.get("summary", {}))
        entries = list(self.ledger.get("entries", []))
        debt = [
            {
                "kind": entry["kind"],
                "symbol": entry["symbol"],
                "missing_reviewed": int(entry.get("missing_reviewed", 0)),
                "reviewed_count": int(entry.get("reviewed_count", 0)),
                "promoted_count": int(entry.get("promoted_count", 0)),
                "auto_admitted_count": int(entry.get("auto_admitted_count", 0)),
            }
            for entry in entries
            if int(entry.get("missing_reviewed", 0)) == 1
        ]
        debt.sort(key=lambda item: (item["kind"], item["symbol"]))
        return {
            "coverage_summary": summary,
            "coverage_entries": entries,
            "coverage_debt": debt,
            "folios": self.folios,
            "annotations": self.list_annotations(),
            "reviewed_manifest_path": self.reviewed_manifest_path.as_posix(),
            "coverage_ledger_path": self.coverage_ledger_path.as_posix(),
            "selection_manifest_path": self.selection_manifest_path.as_posix(),
            "output_root": self.output_root.as_posix(),
        }

    def save_annotation(self, payload: dict[str, Any]) -> dict[str, Any]:
        kind = str(payload.get("kind", "")).strip()
        symbol = str(payload.get("symbol", "")).strip()
        quality = str(payload.get("quality", "usable")).strip() or "usable"
        if kind not in {"glyph", "join"}:
            raise ValueError("annotation kind must be 'glyph' or 'join'")
        if not symbol:
            raise ValueError("annotation symbol is required")
        if quality not in {"trusted", "usable", "uncertain"}:
            raise ValueError("annotation quality must be trusted, usable, or uncertain")

        folio = self.get_folio(str(payload.get("folio_id", "")))
        image_path = Path(folio["local_path"])
        if not image_path.exists():
            raise FileNotFoundError(f"source image does not exist: {image_path}")
        image_width_px, image_height_px = Image.open(image_path).size
        bounds = _ensure_bounds(dict(payload.get("bounds_px", {})))
        if bounds["x"] + bounds["width"] > image_width_px or bounds["y"] + bounds["height"] > image_height_px:
            raise ValueError("annotation bounds exceed source image size")

        annotation_id = str(payload.get("id", "")).strip()
        now = _utc_now()

        with self._lock:
            entries = list(self.reviewed_manifest.get("entries", []))
            index = None
            existing = None
            if annotation_id:
                for idx, entry in enumerate(entries):
                    if str(entry.get("id")) == annotation_id:
                        index = idx
                        existing = entry
                        break
            if not annotation_id:
                annotation_id = f"{_safe_id(kind, symbol)}_{len(entries) + 1:04d}"

            entry = {
                "id": annotation_id,
                "kind": kind,
                "symbol": symbol,
                "quality": quality,
                "notes": str(payload.get("notes", "")).strip(),
                "source_path": image_path.as_posix(),
                "source_manuscript_label": folio["source_manuscript_label"],
                "canvas_label": folio["canvas_label"],
                "source_object_id": folio["source_object_id"],
                "image_width_px": image_width_px,
                "image_height_px": image_height_px,
                "bounds_px": bounds,
                "reviewed_source_paths": [image_path.as_posix()],
                "cleanup_strokes": _normalize_cleanup_strokes(payload.get("cleanup_strokes", [])),
                "created_at": str(existing.get("created_at", now)) if existing else now,
                "updated_at": now,
            }
            if index is None:
                entries.append(entry)
            else:
                entries[index] = entry
            entries.sort(key=lambda item: (item["source_path"], item["kind"], item["symbol"], item["id"]))
            self.reviewed_manifest["entries"] = entries
            self._write_manifest()
        return _entry_to_payload(entry)

    def delete_annotation(self, annotation_id: str) -> bool:
        with self._lock:
            entries = list(self.reviewed_manifest.get("entries", []))
            kept = [entry for entry in entries if str(entry.get("id")) != str(annotation_id)]
            if len(kept) == len(entries):
                return False
            self.reviewed_manifest["entries"] = kept
            self._write_manifest()
        return True

    def read_folio_image(self, folio_id: str) -> tuple[bytes, str]:
        folio = self.get_folio(folio_id)
        image_path = Path(folio["local_path"])
        suffix = image_path.suffix.lower()
        content_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }.get(suffix, "application/octet-stream")
        return image_path.read_bytes(), content_type


_APP_CSS = """
:root {
  color-scheme: light;
  --bg: #f3efe6;
  --panel: #fffdf7;
  --ink: #222018;
  --muted: #6f6757;
  --line: #d8cfbe;
  --accent: #885d3a;
  --accent-soft: #efe2d3;
  --glyph: #2563eb;
  --join: #b45309;
  --selected: #dc2626;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Georgia, "Iowan Old Style", serif;
  color: var(--ink);
  background: radial-gradient(circle at top, #fbf8f1, var(--bg) 55%);
  overflow: hidden;
}
.app {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr) 360px;
  height: 100vh;
  overflow: hidden;
}
.panel {
  overflow: auto;
  border-right: 1px solid var(--line);
  background: rgba(255, 253, 247, 0.93);
  padding: 16px 18px 28px;
}
.panel:last-child { border-right: 0; border-left: 1px solid var(--line); }
h1, h2, h3 { margin: 0 0 10px; font-weight: 600; }
h1 { font-size: 1.15rem; }
h2 { font-size: 1rem; margin-top: 18px; }
h3 { font-size: 0.92rem; margin-top: 16px; }
.meta, .small { color: var(--muted); font-size: 0.88rem; line-height: 1.4; }
.pill {
  display: inline-block;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 4px 8px;
  margin: 0 6px 6px 0;
  font-size: 0.82rem;
  background: #fff;
}
.debt-list, .annotation-list, .folio-list {
  display: grid;
  gap: 8px;
}
.card, .folio-item, .annotation-item {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 12px;
  padding: 10px 12px;
}
.folio-item button,
.annotation-item button,
button {
  font: inherit;
}
.folio-item.active, .annotation-item.active { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(136, 93, 58, 0.14); }
.viewer {
  display: grid;
  grid-template-rows: auto 1fr;
  min-width: 0;
  min-height: 0;
}
.viewer-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 12px 18px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 253, 247, 0.85);
}
.viewer-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.viewer-controls label {
  margin-top: 0;
  min-width: 180px;
}
.viewer-controls button.active {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent);
}
.viewer-stage {
  overflow: auto;
  padding: 20px;
  overscroll-behavior: contain;
  touch-action: pan-x pan-y;
  cursor: default;
  min-height: 0;
}
.viewer-stage.pan-mode {
  cursor: grab;
}
.viewer-stage.pan-mode.dragging {
  cursor: grabbing;
}
.canvas-wrap {
  position: relative;
  width: fit-content;
  margin: 0 auto;
  background: white;
  box-shadow: 0 14px 30px rgba(39, 31, 18, 0.12);
  transform-origin: top left;
}
.canvas-wrap img {
  display: block;
  max-width: none;
  width: auto;
  height: auto;
}
.overlay {
  position: absolute;
  inset: 0;
}
.box {
  position: absolute;
  border: 2px solid;
  background: rgba(255,255,255,0.04);
  cursor: pointer;
}
.box.glyph { border-color: var(--glyph); background: rgba(37, 99, 235, 0.09); }
.box.join { border-color: var(--join); background: rgba(180, 83, 9, 0.1); }
.box.selected { border-color: var(--selected); box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.18); }
.box.draft { border-style: dashed; }
label { display: grid; gap: 6px; font-size: 0.9rem; margin-top: 12px; }
input, select, textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  font: inherit;
}
textarea { min-height: 84px; resize: vertical; }
.grid2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}
button {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 8px 12px;
  background: white;
  cursor: pointer;
}
button.primary {
  border-color: var(--accent);
  background: var(--accent);
  color: white;
}
button.danger {
  border-color: #b91c1c;
  color: #b91c1c;
}
.status {
  min-height: 1.4em;
  margin-top: 10px;
  color: var(--muted);
  font-size: 0.9rem;
}
.magnifier {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}
.magnifier-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
}
.magnifier-meta {
  color: var(--muted);
  font-size: 0.82rem;
}
.magnifier canvas {
  display: block;
  width: 100%;
  max-width: 260px;
  aspect-ratio: 1;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #f8f3e9;
  margin-top: 8px;
}
.cleanup-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 10px;
}
.cleanup-toolbar button.active {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent);
}
.cleanup-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 10px;
}
.cleanup-card {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 8px;
  background: #fff;
}
.cleanup-card h3 {
  margin: 0 0 8px;
  font-size: 0.86rem;
}
.cleanup-canvas {
  display: block;
  width: 100%;
  aspect-ratio: 1;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f8f3e9;
}
"""


_APP_JS = """
const state = {
  payload: null,
  currentFolioId: null,
  selectedAnnotationId: null,
  draftBounds: null,
  naturalWidth: 1,
  naturalHeight: 1,
  panMode: false,
  cleanup: {
    strokes: [],
    mode: 'erase',
    brushSize: 10,
    drawingStroke: null,
    previewTransform: null,
    hoverPoint: null,
  },
};

const dom = {
  coverageSummary: document.getElementById('coverage-summary'),
  coverageDebt: document.getElementById('coverage-debt'),
  folioList: document.getElementById('folio-list'),
  annotationList: document.getElementById('annotation-list'),
  folioTitle: document.getElementById('folio-title'),
  folioMeta: document.getElementById('folio-meta'),
  image: document.getElementById('folio-image'),
  overlay: document.getElementById('overlay'),
  canvasWrap: document.querySelector('.canvas-wrap'),
  viewerStage: document.querySelector('.viewer-stage'),
  magnifierCanvas: document.getElementById('magnifier-canvas'),
  magnifierMeta: document.getElementById('magnifier-meta'),
  zoom: document.getElementById('zoom'),
  zoomValue: document.getElementById('zoom-value'),
  zoomIn: document.getElementById('zoom-in'),
  zoomOut: document.getElementById('zoom-out'),
  zoomReset: document.getElementById('zoom-reset'),
  panToggle: document.getElementById('pan-toggle'),
  annotationId: document.getElementById('annotation-id'),
  kind: document.getElementById('kind'),
  symbol: document.getElementById('symbol'),
  quality: document.getElementById('quality'),
  notes: document.getElementById('notes'),
  x: document.getElementById('x'),
  y: document.getElementById('y'),
  width: document.getElementById('width'),
  height: document.getElementById('height'),
  manifestPath: document.getElementById('manifest-path'),
  status: document.getElementById('status'),
  saveButton: document.getElementById('save-annotation'),
  deleteButton: document.getElementById('delete-annotation'),
  clearButton: document.getElementById('clear-selection'),
  cleanupModeErase: document.getElementById('cleanup-mode-erase'),
  cleanupModeRestore: document.getElementById('cleanup-mode-restore'),
  cleanupBrush: document.getElementById('cleanup-brush'),
  cleanupBrushValue: document.getElementById('cleanup-brush-value'),
  cleanupClear: document.getElementById('cleanup-clear'),
  cleanupRawCanvas: document.getElementById('cleanup-raw-canvas'),
  cleanupCleanCanvas: document.getElementById('cleanup-clean-canvas'),
  cleanupMeta: document.getElementById('cleanup-meta'),
};

const magnifier = {
  ctx: null,
  radiusPx: 24,
  scale: 8,
  visible: false,
  imageBitmap: null,
  lastPoint: null,
};

const viewport = {
  gestureStartZoom: null,
  panDrag: null,
};

const cleanup = {
  rawCtx: null,
  cleanCtx: null,
  pointerId: null,
};

function byId(id) {
  return document.getElementById(id);
}

function setStatus(message, isError = false) {
  dom.status.textContent = message || '';
  dom.status.style.color = isError ? '#b91c1c' : '#6f6757';
}

function cloneCleanupStrokes(strokes) {
  return (strokes || []).map((stroke) => ({
    mode: stroke.mode,
    size_px: Number(stroke.size_px || 1),
    points: (stroke.points || []).map((point) => ({
      x: Number(point.x || 0),
      y: Number(point.y || 0),
    })),
  }));
}

function renderPanMode() {
  dom.panToggle.classList.toggle('active', state.panMode);
  dom.panToggle.setAttribute('aria-pressed', state.panMode ? 'true' : 'false');
  dom.panToggle.textContent = state.panMode ? 'Pan: on' : 'Pan: off';
  dom.viewerStage.classList.toggle('pan-mode', state.panMode);
}

function annotationColor(kind) {
  return kind === 'join' ? 'join' : 'glyph';
}

function annotationForCurrentFolio() {
  if (!state.payload || !state.currentFolioId) return [];
  const folio = state.payload.folios.find((item) => item.id === state.currentFolioId);
  if (!folio) return [];
  return state.payload.annotations.filter((entry) => entry.source_path === folio.local_path);
}

function renderCoverage() {
  const summary = state.payload.coverage_summary;
  dom.coverageSummary.innerHTML = '';
  const items = [
    ['Glyph reviewed', summary.glyph_reviewed_coverage],
    ['Join reviewed', summary.join_reviewed_coverage],
    ['Glyph promoted', summary.glyph_promoted_coverage],
    ['Join promoted', summary.join_promoted_coverage],
  ];
  items.forEach(([label, value]) => {
    const pill = document.createElement('span');
    pill.className = 'pill';
    pill.textContent = `${label}: ${(value * 100).toFixed(1)}%`;
    dom.coverageSummary.appendChild(pill);
  });

  dom.coverageDebt.innerHTML = '';
  state.payload.coverage_debt.forEach((entry) => {
    const card = document.createElement('div');
    card.className = 'card';
    const button = document.createElement('button');
    button.textContent = `${entry.kind} ${entry.symbol}`;
    button.addEventListener('click', () => {
      dom.kind.value = entry.kind;
      dom.symbol.value = entry.symbol;
      setStatus(`Prepared label ${entry.kind} ${entry.symbol}`);
    });
    card.appendChild(button);
    const meta = document.createElement('div');
    meta.className = 'small';
    meta.textContent = `reviewed ${entry.reviewed_count} • promoted ${entry.promoted_count} • auto ${entry.auto_admitted_count}`;
    card.appendChild(meta);
    dom.coverageDebt.appendChild(card);
  });
}

function renderFolios() {
  dom.folioList.innerHTML = '';
  state.payload.folios.forEach((folio) => {
    const item = document.createElement('div');
    item.className = 'folio-item' + (folio.id === state.currentFolioId ? ' active' : '');
    const button = document.createElement('button');
    button.textContent = `${folio.rank}. ${folio.canvas_label}`;
    button.addEventListener('click', () => loadFolio(folio.id));
    item.appendChild(button);
    const meta = document.createElement('div');
    meta.className = 'small';
    meta.textContent = folio.source_manuscript_label;
    item.appendChild(meta);
    dom.folioList.appendChild(item);
  });
}

function renderAnnotations() {
  const annotations = annotationForCurrentFolio();
  dom.annotationList.innerHTML = '';
  annotations.forEach((entry) => {
    const item = document.createElement('div');
    item.className = 'annotation-item' + (entry.id === state.selectedAnnotationId ? ' active' : '');
    const button = document.createElement('button');
    button.textContent = `${entry.kind} ${entry.symbol}`;
    button.addEventListener('click', () => selectAnnotation(entry.id));
    item.appendChild(button);
    const meta = document.createElement('div');
    meta.className = 'small';
    meta.textContent = `${entry.quality} • ${entry.bounds_px.width}×${entry.bounds_px.height}px`;
    item.appendChild(meta);
    dom.annotationList.appendChild(item);
  });
}

function applyFormFromBounds(bounds) {
  dom.x.value = Math.round(bounds.x);
  dom.y.value = Math.round(bounds.y);
  dom.width.value = Math.round(bounds.width);
  dom.height.value = Math.round(bounds.height);
}

function loadFolio(folioId) {
  state.currentFolioId = folioId;
  state.selectedAnnotationId = null;
  state.draftBounds = null;
  renderFolios();
  renderAnnotations();
  syncFormFromSelection();
  const folio = state.payload.folios.find((item) => item.id === folioId);
  if (!folio) return;
  dom.folioTitle.textContent = `${folio.canvas_label}`;
  dom.folioMeta.textContent = `${folio.source_manuscript_label}`;
  dom.image.src = `/api/folio-image/${encodeURIComponent(folio.id)}`;
}

function selectAnnotation(annotationId) {
  state.selectedAnnotationId = annotationId;
  state.draftBounds = null;
  syncFormFromSelection();
  renderAnnotations();
  renderOverlay();
}

function syncFormFromSelection() {
  const selected = state.payload.annotations.find((entry) => entry.id === state.selectedAnnotationId);
  if (!selected) {
    dom.annotationId.value = '';
    dom.notes.value = '';
    dom.kind.value = dom.kind.value || 'glyph';
    dom.symbol.value = dom.symbol.value || '';
    dom.quality.value = dom.quality.value || 'usable';
    applyFormFromBounds(state.draftBounds || {x: 0, y: 0, width: 0, height: 0});
    state.cleanup.strokes = [];
    state.cleanup.drawingStroke = null;
    renderCleanupEditor();
    return;
  }
  dom.annotationId.value = selected.id;
  dom.kind.value = selected.kind;
  dom.symbol.value = selected.symbol;
  dom.quality.value = selected.quality;
  dom.notes.value = selected.notes || '';
  applyFormFromBounds(selected.bounds_px);
  state.cleanup.strokes = cloneCleanupStrokes(selected.cleanup_strokes || []);
  state.cleanup.drawingStroke = null;
  renderCleanupEditor();
}

function renderOverlay() {
  dom.overlay.innerHTML = '';
  const makeBox = (entry, extraClass = '') => {
    const box = document.createElement('div');
    box.className = `box ${annotationColor(entry.kind)} ${extraClass}`.trim();
    box.style.left = `${(entry.bounds_px.x / state.naturalWidth) * 100}%`;
    box.style.top = `${(entry.bounds_px.y / state.naturalHeight) * 100}%`;
    box.style.width = `${(entry.bounds_px.width / state.naturalWidth) * 100}%`;
    box.style.height = `${(entry.bounds_px.height / state.naturalHeight) * 100}%`;
    return box;
  };
  annotationForCurrentFolio().forEach((entry) => {
    const box = makeBox(entry, entry.id === state.selectedAnnotationId ? 'selected' : '');
    box.addEventListener('click', (event) => {
      event.stopPropagation();
      selectAnnotation(entry.id);
    });
    dom.overlay.appendChild(box);
  });
  if (state.draftBounds) {
    const box = makeBox({kind: dom.kind.value, bounds_px: state.draftBounds}, 'draft selected');
    dom.overlay.appendChild(box);
  }
}

function renderMagnifier(point = null) {
  if (!magnifier.ctx) return;
  const ctx = magnifier.ctx;
  const canvas = dom.magnifierCanvas;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#f8f3e9';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  if (!point || !dom.image.complete || !state.naturalWidth || !state.naturalHeight) {
    ctx.fillStyle = '#6f6757';
    ctx.font = '16px Georgia';
    ctx.fillText('Move cursor over folio', 18, canvas.height / 2);
    dom.magnifierMeta.textContent = 'No cursor sample';
    return;
  }

  const sourceSize = magnifier.radiusPx * 2;
  let sx = Math.round(point.x - magnifier.radiusPx);
  let sy = Math.round(point.y - magnifier.radiusPx);
  sx = Math.max(0, Math.min(state.naturalWidth - sourceSize, sx));
  sy = Math.max(0, Math.min(state.naturalHeight - sourceSize, sy));
  const sw = Math.min(sourceSize, state.naturalWidth);
  const sh = Math.min(sourceSize, state.naturalHeight);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(dom.image, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = '#dc2626';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(canvas.width / 2, 0);
  ctx.lineTo(canvas.width / 2, canvas.height);
  ctx.moveTo(0, canvas.height / 2);
  ctx.lineTo(canvas.width, canvas.height / 2);
  ctx.stroke();

  ctx.strokeStyle = '#ffffff';
  ctx.setLineDash([4, 3]);
  ctx.strokeRect(0.5, 0.5, canvas.width - 1, canvas.height - 1);
  ctx.setLineDash([]);

  const selected = state.payload?.annotations?.find((entry) => entry.id === state.selectedAnnotationId) || null;
  const activeBounds = state.draftBounds || selected?.bounds_px || null;
  if (activeBounds) {
    const scaleX = canvas.width / sw;
    const scaleY = canvas.height / sh;
    const rx = (activeBounds.x - sx) * scaleX;
    const ry = (activeBounds.y - sy) * scaleY;
    const rw = activeBounds.width * scaleX;
    const rh = activeBounds.height * scaleY;
    ctx.strokeStyle = activeBounds === state.draftBounds ? '#dc2626' : '#2563eb';
    ctx.lineWidth = 2;
    ctx.setLineDash(activeBounds === state.draftBounds ? [6, 4] : []);
    ctx.strokeRect(rx, ry, rw, rh);
    ctx.setLineDash([]);
  }

  dom.magnifierMeta.textContent = `x ${Math.round(point.x)}, y ${Math.round(point.y)} · ${magnifier.scale}x local view`;
}

function selectedAnnotation() {
  return state.payload?.annotations?.find((entry) => entry.id === state.selectedAnnotationId) || null;
}

function drawCleanupStroke(ctx, stroke) {
  const points = stroke.points || [];
  if (!points.length) return;
  ctx.save();
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.lineWidth = Number(stroke.size_px || 1);
  if (stroke.mode === 'erase') {
    ctx.globalCompositeOperation = 'destination-out';
    ctx.strokeStyle = 'rgba(0,0,0,1)';
  } else {
    ctx.globalCompositeOperation = 'source-over';
    ctx.strokeStyle = 'rgba(255,255,255,1)';
  }
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let index = 1; index < points.length; index += 1) {
    ctx.lineTo(points[index].x, points[index].y);
  }
  if (points.length === 1) {
    ctx.lineTo(points[0].x + 0.01, points[0].y + 0.01);
  }
  ctx.stroke();
  ctx.restore();
}

function drawCleanupBrushPreview(ctx, point) {
  if (!point) return;
  const transform = state.cleanup.previewTransform;
  if (!transform) return;
  const radius = Math.max(1, (Number(state.cleanup.brushSize || 1) * transform.scale) / 2);
  const cx = transform.offsetX + point.x * transform.scale;
  const cy = transform.offsetY + point.y * transform.scale;
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fillStyle = state.cleanup.mode === 'erase' ? 'rgba(220, 38, 38, 0.18)' : 'rgba(37, 99, 235, 0.18)';
  ctx.strokeStyle = state.cleanup.mode === 'erase' ? 'rgba(220, 38, 38, 0.95)' : 'rgba(37, 99, 235, 0.95)';
  ctx.lineWidth = 2;
  ctx.setLineDash([5, 4]);
  ctx.fill();
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.beginPath();
  ctx.moveTo(cx - radius, cy);
  ctx.lineTo(cx + radius, cy);
  ctx.moveTo(cx, cy - radius);
  ctx.lineTo(cx, cy + radius);
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.restore();
}

function renderCleanupCanvas(targetCanvas, bounds, drawCleaned) {
  const ctx = targetCanvas.getContext('2d');
  ctx.clearRect(0, 0, targetCanvas.width, targetCanvas.height);
  ctx.fillStyle = '#f8f3e9';
  ctx.fillRect(0, 0, targetCanvas.width, targetCanvas.height);
  if (!bounds || !dom.image.complete) {
    ctx.fillStyle = '#6f6757';
    ctx.font = '15px Georgia';
    ctx.fillText('Select a saved annotation', 14, targetCanvas.height / 2);
    return null;
  }

  const cropWidth = Math.max(1, Number(bounds.width));
  const cropHeight = Math.max(1, Number(bounds.height));
  const scale = Math.min(targetCanvas.width / cropWidth, targetCanvas.height / cropHeight);
  const drawWidth = Math.max(1, cropWidth * scale);
  const drawHeight = Math.max(1, cropHeight * scale);
  const offsetX = (targetCanvas.width - drawWidth) / 2;
  const offsetY = (targetCanvas.height - drawHeight) / 2;

  if (!drawCleaned) {
    ctx.drawImage(
      dom.image,
      bounds.x,
      bounds.y,
      cropWidth,
      cropHeight,
      offsetX,
      offsetY,
      drawWidth,
      drawHeight
    );
  } else {
    const sourceCanvas = document.createElement('canvas');
    sourceCanvas.width = cropWidth;
    sourceCanvas.height = cropHeight;
    const sourceCtx = sourceCanvas.getContext('2d');
    sourceCtx.drawImage(dom.image, bounds.x, bounds.y, cropWidth, cropHeight, 0, 0, cropWidth, cropHeight);

    const maskCanvas = document.createElement('canvas');
    maskCanvas.width = cropWidth;
    maskCanvas.height = cropHeight;
    const maskCtx = maskCanvas.getContext('2d');
    maskCtx.fillStyle = 'rgba(255,255,255,1)';
    maskCtx.fillRect(0, 0, cropWidth, cropHeight);
    state.cleanup.strokes.forEach((stroke) => drawCleanupStroke(maskCtx, stroke));
    if (state.cleanup.drawingStroke) {
      drawCleanupStroke(maskCtx, state.cleanup.drawingStroke);
    }

    sourceCtx.globalCompositeOperation = 'destination-in';
    sourceCtx.drawImage(maskCanvas, 0, 0);

    const composed = document.createElement('canvas');
    composed.width = cropWidth;
    composed.height = cropHeight;
    const composedCtx = composed.getContext('2d');
    composedCtx.fillStyle = '#ffffff';
    composedCtx.fillRect(0, 0, cropWidth, cropHeight);
    composedCtx.drawImage(sourceCanvas, 0, 0);
    ctx.drawImage(composed, 0, 0, cropWidth, cropHeight, offsetX, offsetY, drawWidth, drawHeight);
  }

  ctx.strokeStyle = 'rgba(34, 32, 24, 0.18)';
  ctx.lineWidth = 1;
  ctx.strokeRect(offsetX + 0.5, offsetY + 0.5, drawWidth - 1, drawHeight - 1);
  if (drawCleaned) {
    drawCleanupBrushPreview(ctx, state.cleanup.hoverPoint);
  }
  return { offsetX, offsetY, scale, cropWidth, cropHeight };
}

function renderCleanupEditor() {
  const selected = selectedAnnotation();
  const bounds = selected?.bounds_px || null;
  const rawTransform = renderCleanupCanvas(dom.cleanupRawCanvas, bounds, false);
  const cleanTransform = renderCleanupCanvas(dom.cleanupCleanCanvas, bounds, true);
  state.cleanup.previewTransform = cleanTransform || rawTransform;
  dom.cleanupBrushValue.textContent = `${state.cleanup.brushSize}px`;
  dom.cleanupModeErase.classList.toggle('active', state.cleanup.mode === 'erase');
  dom.cleanupModeRestore.classList.toggle('active', state.cleanup.mode === 'restore');
  if (!selected) {
    dom.cleanupMeta.textContent = 'Select a saved annotation to clean nearby artifacts.';
    return;
  }
  dom.cleanupMeta.textContent =
    `${selected.symbol} · ${state.cleanup.strokes.length} cleanup stroke(s) · ${state.cleanup.mode} ${state.cleanup.brushSize}px`;
}

function cleanupEventToPoint(event) {
  const selected = selectedAnnotation();
  const transform = state.cleanup.previewTransform;
  if (!selected || !transform) return null;
  const rect = dom.cleanupCleanCanvas.getBoundingClientRect();
  const canvasX = ((event.clientX - rect.left) / rect.width) * dom.cleanupCleanCanvas.width;
  const canvasY = ((event.clientY - rect.top) / rect.height) * dom.cleanupCleanCanvas.height;
  const x = (canvasX - transform.offsetX) / transform.scale;
  const y = (canvasY - transform.offsetY) / transform.scale;
  if (x < 0 || y < 0 || x > transform.cropWidth || y > transform.cropHeight) {
    return null;
  }
  return {
    x: Math.max(0, Math.min(transform.cropWidth, x)),
    y: Math.max(0, Math.min(transform.cropHeight, y)),
  };
}

function applyZoom() {
  const zoom = Number(dom.zoom.value || 100);
  const scaledWidth = Math.max(1, Math.round(state.naturalWidth * (zoom / 100)));
  dom.zoomValue.textContent = `${zoom}%`;
  dom.image.style.width = `${scaledWidth}px`;
}

function setZoom(nextZoom, focusClientX = null, focusClientY = null) {
  const clampedZoom = Math.max(50, Math.min(500, Math.round(nextZoom)));
  const stage = dom.viewerStage;
  const rect = stage.getBoundingClientRect();
  const focusX = focusClientX ?? (rect.left + rect.width / 2);
  const focusY = focusClientY ?? (rect.top + rect.height / 2);
  const imageXBefore = ((focusX - rect.left) + stage.scrollLeft) / (Number(dom.zoom.value || 100) / 100);
  const imageYBefore = ((focusY - rect.top) + stage.scrollTop) / (Number(dom.zoom.value || 100) / 100);
  dom.zoom.value = String(clampedZoom);
  applyZoom();
  const scale = clampedZoom / 100;
  stage.scrollLeft = Math.max(0, imageXBefore * scale - (focusX - rect.left));
  stage.scrollTop = Math.max(0, imageYBefore * scale - (focusY - rect.top));
}

function currentBoundsFromForm() {
  return {
    x: Number(dom.x.value || 0),
    y: Number(dom.y.value || 0),
    width: Number(dom.width.value || 0),
    height: Number(dom.height.value || 0),
  };
}

function updateDraftFromForm() {
  const bounds = currentBoundsFromForm();
  if (bounds.width > 0 && bounds.height > 0) {
    state.draftBounds = bounds;
    renderOverlay();
  }
}

async function saveAnnotation() {
  if (!state.currentFolioId) {
    setStatus('Select a folio first.', true);
    return;
  }
  const payload = {
    id: dom.annotationId.value || undefined,
    folio_id: state.currentFolioId,
    kind: dom.kind.value,
    symbol: dom.symbol.value.trim(),
    quality: dom.quality.value,
    notes: dom.notes.value.trim(),
    bounds_px: currentBoundsFromForm(),
    cleanup_strokes: cloneCleanupStrokes(state.cleanup.strokes),
  };
  try {
    const response = await fetch('/api/annotations', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    state.payload.annotations = data.annotations;
    state.selectedAnnotationId = data.saved.id;
    state.draftBounds = null;
    syncFormFromSelection();
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
    setStatus(`Saved ${data.saved.kind} ${data.saved.symbol}`);
  } catch (error) {
    setStatus(String(error), true);
  }
}

async function deleteAnnotation() {
  if (!state.selectedAnnotationId) {
    setStatus('Select an annotation to delete.', true);
    return;
  }
  try {
    const response = await fetch(`/api/annotations/${encodeURIComponent(state.selectedAnnotationId)}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    state.payload.annotations = data.annotations;
    state.selectedAnnotationId = null;
    state.draftBounds = null;
    syncFormFromSelection();
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
    setStatus('Deleted annotation.');
  } catch (error) {
    setStatus(String(error), true);
  }
}

function bindDraftDrawing() {
  let drag = null;
  dom.overlay.addEventListener('mousedown', (event) => {
    if (!state.currentFolioId || event.button !== 0 || state.panMode) return;
    state.selectedAnnotationId = null;
    dom.annotationId.value = '';
    const rect = dom.overlay.getBoundingClientRect();
    const startX = ((event.clientX - rect.left) / rect.width) * state.naturalWidth;
    const startY = ((event.clientY - rect.top) / rect.height) * state.naturalHeight;
    drag = {startX, startY};
    state.draftBounds = {x: startX, y: startY, width: 1, height: 1};
    renderAnnotations();
    renderOverlay();
    renderMagnifier({x: startX, y: startY});
  });
  window.addEventListener('mousemove', (event) => {
    const rect = dom.overlay.getBoundingClientRect();
    const currentX = ((event.clientX - rect.left) / rect.width) * state.naturalWidth;
    const currentY = ((event.clientY - rect.top) / rect.height) * state.naturalHeight;
    if (
      event.clientX >= rect.left &&
      event.clientX <= rect.right &&
      event.clientY >= rect.top &&
      event.clientY <= rect.bottom
    ) {
      const boundedPoint = {
        x: Math.max(0, Math.min(state.naturalWidth - 1, currentX)),
        y: Math.max(0, Math.min(state.naturalHeight - 1, currentY)),
      };
      magnifier.lastPoint = boundedPoint;
      renderMagnifier(boundedPoint);
    }
    if (!drag) return;
    const x = Math.max(0, Math.min(drag.startX, currentX));
    const y = Math.max(0, Math.min(drag.startY, currentY));
    const width = Math.abs(currentX - drag.startX);
    const height = Math.abs(currentY - drag.startY);
    state.draftBounds = {x, y, width, height};
    applyFormFromBounds(state.draftBounds);
    renderOverlay();
  });
  window.addEventListener('mouseup', () => {
    drag = null;
  });
  dom.overlay.addEventListener('mouseleave', () => {
    renderMagnifier(null);
  });
}

function bindForm() {
  [dom.x, dom.y, dom.width, dom.height].forEach((input) => {
    input.addEventListener('input', updateDraftFromForm);
  });
  dom.saveButton.addEventListener('click', saveAnnotation);
  dom.deleteButton.addEventListener('click', deleteAnnotation);
  dom.clearButton.addEventListener('click', () => {
    state.selectedAnnotationId = null;
    state.draftBounds = null;
    dom.annotationId.value = '';
    dom.notes.value = '';
    dom.symbol.value = '';
    state.cleanup.strokes = [];
    state.cleanup.drawingStroke = null;
    applyFormFromBounds({x: 0, y: 0, width: 0, height: 0});
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
    setStatus('Cleared selection.');
  });
  dom.zoom.addEventListener('input', () => {
    setZoom(Number(dom.zoom.value || 100));
  });
  dom.zoomIn.addEventListener('click', () => setZoom(Number(dom.zoom.value || 100) + 25));
  dom.zoomOut.addEventListener('click', () => setZoom(Number(dom.zoom.value || 100) - 25));
  dom.zoomReset.addEventListener('click', () => setZoom(100));
  dom.panToggle.addEventListener('click', () => {
    state.panMode = !state.panMode;
    renderPanMode();
  });
  dom.cleanupModeErase.addEventListener('click', () => {
    state.cleanup.mode = 'erase';
    renderCleanupEditor();
  });
  dom.cleanupModeRestore.addEventListener('click', () => {
    state.cleanup.mode = 'restore';
    renderCleanupEditor();
  });
  dom.cleanupBrush.addEventListener('input', () => {
    state.cleanup.brushSize = Number(dom.cleanupBrush.value || 10);
    renderCleanupEditor();
  });
  dom.cleanupClear.addEventListener('click', () => {
    state.cleanup.strokes = [];
    state.cleanup.drawingStroke = null;
    renderCleanupEditor();
    setStatus('Cleared cleanup strokes for the selected annotation. Save to persist.');
  });
}

function bindCleanupDrawing() {
  dom.cleanupCleanCanvas.addEventListener('mousedown', (event) => {
    if (event.button !== 0 || !selectedAnnotation()) return;
    const point = cleanupEventToPoint(event);
    if (!point) return;
    state.cleanup.hoverPoint = point;
    state.cleanup.drawingStroke = {
      mode: state.cleanup.mode,
      size_px: state.cleanup.brushSize,
      points: [point],
    };
    cleanup.pointerId = 'mouse';
    renderCleanupEditor();
    event.preventDefault();
  });

  window.addEventListener('mousemove', (event) => {
    if (selectedAnnotation()) {
      state.cleanup.hoverPoint = cleanupEventToPoint(event);
      if (!state.cleanup.drawingStroke) {
        renderCleanupEditor();
      }
    }
    if (!state.cleanup.drawingStroke || cleanup.pointerId !== 'mouse') return;
    const point = cleanupEventToPoint(event);
    if (!point) return;
    state.cleanup.hoverPoint = point;
    state.cleanup.drawingStroke.points.push(point);
    renderCleanupEditor();
  });

  window.addEventListener('mouseup', () => {
    if (!state.cleanup.drawingStroke || cleanup.pointerId !== 'mouse') return;
    state.cleanup.strokes.push(state.cleanup.drawingStroke);
    state.cleanup.drawingStroke = null;
    cleanup.pointerId = null;
    renderCleanupEditor();
    setStatus('Cleanup stroke added. Save annotation to persist.');
  });

  dom.cleanupCleanCanvas.addEventListener('mouseleave', () => {
    state.cleanup.hoverPoint = null;
    if (!state.cleanup.drawingStroke) {
      renderCleanupEditor();
    }
  });
}

function bindViewportGestures() {
  dom.viewerStage.addEventListener(
    'wheel',
    (event) => {
      if (event.ctrlKey || event.metaKey) {
        event.preventDefault();
        const currentZoom = Number(dom.zoom.value || 100);
        const delta = -event.deltaY * 0.05;
        setZoom(currentZoom + delta, event.clientX, event.clientY);
        return;
      }
      event.preventDefault();
      dom.viewerStage.scrollLeft += event.deltaX;
      dom.viewerStage.scrollTop += event.deltaY;
    },
    { passive: false }
  );

  dom.viewerStage.addEventListener('gesturestart', (event) => {
    event.preventDefault();
    viewport.gestureStartZoom = Number(dom.zoom.value || 100);
  });
  dom.viewerStage.addEventListener('gesturechange', (event) => {
    event.preventDefault();
    const baseZoom = viewport.gestureStartZoom ?? Number(dom.zoom.value || 100);
    setZoom(baseZoom * event.scale, event.clientX, event.clientY);
  });
  dom.viewerStage.addEventListener('gestureend', () => {
    viewport.gestureStartZoom = null;
  });

  dom.viewerStage.addEventListener('mousedown', (event) => {
    if (!state.panMode || event.button !== 0) return;
    viewport.panDrag = {
      startX: event.clientX,
      startY: event.clientY,
      scrollLeft: dom.viewerStage.scrollLeft,
      scrollTop: dom.viewerStage.scrollTop,
    };
    dom.viewerStage.classList.add('dragging');
    event.preventDefault();
  });

  window.addEventListener('mousemove', (event) => {
    if (!viewport.panDrag) return;
    const dx = event.clientX - viewport.panDrag.startX;
    const dy = event.clientY - viewport.panDrag.startY;
    dom.viewerStage.scrollLeft = viewport.panDrag.scrollLeft - dx;
    dom.viewerStage.scrollTop = viewport.panDrag.scrollTop - dy;
  });

  window.addEventListener('mouseup', () => {
    viewport.panDrag = null;
    dom.viewerStage.classList.remove('dragging');
  });
}

async function init() {
  const response = await fetch('/api/state');
  state.payload = await response.json();
  magnifier.ctx = dom.magnifierCanvas.getContext('2d');
  cleanup.rawCtx = dom.cleanupRawCanvas.getContext('2d');
  cleanup.cleanCtx = dom.cleanupCleanCanvas.getContext('2d');
  dom.manifestPath.textContent = state.payload.reviewed_manifest_path;
  renderCoverage();
  renderFolios();
  bindForm();
  bindDraftDrawing();
  bindCleanupDrawing();
  bindViewportGestures();
  renderPanMode();
  renderMagnifier(null);
  renderCleanupEditor();
  const first = state.payload.folios[0];
  if (first) {
    loadFolio(first.id);
  }
}

dom.image.addEventListener('load', () => {
  state.naturalWidth = dom.image.naturalWidth || 1;
  state.naturalHeight = dom.image.naturalHeight || 1;
  applyZoom();
  renderOverlay();
  renderCleanupEditor();
});

init().catch((error) => setStatus(String(error), true));
"""


_APP_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reviewed Annotation Workbench</title>
  <link rel="stylesheet" href="/app.css">
</head>
<body>
  <div class="app">
    <aside class="panel">
      <h1>Reviewed Annotation Workbench</h1>
      <div class="meta">Coverage debt and harvested folios for reviewed exemplar labeling.</div>
      <h2>Coverage</h2>
      <div id="coverage-summary"></div>
      <h3>Needs Reviewed Samples</h3>
      <div id="coverage-debt" class="debt-list"></div>
      <h2>Folios</h2>
      <div id="folio-list" class="folio-list"></div>
    </aside>
    <main class="viewer">
      <div class="viewer-toolbar">
        <div>
          <h2 id="folio-title">Select a folio</h2>
          <div id="folio-meta" class="meta"></div>
        </div>
        <div class="viewer-controls">
          <button id="zoom-out" type="button">-</button>
          <button id="zoom-in" type="button">+</button>
          <button id="zoom-reset" type="button">Reset</button>
          <button id="pan-toggle" type="button" aria-pressed="false">Pan: off</button>
          <label>
            Zoom
            <input id="zoom" type="range" min="50" max="500" value="100">
            <span id="zoom-value" class="small">100%</span>
          </label>
        </div>
      </div>
      <div class="viewer-stage">
        <div class="canvas-wrap">
          <img id="folio-image" alt="Selected folio">
          <div id="overlay" class="overlay"></div>
        </div>
      </div>
    </main>
    <aside class="panel">
      <h2>Annotation Editor</h2>
      <div class="meta">Draw a rectangle on the folio, then save a glyph or join label.</div>
      <div class="magnifier">
        <div class="magnifier-head">
          <h2>Magnifier</h2>
          <div id="magnifier-meta" class="magnifier-meta">No cursor sample</div>
        </div>
        <canvas id="magnifier-canvas" width="240" height="240"></canvas>
      </div>
      <div class="small">Reviewed manifest:</div>
      <div id="manifest-path" class="small"></div>
      <input id="annotation-id" type="hidden">
      <label>Kind
        <select id="kind">
          <option value="glyph">glyph</option>
          <option value="join">join</option>
        </select>
      </label>
      <label>Symbol
        <input id="symbol" type="text" placeholder="e or d->e">
      </label>
      <label>Quality
        <select id="quality">
          <option value="trusted">trusted</option>
          <option value="usable" selected>usable</option>
          <option value="uncertain">uncertain</option>
        </select>
      </label>
      <div class="grid2">
        <label>X
          <input id="x" type="number" min="0" step="1" value="0">
        </label>
        <label>Y
          <input id="y" type="number" min="0" step="1" value="0">
        </label>
        <label>Width
          <input id="width" type="number" min="0" step="1" value="0">
        </label>
        <label>Height
          <input id="height" type="number" min="0" step="1" value="0">
        </label>
      </div>
      <label>Notes
        <textarea id="notes" placeholder="Optional note about form, clarity, or join behavior"></textarea>
      </label>
      <div class="actions">
        <button id="save-annotation" class="primary">Save Annotation</button>
        <button id="delete-annotation" class="danger" type="button">Delete Selected</button>
        <button id="clear-selection" type="button">Clear</button>
      </div>
      <h2>Cleanup Editor</h2>
      <div id="cleanup-meta" class="meta">Select a saved annotation to clean nearby artifacts.</div>
      <div class="cleanup-toolbar">
        <button id="cleanup-mode-erase" type="button" class="active">Erase</button>
        <button id="cleanup-mode-restore" type="button">Restore</button>
        <label>
          Brush
          <input id="cleanup-brush" type="range" min="2" max="48" value="10">
          <span id="cleanup-brush-value" class="small">10px</span>
        </label>
        <button id="cleanup-clear" type="button">Clear Cleanup</button>
      </div>
      <div class="cleanup-grid">
        <div class="cleanup-card">
          <h3>Raw Crop</h3>
          <canvas id="cleanup-raw-canvas" class="cleanup-canvas" width="240" height="240"></canvas>
        </div>
        <div class="cleanup-card">
          <h3>Cleaned Preview</h3>
          <canvas id="cleanup-clean-canvas" class="cleanup-canvas" width="240" height="240"></canvas>
        </div>
      </div>
      <div id="status" class="status"></div>
      <h2>Annotations On This Folio</h2>
      <div id="annotation-list" class="annotation-list"></div>
    </aside>
  </div>
  <script src="/app.js"></script>
</body>
</html>
"""


class _WorkbenchHandler(BaseHTTPRequestHandler):
    server_version = "ScribeSimAnnotate/0.1"

    @property
    def workbench(self) -> ReviewedAnnotationWorkbench:
        return self.server.workbench  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _send_json(self, payload: Any, *, status: int = 200) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, body: str, *, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_bytes(self, body: bytes, *, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_text(_APP_HTML, content_type="text/html; charset=utf-8")
            return
        if parsed.path == "/app.css":
            self._send_text(_APP_CSS, content_type="text/css; charset=utf-8")
            return
        if parsed.path == "/app.js":
            self._send_text(_APP_JS, content_type="application/javascript; charset=utf-8")
            return
        if parsed.path == "/api/state":
            self._send_json(self.workbench.get_state())
            return
        if parsed.path.startswith("/api/folio-image/"):
            folio_id = parsed.path.rsplit("/", 1)[-1]
            try:
                body, content_type = self.workbench.read_folio_image(folio_id)
            except Exception as exc:  # pragma: no cover - defensive server error
                self._send_text(str(exc), status=404)
                return
            self._send_bytes(body, content_type=content_type)
            return
        self._send_text("not found", status=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/annotations":
            self._send_text("not found", status=404)
            return
        try:
            payload = self._read_json_body()
            saved = self.workbench.save_annotation(payload)
            self._send_json({"saved": saved, "annotations": self.workbench.list_annotations()})
        except Exception as exc:
            self._send_text(str(exc), status=400)

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/annotations/"):
            self._send_text("not found", status=404)
            return
        annotation_id = parsed.path.rsplit("/", 1)[-1]
        deleted = self.workbench.delete_annotation(annotation_id)
        if not deleted:
            self._send_text("annotation not found", status=404)
            return
        self._send_json({"deleted": annotation_id, "annotations": self.workbench.list_annotations()})


class AnnotationWorkbenchServer:
    """Thin wrapper around the local reviewed-annotation HTTP server."""

    def __init__(
        self,
        *,
        coverage_ledger_path: Path | str,
        output_root: Path | str,
        reviewed_manifest_path: Path | str | None = None,
        selection_manifest_path: Path | str | None = None,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self.workbench = ReviewedAnnotationWorkbench(
            coverage_ledger_path=coverage_ledger_path,
            output_root=output_root,
            reviewed_manifest_path=reviewed_manifest_path,
            selection_manifest_path=selection_manifest_path,
        )
        self.httpd = ThreadingHTTPServer((host, port), _WorkbenchHandler)
        self.httpd.workbench = self.workbench  # type: ignore[attr-defined]
        self.host = host
        self.port = int(self.httpd.server_address[1])

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def serve_forever(self) -> None:
        self.httpd.serve_forever()

    def shutdown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def serve_reviewed_annotation_workbench(
    *,
    coverage_ledger_path: Path | str = DEFAULT_COVERAGE_LEDGER_PATH,
    output_root: Path | str = DEFAULT_REVIEWED_ANNOTATION_OUTPUT_ROOT,
    reviewed_manifest_path: Path | str | None = None,
    selection_manifest_path: Path | str | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> dict[str, Any]:
    """Start the reviewed-annotation workbench and block until interrupted."""
    server = AnnotationWorkbenchServer(
        coverage_ledger_path=coverage_ledger_path,
        output_root=output_root,
        reviewed_manifest_path=reviewed_manifest_path,
        selection_manifest_path=selection_manifest_path,
        host=host,
        port=port,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
    return {
        "url": server.url,
        "reviewed_manifest_path": server.workbench.reviewed_manifest_path,
        "coverage_ledger_path": server.workbench.coverage_ledger_path,
        "selection_manifest_path": server.workbench.selection_manifest_path,
    }
