#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple

DEFAULT_WORKSPACE = Path("auto-pts/autopts/workspaces/zephyr/zephyr-master/zephyr-master.pqw6")
DEFAULT_OUTPUT = Path("tools/runtime_active_tcids.json")
DEFAULT_HISTORY_DIR = Path("tools/runtime_history")

PROFILE_PREFIXES = {
    "DIS": "DIS/",
    "BAS": "BAS/",
    "HRS": "HRS/",
    "HID": "HOGP/",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export deterministic runtime-active TCIDs from PTS "
            "using get_test_case_list(project) for all workspace projects."
        )
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE,
        help=f"Path to PTS workspace (.pqw6). Default: {DEFAULT_WORKSPACE}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSON path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--copy-workspace",
        action="store_true",
        help="Open a temporary copy of the workspace (safe when multiple sessions use the same workspace).",
    )
    parser.add_argument(
        "--history-dir",
        type=Path,
        default=DEFAULT_HISTORY_DIR,
        help=f"Directory for timestamped snapshot history copies. Default: {DEFAULT_HISTORY_DIR}",
    )
    parser.add_argument(
        "--skip-history",
        action="store_true",
        help="Do not write timestamped history copy.",
    )
    return parser.parse_args()


def add_autopts_repo_to_sys_path(repo_root: Path) -> None:
    autopts_repo = repo_root / "auto-pts"
    if str(autopts_repo) not in sys.path:
        sys.path.insert(0, str(autopts_repo))


def collect_project_active_tcids(workspace: Path, copy_workspace: bool) -> Dict[str, List[str]]:
    # Import lazily so this script fails gracefully on non-Windows hosts.
    from autopts.ptscontrol import PyPTS  # type: ignore

    pts = PyPTS(lite_start=True)
    project_cases: Dict[str, List[str]] = {}

    try:
        pts.start_pts()
        pts.open_workspace(str(workspace), copy=copy_workspace)
        for project in sorted(pts.get_project_list()):
            tcids = sorted(set(pts.get_test_case_list(project)))
            project_cases[project] = tcids
    finally:
        try:
            pts.stop_pts()
        except Exception:
            pass
        try:
            pts.terminate()
        except Exception:
            pass

    return project_cases


def split_tcids_by_profile(project_cases: Dict[str, List[str]]) -> Tuple[Dict[str, Dict], List[str]]:
    all_tcids: Set[str] = set()
    for tcids in project_cases.values():
        all_tcids.update(tcid for tcid in tcids if isinstance(tcid, str) and tcid)

    all_sorted = sorted(all_tcids)
    profiles: Dict[str, Dict] = {}
    for profile, prefix in PROFILE_PREFIXES.items():
        active_tcids = [tcid for tcid in all_sorted if tcid.startswith(prefix)]
        projects = sorted(
            project for project, tcids in project_cases.items() if any(tcid.startswith(prefix) for tcid in tcids)
        )
        profiles[profile] = {
            "project": projects[0] if len(projects) == 1 else None,
            "projects": projects,
            "active_tcids": active_tcids,
            "count": len(active_tcids),
        }

    return profiles, all_sorted


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    workspace = args.workspace
    if not workspace.is_absolute():
        workspace = repo_root / workspace
    output = args.output
    if not output.is_absolute():
        output = repo_root / output
    history_dir = args.history_dir
    if not history_dir.is_absolute():
        history_dir = repo_root / history_dir

    if platform.system().lower() != "windows":
        print(
            "ERROR: This exporter must run on Windows with installed PTS COM server.",
            file=sys.stderr,
        )
        return 2

    if not workspace.exists():
        print(f"ERROR: workspace not found: {workspace}", file=sys.stderr)
        return 2

    if workspace.suffix.lower() != ".pqw6":
        print(f"ERROR: workspace must be a .pqw6 file: {workspace}", file=sys.stderr)
        return 2

    add_autopts_repo_to_sys_path(repo_root)

    try:
        project_cases = collect_project_active_tcids(workspace, copy_workspace=args.copy_workspace)
    except Exception as exc:
        print(f"ERROR: failed to collect active TCIDs from PTS: {exc}", file=sys.stderr)
        return 1

    profiles, all_tcids = split_tcids_by_profile(project_cases)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workspace": str(workspace),
        "export_tool": "tools/export_runtime_active_tcids.py",
        "platform": platform.platform(),
        "profile_prefixes": PROFILE_PREFIXES,
        "projects": {project: {"active_tcids": tcids, "count": len(tcids)} for project, tcids in project_cases.items()},
        "profiles": profiles,
        "all_active_tcids": all_tcids,
        "all_active_count": len(all_tcids),
    }

    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialized, encoding="utf-8")

    history_path = None
    if not args.skip_history:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        history_dir.mkdir(parents=True, exist_ok=True)
        history_path = history_dir / f"runtime_active_tcids_{stamp}.json"
        history_path.write_text(serialized, encoding="utf-8")

    print(f"WROTE {output}")
    if history_path is not None:
        print(f"WROTE {history_path}")
    print(f"Workspace: {workspace}")
    print(f"Projects scanned: {len(project_cases)}")
    for profile in ("DIS", "BAS", "HRS", "HID"):
        print(f"{profile}: {profiles[profile]['count']} active TCIDs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
