from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

try:
    from autopts_guide_data import build_autopts_guide_data
except Exception:  # pragma: no cover - support module import style in local tests
    from tools.autopts_guide_data import build_autopts_guide_data  # type: ignore


REQUIRED_HUB_KEYS = [
    "meta",
    "navigation",
    "auto_pts_summary",
    "group_b",
    "known_limits",
]

PROFILE_IDS = ("BPS", "WSS", "SCPS")
DOC_KINDS = ("logic", "structure")
BLOCK_TYPES = {
    "groupb_finding",
    "groupb_source_observation",
    "groupb_method",
    "groupb_open_question",
    "groupb_decision",
    "groupb_impl_contract",
    "groupb_test_target",
    "groupb_review_signoff",
}

REQUIRED_SECTIONS_BY_KIND = {
    "logic": [
        "סיכום",
        "ממצאים",
        "תצפיות לפי מקור",
        "שיטות חילוץ/ניתוח",
        "פערים ושאלות פתוחות",
        "השלכות למימוש",
        "החלטות Phase 1",
        "חוזה מימוש (Implementation Contract)",
        "יעדי בדיקות Phase 1",
        "חתימת Review / מוכנות",
        "מקורות",
    ],
    "structure": [
        "סיכום",
        "מבנה מוצע",
        "דפוסים שזוהו לפי מקור",
        "שיטות חילוץ/ניתוח",
        "פערים ושאלות פתוחות",
        "השלכות למימוש",
        "החלטות Phase 1",
        "חוזה מימוש (Implementation Contract)",
        "יעדי בדיקות Phase 1",
        "חתימת Review / מוכנות",
        "מקורות",
    ],
}


@dataclass(frozen=True)
class Paths:
    repo: Path
    tools: Path
    templates_root: Path
    group_b_root: Path
    group_b_logic_dir: Path
    group_b_structure_dir: Path
    docs_profiles_root: Path
    data_dir: Path
    builder_script: Path


def _paths(repo_root: Path | str = ".") -> Paths:
    repo = Path(repo_root).resolve()
    tools = repo / "tools"
    templates_root = tools / "templates" / "pts_report_he"
    group_b_root = templates_root / "Group_B_data"
    docs_profiles_root = repo / "docs" / "Profiles"
    if not docs_profiles_root.exists():
        alt = repo / "docs" / "profiles"
        if alt.exists():
            docs_profiles_root = alt
    return Paths(
        repo=repo,
        tools=tools,
        templates_root=templates_root,
        group_b_root=group_b_root,
        group_b_logic_dir=group_b_root / "Logic",
        group_b_structure_dir=group_b_root / "Structure",
        docs_profiles_root=docs_profiles_root,
        data_dir=tools / "data",
        builder_script=tools / "build_pts_report_bundle.py",
    )


def _norm_rel(repo: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def repo_source(paths: Paths, path: Path, line: Optional[int] = None, note: Optional[str] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {"file": _norm_rel(paths.repo, path)}
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
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Invalid UTF-8 in file: {path}") from exc


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(read_text(path))


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
        return value[1:-1]
    return value


def _parse_scalar(value: str) -> Any:
    raw = value.strip()
    if raw == "":
        return ""
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    if raw.lower() in ("null", "none"):
        return None
    if raw.startswith("[") or raw.startswith("{"):
        try:
            return json.loads(raw)
        except Exception:
            return raw
    if re.fullmatch(r"-?\d+", raw):
        try:
            return int(raw)
        except Exception:
            pass
    return _strip_quotes(raw)


def parse_simple_yaml(yaml_text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    current_key: Optional[str] = None
    for raw_line in yaml_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^\s+-\s+", line) and current_key and isinstance(out.get(current_key), list):
            out[current_key].append(_parse_scalar(line.split("-", 1)[1]))
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        current_key = key
        if value == "":
            out[key] = []
            continue
        out[key] = _parse_scalar(value)
    return out


def split_front_matter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end_marker = "\n---\n"
    end = text.find(end_marker, 4)
    if end == -1:
        return {}, text
    fm_text = text[4:end]
    body = text[end + len(end_marker) :]
    return parse_simple_yaml(fm_text), body


def parse_sections(markdown_body: str) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    lines = markdown_body.splitlines()
    for idx, line in enumerate(lines, start=1):
        m = re.match(r"^(##|###)\s+(.+?)\s*$", line)
        if m:
            if current is not None:
                current["body"] = "\n".join(current["body_lines"]).strip()
                current.pop("body_lines", None)
                sections.append(current)
            current = {
                "level": len(m.group(1)),
                "title": m.group(2).strip(),
                "line": idx,
                "body_lines": [],
            }
            continue
        if current is not None:
            current["body_lines"].append(line)
    if current is not None:
        current["body"] = "\n".join(current["body_lines"]).strip()
        current.pop("body_lines", None)
        sections.append(current)
    return sections


BLOCK_RE = re.compile(r"```(groupb_[a-z_]+)\n(.*?)\n```", re.DOTALL)


def parse_structured_blocks(markdown_body: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, match in enumerate(BLOCK_RE.finditer(markdown_body), start=1):
        block_type = match.group(1).strip()
        if block_type not in BLOCK_TYPES:
            continue
        payload_text = match.group(2).strip()
        payload: Dict[str, Any]
        block_line = markdown_body.count("\n", 0, match.start()) + 1
        try:
            parsed = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {block_type} block #{i} (line {block_line}): {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"Structured block {block_type} #{i} (line {block_line}) must contain a JSON object")
        payload = parsed
        payload["_block_type"] = block_type
        payload["_ordinal"] = i
        payload["_line"] = block_line
        out.append(payload)
    return out


def parse_sources_section_ids(sections: List[Dict[str, Any]]) -> List[str]:
    for sec in sections:
        if sec.get("title") != "מקורות":
            continue
        ids: List[str] = []
        for line in str(sec.get("body") or "").splitlines():
            m = re.search(r"`([A-Za-z0-9_\\-]+)`", line)
            if m:
                ids.append(m.group(1))
                continue
            m2 = re.match(r"^\s*-\s*([A-Za-z0-9_\\-]+)\s*$", line)
            if m2:
                ids.append(m2.group(1))
        return ids
    return []


def extract_first_paragraph(text: str) -> str:
    if not text:
        return ""
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return parts[0] if parts else ""


def load_group_b_markdown_doc(paths: Paths, path: Path, expected_kind: str) -> Dict[str, Any]:
    raw = read_text(path) if path.exists() else ""
    try:
        front_matter, body = split_front_matter(raw) if raw else ({}, "")
        sections = parse_sections(body) if body else []
        blocks = parse_structured_blocks(body) if body else []
    except Exception as exc:
        raise ValueError(f"Failed parsing Group_B markdown: {path}") from exc
    section_titles = [str(sec.get("title") or "") for sec in sections]
    required = REQUIRED_SECTIONS_BY_KIND.get(expected_kind, [])
    missing_sections = [title for title in required if title not in section_titles]
    sources_ids = parse_sources_section_ids(sections)

    return {
        "exists": path.exists(),
        "path": _norm_rel(paths.repo, path),
        "front_matter": front_matter,
        "body": body,
        "raw_markdown": raw,
        "sections": sections,
        "blocks": blocks,
        "section_titles": section_titles,
        "missing_sections": missing_sections,
        "declared_source_ids": sources_ids,
        "sources": [repo_source(paths, path, note="Group B source markdown")] if path.exists() else [],
    }


def load_profile_map(paths: Paths) -> Dict[str, Any]:
    path = paths.data_dir / "group_b_profile_map.json"
    parsed = read_json(path)
    rows = parsed.get("profiles") if isinstance(parsed, dict) else []
    if not isinstance(rows, list):
        rows = []
    by_id = {}
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("profile_id"), str):
            by_id[str(row["profile_id"]).upper()] = row
    return {
        "profiles": rows,
        "by_id": by_id,
        "generated_at": parsed.get("generated_at") if isinstance(parsed, dict) else None,
        "sources": [repo_source(paths, path)],
    }


def load_group_b_manifests(paths: Paths) -> Dict[str, Any]:
    official_path = paths.data_dir / "group_b_official_sources.json"
    sdk_path = paths.data_dir / "group_b_sdk_sources.json"
    methods_path = paths.data_dir / "group_b_derivation_methods.json"
    sync_manifest_path = paths.data_dir / "group_b_spec_sync_manifest.json"

    official = read_json(official_path) if official_path.exists() else {"entries": [], "whitelists": {}}
    sdk = read_json(sdk_path) if sdk_path.exists() else {"entries": [], "whitelists": {}}
    methods = read_json(methods_path) if methods_path.exists() else {"methods": []}
    sync_manifest = read_json(sync_manifest_path) if sync_manifest_path.exists() else {"profiles": []}

    source_catalog: Dict[str, Dict[str, Any]] = {}
    for manifest, path in ((official, official_path), (sdk, sdk_path)):
        entries = manifest.get("entries") if isinstance(manifest, dict) else []
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                continue
            item = dict(entry)
            item.setdefault("sources", [repo_source(paths, path)])
            source_catalog[item["id"]] = item

    method_catalog: Dict[str, Dict[str, Any]] = {}
    for method in methods.get("methods", []) if isinstance(methods, dict) else []:
        if not isinstance(method, dict) or not isinstance(method.get("id"), str):
            continue
        item = dict(method)
        item.setdefault("sources", [repo_source(paths, methods_path)])
        method_catalog[item["id"]] = item

    return {
        "official": {
            "manifest": official,
            "path": _norm_rel(paths.repo, official_path),
            "sources": [repo_source(paths, official_path)] if official_path.exists() else [],
        },
        "sdk": {
            "manifest": sdk,
            "path": _norm_rel(paths.repo, sdk_path),
            "sources": [repo_source(paths, sdk_path)] if sdk_path.exists() else [],
        },
        "methods": {
            "manifest": methods,
            "path": _norm_rel(paths.repo, methods_path),
            "catalog": method_catalog,
            "sources": [repo_source(paths, methods_path)] if methods_path.exists() else [],
        },
        "spec_sync": {
            "manifest": sync_manifest,
            "path": _norm_rel(paths.repo, sync_manifest_path),
            "sources": [repo_source(paths, sync_manifest_path)] if sync_manifest_path.exists() else [],
        },
        "source_catalog": source_catalog,
    }


def load_group_b_qa_meta(paths: Paths) -> Dict[str, Any]:
    qa_path = paths.data_dir / "group_b_qa_meta.json"
    default = {
        "last_smoke_test_at": None,
        "smoke_test_mode": "manual",
        "known_expected_console_errors": [
            "GET /dashboards/pts_report_he/api/run-status -> 404 (static server)",
            "GET /favicon.ico -> 404 (static server)",
        ],
        "last_manual_review_notes_he": [
            "יש להשלים QA ידני לכל הטאבים ותתי-הלשוניות אחרי כל שינוי משמעותי בתוכן/רינדור.",
        ],
    }
    if not qa_path.exists():
        return {
            **default,
            "exists": False,
            "sources": [],
        }
    payload = read_json(qa_path)
    if not isinstance(payload, dict):
        payload = {}
    return {
        **default,
        **payload,
        "exists": True,
        "sources": [repo_source(paths, qa_path)],
    }


def _coerce_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return [value]


def _resolve_source_refs(
    source_ids: Iterable[str],
    source_catalog: Dict[str, Dict[str, Any]],
    extra_sources: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for sid in source_ids:
        if not sid:
            continue
        sid_s = str(sid)
        if sid_s in seen:
            continue
        seen.add(sid_s)
        src = source_catalog.get(sid_s)
        if src is None:
            out.append({"note": f"missing_source_id:{sid_s}"})
            continue
        out.append(web_source(src.get("url", ""), src.get("title", sid_s), src.get("retrieved_at", ""), note=f"source_id:{sid_s}"))
    for item in extra_sources or []:
        if item and (item.get("file") or item.get("url")):
            out.append(item)
    return out


def _normalize_finding(
    raw: Dict[str, Any],
    profile_id: str,
    doc_kind: str,
    source_catalog: Dict[str, Dict[str, Any]],
    file_source: Dict[str, Any],
) -> Dict[str, Any]:
    source_ids = [str(x) for x in _coerce_list(raw.get("source_ids")) if str(x)]
    method_ids = [str(x) for x in _coerce_list(raw.get("derivation_method_ids")) if str(x)]
    evidence_refs = raw.get("evidence_refs")
    if not isinstance(evidence_refs, list):
        evidence_refs = []
    normalized = {
        "id": str(raw.get("id") or f"{profile_id.lower()}_{doc_kind}_finding_{raw.get('_ordinal', 0):03d}"),
        "title_he": str(raw.get("title_he") or "ממצא ללא כותרת"),
        "type": doc_kind,
        "statement_he": str(raw.get("statement_he") or ""),
        "why_it_matters_he": str(raw.get("why_it_matters_he") or ""),
        "profile_id": profile_id,
        "confidence": str(raw.get("confidence") or "low"),
        "status": str(raw.get("status") or "needs_validation"),
        "evidence_refs": evidence_refs,
        "derivation_method_ids": method_ids,
        "source_ids": source_ids,
        "related_patterns": [str(x) for x in _coerce_list(raw.get("related_patterns")) if str(x)],
        "implementation_notes_he": [str(x) for x in _coerce_list(raw.get("implementation_notes_he")) if str(x)],
        "sources": _resolve_source_refs(source_ids, source_catalog, [file_source]),
    }
    return normalized


def _normalize_source_observation(
    raw: Dict[str, Any],
    profile_id: str,
    doc_kind: str,
    source_catalog: Dict[str, Dict[str, Any]],
    file_source: Dict[str, Any],
) -> Dict[str, Any]:
    source_id = str(raw.get("source_id") or "")
    refs = _resolve_source_refs([source_id] if source_id else [], source_catalog, [file_source])
    return {
        "id": str(raw.get("id") or f"{profile_id.lower()}_{doc_kind}_obs_{raw.get('_ordinal', 0):03d}"),
        "profile_id": profile_id,
        "doc_kind": doc_kind,
        "source_id": source_id,
        "what_identified_he": str(raw.get("what_identified_he") or ""),
        "how_identified_he": str(raw.get("how_identified_he") or ""),
        "artifact_ref": str(raw.get("artifact_ref") or ""),
        "line_refs": raw.get("line_refs") if isinstance(raw.get("line_refs"), list) else [],
        "quote_excerpt": str(raw.get("quote_excerpt") or ""),
        "confidence": str(raw.get("confidence") or "low"),
        "notes_he": str(raw.get("notes_he") or ""),
        "sources": refs,
    }


def _normalize_open_question(
    raw: Dict[str, Any],
    profile_id: str,
    doc_kind: str,
    source_catalog: Dict[str, Dict[str, Any]],
    file_source: Dict[str, Any],
) -> Dict[str, Any]:
    source_ids = [str(x) for x in _coerce_list(raw.get("source_ids")) if str(x)]
    return {
        "id": str(raw.get("id") or f"{profile_id.lower()}_{doc_kind}_q_{raw.get('_ordinal', 0):03d}"),
        "profile_id": profile_id,
        "doc_kind": doc_kind,
        "title_he": str(raw.get("title_he") or "שאלה פתוחה"),
        "detail_he": str(raw.get("detail_he") or ""),
        "priority": str(raw.get("priority") or "medium"),
        "status": str(raw.get("status") or "open"),
        "source_ids": source_ids,
        "sources": _resolve_source_refs(source_ids, source_catalog, [file_source]),
    }


def _normalize_local_method(raw: Dict[str, Any], profile_id: str, doc_kind: str, file_source: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(raw.get("id") or f"{profile_id.lower()}_{doc_kind}_method_{raw.get('_ordinal', 0):03d}"),
        "profile_id": profile_id,
        "doc_kind": doc_kind,
        "status": str(raw.get("status") or "planned"),
        "notes_he": str(raw.get("notes_he") or ""),
        "sources": [file_source],
    }


def _normalize_phase1_decision(
    raw: Dict[str, Any],
    profile_id: str,
    doc_kind: str,
    source_catalog: Dict[str, Dict[str, Any]],
    file_source: Dict[str, Any],
) -> Dict[str, Any]:
    source_ids = [str(x) for x in _coerce_list(raw.get("source_ids")) if str(x)]
    method_ids = [str(x) for x in _coerce_list(raw.get("derivation_method_ids")) if str(x)]
    return {
        "id": str(raw.get("id") or f"{profile_id.lower()}_{doc_kind}_decision_{raw.get('_ordinal', 0):03d}"),
        "profile_id": profile_id,
        "doc_kind": doc_kind,
        "phase": str(raw.get("phase") or "phase1"),
        "title_he": str(raw.get("title_he") or "החלטה ללא כותרת"),
        "decision_he": str(raw.get("decision_he") or ""),
        "rationale_he": str(raw.get("rationale_he") or ""),
        "status": str(raw.get("status") or "decided"),
        "confidence": str(raw.get("confidence") or "medium"),
        "source_ids": source_ids,
        "derivation_method_ids": method_ids,
        "impacts_he": [str(x) for x in _coerce_list(raw.get("impacts_he")) if str(x)],
        "applies_to_checks": [str(x) for x in _coerce_list(raw.get("applies_to_checks")) if str(x)],
        "sources": _resolve_source_refs(source_ids, source_catalog, [file_source]),
    }


def _normalize_impl_contract_block(
    raw: Dict[str, Any],
    profile_id: str,
    doc_kind: str,
    source_catalog: Dict[str, Dict[str, Any]],
    file_source: Dict[str, Any],
) -> Dict[str, Any]:
    source_ids = [str(x) for x in _coerce_list(raw.get("source_ids")) if str(x)]
    contract = raw.get("service_api_contract") if isinstance(raw.get("service_api_contract"), dict) else {}
    runtime_flow = raw.get("runtime_flow_contract") if isinstance(raw.get("runtime_flow_contract"), dict) else {}
    data_model = raw.get("data_model_contract") if isinstance(raw.get("data_model_contract"), dict) else {}
    ccc_contract = raw.get("ccc_and_notify_indicate_contract") if isinstance(raw.get("ccc_and_notify_indicate_contract"), dict) else {}
    error_policy = raw.get("error_policy_contract") if isinstance(raw.get("error_policy_contract"), dict) else {}
    dependency_contract = raw.get("dependency_contract") if isinstance(raw.get("dependency_contract"), dict) else {}
    module_boundaries = raw.get("module_boundaries") if isinstance(raw.get("module_boundaries"), dict) else {}
    return {
        "id": str(raw.get("id") or f"{profile_id.lower()}_{doc_kind}_impl_contract_{raw.get('_ordinal', 0):03d}"),
        "profile_id": profile_id,
        "doc_kind": doc_kind,
        "phase": str(raw.get("phase") or "phase1"),
        "scope_in": [str(x) for x in _coerce_list(raw.get("scope_in")) if str(x)],
        "scope_out": [str(x) for x in _coerce_list(raw.get("scope_out")) if str(x)],
        "service_api_contract": contract,
        "runtime_flow_contract": runtime_flow,
        "data_model_contract": data_model,
        "ccc_and_notify_indicate_contract": ccc_contract,
        "error_policy_contract": error_policy,
        "dependency_contract": dependency_contract,
        "module_boundaries": module_boundaries,
        "implementation_order": [str(x) for x in _coerce_list(raw.get("implementation_order")) if str(x)],
        "blocking_assumptions": [str(x) for x in _coerce_list(raw.get("blocking_assumptions")) if str(x)],
        "non_blocking_deferred": [str(x) for x in _coerce_list(raw.get("non_blocking_deferred")) if str(x)],
        "summary_he": str(raw.get("summary_he") or ""),
        "source_ids": source_ids,
        "sources": _resolve_source_refs(source_ids, source_catalog, [file_source]),
    }


def _normalize_test_target_block(
    raw: Dict[str, Any],
    profile_id: str,
    doc_kind: str,
    source_catalog: Dict[str, Dict[str, Any]],
    file_source: Dict[str, Any],
) -> Dict[str, Any]:
    source_ids = [str(x) for x in _coerce_list(raw.get("source_ids")) if str(x)]
    return {
        "id": str(raw.get("id") or f"{profile_id.lower()}_{doc_kind}_test_target_{raw.get('_ordinal', 0):03d}"),
        "profile_id": profile_id,
        "doc_kind": doc_kind,
        "phase": str(raw.get("phase") or "phase1"),
        "manual_smoke_checks": [str(x) for x in _coerce_list(raw.get("manual_smoke_checks")) if str(x)],
        "pts_autopts_target_areas": [str(x) for x in _coerce_list(raw.get("pts_autopts_target_areas")) if str(x)],
        "ics_ixit_assumptions": [str(x) for x in _coerce_list(raw.get("ics_ixit_assumptions")) if str(x)],
        "phase1_done_criteria": [str(x) for x in _coerce_list(raw.get("phase1_done_criteria")) if str(x)],
        "known_non_goals": [str(x) for x in _coerce_list(raw.get("known_non_goals")) if str(x)],
        "summary_he": str(raw.get("summary_he") or ""),
        "source_ids": source_ids,
        "sources": _resolve_source_refs(source_ids, source_catalog, [file_source]),
    }


def _normalize_review_signoff_block(
    raw: Dict[str, Any],
    profile_id: str,
    doc_kind: str,
    source_catalog: Dict[str, Dict[str, Any]],
    file_source: Dict[str, Any],
) -> Dict[str, Any]:
    source_ids = [str(x) for x in _coerce_list(raw.get("source_ids")) if str(x)]
    return {
        "id": str(raw.get("id") or f"{profile_id.lower()}_{doc_kind}_review_signoff_{raw.get('_ordinal', 0):03d}"),
        "profile_id": profile_id,
        "doc_kind": doc_kind,
        "logic_reviewed": bool(raw.get("logic_reviewed")),
        "structure_reviewed": bool(raw.get("structure_reviewed")),
        "logic_reviewed_at": str(raw.get("logic_reviewed_at") or ""),
        "structure_reviewed_at": str(raw.get("structure_reviewed_at") or ""),
        "review_summary_he": str(raw.get("review_summary_he") or ""),
        "reviewer_notes_he": [str(x) for x in _coerce_list(raw.get("reviewer_notes_he")) if str(x)],
        "remaining_phase1_blockers": [str(x) for x in _coerce_list(raw.get("remaining_phase1_blockers")) if str(x)],
        "ready_for_impl_phase1": bool(raw.get("ready_for_impl_phase1")),
        "ready_decision_reason_he": str(raw.get("ready_decision_reason_he") or ""),
        "source_ids": source_ids,
        "sources": _resolve_source_refs(source_ids, source_catalog, [file_source]),
    }


def _merge_source_lists(*groups: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for group in groups:
        items = group if isinstance(group, list) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            key = json.dumps(item, ensure_ascii=False, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
    return out


def _pick_best_block(candidates: List[Dict[str, Any]], preferred_doc_kind: str = "structure") -> Dict[str, Any]:
    if not candidates:
        return {}
    for item in candidates:
        if str(item.get("doc_kind") or "") == preferred_doc_kind:
            return item
    return candidates[0]


def _extract_analysis_warnings(findings: List[Dict[str, Any]], source_observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    warnings: List[Dict[str, Any]] = []
    for finding in findings:
        confidence = str(finding.get("confidence") or "").lower()
        status = str(finding.get("status") or "").lower()
        evidence_refs = finding.get("evidence_refs") if isinstance(finding.get("evidence_refs"), list) else []
        if status == "inferred" and confidence == "high" and len(evidence_refs) < 2:
            warnings.append(
                {
                    "severity": "warning",
                    "code": "inferred_high_confidence_low_evidence",
                    "finding_id": finding.get("id"),
                    "message_he": "ממצא מוסק עם ודאות גבוהה ללא לפחות 2 ראיות מפורטות.",
                }
            )
    for obs in source_observations:
        line_refs = obs.get("line_refs") if isinstance(obs.get("line_refs"), list) else []
        if not line_refs:
            warnings.append(
                {
                    "severity": "warning",
                    "code": "source_observation_missing_line_refs",
                    "source_observation_id": obs.get("id"),
                    "message_he": "תצפית מקור ללא line_refs. מומלץ להוסיף שורות/טווחים.",
                }
            )
    return warnings


def _detect_phase1_subset_decision(
    profile_id: str,
    doc_kind: str,
    findings: List[Dict[str, Any]],
    implications: List[str],
    open_questions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    phase_tokens = ("phase 1", "שלב 1", "שלב ראשון", "subset")
    searchable_findings = []
    for finding in findings:
        searchable_findings.append(
            " ".join(
                [
                    str(finding.get("id") or ""),
                    str(finding.get("title_he") or ""),
                    str(finding.get("statement_he") or ""),
                    str(finding.get("why_it_matters_he") or ""),
                ]
            ).lower()
        )
    searchable_implications = " ".join(str(x) for x in implications).lower()
    phase_findings = [f for f in findings if any(t in " ".join([str(f.get("id") or ""), str(f.get("title_he") or ""), str(f.get("statement_he") or "")]).lower() for t in phase_tokens)]
    has_phase_text = any(any(t in text for t in phase_tokens) for text in searchable_findings) or any(
        t in searchable_implications for t in phase_tokens
    )

    unresolved_phase_questions = []
    for q in open_questions:
        q_text = " ".join([str(q.get("id") or ""), str(q.get("title_he") or ""), str(q.get("detail_he") or "")]).lower()
        if any(t in q_text for t in phase_tokens):
            unresolved_phase_questions.append(q)

    decided = bool(phase_findings or has_phase_text) and not any(str(q.get("status") or "open").lower() == "open" for q in unresolved_phase_questions)
    note = (
        f"{profile_id}/{doc_kind}: נמצאה החלטת Phase 1 subset"
        if decided
        else f"{profile_id}/{doc_kind}: טרם זוהתה החלטת Phase 1 subset מפורשת"
    )
    return {
        "decided": decided,
        "has_phase_related_text": has_phase_text,
        "open_phase_questions": [str(q.get("id") or "") for q in unresolved_phase_questions],
        "note_he": note,
    }


def build_knowledge_analysis(
    paths: Paths,
    profile_id: str,
    doc_kind: str,
    doc: Dict[str, Any],
    source_catalog: Dict[str, Dict[str, Any]],
    derivation_catalog: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    file_source = doc.get("sources", [{}])[0] if doc.get("sources") else {"file": doc.get("path")}
    front = doc.get("front_matter") if isinstance(doc.get("front_matter"), dict) else {}
    sections = doc.get("sections", [])
    summary_section_title = "סיכום"
    summary_body = ""
    implications_body = ""
    for sec in sections:
        if sec.get("title") == summary_section_title:
            summary_body = str(sec.get("body") or "")
        if sec.get("title") == "השלכות למימוש":
            implications_body = str(sec.get("body") or "")

    blocks = doc.get("blocks", [])
    findings = [
        _normalize_finding(b, profile_id, doc_kind, source_catalog, file_source)
        for b in blocks
        if isinstance(b, dict) and b.get("_block_type") == "groupb_finding"
    ]
    source_observations = [
        _normalize_source_observation(b, profile_id, doc_kind, source_catalog, file_source)
        for b in blocks
        if isinstance(b, dict) and b.get("_block_type") == "groupb_source_observation"
    ]
    local_methods = [
        _normalize_local_method(b, profile_id, doc_kind, file_source)
        for b in blocks
        if isinstance(b, dict) and b.get("_block_type") == "groupb_method"
    ]
    open_questions = [
        _normalize_open_question(b, profile_id, doc_kind, source_catalog, file_source)
        for b in blocks
        if isinstance(b, dict) and b.get("_block_type") == "groupb_open_question"
    ]
    phase1_decisions = [
        _normalize_phase1_decision(b, profile_id, doc_kind, source_catalog, file_source)
        for b in blocks
        if isinstance(b, dict) and b.get("_block_type") == "groupb_decision"
    ]
    impl_contract_blocks = [
        _normalize_impl_contract_block(b, profile_id, doc_kind, source_catalog, file_source)
        for b in blocks
        if isinstance(b, dict) and b.get("_block_type") == "groupb_impl_contract"
    ]
    test_target_blocks = [
        _normalize_test_target_block(b, profile_id, doc_kind, source_catalog, file_source)
        for b in blocks
        if isinstance(b, dict) and b.get("_block_type") == "groupb_test_target"
    ]
    review_signoff_blocks = [
        _normalize_review_signoff_block(b, profile_id, doc_kind, source_catalog, file_source)
        for b in blocks
        if isinstance(b, dict) and b.get("_block_type") == "groupb_review_signoff"
    ]

    used_method_ids = set()
    for finding in findings:
        used_method_ids.update(str(x) for x in finding.get("derivation_method_ids", []))
    used_method_ids.update(str(m.get("id")) for m in local_methods if m.get("id"))

    derivation_methods: List[Dict[str, Any]] = []
    for method_id in sorted(used_method_ids):
        if method_id in derivation_catalog:
            derivation_methods.append(dict(derivation_catalog[method_id]))
            continue
        local_match = next((m for m in local_methods if m.get("id") == method_id), None)
        if local_match:
            derivation_methods.append(dict(local_match))

    confidence_counts = Counter()
    for item in findings:
        confidence_counts[str(item.get("confidence") or "unknown")] += 1
    for item in source_observations:
        confidence_counts[str(item.get("confidence") or "unknown")] += 1

    source_ids_declared = [str(x) for x in doc.get("declared_source_ids", []) if str(x)]
    all_source_ids: List[str] = []
    for item in findings:
        all_source_ids.extend([str(x) for x in item.get("source_ids", []) if str(x)])
    for item in source_observations:
        if item.get("source_id"):
            all_source_ids.append(str(item["source_id"]))
    for item in open_questions:
        all_source_ids.extend([str(x) for x in item.get("source_ids", []) if str(x)])
    all_source_ids.extend(source_ids_declared)
    dedup_source_ids = list(dict.fromkeys(all_source_ids))

    implementation_implications = [
        line.strip("- ").strip()
        for line in implications_body.splitlines()
        if line.strip()
    ]

    missing_methods = [mid for mid in used_method_ids if mid not in derivation_catalog and mid not in {m.get("id") for m in local_methods}]
    warnings = _extract_analysis_warnings(findings, source_observations)
    phase1_subset = _detect_phase1_subset_decision(profile_id, doc_kind, findings, implementation_implications, open_questions)

    return {
        "profile_id": profile_id,
        "ui_label": "ScPS" if profile_id == "SCPS" else profile_id,
        "doc_kind": doc_kind,
        "status": str(front.get("status") or ("missing" if not doc.get("exists") else "draft")),
        "summary_he": extract_first_paragraph(summary_body) or "אין תקציר זמין (טרם הוזן תוכן).",
        "core_findings": findings,
        "source_observations": source_observations,
        "derivation_methods": derivation_methods,
        "inference_steps": [],
        "confidence_scores": dict(sorted(confidence_counts.items())),
        "open_questions": open_questions,
        "phase1_decisions": phase1_decisions,
        "implementation_contract_blocks": impl_contract_blocks,
        "test_target_blocks": test_target_blocks,
        "review_signoff_blocks": review_signoff_blocks,
        "implementation_implications": implementation_implications,
        "sources": _resolve_source_refs(dedup_source_ids, source_catalog, [file_source]),
        "source_ids": dedup_source_ids,
        "doc_meta": {
            "path": doc.get("path"),
            "exists": bool(doc.get("exists")),
            "front_matter": front,
            "section_titles": doc.get("section_titles", []),
            "missing_sections": doc.get("missing_sections", []),
        },
        "raw_markdown": doc.get("raw_markdown", ""),
        "raw_markdown_preview": "\n".join(str(doc.get("raw_markdown") or "").splitlines()[:60]),
        "validation": {
            "missing_sections": doc.get("missing_sections", []),
            "missing_methods": missing_methods,
            "has_front_matter": bool(front),
            "block_counts": {
                "findings": len(findings),
                "source_observations": len(source_observations),
                "methods": len(local_methods),
                "open_questions": len(open_questions),
                "phase1_decisions": len(phase1_decisions),
                "impl_contracts": len(impl_contract_blocks),
                "test_targets": len(test_target_blocks),
                "review_signoffs": len(review_signoff_blocks),
            },
            "warnings": warnings,
        },
        "warnings": warnings,
        "phase1_subset": phase1_subset,
    }


def classify_spec_artifact(path: Path) -> str:
    name = path.name.lower()
    if path.is_dir():
        if "tcrl" in name:
            return "tcrl_folder"
        if "ixit" in name:
            return "ixit_folder"
        return "folder"
    if name.endswith(".pdf"):
        if "conformance_statement" in name or "ics" in name:
            return "ics_pdf"
        if "extra_information" in name or "ixit" in name:
            return "ixit_pdf"
        if "test_suite" in name or name == "test_suite_ts.pdf":
            return "ts_pdf"
        if "changes_since" in name:
            return "changes_pdf"
        if "errata" in name:
            return "errata_pdf"
        if "scan_parameters_service" in name or "weight_scale_service" in name or "blood_pressure_service" in name:
            return "spec_pdf"
        return "pdf"
    if name.endswith(".xlsx"):
        return "tcrl_xlsx"
    if name.endswith(".xls"):
        return "xls"
    if name.endswith(".html"):
        return "html"
    return "file"


def build_spec_research(
    paths: Paths,
    profile_map: Dict[str, Any],
    manifests: Dict[str, Any],
) -> Dict[str, Any]:
    sync_manifest = manifests.get("spec_sync", {}).get("manifest", {})
    sync_profiles_rows = sync_manifest.get("profiles", []) if isinstance(sync_manifest, dict) else []
    sync_by_id = {
        str(row.get("profile_id")).upper(): row
        for row in sync_profiles_rows
        if isinstance(row, dict) and row.get("profile_id")
    }
    official_entries = manifests.get("official", {}).get("manifest", {}).get("entries", [])
    official_by_profile: Dict[str, List[Dict[str, Any]]] = {pid: [] for pid in PROFILE_IDS}
    for entry in official_entries if isinstance(official_entries, list) else []:
        if not isinstance(entry, dict):
            continue
        for pid in entry.get("profile_ids", []) if isinstance(entry.get("profile_ids"), list) else []:
            pid_u = str(pid).upper()
            if pid_u in official_by_profile:
                official_by_profile[pid_u].append(entry)

    rows: List[Dict[str, Any]] = []
    summaries: Dict[str, Any] = {}
    for row in profile_map.get("profiles", []):
        if not isinstance(row, dict):
            continue
        pid = str(row.get("profile_id") or "").upper()
        if pid not in PROFILE_IDS:
            continue
        prof_dir = paths.repo / str(row.get("spec_dir") or "")
        if not prof_dir.exists():
            alt_rel = str(row.get("spec_dir") or "").replace("docs/Profiles/", "docs/profiles/")
            alt_dir = paths.repo / alt_rel
            if alt_dir.exists():
                prof_dir = alt_dir
        artifacts: List[Dict[str, Any]] = []
        if prof_dir.exists():
            for item in sorted(prof_dir.iterdir(), key=lambda p: p.name.lower()):
                if item.name.startswith("."):
                    continue
                kind = classify_spec_artifact(item)
                artifact: Dict[str, Any] = {
                    "name": item.name,
                    "path": _norm_rel(paths.repo, item),
                    "kind": kind,
                    "is_dir": item.is_dir(),
                    "sources": [repo_source(paths, item)],
                }
                if item.is_dir():
                    xlsx_files = sorted(item.rglob("*.xlsx"))
                    artifact["xlsx_count"] = len(xlsx_files)
                    artifact["sample_files"] = [_norm_rel(paths.repo, p) for p in xlsx_files[:6]]
                else:
                    try:
                        artifact["size_bytes"] = item.stat().st_size
                    except Exception:
                        pass
                artifacts.append(artifact)
        kind_counts = Counter(str(a.get("kind") or "unknown") for a in artifacts)
        sync_info = sync_by_id.get(pid, {})
        official_refs = []
        for entry in official_by_profile.get(pid, []):
            official_refs.append(
                web_source(
                    str(entry.get("url") or ""),
                    str(entry.get("title") or ""),
                    str(entry.get("retrieved_at") or ""),
                    note=f"category:{entry.get('category') or 'unknown'}",
                )
            )

        summaries[pid] = {
            "profile_id": pid,
            "ui_label": "ScPS" if pid == "SCPS" else pid,
            "display_name_he": row.get("display_name_he") or pid,
            "spec_dir": _norm_rel(paths.repo, prof_dir),
            "exists": prof_dir.exists(),
            "sync_status": str(sync_info.get("status") or ("present" if prof_dir.exists() else "missing")),
            "resolved_title": sync_info.get("resolved_title"),
            "spec_page_url": sync_info.get("spec_page_url"),
            "query": sync_info.get("query") or row.get("spec_query"),
            "artifacts": artifacts,
            "summary": {
                "artifact_count": len(artifacts),
                "kind_counts": dict(sorted(kind_counts.items())),
                "tcrl_xlsx_total": sum(int(a.get("xlsx_count") or 0) for a in artifacts if a.get("kind") == "tcrl_folder"),
                "has_spec_pdf": any(a.get("kind") == "spec_pdf" for a in artifacts),
                "has_ics_pdf": any(a.get("kind") == "ics_pdf" for a in artifacts),
                "has_ts_pdf": any(a.get("kind") == "ts_pdf" for a in artifacts),
                "has_tcrl_folder": any(a.get("kind") == "tcrl_folder" for a in artifacts),
                "has_ixit": any(a.get("kind") in ("ixit_pdf", "ixit_folder") for a in artifacts),
            },
            "notes": list(sync_info.get("notes", [])) if isinstance(sync_info.get("notes"), list) else [],
            "sources": [repo_source(paths, prof_dir, note="Profile specs directory")] + official_refs + [
                *manifests.get("spec_sync", {}).get("sources", []),
                *manifests.get("official", {}).get("sources", []),
            ],
        }
        rows.append(summaries[pid])

    return {
        "profiles": summaries,
        "rows": rows,
        "summary": {
            "profiles": len(rows),
            "synced": sum(1 for r in rows if r.get("sync_status") == "synced"),
            "with_artifacts": sum(1 for r in rows if (r.get("summary") or {}).get("artifact_count", 0)),
        },
        "sources": manifests.get("spec_sync", {}).get("sources", []) + manifests.get("official", {}).get("sources", []),
    }


def build_md_file_inventory(
    paths: Paths,
    profile_map: Dict[str, Any],
    manifests: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    source_catalog = manifests.get("source_catalog", {})
    derivation_catalog = manifests.get("methods", {}).get("catalog", {})
    logic_files: Dict[str, Any] = {}
    structure_files: Dict[str, Any] = {}
    logic_analysis: Dict[str, Any] = {}
    structure_analysis: Dict[str, Any] = {}

    by_id = profile_map.get("by_id", {})
    for pid in PROFILE_IDS:
        row = by_id.get(pid, {})
        logic_path = paths.repo / str(row.get("group_b_logic_md") or paths.group_b_logic_dir / f"{pid}.md")
        structure_path = paths.repo / str(row.get("group_b_structure_md") or paths.group_b_structure_dir / f"{pid}.md")

        logic_doc = load_group_b_markdown_doc(paths, logic_path, "logic")
        structure_doc = load_group_b_markdown_doc(paths, structure_path, "structure")

        logic_files[pid] = {
            "profile_id": pid,
            "ui_label": "ScPS" if pid == "SCPS" else pid,
            "doc_kind": "logic",
            "path": logic_doc.get("path"),
            "exists": logic_doc.get("exists"),
            "front_matter": logic_doc.get("front_matter"),
            "missing_sections": logic_doc.get("missing_sections"),
            "section_titles": logic_doc.get("section_titles"),
            "raw_markdown": logic_doc.get("raw_markdown"),
            "sources": logic_doc.get("sources", []),
        }
        structure_files[pid] = {
            "profile_id": pid,
            "ui_label": "ScPS" if pid == "SCPS" else pid,
            "doc_kind": "structure",
            "path": structure_doc.get("path"),
            "exists": structure_doc.get("exists"),
            "front_matter": structure_doc.get("front_matter"),
            "missing_sections": structure_doc.get("missing_sections"),
            "section_titles": structure_doc.get("section_titles"),
            "raw_markdown": structure_doc.get("raw_markdown"),
            "sources": structure_doc.get("sources", []),
        }

        logic_analysis[pid] = build_knowledge_analysis(paths, pid, "logic", logic_doc, source_catalog, derivation_catalog)
        structure_analysis[pid] = build_knowledge_analysis(paths, pid, "structure", structure_doc, source_catalog, derivation_catalog)

    return logic_files, structure_files, logic_analysis, structure_analysis


def summarize_autopts_for_hub(paths: Paths, autopts_guide: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    guide = autopts_guide or build_autopts_guide_data(paths.repo)
    quickstart_rows = []
    for sc in (guide.get("quickstart", {}) or {}).get("scenarios", [])[:8]:
        if not isinstance(sc, dict):
            continue
        quickstart_rows.append(
            {
                "title": sc.get("title"),
                "summary": sc.get("summary"),
                "commands": sc.get("commands", [])[:4] if isinstance(sc.get("commands"), list) else [],
                "sources": sc.get("sources", []),
            }
        )
    three_layers = ((guide.get("test_support_3_layers", {}) or {}).get("layers", {}) or {})
    code_layer = three_layers.get("code_support", {}) if isinstance(three_layers, dict) else {}
    ws_layer = three_layers.get("bundled_workspaces", {}) if isinstance(three_layers, dict) else {}
    runtime_layer = three_layers.get("exact_runtime", {}) if isinstance(three_layers, dict) else {}

    return {
        "summary_he": "סיכום ממוקד של תשתית AutoPTS, כדי לתמוך בעבודת Group B בלי להעמיס מידע בתוך הדשבורד הראשי.",
        "meta": {
            "generated_date": (guide.get("meta", {}) or {}).get("generated_date"),
            "autopts_repo": (guide.get("meta", {}) or {}).get("autopts_repo"),
        },
        "overview": {
            "summary": (guide.get("overview", {}) or {}).get("summary"),
            "key_points": (guide.get("overview", {}) or {}).get("key_points", [])[:8],
            "defaults": (guide.get("overview", {}) or {}).get("defaults", {}),
            "stack_summary": (guide.get("overview", {}) or {}).get("stack_summary", {}),
            "sources": (guide.get("overview", {}) or {}).get("sources", []),
        },
        "quickstart": {
            "scenarios": quickstart_rows,
            "sources": (guide.get("quickstart", {}) or {}).get("sources", []),
        },
        "cli": {
            "summary": (guide.get("cli", {}) or {}).get("summary", {}),
            "group_labels": (guide.get("cli", {}) or {}).get("group_labels", {}),
            "sample_arguments": [a for a in ((guide.get("cli", {}) or {}).get("arguments", []) if isinstance((guide.get("cli", {}) or {}).get("arguments"), list) else [])[:12]],
            "sources": (guide.get("cli", {}) or {}).get("sources", []),
        },
        "test_support_3_layers": {
            "summary_he": "העמוד החדש מציג את שלוש שכבות התמיכה (כיסוי קוד / workspaces / runtime exact) בצורה תמציתית.",
            "code_support": {
                "summary": (code_layer or {}).get("summary", {}),
                "top_profiles": (code_layer or {}).get("top_explicit_profiles", [])[:12],
                "sources": (code_layer or {}).get("sources", []),
            },
            "bundled_workspaces": {
                "summary": (ws_layer or {}).get("summary", {}),
                "limitations": (ws_layer or {}).get("limitations", []),
                "sources": (ws_layer or {}).get("sources", []),
            },
            "exact_runtime": {
                "platform_requirements": (runtime_layer or {}).get("platform_requirements", []),
                "commands": (runtime_layer or {}).get("commands", [])[:6],
                "filtering_rules": (runtime_layer or {}).get("filtering_rules", [])[:6],
                "sources": (runtime_layer or {}).get("sources", []),
            },
            "sources": (guide.get("test_support_3_layers", {}) or {}).get("sources", []),
        },
        "stacks": {
            "summary": (guide.get("stacks", {}) or {}).get("summary", {}),
            "rows": (guide.get("stacks", {}) or {}).get("rows", []),
            "sources": (guide.get("stacks", {}) or {}).get("sources", []),
        },
        "profiles_inventory": {
            "rows_count": len((guide.get("profiles_inventory", {}) or {}).get("rows", []) if isinstance((guide.get("profiles_inventory", {}) or {}).get("rows"), list) else []),
            "sources": (guide.get("profiles_inventory", {}) or {}).get("sources", []),
        },
        "official_sources": (guide.get("official_sources", {}) or {}),
        "sources": (guide.get("meta", {}) or {}).get("sources", []),
    }


def _is_contract_defined(contract: Dict[str, Any]) -> bool:
    if not isinstance(contract, dict):
        return False
    required_list_keys = ("scope_in", "implementation_order")
    if any(not isinstance(contract.get(k), list) or not contract.get(k) for k in required_list_keys):
        return False
    for key in (
        "service_api_contract",
        "runtime_flow_contract",
        "data_model_contract",
        "ccc_and_notify_indicate_contract",
        "error_policy_contract",
        "dependency_contract",
        "module_boundaries",
    ):
        if not isinstance(contract.get(key), dict) or not contract.get(key):
            return False
    return bool(contract.get("sources"))


def _is_test_target_defined(test_target: Dict[str, Any]) -> bool:
    if not isinstance(test_target, dict):
        return False
    for key in ("manual_smoke_checks", "phase1_done_criteria", "ics_ixit_assumptions"):
        if not isinstance(test_target.get(key), list) or not test_target.get(key):
            return False
    return bool(test_target.get("sources"))


def build_phase1_profile_artifacts(
    profile_map: Dict[str, Any],
    logic_analysis: Dict[str, Any],
    structure_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    by_id = {str(r.get("profile_id") or "").upper(): r for r in profile_map.get("profiles", []) if isinstance(r, dict)}
    implementation_contracts: Dict[str, Any] = {}
    test_targets_phase1: Dict[str, Any] = {}
    review_signoffs: Dict[str, Any] = {}
    decisions_by_profile: Dict[str, Any] = {}
    rows: List[Dict[str, Any]] = []

    for pid in PROFILE_IDS:
        p_row = by_id.get(pid, {})
        logic = logic_analysis.get(pid, {}) if isinstance(logic_analysis, dict) else {}
        structure = structure_analysis.get(pid, {}) if isinstance(structure_analysis, dict) else {}

        logic_decisions = logic.get("phase1_decisions", []) if isinstance(logic.get("phase1_decisions"), list) else []
        structure_decisions = (
            structure.get("phase1_decisions", []) if isinstance(structure.get("phase1_decisions"), list) else []
        )
        decisions = [*logic_decisions, *structure_decisions]
        decisions_by_profile[pid] = {
            "profile_id": pid,
            "ui_label": p_row.get("ui_label") or ("ScPS" if pid == "SCPS" else pid),
            "rows": decisions,
            "sources": _merge_source_lists(
                *[d.get("sources", []) for d in decisions if isinstance(d, dict)],
                logic.get("sources", []),
                structure.get("sources", []),
            ),
        }

        contract_candidates = []
        for item in logic.get("implementation_contract_blocks", []) if isinstance(logic.get("implementation_contract_blocks"), list) else []:
            if isinstance(item, dict):
                contract_candidates.append(item)
        for item in (
            structure.get("implementation_contract_blocks", [])
            if isinstance(structure.get("implementation_contract_blocks"), list)
            else []
        ):
            if isinstance(item, dict):
                contract_candidates.append(item)
        contract = _pick_best_block(contract_candidates, preferred_doc_kind="structure")
        if contract:
            contract = dict(contract)
        if not contract:
            contract = {
                "profile_id": pid,
                "phase": "phase1",
                "scope_in": [],
                "scope_out": [],
                "service_api_contract": {},
                "runtime_flow_contract": {},
                "data_model_contract": {},
                "ccc_and_notify_indicate_contract": {},
                "error_policy_contract": {},
                "dependency_contract": {},
                "module_boundaries": {},
                "implementation_order": [],
                "blocking_assumptions": [],
                "non_blocking_deferred": [],
                "summary_he": "",
                "sources": [],
                "source_ids": [],
                "doc_kind": "",
                "id": "",
            }
        contract["is_defined"] = _is_contract_defined(contract)
        implementation_contracts[pid] = contract

        test_target_candidates = []
        for item in logic.get("test_target_blocks", []) if isinstance(logic.get("test_target_blocks"), list) else []:
            if isinstance(item, dict):
                test_target_candidates.append(item)
        for item in structure.get("test_target_blocks", []) if isinstance(structure.get("test_target_blocks"), list) else []:
            if isinstance(item, dict):
                test_target_candidates.append(item)
        test_target = _pick_best_block(test_target_candidates, preferred_doc_kind="structure")
        if test_target:
            test_target = dict(test_target)
        if not test_target:
            test_target = {
                "profile_id": pid,
                "phase": "phase1",
                "manual_smoke_checks": [],
                "pts_autopts_target_areas": [],
                "ics_ixit_assumptions": [],
                "phase1_done_criteria": [],
                "known_non_goals": [],
                "summary_he": "",
                "sources": [],
                "source_ids": [],
                "doc_kind": "",
                "id": "",
            }
        test_target["is_defined"] = _is_test_target_defined(test_target)
        test_targets_phase1[pid] = test_target

        signoff_candidates = []
        for item in logic.get("review_signoff_blocks", []) if isinstance(logic.get("review_signoff_blocks"), list) else []:
            if isinstance(item, dict):
                signoff_candidates.append(item)
        for item in structure.get("review_signoff_blocks", []) if isinstance(structure.get("review_signoff_blocks"), list) else []:
            if isinstance(item, dict):
                signoff_candidates.append(item)
        signoff = _pick_best_block(signoff_candidates, preferred_doc_kind="structure")
        if signoff:
            signoff = dict(signoff)
        else:
            signoff = {
                "profile_id": pid,
                "logic_reviewed": False,
                "structure_reviewed": False,
                "logic_reviewed_at": "",
                "structure_reviewed_at": "",
                "review_summary_he": "",
                "reviewer_notes_he": [],
                "remaining_phase1_blockers": [],
                "ready_for_impl_phase1": False,
                "ready_decision_reason_he": "",
                "sources": [],
                "source_ids": [],
                "doc_kind": "",
                "id": "",
            }
        signoff["review_signoff_complete"] = bool(
            signoff.get("logic_reviewed")
            and signoff.get("structure_reviewed")
            and str(signoff.get("review_summary_he") or "").strip()
            and str(signoff.get("ready_decision_reason_he") or "").strip()
        )
        signoff["phase1_blockers_closed_or_deferred"] = len(signoff.get("remaining_phase1_blockers", []) or []) == 0
        review_signoffs[pid] = signoff

        rows.append(
            {
                "profile_id": pid,
                "ui_label": p_row.get("ui_label") or ("ScPS" if pid == "SCPS" else pid),
                "decisions_count": len(decisions),
                "implementation_contract_defined": bool(contract.get("is_defined")),
                "phase1_test_targets_defined": bool(test_target.get("is_defined")),
                "review_signoff_complete": bool(signoff.get("review_signoff_complete")),
                "phase1_blockers_closed_or_deferred": bool(signoff.get("phase1_blockers_closed_or_deferred")),
                "ready_for_impl_phase1": bool(signoff.get("ready_for_impl_phase1")),
            }
        )

    summary = {
        "profiles": len(rows),
        "implementation_contract_defined": sum(1 for r in rows if r.get("implementation_contract_defined")),
        "phase1_test_targets_defined": sum(1 for r in rows if r.get("phase1_test_targets_defined")),
        "review_signoff_complete": sum(1 for r in rows if r.get("review_signoff_complete")),
        "phase1_blockers_closed_or_deferred": sum(1 for r in rows if r.get("phase1_blockers_closed_or_deferred")),
        "ready_for_impl_phase1": sum(1 for r in rows if r.get("ready_for_impl_phase1")),
    }
    return {
        "implementation_contracts": implementation_contracts,
        "test_targets_phase1": test_targets_phase1,
        "review_signoffs": review_signoffs,
        "phase1_decisions": decisions_by_profile,
        "summary": summary,
        "rows": rows,
        "sources": [],
    }


def build_readiness_gates(
    profile_map: Dict[str, Any],
    spec_research: Dict[str, Any],
    logic_analysis: Dict[str, Any],
    structure_analysis: Dict[str, Any],
    implementation_contracts: Dict[str, Any],
    test_targets_phase1: Dict[str, Any],
    review_signoffs: Dict[str, Any],
) -> Dict[str, Any]:
    by_id = {str(r.get("profile_id") or "").upper(): r for r in profile_map.get("profiles", []) if isinstance(r, dict)}
    profiles: Dict[str, Any] = {}
    rows: List[Dict[str, Any]] = []
    for pid in PROFILE_IDS:
        p_row = by_id.get(pid, {})
        spec = (spec_research.get("profiles", {}) or {}).get(pid, {})
        logic = logic_analysis.get(pid, {})
        structure = structure_analysis.get(pid, {})
        impl_contract = implementation_contracts.get(pid, {}) if isinstance(implementation_contracts, dict) else {}
        test_targets = test_targets_phase1.get(pid, {}) if isinstance(test_targets_phase1, dict) else {}
        signoff = review_signoffs.get(pid, {}) if isinstance(review_signoffs, dict) else {}

        logic_findings = len(logic.get("core_findings", []) if isinstance(logic.get("core_findings"), list) else [])
        struct_findings = len(structure.get("core_findings", []) if isinstance(structure.get("core_findings"), list) else [])
        logic_obs = len(logic.get("source_observations", []) if isinstance(logic.get("source_observations"), list) else [])
        struct_obs = len(structure.get("source_observations", []) if isinstance(structure.get("source_observations"), list) else [])

        checks = [
            ("spec_sync_complete", (spec.get("sync_status") == "synced"), "בוצע סנכרון specs רשמי"),
            ("logic_analysis_baselined", logic_findings >= 5 and logic_obs >= 4, "לוגיקה: >=5 ממצאים ו->=4 תצפיות מקור"),
            ("structure_analysis_baselined", struct_findings >= 5 and struct_obs >= 4, "מבנה: >=5 ממצאים ו->=4 תצפיות מקור"),
            ("logic_analysis_reviewed", str(logic.get("status") or "").lower() in {"reviewed", "ready"}, "לוגיקה סומנה reviewed/ready"),
            ("structure_analysis_reviewed", str(structure.get("status") or "").lower() in {"reviewed", "ready"}, "מבנה סומן reviewed/ready"),
            (
                "phase1_subset_decided",
                bool((logic.get("phase1_subset") or {}).get("decided")) or bool((structure.get("phase1_subset") or {}).get("decided")),
                "הוגדרה החלטת Phase 1 subset מפורשת",
            ),
            (
                "implementation_contract_defined",
                bool(impl_contract.get("is_defined")),
                "הוגדר חוזה מימוש Phase 1 מלא",
            ),
            (
                "phase1_test_targets_defined",
                bool(test_targets.get("is_defined")),
                "הוגדרו יעדי בדיקות Phase 1",
            ),
            (
                "phase1_blockers_closed_or_deferred",
                bool(signoff.get("phase1_blockers_closed_or_deferred")),
                "אין blockers של Phase 1 (או שסומנו deferred שאינם חוסמים)",
            ),
            (
                "review_signoff_complete",
                bool(signoff.get("review_signoff_complete")) and bool(signoff.get("ready_for_impl_phase1")),
                "קיימת חתימת review מלאה עם ready_for_impl_phase1=true",
            ),
        ]

        required_checks = [c[0] for c in checks]
        completed_checks = [c[0] for c in checks if c[1]]
        blocked_checks = [
            {
                "id": c[0],
                "reason_he": c[2],
            }
            for c in checks
            if not c[1]
        ]
        ready_for_impl_phase1 = all(c[1] for c in checks)
        decision_notes_he = [
            f"Logic findings/source observations: {logic_findings}/{logic_obs}",
            f"Structure findings/source observations: {struct_findings}/{struct_obs}",
            str((logic.get("phase1_subset") or {}).get("note_he") or ""),
            str((structure.get("phase1_subset") or {}).get("note_he") or ""),
            f"Implementation contract defined: {'yes' if impl_contract.get('is_defined') else 'no'}",
            f"Test targets defined: {'yes' if test_targets.get('is_defined') else 'no'}",
            str(signoff.get("ready_decision_reason_he") or ""),
        ]
        gate_row = {
            "profile_id": pid,
            "ui_label": p_row.get("ui_label") or ("ScPS" if pid == "SCPS" else pid),
            "display_name_he": p_row.get("display_name_he") or pid,
            "required_checks": required_checks,
            "completed_checks": completed_checks,
            "blocked_checks": blocked_checks,
            "decision_notes_he": [x for x in decision_notes_he if x],
            "last_reviewed_at": signoff.get("structure_reviewed_at") or signoff.get("logic_reviewed_at") or None,
            "ready_for_impl_phase1": ready_for_impl_phase1,
            "sources": _merge_source_lists(impl_contract.get("sources", []), test_targets.get("sources", []), signoff.get("sources", [])),
        }
        profiles[pid] = gate_row
        rows.append(gate_row)

    summary = {
        "profiles": len(rows),
        "spec_sync_complete": sum(1 for r in rows if "spec_sync_complete" in r.get("completed_checks", [])),
        "logic_analysis_baselined": sum(1 for r in rows if "logic_analysis_baselined" in r.get("completed_checks", [])),
        "structure_analysis_baselined": sum(1 for r in rows if "structure_analysis_baselined" in r.get("completed_checks", [])),
        "logic_analysis_reviewed": sum(1 for r in rows if "logic_analysis_reviewed" in r.get("completed_checks", [])),
        "structure_analysis_reviewed": sum(1 for r in rows if "structure_analysis_reviewed" in r.get("completed_checks", [])),
        "phase1_subset_decided": sum(1 for r in rows if "phase1_subset_decided" in r.get("completed_checks", [])),
        "implementation_contract_defined": sum(1 for r in rows if "implementation_contract_defined" in r.get("completed_checks", [])),
        "phase1_test_targets_defined": sum(1 for r in rows if "phase1_test_targets_defined" in r.get("completed_checks", [])),
        "phase1_blockers_closed_or_deferred": sum(
            1 for r in rows if "phase1_blockers_closed_or_deferred" in r.get("completed_checks", [])
        ),
        "review_signoff_complete": sum(1 for r in rows if "review_signoff_complete" in r.get("completed_checks", [])),
        "ready_for_impl_phase1": sum(1 for r in rows if r.get("ready_for_impl_phase1")),
    }
    return {"profiles": profiles, "rows": rows, "summary": summary, "sources": []}


def build_status_tracker(
    profile_map: Dict[str, Any],
    spec_research: Dict[str, Any],
    logic_analysis: Dict[str, Any],
    structure_analysis: Dict[str, Any],
    implementation_contracts: Dict[str, Any],
    test_targets_phase1: Dict[str, Any],
    review_signoffs: Dict[str, Any],
    readiness_gates: Dict[str, Any],
    qa_meta: Dict[str, Any],
) -> Dict[str, Any]:
    rows = []
    for profile_row in profile_map.get("profiles", []):
        if not isinstance(profile_row, dict):
            continue
        pid = str(profile_row.get("profile_id") or "").upper()
        if pid not in PROFILE_IDS:
            continue
        spec = (spec_research.get("profiles", {}) or {}).get(pid, {})
        logic = logic_analysis.get(pid, {})
        structure = structure_analysis.get(pid, {})
        impl_contract = implementation_contracts.get(pid, {}) if isinstance(implementation_contracts, dict) else {}
        test_targets = test_targets_phase1.get(pid, {}) if isinstance(test_targets_phase1, dict) else {}
        signoff = review_signoffs.get(pid, {}) if isinstance(review_signoffs, dict) else {}
        readiness = (readiness_gates.get("profiles", {}) or {}).get(pid, {})
        row = {
            "profile_id": pid,
            "ui_label": profile_row.get("ui_label") or pid,
            "display_name_he": profile_row.get("display_name_he") or pid,
            "spec_sync_status": spec.get("sync_status") or "unknown",
            "spec_artifacts": (spec.get("summary") or {}).get("artifact_count", 0),
            "logic_doc_status": logic.get("status") or "unknown",
            "logic_findings": len(logic.get("core_findings", []) if isinstance(logic.get("core_findings"), list) else []),
            "logic_source_observations": len(logic.get("source_observations", []) if isinstance(logic.get("source_observations"), list) else []),
            "logic_open_questions": len(logic.get("open_questions", []) if isinstance(logic.get("open_questions"), list) else []),
            "structure_doc_status": structure.get("status") or "unknown",
            "structure_findings": len(structure.get("core_findings", []) if isinstance(structure.get("core_findings"), list) else []),
            "structure_source_observations": len(
                structure.get("source_observations", []) if isinstance(structure.get("source_observations"), list) else []
            ),
            "structure_open_questions": len(structure.get("open_questions", []) if isinstance(structure.get("open_questions"), list) else []),
            "spec_sync_complete": "spec_sync_complete" in (readiness.get("completed_checks") or []),
            "logic_analysis_baselined": "logic_analysis_baselined" in (readiness.get("completed_checks") or []),
            "logic_analysis_reviewed": "logic_analysis_reviewed" in (readiness.get("completed_checks") or []),
            "structure_analysis_baselined": "structure_analysis_baselined" in (readiness.get("completed_checks") or []),
            "structure_analysis_reviewed": "structure_analysis_reviewed" in (readiness.get("completed_checks") or []),
            "phase1_subset_decided": "phase1_subset_decided" in (readiness.get("completed_checks") or []),
            "implementation_contract_defined": "implementation_contract_defined" in (readiness.get("completed_checks") or []),
            "phase1_test_targets_defined": "phase1_test_targets_defined" in (readiness.get("completed_checks") or []),
            "phase1_blockers_closed_or_deferred": "phase1_blockers_closed_or_deferred" in (readiness.get("completed_checks") or []),
            "review_signoff_complete": "review_signoff_complete" in (readiness.get("completed_checks") or []),
            "phase1_decisions_count": len(
                (
                    (logic.get("phase1_decisions") if isinstance(logic.get("phase1_decisions"), list) else [])
                    + (structure.get("phase1_decisions") if isinstance(structure.get("phase1_decisions"), list) else [])
                )
            ),
            "implementation_contract_summary_he": str(impl_contract.get("summary_he") or ""),
            "test_targets_summary_he": str(test_targets.get("summary_he") or ""),
            "review_signoff_summary_he": str(signoff.get("review_summary_he") or ""),
            "ready_for_impl_phase1": bool(readiness.get("ready_for_impl_phase1")),
            "gaps_he": [],
        }
        if (spec.get("summary") or {}).get("artifact_count", 0) == 0:
            row["gaps_he"].append("אין artifacts מסונכרנים ב-docs/Profiles")
        if row["logic_doc_status"] in ("missing", ""):
            row["gaps_he"].append("קובץ Logic חסר")
        if row["structure_doc_status"] in ("missing", ""):
            row["gaps_he"].append("קובץ Structure חסר")
        if row["logic_findings"] == 0:
            row["gaps_he"].append("טרם חולצו ממצאי לוגיקה")
        if row["structure_findings"] == 0:
            row["gaps_he"].append("טרם חולצו ממצאי מבנה")
        if not row["phase1_subset_decided"]:
            row["gaps_he"].append("טרם הוגדרה החלטת Phase 1 subset מפורשת")
        if not row["implementation_contract_defined"]:
            row["gaps_he"].append("טרם הוגדר חוזה מימוש Phase 1 מלא")
        if not row["phase1_test_targets_defined"]:
            row["gaps_he"].append("טרם הוגדרו יעדי בדיקות Phase 1")
        if not row["phase1_blockers_closed_or_deferred"]:
            row["gaps_he"].append("יש blockers של Phase 1 שטרם נסגרו/סומנו כנדחים")
        if not row["review_signoff_complete"]:
            row["gaps_he"].append("טרם הושלמה חתימת review ומוכנות Phase 1")
        if not row["logic_analysis_baselined"]:
            row["gaps_he"].append("לוגיקה טרם עומדת בסף baseline (ממצאים/תצפיות)")
        if not row["structure_analysis_baselined"]:
            row["gaps_he"].append("מבנה טרם עומד בסף baseline (ממצאים/תצפיות)")
        rows.append(row)

    summary = {
        "profiles": len(rows),
        "spec_synced": sum(1 for r in rows if r.get("spec_sync_status") == "synced"),
        "logic_with_findings": sum(1 for r in rows if int(r.get("logic_findings") or 0) > 0),
        "structure_with_findings": sum(1 for r in rows if int(r.get("structure_findings") or 0) > 0),
        "logic_baselined": sum(1 for r in rows if r.get("logic_analysis_baselined")),
        "structure_baselined": sum(1 for r in rows if r.get("structure_analysis_baselined")),
        "phase1_subset_decided": sum(1 for r in rows if r.get("phase1_subset_decided")),
        "implementation_contract_defined": sum(1 for r in rows if r.get("implementation_contract_defined")),
        "phase1_test_targets_defined": sum(1 for r in rows if r.get("phase1_test_targets_defined")),
        "phase1_blockers_closed_or_deferred": sum(1 for r in rows if r.get("phase1_blockers_closed_or_deferred")),
        "review_signoff_complete": sum(1 for r in rows if r.get("review_signoff_complete")),
        "ready_for_impl_phase1": sum(1 for r in rows if r.get("ready_for_impl_phase1")),
        "all_logic_scaffold": all(str(r.get("logic_doc_status")) in ("scaffold", "draft", "scaffold_partial") for r in rows) if rows else True,
        "all_structure_scaffold": all(str(r.get("structure_doc_status")) in ("scaffold", "draft", "scaffold_partial") for r in rows) if rows else True,
        "last_smoke_test_at": qa_meta.get("last_smoke_test_at"),
        "smoke_test_mode": qa_meta.get("smoke_test_mode"),
    }
    return {"rows": rows, "summary": summary, "sources": qa_meta.get("sources", [])}


def _walk_sources(obj: Any) -> Iterator[Tuple[str, Dict[str, Any]]]:
    if isinstance(obj, dict):
        if "file" in obj and isinstance(obj.get("file"), str):
            yield ("file", obj)
        if "url" in obj and isinstance(obj.get("url"), str):
            yield ("url", obj)
        for value in obj.values():
            yield from _walk_sources(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_sources(item)


def build_traceability_index(data: Dict[str, Any]) -> Dict[str, Any]:
    local_counter: Counter[str] = Counter()
    web_counter: Counter[str] = Counter()
    web_meta: Dict[str, Dict[str, Any]] = {}
    for kind, src in _walk_sources(data):
        if kind == "file":
            key = f"{src.get('file')}:{src.get('line')}" if src.get("line") is not None else str(src.get("file"))
            local_counter[key] += 1
        elif kind == "url":
            url = str(src.get("url"))
            web_counter[url] += 1
            if url not in web_meta:
                web_meta[url] = {"url": url, "title": src.get("title"), "retrieved_at": src.get("retrieved_at")}
    local_rows = []
    for key, count in local_counter.most_common(400):
        file_part, line_part = (key.rsplit(":", 1) + [None])[:2] if ":" in key else (key, None)
        line_val = None
        if line_part and line_part.isdigit():
            file_part, line_val = key.rsplit(":", 1)[0], int(line_part)
        else:
            file_part, line_val = key, None
        local_rows.append({"file": file_part, "line": line_val, "count": count})
    web_rows = []
    for url, count in web_counter.most_common():
        meta = web_meta.get(url, {})
        web_rows.append({"url": url, "title": meta.get("title"), "retrieved_at": meta.get("retrieved_at"), "count": count})
    return {
        "summary": {"local_sources": len(local_rows), "web_sources": len(web_rows)},
        "local": local_rows,
        "web": web_rows,
        "sources": [],
    }


def _ui_label(pid: str) -> str:
    return "ScPS" if str(pid).upper() == "SCPS" else str(pid).upper()


def _safe_slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", str(text or "").strip().lower())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "item"


def _first_web_source(items: Any) -> Optional[Dict[str, Any]]:
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict) and item.get("url"):
            return item
    return None


def _first_local_source(items: Any) -> Optional[Dict[str, Any]]:
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict) and item.get("file"):
            return item
    return None


def _kind_display_he(kind: str, is_dir: bool) -> str:
    k = str(kind or "")
    if k == "spec_pdf":
        return "מסמך Spec (PDF)"
    if k == "ics_pdf":
        return "מסמך ICS / Conformance Statement"
    if k == "ixit_pdf":
        return "מסמך IXIT / Extra Information"
    if k == "ts_pdf":
        return "מסמך Test Suite (TS)"
    if k == "tcrl_folder":
        return "תיקיית TCRL"
    if k == "ixit_folder":
        return "תיקיית IXIT"
    if k == "tcrl_xlsx":
        return "קובץ TCRL (Excel)"
    if k == "changes_pdf":
        return "מסמך Changes/Release Notes"
    if k == "errata_pdf":
        return "מסמך Errata"
    if is_dir:
        return "תיקייה"
    return "קובץ"


def _describe_spec_artifact_for_user(artifact: Dict[str, Any]) -> Dict[str, str]:
    kind = str(artifact.get("kind") or "")
    is_dir = bool(artifact.get("is_dir"))
    name = str(artifact.get("name") or "")
    display_kind_he = _kind_display_he(kind, is_dir)
    if kind == "spec_pdf":
        return {
            "display_kind_he": display_kind_he,
            "what_it_is_he": "קובץ PDF של המפרט הרשמי של הפרופיל.",
            "what_we_take_from_it_he": "הגדרת ההתנהגות הפונקציונלית של הפרופיל, דרישות עיקריות, ומונחי היסוד למימוש.",
            "relevance_he": "גבוה",
        }
    if kind == "ics_pdf":
        return {
            "display_kind_he": display_kind_he,
            "what_it_is_he": "מסמך הצהרת יכולות/תאימות (ICS).",
            "what_we_take_from_it_he": "עוזר להבין אילו יכולות ממומשות ואיך למפות את subset של Phase 1.",
            "relevance_he": "גבוה",
        }
    if kind == "ixit_pdf" or kind == "ixit_folder":
        return {
            "display_kind_he": display_kind_he,
            "what_it_is_he": "מסמך/תיקייה עם פרטי IXIT/Extra Information עבור בדיקות.",
            "what_we_take_from_it_he": "הנחות וקונפיגורציות בדיקה שמסייעות להכנת יעדי PTS/AutoPTS בהמשך.",
            "relevance_he": "בינוני",
        }
    if kind == "ts_pdf":
        return {
            "display_kind_he": display_kind_he,
            "what_it_is_he": "מסמך Test Suite רשמי.",
            "what_we_take_from_it_he": "תמונה של תחומי בדיקה וזרימות בדיקה אפשריות שצריך לכסות במימוש.",
            "relevance_he": "גבוה",
        }
    if kind == "tcrl_folder":
        return {
            "display_kind_he": display_kind_he,
            "what_it_is_he": "תיקייה של TCRL (Test Case Reference List) עם קבצי Excel.",
            "what_we_take_from_it_he": "מיפוי טסטים ו-reference ליכולות/סעיפים רלוונטיים לצורך תכנון בדיקות ומוכנות למימוש.",
            "relevance_he": "גבוה",
        }
    if kind == "tcrl_xlsx":
        return {
            "display_kind_he": display_kind_he,
            "what_it_is_he": "קובץ Excel מתוך TCRL.",
            "what_we_take_from_it_he": "רשימות test cases והתאמות שנשתמש בהן למיפוי יעדי בדיקות ו־Phase 1.",
            "relevance_he": "גבוה",
        }
    if kind == "changes_pdf":
        return {
            "display_kind_he": display_kind_he,
            "what_it_is_he": "מסמך שינויים בין גרסאות.",
            "what_we_take_from_it_he": "עוזר להבין האם יש דגשים/שינויים שמשפיעים על המימוש או על הבדיקות.",
            "relevance_he": "בינוני",
        }
    if kind == "errata_pdf":
        return {
            "display_kind_he": display_kind_he,
            "what_it_is_he": "מסמך errata/תיקוני מפרט.",
            "what_we_take_from_it_he": "חריגים/תיקונים שיכולים להשפיע על פרשנות דרישות או בדיקות.",
            "relevance_he": "בינוני",
        }
    if is_dir:
        return {
            "display_kind_he": display_kind_he,
            "what_it_is_he": f"תיקייה מסונכרנת של קבצי עזר ({name}).",
            "what_we_take_from_it_he": "משמשת כמקור ארטיפקטים למחקר/בדיקות לפי תוכן הקבצים שבתוכה.",
            "relevance_he": "בינוני",
        }
    return {
        "display_kind_he": display_kind_he,
        "what_it_is_he": "קובץ מסונכרן מתוך מקור רשמי.",
        "what_we_take_from_it_he": "נבדק לפי הצורך כדי לחלץ מידע רלוונטי למימוש/בדיקות.",
        "relevance_he": "נמוך",
    }


def build_specs_presentation(profile_map: Dict[str, Any], spec_research: Dict[str, Any]) -> Dict[str, Any]:
    out_profiles: Dict[str, Any] = {}
    rows: List[Dict[str, Any]] = []
    research_profiles = (spec_research.get("profiles") or {}) if isinstance(spec_research, dict) else {}
    for p_row in profile_map.get("profiles", []) if isinstance(profile_map.get("profiles"), list) else []:
        if not isinstance(p_row, dict):
            continue
        pid = str(p_row.get("profile_id") or "").upper()
        if pid not in PROFILE_IDS:
            continue
        spec = research_profiles.get(pid, {}) if isinstance(research_profiles, dict) else {}
        artifacts = spec.get("artifacts", []) if isinstance(spec.get("artifacts"), list) else []
        group_source = {
            "group_id": f"{pid.lower()}_sig_sync",
            "source_label_he": "Bluetooth SIG (סנכרון מקומי)",
            "source_url": spec.get("spec_page_url"),
            "source_kind": "sig",
            "summary_he": (
                "קבוצת הקבצים הרשמית שסונכרנה מדף ה-spec של Bluetooth SIG ומשמשת מקור למחקר, מיפוי בדיקות ותיחום Phase 1."
                if artifacts
                else "לא נמצאו עדיין קבצים מסונכרנים עבור מקור זה."
            ),
            "files": [],
            "sources": spec.get("sources", []),
        }
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            desc = _describe_spec_artifact_for_user(artifact)
            group_source["files"].append(
                {
                    "path": artifact.get("path"),
                    "name": artifact.get("name"),
                    "is_dir": bool(artifact.get("is_dir")),
                    "display_kind_he": desc["display_kind_he"],
                    "what_it_is_he": desc["what_it_is_he"],
                    "what_we_take_from_it_he": desc["what_we_take_from_it_he"],
                    "relevance_he": desc.get("relevance_he"),
                    "sources": artifact.get("sources", []),
                }
            )

        profile_vm = {
            "profile_id": pid,
            "ui_label": p_row.get("ui_label") or _ui_label(pid),
            "display_name_he": p_row.get("display_name_he") or _ui_label(pid),
            "sync_status": spec.get("sync_status") or "missing",
            "spec_page_url": spec.get("spec_page_url"),
            "groups": [group_source],
            "sources": spec.get("sources", []),
        }
        out_profiles[pid] = profile_vm
        rows.append(profile_vm)

    return {"profiles": out_profiles, "rows": rows, "sources": spec_research.get("sources", []) if isinstance(spec_research, dict) else []}


def _source_entry_label(source_id: str, source_catalog: Dict[str, Dict[str, Any]]) -> str:
    entry = source_catalog.get(source_id, {}) if isinstance(source_catalog, dict) else {}
    if isinstance(entry, dict):
        title = str(entry.get("title") or "").strip()
        if title:
            return title
    return source_id


def _source_entry_type(source_id: str, source_catalog: Dict[str, Dict[str, Any]]) -> str:
    entry = source_catalog.get(source_id, {}) if isinstance(source_catalog, dict) else {}
    if not isinstance(entry, dict):
        return "unknown"
    if entry.get("vendor"):
        return f"vendor:{entry.get('vendor')}"
    if entry.get("category"):
        return f"official:{entry.get('category')}"
    return "catalog"


def _contribution_label_from_count(count: int) -> str:
    if count <= 0:
        return "לא תרם מידע בפועל"
    if count == 1:
        return "מעט"
    if count <= 3:
        return "בינוני"
    return "הרבה"


def _logic_behaviors_from_analysis(analysis: Dict[str, Any], contract: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for f in analysis.get("core_findings", []) if isinstance(analysis.get("core_findings"), list) else []:
        stmt = str(f.get("statement_he") or "").strip()
        if stmt:
            out.append(stmt)
    for x in analysis.get("implementation_implications", []) if isinstance(analysis.get("implementation_implications"), list) else []:
        sx = str(x).strip()
        if sx:
            out.append(sx)
    rfc = (contract.get("runtime_flow_contract") or {}) if isinstance(contract, dict) else {}
    for step in rfc.get("steps_he", []) if isinstance(rfc.get("steps_he"), list) else []:
        out.append(f"שלב Runtime: {step}")
    dedup = []
    seen = set()
    for item in out:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        dedup.append(key)
    return dedup[:8]


def _group_source_observations_for_presentation(
    observations: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
    source_catalog: Dict[str, Dict[str, Any]],
    kind: str,
) -> List[Dict[str, Any]]:
    by_source: Dict[str, Dict[str, Any]] = {}
    for obs in observations:
        if not isinstance(obs, dict):
            continue
        sid = str(obs.get("source_id") or "").strip()
        if not sid:
            continue
        row = by_source.setdefault(
            sid,
            {
                "source_id": sid,
                "source_label_he": _source_entry_label(sid, source_catalog),
                "source_type": _source_entry_type(sid, source_catalog),
                "relevance": "none",
                "what_was_checked_he": [],
                "what_was_found_he": [],
                "what_we_learned_he": [],
                "_confidence_scores": [],
                "sources": _merge_source_lists(obs.get("sources", []), (source_catalog.get(sid) or {}).get("sources", [])),
            },
        )
        how = str(obs.get("how_identified_he") or "").strip()
        what = str(obs.get("what_identified_he") or "").strip()
        if how:
            row["what_was_checked_he"].append(how)
        if what:
            row["what_was_found_he"].append(what)
        row["_confidence_scores"].append(str(obs.get("confidence") or "").lower())

    for f in findings:
        if not isinstance(f, dict):
            continue
        learned = str(f.get("statement_he") or "").strip()
        if not learned:
            continue
        for sid in f.get("source_ids", []) if isinstance(f.get("source_ids"), list) else []:
            sid_s = str(sid).strip()
            if not sid_s:
                continue
            row = by_source.setdefault(
                sid_s,
                {
                    "source_id": sid_s,
                    "source_label_he": _source_entry_label(sid_s, source_catalog),
                    "source_type": _source_entry_type(sid_s, source_catalog),
                    "relevance": "none",
                    "what_was_checked_he": [],
                    "what_was_found_he": [],
                    "what_we_learned_he": [],
                    "_confidence_scores": [],
                    "sources": _merge_source_lists(f.get("sources", []), (source_catalog.get(sid_s) or {}).get("sources", [])),
                },
            )
            row["what_we_learned_he"].append(learned)

    rows: List[Dict[str, Any]] = []
    for sid, row in by_source.items():
        checked = list(dict.fromkeys([x for x in row.pop("what_was_checked_he", []) if x]))
        found = list(dict.fromkeys([x for x in row.pop("what_was_found_he", []) if x]))
        learned = list(dict.fromkeys([x for x in row.pop("what_we_learned_he", []) if x]))
        confs = [c for c in row.pop("_confidence_scores", []) if c]
        conf_counter = Counter(confs)
        if found or learned:
            if conf_counter.get("high", 0) >= 2 or len(found) + len(learned) >= 4:
                relevance = "high"
            elif conf_counter.get("medium", 0) or len(found) + len(learned) >= 2:
                relevance = "medium"
            else:
                relevance = "low"
        else:
            relevance = "none"
        contrib = _contribution_label_from_count(len(found) + len(learned))
        rows.append(
            {
                **row,
                "relevance": relevance,
                "contribution_level_he": contrib,
                "what_was_checked_he": " | ".join(checked[:3]) if checked else "לא תועד חילוץ מפורש.",
                "what_was_found_he": " | ".join(found[:3]) if found else "לא נמצא מידע רלוונטי מתועד.",
                f"what_we_learned_for_{kind}_he": " | ".join(learned[:3]) if learned else "לא נגזרה מסקנה ישירה לשלב זה.",
                "sources": row.get("sources", []),
            }
        )
    rows.sort(key=lambda r: ({"high": 0, "medium": 1, "low": 2, "none": 3}.get(str(r.get("relevance")), 4), str(r.get("source_id"))))
    return rows


def build_logic_presentation(
    profile_map: Dict[str, Any],
    logic_analysis: Dict[str, Any],
    implementation_contracts: Dict[str, Any],
    source_catalog: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    profiles: Dict[str, Any] = {}
    rows: List[Dict[str, Any]] = []
    for p_row in profile_map.get("profiles", []) if isinstance(profile_map.get("profiles"), list) else []:
        if not isinstance(p_row, dict):
            continue
        pid = str(p_row.get("profile_id") or "").upper()
        if pid not in PROFILE_IDS:
            continue
        analysis = logic_analysis.get(pid, {}) if isinstance(logic_analysis, dict) else {}
        contract = implementation_contracts.get(pid, {}) if isinstance(implementation_contracts, dict) else {}
        findings = analysis.get("core_findings", []) if isinstance(analysis.get("core_findings"), list) else []
        observations = analysis.get("source_observations", []) if isinstance(analysis.get("source_observations"), list) else []
        researched_sources = _group_source_observations_for_presentation(observations, findings, source_catalog, "logic")
        vm = {
            "profile_id": pid,
            "ui_label": p_row.get("ui_label") or _ui_label(pid),
            "display_name_he": p_row.get("display_name_he") or _ui_label(pid),
            "researched_sources": researched_sources,
            "logic_summary": {
                "summary_he": str(analysis.get("summary_he") or ""),
                "behaviors_required_he": _logic_behaviors_from_analysis(analysis, contract),
                "important_conditions_he": [
                    str(q.get("detail_he"))
                    for q in (analysis.get("open_questions", []) if isinstance(analysis.get("open_questions"), list) else [])
                    if isinstance(q, dict) and str(q.get("status") or "").lower() != "resolved"
                ][:5],
                "phase1_focus_he": [str(x) for x in (contract.get("scope_in") if isinstance(contract.get("scope_in"), list) else [])][:6],
                "sources": _merge_source_lists(analysis.get("sources", []), contract.get("sources", [])),
            },
            "sources": _merge_source_lists(analysis.get("sources", []), contract.get("sources", [])),
        }
        profiles[pid] = vm
        rows.append(vm)
    return {"profiles": profiles, "rows": rows, "sources": []}


def _structure_complexity(
    pid: str,
    structure_analysis: Dict[str, Any],
    contract: Dict[str, Any],
) -> Dict[str, Any]:
    modules = ((contract.get("module_boundaries") or {}).get("modules_he") or []) if isinstance(contract, dict) else []
    boundaries = ((contract.get("module_boundaries") or {}).get("boundaries_he") or []) if isinstance(contract, dict) else []
    data_items = ((contract.get("data_model_contract") or {}).get("items_he") or []) if isinstance(contract, dict) else []
    findings = structure_analysis.get("core_findings", []) if isinstance(structure_analysis.get("core_findings"), list) else []
    text_blob = " ".join(
        [str(f.get("statement_he") or "") for f in findings if isinstance(f, dict)]
        + [str(x) for x in modules]
        + [str(x) for x in boundaries]
    ).lower()
    score = 0
    if len(modules) >= 3:
        score += 1
    if len(data_items) >= 3:
        score += 1
    if any(tok in text_blob for tok in ("callback", "ccc", "state", "subscription", "policy")):
        score += 1
    if len(findings) >= 5:
        score += 1
    classification = "complex" if score >= 3 else "simple"
    reason = (
        "פרופיל מורכב: דורש פיצול למודולים, callbacks/state management, וזרימות GATT/Policy נפרדות."
        if classification == "complex"
        else "פרופיל פשוט יחסית: ניתן לממש סביב service + מספר מצומצם של מסלולים/characteristics."
    )
    return {"classification": classification, "classification_reason_he": reason, "sources": _merge_source_lists(structure_analysis.get("sources", []), contract.get("sources", []))}


def _derive_similar_profiles(structure_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    text_blob = " ".join(
        [
            str(f.get("statement_he") or "")
            for f in (structure_analysis.get("core_findings", []) if isinstance(structure_analysis.get("core_findings"), list) else [])
            if isinstance(f, dict)
        ]
        + [
            str(o.get("what_identified_he") or "")
            for o in (structure_analysis.get("source_observations", []) if isinstance(structure_analysis.get("source_observations"), list) else [])
            if isinstance(o, dict)
        ]
    ).upper()
    candidates = []
    for token, name_he, why, learn in [
        ("HRS", "HRS (Heart Rate Service)", "יש דמיון בדפוסי שירות BLE עם CCC ונתיב publish ציבורי.", "אפשר ללמוד דפוס service API + CCC callback + notify path ב-Zephyr."),
        ("BAS", "BAS (Battery Service)", "יש דמיון בדפוס service BLE פשוט/בינוני עם API ציבורי ו-GATT plumbing self-contained.", "אפשר ללמוד חלוקת אחריות של service module ב-Zephyr."),
        ("CGMS", "CGMS (Continuous Glucose Monitoring)", "מופיע כמקור דפוס health-service עם flow לוגי עשיר יותר.", "אפשר ללמוד callback/session/runtime flow בצד האפליקציה."),
    ]:
        if token in text_blob:
            candidates.append(
                {
                    "profile_name": name_he,
                    "why_similar_he": why,
                    "what_can_be_learned_he": learn,
                    "source_origin": "derived_from_findings",
                    "sources": structure_analysis.get("sources", []),
                }
            )
    return candidates[:4]


def _build_file_plan_and_blueprints(pid: str, contract: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    modules = ((contract.get("module_boundaries") or {}).get("modules_he") or []) if isinstance(contract, dict) else []
    boundaries = ((contract.get("module_boundaries") or {}).get("boundaries_he") or []) if isinstance(contract, dict) else []
    runtime_steps = ((contract.get("runtime_flow_contract") or {}).get("steps_he") or []) if isinstance(contract, dict) else []
    service_funcs = ((contract.get("service_api_contract") or {}).get("public_functions_he") or []) if isinstance(contract, dict) else []
    ccc_rules = ((contract.get("ccc_and_notify_indicate_contract") or {}).get("rules_he") or []) if isinstance(contract, dict) else []
    data_items = ((contract.get("data_model_contract") or {}).get("items_he") or []) if isinstance(contract, dict) else []
    error_rules = ((contract.get("error_policy_contract") or {}).get("rules_he") or []) if isinstance(contract, dict) else []
    deps = ((contract.get("dependency_contract") or {}).get("items_he") or []) if isinstance(contract, dict) else []

    file_plan: List[Dict[str, Any]] = []
    blueprints: List[Dict[str, Any]] = []
    pid_l = str(pid).lower()
    for idx, module in enumerate(modules if modules else [f"{pid_l}_service"], start=1):
        mod = str(module).strip()
        base = mod
        if base.endswith(".c") or base.endswith(".h"):
            base = base.rsplit(".", 1)[0]
        c_path = f"zephyr/subsys/bluetooth/services/{base}.c" if "service" in base else f"zephyr/subsys/bluetooth/services/{base}.c"
        h_path = f"zephyr/include/zephyr/bluetooth/services/{base}.h"
        purpose = "מודול שירות GATT (plumbing / attributes / CCC)" if "service" in base else ("שכבת לוגיקה/policy של הפרופיל" if "logic" in base or "policy" in base else "שכבת adapter/app integration של הפרופיל")
        file_plan.append(
            {
                "path": c_path,
                "filename": Path(c_path).name,
                "purpose_he": purpose,
                "created_in_phase": "phase1",
                "depends_on": [h_path] if "service" in base else [],
            }
        )
        file_plan.append(
            {
                "path": h_path,
                "filename": Path(h_path).name,
                "purpose_he": f"הצהרות/חוזה ציבורי עבור {base}",
                "created_in_phase": "phase1",
                "depends_on": [],
            }
        )
        responsibilities = []
        if "service" in base:
            responsibilities.extend(service_funcs[:4])
            responsibilities.extend(ccc_rules[:3])
        elif "logic" in base or "policy" in base:
            responsibilities.extend(runtime_steps[:4])
            responsibilities.extend(data_items[:3])
        else:
            responsibilities.extend(boundaries[:3])
            responsibilities.extend(deps[:3])
        blueprints.append(
            {
                "file_key": c_path,
                "internal_sections_he": [
                    "Includes / UUIDs / constants",
                    "State / static data",
                    "Public API",
                    "Callbacks / handlers",
                    "Helpers פנימיים",
                ],
                "functions_he": [str(x) for x in responsibilities[:6]],
                "responsibilities_he": [str(x) for x in responsibilities[:6]] or [purpose],
                "notes_he": [str(x) for x in error_rules[:2]],
            }
        )
        blueprints.append(
            {
                "file_key": h_path,
                "internal_sections_he": [
                    "Public types",
                    "Callback typedefs",
                    "Public API declarations",
                ],
                "functions_he": [str(x) for x in service_funcs[:4]],
                "responsibilities_he": [f"חוזה ציבורי עבור {base}"],
                "notes_he": [],
            }
        )

    return file_plan, blueprints


def build_structure_presentation(
    profile_map: Dict[str, Any],
    structure_analysis: Dict[str, Any],
    implementation_contracts: Dict[str, Any],
    source_catalog: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    profiles: Dict[str, Any] = {}
    rows: List[Dict[str, Any]] = []
    for p_row in profile_map.get("profiles", []) if isinstance(profile_map.get("profiles"), list) else []:
        if not isinstance(p_row, dict):
            continue
        pid = str(p_row.get("profile_id") or "").upper()
        if pid not in PROFILE_IDS:
            continue
        analysis = structure_analysis.get(pid, {}) if isinstance(structure_analysis, dict) else {}
        contract = implementation_contracts.get(pid, {}) if isinstance(implementation_contracts, dict) else {}
        findings = analysis.get("core_findings", []) if isinstance(analysis.get("core_findings"), list) else []
        observations = analysis.get("source_observations", []) if isinstance(analysis.get("source_observations"), list) else []
        researched_sources = _group_source_observations_for_presentation(observations, findings, source_catalog, "structure")
        file_plan, blueprints = _build_file_plan_and_blueprints(pid, contract)
        vm = {
            "profile_id": pid,
            "ui_label": p_row.get("ui_label") or _ui_label(pid),
            "display_name_he": p_row.get("display_name_he") or _ui_label(pid),
            "researched_sources": researched_sources,
            "profile_complexity": _structure_complexity(pid, analysis, contract),
            "similar_profiles": _derive_similar_profiles(analysis),
            "structure_summary": {
                "summary_he": str(analysis.get("summary_he") or ""),
                "base_profile_structure_ref": {
                    "status": "placeholder",
                    "label_he": "מבנה בסיסי לכל פרופיל (placeholder עתידי)",
                    "detail_he": "כרגע משתמשים ב-fallback המבוסס על findings + implementation contract עד שהמקור הבסיסי יוזן.",
                    "sources": [],
                },
                "file_plan": file_plan,
                "file_internal_blueprints": blueprints,
                "sources": _merge_source_lists(analysis.get("sources", []), contract.get("sources", [])),
            },
            "sources": _merge_source_lists(analysis.get("sources", []), contract.get("sources", [])),
        }
        profiles[pid] = vm
        rows.append(vm)
    return {"profiles": profiles, "rows": rows, "sources": []}


def _build_task_templates_for_profile(
    pid: str,
    p_row: Dict[str, Any],
    status_row: Dict[str, Any],
    impl_contract: Dict[str, Any],
    test_targets: Dict[str, Any],
    logic_p: Dict[str, Any],
    structure_p: Dict[str, Any],
    readiness: Dict[str, Any],
    phase1_decisions: Dict[str, Any],
) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []

    def add_task(
        task_id: str,
        title_he: str,
        description_he: str,
        category: str,
        suggested_priority: str = "medium",
        derived_from: str = "manual",
        source_refs: Optional[List[Dict[str, Any]]] = None,
        default_assignee: str = "",
        default_status: str = "todo",
        is_completed_seed: bool = False,
        parent_task_id: Optional[str] = None,
    ) -> None:
        tasks.append(
            {
                "task_id": task_id,
                "parent_task_id": parent_task_id,
                "title_he": title_he,
                "description_he": description_he,
                "category": category,
                "suggested_priority": suggested_priority,
                "derived_from": derived_from,
                "source_refs": source_refs or [],
                "default_assignee": default_assignee,
                "default_status": default_status,
                "is_completed_seed": bool(is_completed_seed),
            }
        )

    # Completed prep tasks (Codex)
    completed_map = [
        ("prep_spec_sync", "סנכרון מפרטים רשמיים", "בוצע סנכרון וקיטלוג ארטיפקטים רשמיים לפרופיל.", "docs", bool(status_row.get("spec_sync_complete"))),
        ("prep_logic_review", "Review לוגיקה", "בוצע review לוגיקה והוגדרה חתימת מוכנות ברמת לוגיקה.", "logic", bool(status_row.get("logic_analysis_reviewed"))),
        ("prep_structure_review", "Review מבנה", "בוצע review מבנה והוגדרה חתימת מוכנות ברמת מבנה.", "structure", bool(status_row.get("structure_analysis_reviewed"))),
        ("prep_impl_contract", "הגדרת חוזה מימוש Phase 1", "הוגדר Implementation Contract מלא עבור הפרופיל.", "structure", bool(status_row.get("implementation_contract_defined"))),
        ("prep_test_targets", "הגדרת יעדי בדיקות Phase 1", "הוגדרו יעדי בדיקות ידניות + PTS/AutoPTS ל-Phase 1.", "tests", bool(status_row.get("phase1_test_targets_defined"))),
        ("prep_signoff", "חתימת מוכנות Phase 1", "בוצעה חתימת review סופית ונקבע ready_for_impl_phase1.", "docs", bool(status_row.get("review_signoff_complete"))),
    ]
    for tid, title, desc, cat, done in completed_map:
        add_task(
            f"{pid.lower()}_{tid}",
            title,
            desc,
            cat,
            suggested_priority="high",
            derived_from="codex_completed",
            source_refs=_merge_source_lists(impl_contract.get("sources", []), test_targets.get("sources", []), readiness.get("sources", [])),
            default_assignee="codex" if done else "",
            default_status="done" if done else "todo",
            is_completed_seed=done,
        )

    # Implementation tasks derived from contract order
    parent_impl_id = f"{pid.lower()}_impl_phase1"
    add_task(
        parent_impl_id,
        f"מימוש Phase 1 — {_ui_label(pid)}",
        "משימת אב שמרכזת את משימות המימוש בפועל לפי חוזה המימוש שנקבע.",
        "integration",
        suggested_priority="high",
        derived_from="contract",
        source_refs=impl_contract.get("sources", []),
    )
    for idx, step in enumerate(impl_contract.get("implementation_order", []) if isinstance(impl_contract.get("implementation_order"), list) else [], start=1):
        step_text = str(step).strip()
        if not step_text:
            continue
        add_task(
            f"{pid.lower()}_impl_step_{idx:02d}_{_safe_slug(step_text)[:32]}",
            step_text,
            "נגזר מחוזה המימוש (implementation_order).",
            "integration" if idx == 1 else "logic",
            suggested_priority="high" if idx <= 2 else "medium",
            derived_from="contract",
            source_refs=impl_contract.get("sources", []),
            parent_task_id=parent_impl_id,
        )

    # File plan tasks
    structure_summary = structure_p.get("structure_summary", {}) if isinstance(structure_p, dict) else {}
    for file_row in structure_summary.get("file_plan", []) if isinstance(structure_summary.get("file_plan"), list) else []:
        if not isinstance(file_row, dict):
            continue
        fpath = str(file_row.get("path") or "")
        title = f"לממש קובץ: {Path(fpath).name}" if fpath else "לממש קובץ"
        desc = f"{file_row.get('purpose_he') or 'מימוש קובץ לפי המבנה שנקבע.'}"
        add_task(
            f"{pid.lower()}_file_{_safe_slug(fpath)[:36]}",
            title,
            desc,
            "structure",
            suggested_priority="high" if str(file_row.get("created_in_phase") or "") == "phase1" else "low",
            derived_from="structure",
            source_refs=structure_summary.get("sources", []),
            parent_task_id=parent_impl_id,
        )

    # Logic-derived follow-ups
    logic_summary = logic_p.get("logic_summary", {}) if isinstance(logic_p, dict) else {}
    parent_logic_id = f"{pid.lower()}_logic_followups"
    add_task(
        parent_logic_id,
        "מימוש התנהגות/לוגיקה לפי הסיכום",
        "פירוק סעיפי הלוגיקה שנמצאו במשימות מימוש/בדיקה.",
        "logic",
        suggested_priority="high",
        derived_from="logic",
        source_refs=logic_summary.get("sources", []),
    )
    for idx, item in enumerate(logic_summary.get("behaviors_required_he", []) if isinstance(logic_summary.get("behaviors_required_he"), list) else [], start=1):
        txt = str(item).strip()
        if not txt:
            continue
        add_task(
            f"{pid.lower()}_logic_behavior_{idx:02d}_{_safe_slug(txt)[:24]}",
            f"להטמיע לוגיקה: {txt[:90]}",
            "נגזר מסיכום הלוגיקה של הפרופיל.",
            "logic",
            suggested_priority="medium",
            derived_from="logic",
            source_refs=logic_summary.get("sources", []),
            parent_task_id=parent_logic_id,
        )

    # Test targets tasks
    parent_tests_id = f"{pid.lower()}_phase1_tests"
    add_task(
        parent_tests_id,
        "בדיקות Phase 1",
        "משימות בדיקה ידניות ויעדי PTS/AutoPTS ל-Phase 1.",
        "tests",
        suggested_priority="high",
        derived_from="test_targets",
        source_refs=test_targets.get("sources", []),
    )
    for idx, item in enumerate(test_targets.get("manual_smoke_checks", []) if isinstance(test_targets.get("manual_smoke_checks"), list) else [], start=1):
        txt = str(item).strip()
        if txt:
            add_task(
                f"{pid.lower()}_manual_smoke_{idx:02d}_{_safe_slug(txt)[:24]}",
                txt,
                "בדיקת smoke ידנית שנקבעה ביעדי Phase 1.",
                "tests",
                suggested_priority="high",
                derived_from="test_targets",
                source_refs=test_targets.get("sources", []),
                parent_task_id=parent_tests_id,
            )
    for idx, item in enumerate(test_targets.get("pts_autopts_target_areas", []) if isinstance(test_targets.get("pts_autopts_target_areas"), list) else [], start=1):
        txt = str(item).strip()
        if txt:
            add_task(
                f"{pid.lower()}_pts_target_{idx:02d}_{_safe_slug(txt)[:24]}",
                f"יעד PTS/AutoPTS: {txt}",
                "מיפוי והרצת בדיקות לפי תחום יעד שהוגדר ל-Phase 1.",
                "tests",
                suggested_priority="medium",
                derived_from="test_targets",
                source_refs=test_targets.get("sources", []),
                parent_task_id=parent_tests_id,
            )

    # Decisions and blockers
    decisions_rows = (phase1_decisions.get("rows") or []) if isinstance(phase1_decisions, dict) else []
    for idx, dec in enumerate(decisions_rows, start=1):
        if not isinstance(dec, dict):
            continue
        title = str(dec.get("title_he") or f"החלטת Phase 1 {idx}")
        add_task(
            f"{pid.lower()}_decision_followup_{idx:02d}_{_safe_slug(title)[:24]}",
            f"לוודא יישום החלטה: {title}",
            str(dec.get("decision_he") or "משימת follow-up להחלטת Phase 1."),
            "docs",
            suggested_priority="medium",
            derived_from="readiness",
            source_refs=dec.get("sources", []),
        )

    return tasks


def _current_work_summary(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    def _status_of(t: Dict[str, Any]) -> str:
        return str(t.get("default_status") or "todo")
    statuses = Counter(_status_of(t) for t in tasks if isinstance(t, dict))
    priorities = Counter(str((t.get("suggested_priority") or "medium")) for t in tasks if isinstance(t, dict))
    return {
        "total": len(tasks),
        "done": statuses.get("done", 0),
        "in_progress": statuses.get("in_progress", 0),
        "blocked": statuses.get("blocked", 0),
        "by_priority": dict(priorities),
    }


def build_current_work_templates(
    profile_map: Dict[str, Any],
    status_tracker: Dict[str, Any],
    implementation_contracts: Dict[str, Any],
    test_targets_phase1: Dict[str, Any],
    logic_presentation: Dict[str, Any],
    structure_presentation: Dict[str, Any],
    readiness_gates: Dict[str, Any],
    phase1_decisions: Dict[str, Any],
) -> Dict[str, Any]:
    profiles: Dict[str, Any] = {}
    status_rows_by_id = {
        str(r.get("profile_id") or "").upper(): r
        for r in (status_tracker.get("rows", []) if isinstance(status_tracker.get("rows"), list) else [])
        if isinstance(r, dict)
    }
    readiness_by_id = (readiness_gates.get("profiles") or {}) if isinstance(readiness_gates, dict) else {}
    for p_row in profile_map.get("profiles", []) if isinstance(profile_map.get("profiles"), list) else []:
        if not isinstance(p_row, dict):
            continue
        pid = str(p_row.get("profile_id") or "").upper()
        if pid not in PROFILE_IDS:
            continue
        status_row = status_rows_by_id.get(pid, {})
        impl_contract = (implementation_contracts.get(pid) or {}) if isinstance(implementation_contracts, dict) else {}
        test_targets = (test_targets_phase1.get(pid) or {}) if isinstance(test_targets_phase1, dict) else {}
        logic_p = ((logic_presentation.get("profiles") or {}).get(pid) or {}) if isinstance(logic_presentation, dict) else {}
        structure_p = ((structure_presentation.get("profiles") or {}).get(pid) or {}) if isinstance(structure_presentation, dict) else {}
        readiness = (readiness_by_id.get(pid) or {}) if isinstance(readiness_by_id, dict) else {}
        decisions = ((phase1_decisions.get(pid) or {})) if isinstance(phase1_decisions, dict) else {}
        templates = _build_task_templates_for_profile(pid, p_row, status_row, impl_contract, test_targets, logic_p, structure_p, readiness, decisions)
        profiles[pid] = {
            "profile_id": pid,
            "ui_label": p_row.get("ui_label") or _ui_label(pid),
            "display_name_he": p_row.get("display_name_he") or _ui_label(pid),
            "task_templates": templates,
            "task_state": {"version": 1, "tasks": {}},
            "tasks_merged": templates,
            "summary": _current_work_summary(templates),
            "sources": _merge_source_lists(
                impl_contract.get("sources", []),
                test_targets.get("sources", []),
                logic_p.get("sources", []),
                structure_p.get("sources", []),
                readiness.get("sources", []),
                decisions.get("sources", []),
            ),
        }
    return {
        "profiles": profiles,
        "rows": list(profiles.values()),
        "summary": {"profiles": len(profiles)},
        "sources": [],
    }


def build_knowledge_center(
    profile_map: Dict[str, Any],
    spec_research: Dict[str, Any],
    logic_analysis: Dict[str, Any],
    structure_analysis: Dict[str, Any],
    status_tracker: Dict[str, Any],
    readiness_gates: Dict[str, Any],
    qa_meta: Dict[str, Any],
    autopts_summary: Dict[str, Any],
) -> Dict[str, Any]:
    profile_rows = profile_map.get("profiles", []) if isinstance(profile_map.get("profiles"), list) else []
    deep_profile_entries = []
    spec_meta_entries = []
    readiness_entries = []
    raw_entries = []
    for p in profile_rows:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("profile_id") or "").upper()
        if pid not in PROFILE_IDS:
            continue
        spec = ((spec_research.get("profiles") or {}).get(pid) or {}) if isinstance(spec_research, dict) else {}
        logic = (logic_analysis.get(pid) or {}) if isinstance(logic_analysis, dict) else {}
        struct = (structure_analysis.get(pid) or {}) if isinstance(structure_analysis, dict) else {}
        status_row = next((r for r in (status_tracker.get("rows") or []) if isinstance(r, dict) and r.get("profile_id") == pid), {})
        gate = ((readiness_gates.get("profiles") or {}).get(pid) or {}) if isinstance(readiness_gates, dict) else {}
        deep_profile_entries.append(
            {
                "profile_id": pid,
                "ui_label": p.get("ui_label") or _ui_label(pid),
                "label_he": "Deep Logic/Structure",
                "logic": {
                    "findings": len(logic.get("core_findings", []) if isinstance(logic.get("core_findings"), list) else []),
                    "source_observations": len(logic.get("source_observations", []) if isinstance(logic.get("source_observations"), list) else []),
                    "open_questions": len(logic.get("open_questions", []) if isinstance(logic.get("open_questions"), list) else []),
                    "status": logic.get("status"),
                },
                "structure": {
                    "findings": len(struct.get("core_findings", []) if isinstance(struct.get("core_findings"), list) else []),
                    "source_observations": len(struct.get("source_observations", []) if isinstance(struct.get("source_observations"), list) else []),
                    "open_questions": len(struct.get("open_questions", []) if isinstance(struct.get("open_questions"), list) else []),
                    "status": struct.get("status"),
                },
                "sources": _merge_source_lists(logic.get("sources", []), struct.get("sources", [])),
            }
        )
        spec_summary = spec.get("summary", {}) if isinstance(spec.get("summary"), dict) else {}
        spec_meta_entries.append(
            {
                "profile_id": pid,
                "ui_label": p.get("ui_label") or _ui_label(pid),
                "sync_status": spec.get("sync_status"),
                "artifact_count": spec_summary.get("artifact_count", 0),
                "kind_counts": spec_summary.get("kind_counts", {}),
                "spec_dir": spec.get("spec_dir"),
                "spec_page_url": spec.get("spec_page_url"),
                "sources": spec.get("sources", []),
            }
        )
        readiness_entries.append(
            {
                "profile_id": pid,
                "ui_label": p.get("ui_label") or _ui_label(pid),
                "ready_for_impl_phase1": bool(gate.get("ready_for_impl_phase1")),
                "completed_checks": gate.get("completed_checks", []),
                "blocked_checks": gate.get("blocked_checks", []),
                "status_summary": {
                    "spec_sync_status": status_row.get("spec_sync_status"),
                    "logic_doc_status": status_row.get("logic_doc_status"),
                    "structure_doc_status": status_row.get("structure_doc_status"),
                },
                "sources": _merge_source_lists(gate.get("sources", []), (logic.get("sources") or []), (struct.get("sources") or [])),
            }
        )
        raw_entries.append(
            {
                "profile_id": pid,
                "ui_label": p.get("ui_label") or _ui_label(pid),
                "logic_raw_markdown_preview": logic.get("raw_markdown_preview") or "",
                "structure_raw_markdown_preview": struct.get("raw_markdown_preview") or "",
                "logic_path": ((logic.get("doc_meta") or {}).get("path") if isinstance(logic.get("doc_meta"), dict) else None),
                "structure_path": ((struct.get("doc_meta") or {}).get("path") if isinstance(struct.get("doc_meta"), dict) else None),
                "sources": _merge_source_lists(logic.get("sources", []), struct.get("sources", [])),
            }
        )

    autopts_entry = {
        "summary": {
            "cli_total": (((autopts_summary.get("cli") or {}).get("summary") or {}).get("total") if isinstance((autopts_summary.get("cli") or {}).get("summary"), dict) else 0),
            "stacks_count": len((autopts_summary.get("stacks") or {}).get("rows") or []),
            "quickstart_scenarios": len((autopts_summary.get("quickstart") or {}).get("scenarios") or []),
        },
        "sources": autopts_summary.get("sources", []),
    }

    sections = [
        {
            "id": "profile_deep_logic_structure",
            "label_he": "Deep Dive לפרופילים",
            "summary_he": "ממצאים/תצפיות/שאלות עומק לכל פרופיל (המידע שלא מוצג במסכי הפרופיל הפשוטים).",
            "entries": deep_profile_entries,
            "sources": _merge_source_lists(*[e.get("sources", []) for e in deep_profile_entries]),
        },
        {
            "id": "spec_artifacts_technical",
            "label_he": "מטא-דטה טכני של מפרטים וארטיפקטים",
            "summary_he": "artifact counts, kind_counts, נתיבי sync וסטטוסי סנכרון.",
            "entries": spec_meta_entries,
            "sources": _merge_source_lists(*[e.get("sources", []) for e in spec_meta_entries]),
        },
        {
            "id": "readiness_validation_qa",
            "label_he": "Readiness / Validation / QA (טכני)",
            "summary_he": "פירוט gates, validation ו-QA meta לצרכי בקרה ודיבאג.",
            "entries": readiness_entries,
            "panels": [
                {"id": "qa_meta", "label_he": "QA meta", "data": qa_meta},
                {"id": "readiness_summary", "label_he": "Readiness summary", "data": readiness_gates.get("summary", {})},
            ],
            "sources": _merge_source_lists(*[e.get("sources", []) for e in readiness_entries], qa_meta.get("sources", [])),
        },
        {
            "id": "autopts_deep_dive",
            "label_he": "AutoPTS Deep (מעבר לתקציר)",
            "summary_he": "סיכומי עומק רלוונטיים ל-AutoPTS (CLI / stacks / quickstart / 3-layers).",
            "entries": [autopts_entry],
            "panels": [
                {"id": "cli_summary", "label_he": "CLI summary", "data": (autopts_summary.get("cli") or {}).get("summary", {})},
                {"id": "test_support_layers", "label_he": "3 שכבות תמיכה", "data": autopts_summary.get("test_support_3_layers", {})},
                {"id": "stacks", "label_he": "Stacks", "data": autopts_summary.get("stacks", {})},
            ],
            "sources": autopts_summary.get("sources", []),
        },
        {
            "id": "raw_markdown_and_debug",
            "label_he": "Raw Markdown / Debug",
            "summary_he": "תצוגות raw previews ונתיבי קבצי MD לצורך review/debug בלבד.",
            "entries": raw_entries,
            "sources": _merge_source_lists(*[e.get("sources", []) for e in raw_entries]),
        },
    ]
    return {"sections": sections, "search_index": [], "sources": _merge_source_lists(*[s.get("sources", []) for s in sections])}


def build_base_profile_structure_catalog_placeholder(paths: Paths) -> Dict[str, Any]:
    return {
        "version": 1,
        "status": "placeholder",
        "profiles": {
            "simple_profile_baseline": {
                "label_he": "Profile פשוט (baseline placeholder)",
                "description_he": "Service + 1-2 Characteristics עם לוגיקה ומדיניות פשוטות יחסית.",
            },
            "complex_profile_baseline": {
                "label_he": "Profile מורכב (baseline placeholder)",
                "description_he": "Service עם כמה Characteristics, callbacks, state management ופיצול שכבות.",
            },
        },
        "sources": [repo_source(paths, paths.templates_root, note="Placeholder baseline until external base-structure source is integrated")],
    }


def build_group_b_hub_data(repo_root: Path | str = ".", autopts_guide: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    paths = _paths(repo_root)
    profile_map = load_profile_map(paths)
    manifests = load_group_b_manifests(paths)
    qa_meta = load_group_b_qa_meta(paths)
    spec_research = build_spec_research(paths, profile_map, manifests)
    logic_files, structure_files, logic_analysis, structure_analysis = build_md_file_inventory(paths, profile_map, manifests)
    autopts_summary = summarize_autopts_for_hub(paths, autopts_guide=autopts_guide)
    phase1_artifacts = build_phase1_profile_artifacts(profile_map, logic_analysis, structure_analysis)
    implementation_contracts = phase1_artifacts.get("implementation_contracts", {})
    test_targets_phase1 = phase1_artifacts.get("test_targets_phase1", {})
    review_signoffs = phase1_artifacts.get("review_signoffs", {})
    readiness_gates = build_readiness_gates(
        profile_map,
        spec_research,
        logic_analysis,
        structure_analysis,
        implementation_contracts,
        test_targets_phase1,
        review_signoffs,
    )
    status_tracker = build_status_tracker(
        profile_map,
        spec_research,
        logic_analysis,
        structure_analysis,
        implementation_contracts,
        test_targets_phase1,
        review_signoffs,
        readiness_gates,
        qa_meta,
    )
    source_catalog = manifests.get("source_catalog", {}) if isinstance(manifests, dict) else {}
    specs_presentation = build_specs_presentation(profile_map, spec_research)
    logic_presentation = build_logic_presentation(profile_map, logic_analysis, implementation_contracts, source_catalog)
    structure_presentation = build_structure_presentation(profile_map, structure_analysis, implementation_contracts, source_catalog)
    current_work = build_current_work_templates(
        profile_map,
        status_tracker,
        implementation_contracts,
        test_targets_phase1,
        logic_presentation,
        structure_presentation,
        readiness_gates,
        phase1_artifacts.get("phase1_decisions", {}),
    )
    base_profile_structure_catalog = build_base_profile_structure_catalog_placeholder(paths)
    knowledge_center = build_knowledge_center(
        profile_map,
        spec_research,
        logic_analysis,
        structure_analysis,
        status_tracker,
        readiness_gates,
        qa_meta,
        autopts_summary,
    )

    official_manifest = manifests.get("official", {}).get("manifest", {})
    sdk_manifest = manifests.get("sdk", {}).get("manifest", {})
    methods_manifest = manifests.get("methods", {}).get("manifest", {})

    sources_policy = {
        "summary_he": "מדיניות מקורות לעמוד Hub: Specs מ-SIG בלבד, Logic מ-Nordic רשמי, Structure מ-TI רשמי + דפוסים ממקורות מאושרים.",
        "sig": {
            "allowed_domains": (official_manifest.get("whitelists") or {}).get("sig", []),
            "rule_he": "מותר רק מקורות Bluetooth SIG/Qualification/PTS/Support רשמיים עבור Specs.",
        },
        "sdk_nordic": {
            "allowed_domains": (sdk_manifest.get("whitelists") or {}).get("sdk_nordic", []),
            "rule_he": "לוגיקה תיגזר ממקורות רשמיים של Nordic בלבד.",
        },
        "sdk_ti": {
            "allowed_domains": (sdk_manifest.get("whitelists") or {}).get("sdk_ti", []),
            "rule_he": "מבנה ייגזר ממקורות רשמיים של TI SimpleLink בלבד.",
        },
        "autopts_official": {
            "allowed_domains": ((autopts_summary.get("official_sources", {}) or {}).get("whitelist_domains") or []),
            "rule_he": "מידע AutoPTS משתמש ברשימת המקורות הרשמיים המאושרים שלו (Zephyr/Bluetooth SIG).",
        },
        "ux_ui": {
            "allowed_domains": (official_manifest.get("whitelists") or {}).get("ux_ui", []),
            "rule_he": "מקורות UX/UI מותרים לצורך תכנון תצוגה בלבד.",
        },
        "enforcement_rules": [
            "כל finding חייב confidence + source_ids + derivation_method_ids (אם קיים).",
            "כל URL חיצוני חייב להיות domain מאושר לפי הקטגוריה המתאימה.",
            "תצוגת פרופיל דורשת summary_he גם אם אין עדיין findings.",
        ],
        "sources": manifests.get("official", {}).get("sources", []) + manifests.get("sdk", {}).get("sources", []),
    }

    group_b = {
        "profile_map": profile_map,
        "spec_research": spec_research,
        "logic_files": logic_files,
        "structure_files": structure_files,
        "logic_analysis": logic_analysis,
        "structure_analysis": structure_analysis,
        "phase1_decisions": phase1_artifacts.get("phase1_decisions", {}),
        "implementation_contracts": implementation_contracts,
        "test_targets_phase1": test_targets_phase1,
        "review_signoffs": review_signoffs,
        "specs_presentation": specs_presentation,
        "logic_presentation": logic_presentation,
        "structure_presentation": structure_presentation,
        "current_work": current_work,
        "knowledge_center": knowledge_center,
        "base_profile_structure_catalog": base_profile_structure_catalog,
        "status_tracker": status_tracker,
        "sources_policy": sources_policy,
        "official_sources": {
            "entries": official_manifest.get("entries", []) if isinstance(official_manifest, dict) else [],
            "whitelists": official_manifest.get("whitelists", {}) if isinstance(official_manifest, dict) else {},
            "sources": manifests.get("official", {}).get("sources", []),
        },
        "sdk_sources": {
            "entries": sdk_manifest.get("entries", []) if isinstance(sdk_manifest, dict) else [],
            "whitelists": sdk_manifest.get("whitelists", {}) if isinstance(sdk_manifest, dict) else {},
            "sources": manifests.get("sdk", {}).get("sources", []),
        },
        "derivation_methods_catalog": {
            "methods": methods_manifest.get("methods", []) if isinstance(methods_manifest, dict) else [],
            "sources": manifests.get("methods", {}).get("sources", []),
        },
        "spec_sync_manifest": {
            "manifest": manifests.get("spec_sync", {}).get("manifest", {}),
            "sources": manifests.get("spec_sync", {}).get("sources", []),
        },
        "traceability_index": {},
        "readiness_gates": readiness_gates,
        "qa_meta": {
            **qa_meta,
            "sources": qa_meta.get("sources", []),
        },
        "sources": (
            profile_map.get("sources", [])
            + spec_research.get("sources", [])
            + manifests.get("official", {}).get("sources", [])
            + manifests.get("sdk", {}).get("sources", [])
            + manifests.get("methods", {}).get("sources", [])
            + manifests.get("spec_sync", {}).get("sources", [])
            + qa_meta.get("sources", [])
        ),
    }

    navigation = {
        "top_tabs": [
            {"id": "autopts", "label": "AutoPTS"},
            {"id": "BPS", "label": "BPS"},
            {"id": "WSS", "label": "WSS"},
            {"id": "SCPS", "label": "ScPS"},
            {"id": "knowledge_center", "label": "מרכז ידע"},
            {"id": "sources", "label": "מקורות ועקיבות"},
        ],
        "profile_subtabs": [
            {"id": "specs", "label": "מפרטים"},
            {"id": "logic", "label": "לוגיקה"},
            {"id": "structure", "label": "מבנה"},
            {"id": "status", "label": "מצב עבודה נוכחי"},
        ],
    }

    data = {
        "meta": {
            "generated_date": date.today().isoformat(),
            "repo_root": str(paths.repo),
            "builder_script": _norm_rel(paths.repo, paths.builder_script),
            "templates_root": _norm_rel(paths.repo, paths.templates_root),
            "hub_output_dir": "dashboards/pts_report_he/autopts",
            "summary_he": "Hub ייעודי ל-AutoPTS + Group B עם תצוגת ידע מובנית עבור Logic/Structure.",
            "sources": [
                repo_source(paths, paths.builder_script, note="Builder integrates hub output"),
                repo_source(paths, paths.templates_root, note="Hub templates + Group_B_data source"),
            ],
        },
        "navigation": navigation,
        "auto_pts_summary": autopts_summary,
        "group_b": group_b,
        "known_limits": {
            "items": [
                {
                    "title_he": "מוכנות Group B נמדדת דרך readiness gates ולא רק baseline",
                    "detail_he": "העמוד מבחין בין baseline (ממצאים/תצפיות) לבין sign-off למוכנות מימוש Phase 1 (review, contracts, test targets).",
                    "tags": ["group_b", "readiness", "phase1"],
                },
                {
                    "title_he": "תצוגת Raw MD זמינה רק לצורכי review/debug",
                    "detail_he": "התצוגה הראשית היא מסונתזת ומבוססת schema, לא Markdown raw.",
                    "tags": ["ux", "storage-vs-presentation"],
                },
                {
                    "title_he": "Exact runtime test list של AutoPTS עדיין דורש Windows + PTS COM",
                    "detail_he": "העמוד מציג הנחיות ותשתית, לא שאילתה live מתוך PTS COM.",
                    "tags": ["autopts", "runtime"],
                },
            ],
            "sources": autopts_summary.get("sources", []) + qa_meta.get("sources", []),
        },
    }

    group_b["traceability_index"] = build_traceability_index(data)
    return data


def _collect_external_urls(obj: Any) -> Iterator[str]:
    if isinstance(obj, dict):
        url = obj.get("url")
        if isinstance(url, str):
            yield url
        for v in obj.values():
            yield from _collect_external_urls(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _collect_external_urls(item)


def enforce_group_b_hub_source_policy(data: Dict[str, Any]) -> None:
    for key in REQUIRED_HUB_KEYS:
        if key not in data:
            raise ValueError(f"group_b_hub_data missing required top-level key: {key}")

    group_b = data.get("group_b", {})
    if not isinstance(group_b, dict):
        raise ValueError("group_b must be a dict")
    if not isinstance(group_b.get("readiness_gates"), dict):
        raise ValueError("group_b.readiness_gates must be a dict")
    if not isinstance(group_b.get("qa_meta"), dict):
        raise ValueError("group_b.qa_meta must be a dict")
    for key in (
        "implementation_contracts",
        "test_targets_phase1",
        "review_signoffs",
        "phase1_decisions",
        "specs_presentation",
        "logic_presentation",
        "structure_presentation",
        "current_work",
        "knowledge_center",
        "base_profile_structure_catalog",
    ):
        if not isinstance(group_b.get(key), dict):
            raise ValueError(f"group_b.{key} must be a dict")

    policy = group_b.get("sources_policy", {})
    if not isinstance(policy, dict):
        raise ValueError("group_b.sources_policy must be a dict")

    allowed_domains: set[str] = set()
    for key in ("sig", "sdk_nordic", "sdk_ti", "autopts_official", "ux_ui"):
        section = policy.get(key, {})
        if isinstance(section, dict):
            for domain in section.get("allowed_domains", []) if isinstance(section.get("allowed_domains"), list) else []:
                allowed_domains.add(str(domain).lower())
    if not allowed_domains:
        raise ValueError("group_b sources policy has no allowed domains")

    for url in _collect_external_urls(data):
        domain = (urlparse(url).hostname or "").lower()
        if not domain:
            raise ValueError(f"Invalid URL in hub data: {url}")
        if domain.startswith("www."):
            bare = domain[4:]
        else:
            bare = domain
        if bare not in allowed_domains and domain not in allowed_domains:
            raise ValueError(f"External URL domain not allowed by group_b source policy: {url} (domain={domain})")

    for analysis_key in ("logic_analysis", "structure_analysis"):
        analysis = group_b.get(analysis_key, {})
        if not isinstance(analysis, dict):
            raise ValueError(f"group_b.{analysis_key} must be a dict")
        for pid in PROFILE_IDS:
            row = analysis.get(pid)
            if not isinstance(row, dict):
                raise ValueError(f"group_b.{analysis_key}.{pid} missing or invalid")
            if not str(row.get("summary_he") or "").strip():
                raise ValueError(f"group_b.{analysis_key}.{pid} missing summary_he")
            for finding in row.get("core_findings", []) if isinstance(row.get("core_findings"), list) else []:
                if not str(finding.get("confidence") or "").strip():
                    raise ValueError(f"{analysis_key}.{pid} finding missing confidence")
                if not isinstance(finding.get("source_ids"), list):
                    raise ValueError(f"{analysis_key}.{pid} finding missing source_ids list")
                if not [x for x in finding.get("source_ids", []) if str(x).strip()]:
                    raise ValueError(f"{analysis_key}.{pid} finding source_ids list is empty")
                if not isinstance(finding.get("derivation_method_ids"), list):
                    raise ValueError(f"{analysis_key}.{pid} finding missing derivation_method_ids list")
                if not [x for x in finding.get("derivation_method_ids", []) if str(x).strip()]:
                    raise ValueError(f"{analysis_key}.{pid} finding derivation_method_ids list is empty")
                if not finding.get("sources"):
                    raise ValueError(f"{analysis_key}.{pid} finding missing sources")
                if str(finding.get("status") or "").lower() == "inferred" and str(finding.get("confidence") or "").lower() == "high":
                    evidence_refs = finding.get("evidence_refs")
                    if not isinstance(evidence_refs, list) or len(evidence_refs) < 2:
                        # warning-level rule enforced as data warning, not hard-fail
                        pass
            for obs in row.get("source_observations", []) if isinstance(row.get("source_observations"), list) else []:
                if not str(obs.get("source_id") or "").strip():
                    raise ValueError(f"{analysis_key}.{pid} source observation missing source_id")
                if not str(obs.get("confidence") or "").strip():
                    raise ValueError(f"{analysis_key}.{pid} source observation missing confidence")
                if not str(obs.get("what_identified_he") or "").strip():
                    raise ValueError(f"{analysis_key}.{pid} source observation missing what_identified_he")
                if not str(obs.get("how_identified_he") or "").strip():
                    raise ValueError(f"{analysis_key}.{pid} source observation missing how_identified_he")

    for presentation_key in ("specs_presentation", "logic_presentation", "structure_presentation", "current_work"):
        vm = group_b.get(presentation_key, {})
        profiles = vm.get("profiles", {}) if isinstance(vm, dict) else {}
        if not isinstance(profiles, dict):
            raise ValueError(f"group_b.{presentation_key}.profiles must be a dict")
        for pid in PROFILE_IDS:
            row = profiles.get(pid)
            if not isinstance(row, dict):
                raise ValueError(f"group_b.{presentation_key}.profiles.{pid} missing or invalid")
            if not str(row.get("profile_id") or "").strip():
                raise ValueError(f"group_b.{presentation_key}.profiles.{pid}.profile_id missing")

    specs_presentation = group_b.get("specs_presentation", {})
    for pid in PROFILE_IDS:
        srow = ((specs_presentation.get("profiles") or {}).get(pid) or {})
        groups = srow.get("groups")
        if not isinstance(groups, list):
            raise ValueError(f"group_b.specs_presentation.profiles.{pid}.groups must be a list")
        for grp in groups:
            if not isinstance(grp, dict):
                raise ValueError(f"group_b.specs_presentation.profiles.{pid}.groups contains non-dict")
            if not isinstance(grp.get("files"), list):
                raise ValueError(f"group_b.specs_presentation.profiles.{pid}.groups[].files must be a list")

    current_work = group_b.get("current_work", {})
    for pid in PROFILE_IDS:
        crow = ((current_work.get("profiles") or {}).get(pid) or {})
        templates = crow.get("task_templates")
        if not isinstance(templates, list):
            raise ValueError(f"group_b.current_work.profiles.{pid}.task_templates must be a list")
        for task in templates:
            if not isinstance(task, dict):
                raise ValueError(f"group_b.current_work.profiles.{pid}.task_templates contains non-dict task")
            for key in ("task_id", "title_he", "category", "default_status"):
                if not str(task.get(key) or "").strip():
                    raise ValueError(f"group_b.current_work.profiles.{pid} task missing {key}")
            if not isinstance(task.get("source_refs"), list):
                raise ValueError(f"group_b.current_work.profiles.{pid} task.source_refs must be a list")

    knowledge_center = group_b.get("knowledge_center", {})
    sections = knowledge_center.get("sections") if isinstance(knowledge_center, dict) else None
    if not isinstance(sections, list):
        raise ValueError("group_b.knowledge_center.sections must be a list")
    for sec in sections:
        if not isinstance(sec, dict):
            raise ValueError("group_b.knowledge_center.sections contains non-dict")
        for key in ("id", "label_he", "summary_he"):
            if not str(sec.get(key) or "").strip():
                raise ValueError(f"group_b.knowledge_center section missing {key}")

    for pid in PROFILE_IDS:
        contract = (group_b.get("implementation_contracts") or {}).get(pid)
        if not isinstance(contract, dict):
            raise ValueError(f"group_b.implementation_contracts.{pid} missing or invalid")
        for key in (
            "scope_in",
            "scope_out",
            "implementation_order",
            "blocking_assumptions",
            "non_blocking_deferred",
            "sources",
        ):
            if not isinstance(contract.get(key), list):
                raise ValueError(f"implementation_contracts.{pid}.{key} must be a list")
        for key in (
            "service_api_contract",
            "runtime_flow_contract",
            "data_model_contract",
            "ccc_and_notify_indicate_contract",
            "error_policy_contract",
            "dependency_contract",
            "module_boundaries",
        ):
            if not isinstance(contract.get(key), dict):
                raise ValueError(f"implementation_contracts.{pid}.{key} must be a dict")

        test_target = (group_b.get("test_targets_phase1") or {}).get(pid)
        if not isinstance(test_target, dict):
            raise ValueError(f"group_b.test_targets_phase1.{pid} missing or invalid")
        for key in (
            "manual_smoke_checks",
            "pts_autopts_target_areas",
            "ics_ixit_assumptions",
            "phase1_done_criteria",
            "known_non_goals",
            "sources",
        ):
            if not isinstance(test_target.get(key), list):
                raise ValueError(f"test_targets_phase1.{pid}.{key} must be a list")

        signoff = (group_b.get("review_signoffs") or {}).get(pid)
        if not isinstance(signoff, dict):
            raise ValueError(f"group_b.review_signoffs.{pid} missing or invalid")
        for key in ("logic_reviewed", "structure_reviewed", "ready_for_impl_phase1"):
            if not isinstance(signoff.get(key), bool):
                raise ValueError(f"review_signoffs.{pid}.{key} must be a bool")
        for key in ("reviewer_notes_he", "remaining_phase1_blockers", "sources"):
            if not isinstance(signoff.get(key), list):
                raise ValueError(f"review_signoffs.{pid}.{key} must be a list")
        for key in ("review_summary_he", "ready_decision_reason_he"):
            if not str(signoff.get(key) or "").strip():
                raise ValueError(f"review_signoffs.{pid}.{key} missing")

        decisions = ((group_b.get("phase1_decisions") or {}).get(pid) or {}).get("rows")
        if decisions is None or not isinstance(decisions, list):
            raise ValueError(f"group_b.phase1_decisions.{pid}.rows must be a list")
        for dec in decisions:
            if not isinstance(dec, dict):
                raise ValueError(f"group_b.phase1_decisions.{pid} contains non-dict decision")
            if not str(dec.get("title_he") or "").strip():
                raise ValueError(f"group_b.phase1_decisions.{pid} decision missing title_he")
            if not str(dec.get("decision_he") or "").strip():
                raise ValueError(f"group_b.phase1_decisions.{pid} decision missing decision_he")
            if not isinstance(dec.get("source_ids"), list) or not [x for x in dec.get("source_ids", []) if str(x).strip()]:
                raise ValueError(f"group_b.phase1_decisions.{pid} decision missing source_ids")

    readiness = group_b.get("readiness_gates", {})
    profiles_readiness = readiness.get("profiles", {}) if isinstance(readiness, dict) else {}
    if not isinstance(profiles_readiness, dict):
        raise ValueError("group_b.readiness_gates.profiles must be a dict")
    for pid in PROFILE_IDS:
        gate = profiles_readiness.get(pid)
        if not isinstance(gate, dict):
            raise ValueError(f"group_b.readiness_gates.profiles.{pid} missing or invalid")
        for list_key in ("required_checks", "completed_checks", "blocked_checks", "decision_notes_he"):
            if not isinstance(gate.get(list_key), list):
                raise ValueError(f"group_b.readiness_gates.profiles.{pid}.{list_key} must be a list")
        if "ready_for_impl_phase1" not in gate:
            raise ValueError(f"group_b.readiness_gates.profiles.{pid} missing ready_for_impl_phase1")
        for check in (
            "implementation_contract_defined",
            "phase1_test_targets_defined",
            "phase1_blockers_closed_or_deferred",
            "review_signoff_complete",
        ):
            if check not in gate.get("required_checks", []):
                raise ValueError(f"group_b.readiness_gates.profiles.{pid} missing required check {check}")

    qa_meta = group_b.get("qa_meta", {})
    for key in ("smoke_test_mode", "known_expected_console_errors", "last_manual_review_notes_he"):
        if key not in qa_meta:
            raise ValueError(f"group_b.qa_meta missing {key}")
    if not isinstance(qa_meta.get("known_expected_console_errors"), list):
        raise ValueError("group_b.qa_meta.known_expected_console_errors must be a list")
    if not isinstance(qa_meta.get("last_manual_review_notes_he"), list):
        raise ValueError("group_b.qa_meta.last_manual_review_notes_he must be a list")
