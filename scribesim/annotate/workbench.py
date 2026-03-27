"""Local reviewed-annotation workbench for TD-014."""

from __future__ import annotations

import json
import mimetypes
import re
import threading
import tomllib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from PIL import Image

from scribesim.annotate.freeze import freeze_reviewed_exemplars
from scribesim.evo.genome import BezierSegment
from scribesim.evofit.workflow import EvofitConfig, run_reviewed_evofit
from scribesim.pathguide.io import write_pathguides_toml
from scribesim.pathguide.model import DensePathGuide
from scribesim.pathguide.review import write_guide_overlay_snapshot, write_nominal_guide_snapshot
from scribesim.pathguide.freeze import freeze_reviewed_evofit_guides

DEFAULT_COVERAGE_LEDGER_PATH = Path(
    "shared/training/handsim/reviewed_annotations/coverage_ledger_v1/coverage_ledger.json"
)
DEFAULT_REVIEWED_ANNOTATION_OUTPUT_ROOT = Path("shared/training/handsim/reviewed_annotations/workbench_v1")
_REPO_ROOT = Path(__file__).resolve().parents[2]

_CROP_CANVAS_RE = re.compile(r"^.+?_\d{3}_(?P<canvas>.+)_l\d+_w\d+_c\d+\.png$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_toml(path: Path | str) -> dict[str, Any]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def _load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sanitize_fragment(label: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in str(label))
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_") or "item"


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


def _resolve_optional_path(path: str | Path | None, *, relative_to: Path | None = None) -> Path | None:
    if path in {None, ""}:
        return None
    resolved = _resolve_path(str(path), relative_to=relative_to)
    return resolved if resolved.exists() else None


def _safe_id(prefix: str, value: str) -> str:
    sanitized = "".join(ch if ch.isalnum() else "_" for ch in value).strip("_").lower()
    sanitized = "_".join(part for part in sanitized.split("_") if part)
    return f"{prefix}_{sanitized or 'item'}"


def _pathguide_symbol_slug(symbol: str) -> str:
    return str(symbol).replace("->", "_to_").replace("/", "_").replace(" ", "_")


def _symbol_status_key(kind: str, symbol: str) -> str:
    return f"{str(kind)}:{str(symbol)}"


def _failure_metric_name(reason: str) -> str:
    if "=" in reason:
        return reason.split("=", 1)[0].strip()
    return reason.strip()


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    kept: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        kept.append(text)
        seen.add(text)
    return kept


def _artifact_payload(path: str | Path | None, *, allowed_roots: tuple[Path, ...] = (_REPO_ROOT,)) -> dict[str, Any] | None:
    if not path:
        return None
    resolved = _resolve_optional_path(path, relative_to=_REPO_ROOT)
    if resolved is None:
        return None
    relative = None
    for root in allowed_roots:
        try:
            relative = resolved.relative_to(root.resolve())
            break
        except ValueError:
            continue
    if relative is None:
        return None
    content_type, _ = mimetypes.guess_type(resolved.name)
    return {
        "path": resolved.as_posix(),
        "label": relative.as_posix(),
        "url": f"/api/artifact?path={resolved.as_posix()}",
        "content_type": content_type or "application/octet-stream",
        "is_image": (content_type or "").startswith("image/"),
    }


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


def _normalize_manual_point(point: dict[str, Any]) -> dict[str, float]:
    return {
        "x": float(point["x"]),
        "y": float(point["y"]),
    }


def _normalize_manual_segments(
    segments: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    if not segments:
        return normalized
    for index, segment in enumerate(segments):
        stroke_order = int(round(float(segment.get("stroke_order", index + 1))))
        points = {}
        for key in ("p0", "p1", "p2", "p3"):
            if key not in segment:
                raise ValueError(f"manual guide segment missing {key}")
            points[key] = _normalize_manual_point(dict(segment[key]))
        normalized.append(
            {
                "stroke_order": max(1, stroke_order),
                "contact": bool(segment.get("contact", True)),
                "p0": points["p0"],
                "p1": points["p1"],
                "p2": points["p2"],
                "p3": points["p3"],
            }
        )
    normalized.sort(key=lambda item: (item["stroke_order"], item["p0"]["x"], item["p0"]["y"]))
    return normalized


def _entry_to_payload(entry: dict[str, Any]) -> dict[str, Any]:
    payload = dict(entry)
    payload["bounds_px"] = dict(entry.get("bounds_px", {}))
    payload["reviewed_source_paths"] = list(entry.get("reviewed_source_paths", []))
    payload["cleanup_strokes"] = _normalize_cleanup_strokes(entry.get("cleanup_strokes", []))
    payload["catalog_included"] = bool(entry.get("catalog_included", True))
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
                f"catalog_included = {'true' if bool(entry.get('catalog_included', True)) else 'false'}",
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
        self.symbol_rerun_root = (self.output_root / "symbol_reruns").resolve()
        self.symbol_rerun_root.mkdir(parents=True, exist_ok=True)
        self._symbol_reruns: dict[str, dict[str, Any]] = {}
        self.manual_guide_root = (self.output_root / "manual_guides_v1").resolve()
        self.manual_guide_root.mkdir(parents=True, exist_ok=True)
        self.manual_guide_manifest_path = self.manual_guide_root / "manual_guides.json"
        if self.manual_guide_manifest_path.exists():
            self.manual_guides = _load_json(self.manual_guide_manifest_path)
        else:
            self.manual_guides = {
                "schema_version": 1,
                "manifest_kind": "manual_guides",
                "created_by": "annotate-workbench",
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
                "entry_count": 0,
                "entries": [],
            }
            self._write_manual_guides()

        self.ledger = _load_json(self.coverage_ledger_path)
        self.corpus_manifest_path = _resolve_path(self.ledger["corpus_manifest_path"])
        corpus_manifest = _load_toml(self.corpus_manifest_path)
        self.corpus_manifest = corpus_manifest
        self._corpus_entries = {
            (str(entry.get("kind", "")), str(entry.get("symbol", ""))): dict(entry)
            for entry in corpus_manifest.get("entries", [])
            if str(entry.get("kind", "")) in {"glyph", "join"} and str(entry.get("symbol", ""))
        }

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
        self._folios_by_source_path = {
            Path(folio["local_path"]).resolve().as_posix(): folio
            for folio in self.folios
        }
        self._folios_by_canvas_slug = {
            _sanitize_fragment(folio["canvas_label"]): folio
            for folio in self.folios
        }

        promoted_manifest_path = _resolve_optional_path(
            corpus_manifest.get("promoted_manifest_path"),
            relative_to=self.corpus_manifest_path.parent,
        )
        self.promoted_manifest = _load_toml(promoted_manifest_path) if promoted_manifest_path else {}
        self._promoted_entries = {
            (str(entry.get("kind", "")), str(entry.get("symbol", ""))): dict(entry)
            for entry in self.promoted_manifest.get("entries", [])
            if str(entry.get("kind", "")) in {"glyph", "join"} and str(entry.get("symbol", ""))
        }

        promotion_gate_report_path = _resolve_optional_path(
            corpus_manifest.get("promotion_gate_report_json_path"),
            relative_to=self.corpus_manifest_path.parent,
        )
        self.promotion_gate_report = _load_json(promotion_gate_report_path) if promotion_gate_report_path else {}

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

    def _write_manual_guides(self) -> None:
        self.manual_guides["entry_count"] = len(self.manual_guides.get("entries", []))
        self.manual_guides["updated_at"] = _utc_now()
        self.manual_guide_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manual_guide_manifest_path.write_text(
            json.dumps(self.manual_guides, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _annotation_by_id(self, annotation_id: str) -> dict[str, Any] | None:
        for entry in self.reviewed_manifest.get("entries", []):
            if str(entry.get("id", "")) == str(annotation_id):
                return _entry_to_payload(entry)
        return None

    def _crop_annotation_image(self, annotation: dict[str, Any], destination: Path, *, padding_px: int = 0) -> Path:
        source_path = Path(str(annotation.get("source_path", "")))
        bounds = dict(annotation.get("bounds_px", {}))
        destination.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source_path) as image:
            cropped = image.crop(
                (
                    int(bounds.get("x", 0)),
                    int(bounds.get("y", 0)),
                    int(bounds.get("x", 0)) + int(bounds.get("width", 0)),
                    int(bounds.get("y", 0)) + int(bounds.get("height", 0)),
                )
            )
            if padding_px > 0:
                canvas = Image.new(cropped.mode, (cropped.width + padding_px * 2, cropped.height + padding_px * 2), color="white")
                canvas.paste(cropped, (padding_px, padding_px))
                canvas.save(destination)
            else:
                cropped.save(destination)
        return destination

    def _manual_guide_payload(self, entry: dict[str, Any]) -> dict[str, Any]:
        payload = dict(entry)
        payload["bounds_px"] = dict(entry.get("bounds_px", {}))
        payload["segments"] = _normalize_manual_segments(entry.get("segments", []))
        payload["validation_errors"] = list(entry.get("validation_errors", []))
        payload["preview_artifacts"] = {
            name: artifact
            for name, artifact in {
                "overlay": _artifact_payload(
                    entry.get("preview_overlay_path"),
                    allowed_roots=(_REPO_ROOT, self.output_root, self.manual_guide_root),
                ),
                "nominal": _artifact_payload(
                    entry.get("preview_nominal_path"),
                    allowed_roots=(_REPO_ROOT, self.output_root, self.manual_guide_root),
                ),
                "source_crop": _artifact_payload(
                    entry.get("source_crop_path"),
                    allowed_roots=(_REPO_ROOT, self.output_root, self.manual_guide_root),
                ),
            }.items()
            if artifact is not None
        }
        return payload

    def _manual_guide_entries_for(self, kind: str, symbol: str) -> list[dict[str, Any]]:
        entries = [
            dict(entry)
            for entry in self.manual_guides.get("entries", [])
            if str(entry.get("kind", "")) == str(kind) and str(entry.get("symbol", "")) == str(symbol)
        ]
        entries.sort(key=lambda item: str(item.get("updated_at", "")), reverse=True)
        entries.sort(key=lambda item: 0 if bool(item.get("active", False)) else 1)
        return entries

    def _manual_guide_groups(self) -> dict[str, dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for entry in self.manual_guides.get("entries", []):
            key = _symbol_status_key(str(entry.get("kind", "")), str(entry.get("symbol", "")))
            if key == ":":
                continue
            grouped[key].append(dict(entry))
        result: dict[str, dict[str, Any]] = {}
        for key, entries in grouped.items():
            entries.sort(key=lambda item: str(item.get("updated_at", "")), reverse=True)
            active_entry = next((entry for entry in entries if bool(entry.get("active", False))), entries[0] if entries else None)
            result[key] = {
                "active_id": str(active_entry.get("id", "")) if active_entry else "",
                "entries": [self._manual_guide_payload(entry) for entry in entries],
            }
            if active_entry is not None:
                result[key]["active"] = self._manual_guide_payload(active_entry)
        return result

    def _manual_guides_by_symbol(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for key, group in self._manual_guide_groups().items():
            active = group.get("active")
            if isinstance(active, dict):
                result[key] = active
        return result

    def _build_manual_dense_guide(self, entry: dict[str, Any]) -> DensePathGuide:
        x_height_px = float(entry.get("x_height_px", 0.0) or 0.0)
        if x_height_px <= 0.0:
            raise ValueError("manual guide x_height_px must be > 0")
        x_height_mm = float(entry.get("x_height_mm", EvofitConfig().x_height_mm) or EvofitConfig().x_height_mm)
        annotation = self._annotation_by_id(str(entry.get("annotation_id", "")))
        if annotation is None:
            raise ValueError(f"manual guide annotation not found: {entry.get('annotation_id', '')}")
        crop_height = float(annotation["bounds_px"]["height"])
        crop_width = float(annotation["bounds_px"]["width"])
        if crop_height <= 0.0 or crop_width <= 0.0:
            raise ValueError("manual guide annotation bounds must be positive")
        segments: list[BezierSegment] = []
        for segment in _normalize_manual_segments(entry.get("segments", [])):
            def transform(point: dict[str, float]) -> tuple[float, float]:
                return (float(point["x"]), crop_height - float(point["y"]))

            segments.append(
                BezierSegment(
                    p0=transform(segment["p0"]),
                    p1=transform(segment["p1"]),
                    p2=transform(segment["p2"]),
                    p3=transform(segment["p3"]),
                    contact=bool(segment.get("contact", True)),
                )
            )
        if not segments:
            raise ValueError("manual guide must include at least one cubic segment")

        from scribesim.pathguide.io import guide_from_trace_segments

        guide = guide_from_trace_segments(
            str(entry["symbol"]),
            segments,
            x_height_px=x_height_px,
            x_height_mm=x_height_mm,
            kind=str(entry.get("kind", "glyph")),
            default_corridor_half_width_mm=float(entry.get("corridor_half_width_mm", 0.2) or 0.2),
            source_id=f"manual-guide:{entry['symbol']}",
            source_path=str(entry.get("source_crop_path", "")),
            extraction_run="ADV-SS-ANNOTATE-MANUAL-GUIDE",
            confidence_tier="accepted",
            split="validation",
        )
        x_advance_px = float(entry.get("x_advance_px", crop_width) or crop_width)
        if x_advance_px <= 0.0:
            raise ValueError("manual guide x_advance_px must be > 0")
        return DensePathGuide(
            symbol=guide.symbol,
            kind=guide.kind,
            samples=guide.samples,
            x_advance_mm=(x_advance_px / x_height_px) * x_height_mm,
            x_height_mm=guide.x_height_mm,
            entry_tangent=guide.entry_tangent,
            exit_tangent=guide.exit_tangent,
            sources=guide.sources,
        )

    def _write_manual_guide_previews(self, entry: dict[str, Any]) -> dict[str, str]:
        guide = self._build_manual_dense_guide(entry)
        guide_root = (self.manual_guide_root / str(entry["id"])).resolve()
        guide_root.mkdir(parents=True, exist_ok=True)
        overlay_path = write_guide_overlay_snapshot(guide, guide_root / "overlay.png")
        nominal_path = write_nominal_guide_snapshot(guide, guide_root / "nominal.png")
        source_crop_raw = str(entry.get("source_crop_path", "")).strip()
        source_crop_path = Path(source_crop_raw) if source_crop_raw else guide_root / "source_crop.png"
        if not source_crop_raw or not source_crop_path.exists():
            annotation = self._annotation_by_id(str(entry.get("annotation_id", "")))
            if annotation is None:
                raise ValueError(f"manual guide annotation not found: {entry.get('annotation_id', '')}")
            source_crop_path = self._crop_annotation_image(
                annotation,
                guide_root / "source_crop.png",
                padding_px=int(float(entry.get("canvas_padding_px", 0.0) or 0.0)),
            )
        catalog_path = guide_root / "manual_proposal_guides.toml"
        write_pathguides_toml({guide.symbol: guide}, catalog_path)
        return {
            "guide_catalog_path": catalog_path.as_posix(),
            "preview_overlay_path": overlay_path.as_posix(),
            "preview_nominal_path": nominal_path.as_posix(),
            "source_crop_path": source_crop_path.as_posix(),
        }

    def _reviewed_entries_by_symbol(self, *, catalog_only: bool = False) -> dict[tuple[str, str], list[dict[str, Any]]]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for entry in self.reviewed_manifest.get("entries", []):
            kind = str(entry.get("kind", ""))
            symbol = str(entry.get("symbol", ""))
            if not kind or not symbol:
                continue
            if catalog_only and not bool(entry.get("catalog_included", True)):
                continue
            grouped[(kind, symbol)].append(_entry_to_payload(entry))
        return grouped

    def _live_coverage_entries(self) -> list[dict[str, Any]]:
        reviewed_entries = self._reviewed_entries_by_symbol(catalog_only=True)
        reviewed_entries_all = self._reviewed_entries_by_symbol(catalog_only=False)
        reviewed_manuscripts: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
        for key, entries in reviewed_entries.items():
            counts: dict[str, int] = defaultdict(int)
            for entry in entries:
                manuscript = str(entry.get("source_manuscript_label", "unknown"))
                counts[manuscript] += 1
            reviewed_manuscripts[key] = dict(counts)

        live_entries: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str]] = set()
        for entry in self.ledger.get("entries", []):
            kind = str(entry.get("kind", ""))
            symbol = str(entry.get("symbol", ""))
            key = (kind, symbol)
            seen_keys.add(key)
            corpus_entry = self._corpus_entries.get(key, {})
            by_manuscript = {
                tier: dict(values)
                for tier, values in dict(entry.get("by_manuscript", {})).items()
            }
            by_manuscript["reviewed"] = dict(reviewed_manuscripts.get(key, {}))
            live_entry = dict(entry)
            live_entry["reviewed_count"] = len(reviewed_entries.get(key, []))
            live_entry["reviewed_total_count"] = len(reviewed_entries_all.get(key, []))
            live_entry["reviewed_excluded_count"] = max(
                0, live_entry["reviewed_total_count"] - live_entry["reviewed_count"]
            )
            live_entry["missing_reviewed"] = int(live_entry["reviewed_count"] == 0)
            live_entry["repair_only_count"] = int(
                corpus_entry.get("repair_only_count", live_entry.get("repair_only_count", 0))
            )
            live_entry["by_manuscript"] = by_manuscript
            live_entries.append(live_entry)
        extra_keys = set(reviewed_entries_all) | {
            (str(entry.get("kind", "")), str(entry.get("symbol", "")))
            for entry in self.manual_guides.get("entries", [])
            if str(entry.get("kind", "")) and str(entry.get("symbol", ""))
        }
        for kind, symbol in sorted(extra_keys - seen_keys):
            key = (kind, symbol)
            corpus_entry = self._corpus_entries.get(key, {})
            promoted_entry = self._promoted_entries.get(key, {})
            by_manuscript = {
                "auto_admitted": {},
                "quarantined": {},
                "rejected": {},
                "promoted": {},
                "reviewed": dict(reviewed_manuscripts.get(key, {})),
            }
            for tier in ("auto_admitted", "quarantined", "rejected"):
                counts: dict[str, int] = defaultdict(int)
                for path in corpus_entry.get(f"{tier}_paths", []):
                    folio = self._folio_from_crop_path(str(path))
                    manuscript = (
                        str(folio.get("source_manuscript_label", "unknown"))
                        if folio is not None
                        else "unknown"
                    )
                    counts[manuscript] += 1
                by_manuscript[tier] = dict(counts)
            promoted_counts: dict[str, int] = defaultdict(int)
            for path in promoted_entry.get("promoted_exemplar_source_paths", []):
                folio = self._folio_from_source_path(str(path))
                manuscript = (
                    str(folio.get("source_manuscript_label", "unknown"))
                    if folio is not None
                    else "unknown"
                )
                promoted_counts[manuscript] += 1
            by_manuscript["promoted"] = dict(promoted_counts)
            reviewed_count = len(reviewed_entries.get(key, []))
            reviewed_total_count = len(reviewed_entries_all.get(key, []))
            live_entries.append(
                {
                    "kind": kind,
                    "symbol": symbol,
                    "auto_admitted_count": int(corpus_entry.get("auto_admitted_count", 0)),
                    "quarantined_count": int(corpus_entry.get("quarantined_count", 0)),
                    "rejected_count": int(corpus_entry.get("rejected_count", 0)),
                    "promoted_count": sum(promoted_counts.values()),
                    "reviewed_count": reviewed_count,
                    "reviewed_total_count": reviewed_total_count,
                    "reviewed_excluded_count": max(0, reviewed_total_count - reviewed_count),
                    "missing_reviewed": int(reviewed_count == 0),
                    "coverage_promoted": bool(corpus_entry.get("coverage_promoted", False)),
                    "repair_only_count": int(corpus_entry.get("repair_only_count", 0)),
                    "by_manuscript": by_manuscript,
                }
            )
        live_entries.sort(key=lambda item: (str(item.get("kind", "")), str(item.get("symbol", ""))))
        return live_entries

    def _live_coverage_summary(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        summary = dict(self.ledger.get("summary", {}))
        glyph_entries = [entry for entry in entries if entry.get("kind") == "glyph"]
        join_entries = [entry for entry in entries if entry.get("kind") == "join"]
        glyph_missing_reviewed = [entry["symbol"] for entry in glyph_entries if int(entry.get("missing_reviewed", 0)) == 1]
        join_missing_reviewed = [entry["symbol"] for entry in join_entries if int(entry.get("missing_reviewed", 0)) == 1]
        summary["glyph_reviewed_coverage"] = 1.0 - (len(glyph_missing_reviewed) / max(len(glyph_entries), 1))
        summary["join_reviewed_coverage"] = 1.0 - (len(join_missing_reviewed) / max(len(join_entries), 1))
        summary["glyph_missing_reviewed"] = glyph_missing_reviewed
        summary["join_missing_reviewed"] = join_missing_reviewed
        return summary

    def _promotion_decisions_for(self, kind: str, symbol: str) -> list[dict[str, Any]]:
        section = "glyphs" if kind == "glyph" else "joins"
        decisions = self.promotion_gate_report.get(section, {})
        if not isinstance(decisions, dict):
            return []
        raw = decisions.get(symbol, [])
        return [dict(entry) for entry in raw if isinstance(entry, dict)]

    def _folio_from_source_path(self, path: str) -> dict[str, Any] | None:
        resolved = _resolve_optional_path(path, relative_to=self.corpus_manifest_path.parent)
        if not resolved:
            return None
        return self._folios_by_source_path.get(resolved.as_posix())

    def _folio_from_crop_path(self, path: str) -> dict[str, Any] | None:
        match = _CROP_CANVAS_RE.match(Path(path).name)
        if not match:
            return None
        return self._folios_by_canvas_slug.get(match.group("canvas"))

    def _sample_ref(
        self,
        *,
        tier: str,
        detail: str,
        path: str,
        folio: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if folio is not None:
            label = f"{folio['source_manuscript_label']} • {folio['canvas_label']}"
            folio_id = folio["id"]
        else:
            label = Path(path).name
            folio_id = None
        return {
            "tier": tier,
            "label": label,
            "detail": detail,
            "folio_id": folio_id,
            "path": str(path),
        }

    def _guidance_for_reason(self, kind: str, reason: str) -> str | None:
        metric = _failure_metric_name(reason)
        if metric == "competitor_margin":
            return (
                "Choose a form whose distinguishing strokes make it less confusable with nearby symbols."
            )
        if metric == "self_ncc_score":
            return "Prefer a canonical, well-formed instance instead of an ornate, damaged, or highly idiosyncratic variant."
        if metric == "cluster_consistency":
            return "Prefer a form that matches the common shape family already seen for this symbol."
        if metric == "cluster_separation":
            return "Pick an example whose geometry is clearly separated from neighboring symbols, not a borderline look-alike."
        if metric == "occupancy_balance_score":
            return (
                "Crop tightly enough to include the full inked form, but avoid extra blank margin or neighboring ink that distorts the foreground balance."
            )
        return None

    def _build_symbol_status(
        self,
        entry: dict[str, Any],
        reviewed_entries: list[dict[str, Any]],
        all_reviewed_entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        kind = str(entry.get("kind", ""))
        symbol = str(entry.get("symbol", ""))
        counts = {
            "auto_admitted": int(entry.get("auto_admitted_count", 0)),
            "quarantined": int(entry.get("quarantined_count", 0)),
            "rejected": int(entry.get("rejected_count", 0)),
            "repair_only": int(entry.get("repair_only_count", 0)),
            "promoted": int(entry.get("promoted_count", 0)),
            "reviewed": int(entry.get("reviewed_count", 0)),
            "reviewed_excluded": max(0, len(all_reviewed_entries) - len(reviewed_entries)),
        }
        corpus_entry = self._corpus_entries.get((kind, symbol), {})
        promoted_entry = self._promoted_entries.get((kind, symbol), {})
        decisions = self._promotion_decisions_for(kind, symbol)
        pass_count = sum(1 for decision in decisions if bool(decision.get("passed")))
        fail_count = max(0, len(decisions) - pass_count)

        stage_statuses: list[dict[str, Any]] = []
        if any(counts[tier] > 0 for tier in ("auto_admitted", "quarantined", "rejected", "repair_only")):
            parts = []
            for tier in ("auto_admitted", "quarantined", "rejected", "repair_only"):
                if counts[tier]:
                    parts.append(f"{counts[tier]} {tier.replace('_', ' ')}")
            stage_statuses.append(
                {
                    "stage": "Automatic corpus",
                    "status": "available",
                    "detail": ", ".join(parts),
                }
            )
        else:
            stage_statuses.append(
                {
                    "stage": "Automatic corpus",
                    "status": "missing",
                    "detail": "No automatic candidates recorded for this symbol on the current review slice.",
                }
            )

        if counts["promoted"] > 0:
            stage_statuses.append(
                {
                    "stage": "Promotion gate",
                    "status": "passed",
                    "detail": f"{counts['promoted']} promoted exemplar(s) available; {len(decisions)} candidate(s) evaluated, {pass_count} passed.",
                }
            )
        elif decisions:
            stage_statuses.append(
                {
                    "stage": "Promotion gate",
                    "status": "blocked",
                    "detail": f"{len(decisions)} candidate(s) evaluated, {fail_count} blocked, 0 promoted.",
                }
            )
        elif counts["auto_admitted"] > 0:
            stage_statuses.append(
                {
                    "stage": "Promotion gate",
                    "status": "unknown",
                    "detail": "Auto-admitted candidates exist, but no structured promotion decision was recorded.",
                }
            )
        else:
            stage_statuses.append(
                {
                    "stage": "Promotion gate",
                    "status": "unavailable",
                    "detail": "No auto-admitted candidate was available for promotion.",
                }
            )

        stage_statuses.append(
            {
                "stage": "Reviewed catalog",
                "status": "complete" if counts["reviewed"] > 0 else "needed",
                "detail": (
                    f"{counts['reviewed']} active reviewed annotation(s) saved."
                    + (
                        f" {counts['reviewed_excluded']} excluded from catalog."
                        if counts["reviewed_excluded"] > 0
                        else ""
                    )
                    if counts["reviewed"] > 0
                    else (
                        f"No active reviewed annotation saved. {counts['reviewed_excluded']} excluded reference(s) exist."
                        if counts["reviewed_excluded"] > 0
                        else "No reviewed annotation saved yet."
                    )
                ),
            }
        )

        aggregated_failures = Counter(
            str(failure)
            for decision in decisions
            if not bool(decision.get("passed"))
            for failure in decision.get("failures", [])
        )
        blockers: list[dict[str, Any]] = []
        for reason, count in aggregated_failures.items():
            blockers.append(
                {
                    "source": "promotion_gate",
                    "text": reason,
                    "count": int(count),
                }
            )
        if counts["repair_only"] > 0:
            blockers.append(
                {
                    "source": "repair_only",
                    "text": (
                        f"{counts['repair_only']} repair-only candidate(s) exist for coverage accounting, "
                        "but repair-only samples are non-reviewable and cannot enter the catalog."
                    ),
                    "count": counts["repair_only"],
                }
            )
        if (counts["quarantined"] > 0 or counts["rejected"] > 0) and not aggregated_failures:
            blockers.append(
                {
                    "source": "automatic_corpus",
                    "text": (
                        f"Automatic corpus recorded {counts['quarantined']} quarantined and {counts['rejected']} rejected "
                        "candidate(s), but no structured blocker reasons were preserved for those tiers."
                    ),
                    "count": counts["quarantined"] + counts["rejected"],
                }
            )
        if counts["auto_admitted"] == 0 and not decisions:
            blockers.append(
                {
                    "source": "automatic_corpus",
                    "text": "No auto-admitted candidate exists for this symbol on the current review slice.",
                    "count": 0,
                }
            )
        if counts["reviewed"] == 0 and counts["reviewed_excluded"] > 0:
            blockers.append(
                {
                    "source": "reviewed_catalog",
                    "text": (
                        f"All reviewed references for this symbol are currently excluded from the catalog. "
                        "Restore at least one reference before rerunning reviewed evofit."
                    ),
                    "count": counts["reviewed_excluded"],
                }
            )

        guidance = [
            "Select a clean, high-confidence example with the full intended form visible.",
        ]
        if kind == "glyph":
            guidance.extend(
                [
                    "Keep the crop focused on one glyph and avoid neighboring letters, punctuation, or flourish strokes.",
                    "Do not clip ascenders, descenders, entry strokes, or exit strokes that define the glyph shape.",
                ]
            )
        else:
            guidance.extend(
                [
                    "Include the full connection between both letters, not only the midpoint of the join.",
                    "Keep enough of each adjoining letter visible that the join identity is unambiguous.",
                ]
            )
        if counts["auto_admitted"] == 0:
            guidance.append("Search the harvested folios for a fresh example; nothing automatic was found to seed promotion for this symbol.")
        if counts["repair_only"] > 0:
            guidance.append("Prefer a naturally readable exemplar, not a repair-only backfill used only for coverage accounting.")
        if counts["reviewed_excluded"] > 0:
            guidance.append("Open the reference catalog for this symbol and restore only the reviewed samples you want freeze and evofit to consider.")
        for reason in aggregated_failures:
            derived = self._guidance_for_reason(kind, reason)
            if derived:
                guidance.append(derived)
        if counts["promoted"] > 0 and counts["reviewed"] == 0:
            guidance.append("Use the promoted exemplar as a reference shape, but add a reviewed annotation with exact source bounds and quality.")
        guidance = _dedupe_strings(guidance)

        sample_refs: list[dict[str, Any]] = []
        seen_sample_keys: set[tuple[str, str, str]] = set()

        def add_sample(sample: dict[str, Any]) -> None:
            sample_key = (str(sample["tier"]), str(sample["label"]), str(sample["detail"]))
            if sample_key in seen_sample_keys or len(sample_refs) >= 8:
                return
            sample_refs.append(sample)
            seen_sample_keys.add(sample_key)

        for path in promoted_entry.get("promoted_exemplar_source_paths", [])[:3]:
            folio = self._folio_from_source_path(str(path))
            add_sample(
                self._sample_ref(
                    tier="promoted",
                    detail="promoted exemplar source",
                    path=str(path),
                    folio=folio,
                )
            )

        for decision in decisions[:3]:
            folio = self._folio_from_source_path(str(decision.get("source_path", "")))
            decision_detail = (
                f"promotion candidate rank {int(decision.get('rank', 0))} "
                f"{'passed' if bool(decision.get('passed')) else 'blocked'}"
            )
            add_sample(
                self._sample_ref(
                    tier="promotion_candidate",
                    detail=decision_detail,
                    path=str(decision.get("source_path", decision.get("path", ""))),
                    folio=folio,
                )
            )

        for reviewed_entry in reviewed_entries[:3]:
            source_path = str(reviewed_entry.get("source_path", ""))
            folio = self._folio_from_source_path(source_path)
            add_sample(
                self._sample_ref(
                    tier="reviewed",
                    detail="reviewed annotation source",
                    path=source_path,
                    folio=folio,
                )
            )

        for tier in ("auto_admitted", "quarantined", "rejected", "repair_only"):
            for path in corpus_entry.get(f"{tier}_paths", [])[:2]:
                folio = self._folio_from_crop_path(str(path))
                add_sample(
                    self._sample_ref(
                        tier=tier,
                        detail=f"{tier.replace('_', ' ')} crop",
                        path=str(path),
                        folio=folio,
                    )
                )

        return {
            "key": _symbol_status_key(kind, symbol),
            "kind": kind,
            "symbol": symbol,
            "counts": counts,
            "stage_statuses": stage_statuses,
            "blockers": blockers,
            "guidance": guidance,
            "sample_refs": sample_refs,
            "promotion_candidates": decisions,
            "coverage_promoted": bool(entry.get("coverage_promoted", False)),
            "missing_reviewed": int(entry.get("missing_reviewed", 0)),
        }

    def _symbol_statuses(self, entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        reviewed_entries = self._reviewed_entries_by_symbol(catalog_only=True)
        reviewed_entries_all = self._reviewed_entries_by_symbol(catalog_only=False)
        return {
            _symbol_status_key(str(entry.get("kind", "")), str(entry.get("symbol", ""))): self._build_symbol_status(
                entry,
                reviewed_entries.get((str(entry.get("kind", "")), str(entry.get("symbol", ""))), []),
                reviewed_entries_all.get((str(entry.get("kind", "")), str(entry.get("symbol", ""))), []),
            )
            for entry in entries
        }

    def _symbol_reruns_payload(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {key: dict(value) for key, value in self._symbol_reruns.items()}

    def save_manual_guide(self, payload: dict[str, Any]) -> dict[str, Any]:
        annotation_id = str(payload.get("annotation_id", "")).strip()
        annotation = self._annotation_by_id(annotation_id)
        if annotation is None:
            raise ValueError("manual guide annotation_id must reference a saved reviewed annotation")
        kind = str(annotation.get("kind", ""))
        symbol = str(annotation.get("symbol", ""))
        segments = _normalize_manual_segments(payload.get("segments", []))
        if not segments:
            raise ValueError("manual guide must include at least one cubic segment")
        x_height_px = float(payload.get("x_height_px", annotation["bounds_px"]["height"]))
        x_advance_px = float(payload.get("x_advance_px", annotation["bounds_px"]["width"]))
        corridor_half_width_mm = float(payload.get("corridor_half_width_mm", 0.2))
        canvas_padding_px = max(0.0, float(payload.get("canvas_padding_px", 0.0) or 0.0))
        if x_height_px <= 0.0 or x_advance_px <= 0.0:
            raise ValueError("manual guide x_height_px and x_advance_px must be > 0")
        if corridor_half_width_mm <= 0.0:
            raise ValueError("manual guide corridor_half_width_mm must be > 0")
        guide_id = str(payload.get("id", "")).strip() or _safe_id(kind, f"{symbol}_{annotation_id}")
        guide_entry = {
            "id": guide_id,
            "kind": kind,
            "symbol": symbol,
            "annotation_id": annotation_id,
            "source_path": annotation["source_path"],
            "source_manuscript_label": annotation.get("source_manuscript_label", ""),
            "canvas_label": annotation.get("canvas_label", ""),
            "source_object_id": annotation.get("source_object_id", ""),
            "bounds_px": dict(annotation["bounds_px"]),
            "x_height_px": x_height_px,
            "x_advance_px": x_advance_px,
            "x_height_mm": float(payload.get("x_height_mm", EvofitConfig().x_height_mm)),
            "corridor_half_width_mm": corridor_half_width_mm,
            "canvas_padding_px": canvas_padding_px,
            "segments": segments,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "validation_errors": [],
            "active": True,
        }
        preview_info = self._write_manual_guide_previews(guide_entry)
        guide_entry.update(preview_info)
        with self._lock:
            entries = list(self.manual_guides.get("entries", []))
            replaced = False
            for index, entry in enumerate(entries):
                same_symbol = (
                    str(entry.get("kind", "")) == kind and str(entry.get("symbol", "")) == symbol
                )
                if same_symbol:
                    entry["active"] = False
                same_entry = str(entry.get("id", "")) == guide_id or str(entry.get("annotation_id", "")) == annotation_id
                if same_entry:
                    guide_entry["created_at"] = str(entry.get("created_at", guide_entry["created_at"]))
                    entries[index] = guide_entry
                    replaced = True
            if not replaced:
                entries.append(guide_entry)
            entries.sort(
                key=lambda item: (
                    str(item.get("kind", "")),
                    str(item.get("symbol", "")),
                    str(item.get("updated_at", "")),
                )
            )
            self.manual_guides["entries"] = entries
            self._write_manual_guides()
        return self._manual_guide_payload(guide_entry)

    def delete_manual_guide(self, guide_id: str) -> bool:
        guide_id = str(guide_id).strip()
        if not guide_id:
            return False
        with self._lock:
            entries = list(self.manual_guides.get("entries", []))
            target = next((dict(entry) for entry in entries if str(entry.get("id", "")) == guide_id), None)
            kept = [entry for entry in entries if str(entry.get("id", "")) != guide_id]
            if len(kept) == len(entries):
                return False
            if target is not None and bool(target.get("active", False)):
                kind = str(target.get("kind", ""))
                symbol = str(target.get("symbol", ""))
                replacement = next(
                    (
                        entry
                        for entry in sorted(
                            kept,
                            key=lambda item: str(item.get("updated_at", "")),
                            reverse=True,
                        )
                        if str(entry.get("kind", "")) == kind and str(entry.get("symbol", "")) == symbol
                    ),
                    None,
                )
                if replacement is not None:
                    replacement["active"] = True
            self.manual_guides["entries"] = kept
            self._write_manual_guides()
        return True

    def _manual_guide_for_annotation(self, annotation_id: str) -> dict[str, Any] | None:
        annotation_id = str(annotation_id).strip()
        for entry in self.manual_guides.get("entries", []):
            if str(entry.get("annotation_id", "")) == annotation_id:
                return self._manual_guide_payload(entry)
        return None

    def _manual_guide_for(self, kind: str, symbol: str) -> dict[str, Any] | None:
        entries = self._manual_guide_entries_for(kind, symbol)
        if not entries:
            return None
        active = next((entry for entry in entries if bool(entry.get("active", False))), entries[0])
        return self._manual_guide_payload(active)

    def _write_manual_guide_bundle(
        self,
        *,
        run_root: Path,
        freeze_manifest_path: Path,
        manual_guide: dict[str, Any],
    ) -> tuple[Path, dict[str, Any]]:
        bundle_root = run_root / "manual_guide_override"
        bundle_root.mkdir(parents=True, exist_ok=True)
        guide = self._build_manual_dense_guide(manual_guide)
        proposal_catalog_path = bundle_root / "proposal_guides.toml"
        write_pathguides_toml({guide.symbol: guide}, proposal_catalog_path)
        fit_source = {
            "kind": manual_guide["kind"],
            "symbol": manual_guide["symbol"],
            "text": manual_guide["symbol"] if manual_guide["kind"] == "glyph" else manual_guide["symbol"].replace("->", ""),
            "selected_source_path": str(manual_guide.get("source_crop_path", "")),
            "selected_source_document_path": str(manual_guide.get("source_path", "")),
            "selected_source_tier": "manual_guide",
            "selected_source_variant": "manual",
            "selected_source_raw_path": str(manual_guide.get("source_crop_path", "")),
            "selected_source_cleaned_path": "",
            "selected_source_cleanup_stroke_count": 0,
            "selected_source_manuscript": str(manual_guide.get("source_manuscript_label", "")),
            "selected_source_quality_tier": "manual",
            "selected_source_object_id": str(manual_guide.get("source_object_id", "")),
            "best_fitness": 1.0,
            "evofit_ncc": 1.0,
            "nominal_ncc": 0.0,
            "structurally_convertible": True,
        }
        summary_payload = {
            "fit_source_count": 1,
            "converted_guide_count": 1,
            "convertible_rate": 1.0,
            "beats_prior_rate": 1.0,
            "mean_evofit_ncc": 1.0,
            "mean_nominal_ncc": 0.0,
            "baseline_comparison": {"status": "manual-guide"},
            "fit_sources": [fit_source],
        }
        (bundle_root / "summary.json").write_text(
            json.dumps(summary_payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (bundle_root / "summary.md").write_text(
            "# TD-014 Manual Guide Override\n\n"
            f"- symbol: `{manual_guide['symbol']}`\n"
            f"- source annotation: `{manual_guide['annotation_id']}`\n"
            f"- source crop: `{manual_guide.get('source_crop_path', '')}`\n",
            encoding="utf-8",
        )
        manifest_path = bundle_root / "manifest.toml"
        manifest_path.write_text(
            "\n".join(
                [
                    "# TD-014 manual guide override bundle",
                    "schema_version = 1",
                    f"corpus_manifest_path = {json.dumps(freeze_manifest_path.as_posix())}",
                    f"proposal_catalog_path = {json.dumps(proposal_catalog_path.as_posix())}",
                    f"summary_json_path = {json.dumps((bundle_root / 'summary.json').as_posix())}",
                    f"summary_md_path = {json.dumps((bundle_root / 'summary.md').as_posix())}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return manifest_path, fit_source

    def _update_symbol_rerun(self, run_key: str, **changes: Any) -> dict[str, Any]:
        with self._lock:
            current = dict(self._symbol_reruns.get(run_key, {}))
            current.update(changes)
            self._symbol_reruns[run_key] = current
            return dict(current)

    def start_symbol_rerun(self, kind: str, symbol: str) -> dict[str, Any]:
        kind = str(kind).strip()
        symbol = str(symbol).strip()
        if kind not in {"glyph", "join"}:
            raise ValueError("symbol rerun kind must be 'glyph' or 'join'")
        if not symbol:
            raise ValueError("symbol rerun symbol is required")

        key = _symbol_status_key(kind, symbol)
        with self._lock:
            existing = dict(self._symbol_reruns.get(key, {}))
        if existing.get("status") == "running":
            return existing
        slug = _safe_id(kind, symbol)
        run_root = (self.symbol_rerun_root / slug / _utc_now().replace(":", "").replace(".", "_")).resolve()
        payload = self._update_symbol_rerun(
            key,
            key=key,
            kind=kind,
            symbol=symbol,
            status="running",
            stage="queued",
            percent=0,
            message="Queued symbol rerun.",
            started_at=_utc_now(),
            finished_at="",
            run_root=run_root.as_posix(),
            result=None,
            error="",
        )
        thread = threading.Thread(
            target=self._run_symbol_rerun,
            args=(key, kind, symbol, run_root),
            daemon=True,
        )
        thread.start()
        return payload

    def _run_symbol_rerun(self, key: str, kind: str, symbol: str, run_root: Path) -> None:
        try:
            freeze_root = run_root / "reviewed_exemplars"
            self._update_symbol_rerun(
                key,
                stage="freeze-reviewed-exemplars",
                percent=15,
                message="Freezing reviewed exemplars for the current reviewed manifest.",
            )
            freeze_result = freeze_reviewed_exemplars(
                self.reviewed_manifest_path,
                output_root=freeze_root,
            )

            self._update_symbol_rerun(
                key,
                stage="evofit-reviewed-exemplars",
                percent=45,
                message=f"Running reviewed evofit for {kind} {symbol}.",
            )
            evofit_root = run_root / "reviewed_evofit"
            evofit_result = run_reviewed_evofit(
                freeze_result["manifest_path"],
                output_root=evofit_root,
                config=EvofitConfig(allowed_tiers=(), max_candidates_per_symbol=3),
                kind=kind,
                symbols=(symbol,),
            )
            summary = dict(evofit_result["summary"])
            fit_sources = list(summary.get("fit_sources", []))
            fit_source = next((item for item in fit_sources if str(item.get("symbol", "")) == symbol), None)
            manual_guide = self._manual_guide_for(kind, symbol)

            guide_result = None
            guide_error = ""
            guide_catalog_path = run_root / "reviewed_promoted_v1.toml"
            guide_output_root = run_root / "reviewed_promoted_guides"
            guide_manifest_path = None
            guide_fit_source = fit_source
            if manual_guide is not None:
                self._update_symbol_rerun(
                    key,
                    stage="freeze-manual-guides",
                    percent=80,
                    message=f"Freezing manual guide override for {kind} {symbol}.",
                )
                try:
                    guide_manifest_path, guide_fit_source = self._write_manual_guide_bundle(
                        run_root=run_root,
                        freeze_manifest_path=freeze_result["manifest_path"],
                        manual_guide=manual_guide,
                    )
                    guide_result = freeze_reviewed_evofit_guides(
                        guide_manifest_path,
                        output_root=guide_output_root,
                        guide_catalog_path=guide_catalog_path,
                    )
                except Exception as exc:  # pragma: no cover - defensive, surfaced in result
                    guide_error = str(exc)
            elif fit_source is not None and bool(fit_source.get("structurally_convertible", False)):
                self._update_symbol_rerun(
                    key,
                    stage="freeze-reviewed-evofit-guides",
                    percent=80,
                    message=f"Freezing promoted guides for {kind} {symbol}.",
                )
                try:
                    guide_result = freeze_reviewed_evofit_guides(
                        evofit_result["manifest_path"],
                        output_root=guide_output_root,
                        guide_catalog_path=guide_catalog_path,
                    )
                except Exception as exc:  # pragma: no cover - defensive, surfaced in result
                    guide_error = str(exc)

            result_payload = {
                "freeze_summary_path": str(freeze_result["summary_md_path"]),
                "freeze_manifest_path": str(freeze_result["manifest_path"]),
                "reviewed_exemplar_count": (
                    int(freeze_result["summary"].get("reviewed_glyph_count", 0))
                    if kind == "glyph"
                    else int(freeze_result["summary"].get("reviewed_join_count", 0))
                ),
                "evofit_summary_path": str(evofit_result["summary_md_path"]),
                "evofit_manifest_path": str(evofit_result["manifest_path"]),
                "proposal_catalog_path": str(evofit_result["proposal_catalog_path"]),
                "fit_source_count": int(summary.get("fit_source_count", 0)),
                "converted_guide_count": int(summary.get("converted_guide_count", 0)),
                "fit_source": fit_source,
                "guide_source": "manual" if manual_guide is not None else "evofit",
                "manual_guide": manual_guide,
                "guide_freeze_error": guide_error,
                "guide_catalog_path": str(guide_result["guide_catalog_path"]) if guide_result else "",
                "guide_freeze_summary_path": str(guide_result["coverage_provenance_report_md_path"]) if guide_result else "",
                "guide_validation_path": str(guide_result["validation_report_md_path"]) if guide_result else "",
                "artifacts": {
                    "comparison": _artifact_payload(
                        fit_source.get("comparison_path"),
                        allowed_roots=(_REPO_ROOT, self.output_root, self.symbol_rerun_root),
                    )
                    if fit_source
                    else None,
                    "best_render": _artifact_payload(
                        fit_source.get("best_render_path"),
                        allowed_roots=(_REPO_ROOT, self.output_root, self.symbol_rerun_root),
                    )
                    if fit_source
                    else None,
                    "fit_source": _artifact_payload(
                        fit_source.get("fit_source_copy_path"),
                        allowed_roots=(_REPO_ROOT, self.output_root, self.symbol_rerun_root),
                    )
                    if fit_source
                    else None,
                    "prior_render": _artifact_payload(
                        fit_source.get("prior_render_path"),
                        allowed_roots=(_REPO_ROOT, self.output_root, self.symbol_rerun_root),
                    )
                    if fit_source
                    else None,
                    "guide_overlay": _artifact_payload(
                        guide_output_root / "overlay_snapshots" / f"{_pathguide_symbol_slug(symbol)}.png",
                        allowed_roots=(_REPO_ROOT, self.output_root, self.symbol_rerun_root),
                    )
                    if guide_result
                    else None,
                    "guide_nominal": _artifact_payload(
                        guide_output_root / "nominal_snapshots" / f"{_pathguide_symbol_slug(symbol)}.png",
                        allowed_roots=(_REPO_ROOT, self.output_root, self.symbol_rerun_root),
                    )
                    if guide_result
                    else None,
                    "guide_overlay_panel": _artifact_payload(
                        guide_result.get("overlay_panel_path"),
                        allowed_roots=(_REPO_ROOT, self.output_root, self.symbol_rerun_root),
                    )
                    if guide_result
                    else None,
                    "guide_nominal_panel": _artifact_payload(
                        guide_result.get("nominal_panel_path"),
                        allowed_roots=(_REPO_ROOT, self.output_root, self.symbol_rerun_root),
                    )
                    if guide_result
                    else None,
                    "manual_source": _artifact_payload(
                        manual_guide.get("source_crop_path"),
                        allowed_roots=(_REPO_ROOT, self.output_root, self.manual_guide_root),
                    )
                    if manual_guide
                    else None,
                    "manual_overlay": _artifact_payload(
                        manual_guide.get("preview_overlay_path"),
                        allowed_roots=(_REPO_ROOT, self.output_root, self.manual_guide_root),
                    )
                    if manual_guide
                    else None,
                    "manual_nominal": _artifact_payload(
                        manual_guide.get("preview_nominal_path"),
                        allowed_roots=(_REPO_ROOT, self.output_root, self.manual_guide_root),
                    )
                    if manual_guide
                    else None,
                },
            }
            result_payload["artifacts"] = {
                name: artifact for name, artifact in result_payload["artifacts"].items() if artifact is not None
            }
            message = (
                f"Symbol rerun finished for {kind} {symbol} using {'manual guide override' if manual_guide else 'reviewed evofit'}."
                if fit_source is not None
                else f"Symbol rerun finished for {kind} {symbol}, but no fit source was produced."
            )
            self._update_symbol_rerun(
                key,
                status="completed",
                stage="complete",
                percent=100,
                message=message,
                finished_at=_utc_now(),
                result=result_payload,
                error="",
            )
        except Exception as exc:  # pragma: no cover - defensive background failure
            self._update_symbol_rerun(
                key,
                status="failed",
                stage="failed",
                percent=100,
                message=f"Symbol rerun failed for {kind} {symbol}.",
                finished_at=_utc_now(),
                error=str(exc),
            )

    def read_artifact(self, raw_path: str) -> tuple[bytes, str]:
        path = _resolve_path(raw_path, relative_to=_REPO_ROOT)
        allowed = False
        for root in (_REPO_ROOT, self.output_root, self.symbol_rerun_root):
            try:
                path.relative_to(root.resolve())
                allowed = True
                break
            except ValueError:
                continue
        if not allowed:
            raise FileNotFoundError("artifact path is outside the allowed workbench roots")
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"artifact not found: {path}")
        content_type, _ = mimetypes.guess_type(path.name)
        return path.read_bytes(), content_type or "application/octet-stream"

    def get_folio(self, folio_id: str) -> dict[str, Any]:
        try:
            return self._folios_by_id[str(folio_id)]
        except KeyError as exc:
            raise KeyError(f"unknown folio id: {folio_id}") from exc

    def list_annotations(self) -> list[dict[str, Any]]:
        return [_entry_to_payload(entry) for entry in self.reviewed_manifest.get("entries", [])]

    def get_state(self) -> dict[str, Any]:
        entries = self._live_coverage_entries()
        summary = self._live_coverage_summary(entries)
        debt = [
            {
                "kind": entry["kind"],
                "symbol": entry["symbol"],
                "missing_reviewed": int(entry.get("missing_reviewed", 0)),
                "reviewed_count": int(entry.get("reviewed_count", 0)),
                "reviewed_excluded_count": int(entry.get("reviewed_excluded_count", 0)),
                "promoted_count": int(entry.get("promoted_count", 0)),
                "auto_admitted_count": int(entry.get("auto_admitted_count", 0)),
                "quarantined_count": int(entry.get("quarantined_count", 0)),
                "rejected_count": int(entry.get("rejected_count", 0)),
                "repair_only_count": int(entry.get("repair_only_count", 0)),
                "status_key": _symbol_status_key(entry["kind"], entry["symbol"]),
            }
            for entry in entries
            if int(entry.get("missing_reviewed", 0)) == 1
        ]
        debt.sort(key=lambda item: (item["kind"], item["symbol"]))
        return {
            "coverage_summary": summary,
            "coverage_entries": entries,
            "coverage_debt": debt,
            "symbol_statuses": self._symbol_statuses(entries),
            "manual_guides": self._manual_guides_by_symbol(),
            "manual_guide_groups": self._manual_guide_groups(),
            "symbol_reruns": self._symbol_reruns_payload(),
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
                "catalog_included": bool(existing.get("catalog_included", True)) if existing else True,
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

    def set_annotation_catalog_included(self, annotation_id: str, included: bool) -> dict[str, Any]:
        with self._lock:
            entries = list(self.reviewed_manifest.get("entries", []))
            for index, entry in enumerate(entries):
                if str(entry.get("id")) != str(annotation_id):
                    continue
                updated = dict(entry)
                updated["catalog_included"] = bool(included)
                updated["updated_at"] = _utc_now()
                entries[index] = updated
                self.reviewed_manifest["entries"] = entries
                self._write_manifest()
                return _entry_to_payload(updated)
        raise KeyError(f"unknown annotation id: {annotation_id}")

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
.card.active { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(136, 93, 58, 0.14); }
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
.symbol-status {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.status-list {
  display: grid;
  gap: 8px;
}
.status-row {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fff;
  padding: 8px 10px;
}
.status-row-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}
.status-badge {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 0.75rem;
  border: 1px solid var(--line);
  background: #f7f2e7;
}
.status-badge.available, .status-badge.complete, .status-badge.passed {
  border-color: #9ac5a2;
  background: #eef8ee;
  color: #245b2f;
}
.status-badge.blocked, .status-badge.missing, .status-badge.unavailable {
  border-color: #d7a9a9;
  background: #fff1f1;
  color: #8f2323;
}
.status-badge.unknown, .status-badge.needed {
  border-color: #dbc99d;
  background: #fff8e7;
  color: #7a5b11;
}
.status-bullets {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}
.status-bullets button {
  text-align: left;
}
.artifact-grid {
  display: grid;
  gap: 10px;
  margin-top: 8px;
}
.artifact-grid.wide {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.artifact-card {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fff;
  padding: 8px;
}
.artifact-card img {
  display: block;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f8f3e9;
  margin-top: 6px;
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
.modal-backdrop {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(34, 32, 24, 0.45);
  z-index: 20;
}
.modal-backdrop[hidden] {
  display: none;
}
.modal-card {
  width: min(980px, 100%);
  max-height: min(88vh, 920px);
  display: grid;
  grid-template-rows: auto 1fr;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--panel);
  box-shadow: 0 24px 60px rgba(39, 31, 18, 0.24);
  overflow: hidden;
}
.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--line);
  background: linear-gradient(180deg, #fbf7ef 0%, #fffdf7 100%);
}
.modal-body {
  overflow: auto;
  padding: 18px 20px 22px;
  display: grid;
  gap: 18px;
}
.modal-section {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
  padding: 14px;
}
.reference-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}
.reference-card {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fffdf9;
  padding: 12px;
}
.reference-card.excluded {
  background: #f6f1e8;
  border-style: dashed;
}
.reference-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.reference-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.guide-editor {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 18px;
}
.guide-editor-canvas-wrap {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #f8f3e9;
  padding: 12px;
}
.guide-editor-canvas-viewport {
  overflow: auto;
  max-height: min(72vh, 760px);
}
.guide-editor-zoom {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.guide-editor-modes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}
.guide-editor-canvas {
  display: block;
  width: auto;
  min-width: 100%;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fff;
  cursor: crosshair;
}
.guide-editor-canvas.dragging {
  cursor: grabbing;
}
.guide-editor-side {
  display: grid;
  gap: 12px;
}
.guide-editor-segments {
  display: grid;
  gap: 8px;
  max-height: 320px;
  overflow: auto;
}
.guide-editor-segment {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fffdf9;
  padding: 10px;
}
.guide-editor-pending {
  color: var(--muted);
  font-size: 0.88rem;
}
"""


_APP_JS = """
const GUIDE_EDITOR_BASE_WIDTH = 560;
const GUIDE_EDITOR_BASE_HEIGHT = 420;

const state = {
  payload: null,
  currentFolioId: null,
  currentSymbolKey: null,
  symbolRerunPollId: null,
  selectedAnnotationId: null,
  draftBounds: null,
  naturalWidth: 1,
  naturalHeight: 1,
  panMode: false,
    guideEditor: {
      annotationId: null,
      guideId: null,
      symbolKey: null,
      segments: [],
    pendingPoints: [],
      strokeOrder: 1,
      contact: true,
      xHeightPx: 0,
      xAdvancePx: 0,
      corridorHalfWidthMm: 0.2,
      paddingPx: 32,
      zoomPct: 100,
      mode: 'add',
      transform: null,
      recenterOnRender: false,
      hoverHandle: null,
    draggingHandle: null,
    dragMoved: false,
    suppressCanvasClick: false,
  },
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
  coverageBrowser: document.getElementById('coverage-browser'),
  symbolStatusTitle: document.getElementById('symbol-status-title'),
  symbolStatusMeta: document.getElementById('symbol-status-meta'),
  symbolStatusCounts: document.getElementById('symbol-status-counts'),
  symbolStatusStages: document.getElementById('symbol-status-stages'),
  symbolStatusBlockers: document.getElementById('symbol-status-blockers'),
  symbolStatusGuidance: document.getElementById('symbol-status-guidance'),
  symbolStatusSamples: document.getElementById('symbol-status-samples'),
  symbolMenuModal: document.getElementById('symbol-menu-modal'),
  symbolMenuTitle: document.getElementById('symbol-menu-title'),
  symbolMenuMeta: document.getElementById('symbol-menu-meta'),
  symbolMenuClose: document.getElementById('symbol-menu-close'),
  symbolMenuRerun: document.getElementById('symbol-menu-rerun'),
  symbolMenuOpenRerun: document.getElementById('symbol-menu-open-rerun'),
  symbolMenuGuideEditor: document.getElementById('symbol-menu-guide-editor'),
  symbolMenuDeleteGuide: document.getElementById('symbol-menu-delete-guide'),
  symbolReferenceList: document.getElementById('symbol-reference-list'),
  guideEditorModal: document.getElementById('guide-editor-modal'),
  guideEditorTitle: document.getElementById('guide-editor-title'),
  guideEditorMeta: document.getElementById('guide-editor-meta'),
  guideEditorClose: document.getElementById('guide-editor-close'),
  guideEditorCanvasViewport: document.getElementById('guide-editor-canvas-viewport'),
  guideEditorZoomOut: document.getElementById('guide-editor-zoom-out'),
  guideEditorZoomIn: document.getElementById('guide-editor-zoom-in'),
  guideEditorZoomReset: document.getElementById('guide-editor-zoom-reset'),
  guideEditorZoom: document.getElementById('guide-editor-zoom'),
  guideEditorZoomValue: document.getElementById('guide-editor-zoom-value'),
  guideEditorModeAdd: document.getElementById('guide-editor-mode-add'),
  guideEditorModeEdit: document.getElementById('guide-editor-mode-edit'),
  guideEditorCanvas: document.getElementById('guide-editor-canvas'),
  guideEditorPending: document.getElementById('guide-editor-pending'),
  guideEditorXHeightPx: document.getElementById('guide-editor-x-height-px'),
  guideEditorXAdvancePx: document.getElementById('guide-editor-x-advance-px'),
  guideEditorCorridor: document.getElementById('guide-editor-corridor'),
  guideEditorPaddingPx: document.getElementById('guide-editor-padding-px'),
  guideEditorStrokeOrder: document.getElementById('guide-editor-stroke-order'),
  guideEditorContact: document.getElementById('guide-editor-contact'),
  guideEditorClearPending: document.getElementById('guide-editor-clear-pending'),
  guideEditorSave: document.getElementById('guide-editor-save'),
  guideEditorProcess: document.getElementById('guide-editor-process'),
  guideEditorDelete: document.getElementById('guide-editor-delete'),
  guideEditorSegments: document.getElementById('guide-editor-segments'),
  guideEditorSavedGuides: document.getElementById('guide-editor-saved-guides'),
  guideEditorPreviewArtifacts: document.getElementById('guide-editor-preview-artifacts'),
  guideEditorRerunMeta: document.getElementById('guide-editor-rerun-meta'),
  guideEditorRerunArtifacts: document.getElementById('guide-editor-rerun-artifacts'),
  symbolRerunButton: document.getElementById('symbol-rerun-button'),
  symbolRerunOpen: document.getElementById('symbol-rerun-open'),
  symbolRerunMeta: document.getElementById('symbol-rerun-meta'),
  symbolRerunModal: document.getElementById('symbol-rerun-modal'),
  symbolRerunModalTitle: document.getElementById('symbol-rerun-modal-title'),
  symbolRerunModalMeta: document.getElementById('symbol-rerun-modal-meta'),
  symbolRerunModalClose: document.getElementById('symbol-rerun-modal-close'),
  symbolRerunDetails: document.getElementById('symbol-rerun-details'),
  symbolRerunArtifacts: document.getElementById('symbol-rerun-artifacts'),
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

function symbolKey(kind, symbol) {
  return `${kind}:${symbol}`;
}

function currentSymbolStatus() {
  if (!state.payload || !state.currentSymbolKey) return null;
  return state.payload.symbol_statuses?.[state.currentSymbolKey] || null;
}

function currentSymbolRerun() {
  if (!state.payload || !state.currentSymbolKey) return null;
  return state.payload.symbol_reruns?.[state.currentSymbolKey] || null;
}

function currentManualGuide() {
  if (!state.payload || !state.currentSymbolKey) return null;
  return state.payload.manual_guides?.[state.currentSymbolKey] || null;
}

function currentManualGuideGroup() {
  if (!state.payload || !state.currentSymbolKey) return null;
  return state.payload.manual_guide_groups?.[state.currentSymbolKey] || null;
}

function currentManualGuides() {
  return currentManualGuideGroup()?.entries || [];
}

function currentManualGuideForAnnotation(annotationId) {
  return currentManualGuides().find((entry) => entry.annotation_id === annotationId) || null;
}

function currentManualGuideAnnotation() {
  const manual = currentManualGuide();
  if (!manual || !state.payload) return null;
  return (state.payload.annotations || []).find((entry) => entry.id === manual.annotation_id) || null;
}

function currentSymbolAnnotations() {
  const status = currentSymbolStatus();
  if (!state.payload || !status) return [];
  return [...(state.payload.annotations || [])]
    .filter((entry) => entry.kind === status.kind && entry.symbol === status.symbol)
    .sort((left, right) => {
      if (Boolean(left.catalog_included) !== Boolean(right.catalog_included)) {
        return Boolean(left.catalog_included) ? -1 : 1;
      }
      return String(right.updated_at || '').localeCompare(String(left.updated_at || ''));
    });
}

function browsableSymbols() {
  if (!state.payload?.coverage_entries) return [];
  return state.payload.coverage_entries.filter((entry) => {
    const key = entry.status_key || symbolKey(entry.kind, entry.symbol);
    return Number(entry.reviewed_total_count || 0) > 0 || Boolean(state.payload.manual_guides?.[key]);
  });
}

function chooseInitialSymbol() {
  if (state.currentSymbolKey || !state.payload) return;
  const firstDebt = state.payload.coverage_debt?.[0];
  if (firstDebt) {
    state.currentSymbolKey = firstDebt.status_key || symbolKey(firstDebt.kind, firstDebt.symbol);
    return;
  }
  const firstBrowser = browsableSymbols()[0];
  if (firstBrowser) {
    state.currentSymbolKey = firstBrowser.status_key || symbolKey(firstBrowser.kind, firstBrowser.symbol);
  }
}

async function openSymbolMenuModal() {
  try {
    await refreshWorkbenchState();
    renderCoverage();
    renderFolios();
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
  } catch (error) {
    setStatus(String(error), true);
  }
  dom.symbolMenuModal.hidden = false;
  dom.symbolMenuModal.setAttribute('aria-hidden', 'false');
  renderSymbolMenu();
}

function closeSymbolMenuModal() {
  dom.symbolMenuModal.hidden = true;
  dom.symbolMenuModal.setAttribute('aria-hidden', 'true');
}

function selectDebtSymbol(kind, symbol, {openMenu = false} = {}) {
  state.currentSymbolKey = symbolKey(kind, symbol);
  dom.kind.value = kind;
  dom.symbol.value = symbol;
  renderCoverage();
  renderSelectedSymbolStatus();
  if (openMenu) {
    openSymbolMenuModal();
  }
  setStatus(`Prepared label ${kind} ${symbol}`);
}

function renderStatusBullets(target, items, emptyMessage, {asButtons = false, onClick = null} = {}) {
  target.innerHTML = '';
  if (!items.length) {
    const empty = document.createElement('div');
    empty.className = 'small';
    empty.textContent = emptyMessage;
    target.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const text = typeof item === 'string' ? item : String(item.text || '');
    const detail = typeof item === 'string' ? '' : String(item.detail || '');
    const container = document.createElement('div');
    if (asButtons && typeof onClick === 'function' && item.folio_id) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = text;
      button.addEventListener('click', () => onClick(item));
      container.appendChild(button);
    } else {
      const line = document.createElement('div');
      line.textContent = text;
      container.appendChild(line);
    }
    if (detail) {
      const meta = document.createElement('div');
      meta.className = 'small';
      meta.textContent = detail;
      container.appendChild(meta);
    }
    target.appendChild(container);
  });
}

async function refreshWorkbenchState() {
  const response = await fetch('/api/state');
  state.payload = await response.json();
  dom.manifestPath.textContent = state.payload.reviewed_manifest_path;
}

function stopSymbolRerunPolling() {
  if (state.symbolRerunPollId !== null) {
    window.clearTimeout(state.symbolRerunPollId);
    state.symbolRerunPollId = null;
  }
}

function scheduleSymbolRerunPolling() {
  stopSymbolRerunPolling();
  const rerun = currentSymbolRerun();
  if (!rerun || rerun.status !== 'running') return;
  state.symbolRerunPollId = window.setTimeout(async () => {
    try {
      await refreshWorkbenchState();
      renderCoverage();
      renderFolios();
      renderAnnotations();
      renderOverlay();
      renderCleanupEditor();
      if (!dom.guideEditorModal.hidden) {
        renderGuideEditor();
      }
      scheduleSymbolRerunPolling();
    } catch (error) {
      setStatus(String(error), true);
    }
  }, 2000);
}

function setSymbolRerunModalOpen(isOpen) {
  dom.symbolRerunModal.hidden = !isOpen;
  dom.symbolRerunModal.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
}

function renderRerunArtifacts(target, artifacts) {
  target.innerHTML = '';
  if (!artifacts || !Object.keys(artifacts).length) {
    const empty = document.createElement('div');
    empty.className = 'small';
    empty.textContent = 'No rerun artifacts yet.';
    target.appendChild(empty);
    return;
  }
  const artifactMeta = {
    fit_source: {
      title: 'selected reviewed source',
      detail: 'The reviewed exemplar crop that freeze and evofit actually used as input.',
    },
    comparison: {
      title: 'comparison',
      detail: 'Layout: selected source on the left, prior nominal guide in the middle, evolved best render on the right.',
    },
    best_render: {
      title: 'evolved best render',
      detail: 'The synthesized pathguide render produced from the selected source. This is output, not a second input sample.',
    },
    prior_render: {
      title: 'prior nominal render',
      detail: 'The prior nominal guide used as a comparison baseline when one exists.',
    },
    guide_overlay: {
      title: 'final guide overlay',
      detail: 'The promoted guide rendered as an overlay-style snapshot. This is the final guide shape after guide freeze.',
    },
    guide_nominal: {
      title: 'final guide nominal',
      detail: 'The promoted guide rendered as a nominal snapshot. This is the guide that will influence downstream rendering.',
    },
    guide_overlay_panel: {
      title: 'guide overlay panel',
      detail: 'Panel snapshot for all promoted guides in this rerun freeze.',
    },
    guide_nominal_panel: {
      title: 'guide nominal panel',
      detail: 'Nominal panel snapshot for all promoted guides in this rerun freeze.',
    },
  };
  const orderedNames = [
    'fit_source',
    'comparison',
    'best_render',
    'prior_render',
    'guide_overlay',
    'guide_nominal',
    'guide_overlay_panel',
    'guide_nominal_panel',
  ];
  const entries = Object.entries(artifacts).sort(([left], [right]) => {
    const leftIndex = orderedNames.indexOf(left);
    const rightIndex = orderedNames.indexOf(right);
    return (leftIndex === -1 ? orderedNames.length : leftIndex) - (rightIndex === -1 ? orderedNames.length : rightIndex);
  });
  entries.forEach(([name, artifact]) => {
    const metaInfo = artifactMeta[name] || {title: name.replaceAll('_', ' '), detail: ''};
    const card = document.createElement('div');
    card.className = 'artifact-card';
    const title = document.createElement('strong');
    title.textContent = metaInfo.title;
    card.appendChild(title);
    if (metaInfo.detail) {
      const detail = document.createElement('div');
      detail.className = 'small';
      detail.textContent = metaInfo.detail;
      card.appendChild(detail);
    }
    const link = document.createElement('a');
    link.href = artifact.url;
    link.target = '_blank';
    link.rel = 'noreferrer';
    link.textContent = artifact.label;
    card.appendChild(link);
    if (artifact.is_image) {
      const image = document.createElement('img');
      image.src = artifact.url;
      image.alt = name;
      card.appendChild(image);
    }
    target.appendChild(card);
  });
}

async function openSymbolRerunModal() {
  try {
    await refreshWorkbenchState();
    renderCoverage();
    renderFolios();
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
  } catch (error) {
    setStatus(String(error), true);
  }
  setSymbolRerunModalOpen(true);
  renderSymbolRerun();
}

function closeSymbolRerunModal() {
  setSymbolRerunModalOpen(false);
}

function renderSymbolRerun() {
  const status = currentSymbolStatus();
  const rerun = currentSymbolRerun();
  dom.symbolRerunDetails.innerHTML = '';
  dom.symbolRerunArtifacts.innerHTML = '';
  dom.symbolRerunButton.disabled = !status;
  dom.symbolRerunOpen.disabled = !rerun;
  dom.symbolMenuRerun.disabled = !status;
  dom.symbolMenuOpenRerun.disabled = !rerun;
  if (!status) {
    dom.symbolRerunMeta.textContent = 'Select a glyph or join first.';
    dom.symbolRerunModalTitle.textContent = 'Symbol rerun';
    dom.symbolRerunModalMeta.textContent = 'Select a glyph or join to inspect rerun diagnostics.';
    renderStatusBullets(dom.symbolRerunDetails, [], 'No rerun data yet.');
    renderRerunArtifacts(dom.symbolRerunArtifacts, null);
    stopSymbolRerunPolling();
    return;
  }

  if (!rerun) {
    dom.symbolRerunMeta.textContent = `No rerun yet for ${status.kind} ${status.symbol}. Open the window after a run to inspect diagnostics and artifacts.`;
    dom.symbolRerunModalTitle.textContent = `${status.kind} ${status.symbol}`;
    dom.symbolRerunModalMeta.textContent = `Run a focused reviewed pipeline diagnostic for ${status.kind} ${status.symbol}.`;
    renderStatusBullets(dom.symbolRerunDetails, [], 'No rerun has been executed for this symbol yet.');
    renderRerunArtifacts(dom.symbolRerunArtifacts, null);
    stopSymbolRerunPolling();
    return;
  }

  const rerunSummary =
    `${status.kind} ${status.symbol} · ${rerun.status} · ${rerun.stage} · ${rerun.percent}%` +
    (rerun.message ? ` · ${rerun.message}` : '');
  dom.symbolRerunMeta.textContent = rerunSummary;
  dom.symbolRerunModalTitle.textContent = `${status.kind} ${status.symbol}`;
  dom.symbolRerunModalMeta.textContent = rerunSummary;
  const details = [];
  if (rerun.error) {
    details.push({text: rerun.error, detail: 'error'});
  }
  if (rerun.result) {
    const fitSource = rerun.result.fit_source;
    details.push({
      text: `fit sources ${rerun.result.fit_source_count} · converted guides ${rerun.result.converted_guide_count}`,
      detail: 'summary',
    });
    if (fitSource) {
      details.push({
        text:
          `${fitSource.symbol} · convertible=${fitSource.structurally_convertible} · ` +
          `quality=${fitSource.selected_source_quality_tier || 'n/a'} · variant=${fitSource.selected_source_variant || 'raw'}`,
        detail: 'selected fit source',
      });
      if (fitSource.selected_source_document_path) {
        details.push({
          text: fitSource.selected_source_document_path,
          detail: 'source document',
        });
      }
      const errors = fitSource.validation_errors || [];
      if (errors.length) {
        errors.forEach((item) => details.push({text: item, detail: 'validation error'}));
      } else {
        details.push({text: 'No validation errors recorded.', detail: 'validation'});
      }
    } else {
      details.push({text: 'No fit source was produced for this symbol.', detail: 'result'});
    }
    if (rerun.result.guide_freeze_error) {
      details.push({text: rerun.result.guide_freeze_error, detail: 'guide freeze'});
    }
    if (rerun.result.guide_catalog_path) {
      details.push({text: rerun.result.guide_catalog_path, detail: 'guide catalog'});
    }
    renderRerunArtifacts(dom.symbolRerunArtifacts, rerun.result.artifacts);
  } else {
    renderRerunArtifacts(dom.symbolRerunArtifacts, null);
  }
  renderStatusBullets(dom.symbolRerunDetails, details, 'No rerun details yet.');
  if (rerun.status === 'running') {
    scheduleSymbolRerunPolling();
  } else {
    stopSymbolRerunPolling();
  }
}

async function startSelectedSymbolRerun() {
  try {
    await refreshWorkbenchState();
    renderCoverage();
    renderFolios();
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
    const status = currentSymbolStatus();
    if (!status) {
      setStatus('Select a symbol first.', true);
      return;
    }
    dom.symbolRerunButton.disabled = true;
    dom.symbolMenuRerun.disabled = true;
    const response = await fetch('/api/symbol-reruns', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({kind: status.kind, symbol: status.symbol}),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    if (data.state) {
      state.payload = data.state;
      dom.manifestPath.textContent = state.payload.reviewed_manifest_path;
    }
    renderCoverage();
    renderSymbolRerun();
    openSymbolRerunModal();
    setStatus(`Started rerun for ${status.kind} ${status.symbol}`);
    scheduleSymbolRerunPolling();
  } catch (error) {
    dom.symbolRerunButton.disabled = false;
    dom.symbolMenuRerun.disabled = false;
    setStatus(String(error), true);
  }
}

function openAnnotationReference(entry) {
  const folio = (state.payload?.folios || []).find((item) => item.local_path === entry.source_path);
  if (folio) {
    loadFolio(folio.id);
  }
  state.selectedAnnotationId = entry.id;
  syncFormFromSelection();
  renderAnnotations();
  renderOverlay();
  renderCleanupEditor();
}

async function updateAnnotationCatalogInclusion(annotationId, catalogIncluded) {
  try {
    const response = await fetch('/api/annotations/catalog', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({id: annotationId, catalog_included: catalogIncluded}),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    if (data.state) {
      state.payload = data.state;
      dom.manifestPath.textContent = state.payload.reviewed_manifest_path;
    }
    renderCoverage();
    renderFolios();
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
    renderSymbolMenu();
    setStatus(catalogIncluded ? 'Restored annotation to catalog inputs.' : 'Excluded annotation from catalog inputs.');
  } catch (error) {
    setStatus(String(error), true);
  }
}

async function deleteAnnotationById(annotationId) {
  try {
    const response = await fetch(`/api/annotations/${encodeURIComponent(annotationId)}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    if (data.state) {
      state.payload = data.state;
      dom.manifestPath.textContent = state.payload.reviewed_manifest_path;
    }
    if (state.selectedAnnotationId === annotationId) {
      state.selectedAnnotationId = null;
      state.draftBounds = null;
    }
    renderCoverage();
    renderFolios();
    syncFormFromSelection();
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
    renderSymbolMenu();
    setStatus('Deleted annotation.');
  } catch (error) {
    setStatus(String(error), true);
  }
}

function renderSymbolMenu() {
  const status = currentSymbolStatus();
  const references = currentSymbolAnnotations();
  const manual = currentManualGuide();
  const manualAnnotation = currentManualGuideAnnotation();
  dom.symbolReferenceList.innerHTML = '';
  dom.symbolMenuRerun.disabled = !status;
  dom.symbolMenuOpenRerun.disabled = !currentSymbolRerun();
  dom.symbolMenuGuideEditor.disabled = !(references.length || manualAnnotation);
  dom.symbolMenuDeleteGuide.disabled = !manual;
  if (!status) {
    dom.symbolMenuTitle.textContent = 'Symbol references';
    dom.symbolMenuMeta.textContent = 'Select a glyph or join from the symbol lists to manage reviewed references and manual guide overrides.';
    const empty = document.createElement('div');
    empty.className = 'small';
    empty.textContent = 'No symbol selected.';
    dom.symbolReferenceList.appendChild(empty);
    return;
  }

  dom.symbolMenuTitle.textContent = `${status.kind} ${status.symbol}`;
  dom.symbolMenuMeta.textContent =
    `${status.counts.reviewed} active reviewed reference(s) feed freeze and evofit. ` +
    `${status.counts.reviewed_excluded || 0} excluded reference(s) are kept for provenance but ignored downstream.` +
    (manual ? ' A saved manual guide override exists for this symbol.' : '');

  if (!references.length) {
    const empty = document.createElement('div');
    empty.className = 'small';
    empty.textContent = 'No reviewed references saved for this symbol yet.';
    dom.symbolReferenceList.appendChild(empty);
    return;
  }

  references.forEach((entry) => {
    const card = document.createElement('div');
    card.className = `reference-card${entry.catalog_included ? '' : ' excluded'}`;

    const head = document.createElement('div');
    head.className = 'reference-head';
    const title = document.createElement('strong');
    title.textContent = `${entry.quality} · ${entry.catalog_included ? 'active' : 'excluded'}`;
    head.appendChild(title);
    const badge = document.createElement('span');
    badge.className = `status-badge ${entry.catalog_included ? 'complete' : 'blocked'}`;
    badge.textContent = entry.catalog_included ? 'catalog input' : 'pruned';
    head.appendChild(badge);
    card.appendChild(head);

    const meta = document.createElement('div');
    meta.className = 'small';
    meta.textContent =
      `${entry.source_manuscript_label || 'unknown'} • ${entry.canvas_label || 'unknown'} • ` +
      `${entry.bounds_px.width}×${entry.bounds_px.height}px • updated ${entry.updated_at || 'n/a'}`;
    card.appendChild(meta);

    if (entry.notes) {
      const notes = document.createElement('div');
      notes.className = 'small';
      notes.textContent = entry.notes;
      card.appendChild(notes);
    }

    const actions = document.createElement('div');
    actions.className = 'reference-actions';

    const openButton = document.createElement('button');
    openButton.type = 'button';
    openButton.textContent = 'Open Folio';
    openButton.addEventListener('click', () => openAnnotationReference(entry));
    actions.appendChild(openButton);

    const toggleButton = document.createElement('button');
    toggleButton.type = 'button';
    toggleButton.textContent = entry.catalog_included ? 'Exclude' : 'Restore';
    toggleButton.addEventListener('click', () => updateAnnotationCatalogInclusion(entry.id, !entry.catalog_included));
    actions.appendChild(toggleButton);

    const guideButton = document.createElement('button');
    guideButton.type = 'button';
    guideButton.textContent = 'Guide Editor';
    guideButton.addEventListener('click', () => openGuideEditorForAnnotation(entry));
    actions.appendChild(guideButton);

    const deleteButton = document.createElement('button');
    deleteButton.type = 'button';
    deleteButton.className = 'danger';
    deleteButton.textContent = 'Delete';
    deleteButton.addEventListener('click', () => deleteAnnotationById(entry.id));
    actions.appendChild(deleteButton);

    card.appendChild(actions);
    dom.symbolReferenceList.appendChild(card);
  });
}

function guideEditorAnnotation() {
  if (!state.guideEditor.annotationId || !state.payload) return null;
  return state.payload.annotations.find((entry) => entry.id === state.guideEditor.annotationId) || null;
}

function guideEditorHandleMatches(left, right) {
  if (!left || !right) return false;
  if (left.type !== right.type) return false;
  if (left.type === 'segment') {
    return left.segmentIndex === right.segmentIndex && left.pointKey === right.pointKey;
  }
  return left.pendingIndex === right.pendingIndex;
}

function guideEditorCanvasPoint(point) {
  const transform = state.guideEditor.transform;
  if (!transform) return null;
  return {
    x: transform.offsetX + (point.x + transform.paddingPx) * transform.scale,
    y: transform.offsetY + (point.y + transform.paddingPx) * transform.scale,
  };
}

function guideEditorClampPoint(point) {
  const transform = state.guideEditor.transform;
  if (!transform) return point;
  return {
    x: Math.max(-transform.paddingPx, Math.min(transform.cropWidth + transform.paddingPx, Number(point.x || 0))),
    y: Math.max(-transform.paddingPx, Math.min(transform.cropHeight + transform.paddingPx, Number(point.y || 0))),
  };
}

function guideEditorHandleAtCanvas(canvasX, canvasY) {
  const radius = 16;
  let best = null;

  const considerHandle = (handle, point) => {
    const canvasPoint = guideEditorCanvasPoint(point);
    if (!canvasPoint) return;
    const distance = Math.hypot(canvasPoint.x - canvasX, canvasPoint.y - canvasY);
    if (distance > radius) return;
    if (!best || distance < best.distance) {
      best = {...handle, distance};
    }
  };

  if (state.guideEditor.mode === 'edit') {
    state.guideEditor.segments.forEach((segment, segmentIndex) => {
      ['p0', 'p1', 'p2', 'p3'].forEach((pointKey) => {
        considerHandle({type: 'segment', segmentIndex, pointKey}, segment[pointKey]);
      });
    });
  } else {
    state.guideEditor.pendingPoints.forEach((point, pendingIndex) => {
      considerHandle({type: 'pending', pendingIndex}, point);
    });
  }
  return best;
}

function guideEditorUpdateHandlePoint(handle, point) {
  const clamped = guideEditorClampPoint(point);
  if (handle.type === 'segment') {
    const segment = state.guideEditor.segments[handle.segmentIndex];
    if (!segment) return;
    segment[handle.pointKey] = clamped;
    return;
  }
  if (handle.type === 'pending' && state.guideEditor.pendingPoints[handle.pendingIndex]) {
    state.guideEditor.pendingPoints[handle.pendingIndex] = clamped;
  }
}

function setGuideEditorZoom(value) {
  state.guideEditor.zoomPct = Math.max(50, Math.min(400, Number(value || 100)));
  state.guideEditor.recenterOnRender = true;
  if (dom.guideEditorZoom) {
    dom.guideEditorZoom.value = String(state.guideEditor.zoomPct);
  }
  if (dom.guideEditorZoomValue) {
    dom.guideEditorZoomValue.textContent = `${Math.round(state.guideEditor.zoomPct)}%`;
  }
  renderGuideEditor();
}

function renderGuideEditorCanvas() {
  const canvas = dom.guideEditorCanvas;
  const zoomScale = Math.max(0.5, Number(state.guideEditor.zoomPct || 100) / 100);
  canvas.width = Math.round(GUIDE_EDITOR_BASE_WIDTH * zoomScale);
  canvas.height = Math.round(GUIDE_EDITOR_BASE_HEIGHT * zoomScale);
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#f8f3e9';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const annotation = guideEditorAnnotation();
  if (!annotation || !dom.image.complete) {
    ctx.fillStyle = '#6f6757';
    ctx.font = '16px Georgia';
    ctx.fillText('Open a reviewed annotation to author a guide', 18, canvas.height / 2);
    state.guideEditor.transform = null;
    return;
  }
  const bounds = annotation.bounds_px;
  const cropWidth = Math.max(1, Number(bounds.width));
  const cropHeight = Math.max(1, Number(bounds.height));
  const paddingPx = Math.max(0, Number(state.guideEditor.paddingPx || 0));
  const paddedWidth = cropWidth + paddingPx * 2;
  const paddedHeight = cropHeight + paddingPx * 2;
  const scale = Math.min(canvas.width / paddedWidth, canvas.height / paddedHeight);
  const drawWidth = paddedWidth * scale;
  const drawHeight = paddedHeight * scale;
  const offsetX = (canvas.width - drawWidth) / 2;
  const offsetY = (canvas.height - drawHeight) / 2;
  state.guideEditor.transform = {offsetX, offsetY, scale, cropWidth, cropHeight, paddingPx};
  ctx.save();
  ctx.strokeStyle = 'rgba(49, 45, 34, 0.14)';
  ctx.setLineDash([6, 6]);
  ctx.strokeRect(offsetX + 0.5, offsetY + 0.5, drawWidth - 1, drawHeight - 1);
  ctx.restore();
  ctx.drawImage(
    dom.image,
    bounds.x,
    bounds.y,
    cropWidth,
    cropHeight,
    offsetX + paddingPx * scale,
    offsetY + paddingPx * scale,
    cropWidth * scale,
    cropHeight * scale
  );
  ctx.strokeStyle = 'rgba(34, 32, 24, 0.18)';
  ctx.strokeRect(offsetX + paddingPx * scale + 0.5, offsetY + paddingPx * scale + 0.5, cropWidth * scale - 1, cropHeight * scale - 1);
  if (state.guideEditor.recenterOnRender && dom.guideEditorCanvasViewport) {
    const wrap = dom.guideEditorCanvasViewport;
    const glyphCenterX = offsetX + paddingPx * scale + (cropWidth * scale) / 2;
    const glyphCenterY = offsetY + paddingPx * scale + (cropHeight * scale) / 2;
    requestAnimationFrame(() => {
      wrap.scrollLeft = Math.max(0, glyphCenterX - wrap.clientWidth / 2);
      wrap.scrollTop = Math.max(0, glyphCenterY - wrap.clientHeight / 2);
    });
    state.guideEditor.recenterOnRender = false;
  }
  canvas.classList.toggle('dragging', Boolean(state.guideEditor.draggingHandle));
  canvas.style.cursor = state.guideEditor.draggingHandle
    ? 'grabbing'
    : state.guideEditor.hoverHandle
      ? 'grab'
      : 'crosshair';

  state.guideEditor.segments.forEach((segment, index) => {
    const p0 = guideEditorCanvasPoint(segment.p0);
    const p1 = guideEditorCanvasPoint(segment.p1);
    const p2 = guideEditorCanvasPoint(segment.p2);
    const p3 = guideEditorCanvasPoint(segment.p3);
    ctx.save();
    ctx.strokeStyle = segment.contact ? '#1f5e36' : '#315d8f';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(p0.x, p0.y);
    ctx.bezierCurveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y);
    ctx.stroke();
    ctx.strokeStyle = 'rgba(110, 110, 110, 0.55)';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(p0.x, p0.y);
    ctx.lineTo(p1.x, p1.y);
    ctx.moveTo(p2.x, p2.y);
    ctx.lineTo(p3.x, p3.y);
    ctx.stroke();
    ctx.setLineDash([]);
    [p0, p1, p2, p3].forEach((point, pointIndex) => {
      const pointKey = `p${pointIndex}`;
      const handle = {type: 'segment', segmentIndex: index, pointKey};
      const isActive =
        guideEditorHandleMatches(state.guideEditor.hoverHandle, handle) ||
        guideEditorHandleMatches(state.guideEditor.draggingHandle, handle);
      ctx.beginPath();
      ctx.fillStyle =
        pointIndex === 0 || pointIndex === 3
          ? (isActive ? '#f59e0b' : '#b45309')
          : (isActive ? '#2563eb' : '#6b7280');
      ctx.arc(point.x, point.y, isActive ? 6 : pointIndex === 0 || pointIndex === 3 ? 4 : 3, 0, Math.PI * 2);
      ctx.fill();
      if (isActive) {
        ctx.lineWidth = 2;
        ctx.strokeStyle = 'rgba(17, 24, 39, 0.55)';
        ctx.stroke();
      }
      ctx.fillStyle = '#111827';
      ctx.font = '11px Georgia';
      ctx.fillText(pointKey, point.x + 6, point.y + 12);
    });
    ctx.fillStyle = '#111827';
    ctx.font = '14px Georgia';
    ctx.fillText(`${segment.stroke_order}`, p0.x + 6, p0.y - 6);
    ctx.restore();
  });

  state.guideEditor.pendingPoints.forEach((point, index) => {
    const p = guideEditorCanvasPoint(point);
    const handle = {type: 'pending', pendingIndex: index};
    const isActive =
      guideEditorHandleMatches(state.guideEditor.hoverHandle, handle) ||
      guideEditorHandleMatches(state.guideEditor.draggingHandle, handle);
    ctx.beginPath();
    ctx.fillStyle = '#dc2626';
    ctx.arc(p.x, p.y, isActive ? 6 : 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#dc2626';
    ctx.font = '12px Georgia';
    ctx.fillText(`p${index}`, p.x + 6, p.y - 6);
  });
}

function renderGuideEditor() {
  const annotation = guideEditorAnnotation();
  const manual = state.guideEditor.guideId
    ? currentManualGuides().find((entry) => entry.id === state.guideEditor.guideId) || null
    : (annotation ? currentManualGuideForAnnotation(annotation.id) : currentManualGuide());
  const rerun = currentSymbolRerun();
  dom.guideEditorSegments.innerHTML = '';
  dom.guideEditorSavedGuides.innerHTML = '';
  dom.guideEditorPreviewArtifacts.innerHTML = '';
  dom.guideEditorRerunArtifacts.innerHTML = '';
  if (!annotation) {
    dom.guideEditorTitle.textContent = 'Guide editor';
    dom.guideEditorMeta.textContent = 'Open a reviewed annotation from the symbol menu to author a manual guide.';
    dom.guideEditorRerunMeta.textContent = 'No processing preview yet.';
    renderGuideEditorCanvas();
    return;
  }
  dom.guideEditorTitle.textContent = `${annotation.kind} ${annotation.symbol}`;
  dom.guideEditorMeta.textContent =
    `${annotation.source_manuscript_label || 'unknown'} • ${annotation.canvas_label || 'unknown'} • ` +
    `${annotation.bounds_px.width}×${annotation.bounds_px.height}px crop`;
  dom.guideEditorXHeightPx.value = String(state.guideEditor.xHeightPx || annotation.bounds_px.height);
  dom.guideEditorXAdvancePx.value = String(state.guideEditor.xAdvancePx || annotation.bounds_px.width);
  dom.guideEditorCorridor.value = String(state.guideEditor.corridorHalfWidthMm || 0.2);
  dom.guideEditorPaddingPx.value = String(state.guideEditor.paddingPx || 32);
  dom.guideEditorZoom.value = String(state.guideEditor.zoomPct || 100);
  dom.guideEditorZoomValue.textContent = `${Math.round(state.guideEditor.zoomPct || 100)}%`;
  dom.guideEditorStrokeOrder.value = String(state.guideEditor.strokeOrder || 1);
  dom.guideEditorContact.checked = Boolean(state.guideEditor.contact);
  dom.guideEditorProcess.disabled = Boolean(rerun && rerun.status === 'running');
  dom.guideEditorProcess.textContent = rerun && rerun.status === 'running' ? 'Processing...' : 'Save And Process';
  dom.guideEditorModeAdd.classList.toggle('active', state.guideEditor.mode === 'add');
  dom.guideEditorModeEdit.classList.toggle('active', state.guideEditor.mode === 'edit');
  dom.guideEditorModeEdit.setAttribute('aria-disabled', state.guideEditor.segments.length ? 'false' : 'true');
  dom.guideEditorPending.textContent =
    state.guideEditor.mode === 'add'
      ? (
          state.guideEditor.pendingPoints.length
            ? `Add Segment mode. Pending cubic: ${state.guideEditor.pendingPoints.length}/4 points captured. Drag the red pending handles before the segment is committed.`
            : 'Add Segment mode. Click four points to add a cubic segment: p0, p1, p2, p3. Increase canvas padding when the handles need to sit outside the crop.'
        )
      : 'Edit Handles mode. Drag amber endpoints (p0, p3) to move the stroke ends and drag gray/blue handles (p1, p2) to bend the curve. Increase canvas padding when the handles need to sit outside the crop.';
  if (!state.guideEditor.segments.length) {
    const empty = document.createElement('div');
    empty.className = 'small';
    empty.textContent = 'No cubic segments yet.';
    dom.guideEditorSegments.appendChild(empty);
  } else {
    state.guideEditor.segments.forEach((segment, index) => {
      const row = document.createElement('div');
      row.className = 'guide-editor-segment';
      const title = document.createElement('strong');
      title.textContent = `Stroke ${segment.stroke_order} · ${segment.contact ? 'contact' : 'lift'}`;
      row.appendChild(title);
      const meta = document.createElement('div');
      meta.className = 'small';
      meta.textContent =
        `p0 (${Math.round(segment.p0.x)}, ${Math.round(segment.p0.y)}) → ` +
        `p3 (${Math.round(segment.p3.x)}, ${Math.round(segment.p3.y)})`;
      row.appendChild(meta);
      const actions = document.createElement('div');
      actions.className = 'reference-actions';
      const deleteButton = document.createElement('button');
      deleteButton.type = 'button';
      deleteButton.textContent = 'Delete Segment';
      deleteButton.addEventListener('click', () => {
        state.guideEditor.segments.splice(index, 1);
        if (!state.guideEditor.segments.length) {
          state.guideEditor.mode = 'add';
        }
        renderGuideEditor();
      });
      actions.appendChild(deleteButton);
      row.appendChild(actions);
      dom.guideEditorSegments.appendChild(row);
    });
  }
  const savedGuides = currentManualGuides();
  if (!savedGuides.length) {
    const empty = document.createElement('div');
    empty.className = 'small';
    empty.textContent = 'No saved guides yet for this symbol.';
    dom.guideEditorSavedGuides.appendChild(empty);
  } else {
    savedGuides.forEach((guide) => {
      const row = document.createElement('div');
      row.className = 'guide-editor-segment';
      const title = document.createElement('strong');
      title.textContent =
        `${guide.annotation_id === annotation.id ? 'Current annotation' : 'Saved guide'} ` +
        `· ${guide.canvas_label || 'unknown'}${guide.active ? ' · active' : ''}`;
      row.appendChild(title);
      const meta = document.createElement('div');
      meta.className = 'small';
      meta.textContent =
        `${guide.source_manuscript_label || 'unknown'} • ${guide.bounds_px.width}×${guide.bounds_px.height}px • updated ${guide.updated_at || 'n/a'}`;
      row.appendChild(meta);
      const actions = document.createElement('div');
      actions.className = 'reference-actions';
      const loadButton = document.createElement('button');
      loadButton.type = 'button';
      loadButton.textContent = guide.id === state.guideEditor.guideId ? 'Loaded' : 'Load';
      loadButton.disabled = guide.id === state.guideEditor.guideId;
      loadButton.addEventListener('click', () => {
        const entry = (state.payload.annotations || []).find((item) => item.id === guide.annotation_id);
        if (!entry) {
          setStatus('The saved guide source annotation is no longer present.', true);
          return;
        }
        openGuideEditorForAnnotation(entry, guide.id);
      });
      actions.appendChild(loadButton);
      const previewButton = document.createElement('button');
      previewButton.type = 'button';
      previewButton.textContent = 'Open Folio';
      previewButton.addEventListener('click', () => {
        const entry = (state.payload.annotations || []).find((item) => item.id === guide.annotation_id);
        if (entry) {
          openAnnotationReference(entry);
        }
      });
      actions.appendChild(previewButton);
      row.appendChild(actions);
      dom.guideEditorSavedGuides.appendChild(row);
    });
  }
  renderRerunArtifacts(dom.guideEditorPreviewArtifacts, manual?.preview_artifacts || null);
  if (rerun && rerun.status === 'running') {
    dom.guideEditorRerunMeta.textContent =
      `${rerun.status} · ${rerun.stage} · ${rerun.percent}%` +
      (rerun.message ? ` · ${rerun.message}` : '');
    renderRerunArtifacts(dom.guideEditorRerunArtifacts, null);
  } else if (rerun?.result?.artifacts) {
    dom.guideEditorRerunMeta.textContent =
      `${rerun.status} · ${rerun.stage} · ${rerun.percent}%` +
      (rerun.message ? ` · ${rerun.message}` : '');
    renderRerunArtifacts(dom.guideEditorRerunArtifacts, rerun.result.artifacts);
  } else {
    dom.guideEditorRerunMeta.textContent = 'No processing preview yet. Save and process this guide to inspect the downstream render.';
    renderRerunArtifacts(dom.guideEditorRerunArtifacts, null);
  }
  renderGuideEditorCanvas();
}

function openGuideEditorForAnnotation(entry, guideId = null) {
  state.currentSymbolKey = symbolKey(entry.kind, entry.symbol);
  openAnnotationReference(entry);
  const manual = guideId
    ? currentManualGuides().find((item) => item.id === guideId) || null
    : currentManualGuideForAnnotation(entry.id);
  state.guideEditor.annotationId = entry.id;
  state.guideEditor.guideId = manual?.id || guideId || null;
  state.guideEditor.symbolKey = symbolKey(entry.kind, entry.symbol);
  if (manual && manual.annotation_id === entry.id) {
    state.guideEditor.segments = (manual.segments || []).map((segment) => ({
      stroke_order: Number(segment.stroke_order || 1),
      contact: Boolean(segment.contact),
      p0: {...segment.p0},
      p1: {...segment.p1},
      p2: {...segment.p2},
      p3: {...segment.p3},
    }));
    state.guideEditor.xHeightPx = Number(manual.x_height_px || entry.bounds_px.height);
    state.guideEditor.xAdvancePx = Number(manual.x_advance_px || entry.bounds_px.width);
    state.guideEditor.corridorHalfWidthMm = Number(manual.corridor_half_width_mm || 0.2);
    state.guideEditor.paddingPx = Number(manual.canvas_padding_px || 32);
    state.guideEditor.strokeOrder = Math.max(1, ...state.guideEditor.segments.map((segment) => Number(segment.stroke_order || 1))) + 1;
  } else {
    state.guideEditor.segments = [];
    state.guideEditor.xHeightPx = Number(entry.bounds_px.height || 0);
    state.guideEditor.xAdvancePx = Number(entry.bounds_px.width || 0);
    state.guideEditor.corridorHalfWidthMm = 0.2;
    state.guideEditor.paddingPx = Math.max(24, Math.round(Math.max(Number(entry.bounds_px.width || 0), Number(entry.bounds_px.height || 0)) * 0.35));
    state.guideEditor.strokeOrder = 1;
    state.guideEditor.guideId = null;
  }
  state.guideEditor.pendingPoints = [];
  state.guideEditor.mode = state.guideEditor.segments.length ? 'edit' : 'add';
  state.guideEditor.zoomPct = 100;
  state.guideEditor.recenterOnRender = true;
  state.guideEditor.contact = true;
  state.guideEditor.hoverHandle = null;
  state.guideEditor.draggingHandle = null;
  state.guideEditor.dragMoved = false;
  state.guideEditor.suppressCanvasClick = false;
  dom.guideEditorModal.hidden = false;
  dom.guideEditorModal.setAttribute('aria-hidden', 'false');
  renderGuideEditor();
}

function closeGuideEditorModal() {
  dom.guideEditorModal.hidden = true;
  dom.guideEditorModal.setAttribute('aria-hidden', 'true');
}

function guideEditorEventToPoint(event) {
  const transform = state.guideEditor.transform;
  if (!transform) return null;
  const rect = dom.guideEditorCanvas.getBoundingClientRect();
  const canvasX = ((event.clientX - rect.left) / rect.width) * dom.guideEditorCanvas.width;
  const canvasY = ((event.clientY - rect.top) / rect.height) * dom.guideEditorCanvas.height;
  const x = (canvasX - transform.offsetX) / transform.scale - transform.paddingPx;
  const y = (canvasY - transform.offsetY) / transform.scale - transform.paddingPx;
  if (
    x < -transform.paddingPx ||
    y < -transform.paddingPx ||
    x > transform.cropWidth + transform.paddingPx ||
    y > transform.cropHeight + transform.paddingPx
  ) {
    return null;
  }
  return {x, y};
}

async function saveGuideEditor() {
  const annotation = guideEditorAnnotation();
  if (!annotation) {
    dom.guideEditorRerunMeta.textContent = 'Open a reviewed annotation first.';
    setStatus('Open a reviewed annotation first.', true);
    return null;
  }
  if (!state.guideEditor.segments.length) {
    dom.guideEditorRerunMeta.textContent = 'Add at least one cubic segment before saving the guide.';
    setStatus('Add at least one cubic segment before saving the guide.', true);
    return null;
  }
  try {
    dom.guideEditorRerunMeta.textContent = `Saving manual guide for ${annotation.kind} ${annotation.symbol}...`;
    const response = await fetch('/api/manual-guides', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        id: state.guideEditor.guideId,
        annotation_id: annotation.id,
        x_height_px: Number(dom.guideEditorXHeightPx.value || annotation.bounds_px.height),
        x_advance_px: Number(dom.guideEditorXAdvancePx.value || annotation.bounds_px.width),
        corridor_half_width_mm: Number(dom.guideEditorCorridor.value || 0.2),
        canvas_padding_px: Number(dom.guideEditorPaddingPx.value || 0),
        segments: state.guideEditor.segments,
      }),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    if (data.state) {
      state.payload = data.state;
      dom.manifestPath.textContent = state.payload.reviewed_manifest_path;
    }
    state.guideEditor.guideId = data.saved?.id || state.guideEditor.guideId;
    renderCoverage();
    renderFolios();
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
    renderSymbolMenu();
    renderGuideEditor();
    dom.guideEditorRerunMeta.textContent = `Saved manual guide for ${annotation.kind} ${annotation.symbol}.`;
    setStatus(`Saved manual guide for ${annotation.kind} ${annotation.symbol}`);
    return data;
  } catch (error) {
    dom.guideEditorRerunMeta.textContent = `Save failed: ${String(error)}`;
    setStatus(String(error), true);
    return null;
  }
}

async function deleteCurrentManualGuide() {
  const guideId = state.guideEditor.guideId || currentManualGuide()?.id;
  if (!guideId) {
    setStatus('No saved manual guide is selected.', true);
    return;
  }
  try {
    const response = await fetch(`/api/manual-guides/${encodeURIComponent(guideId)}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    if (data.state) {
      state.payload = data.state;
      dom.manifestPath.textContent = state.payload.reviewed_manifest_path;
    }
    state.guideEditor.guideId = null;
    state.guideEditor.segments = [];
    state.guideEditor.pendingPoints = [];
    state.guideEditor.mode = 'add';
    renderCoverage();
    renderFolios();
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
    renderSymbolMenu();
    renderGuideEditor();
    setStatus('Deleted manual guide.');
  } catch (error) {
    setStatus(String(error), true);
  }
}

async function processGuideEditor() {
  const saved = await saveGuideEditor();
  if (!saved) {
    return;
  }
  const status = currentSymbolStatus();
  if (!status) {
    dom.guideEditorRerunMeta.textContent = 'No symbol is selected for processing. Reopen the guide editor from the symbol menu.';
    setStatus('No symbol is selected for processing.', true);
    return;
  }
  try {
    dom.guideEditorRerunMeta.textContent = `Queued processing for ${status.kind} ${status.symbol}...`;
    dom.guideEditorRerunArtifacts.innerHTML = '';
    const response = await fetch('/api/symbol-reruns', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({kind: status.kind, symbol: status.symbol}),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    if (data.state) {
      state.payload = data.state;
      dom.manifestPath.textContent = state.payload.reviewed_manifest_path;
    }
    renderCoverage();
    renderFolios();
    renderAnnotations();
    renderOverlay();
    renderCleanupEditor();
    renderSymbolMenu();
    renderGuideEditor();
    setStatus(`Processing guide for ${status.kind} ${status.symbol}`);
    scheduleSymbolRerunPolling();
  } catch (error) {
    setStatus(String(error), true);
  }
}

function renderSelectedSymbolStatus() {
  const status = currentSymbolStatus();
  dom.symbolStatusCounts.innerHTML = '';
  dom.symbolStatusStages.innerHTML = '';
  if (!status) {
    dom.symbolStatusTitle.textContent = 'Selected Symbol Status';
    dom.symbolStatusMeta.textContent = 'Select a glyph or join from the symbol lists to inspect its processing history.';
    renderStatusBullets(dom.symbolStatusBlockers, [], 'No blocker details yet.');
    renderStatusBullets(dom.symbolStatusGuidance, [], 'No guidance yet.');
    renderStatusBullets(dom.symbolStatusSamples, [], 'No reference folios yet.');
    renderSymbolRerun();
    renderSymbolMenu();
    return;
  }

  dom.symbolStatusTitle.textContent = `${status.kind} ${status.symbol}`;
  dom.symbolStatusMeta.textContent = 'Processing history, blocker reasons, and manual selection guidance.';

  const countItems = [
    ['auto', status.counts.auto_admitted],
    ['quarantined', status.counts.quarantined],
    ['rejected', status.counts.rejected],
    ['repair-only', status.counts.repair_only],
    ['promoted', status.counts.promoted],
    ['reviewed', status.counts.reviewed],
  ];
  countItems.forEach(([label, value]) => {
    const pill = document.createElement('span');
    pill.className = 'pill';
    pill.textContent = `${label}: ${value}`;
    dom.symbolStatusCounts.appendChild(pill);
  });

  status.stage_statuses.forEach((stage) => {
    const row = document.createElement('div');
    row.className = 'status-row';
    const head = document.createElement('div');
    head.className = 'status-row-head';
    const title = document.createElement('strong');
    title.textContent = stage.stage;
    head.appendChild(title);
    const badge = document.createElement('span');
    badge.className = `status-badge ${stage.status}`;
    badge.textContent = stage.status.replace('_', ' ');
    head.appendChild(badge);
    row.appendChild(head);
    const detail = document.createElement('div');
    detail.className = 'small';
    detail.textContent = stage.detail;
    row.appendChild(detail);
    dom.symbolStatusStages.appendChild(row);
  });

  const blockers = (status.blockers || []).map((item) => ({
    text: item.source === 'promotion_gate' && item.count > 1 ? `${item.text} (${item.count} candidates)` : item.text,
    detail: item.source.replace('_', ' '),
  }));
  renderStatusBullets(dom.symbolStatusBlockers, blockers, 'No blocker reasons recorded.');
  renderStatusBullets(dom.symbolStatusGuidance, status.guidance || [], 'No guidance recorded.');
  const samples = (status.sample_refs || []).map((item) => ({
    text: item.label,
    detail: `${item.tier.replace('_', ' ')} · ${item.detail}`,
    folio_id: item.folio_id,
  }));
  renderStatusBullets(dom.symbolStatusSamples, samples, 'No reference folios recorded.', {
    asButtons: true,
    onClick: (item) => loadFolio(item.folio_id),
  });
  renderSymbolRerun();
  renderSymbolMenu();
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
  chooseInitialSymbol();
  state.payload.coverage_debt.forEach((entry) => {
    const card = document.createElement('div');
    const key = entry.status_key || symbolKey(entry.kind, entry.symbol);
    card.className = 'card' + (state.currentSymbolKey === key ? ' active' : '');
    const button = document.createElement('button');
    button.textContent = `${entry.kind} ${entry.symbol}`;
    button.addEventListener('click', () => {
      selectDebtSymbol(entry.kind, entry.symbol, {openMenu: true});
    });
    card.appendChild(button);
    const meta = document.createElement('div');
    meta.className = 'small';
    meta.textContent =
      `reviewed ${entry.reviewed_count} • promoted ${entry.promoted_count} • auto ${entry.auto_admitted_count} • ` +
      `quarantined ${entry.quarantined_count} • rejected ${entry.rejected_count}` +
      (entry.reviewed_excluded_count ? ` • excluded ${entry.reviewed_excluded_count}` : '');
    card.appendChild(meta);
    dom.coverageDebt.appendChild(card);
  });

  dom.coverageBrowser.innerHTML = '';
  browsableSymbols().forEach((entry) => {
    const key = entry.status_key || symbolKey(entry.kind, entry.symbol);
    const manual = Boolean(state.payload.manual_guides?.[key]);
    const card = document.createElement('div');
    card.className = 'card' + (state.currentSymbolKey === key ? ' active' : '');
    const button = document.createElement('button');
    button.textContent = `${entry.kind} ${entry.symbol}`;
    button.addEventListener('click', () => {
      selectDebtSymbol(entry.kind, entry.symbol, {openMenu: true});
    });
    card.appendChild(button);
    const meta = document.createElement('div');
    meta.className = 'small';
    meta.textContent =
      `reviewed ${entry.reviewed_count} • excluded ${entry.reviewed_excluded_count || 0} • ` +
      `promoted ${entry.promoted_count || 0}` +
      (manual ? ' • manual guide' : '');
    card.appendChild(meta);
    dom.coverageBrowser.appendChild(card);
  });
  renderSelectedSymbolStatus();
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
    if (data.state) {
      state.payload = data.state;
      dom.manifestPath.textContent = state.payload.reviewed_manifest_path;
    } else {
      state.payload.annotations = data.annotations;
    }
    state.selectedAnnotationId = data.saved.id;
    state.draftBounds = null;
    renderCoverage();
    renderFolios();
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
  await deleteAnnotationById(state.selectedAnnotationId);
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
  dom.symbolRerunButton.addEventListener('click', startSelectedSymbolRerun);
  dom.symbolMenuRerun.addEventListener('click', startSelectedSymbolRerun);
  dom.symbolMenuOpenRerun.addEventListener('click', openSymbolRerunModal);
  dom.symbolMenuGuideEditor.addEventListener('click', () => {
    const entry =
      currentSymbolAnnotations().find((item) => Boolean(item.catalog_included)) ||
      currentSymbolAnnotations()[0] ||
      currentManualGuideAnnotation();
    if (!entry) {
      setStatus('Save or restore a reviewed annotation for this symbol first.', true);
      return;
    }
    openGuideEditorForAnnotation(entry);
  });
  dom.symbolMenuDeleteGuide.addEventListener('click', deleteCurrentManualGuide);
  dom.symbolMenuClose.addEventListener('click', closeSymbolMenuModal);
  dom.symbolMenuModal.addEventListener('click', (event) => {
    if (event.target === dom.symbolMenuModal) {
      closeSymbolMenuModal();
    }
  });
  dom.guideEditorClose.addEventListener('click', closeGuideEditorModal);
  dom.guideEditorModal.addEventListener('click', (event) => {
    if (event.target === dom.guideEditorModal) {
      closeGuideEditorModal();
    }
  });
  dom.guideEditorModeAdd.addEventListener('click', () => {
    state.guideEditor.mode = 'add';
    state.guideEditor.hoverHandle = null;
    state.guideEditor.draggingHandle = null;
    renderGuideEditor();
  });
  dom.guideEditorModeEdit.addEventListener('click', () => {
    if (!state.guideEditor.segments.length) {
      setStatus('Add one segment first, then switch to Edit Handles.', true);
      return;
    }
    state.guideEditor.mode = 'edit';
    state.guideEditor.pendingPoints = [];
    state.guideEditor.hoverHandle = null;
    state.guideEditor.draggingHandle = null;
    renderGuideEditor();
  });
  dom.guideEditorCanvas.addEventListener('mousedown', (event) => {
    if (event.button !== 0) return;
    const rect = dom.guideEditorCanvas.getBoundingClientRect();
    const canvasX = ((event.clientX - rect.left) / rect.width) * dom.guideEditorCanvas.width;
    const canvasY = ((event.clientY - rect.top) / rect.height) * dom.guideEditorCanvas.height;
    const handle = guideEditorHandleAtCanvas(canvasX, canvasY);
    if (!handle) return;
    state.guideEditor.draggingHandle = handle;
    state.guideEditor.hoverHandle = handle;
    state.guideEditor.dragMoved = false;
    state.guideEditor.suppressCanvasClick = false;
    renderGuideEditor();
    event.preventDefault();
  });
  dom.guideEditorCanvas.addEventListener('mousemove', (event) => {
    const rect = dom.guideEditorCanvas.getBoundingClientRect();
    const canvasX = ((event.clientX - rect.left) / rect.width) * dom.guideEditorCanvas.width;
    const canvasY = ((event.clientY - rect.top) / rect.height) * dom.guideEditorCanvas.height;
    if (state.guideEditor.draggingHandle) {
      const point = guideEditorEventToPoint(event);
      if (!point) return;
      guideEditorUpdateHandlePoint(state.guideEditor.draggingHandle, point);
      state.guideEditor.dragMoved = true;
      renderGuideEditor();
      return;
    }
    const handle = guideEditorHandleAtCanvas(canvasX, canvasY);
    const nextHover = handle
      ? (handle.type === 'segment'
          ? {type: 'segment', segmentIndex: handle.segmentIndex, pointKey: handle.pointKey}
          : {type: 'pending', pendingIndex: handle.pendingIndex})
      : null;
    if (!guideEditorHandleMatches(state.guideEditor.hoverHandle, nextHover)) {
      state.guideEditor.hoverHandle = nextHover;
      renderGuideEditor();
    }
  });
  dom.guideEditorCanvas.addEventListener('mouseleave', () => {
    if (state.guideEditor.draggingHandle) return;
    if (state.guideEditor.hoverHandle) {
      state.guideEditor.hoverHandle = null;
      renderGuideEditor();
    }
  });
  window.addEventListener('mouseup', () => {
    if (!state.guideEditor.draggingHandle) return;
    state.guideEditor.suppressCanvasClick = state.guideEditor.dragMoved;
    state.guideEditor.draggingHandle = null;
    state.guideEditor.dragMoved = false;
    renderGuideEditor();
  });
  dom.guideEditorCanvas.addEventListener('click', (event) => {
    if (state.guideEditor.suppressCanvasClick) {
      state.guideEditor.suppressCanvasClick = false;
      return;
    }
    if (state.guideEditor.mode !== 'add') {
      return;
    }
    const point = guideEditorEventToPoint(event);
    if (!point) return;
    const rect = dom.guideEditorCanvas.getBoundingClientRect();
    const canvasX = ((event.clientX - rect.left) / rect.width) * dom.guideEditorCanvas.width;
    const canvasY = ((event.clientY - rect.top) / rect.height) * dom.guideEditorCanvas.height;
    if (guideEditorHandleAtCanvas(canvasX, canvasY)) {
      return;
    }
    state.guideEditor.pendingPoints.push(point);
    if (state.guideEditor.pendingPoints.length === 4) {
      state.guideEditor.segments.push({
        stroke_order: Number(dom.guideEditorStrokeOrder.value || state.guideEditor.strokeOrder || 1),
        contact: Boolean(dom.guideEditorContact.checked),
        p0: state.guideEditor.pendingPoints[0],
        p1: state.guideEditor.pendingPoints[1],
        p2: state.guideEditor.pendingPoints[2],
        p3: state.guideEditor.pendingPoints[3],
      });
      state.guideEditor.pendingPoints = [];
      state.guideEditor.strokeOrder = Number(dom.guideEditorStrokeOrder.value || state.guideEditor.strokeOrder || 1) + 1;
      dom.guideEditorStrokeOrder.value = String(state.guideEditor.strokeOrder);
      state.guideEditor.mode = 'edit';
    }
    renderGuideEditor();
  });
  dom.guideEditorClearPending.addEventListener('click', () => {
    state.guideEditor.pendingPoints = [];
    renderGuideEditor();
  });
  dom.guideEditorZoom.addEventListener('input', () => {
    setGuideEditorZoom(dom.guideEditorZoom.value);
  });
  dom.guideEditorZoomIn.addEventListener('click', () => {
    setGuideEditorZoom(Number(state.guideEditor.zoomPct || 100) + 25);
  });
  dom.guideEditorZoomOut.addEventListener('click', () => {
    setGuideEditorZoom(Number(state.guideEditor.zoomPct || 100) - 25);
  });
  dom.guideEditorZoomReset.addEventListener('click', () => {
    setGuideEditorZoom(100);
  });
  dom.guideEditorSave.addEventListener('click', saveGuideEditor);
  dom.guideEditorProcess.addEventListener('click', processGuideEditor);
  dom.guideEditorDelete.addEventListener('click', deleteCurrentManualGuide);
  dom.guideEditorXHeightPx.addEventListener('input', () => {
    state.guideEditor.xHeightPx = Number(dom.guideEditorXHeightPx.value || 0);
  });
  dom.guideEditorXAdvancePx.addEventListener('input', () => {
    state.guideEditor.xAdvancePx = Number(dom.guideEditorXAdvancePx.value || 0);
  });
  dom.guideEditorCorridor.addEventListener('input', () => {
    state.guideEditor.corridorHalfWidthMm = Number(dom.guideEditorCorridor.value || 0.2);
  });
  dom.guideEditorPaddingPx.addEventListener('input', () => {
    state.guideEditor.paddingPx = Number(dom.guideEditorPaddingPx.value || 0);
    state.guideEditor.recenterOnRender = true;
    renderGuideEditor();
  });
  dom.guideEditorStrokeOrder.addEventListener('input', () => {
    state.guideEditor.strokeOrder = Number(dom.guideEditorStrokeOrder.value || 1);
  });
  dom.guideEditorContact.addEventListener('change', () => {
    state.guideEditor.contact = Boolean(dom.guideEditorContact.checked);
  });
  dom.symbolRerunOpen.addEventListener('click', openSymbolRerunModal);
  dom.symbolRerunModalClose.addEventListener('click', closeSymbolRerunModal);
  dom.symbolRerunModal.addEventListener('click', (event) => {
    if (event.target === dom.symbolRerunModal) {
      closeSymbolRerunModal();
    }
  });
  window.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    if (!dom.symbolRerunModal.hidden) {
      closeSymbolRerunModal();
    }
    if (!dom.symbolMenuModal.hidden) {
      closeSymbolMenuModal();
    }
    if (!dom.guideEditorModal.hidden) {
      closeGuideEditorModal();
    }
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
  chooseInitialSymbol();
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
  renderGuideEditor();
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
      <h3>Reviewed And Guided Symbols</h3>
      <div id="coverage-browser" class="debt-list"></div>
      <div class="symbol-status">
        <h3 id="symbol-status-title">Selected Symbol Status</h3>
        <div id="symbol-status-meta" class="meta">Select a glyph or join from the symbol lists to inspect its processing history.</div>
        <div id="symbol-status-counts"></div>
        <h3>Pipeline Status</h3>
        <div id="symbol-status-stages" class="status-list"></div>
        <h3>Blockers</h3>
        <div id="symbol-status-blockers" class="status-bullets"></div>
        <h3>Selection Guidance</h3>
        <div id="symbol-status-guidance" class="status-bullets"></div>
        <h3>Reference Folios</h3>
        <div id="symbol-status-samples" class="status-bullets"></div>
        <h3>Quick Re-run</h3>
        <div id="symbol-rerun-meta" class="meta">Run a symbol-scoped reviewed pipeline diagnostic from the current reviewed manifest.</div>
        <div class="actions">
          <button id="symbol-rerun-button" type="button">Re-run This Symbol</button>
          <button id="symbol-rerun-open" type="button">Open Result Window</button>
        </div>
      </div>
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
  <div id="symbol-menu-modal" class="modal-backdrop" hidden aria-hidden="true">
    <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="symbol-menu-title">
      <div class="modal-head">
        <div>
          <h2 id="symbol-menu-title">Symbol references</h2>
          <div id="symbol-menu-meta" class="meta">Manage the reviewed references that freeze and evofit are allowed to consume for this symbol.</div>
        </div>
        <button id="symbol-menu-close" type="button">Close</button>
      </div>
      <div class="modal-body">
        <div class="modal-section">
          <div class="meta">Clicking a symbol in either left-hand symbol list opens this menu. Excluded references stay in the manifest for provenance, but they are pruned from downstream reviewed freeze and evofit.</div>
          <div class="actions">
            <button id="symbol-menu-rerun" type="button">Re-run This Symbol</button>
            <button id="symbol-menu-open-rerun" type="button">Open Rerun Results</button>
            <button id="symbol-menu-guide-editor" type="button">Guide Editor</button>
            <button id="symbol-menu-delete-guide" class="danger" type="button">Delete Manual Guide</button>
          </div>
        </div>
        <div class="modal-section">
          <h3>Reference Catalog</h3>
          <div id="symbol-reference-list" class="reference-list"></div>
        </div>
      </div>
    </div>
  </div>
  <div id="guide-editor-modal" class="modal-backdrop" hidden aria-hidden="true">
    <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="guide-editor-title">
      <div class="modal-head">
        <div>
          <h2 id="guide-editor-title">Guide editor</h2>
          <div id="guide-editor-meta" class="meta">Author ordered cubic guide strokes on top of a reviewed crop.</div>
        </div>
        <button id="guide-editor-close" type="button">Close</button>
      </div>
      <div class="modal-body guide-editor">
        <div class="guide-editor-canvas-wrap">
          <div class="guide-editor-zoom">
            <button id="guide-editor-zoom-out" type="button">-</button>
            <button id="guide-editor-zoom-in" type="button">+</button>
            <button id="guide-editor-zoom-reset" type="button">Reset</button>
            <label>
              Zoom
              <input id="guide-editor-zoom" type="range" min="50" max="400" step="10" value="100">
            </label>
            <span id="guide-editor-zoom-value" class="small">100%</span>
          </div>
          <div class="guide-editor-modes">
            <button id="guide-editor-mode-add" type="button" class="active">Add Segment</button>
            <button id="guide-editor-mode-edit" type="button">Edit Handles</button>
          </div>
          <div id="guide-editor-canvas-viewport" class="guide-editor-canvas-viewport">
            <canvas id="guide-editor-canvas" class="guide-editor-canvas" width="560" height="420"></canvas>
          </div>
          <div id="guide-editor-pending" class="guide-editor-pending">Click four points to add one cubic segment.</div>
        </div>
        <div class="guide-editor-side">
          <div class="modal-section">
            <h3>Guide Parameters</h3>
            <label>X-Height (px)
              <input id="guide-editor-x-height-px" type="number" min="1" step="0.1" value="1">
            </label>
            <label>X-Advance (px)
              <input id="guide-editor-x-advance-px" type="number" min="1" step="0.1" value="1">
            </label>
            <label>Corridor Half Width (mm)
              <input id="guide-editor-corridor" type="number" min="0.01" step="0.01" value="0.2">
            </label>
            <label>Canvas Padding (px)
              <input id="guide-editor-padding-px" type="number" min="0" step="1" value="32">
            </label>
            <label>Next Stroke Order
              <input id="guide-editor-stroke-order" type="number" min="1" step="1" value="1">
            </label>
            <label>
              <input id="guide-editor-contact" type="checkbox" checked>
              Contact Segment
            </label>
            <div class="actions">
              <button id="guide-editor-clear-pending" type="button">Clear Pending</button>
              <button id="guide-editor-save" class="primary" type="button">Save Manual Guide</button>
              <button id="guide-editor-process" type="button">Save And Process</button>
              <button id="guide-editor-delete" class="danger" type="button">Delete Guide</button>
            </div>
          </div>
          <div class="modal-section">
            <h3>Saved Guides For This Symbol</h3>
            <div id="guide-editor-saved-guides" class="guide-editor-segments"></div>
          </div>
          <div class="modal-section">
            <h3>Segments</h3>
            <div id="guide-editor-segments" class="guide-editor-segments"></div>
          </div>
          <div class="modal-section">
            <h3>Preview Artifacts</h3>
            <div id="guide-editor-preview-artifacts" class="artifact-grid"></div>
          </div>
          <div class="modal-section">
            <h3>Processing Preview</h3>
            <div id="guide-editor-rerun-meta" class="small">No processing preview yet.</div>
            <div id="guide-editor-rerun-artifacts" class="artifact-grid"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div id="symbol-rerun-modal" class="modal-backdrop" hidden aria-hidden="true">
    <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="symbol-rerun-modal-title">
      <div class="modal-head">
        <div>
          <h2 id="symbol-rerun-modal-title">Symbol rerun</h2>
          <div id="symbol-rerun-modal-meta" class="meta">Run a symbol-scoped reviewed pipeline diagnostic to inspect failures and artifacts.</div>
        </div>
        <button id="symbol-rerun-modal-close" type="button">Close</button>
      </div>
      <div class="modal-body">
        <div class="modal-section">
          <h3>Diagnostics</h3>
          <div id="symbol-rerun-details" class="status-bullets"></div>
        </div>
        <div class="modal-section">
          <h3>Artifacts</h3>
          <div id="symbol-rerun-artifacts" class="artifact-grid wide"></div>
        </div>
      </div>
    </div>
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
        if parsed.path == "/api/artifact":
            raw_path = parse_qs(parsed.query).get("path", [""])[0]
            try:
                body, content_type = self.workbench.read_artifact(raw_path)
            except Exception as exc:  # pragma: no cover - defensive server error
                self._send_text(str(exc), status=404)
                return
            self._send_bytes(body, content_type=content_type)
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
        if parsed.path == "/api/symbol-reruns":
            try:
                payload = self._read_json_body()
                started = self.workbench.start_symbol_rerun(
                    str(payload.get("kind", "")),
                    str(payload.get("symbol", "")),
                )
                self._send_json({"started": started, "state": self.workbench.get_state()})
            except Exception as exc:
                self._send_text(str(exc), status=400)
            return
        if parsed.path == "/api/manual-guides":
            try:
                payload = self._read_json_body()
                saved = self.workbench.save_manual_guide(payload)
                self._send_json(
                    {
                        "saved": saved,
                        "state": self.workbench.get_state(),
                    }
                )
            except Exception as exc:
                self._send_text(str(exc), status=400)
            return
        if parsed.path == "/api/annotations/catalog":
            try:
                payload = self._read_json_body()
                updated = self.workbench.set_annotation_catalog_included(
                    str(payload.get("id", "")),
                    bool(payload.get("catalog_included", True)),
                )
                self._send_json(
                    {
                        "updated": updated,
                        "annotations": self.workbench.list_annotations(),
                        "state": self.workbench.get_state(),
                    }
                )
            except Exception as exc:
                self._send_text(str(exc), status=400)
            return
        if parsed.path != "/api/annotations":
            self._send_text("not found", status=404)
            return
        try:
            payload = self._read_json_body()
            saved = self.workbench.save_annotation(payload)
            self._send_json(
                {
                    "saved": saved,
                    "annotations": self.workbench.list_annotations(),
                    "state": self.workbench.get_state(),
                }
            )
        except Exception as exc:
            self._send_text(str(exc), status=400)

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/manual-guides/"):
            guide_id = unquote(parsed.path.rsplit("/", 1)[-1])
            deleted = self.workbench.delete_manual_guide(guide_id)
            if not deleted:
                self._send_text("not found", status=404)
                return
            self._send_json(
                {
                    "deleted": guide_id,
                    "state": self.workbench.get_state(),
                }
            )
            return
        if not parsed.path.startswith("/api/annotations/"):
            self._send_text("not found", status=404)
            return
        annotation_id = parsed.path.rsplit("/", 1)[-1]
        deleted = self.workbench.delete_annotation(annotation_id)
        if not deleted:
            self._send_text("annotation not found", status=404)
            return
        self._send_json(
            {
                "deleted": annotation_id,
                "annotations": self.workbench.list_annotations(),
                "state": self.workbench.get_state(),
            }
        )


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
