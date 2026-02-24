#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict


ROOT_DIR = Path(__file__).resolve().parent
RUN_STATUS_FILE = ROOT_DIR / "data" / "run-status-state.json"
API_PATH = "/api/run-status"
SCHEMA_VERSION = 1


def normalize_run_status_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")
    entries = payload.get("entries")
    if entries is None:
        entries = {}
    if not isinstance(entries, dict):
        raise ValueError("'entries' must be an object")
    version = payload.get("version", SCHEMA_VERSION)
    try:
        version = int(version)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("'version' must be an integer") from exc
    normalized = {
        "version": version,
        "updated_at": payload.get("updated_at"),
        "entries": entries,
    }
    return normalized


def ensure_run_status_file() -> None:
    if RUN_STATUS_FILE.exists():
        return
    RUN_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    seed = {"version": SCHEMA_VERSION, "updated_at": None, "entries": {}}
    RUN_STATUS_FILE.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_run_status_payload() -> Dict[str, Any]:
    ensure_run_status_file()
    raw = json.loads(RUN_STATUS_FILE.read_text(encoding="utf-8"))
    return normalize_run_status_payload(raw)


def write_run_status_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_run_status_payload(payload)
    normalized["updated_at"] = datetime.now(timezone.utc).isoformat()
    RUN_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(RUN_STATUS_FILE.parent),
        prefix="run-status-",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(RUN_STATUS_FILE)
    return normalized


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def _write_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            raise ValueError("Empty request body")
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON body") from exc

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self.path != API_PATH:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Allow", "GET, PUT, OPTIONS")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == API_PATH:
            try:
                payload = read_run_status_payload()
            except Exception as exc:  # noqa: BLE001
                self._write_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"ok": False, "error": f"Failed to read run-status file: {exc}"},
                )
                return
            self._write_json(HTTPStatus.OK, payload)
            return
        super().do_GET()

    def do_PUT(self) -> None:  # noqa: N802
        if self.path != API_PATH:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            payload = self._read_json_body()
            saved = write_run_status_payload(payload)
        except ValueError as exc:
            self._write_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001
            self._write_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": f"Failed to write run-status file: {exc}"},
            )
            return
        self._write_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "file": str(RUN_STATUS_FILE.relative_to(ROOT_DIR)),
                "updated_at": saved.get("updated_at"),
                "entries_count": len(saved.get("entries") or {}),
            },
        )

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        super().log_message(format, *args)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve pts_report_he with file-backed run-status API.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", default=8000, type=int, help="Bind port (default: 8000)")
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the dashboard URL in the default browser automatically.",
    )
    args = parser.parse_args()

    ensure_run_status_file()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Serving {ROOT_DIR} at {url}")
    print(f"Run-status API: {url}api/run-status")
    print(f"File-backed storage: {RUN_STATUS_FILE}")
    if not args.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
