from __future__ import annotations

import ast
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

try:
    import tomllib  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    tomllib = None


CLI_GROUPS = {
    "connection_network": "Connection / Network",
    "test_selection": "Test selection",
    "retries_recovery": "Retries / Recovery",
    "pts_ports": "PTS / Client ports",
    "iut_mode_transport": "IUT mode / transport",
    "board_hw_jlink_rtt": "Board / HW / JLink / RTT",
    "qemu_native_btpclient": "QEMU / Native / btpclient",
    "logging_debug": "Logging / Debug",
    "advanced_internal": "Advanced / Internal",
    "positional": "Positional arguments",
    "other": "Other",
}

REQUIRED_TOP_LEVEL_KEYS = [
    "meta",
    "overview",
    "architecture",
    "quickstart",
    "cli",
    "execution_flow",
    "test_support_3_layers",
    "stacks",
    "profiles_inventory",
    "workspaces_inventory",
    "wid_inventory",
    "btp_inventory",
    "tools_inventory",
    "logs_and_outputs",
    "troubleshooting",
    "extending_autopts",
    "official_sources",
    "sources_index",
    "known_limits",
]

TCID_LITERAL_RE = re.compile(r"\b[A-Z0-9]+(?:/[A-Z0-9]+){2,}/(?:BV|BI)-\d+-[A-Z](?:[_-]LT[23])?\b")
WID_HANDLER_RE = re.compile(r"^def\s+hdl_wid_(\d+)\s*\(", re.MULTILINE)
XML_PROJECT_RE = re.compile(r'<PROJECT_INFORMATION\s+NAME="([^"]+)"')


@dataclass(frozen=True)
class Paths:
    repo: Path
    tools: Path
    autopts_repo: Path
    autopts_pkg: Path
    ptsprojects: Path
    wid_dir: Path
    pybtp_btp_dir: Path
    autopts_tools_dir: Path
    autopts_docs_dir: Path
    autopts_workspaces_dir: Path
    templates_dir: Path
    official_sources_json: Path
    builder_script: Path


def _paths(repo_root: Path | str = ".") -> Paths:
    repo = Path(repo_root).resolve()
    tools = repo / "tools"
    autopts_repo = repo / "auto-pts"
    return Paths(
        repo=repo,
        tools=tools,
        autopts_repo=autopts_repo,
        autopts_pkg=autopts_repo / "autopts",
        ptsprojects=autopts_repo / "autopts" / "ptsprojects",
        wid_dir=autopts_repo / "autopts" / "wid",
        pybtp_btp_dir=autopts_repo / "autopts" / "pybtp" / "btp",
        autopts_tools_dir=autopts_repo / "tools",
        autopts_docs_dir=autopts_repo / "doc",
        autopts_workspaces_dir=autopts_repo / "autopts" / "workspaces",
        templates_dir=tools / "templates" / "pts_report_he",
        official_sources_json=tools / "data" / "autopts_official_sources.json",
        builder_script=tools / "build_pts_report_bundle.py",
    )


def repo_source(paths: Paths, path: Path, line: Optional[int] = None, note: Optional[str] = None) -> Dict[str, Any]:
    try:
        shown = path.resolve().relative_to(paths.repo)
    except Exception:
        shown = path
    out: Dict[str, Any] = {"file": str(shown).replace("\\", "/")}
    if line is not None:
        out["line"] = int(line)
    if note:
        out["note"] = str(note)
    return out


def web_source(url: str, title: str, retrieved_at: str, note: Optional[str] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {"url": url, "title": title, "retrieved_at": retrieved_at}
    if note:
        out["note"] = note
    return out


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_lines(path: Path) -> List[str]:
    return read_text(path).splitlines()


def find_line_contains(path: Path, needle: str) -> Optional[int]:
    for i, line in enumerate(read_lines(path), start=1):
        if needle in line:
            return i
    return None


def find_line_regex(path: Path, pattern: str) -> Optional[int]:
    rx = re.compile(pattern)
    for i, line in enumerate(read_lines(path), start=1):
        if rx.search(line):
            return i
    return None


def parse_python(path: Path) -> ast.AST:
    return ast.parse(read_text(path), filename=str(path))


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def ast_value(node: Optional[ast.AST]) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        pass
    if isinstance(node, ast.Attribute):
        return dotted_name(node)
    if isinstance(node, ast.Name):
        return f"<{node.id}>"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = ast_value(node.left)
        right = ast_value(node.right)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
    if isinstance(node, ast.JoinedStr):
        parts: List[str] = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                parts.append(part.value)
            else:
                parts.append("{...}")
        return "".join(parts)
    if isinstance(node, ast.List):
        return [ast_value(x) for x in node.elts]
    if isinstance(node, ast.Tuple):
        return [ast_value(x) for x in node.elts]
    if isinstance(node, ast.Call):
        return f"<{dotted_name(node.func) or 'call'}()>"
    return f"<{node.__class__.__name__}>"


def parse_pyproject(paths: Paths) -> Dict[str, Any]:
    path = paths.autopts_repo / "pyproject.toml"
    out: Dict[str, Any] = {"path": str(path.relative_to(paths.repo)).replace("\\", "/")}
    if path.exists() and tomllib is not None:
        try:
            parsed = tomllib.loads(read_text(path))
            project = parsed.get("project", {}) if isinstance(parsed, dict) else {}
            if isinstance(project, dict):
                for key in ("name", "version", "description"):
                    if key in project:
                        out[key] = project[key]
        except Exception:
            pass
    return out


def extract_top_constants(path: Path, names: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    tree = parse_python(path)
    wanted = set(names)
    out: Dict[str, Dict[str, Any]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                out[target.id] = {"value": ast_value(node.value), "line": getattr(node, "lineno", None)}
    return out


def extract_file_paths_keys(paths: Paths, config_py: Path) -> List[Dict[str, Any]]:
    lines = read_lines(config_py)
    in_update = False
    out: List[Dict[str, Any]] = []
    for i, line in enumerate(lines, start=1):
        if "FILE_PATHS.update({" in line:
            in_update = True
            continue
        if in_update and "})" in line:
            in_update = False
            continue
        if not in_update:
            continue
        m = re.search(r"'([^']+)'\s*:\s*(.+?)\s*,?\s*$", line)
        if not m:
            continue
        out.append(
            {
                "key": m.group(1),
                "expr": m.group(2),
                "sources": [repo_source(paths, config_py, i)],
            }
        )
    return out


def cli_group_for(dest: str, flags: Sequence[str], hidden: bool, positional: bool) -> str:
    if positional:
        return "positional"
    if hidden:
        return "advanced_internal"

    if dest in {"ip_addr", "local_addr"}:
        return "connection_network"
    if dest in {"srv_port", "cli_port"}:
        return "pts_ports"
    if dest in {"test_cases", "test_cases_file", "excluded", "test_case_limit", "wid_run"}:
        return "test_selection"
    if dest in {
        "retry",
        "no_retry_on_regression",
        "repeat_until_fail",
        "stress_test",
        "recovery",
        "not_recover",
        "superguard",
        "ykush",
        "active_hub_server",
        "usb_replug_available",
        "ykush_replug_delay",
    }:
        return "retries_recovery"
    if dest in {
        "iut_mode",
        "tty_file",
        "net_tty_file",
        "tty_baudrate",
        "rtscts",
        "bd_addr",
        "btp_tcp_ip",
        "btp_tcp_port",
        "btpclient_path",
    }:
        return "iut_mode_transport"
    if dest in {
        "board_name",
        "debugger_snr",
        "device_core",
        "rtt_log",
        "rtt_log_syncto",
        "btmon",
        "gdb",
        "pylink_reset",
        "tty_alias",
        "hci",
        "hid_vid",
        "hid_pid",
        "hid_serial",
    }:
        return "board_hw_jlink_rtt"
    if dest in {
        "qemu_bin",
        "qemu_options",
        "kernel_cpu",
        "project_path",
        "btproxy_bin",
        "btattach_bin",
        "btattach_at_every_test_case",
        "btmgmt_bin",
        "setcap_cmd",
        "kernel_image",
    }:
        return "qemu_native_btpclient"
    if "log" in dest or dest in {"copy", "store", "database_file", "enable_max_logs"}:
        return "logging_debug"
    return "other"


def parse_cli_arguments(paths: Paths) -> Dict[str, Any]:
    cliparser_py = paths.autopts_repo / "cliparser.py"
    tree = parse_python(cliparser_py)
    rows: List[Dict[str, Any]] = []

    def is_hidden_help(node: ast.AST) -> bool:
        return isinstance(node, ast.Attribute) and dotted_name(node) == "argparse.SUPPRESS"

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"):
            continue
        if not (isinstance(node.func.value, ast.Name) and node.func.value.id == "self"):
            continue

        flags = [str(ast_value(arg)) for arg in node.args if isinstance(ast_value(arg), str)]
        keywords = {kw.arg: kw.value for kw in node.keywords if kw.arg is not None}
        parsed = {k: ast_value(v) for k, v in keywords.items()}
        hidden = False
        if "help" in keywords and is_hidden_help(keywords["help"]):
            hidden = True
            parsed["help"] = None

        positional = bool(flags) and all(not f.startswith("-") for f in flags)
        dest = parsed.get("dest")
        if not isinstance(dest, str):
            if positional and flags:
                dest = flags[0]
            elif flags:
                long_flag = next((f for f in flags if f.startswith("--")), flags[0])
                dest = long_flag.lstrip("-").replace("-", "_")
            else:
                dest = "arg"

        rows.append(
            {
                "name": dest,
                "flags": flags,
                "positional": positional,
                "group": cli_group_for(dest, flags, hidden, positional),
                "default": parsed.get("default"),
                "choices": parsed.get("choices"),
                "nargs": parsed.get("nargs"),
                "action": parsed.get("action"),
                "help": parsed.get("help"),
                "hidden": hidden,
                "sources": [repo_source(paths, cliparser_py, getattr(node, "lineno", None))],
            }
        )

    rows.sort(key=lambda r: (r["group"], r["hidden"], r["name"]))
    return {
        "summary": {
            "total": len(rows),
            "public": sum(1 for r in rows if not r["hidden"]),
            "hidden": sum(1 for r in rows if r["hidden"]),
            "positional": sum(1 for r in rows if r["positional"]),
            "groups": dict(sorted(Counter(r["group"] for r in rows).items())),
        },
        "group_labels": CLI_GROUPS,
        "arguments": rows,
        "sources": [
            repo_source(paths, cliparser_py, find_line_regex(cliparser_py, r"class\s+CliParser")),
            repo_source(paths, cliparser_py, find_line_regex(cliparser_py, r"def\s+add_positional_args")),
        ],
    }


def extract_stack_exported_modules(paths: Paths, stack: str) -> List[str]:
    init_py = paths.ptsprojects / stack / "__init__.py"
    tree = parse_python(init_py)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                value = ast_value(node.value)
                if isinstance(value, list):
                    return [str(v) for v in value if isinstance(v, str)]
    return []


def extract_profile_module_row(paths: Paths, stack: str, module_name: str) -> Dict[str, Any]:
    path = paths.ptsprojects / stack / f"{module_name}.py"
    tree = parse_python(path)
    text = read_text(path)

    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    has_test_cases = "test_cases" in funcs
    has_set_pixits = "set_pixits" in funcs

    get_list_calls: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get_test_case_list":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                get_list_calls.append(node.args[0].value)
            else:
                get_list_calls.append("<dynamic>")

    tcids = sorted(set(TCID_LITERAL_RE.findall(text)))
    lt_helpers = [t for t in tcids if t.endswith("_LT2") or t.endswith("_LT3") or t.endswith("-LT2") or t.endswith("-LT3")]
    explicit_tcids = [t for t in tcids if t not in lt_helpers]

    project_wid_path = paths.ptsprojects / stack / f"{module_name}_wid.py"
    project_wid_dispatcher = False
    project_wid_handlers_count = 0
    if project_wid_path.exists():
        wid_text = read_text(project_wid_path)
        project_wid_dispatcher = bool(re.search(r"def\s+\w+_wid_hdl\s*\(", wid_text))
        project_wid_handlers_count = len(WID_HANDLER_RE.findall(wid_text))

    generic_wid_path = paths.wid_dir / f"{module_name}.py"
    generic_wid_handlers_count = len(WID_HANDLER_RE.findall(read_text(generic_wid_path))) if generic_wid_path.exists() else 0

    if len(explicit_tcids) >= 20:
        classification = "explicit-heavy"
    elif explicit_tcids:
        classification = "workspace-driven + explicit overrides"
    else:
        classification = "workspace-driven"

    profile = get_list_calls[0] if get_list_calls else module_name.upper()
    return {
        "stack": stack,
        "profile": profile,
        "module": module_name,
        "classification": classification,
        "has_test_cases": has_test_cases,
        "has_set_pixits": has_set_pixits,
        "workspace_project_calls": sorted(set(get_list_calls)),
        "explicit_tcid_count": len(explicit_tcids),
        "explicit_lt_helper_count": len(lt_helpers),
        "project_wid_dispatcher": project_wid_dispatcher,
        "project_wid_handlers_count": project_wid_handlers_count,
        "generic_wid_handlers_count": generic_wid_handlers_count,
        "module_file": str(path.relative_to(paths.repo)).replace("\\", "/"),
        "sources": [
            repo_source(paths, path, getattr(funcs.get("test_cases"), "lineno", None)),
            repo_source(paths, path, getattr(funcs.get("set_pixits"), "lineno", None)),
        ],
    }


def extract_stacks_and_profiles(paths: Paths) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    stack_rows: List[Dict[str, Any]] = []
    profile_rows: List[Dict[str, Any]] = []
    for stack in ("zephyr", "mynewt", "bluez"):
        modules = extract_stack_exported_modules(paths, stack)
        init_py = paths.ptsprojects / stack / "__init__.py"
        srow = {
            "stack": stack,
            "profile_count": len(modules),
            "profiles": [m.upper() for m in modules],
            "sources": [repo_source(paths, init_py, find_line_contains(init_py, "__all__"))],
        }
        stack_rows.append(srow)
        for module_name in modules:
            profile_rows.append(extract_profile_module_row(paths, stack, module_name))

    profile_rows.sort(key=lambda r: (r["stack"], r["profile"]))
    stacks_section = {
        "summary": "Stacks and exported profile modules are derived from autopts/ptsprojects/*/__init__.py __all__ lists.",
        "rows": stack_rows,
        "sources": [src for row in stack_rows for src in row.get("sources", [])],
    }
    profiles_section = {
        "summary": "Code support inventory per stack/profile, including workspace-driven vs explicit override indicators.",
        "rows": profile_rows,
        "sources": [repo_source(paths, paths.ptsprojects / "zephyr" / "__init__.py", find_line_contains(paths.ptsprojects / "zephyr" / "__init__.py", "__all__"))],
    }
    return stacks_section, profiles_section, stack_rows


def extract_workspaces_inventory(paths: Paths) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(paths.autopts_workspaces_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".pqw6", ".pts", ".bqw"}:
            continue
        row: Dict[str, Any] = {
            "path": str(path.relative_to(paths.repo)).replace("\\", "/"),
            "format": path.suffix.lower().lstrip("."),
            "project_count": 0,
            "projects": [],
            "pics_rows": 0,
            "pixit_rows": 0,
            "all_rows": 0,
            "sources": [repo_source(paths, path, 1)],
        }
        try:
            root = ET.fromstring(path.read_bytes())
            projects = []
            for pe in root.findall(".//PROJECT_INFORMATION"):
                name = (pe.attrib.get("NAME") or "").strip()
                pics_rows = len(pe.findall("./PICS/Rows/Row"))
                pixit_rows = len(pe.findall("./PIXIT/Rows/Row"))
                all_rows = len(pe.findall(".//Row"))
                projects.append(
                    {
                        "name": name,
                        "tc_log": pe.attrib.get("TC_LOG"),
                        "tc_script": pe.attrib.get("TC_SCRIPT"),
                        "pics_rows": pics_rows,
                        "pixit_rows": pixit_rows,
                        "rows": all_rows,
                    }
                )
                row["pics_rows"] += pics_rows
                row["pixit_rows"] += pixit_rows
                row["all_rows"] += all_rows
            row["projects"] = projects
            row["project_count"] = len(projects)
        except Exception:
            names = sorted(set(XML_PROJECT_RE.findall(read_text(path))))
            row["projects"] = [{"name": n} for n in names]
            row["project_count"] = len(names)
        project_names = {str(p.get("name", "")).upper() for p in row["projects"]}
        row["contains_profiles"] = {name: (name in project_names) for name in ("BAS", "DIS", "HRS", "HID", "HOGP")}
        rows.append(row)

    return {
        "summary": {
            "workspace_files": len(rows),
            "formats": dict(sorted(Counter(r["format"] for r in rows).items())),
            "total_projects": sum(int(r.get("project_count") or 0) for r in rows),
        },
        "note": "Bundled workspace scan is metadata-level; exact active testcase lists require PTS runtime API.",
        "rows": rows,
        "sources": [repo_source(paths, paths.autopts_workspaces_dir, None, "Bundled workspace directory")],
    }


def extract_generic_wid_inventory(paths: Paths) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(paths.wid_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        text = read_text(path)
        count = len(WID_HANDLER_RE.findall(text))
        if count == 0 and path.name != "wid.py":
            continue
        rows.append(
            {
                "service": path.stem.upper(),
                "module": path.stem,
                "wid_handler_count": count,
                "sources": [repo_source(paths, path, find_line_regex(path, r"def\s+hdl_wid_") or 1)],
            }
        )
    rows.sort(key=lambda r: (-r["wid_handler_count"], r["service"]))
    return {
        "summary": {
            "services": len(rows),
            "total_wid_handlers": sum(r["wid_handler_count"] for r in rows),
        },
        "rows": rows,
        "sources": [repo_source(paths, paths.wid_dir / "wid.py", find_line_regex(paths.wid_dir / "wid.py", r"def\s+generic_wid_hdl"))],
    }


def extract_btp_inventory(paths: Paths) -> Dict[str, Any]:
    code_modules = []
    for path in sorted(paths.pybtp_btp_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            tree = parse_python(path)
            func_count = sum(1 for n in tree.body if isinstance(n, ast.FunctionDef))
        except Exception:
            func_count = 0
        code_modules.append({"module": path.stem, "function_count": func_count, "sources": [repo_source(paths, path, 1)]})

    docs = [{"doc": p.name, "sources": [repo_source(paths, p, 1)]} for p in sorted(paths.autopts_docs_dir.glob("btp_*.txt"))]
    return {
        "summary": {
            "code_modules": len(code_modules),
            "doc_specs": len(docs),
            "total_code_functions": sum(x["function_count"] for x in code_modules),
        },
        "code_modules": code_modules,
        "doc_specs": docs,
        "sources": [repo_source(paths, paths.autopts_docs_dir / "overview.txt", 1)],
    }


def extract_tools_inventory(paths: Paths) -> Dict[str, Any]:
    def category(path: Path) -> str:
        rel = path.relative_to(paths.autopts_repo).as_posix()
        if rel.startswith("tools/cron/"):
            return "cron"
        if path.name in {"list_testcases.py", "testplan_vs_workspace.py", "wid_usage.py", "create-workspace.py"}:
            return "workspace_testcase_ops"
        if path.name in {"generate_profile.py", "merge_db.py", "ics_rst_from_html.py"}:
            return "developer_support"
        return "other"

    rows = []
    for path in sorted(paths.autopts_tools_dir.rglob("*.py")):
        rows.append(
            {
                "path": str(path.relative_to(paths.repo)).replace("\\", "/"),
                "category": category(path),
                "sources": [repo_source(paths, path, 1)],
            }
        )
    return {
        "summary": {"scripts": len(rows), "categories": dict(sorted(Counter(r["category"] for r in rows).items()))},
        "rows": rows,
        "sources": [repo_source(paths, paths.autopts_tools_dir / "list_testcases.py", 1)],
    }


def extract_logs_and_outputs(paths: Paths) -> Dict[str, Any]:
    config_py = paths.autopts_pkg / "config.py"
    key_rows = extract_file_paths_keys(paths, config_py)
    key_map = {r["key"]: r for r in key_rows}
    ordered = [
        "IUT_LOGS_DIR",
        "TMP_DIR",
        "TC_STATS_RESULTS_XML_FILE",
        "ALL_STATS_RESULTS_XML_FILE",
        "TC_STATS_JSON_FILE",
        "ALL_STATS_JSON_FILE",
        "TEST_CASE_DB_FILE",
        "WID_USE_CSV_FILE",
        "REPORT_XLSX_FILE",
        "REPORT_TXT_FILE",
        "ERROR_TXT_FILE",
    ]
    desc = {
        "IUT_LOGS_DIR": "Main logs directory for run artifacts (session + per-test logs).",
        "TMP_DIR": "Temporary workspace for generated XML/JSON/DB/report temp files.",
        "TC_STATS_RESULTS_XML_FILE": "Per-testcase XML results file used by runtime reporting.",
        "ALL_STATS_RESULTS_XML_FILE": "Aggregated XML results file.",
        "TC_STATS_JSON_FILE": "Per-testcase JSON stats output.",
        "ALL_STATS_JSON_FILE": "Aggregated JSON stats output.",
        "TEST_CASE_DB_FILE": "SQLite DB for testcase timing/history estimation.",
        "WID_USE_CSV_FILE": "CSV mapping WID -> testcases derived from logs.",
        "REPORT_XLSX_FILE": "Excel report output path used by report/bot flows.",
        "REPORT_TXT_FILE": "Text report output path.",
        "ERROR_TXT_FILE": "Temporary error summary file.",
    }
    rows = []
    for key in ordered:
        item = key_map.get(key)
        if not item:
            continue
        rows.append({"key": key, "expr": item["expr"], "description": desc.get(key, ""), "sources": item["sources"]})
    return {"rows": rows, "sources": [repo_source(paths, config_py, find_line_contains(config_py, "FILE_PATHS.update"))]}


def load_official_sources(paths: Paths) -> Dict[str, Any]:
    if not paths.official_sources_json.exists():
        return {
            "whitelist_domains": ["docs.zephyrproject.org", "bluetooth.com", "qualification.bluetooth.com", "support.bluetooth.com", "pts.bluetooth.com"],
            "entries": [],
            "sources": [],
        }
    raw = json.loads(read_text(paths.official_sources_json))
    whitelist = raw.get("whitelist_domains", []) if isinstance(raw, dict) else []
    entries_raw = raw.get("entries", []) if isinstance(raw, dict) else []
    entries = []
    for item in entries_raw:
        if not isinstance(item, dict):
            continue
        eid = str(item.get("id") or "")
        line = find_line_contains(paths.official_sources_json, f'"id": "{eid}"') if eid else 1
        entries.append(
            {
                "id": eid,
                "title": str(item.get("title") or ""),
                "url": str(item.get("url") or ""),
                "domain": str(item.get("domain") or ""),
                "retrieved_at": str(item.get("retrieved_at") or ""),
                "used_for_sections": list(item.get("used_for_sections") or []),
                "notes": str(item.get("notes") or ""),
                "sources": [repo_source(paths, paths.official_sources_json, line)],
                "web_source": web_source(str(item.get("url") or ""), str(item.get("title") or ""), str(item.get("retrieved_at") or "")),
            }
        )
    return {"whitelist_domains": [str(x) for x in whitelist], "entries": entries, "sources": [repo_source(paths, paths.official_sources_json, 1)]}


def official_sources_by_id(official: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(item.get("id")): item for item in official.get("entries", []) if isinstance(item, dict)}


def extract_launchers(paths: Paths) -> List[Dict[str, Any]]:
    entries = []
    for fname in ["autoptsclient-zephyr.py", "autoptsclient-bluez.py", "autoptsclient-mynewt.py", "autoptsclient_bot.py", "autoptsserver.py"]:
        path = paths.autopts_repo / fname
        if not path.exists():
            continue
        text = read_text(path)
        m = re.search(r"super\(\).__init__\([^\n]*'([a-z0-9_]+)'\)", text)
        stack = m.group(1) if m else None
        if fname == "autoptsserver.py":
            kind = "server"
        elif "bot" in fname:
            kind = "bot"
        else:
            kind = "client"
        entries.append(
            {
                "script": fname,
                "kind": kind,
                "stack": stack,
                "summary": ("Windows-side XML-RPC server for PTS COM" if kind == "server" else ("Automation bot entrypoint" if kind == "bot" else f"Client launcher for {stack or 'stack'}")),
                "sources": [repo_source(paths, path, find_line_regex(path, r"def\s+main\(") or 1)],
            }
        )
    return entries


def extract_overview(paths: Paths, official: Dict[str, Any], stack_rows: List[Dict[str, Any]], launchers: List[Dict[str, Any]]) -> Dict[str, Any]:
    auto_readme = paths.autopts_repo / "README.md"
    config_py = paths.autopts_pkg / "config.py"
    consts = extract_top_constants(config_py, ["SERVER_PORT", "CLIENT_PORT", "BTMON_PORT", "MAX_SERVER_RESTART_TIME"])
    pyproject = parse_pyproject(paths)
    src_map = official_sources_by_id(official)
    return {
        "summary": "auto-pts is a Bluetooth PTS automation framework using a Windows PTSControl COM side (server) and a Python client side that orchestrates BTP and IUT behavior.",
        "key_points": [
            "Client/server architecture with XML-RPC and PTSControl COM.",
            "Runtime testcase lists come from PTS API (workspace + PTS), not only static pqw6 parsing.",
            "Multi-stack support (Zephyr / BlueZ / Mynewt) plus Bot orchestration.",
            "Selection and execution are controlled by workspace, filters, blacklist, retries, and recovery policies.",
        ],
        "project_meta": pyproject,
        "launchers": launchers,
        "defaults": {
            "server_port": consts.get("SERVER_PORT", {}).get("value"),
            "client_port": consts.get("CLIENT_PORT", {}).get("value"),
            "btmon_port": consts.get("BTMON_PORT", {}).get("value"),
            "max_server_restart_time": consts.get("MAX_SERVER_RESTART_TIME", {}).get("value"),
        },
        "stack_summary": {row["stack"]: {"profile_count": row["profile_count"], "profiles": row["profiles"]} for row in stack_rows},
        "sources": [
            repo_source(paths, auto_readme, find_line_contains(auto_readme, "auto-pts is the Bluetooth PTS automation framework")),
            repo_source(paths, config_py, find_line_contains(config_py, "SERVER_PORT")),
            src_map.get("bluetooth_pts_download", {}).get("web_source"),
        ],
    }


def extract_architecture(paths: Paths, official: Dict[str, Any]) -> Dict[str, Any]:
    auto_readme = paths.autopts_repo / "README.md"
    client_py = paths.autopts_pkg / "client.py"
    ptscontrol_py = paths.autopts_pkg / "ptscontrol.py"
    src_map = official_sources_by_id(official)
    components = [
        {
            "id": "server",
            "name": "auto-pts server",
            "platform": "Windows",
            "role": "Bridges PTSControl COM and exposes XML-RPC methods to the client.",
            "sources": [repo_source(paths, auto_readme, find_line_contains(auto_readme, "auto-pts server")), repo_source(paths, ptscontrol_py, find_line_contains(ptscontrol_py, "Python bindings for PTSControl"))],
        },
        {
            "id": "client",
            "name": "auto-pts client",
            "platform": "Linux / Windows",
            "role": "Orchestrates testcase execution, WID/MMI responses, BTP actions, retries, recovery, and logging.",
            "sources": [repo_source(paths, auto_readme, find_line_contains(auto_readme, "auto-pts client")), repo_source(paths, client_py, find_line_regex(client_py, r"class\s+Client"))],
        },
        {
            "id": "iut",
            "name": "IUT (Implementation Under Test)",
            "platform": "Depends on mode",
            "role": "Bluetooth stack under test (board, qemu, native, btpclient-connected implementation).",
            "sources": [repo_source(paths, auto_readme, find_line_contains(auto_readme, "Implementation Under Test"))],
        },
        {
            "id": "btp",
            "name": "BTP",
            "platform": "Client <-> IUT",
            "role": "Bluetooth Test Protocol used by auto-pts to control the IUT side behavior.",
            "sources": [repo_source(paths, auto_readme, find_line_contains(auto_readme, "Bluetooth Test Protocol")), repo_source(paths, paths.autopts_docs_dir / "overview.txt", 1)],
        },
    ]
    return {
        "components": components,
        "flows": [
            "PTS runtime (Windows) -> autoptsserver -> XML-RPC -> autoptsclient",
            "autoptsclient -> BTP -> IUT (board/qemu/native/btpclient)",
            "PTS MMIs/WIDs -> callback -> generic/project WID handlers -> BTP response/action",
        ],
        "sources": [repo_source(paths, auto_readme, find_line_contains(auto_readme, "# Architecture")), src_map.get("zephyr_autopts_linux", {}).get("web_source")],
    }


def extract_quickstart(paths: Paths, official: Dict[str, Any]) -> Dict[str, Any]:
    auto_readme = paths.autopts_repo / "README.md"
    bluez_readme = paths.ptsprojects / "bluez" / "README.md"
    bot_readme = paths.autopts_pkg / "bot" / "README.md"
    src_map = official_sources_by_id(official)
    scenarios = [
        {
            "id": "zephyr_linux_windows",
            "title": "Zephyr (Linux + Windows)",
            "summary": "Typical split setup: autoptsserver + PTS on Windows, autoptsclient-zephyr on Linux/host side.",
            "commands": [
                {"command": "python.exe autoptsserver.py", "when": "Windows server side"},
                {"command": "./autoptsclient-zephyr.py zephyr-master -i SERVER_IP -l LOCAL_IP -t /dev/ttyACM0 -b nrf52", "when": "Linux client side (example)"},
            ],
            "notes": ["Close PTS GUI before automation.", "Workspace .pqw6 must be accessible on the machine running PTS/autoptsserver."],
            "sources": [repo_source(paths, auto_readme, find_line_contains(auto_readme, "Running in Client/Server Mode")), repo_source(paths, auto_readme, find_line_contains(auto_readme, "Testing Zephyr combined (controller + host) build on nRF52")), src_map.get("zephyr_autopts_linux", {}).get("web_source")],
        },
        {
            "id": "zephyr_windows",
            "title": "Zephyr (Windows)",
            "summary": "Use the official Zephyr AutoPTS Win10 guide for OS-specific setup details.",
            "commands": [{"command": "python.exe autoptsserver.py", "when": "Windows server side"}],
            "notes": ["OS-specific setup steps are maintained in Zephyr official docs."],
            "sources": [repo_source(paths, auto_readme, find_line_contains(auto_readme, "autopts-win10.html")), src_map.get("zephyr_autopts_win10", {}).get("web_source")],
        },
        {
            "id": "bluez",
            "title": "BlueZ",
            "summary": "Requires BlueZ btpclient and BlueZ daemon setup in addition to autopts client/server.",
            "commands": [
                {"command": "python autoptsserver.py", "when": "Windows server side"},
                {"command": './autoptsclient-bluez.py "C:\\\\...\\\\bluez.pqw6" --btpclient_path=/path/to/bluez/tools/btpclient -i SERVER_IP -l LOCAL_IP -c GAP', "when": "Linux client side (example)"},
            ],
            "notes": ["BlueZ README in auto-pts includes build + bluetoothd run steps and a working example."],
            "sources": [repo_source(paths, bluez_readme, find_line_contains(bluez_readme, "Running AutoPTS Client for BlueZ"))],
        },
        {
            "id": "mynewt",
            "title": "Mynewt NimBLE",
            "summary": "Use autoptsclient-mynewt launcher; prerequisites and examples are documented in auto-pts README.",
            "commands": [{"command": "./autoptsclient-mynewt.py nimble-master -i SERVER_IP -l LOCAL_IP -t /dev/ttyACM0 -b nordic_pca10056", "when": "Linux client side (example)"}],
            "notes": ["AutoPTS README links to Mynewt setup docs and includes example command lines."],
            "sources": [repo_source(paths, auto_readme, find_line_contains(auto_readme, "Testing Mynewt build on nRF52"))],
        },
        {
            "id": "bot",
            "title": "AutoPTSClientBot",
            "summary": "Bot adds build/flash/run/report orchestration across configurations, retries, and reporting backends.",
            "commands": [{"command": "./autoptsclient_bot.py", "when": "Start the bot client"}],
            "notes": ["Bot config sample files exist under autopts/bot/."],
            "sources": [repo_source(paths, bot_readme, find_line_contains(bot_readme, "Usage"))],
        },
    ]
    return {"scenarios": scenarios, "sources": [repo_source(paths, auto_readme, find_line_contains(auto_readme, "Running in Client/Server Mode"))]}


def extract_runtime_flow(paths: Paths) -> Dict[str, Any]:
    client_py = paths.autopts_pkg / "client.py"
    cliparser_py = paths.autopts_repo / "cliparser.py"
    steps = [
        {
            "id": "parse_args",
            "title": "Parse args / config",
            "summary": "CliParser parses and validates arguments, infers iut_mode, and prepares filters.",
            "functions": ["Client.parse_config_and_args", "CliParser.parse"],
            "preconditions": ["Launcher script invoked with workspace and connection params"],
            "outputs": ["args namespace", "IUT mode", "selection filters"],
            "failure_points": ["invalid tty/path", "bad ports", "unsupported mode on platform"],
            "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+parse_config_and_args")), repo_source(paths, cliparser_py, find_line_regex(cliparser_py, r"def\s+parse\("))],
        },
        {
            "id": "init_runtime",
            "title": "Init runtime / temp / optional DB",
            "summary": "Client.main initializes tmp paths, logging, and optional TestCase DB.",
            "functions": ["Client.main", "Client.load_test_case_database"],
            "preconditions": ["args parsed"],
            "outputs": ["tmp dir", "optional sqlite DB"],
            "failure_points": ["permissions", "bad DB path"],
            "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+main\(")), repo_source(paths, client_py, find_line_regex(client_py, r"def\s+load_test_case_database"))],
        },
        {
            "id": "init_pts_btp_iut",
            "title": "Init PTS / BTP / IUT",
            "summary": "Initializes PTS instances, BTP transport, IUT control layer, and stack state.",
            "functions": ["init_pts", "btp.init", "Client.init_iutctl", "stack.init_stack"],
            "preconditions": ["autoptsserver reachable or local mode", "IUT prerequisites satisfied"],
            "outputs": ["ptses", "BTP ready", "stack initialized"],
            "failure_points": ["XML-RPC issues", "BTP init errors", "IUT startup failures"],
            "sources": [repo_source(paths, client_py, find_line_contains(client_py, "btp.init")), repo_source(paths, client_py, find_line_contains(client_py, "stack.init_stack"))],
        },
        {
            "id": "setup_pixits_and_cases",
            "title": "Setup PIXITs + testcase objects",
            "summary": "Loads profile modules for workspace projects, updates PIXITs, and constructs testcase objects.",
            "functions": ["setup_project_pixits", "setup_test_cases", "mod.set_pixits", "mod.test_cases"],
            "preconditions": ["workspace open in PTS"],
            "outputs": ["PIXIT updates", "test_case_instances"],
            "failure_points": ["unsupported profile module", "missing handlers"],
            "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+setup_project_pixits")), repo_source(paths, client_py, find_line_regex(client_py, r"def\s+setup_test_cases"))],
        },
        {
            "id": "resolve_names",
            "title": "Resolve runnable testcase names",
            "summary": "Fetches testcase names from PTS workspace and applies blacklist + CLI filters (+ WID-derived selection).",
            "functions": ["get_test_cases", "run_or_not", "CliParser.wid_run_tcs"],
            "preconditions": ["workspace projects loaded", "optional wid_usage_report.csv if --wid_run used"],
            "outputs": ["final args.test_cases list"],
            "failure_points": ["missing WID report for --wid_run", "filters excluding too much"],
            "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+get_test_cases")), repo_source(paths, client_py, find_line_regex(client_py, r"def\s+run_or_not")), repo_source(paths, cliparser_py, find_line_regex(cliparser_py, r"def\s+wid_run_tcs"))],
        },
        {
            "id": "run_loop",
            "title": "Run loop / retry / recovery",
            "summary": "Executes testcases, collects verdicts, applies retry and recovery policies, and writes runtime stats/logs.",
            "functions": ["run_test_cases", "run_test_case", "LTThread", "run_recovery"],
            "preconditions": ["ptses", "test_case_instances", "filtered testcase names"],
            "outputs": ["session logs", "summary", "XML/JSON stats"],
            "failure_points": ["MISSING WID", "BTP TIMEOUT", "XML-RPC faults", "SUPERGUARD TIMEOUT"],
            "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+run_test_case\(")), repo_source(paths, client_py, find_line_regex(client_py, r"def\s+run_test_cases\(")), repo_source(paths, client_py, find_line_regex(client_py, r"def\s+run_recovery\("))],
        },
        {
            "id": "cleanup",
            "title": "Cleanup / shutdown",
            "summary": "Cleans callbacks, stops PTS instances, and releases IUT resources.",
            "functions": ["Client.cleanup", "Client.shutdown_pts"],
            "preconditions": ["run finished or interrupted"],
            "outputs": ["resources released"],
            "failure_points": ["stuck PTS instance/callback thread"],
            "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+cleanup\(")), repo_source(paths, client_py, find_line_regex(client_py, r"def\s+shutdown_pts\("))],
        },
    ]
    return {"steps": steps, "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"class\s+Client"))]}


def extract_selection_notes(paths: Paths) -> Dict[str, Any]:
    client_py = paths.autopts_pkg / "client.py"
    cliparser_py = paths.autopts_repo / "cliparser.py"
    return {
        "pipeline": [
            "Workspace projects are discovered from PTS (pts.get_project_list()).",
            "Profile modules create code-backed testcase instances via setup_test_cases().",
            "get_test_cases() fetches workspace testcase names and filters them via run_or_not().",
            "run_test_cases() executes filtered names against available testcase instances.",
        ],
        "sources": [
            repo_source(paths, client_py, find_line_regex(client_py, r"def\s+setup_test_cases")),
            repo_source(paths, client_py, find_line_regex(client_py, r"def\s+get_test_cases")),
            repo_source(paths, client_py, find_line_regex(client_py, r"def\s+run_test_cases\(")),
            repo_source(paths, cliparser_py, find_line_regex(cliparser_py, r"def\s+parse\(")),
        ],
    }


def extract_test_support_three_layers(paths: Paths, profiles_inventory: Dict[str, Any], workspaces_inventory: Dict[str, Any]) -> Dict[str, Any]:
    profile_rows = list(profiles_inventory.get("rows", []))
    list_tool = paths.autopts_tools_dir / "list_testcases.py"
    diff_tool = paths.autopts_tools_dir / "testplan_vs_workspace.py"
    wid_tool = paths.autopts_tools_dir / "wid_usage.py"
    client_py = paths.autopts_pkg / "client.py"
    cliparser_py = paths.autopts_repo / "cliparser.py"
    utils_py = paths.autopts_pkg / "utils.py"

    top_explicit = sorted(profile_rows, key=lambda r: (-int(r.get("explicit_tcid_count") or 0), r["stack"], r["profile"]))[:12]
    code_summary = {
        "rows": len(profile_rows),
        "by_stack": dict(sorted(Counter(r["stack"] for r in profile_rows).items())),
        "by_classification": dict(sorted(Counter(r["classification"] for r in profile_rows).items())),
    }

    return {
        "layers": {
            "code_support": {
                "label": "Code-derived",
                "summary": code_summary,
                "top_explicit_profiles": top_explicit,
                "sources": profiles_inventory.get("sources", []),
            },
            "bundled_workspaces": {
                "label": "Workspace-derived",
                "summary": workspaces_inventory.get("summary", {}),
                "rows": workspaces_inventory.get("rows", []),
                "limitations": [
                    "Bundled workspace XML parsing is metadata-level and may not expose the exact active testcase set as plain text.",
                    "Exact active testcase lists depend on PTS runtime API state and workspace interpretation.",
                ],
                "sources": workspaces_inventory.get("sources", []),
            },
            "exact_runtime": {
                "label": "PTS runtime required",
                "platform_requirements": ["Windows", "Installed PTS", "COM access", "Workspace .pqw6"],
                "commands": [
                    {
                        "title": "List active testcases from a PTS workspace (exact runtime list)",
                        "command": "python3 auto-pts/tools/list_testcases.py path/to/workspace.pqw6",
                        "platform": "Windows + PTS COM runtime",
                        "sources": [repo_source(paths, list_tool, 1)],
                    },
                    {
                        "title": "Diff test plan vs workspace",
                        "command": "python3 auto-pts/tools/testplan_vs_workspace.py path/to/workspace.pqw6 path/to/test_plan.xlsx",
                        "platform": "Windows + PTS COM runtime + pandas/win32com",
                        "sources": [repo_source(paths, diff_tool, 1)],
                    },
                    {
                        "title": "Derive WID -> testcases from logs and use --wid_run",
                        "command": "python3 -m tools.wid_usage  # then autoptsclient ... --wid_run SERVICE WID",
                        "platform": "Any (log parsing); --wid_run used at launch time",
                        "sources": [repo_source(paths, wid_tool, 1), repo_source(paths, cliparser_py, find_line_contains(cliparser_py, "--wid_run")), repo_source(paths, utils_py, find_line_regex(utils_py, r"def\s+extract_wid_testcases_to_csv"))],
                    },
                ],
                "filtering_rules": [
                    {
                        "rule": "Workspace testcase names are fetched via PTS API",
                        "detail": "get_test_cases() loops over pts.get_project_list() and pts.get_test_case_list(project).",
                        "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+get_test_cases"))],
                    },
                    {
                        "rule": "Blacklist removes helper/LT internals by default",
                        "detail": "run_or_not() excludes names containing _HELPER, LT2, LT3, TWO_NODES_PROVISIONER.",
                        "sources": [repo_source(paths, client_py, find_line_contains(client_py, "test_case_blacklist"))],
                    },
                    {
                        "rule": "CLI filters merge into final args.test_cases",
                        "detail": "-c/-e/--test-cases-file/--wid_run contribute to the final selection before the run loop.",
                        "sources": [repo_source(paths, cliparser_py, find_line_regex(cliparser_py, r"def\s+wid_run_tcs")), repo_source(paths, client_py, find_line_contains(client_py, "test_cases_file"))],
                    },
                ],
                "sources": [repo_source(paths, list_tool, 1), repo_source(paths, client_py, find_line_regex(client_py, r"def\s+run_or_not"))],
            },
        },
        "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+get_test_cases"))],
    }


def extract_wid_inventory(paths: Paths, generic_wid: Dict[str, Any]) -> Dict[str, Any]:
    cliparser_py = paths.autopts_repo / "cliparser.py"
    utils_py = paths.autopts_pkg / "utils.py"
    wid_py = paths.wid_dir / "wid.py"
    return {
        "generic": generic_wid,
        "wid_run": {
            "flag": "--wid_run SERVICE WID",
            "behavior": "Loads wid_usage_report.csv and appends matching testcases to args.test_cases.",
            "sources": [repo_source(paths, cliparser_py, find_line_contains(cliparser_py, "--wid_run")), repo_source(paths, cliparser_py, find_line_regex(cliparser_py, r"def\s+wid_run_tcs"))],
        },
        "wid_usage_tool": {
            "command": "python3 -m tools.wid_usage [--log-dir /path/to/logs]",
            "output": "wid_usage_report.csv",
            "sources": [repo_source(paths, paths.autopts_tools_dir / "wid_usage.py", 1), repo_source(paths, utils_py, find_line_regex(utils_py, r"def\s+extract_wid_testcases_to_csv")), repo_source(paths, utils_py, find_line_regex(utils_py, r"def\s+load_wid_report"))],
        },
        "sources": [repo_source(paths, wid_py, find_line_regex(wid_py, r"def\s+generic_wid_hdl"))],
    }


def extract_troubleshooting(paths: Paths, official: Dict[str, Any]) -> Dict[str, Any]:
    auto_readme = paths.autopts_repo / "README.md"
    client_py = paths.autopts_pkg / "client.py"
    cliparser_py = paths.autopts_repo / "cliparser.py"
    src_map = official_sources_by_id(official)
    items = [
        {
            "title": "PTS GUI still open while using automation",
            "symptom": "autoptsserver startup/control issues or unstable PTS automation behavior.",
            "why": "auto-pts README explicitly says no PTS GUI instances should be running in GUI mode.",
            "fix": ["Close all PTS GUI instances", "Restart autoptsserver.py"],
            "tags": ["Windows", "PTS runtime required"],
            "sources": [repo_source(paths, auto_readme, find_line_contains(auto_readme, "there should be no PTS instances running in the GUI mode"))],
        },
        {
            "title": "No exact active testcase list from pqw6 parsing only",
            "symptom": "Static workspace parsing does not reveal the exact active testcase set.",
            "why": "auto-pts runtime list is obtained through PTS API (get_test_case_list) when PTS is running.",
            "fix": ["Use auto-pts/tools/list_testcases.py on Windows with PTS runtime", "Treat bundled workspace parsing as metadata only"],
            "tags": ["Windows-only", "PTS runtime required"],
            "sources": [repo_source(paths, paths.autopts_tools_dir / "list_testcases.py", 1), repo_source(paths, client_py, find_line_regex(client_py, r"def\s+get_test_cases"))],
        },
        {
            "title": "CLI sanity-check failures for tty/qemu/native modes",
            "symptom": "Launcher exits before run start with a validation errmsg.",
            "why": "CliParser.parse() validates the inferred or explicit iut_mode and required parameters.",
            "fix": ["Confirm iut_mode", "Check tty/qemu/btpclient paths", "Provide board/qemu/bin args required for the chosen mode"],
            "tags": ["CLI", "IUT mode"],
            "sources": [repo_source(paths, cliparser_py, find_line_regex(cliparser_py, r"def\s+check_args_tty")), repo_source(paths, cliparser_py, find_line_regex(cliparser_py, r"def\s+parse\("))],
        },
        {
            "title": "MISSING WID ERROR / MissingWIDError",
            "symptom": "Testcase ends with missing WID-related errors.",
            "why": "generic/project WID handler chain does not implement hdl_wid_<N> for a requested WID.",
            "fix": ["Inspect logs for WID number", "Add handler in autopts/wid or project-specific *_wid.py", "Use tools/wid_usage.py to map WIDs to testcases from logs"],
            "tags": ["WID/MMI", "Code support"],
            "sources": [repo_source(paths, paths.wid_dir / "wid.py", find_line_contains(paths.wid_dir / "wid.py", "No {wid_str} found")), repo_source(paths, paths.autopts_tools_dir / "wid_usage.py", 1)],
        },
        {
            "title": "BTP timeout / recovery loops",
            "symptom": "BTP TIMEOUT / superguard timeout / repeated recovery attempts.",
            "why": "IUT, transport, or PTS runtime got stuck; recovery logic is triggered by policy.",
            "fix": ["Enable/configure --recovery", "Tune retry/superguard", "Inspect btproxy/btattach/reset tooling and board connectivity"],
            "tags": ["Runtime", "Recovery"],
            "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+run_recovery\(")), repo_source(paths, client_py, find_line_contains(client_py, "SUPERGUARD TIMEOUT"))],
        },
        {
            "title": "OS-specific Zephyr AutoPTS setup problems",
            "symptom": "Toolchain/driver/VM/setup issues outside pure auto-pts code paths.",
            "why": "The authoritative setup steps are maintained in Zephyr official docs.",
            "fix": ["Follow the official Zephyr Linux/Win10 AutoPTS guides for your environment"],
            "tags": ["Official docs", "Zephyr"],
            "sources": [src_map.get("zephyr_autopts_linux", {}).get("web_source"), src_map.get("zephyr_autopts_win10", {}).get("web_source")],
        },
    ]
    return {"items": items, "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+run_test_cases\("))]}


def extract_extending_autopts(paths: Paths) -> Dict[str, Any]:
    tutorial = paths.autopts_docs_dir / "tutorials" / "add_test_case.md"
    steps = [
        {
            "id": "plan_btp",
            "title": "Plan the BTP interface",
            "summary": "Start from ATS/MMI analysis and design BTP operations before implementing handlers.",
            "key_files": ["auto-pts/doc/btp_*.txt", "auto-pts/autopts/pybtp/btp/*.py"],
            "sources": [repo_source(paths, tutorial, find_line_contains(tutorial, "Plan the BTP interface"))],
        },
        {
            "id": "generate_profile",
            "title": "Generate profile boilerplate",
            "summary": "Use tools/generate_profile.py to create profile skeleton and initial wiring.",
            "key_files": ["auto-pts/tools/generate_profile.py", "autopts/pybtp/defs.py", "autopts/wid/<profile>.py"],
            "sources": [repo_source(paths, tutorial, find_line_contains(tutorial, "./tools/generate_profile.py")), repo_source(paths, paths.autopts_tools_dir / "generate_profile.py", 1)],
        },
        {
            "id": "stack_profile_module",
            "title": "Implement <stack>/<profile>.py",
            "summary": "Provide set_pixits(ptses) and test_cases(ptses) to configure PIXITs and testcase objects.",
            "key_files": ["autopts/ptsprojects/<stack>/<profile>.py"],
            "sources": [repo_source(paths, tutorial, find_line_contains(tutorial, "def set_pixits(ptses)"))],
        },
        {
            "id": "wid_handlers",
            "title": "Add WID/MMI handlers",
            "summary": "Implement generic and/or project-specific WID handlers and route via generic_wid_hdl.",
            "key_files": ["autopts/wid/<profile>.py", "autopts/ptsprojects/<stack>/<profile>_wid.py"],
            "sources": [repo_source(paths, tutorial, find_line_contains(tutorial, "profile_wid.py"))],
        },
        {
            "id": "testcase_specific_logic",
            "title": "Customize testcase logic",
            "summary": "Add testcase-specific preconditions, custom flows, and LT synchronization as needed.",
            "key_files": ["autopts/ptsprojects/<stack>/<profile>.py", "autopts/ptsprojects/testcase.py", "autopts/ptsprojects/stack/*"],
            "sources": [repo_source(paths, tutorial, find_line_contains(tutorial, "Add a new test case"))],
        },
    ]
    return {"steps": steps, "sources": [repo_source(paths, tutorial, 1)]}


def extract_official_sources_section(official_raw: Dict[str, Any]) -> Dict[str, Any]:
    entries = []
    for item in official_raw.get("entries", []):
        if not isinstance(item, dict):
            continue
        entries.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "url": item.get("url"),
                "domain": item.get("domain"),
                "retrieved_at": item.get("retrieved_at"),
                "used_for_sections": item.get("used_for_sections", []),
                "notes": item.get("notes", ""),
                "sources": item.get("sources", []),
            }
        )
    return {
        "whitelist_domains": official_raw.get("whitelist_domains", []),
        "entries": entries,
        "sources": official_raw.get("sources", []),
    }


def extract_meta(paths: Paths, stack_rows: List[Dict[str, Any]], official_raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "generated_date": date.today().isoformat(),
        "repo_root": str(paths.repo),
        "autopts_repo": str(paths.autopts_repo.relative_to(paths.repo)).replace("\\", "/"),
        "builder_integration": {
            "builder_script": str(paths.builder_script.relative_to(paths.repo)).replace("\\", "/"),
            "templates_dir": str(paths.templates_dir.relative_to(paths.repo)).replace("\\", "/"),
        },
        "source_policy": {
            "allowed_local_prefixes": ["auto-pts/", "tools/", "dashboards/pts_report_he/"],
            "allowed_official_domains": official_raw.get("whitelist_domains", []),
            "note": "This panel is restricted to auto-pts repo code/docs and whitelisted official external sources.",
        },
        "scan_summary": {
            "stacks_scanned": [row["stack"] for row in stack_rows],
            "official_sources_count": len(official_raw.get("entries", [])),
        },
        "sources": [repo_source(paths, paths.builder_script, 1), repo_source(paths, paths.official_sources_json, 1)],
    }


def extract_known_limits(paths: Paths) -> Dict[str, Any]:
    client_py = paths.autopts_pkg / "client.py"
    return {
        "items": [
            {
                "title": "No live PTS COM extraction in this dashboard build",
                "detail": "Dashboard content is generated from repository code/docs. Exact active testcase lists for a specific workspace require Windows + PTS runtime tools.",
                "tags": ["PTS runtime required", "Windows-only"],
                "sources": [repo_source(paths, paths.autopts_tools_dir / "list_testcases.py", 1)],
            },
            {
                "title": "Bundled workspace parsing is metadata-level",
                "detail": "XML parsing provides projects/PICS/PIXIT metadata but does not guarantee a complete active testcase list.",
                "tags": ["Workspace-derived"],
                "sources": [repo_source(paths, client_py, find_line_regex(client_py, r"def\s+get_test_cases"))],
            },
            {
                "title": "Inventories reflect the checked-out repo snapshot",
                "detail": "If the auto-pts subtree changes, rebuild the dashboard to refresh extracted inventories and support matrices.",
                "tags": ["Snapshot"],
                "sources": [repo_source(paths, paths.builder_script, 1)],
            },
        ],
        "sources": [repo_source(paths, paths.builder_script, 1)],
    }


def extract_sources_index(guide: Dict[str, Any]) -> Dict[str, Any]:
    local_map: Dict[Tuple[str, Optional[int]], Dict[str, Any]] = {}
    web_map: Dict[str, Dict[str, Any]] = {}

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            if isinstance(obj.get("file"), str):
                key = (obj["file"], obj.get("line") if isinstance(obj.get("line"), int) else None)
                entry = local_map.setdefault(key, {"file": key[0], "line": key[1], "count": 0})
                entry["count"] += 1
            if isinstance(obj.get("url"), str):
                key = obj["url"]
                entry = web_map.setdefault(key, {"url": key, "title": obj.get("title"), "retrieved_at": obj.get("retrieved_at"), "count": 0})
                entry["count"] += 1
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(guide)
    local_rows = sorted(local_map.values(), key=lambda r: (r["file"], r["line"] or 0))
    web_rows = sorted(web_map.values(), key=lambda r: r["url"])
    return {
        "summary": {"local_sources": len(local_rows), "web_sources": len(web_rows)},
        "local": local_rows,
        "web": web_rows,
        "sources": [],
    }


def domain_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def domain_allowed(domain: str, whitelist: Iterable[str]) -> bool:
    domain = (domain or "").lower()
    for item in whitelist:
        allowed = str(item).lower().strip()
        if not allowed:
            continue
        if domain == allowed or domain.endswith("." + allowed):
            return True
    return False


def enforce_autopts_guide_source_policy(data: Dict[str, Any]) -> None:
    guide = data.get("auto_pts_guide")
    if not isinstance(guide, dict):
        raise ValueError("Missing data['auto_pts_guide'] or invalid type")

    missing = [k for k in REQUIRED_TOP_LEVEL_KEYS if k not in guide]
    if missing:
        raise ValueError(f"auto_pts_guide missing required top-level keys: {missing}")

    official = guide.get("official_sources", {})
    if not isinstance(official, dict):
        raise ValueError("auto_pts_guide.official_sources must be an object")
    whitelist = official.get("whitelist_domains", [])
    if not whitelist:
        raise ValueError("auto_pts_guide.official_sources.whitelist_domains is empty")

    def walk(obj: Any, path: str = "auto_pts_guide") -> Iterator[Tuple[str, Dict[str, Any]]]:
        if isinstance(obj, dict):
            yield path, obj
            for k, v in obj.items():
                yield from walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                yield from walk(v, f"{path}[{i}]")

    for path, item in walk(guide):
        if "url" in item:
            url = str(item.get("url") or "")
            if not url:
                continue
            if not domain_allowed(domain_of(url), whitelist):
                raise ValueError(f"Disallowed official source domain in {path}: {url}")
            if not item.get("title"):
                raise ValueError(f"Missing title for web source in {path}: {url}")
            if not item.get("retrieved_at"):
                raise ValueError(f"Missing retrieved_at for web source in {path}: {url}")

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key == "sources_index":
            continue
        section = guide.get(key)
        if isinstance(section, dict):
            if key == "official_sources":
                if not section.get("entries"):
                    raise ValueError("auto_pts_guide.official_sources.entries is empty")
                continue
            if not section.get("sources"):
                raise ValueError(f"auto_pts_guide.{key} has no section-level sources")


def build_autopts_guide_data(repo_root: Path | str = ".") -> Dict[str, Any]:
    paths = _paths(repo_root)
    official_raw = load_official_sources(paths)

    stacks_section, profiles_inventory, stack_rows = extract_stacks_and_profiles(paths)
    generic_wid = extract_generic_wid_inventory(paths)
    workspaces_inventory = extract_workspaces_inventory(paths)
    btp_inventory = extract_btp_inventory(paths)
    tools_inventory = extract_tools_inventory(paths)
    logs_outputs = extract_logs_and_outputs(paths)
    cli_section = parse_cli_arguments(paths)
    runtime_flow = extract_runtime_flow(paths)
    quickstart = extract_quickstart(paths, official_raw)
    overview = extract_overview(paths, official_raw, stack_rows, extract_launchers(paths))
    architecture = extract_architecture(paths, official_raw)
    selection_notes = extract_selection_notes(paths)
    test_support_3_layers = extract_test_support_three_layers(paths, profiles_inventory, workspaces_inventory)
    wid_inventory = extract_wid_inventory(paths, generic_wid)
    troubleshooting = extract_troubleshooting(paths, official_raw)
    extending_autopts = extract_extending_autopts(paths)
    official_sources = extract_official_sources_section(official_raw)
    known_limits = extract_known_limits(paths)

    guide: Dict[str, Any] = {
        "meta": extract_meta(paths, stack_rows, official_raw),
        "overview": overview,
        "architecture": architecture,
        "quickstart": quickstart,
        "cli": cli_section,
        "execution_flow": runtime_flow,
        "test_support_3_layers": test_support_3_layers,
        "stacks": stacks_section,
        "profiles_inventory": profiles_inventory,
        "workspaces_inventory": workspaces_inventory,
        "wid_inventory": wid_inventory,
        "btp_inventory": btp_inventory,
        "tools_inventory": tools_inventory,
        "logs_and_outputs": logs_outputs,
        "troubleshooting": troubleshooting,
        "extending_autopts": extending_autopts,
        "official_sources": official_sources,
        "known_limits": known_limits,
        "selection_notes": selection_notes,
    }
    guide["sources_index"] = extract_sources_index(guide)
    return guide


__all__ = ["build_autopts_guide_data", "enforce_autopts_guide_source_policy"]
