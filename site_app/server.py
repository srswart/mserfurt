"""Production HTTP server for the MS Erfurt showcase.

Clean routes, gzip for text, and long-lived caching for built assets.
Fly.io app ``ms-erfurt`` listens on port 8080.
"""

from __future__ import annotations

import argparse
import gzip
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_DIST = Path("site/dist")

PAGE_ROUTES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/main.dc.html": "index.html",
    "/reader": "reader.html",
    "/reader.html": "reader.html",
    "/reader.dc.html": "reader.html",
    "/viewer": "viewer.html",
    "/viewer.html": "viewer.html",
    "/viewer.dc.html": "viewer.html",
    "/folios": "folios.html",
    "/folios.html": "folios.html",
    "/folios.dc.html": "folios.html",
    "/colophon": "colophon.html",
    "/colophon.html": "colophon.html",
    "/colophonsealed.dc.html": "colophon.html",
    "/colophon.dc.html": "colophon.html",
}

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
    ".txt": "text/plain; charset=utf-8",
    ".pdf": "application/pdf",
}

COMPRESSIBLE = {".html", ".css", ".js", ".json", ".svg", ".txt"}


def resolve_route_file(path: str, dist_dir: Path) -> Path:
    """Map a request path to a file under ``dist_dir``.

    Design-bundle aliases (``/Reader.dc.html`` and the rest) resolve to the
    generated pages. Other paths are static files, with directory traversal
    refused.
    """
    dist_dir = Path(dist_dir)
    raw = urlsplit(path).path or "/"
    if raw != "/" and raw.endswith("/"):
        raw = raw.rstrip("/") or "/"
    page = PAGE_ROUTES.get(raw.lower())
    if page:
        return dist_dir / page
    relative = raw.lstrip("/")
    candidate = (dist_dir / relative).resolve()
    root = dist_dir.resolve()
    if candidate != root and root not in candidate.parents:
        return dist_dir / "index.html"
    return candidate


class SiteHandler(BaseHTTPRequestHandler):
    dist_dir = DEFAULT_DIST

    def do_GET(self) -> None:  # noqa: N802
        self._serve(include_body=True)

    def do_HEAD(self) -> None:  # noqa: N802
        self._serve(include_body=False)

    def _serve(self, *, include_body: bool) -> None:
        path = urlsplit(self.path).path or "/"
        if path == "/healthz":
            body = b"ok\n"
            self._write(200, body, "text/plain; charset=utf-8", "no-store", include_body)
            return
        file_path = resolve_route_file(self.path, self.dist_dir)
        if not file_path.is_file():
            self._write(404, b"Not found\n", "text/plain; charset=utf-8", "no-store", include_body)
            return
        payload = file_path.read_bytes()
        suffix = file_path.suffix.lower()
        mime = MIME_TYPES.get(suffix, "application/octet-stream")
        relative = file_path.resolve().relative_to(self.dist_dir.resolve()).as_posix()
        if path.lower() in PAGE_ROUTES or suffix in {".html", ".css", ".js"}:
            cache = "no-cache"
        elif relative.startswith("assets/"):
            cache = "public, max-age=31536000, immutable"
        else:
            cache = "public, max-age=300"
        self._write(200, payload, mime, cache, include_body, suffix=suffix)

    def _write(
        self,
        status: int,
        payload: bytes,
        mime: str,
        cache: str,
        include_body: bool,
        suffix: str = "",
    ) -> None:
        accept = self.headers.get("Accept-Encoding", "")
        if suffix in COMPRESSIBLE and "gzip" in accept and len(payload) > 800:
            payload = gzip.compress(payload, compresslevel=6)
            encoding = "gzip"
        else:
            encoding = ""
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        if encoding:
            self.send_header("Content-Encoding", encoding)
            self.send_header("Vary", "Accept-Encoding")
        self.end_headers()
        if include_body:
            self.wfile.write(payload)

    def log_message(self, fmt: str, *args: object) -> None:
        if str(args[1:2]) == "('404',)" or (args and str(args[1]) == "404"):
            super().log_message(fmt, *args)
            return
        super().log_message(fmt, *args)


def serve(dist_dir: Path, host: str, port: int) -> None:
    SiteHandler.dist_dir = Path(dist_dir)
    server = ThreadingHTTPServer((host, port), SiteHandler)
    print(f"MS Erfurt site listening on http://{host}:{port} ({SiteHandler.dist_dir})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the MS Erfurt showcase.")
    parser.add_argument("--dist", type=Path, default=Path(os.environ.get("SITE_DIST", "site/dist")))
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    args = parser.parse_args()
    serve(args.dist, args.host, args.port)


if __name__ == "__main__":
    main()
