from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.import_service import ImportService

PROJECT_ROOT = Path(__file__).resolve().parent
STATIC_DIR = PROJECT_ROOT / "static"
service = ImportService(PROJECT_ROOT)


class ImportRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/import/preview":
            self._handle_preview()
            return

        if self.path == "/api/import/commit":
            self._handle_commit()
            return

        if self.path == "/api/import/progress":
            self._handle_progress_import()
            return

        self._send_json({"error": "Route introuvable"}, status=HTTPStatus.NOT_FOUND)

    def _read_request_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _handle_preview(self) -> None:
        try:
            payload = self._read_request_json()
            data = service.preview_source(payload.get("sourceType", ""), payload.get("sourcePath", ""))
            self._send_json(data)
        except Exception as exc:  # noqa: BLE001
            service.logger.exception("Preview endpoint failed")
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _handle_commit(self) -> None:
        try:
            payload = self._read_request_json()
            data = service.import_source(payload.get("sourceType", ""), payload.get("sourcePath", ""))
            self._send_json(data)
        except Exception as exc:  # noqa: BLE001
            service.logger.exception("Import endpoint failed")
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _handle_progress_import(self) -> None:
        try:
            payload = self._read_request_json()
            data = service.import_progress(payload)
            self._send_json(data)
        except Exception as exc:  # noqa: BLE001
            service.logger.exception("Progress endpoint failed")
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080
    server = ThreadingHTTPServer((host, port), ImportRequestHandler)
    print(f"Import UI disponible sur http://{host}:{port}/import.html")
    server.serve_forever()
