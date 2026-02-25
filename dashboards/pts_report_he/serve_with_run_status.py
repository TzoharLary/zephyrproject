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
GROUP_B_TASKS_FILE = ROOT_DIR / "autopts" / "data" / "group-b-task-state.json"
GROUP_B_TASKS_API_PATH = "/api/group-b-tasks"
SCHEMA_VERSION = 1
GROUP_B_TASKS_SCHEMA_VERSION = 1
GROUP_B_TASKS_PROFILE_IDS = ("BPS", "WSS", "SCPS")


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


def normalize_group_b_tasks_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")
    profiles = payload.get("profiles")
    if profiles is None:
        profiles = {}
    if not isinstance(profiles, dict):
        raise ValueError("'profiles' must be an object")
    version = payload.get("version", GROUP_B_TASKS_SCHEMA_VERSION)
    try:
        version = int(version)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("'version' must be an integer") from exc

    norm_profiles: Dict[str, Any] = {}
    for pid in GROUP_B_TASKS_PROFILE_IDS:
        raw_profile = profiles.get(pid, {})
        if raw_profile is None:
            raw_profile = {}
        if not isinstance(raw_profile, dict):
            raise ValueError(f"'profiles.{pid}' must be an object")
        tasks = raw_profile.get("tasks", {})
        if tasks is None:
            tasks = {}
        if not isinstance(tasks, dict):
            raise ValueError(f"'profiles.{pid}.tasks' must be an object")
        norm_tasks: Dict[str, Any] = {}
        for task_id, task in tasks.items():
            if not isinstance(task_id, str) or not task_id.strip():
                raise ValueError(f"'profiles.{pid}.tasks' contains invalid task id")
            if task is None:
                task = {}
            if not isinstance(task, dict):
                raise ValueError(f"'profiles.{pid}.tasks.{task_id}' must be an object")
            depends_on = task.get("depends_on", [])
            if depends_on is None:
                depends_on = []
            if not isinstance(depends_on, list):
                raise ValueError(f"'profiles.{pid}.tasks.{task_id}.depends_on' must be a list")
            norm_tasks[task_id] = {
                "assignee": task.get("assignee", ""),
                "status": task.get("status", "todo"),
                "priority": task.get("priority", "medium"),
                "notes": task.get("notes", ""),
                "blocked_reason": task.get("blocked_reason", ""),
                "depends_on": [str(x) for x in depends_on if str(x).strip()],
                "updated_at": task.get("updated_at"),
                "updated_by": task.get("updated_by", ""),
            }
        norm_profiles[pid] = {"tasks": norm_tasks}

    return {
        "version": version,
        "updated_at": payload.get("updated_at"),
        "profiles": norm_profiles,
    }


def ensure_run_status_file() -> None:
    if RUN_STATUS_FILE.exists():
        return
    RUN_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    seed = {"version": SCHEMA_VERSION, "updated_at": None, "entries": {}}
    RUN_STATUS_FILE.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_group_b_tasks_file() -> None:
    if GROUP_B_TASKS_FILE.exists():
        return
    GROUP_B_TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    seed = {
        "version": GROUP_B_TASKS_SCHEMA_VERSION,
        "updated_at": None,
        "profiles": {pid: {"tasks": {}} for pid in GROUP_B_TASKS_PROFILE_IDS},
    }
    GROUP_B_TASKS_FILE.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_run_status_payload() -> Dict[str, Any]:
    ensure_run_status_file()
    raw = json.loads(RUN_STATUS_FILE.read_text(encoding="utf-8"))
    return normalize_run_status_payload(raw)


def read_group_b_tasks_payload() -> Dict[str, Any]:
    ensure_group_b_tasks_file()
    raw = json.loads(GROUP_B_TASKS_FILE.read_text(encoding="utf-8"))
    return normalize_group_b_tasks_payload(raw)


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


def write_group_b_tasks_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_group_b_tasks_payload(payload)
    normalized["updated_at"] = datetime.now(timezone.utc).isoformat()
    GROUP_B_TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(GROUP_B_TASKS_FILE.parent),
        prefix="group-b-tasks-",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(GROUP_B_TASKS_FILE)
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
        if self.path not in {API_PATH, GROUP_B_TASKS_API_PATH}:
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
        if self.path == GROUP_B_TASKS_API_PATH:
            try:
                payload = read_group_b_tasks_payload()
            except Exception as exc:  # noqa: BLE001
                self._write_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"ok": False, "error": f"Failed to read group-b tasks file: {exc}"},
                )
                return
            self._write_json(HTTPStatus.OK, payload)
            return
        super().do_GET()

    def do_PUT(self) -> None:  # noqa: N802
        if self.path not in {API_PATH, GROUP_B_TASKS_API_PATH}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            payload = self._read_json_body()
            if self.path == API_PATH:
                saved = write_run_status_payload(payload)
            else:
                saved = write_group_b_tasks_payload(payload)
        except ValueError as exc:
            self._write_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001
            self._write_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": f"Failed to write run-status file: {exc}"},
            )
            return
        if self.path == API_PATH:
            self._write_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "file": str(RUN_STATUS_FILE.relative_to(ROOT_DIR)),
                    "updated_at": saved.get("updated_at"),
                    "entries_count": len(saved.get("entries") or {}),
                },
            )
            return
        task_profiles = saved.get("profiles") if isinstance(saved, dict) else {}
        tasks_count = 0
        if isinstance(task_profiles, dict):
            for pid in GROUP_B_TASKS_PROFILE_IDS:
                tasks = ((task_profiles.get(pid) or {}).get("tasks") if isinstance(task_profiles.get(pid), dict) else {})
                if isinstance(tasks, dict):
                    tasks_count += len(tasks)
        self._write_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "file": str(GROUP_B_TASKS_FILE.relative_to(ROOT_DIR)),
                "updated_at": saved.get("updated_at"),
                "profiles_count": len(GROUP_B_TASKS_PROFILE_IDS),
                "tasks_count": tasks_count,
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
    ensure_group_b_tasks_file()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Serving {ROOT_DIR} at {url}")
    print(f"Run-status API: {url}api/run-status")
    print(f"Group B tasks API: {url}api/group-b-tasks")
    print(f"File-backed storage: {RUN_STATUS_FILE}")
    print(f"Group B tasks file: {GROUP_B_TASKS_FILE}")
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
