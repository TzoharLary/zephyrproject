from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
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
}

REQUIRED_SECTIONS_BY_KIND = {
    "logic": [
        "סיכום",
        "ממצאים",
        "תצפיות לפי מקור",
        "שיטות חילוץ/ניתוח",
        "פערים ושאלות פתוחות",
        "השלכות למימוש",
        "מקורות",
    ],
    "structure": [
        "סיכום",
        "מבנה מוצע",
        "דפוסים שזוהו לפי מקור",
        "שיטות חילוץ/ניתוח",
        "פערים ושאלות פתוחות",
        "השלכות למימוש",
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
    return path.read_text(encoding="utf-8", errors="replace")


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
        try:
            parsed = json.loads(payload_text)
            payload = parsed if isinstance(parsed, dict) else {"value": parsed}
        except Exception:
            payload = {"raw": payload_text}
            for line in payload_text.splitlines():
                m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line.strip())
                if m:
                    payload[m.group(1)] = _parse_scalar(m.group(2))
        payload["_block_type"] = block_type
        payload["_ordinal"] = i
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
    front_matter, body = split_front_matter(raw) if raw else ({}, "")
    sections = parse_sections(body) if body else []
    blocks = parse_structured_blocks(body) if body else []
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
            },
        },
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


def build_status_tracker(
    profile_map: Dict[str, Any],
    spec_research: Dict[str, Any],
    logic_analysis: Dict[str, Any],
    structure_analysis: Dict[str, Any],
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
        row = {
            "profile_id": pid,
            "ui_label": profile_row.get("ui_label") or pid,
            "display_name_he": profile_row.get("display_name_he") or pid,
            "spec_sync_status": spec.get("sync_status") or "unknown",
            "spec_artifacts": (spec.get("summary") or {}).get("artifact_count", 0),
            "logic_doc_status": logic.get("status") or "unknown",
            "logic_findings": len(logic.get("core_findings", []) if isinstance(logic.get("core_findings"), list) else []),
            "logic_open_questions": len(logic.get("open_questions", []) if isinstance(logic.get("open_questions"), list) else []),
            "structure_doc_status": structure.get("status") or "unknown",
            "structure_findings": len(structure.get("core_findings", []) if isinstance(structure.get("core_findings"), list) else []),
            "structure_open_questions": len(structure.get("open_questions", []) if isinstance(structure.get("open_questions"), list) else []),
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
        rows.append(row)

    summary = {
        "profiles": len(rows),
        "spec_synced": sum(1 for r in rows if r.get("spec_sync_status") == "synced"),
        "logic_with_findings": sum(1 for r in rows if int(r.get("logic_findings") or 0) > 0),
        "structure_with_findings": sum(1 for r in rows if int(r.get("structure_findings") or 0) > 0),
        "all_logic_scaffold": all(str(r.get("logic_doc_status")) in ("scaffold", "draft", "scaffold_partial") for r in rows) if rows else True,
        "all_structure_scaffold": all(str(r.get("structure_doc_status")) in ("scaffold", "draft", "scaffold_partial") for r in rows) if rows else True,
    }
    return {"rows": rows, "summary": summary, "sources": []}


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


def build_group_b_hub_data(repo_root: Path | str = ".", autopts_guide: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    paths = _paths(repo_root)
    profile_map = load_profile_map(paths)
    manifests = load_group_b_manifests(paths)
    spec_research = build_spec_research(paths, profile_map, manifests)
    logic_files, structure_files, logic_analysis, structure_analysis = build_md_file_inventory(paths, profile_map, manifests)
    autopts_summary = summarize_autopts_for_hub(paths, autopts_guide=autopts_guide)
    status_tracker = build_status_tracker(profile_map, spec_research, logic_analysis, structure_analysis)

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
        "sources": (
            profile_map.get("sources", [])
            + spec_research.get("sources", [])
            + manifests.get("official", {}).get("sources", [])
            + manifests.get("sdk", {}).get("sources", [])
            + manifests.get("methods", {}).get("sources", [])
            + manifests.get("spec_sync", {}).get("sources", [])
        ),
    }

    navigation = {
        "top_tabs": [
            {"id": "overview", "label": "סקירה"},
            {"id": "autopts", "label": "AutoPTS"},
            {"id": "BPS", "label": "BPS"},
            {"id": "WSS", "label": "WSS"},
            {"id": "SCPS", "label": "ScPS"},
            {"id": "sources", "label": "מקורות ועקיבות"},
        ],
        "profile_subtabs": [
            {"id": "specs", "label": "מפרטים"},
            {"id": "logic", "label": "לוגיקה"},
            {"id": "structure", "label": "מבנה"},
            {"id": "status", "label": "מצב עבודה / פערים"},
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
                    "title_he": "קבצי Logic/Structure מוגדרים כטיוטת scaffold בשלב זה",
                    "detail_he": "ה-parser והתצוגה מוכנים, אך רוב הממצאים הטכניים טרם חולצו מ-Nordic/TI בפועל.",
                    "tags": ["scaffold", "group_b"],
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
            "sources": autopts_summary.get("sources", []),
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
                if not isinstance(finding.get("derivation_method_ids"), list):
                    raise ValueError(f"{analysis_key}.{pid} finding missing derivation_method_ids list")
                if not finding.get("sources"):
                    raise ValueError(f"{analysis_key}.{pid} finding missing sources")
            for obs in row.get("source_observations", []) if isinstance(row.get("source_observations"), list) else []:
                if not str(obs.get("source_id") or "").strip():
                    raise ValueError(f"{analysis_key}.{pid} source observation missing source_id")
                if not str(obs.get("confidence") or "").strip():
                    raise ValueError(f"{analysis_key}.{pid} source observation missing confidence")
