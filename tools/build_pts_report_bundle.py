#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


WORKSPACE_PQW6 = Path("auto-pts/autopts/workspaces/zephyr/zephyr-master/zephyr-master.pqw6")
PTSCONTROL_PY = Path("auto-pts/autopts/ptscontrol.py")
ICS_RST_SCRIPT = Path("auto-pts/tools/ics_rst_from_html.py")

PROFILES_DIR = Path("docs/profiles")
PROFILE_DOCS = {
    "BAS": {
        "dir": PROFILES_DIR / "BAS",
        "spec": "Battery_Service_1.1.pdf",
        "ics": "Implementation_Conformance_Statement_ICS.pdf",
        "ts": "Test_Suite_TS.pdf",
    },
    "DIS": {
        "dir": PROFILES_DIR / "DIS",
        "spec": "Device_Information_Service_1.2.pdf",
        "ics": "Implementation_Conformance_Statement_ICS.pdf",
        "ts": "Test_Suite_TS.pdf",
    },
    "HRS": {
        "dir": PROFILES_DIR / "HRS",
        "spec": "Heart_Rate_Service_1.0.pdf",
        "ics": "Implementation_Conformance_Statement_ICS.pdf",
        "ts": "Test_Suite_TS.pdf",
    },
    "HID": {
        "dir": PROFILES_DIR / "HID",
        "spec": "HID_Over_GATT_Profile_1.1.pdf",
        "ics": "Implementation_Conformance_Statement_ICS.pdf",
        "ts": "Test_Suite_TS.pdf",
    },
}

ICS_PDF = {
    "BAS": PROFILE_DOCS["BAS"]["dir"] / PROFILE_DOCS["BAS"]["ics"],
    "DIS": PROFILE_DOCS["DIS"]["dir"] / PROFILE_DOCS["DIS"]["ics"],
    "HRS": PROFILE_DOCS["HRS"]["dir"] / PROFILE_DOCS["HRS"]["ics"],
    "HOGP": PROFILE_DOCS["HID"]["dir"] / PROFILE_DOCS["HID"]["ics"],
}

OUT_DIR = Path("dashboards/pts_report_he")
OUT_HTML = OUT_DIR / "index.html"
OUT_CSS = OUT_DIR / "assets" / "report.css"
OUT_JS = OUT_DIR / "assets" / "report.js"
OUT_DATA = OUT_DIR / "data" / "report-data.js"

TEMPLATE_DIR = Path(__file__).parent / "templates" / "pts_report_he"
TEMPLATE_HTML = TEMPLATE_DIR / "index.html"
TEMPLATE_CSS = TEMPLATE_DIR / "report.css"
TEMPLATE_JS = TEMPLATE_DIR / "report.js"
RUNTIME_ACTIVE_EXPORT_DEFAULT = Path("tools/runtime_active_tcids.json")
RUNTIME_ACTIVE_HISTORY_DIR_DEFAULT = Path("tools/runtime_history")

EXPECTED_WORKSPACE_SUFFIX = "/zephyr-master/zephyr-master.pqw6"

TOKEN_STOPWORDS = {
    "and",
    "or",
    "the",
    "of",
    "for",
    "to",
    "with",
    "without",
    "supported",
    "support",
    "service",
    "characteristic",
    "descriptor",
    "string",
    "record",
    "present",
    "over",
    "profile",
    "device",
    "information",
    "mode",
    "feature",
    "test",
    "cases",
    "case",
    "all",
    "enables",
    "set",
    "when",
    "used",
    "no",
    "longer",
}

ACTION_TERMS = {
    "read": {"read", "get"},
    "write": {"write", "set"},
    "notify": {"notify", "notification"},
    "indicate": {"indicate", "indication"},
    "broadcast": {"broadcast"},
    "configure": {"configure", "config"},
    "report": {"report"},
    "service": {"service"},
    "descriptor": {"descriptor"},
    "characteristic": {"characteristic"},
}

ENTITY_ALIASES = {
    "manufacturer": {"manufacturer", "manufacturername"},
    "model": {"model", "modelnumber"},
    "serial": {"serial", "serialnumber"},
    "firmware": {"firmware", "fw"},
    "software": {"software", "sw"},
    "hardware": {"hardware", "hw"},
    "pnp": {"pnp"},
    "battery": {"battery"},
    "heart": {"heart"},
    "rate": {"rate"},
    "energy": {"energy"},
    "rr": {"rr", "rrinterval"},
    "hid": {"hid", "hids", "hogp"},
    "protocol": {"protocol"},
    "reportmap": {"reportmap"},
}

TCID_PATTERN = re.compile(r"\b[A-Z0-9]+(?:/[A-Z0-9]+){2,}/(?:BV|BI)-\d+-[A-Z]\b")
PROFILE_TCID_PREFIX = {"DIS": "DIS", "BAS": "BAS", "HRS": "HRS", "HID": "HOGP"}
TCMT_SECTION_RE = re.compile(r"^5\s+test case mapping\s*$", re.IGNORECASE)
REVISION_SECTION_RE = re.compile(r"^6\s+revision history", re.IGNORECASE)
NO_OFFICIAL_ENGLISH_TEXT = "No official English test description is available."

IOPT_VERIFIED_HEBREW: Dict[str, str] = {
    "IOPT/BAS/SR/GATTDB/BV-01-I": "הטסט מאמת את תקינות שירות GATT עבור פרופיל BAS.",
    "IOPT/BAS/SR/SGGIT/SDP/BV-01-I": "הטסט מאמת את רשומת ה-SDP של שירות BAS המבוסס על GATT.",
    "IOPT/DIS/SR/GATTDB/BV-01-I": "הטסט מאמת את תקינות שירות GATT עבור פרופיל DIS.",
    "IOPT/DIS/SR/SGGIT/SDP/BV-01-I": "הטסט מאמת את רשומת ה-SDP של שירות DIS המבוסס על GATT.",
    "IOPT/HRS/SEN/GATTDB/BV-01-I": "הטסט מאמת את תקינות שירות GATT עבור פרופיל HRS.",
    "IOPT/HID/DEV/SDPR/BV-01-I": "הטסט מאמת את רשומת ה-SDP עבור תפקיד התקן HID.",
    "IOPT/HID/HOS/CGSIT/SFC/BV-01-I": "הטסט מאמת תאימות עתידית ב-SDP כאשר ה-IUT פועל כמארח HID.",
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def ensure_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def run_pdftotext(path: Path, first_page: Optional[int] = None, last_page: Optional[int] = None) -> str:
    cmd = ["pdftotext", "-layout"]
    if first_page is not None:
        cmd.extend(["-f", str(first_page)])
    if last_page is not None:
        cmd.extend(["-l", str(last_page)])
    cmd.extend([str(path), "-"])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"pdftotext failed for {path}: {proc.stderr.strip()}")
    return proc.stdout


PDF_LINE_CACHE: Dict[str, List[str]] = {}
PDF_META_CACHE: Dict[str, Dict[str, str]] = {}


def read_pdf_lines(path: Path) -> List[str]:
    key = str(path)
    if key in PDF_LINE_CACHE:
        return PDF_LINE_CACHE[key]
    ensure_exists(path, "PDF")
    text = run_pdftotext(path)
    PDF_LINE_CACHE[key] = text.splitlines()
    return PDF_LINE_CACHE[key]


def find_line_in_pdf(path: Path, needle: str) -> Optional[int]:
    n = normalize_text(needle)
    if not n:
        return None
    for i, line in enumerate(read_pdf_lines(path), start=1):
        if n in normalize_text(line):
            return i
    return None


def extract_pdf_metadata(path: Path) -> Dict[str, str]:
    key = str(path)
    if key in PDF_META_CACHE:
        return PDF_META_CACHE[key]

    header = run_pdftotext(path, first_page=1, last_page=3)
    meta = {}
    for line in header.splitlines():
        m = re.search(
            r"(Revision|Version|Revision Date|Version Date|Published during TCRL)\s*:\s*(.+?)\s*$",
            line,
        )
        if m:
            meta[m.group(1)] = m.group(2)
    PDF_META_CACHE[key] = meta
    return meta


def read_template_or_fallback(path: Path, fallback: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return fallback


def resolve_runtime_active_export_path() -> Path:
    override = os.environ.get("PTS_RUNTIME_ACTIVE_JSON", "").strip()
    if override:
        return Path(override)
    return RUNTIME_ACTIVE_EXPORT_DEFAULT


def resolve_runtime_active_history_dir() -> Path:
    override = os.environ.get("PTS_RUNTIME_HISTORY_DIR", "").strip()
    if override:
        return Path(override)
    return RUNTIME_ACTIVE_HISTORY_DIR_DEFAULT


def parse_runtime_timestamp(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    ts = value.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_tcid_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out = []
    for value in values:
        if not isinstance(value, str):
            continue
        item = value.strip()
        if not item:
            continue
        out.append(item)
    return sorted(set(out))


def parse_project_active_tcids(raw_projects: Any) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    if not isinstance(raw_projects, dict):
        return out

    for project, value in raw_projects.items():
        if not isinstance(project, str) or not project:
            continue
        if isinstance(value, list):
            out[project] = normalize_tcid_list(value)
            continue
        if isinstance(value, dict):
            tcids = normalize_tcid_list(value.get("active_tcids"))
            if tcids:
                out[project] = tcids
    return out


def load_runtime_active_export(path: Path) -> Dict[str, Any]:
    profile_prefixes = {
        "DIS": "DIS/",
        "BAS": "BAS/",
        "HRS": "HRS/",
        "HID": "HOGP/",
    }
    empty_profiles = {
        profile: {"active_tcids": [], "count": 0, "project": None, "projects": []}
        for profile in profile_prefixes.keys()
    }
    out: Dict[str, Any] = {
        "available": False,
        "file": str(path),
        "generated_at": None,
        "workspace": None,
        "export_tool": None,
        "profile_prefixes": profile_prefixes,
        "profiles": empty_profiles,
        "project_counts": {},
        "errors": [],
    }
    if not path.exists():
        out["errors"].append("runtime_active_export_missing")
        return out

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        out["errors"].append(f"runtime_active_export_invalid_json: {exc}")
        return out

    out["available"] = True
    out["generated_at"] = raw.get("generated_at")
    out["workspace"] = raw.get("workspace")
    out["export_tool"] = raw.get("export_tool")

    project_active = parse_project_active_tcids(raw.get("projects"))
    out["project_counts"] = {project: len(tcids) for project, tcids in project_active.items()}

    all_project_tcids: List[str] = []
    for tcids in project_active.values():
        all_project_tcids.extend(tcids)
    all_project_tcids = sorted(set(all_project_tcids))

    raw_profiles = raw.get("profiles") if isinstance(raw.get("profiles"), dict) else {}
    for profile, prefix in profile_prefixes.items():
        profile_raw = raw_profiles.get(profile) if isinstance(raw_profiles.get(profile), dict) else {}
        explicit_tcids = normalize_tcid_list(profile_raw.get("active_tcids"))
        derived_tcids = [tcid for tcid in all_project_tcids if tcid.startswith(prefix)]
        active_tcids = explicit_tcids or derived_tcids

        projects = profile_raw.get("projects")
        if not isinstance(projects, list):
            projects = []
        projects = [item for item in projects if isinstance(item, str) and item]

        project = profile_raw.get("project")
        if not isinstance(project, str) or not project:
            project = None

        out["profiles"][profile] = {
            "active_tcids": active_tcids,
            "count": len(active_tcids),
            "project": project,
            "projects": projects,
        }

    return out


def make_runtime_snapshot_id(snapshot: Dict[str, Any], index: int = 0) -> str:
    generated = snapshot.get("generated_at") if isinstance(snapshot.get("generated_at"), str) else "na"
    file_name = Path(str(snapshot.get("file") or "snapshot")).name
    return f"{index:03d}:{file_name}:{generated}"


def collect_runtime_active_history(current_path: Path) -> List[Dict[str, Any]]:
    candidates: List[Path] = [current_path]
    history_dir = resolve_runtime_active_history_dir()
    if history_dir.exists():
        candidates.extend(sorted(history_dir.glob("*.json")))

    snapshots: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    for path in candidates:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)

        snapshot = load_runtime_active_export(path)
        if not snapshot.get("available"):
            continue
        snapshots.append(snapshot)

    def sort_key(item: Dict[str, Any]) -> Tuple[datetime, str]:
        parsed = parse_runtime_timestamp(item.get("generated_at")) or datetime.min.replace(
            tzinfo=timezone.utc
        )
        return (parsed, str(item.get("file") or ""))

    snapshots.sort(key=sort_key, reverse=True)

    for index, snapshot in enumerate(snapshots):
        snapshot["id"] = make_runtime_snapshot_id(snapshot, index)

    return snapshots


def find_line(path: Path, pattern: str) -> Optional[int]:
    rx = re.compile(pattern)
    for i, line in enumerate(read_lines(path), start=1):
        if rx.search(line):
            return i
    return None


def find_first_line_containing(path: Path, needle: str) -> Optional[int]:
    for i, line in enumerate(read_lines(path), start=1):
        if needle in line:
            return i
    return None


def resolve_profile_sources() -> Dict[str, Dict[str, Path]]:
    out: Dict[str, Dict[str, Path]] = {}
    for profile, cfg in PROFILE_DOCS.items():
        pdir = cfg["dir"]
        spec = pdir / cfg["spec"]
        ics = pdir / cfg["ics"]
        ts = pdir / cfg["ts"]
        tcrl_dir = pdir / "Test_Case_Reference_List_TCRL" / "TCRLpkg101p1"
        out[profile] = {
            "dir": pdir,
            "spec": spec,
            "ics": ics,
            "ts": ts,
            "tcrl_dir": tcrl_dir,
            "tcrl_gatt": tcrl_dir / "GATTBased.TCRL.p27.xlsx",
            "tcrl_trad": tcrl_dir / "Traditional.TCRL.p47.xlsx",
            "tcrl_iopt": tcrl_dir / "IOPT.TCRL.p8.xlsx",
        }
    return out


def validate_profile_sources(profile_sources: Dict[str, Dict[str, Path]]) -> None:
    for profile, src in profile_sources.items():
        ensure_exists(src["spec"], f"{profile} spec")
        ensure_exists(src["ics"], f"{profile} ICS")
        ensure_exists(src["ts"], f"{profile} TS")
        ensure_exists(src["tcrl_gatt"], f"{profile} TCRL GATT workbook")
        ensure_exists(src["tcrl_trad"], f"{profile} TCRL Traditional workbook")
        ensure_exists(src["tcrl_iopt"], f"{profile} TCRL IOPT workbook")


def normalize_text(s: str) -> str:
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def normalize_ics_item(item: str) -> str:
    return re.sub(r"\s+", "", str(item or "")).lower()


def collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").replace("\x0c", " ")).strip()


def profile_tcid_prefix(profile: str) -> str:
    return PROFILE_TCID_PREFIX.get(profile, profile)


def is_profile_tcid(profile: str, tcid: str) -> bool:
    prefix = profile_tcid_prefix(profile)
    return str(tcid or "").startswith(f"{prefix}/")


def tri_not(value: Optional[bool]) -> Optional[bool]:
    if value is None:
        return None
    return not value


def tri_and(left: Optional[bool], right: Optional[bool]) -> Optional[bool]:
    if left is False or right is False:
        return False
    if left is True and right is True:
        return True
    return None


def tri_or(left: Optional[bool], right: Optional[bool]) -> Optional[bool]:
    if left is True or right is True:
        return True
    if left is False and right is False:
        return False
    return None


def tokenize_text(s: str) -> Set[str]:
    norm = normalize_text(s)
    if not norm:
        return set()
    chunks = re.split(r"[^a-z0-9]+", norm)
    out = set()
    for chunk in chunks:
        if not chunk:
            continue
        if len(chunk) == 1 and not chunk.isdigit():
            continue
        if chunk in TOKEN_STOPWORDS:
            continue
        out.add(chunk)
    return out


def collect_action_hits(s: str) -> Set[str]:
    norm = normalize_text(s)
    hits = set()
    for action, aliases in ACTION_TERMS.items():
        if any(alias in norm for alias in aliases):
            hits.add(action)
    return hits


def collect_entity_hits(tokens: Set[str]) -> Set[str]:
    hits = set()
    for entity, aliases in ENTITY_ALIASES.items():
        if tokens.intersection(aliases):
            hits.add(entity)
    return hits


def split_desc_status(desc: str) -> Tuple[str, str]:
    m = re.search(r"\(([^()]+)\)\s*$", desc)
    if not m:
        return desc.strip(), ""
    status = m.group(1).strip()
    capability = desc[: m.start()].strip()
    return capability, status


def ics_item_from_tspc_name(name: str) -> str:
    m = re.match(r"^TSPC_[A-Z0-9]+_(.+)$", name)
    if not m:
        return ""
    suffix = m.group(1)
    parts = suffix.split("_", 1)
    if len(parts) == 2:
        return f"{parts[0]}/{parts[1]}"
    return suffix


def parse_pqw6(path: Path):
    root = ET.parse(path).getroot()
    lines = read_lines(path)

    if root.tag.startswith("{"):
        ns_uri = root.tag[1:].split("}")[0]
        q = lambda t: f"{{{ns_uri}}}{t}"
    else:
        q = lambda t: t

    projects = {}
    for pi in root.findall(f".//{q('PROJECT_INFORMATION')}"):
        name = pi.attrib.get("NAME", "")
        if name:
            projects[name] = pi

    project_start_lines = {
        name: find_first_line_containing(path, f'<PROJECT_INFORMATION NAME="{name}"')
        for name in projects.keys()
    }

    def find_from(needle: str, start_line: int) -> Optional[int]:
        start = max(1, start_line)
        for i in range(start - 1, len(lines)):
            if needle in lines[i]:
                return i + 1
        return None

    def pics_rows(project_name: str):
        pi = projects.get(project_name)
        rows = []
        if pi is None:
            return rows

        cursor = project_start_lines.get(project_name) or 1
        for row in pi.findall(f".//{q('PICS')}/{q('Rows')}/{q('Row')}"):
            name = (row.findtext(q("Name")) or "").strip()
            desc = (row.findtext(q("Description")) or "").strip()
            value = (row.findtext(q("Value")) or "").strip()
            mandatory = (row.findtext(q("Mandatory")) or "").strip()
            if not name:
                continue

            name_line = find_from(f"<Name>{name}</Name>", cursor)
            if name_line is not None:
                cursor = name_line + 1

            desc_line = None
            if desc:
                desc_start = name_line if name_line is not None else cursor
                desc_line = find_from(f"<Description>{desc}</Description>", desc_start)
                if desc_line is not None:
                    cursor = desc_line + 1

            rows.append(
                {
                    "name": name,
                    "desc": desc,
                    "value": value,
                    "mandatory": mandatory,
                    "source": {
                        "file": str(path),
                        "name_line": name_line,
                        "desc_line": desc_line,
                    },
                }
            )
        return rows

    data = {
        "BAS": pics_rows("BAS"),
        "DIS": pics_rows("DIS"),
        "HRS": pics_rows("HRS"),
        "IOPT": pics_rows("IOPT"),
        "_project_lines": {
            "BAS": project_start_lines.get("BAS"),
            "DIS": project_start_lines.get("DIS"),
            "HRS": project_start_lines.get("HRS"),
            "IOPT": project_start_lines.get("IOPT"),
            "HRC": find_first_line_containing(path, '<PROJECT_INFORMATION NAME="HRC"'),
        },
        "_project_names": sorted(projects.keys()),
    }
    return data


NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_sheet_rows(xlsx_path: Path, sheet_name: str) -> List[Tuple[int, Dict[str, str]]]:
    with zipfile.ZipFile(xlsx_path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid2target = {
            r.attrib["Id"]: r.attrib["Target"]
            for r in rels.findall(
                ".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
            )
        }

        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in sst.findall("a:si", NS):
                shared.append("".join((t.text or "") for t in si.findall(".//a:t", NS)))

        rid = None
        for s in wb.findall(".//a:sheets/a:sheet", NS):
            if s.attrib["name"] == sheet_name:
                rid = s.attrib[
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                ]
                break

        if rid is None:
            raise RuntimeError(f"Sheet {sheet_name} not found in {xlsx_path}")

        tgt = rid2target[rid]
        xml_path = "xl/" + tgt if not tgt.startswith("xl/") else tgt
        sh = ET.fromstring(z.read(xml_path))

        out = []
        for row in sh.findall(".//a:sheetData/a:row", NS):
            rownum = int(row.attrib.get("r", "0"))
            vals: Dict[str, str] = {}
            for c in row.findall("a:c", NS):
                ref = c.attrib["r"]
                col = "".join(ch for ch in ref if ch.isalpha())
                v = c.find("a:v", NS)
                if v is None:
                    continue
                raw = v.text or ""
                typ = c.attrib.get("t")
                if typ == "s" and raw.isdigit() and int(raw) < len(shared):
                    val = shared[int(raw)]
                else:
                    val = raw
                vals[col] = val
            out.append((rownum, vals))
        return out


def extract_tc(rows: List[Tuple[int, Dict[str, str]]], prefix: str, xlsx_path: Path, sheet_name: str):
    out = []
    for rownum, vals in rows:
        tcid = vals.get("A", "")
        if not tcid.startswith(prefix):
            continue
        desc = vals.get("B", "")
        if "No longer used" in desc:
            continue
        category = vals.get("H") or vals.get("D") or ""
        active_date = vals.get("I") or vals.get("E") or ""
        out.append(
            {
                "tcid": tcid,
                "desc": desc,
                "category": category,
                "active_date": active_date,
                "source": {
                    "file": str(xlsx_path),
                    "sheet": sheet_name,
                    "row": rownum,
                    "columns": "A,B,D/H,E/I",
                },
            }
        )
    return out


def find_ics_refs() -> Dict[str, List[Dict[str, Optional[str]]]]:
    needles = {
        "BAS": [
            "Battery Service                                                  [1] 2         M",
            "Battery Service, Multiple Instances",
            "Mandatory IF BAS 1/1 “Service supported over BR/EDR”",
            "Optional IF BAS 2/7 “Battery Level Status",
        ],
        "DIS": [
            "Device Information Service                                       [1] 2        M",
            "Manufacturer Name String Characteristic",
            "Mandatory IF DIS 1/1 “Service supported over BR/EDR”",
            "Mandatory IF DIS 0/1 “DIS v1.1”, otherwise Optional.",
        ],
        "HRS": [
            "Heart Rate Service                                                [1] 2            M",
            "Support for Heart Rate Measurement Values in UINT16 format",
            "Mandatory IF HRS 2/5 “Energy Expended feature”, otherwise Excluded.",
        ],
        "HOGP": [
            "HID Service                               [1] 3.1        M",
            "Battery Service                           [1] 3.2        M",
            "Device Information Service                [1] 3.3        M",
            "HID ISO Service                           [9] 3.5        C.1",
        ],
    }
    refs = {}
    for doc_key, needle_list in needles.items():
        doc_refs = []
        for needle in needle_list:
            ln = find_line_in_pdf(ICS_PDF[doc_key], needle)
            doc_refs.append({"needle": needle, "line": ln, "file": str(ICS_PDF[doc_key])})
        refs[doc_key] = doc_refs
    return refs


def find_ics_line_for_capability(
    capability: str, docs: List[str], item: str = "", status: str = ""
) -> Tuple[Optional[str], Optional[int]]:
    cap_norm = normalize_text(capability)
    if not cap_norm:
        return None, None

    best: Tuple[int, int, Optional[str]] = (-1, 10**9, None)
    for doc in docs:
        lines = read_pdf_lines(ICS_PDF[doc])
        for i, line in enumerate(lines, start=1):
            ln_norm = normalize_text(line)
            if cap_norm not in ln_norm:
                continue
            score = 0
            if re.match(r"^\s*\d+\s+", line):
                score += 10
            if item:
                major = item.split("/", 1)[0].lower()
                if re.match(rf"^\s*{re.escape(major)}\s+", ln_norm):
                    score += 5
            if status and status.lower() in ln_norm:
                score += 3
            if "mandatory if" in ln_norm or "optional if" in ln_norm:
                score -= 2
            if score > best[0] or (score == best[0] and i < best[1]):
                best = (score, i, doc)
    if best[2] is None:
        return None, None
    return best[2], best[1]


def build_tspc_entries(rows: List[Dict[str, str]], profile: str) -> List[Dict[str, str]]:
    out = []
    for r in rows:
        capability, status = split_desc_status(r["desc"])
        item = ics_item_from_tspc_name(r["name"])
        if profile in ("DIS", "BAS", "HRS"):
            docs = [profile]
        else:
            docs = ["HOGP"]
        doc_key, doc_line = find_ics_line_for_capability(capability, docs, item=item, status=status)
        out.append(
            {
                "name": r["name"],
                "item": item,
                "capability": capability,
                "status": status,
                "mandatory": r["mandatory"],
                "value": r["value"],
                "source": r["source"],
                "ics_doc_key": doc_key,
                "ics_line": doc_line,
            }
        )
    return out


def split_mand_opt_cond(rows: List[Dict[str, str]]):
    mandatory = [r for r in rows if r["mandatory"] == "TRUE"]
    optional = [r for r in rows if r["status"].startswith("O")]
    conditional = [r for r in rows if r["mandatory"] == "FALSE" and not r["status"].startswith("O")]
    return mandatory, optional, conditional


def category_counts(tcs: List[Dict[str, str]]) -> Dict[str, int]:
    c = Counter(t["category"] for t in tcs)
    return dict(sorted(c.items()))


def source_ref(file: str, line: Optional[int]) -> Dict[str, Optional[str]]:
    return {"file": file, "line": line}


def iter_source_files(obj):
    if isinstance(obj, dict):
        f = obj.get("file")
        if isinstance(f, str):
            yield f
        for value in obj.values():
            yield from iter_source_files(value)
        return
    if isinstance(obj, list):
        for value in obj:
            yield from iter_source_files(value)


def enforce_workspace_source_consistency(data: Dict) -> None:
    workspace_file = str(WORKSPACE_PQW6).replace("\\", "/")
    if not workspace_file.endswith(EXPECTED_WORKSPACE_SUFFIX):
        raise ValueError(f"WORKSPACE_PQW6 must point to zephyr-master.pqw6, got: {workspace_file}")

    for src in iter_source_files(data):
        normalized = str(src).replace("\\", "/")
        if normalized.lower().endswith(".pqw6") and normalized != workspace_file:
            raise ValueError(
                "Found pqw6 source that is not zephyr-master.pqw6: "
                f"{normalized} (expected {workspace_file})"
            )


def build_official_sources(profile_sources: Dict[str, Dict[str, Path]]) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for profile in ("DIS", "BAS", "HRS", "HID"):
        src = profile_sources[profile]
        out[profile] = {
            "profile_dir": str(src["dir"]),
            "spec": {
                "file": str(src["spec"]),
                "meta": extract_pdf_metadata(src["spec"]),
            },
            "ics": {
                "file": str(src["ics"]),
                "meta": extract_pdf_metadata(src["ics"]),
            },
            "ts": {
                "file": str(src["ts"]),
                "meta": extract_pdf_metadata(src["ts"]),
            },
            "tcrl": {
                "dir": str(src["tcrl_dir"]),
                "gatt": str(src["tcrl_gatt"]),
                "traditional": str(src["tcrl_trad"]),
                "iopt": str(src["tcrl_iopt"]),
            },
        }
    return out


def summarize_prefixes(tc_rows: List[Dict[str, str]]) -> List[str]:
    prefixes: Set[str] = set()
    for row in tc_rows:
        tcid = row.get("tcid", "")
        if "/" in tcid:
            prefixes.add(tcid.split("/", 1)[0] + "/")
    return sorted(prefixes)


def find_official_tcid_anchor(xlsx_path: Path, sheet_name: str, prefix: str) -> Dict:
    try:
        rows = read_sheet_rows(xlsx_path, sheet_name)
    except Exception as exc:
        return {
            "file": str(xlsx_path),
            "sheet": sheet_name,
            "row": None,
            "note": f"לא ניתן לחלץ שורת TCID רשמית: {exc}",
        }

    for rownum, vals in rows:
        tcid = vals.get("A", "")
        desc = vals.get("B", "")
        if not tcid.startswith(prefix):
            continue
        if "No longer used" in desc:
            continue
        return {
            "file": str(xlsx_path),
            "sheet": sheet_name,
            "row": rownum,
            "note": f"TCID רשמי לדוגמה: {tcid}",
        }

    return {
        "file": str(xlsx_path),
        "sheet": sheet_name,
        "row": None,
        "note": f"לא נמצאה שורת TCID עם prefix {prefix}",
    }


def bucket_for_tspc_row(row: Dict[str, str]) -> str:
    if row.get("mandatory") == "TRUE":
        return "mandatory"
    if (row.get("status") or "").startswith("O"):
        return "optional"
    return "conditional"


def find_best_line_in_pdf(path: Path, needles: List[str]) -> Optional[int]:
    for needle in needles:
        if not needle:
            continue
        n = needle.strip()
        if len(n) < 3:
            continue
        line = find_line_in_pdf(path, n)
        if line is not None:
            return line
    return None


def find_tcmt_section_bounds(lines: List[str]) -> Tuple[Optional[int], Optional[int]]:
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None
    for idx, raw in enumerate(lines):
        compact = collapse_ws(raw)
        if not compact:
            continue
        if start_idx is None and TCMT_SECTION_RE.match(compact):
            start_idx = idx
            continue
        if start_idx is not None and REVISION_SECTION_RE.match(compact):
            end_idx = idx
            break
    return start_idx, end_idx


def item_expr_expects_continuation(item_expr: str) -> bool:
    tail = collapse_ws(item_expr).upper()
    if not tail:
        return False
    if tail.endswith("("):
        return True
    for suffix in (" AND", " OR", " NOT", " AND NOT", " OR NOT"):
        if tail.endswith(suffix):
            return True
    return False


def looks_like_item_start(fragment: str, prefix: str) -> bool:
    up = collapse_ws(fragment).upper()
    return bool(re.match(rf"^{re.escape(prefix.upper())}\s+\d", up))


def looks_like_item_fragment(fragment: str, prefix: str) -> bool:
    up = collapse_ws(fragment).upper()
    if not up:
        return False
    if looks_like_item_start(up, prefix):
        return True
    if re.match(r"^(AND|OR|NOT)\b", up):
        return True
    if re.match(r"^\d+[A-Z]?/[0-9A-Z]+\)?$", up):
        return True
    return False


def extract_item_refs_from_expression(item_expr: str, prefix: str) -> List[str]:
    expr = collapse_ws(item_expr).upper()
    if not expr:
        return []

    pref = re.escape(prefix.upper())
    refs: List[str] = []
    seen: Set[str] = set()

    for m in re.finditer(rf"\b{pref}\s+(\d+[A-Z]?/[0-9A-Z]+)\b", expr):
        ref = normalize_ics_item(m.group(1))
        if ref and ref not in seen:
            seen.add(ref)
            refs.append(ref)

    for m in re.finditer(r"\b(\d+[A-Z]?/[0-9A-Z]+)\b", expr):
        ref = normalize_ics_item(m.group(1))
        if ref and ref not in seen:
            seen.add(ref)
            refs.append(ref)

    return refs


def evaluate_tcmt_expression(
    item_expr: str,
    prefix: str,
    value_by_item: Dict[str, Optional[bool]],
) -> Dict[str, Any]:
    expr = collapse_ws(item_expr).upper()
    if not expr:
        return {"result": "unknown", "items": []}

    pref = re.escape(prefix.upper())
    token_re = re.compile(
        rf"\b{pref}\s+\d+[A-Z]?/[0-9A-Z]+\b|\b\d+[A-Z]?/[0-9A-Z]+\b|\bAND\b|\bOR\b|\bNOT\b|\(|\)",
        re.IGNORECASE,
    )
    tokens = [collapse_ws(m.group(0)).upper() for m in token_re.finditer(expr)]
    if not tokens:
        return {"result": "unknown", "items": []}

    cursor = 0
    seen_refs: Dict[str, Optional[bool]] = {}

    def ref_from_token(token: str) -> str:
        token_up = token.upper()
        m = re.match(rf"^{pref}\s+(.+)$", token_up)
        raw = m.group(1) if m else token_up
        return normalize_ics_item(raw)

    def parse_atom() -> Optional[bool]:
        nonlocal cursor
        if cursor >= len(tokens):
            return None
        token = tokens[cursor]
        if token == "(":
            cursor += 1
            value = parse_or()
            if cursor < len(tokens) and tokens[cursor] == ")":
                cursor += 1
            return value
        if token in {"AND", "OR", "NOT", ")"}:
            cursor += 1
            return None

        cursor += 1
        ref = ref_from_token(token)
        value = value_by_item.get(ref)
        seen_refs[ref] = value
        return value

    def parse_not() -> Optional[bool]:
        nonlocal cursor
        if cursor < len(tokens) and tokens[cursor] == "NOT":
            cursor += 1
            return tri_not(parse_not())
        return parse_atom()

    def parse_and() -> Optional[bool]:
        nonlocal cursor
        left = parse_not()
        while cursor < len(tokens) and tokens[cursor] == "AND":
            cursor += 1
            right = parse_not()
            left = tri_and(left, right)
        return left

    def parse_or() -> Optional[bool]:
        nonlocal cursor
        left = parse_and()
        while cursor < len(tokens) and tokens[cursor] == "OR":
            cursor += 1
            right = parse_and()
            left = tri_or(left, right)
        return left

    result_value = parse_or()
    if cursor < len(tokens):
        result_value = None

    if result_value is True:
        result = "true"
    elif result_value is False:
        result = "false"
    else:
        result = "unknown"

    items = []
    for ref in sorted(seen_refs.keys()):
        value = seen_refs[ref]
        value_label = "TRUE" if value is True else "FALSE" if value is False else "UNKNOWN"
        items.append({"item": ref, "value": value_label})

    return {"result": result, "items": items}


def parse_tcmt_rows_from_ts(
    profile: str,
    ts_file: Path,
    value_by_item: Dict[str, Optional[bool]],
) -> Dict[str, Any]:
    lines = read_pdf_lines(ts_file)
    start_idx, end_idx = find_tcmt_section_bounds(lines)
    if start_idx is None:
        return {"line_start": None, "line_end": None, "rows": []}
    if end_idx is None:
        end_idx = len(lines)

    prefix = profile_tcid_prefix(profile)
    feature_start: Optional[int] = None
    test_start: Optional[int] = None
    rows: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    def init_current(line_no: int) -> Dict[str, Any]:
        return {"line_start": line_no, "line_end": line_no, "item_parts": [], "feature_parts": [], "tcids": []}

    def append_unique_tcids(target: List[str], tcids: List[str]) -> None:
        seen = set(target)
        for tcid in tcids:
            if tcid in seen:
                continue
            seen.add(tcid)
            target.append(tcid)

    def finalize_current() -> None:
        nonlocal current
        if not current:
            return

        item_expr = collapse_ws(" ".join(current["item_parts"]))
        feature = collapse_ws(" ".join(current["feature_parts"]))
        tcids = [tcid for tcid in current["tcids"] if is_profile_tcid(profile, tcid)]
        if tcids:
            item_refs = extract_item_refs_from_expression(item_expr, prefix)
            rows.append(
                {
                    "item_expression": item_expr,
                    "item_refs": item_refs,
                    "feature": feature,
                    "tcids": tcids,
                    "expression_eval": evaluate_tcmt_expression(item_expr, prefix, value_by_item),
                    "source": {
                        "file": str(ts_file),
                        "line_start": current["line_start"],
                        "line_end": current["line_end"],
                        "note": "שורת TCMT מתוך TS",
                    },
                }
            )
        current = None

    for idx in range(start_idx + 1, end_idx):
        line_no = idx + 1
        raw_line = lines[idx].replace("\x0c", "")
        stripped = raw_line.strip()
        if not stripped:
            continue

        compact = collapse_ws(stripped)
        compact_lower = compact.lower()
        if compact_lower.startswith("table 5.1"):
            continue
        if compact_lower.startswith("bluetooth sig proprietary"):
            continue
        if compact_lower.startswith("page "):
            continue
        if compact_lower.startswith("item feature test case"):
            continue

        if "Item" in raw_line and "Feature" in raw_line and "Test Case" in raw_line:
            feature_start = raw_line.find("Feature")
            test_start = raw_line.find("Test Case")
            continue

        item_part = ""
        feature_part = ""
        test_part = ""

        if (
            feature_start is not None
            and test_start is not None
            and feature_start >= 0
            and test_start > feature_start
        ):
            padded = raw_line
            if len(padded) < test_start:
                padded += " " * (test_start - len(padded))
            item_part = padded[:feature_start].strip()
            feature_part = padded[feature_start:test_start].strip()
            test_part = padded[test_start:].strip()
        else:
            parts = re.split(r"\s{2,}", stripped)
            if len(parts) >= 3:
                item_part = parts[0].strip()
                feature_part = parts[1].strip()
                test_part = " ".join(parts[2:]).strip()
            elif len(parts) == 2:
                item_part = parts[0].strip()
                test_part = parts[1].strip()
            else:
                feature_part = parts[0].strip()

        tcids = [tcid for tcid in TCID_PATTERN.findall(raw_line) if is_profile_tcid(profile, tcid)]

        has_payload = bool(item_part or feature_part or test_part or tcids)
        if not has_payload:
            continue

        if current is None:
            current = init_current(line_no)
        else:
            should_start_new = (
                item_part
                and looks_like_item_start(item_part, prefix)
                and current["tcids"]
                and not item_expr_expects_continuation(" ".join(current["item_parts"]))
            )
            if should_start_new:
                finalize_current()
                current = init_current(line_no)

        if item_part and item_part.lower() not in {"item"}:
            current["item_parts"].append(item_part)
        if feature_part and feature_part.lower() not in {"feature"}:
            current["feature_parts"].append(feature_part)

        # Some TCMT rows continue item expression on a dedicated line without tcids.
        if not tcids and test_part and looks_like_item_fragment(test_part, prefix):
            current["item_parts"].append(test_part)
        elif test_part and not tcids and test_part.lower() not in {"test case(s)"}:
            current["feature_parts"].append(test_part)

        append_unique_tcids(current["tcids"], tcids)
        current["line_end"] = line_no

    finalize_current()
    return {
        "line_start": start_idx + 1,
        "line_end": end_idx if end_idx is not None else len(lines),
        "rows": rows,
    }


def extract_ts_tcid_titles(profile: str, lines: List[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for idx, raw in enumerate(lines, start=1):
        tcids = [tcid for tcid in TCID_PATTERN.findall(raw) if is_profile_tcid(profile, tcid)]
        if not tcids:
            continue
        m = re.search(r"\[([^\]]+)\]", raw)
        if not m:
            continue
        title = collapse_ws(m.group(1))
        if not title:
            continue
        for tcid in tcids:
            if tcid in out:
                continue
            out[tcid] = {
                "title": title,
                "source": {"file": "", "line": idx, "note": "כותרת טסט מתוך TS"},
            }
    return out


def extract_ts_test_groups(lines: List[str]) -> List[str]:
    start_idx = None
    for idx, raw in enumerate(lines):
        compact = collapse_ws(raw).lower()
        if compact.startswith("3.3 test groups") or compact == "test groups":
            start_idx = idx
            break

    if start_idx is None:
        return []

    groups: List[str] = []
    seen: Set[str] = set()
    for idx in range(start_idx + 1, min(len(lines), start_idx + 120)):
        compact = collapse_ws(lines[idx])
        if not compact:
            continue
        compact_lower = compact.lower()
        if re.match(r"^4(\.|\s|$)", compact_lower):
            break
        if compact_lower.startswith("the following test groups have been defined"):
            continue
        if compact_lower.startswith("test groups"):
            continue
        candidate = compact.strip("•- ").strip()
        if not candidate or len(candidate) < 3:
            continue
        if "/" in candidate and TCID_PATTERN.search(candidate):
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        groups.append(candidate)
    return groups


def extract_ts_tcid_convention(lines: List[str], prefix: str) -> Dict[str, Any]:
    heading_line = None
    for idx, raw in enumerate(lines, start=1):
        compact = collapse_ws(raw).lower()
        if "test case identification convention" in compact or "test case identification conventions" in compact:
            heading_line = idx
            break

    example_tcid = None
    if heading_line is not None:
        scan_end = min(len(lines), heading_line + 120)
        for idx in range(heading_line - 1, scan_end):
            for tcid in TCID_PATTERN.findall(lines[idx]):
                if tcid.startswith(f"{prefix}/"):
                    example_tcid = tcid
                    break
            if example_tcid:
                break

    return {
        "heading_line": heading_line,
        "example_tcid": example_tcid,
        "format_hint": "<spec>/<role>/<class>/<feature>/<capability>/<BV|BI>-<nn>-<variant>",
    }


def extract_ts_revision_notes(lines: List[str]) -> List[Dict[str, Any]]:
    revision_idx = None
    for idx, raw in enumerate(lines):
        if collapse_ws(raw).lower() == "revision history":
            revision_idx = idx
            break

    if revision_idx is None:
        return []

    notes = []
    for idx in range(revision_idx + 1, min(len(lines), revision_idx + 260)):
        compact = collapse_ws(lines[idx])
        if not compact:
            continue
        if "tse " not in compact.lower():
            continue
        notes.append({"line": idx + 1, "text": compact})
        if len(notes) >= 12:
            break
    return notes


def build_ts_value_index(tspc_rows: List[Dict[str, Any]]) -> Dict[str, Optional[bool]]:
    out: Dict[str, Optional[bool]] = {}
    for row in tspc_rows:
        item = normalize_ics_item(row.get("item", ""))
        if not item:
            continue
        value_raw = str(row.get("value", "")).upper()
        if value_raw == "TRUE":
            out[item] = True
        elif value_raw == "FALSE":
            out[item] = False
        else:
            out[item] = None
    return out


def extract_ts_profile_data(profile: str, ts_file: Path, tspc_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    lines = read_pdf_lines(ts_file)
    prefix = profile_tcid_prefix(profile)
    value_by_item = build_ts_value_index(tspc_rows)
    tcmt = parse_tcmt_rows_from_ts(profile, ts_file, value_by_item)
    tcid_titles = extract_ts_tcid_titles(profile, lines)

    tcmt_tcid_set: Set[str] = set()
    rows_with_unknown_eval = 0
    for row in tcmt["rows"]:
        tcmt_tcid_set.update(row.get("tcids", []))
        if (row.get("expression_eval") or {}).get("result") == "unknown":
            rows_with_unknown_eval += 1

    return {
        "profile": profile,
        "source": {"file": str(ts_file)},
        "meta": extract_pdf_metadata(ts_file),
        "test_groups": extract_ts_test_groups(lines),
        "tcid_convention": extract_ts_tcid_convention(lines, prefix),
        "revision_notes": extract_ts_revision_notes(lines),
        "tcid_titles": tcid_titles,
        "tcmt": {
            "line_start": tcmt.get("line_start"),
            "line_end": tcmt.get("line_end"),
            "row_count": len(tcmt.get("rows", [])),
            "mapped_tcid_count": len(tcmt_tcid_set),
            "rows_with_unknown_eval": rows_with_unknown_eval,
            "rows": tcmt.get("rows", []),
        },
    }


def ts_public_summary(ts_data: Dict[str, Any]) -> Dict[str, Any]:
    tcmt = ts_data.get("tcmt", {})
    return {
        "profile": ts_data.get("profile"),
        "source": ts_data.get("source", {}),
        "meta": ts_data.get("meta", {}),
        "test_groups": ts_data.get("test_groups", []),
        "tcid_convention": ts_data.get("tcid_convention", {}),
        "revision_notes": ts_data.get("revision_notes", []),
        "tcid_titles_count": len(ts_data.get("tcid_titles", {})),
        "tcmt": {
            "line_start": tcmt.get("line_start"),
            "line_end": tcmt.get("line_end"),
            "row_count": tcmt.get("row_count", 0),
            "mapped_tcid_count": tcmt.get("mapped_tcid_count", 0),
            "rows_with_unknown_eval": tcmt.get("rows_with_unknown_eval", 0),
        },
    }


def apply_ts_titles_to_tc_rows(tc_rows: List[Dict[str, Any]], ts_tcid_titles: Dict[str, Dict[str, Any]], ts_file: Path) -> None:
    for row in tc_rows:
        tcid = row.get("tcid")
        if not tcid:
            continue
        title_entry = ts_tcid_titles.get(tcid)
        if not title_entry:
            continue
        row["ts_title"] = title_entry.get("title")
        source = dict(title_entry.get("source") or {})
        source["file"] = str(ts_file)
        row["ts_title_source"] = source


def score_tspc_to_tcid(tspc_row: Dict, tc_row: Dict) -> Tuple[float, Dict]:
    tspc_text = " ".join(
        [
            tspc_row.get("name", ""),
            tspc_row.get("capability", ""),
            tspc_row.get("item", ""),
            tspc_row.get("status", ""),
        ]
    )
    tc_text = " ".join([tc_row.get("tcid", ""), tc_row.get("desc", "")])

    tspc_tokens = tokenize_text(tspc_text)
    tc_tokens = tokenize_text(tc_text)
    overlap = tspc_tokens.intersection(tc_tokens)
    min_size = max(1, min(len(tspc_tokens), len(tc_tokens)))
    overlap_ratio = len(overlap) / min_size
    score = overlap_ratio * 100.0

    tspc_actions = collect_action_hits(tspc_text)
    tc_actions = collect_action_hits(tc_text)
    action_matches = tspc_actions.intersection(tc_actions)
    score += float(len(action_matches) * 12)

    tspc_entities = collect_entity_hits(tspc_tokens)
    tc_entities = collect_entity_hits(tc_tokens)
    entity_matches = tspc_entities.intersection(tc_entities)
    score += float(len(entity_matches) * 10)

    tspc_capability = normalize_text(tspc_row.get("capability", ""))
    tc_desc = normalize_text(tc_row.get("desc", ""))
    if tspc_capability and tspc_capability in tc_desc:
        score += 35.0

    if "no longer used" in tc_desc:
        score -= 80.0

    return score, {
        "overlap_tokens": sorted(overlap),
        "action_matches": sorted(action_matches),
        "entity_matches": sorted(entity_matches),
        "overlap_ratio": round(overlap_ratio, 4),
    }


def confidence_from_score(score: float) -> str:
    if score >= 80:
        return "High"
    if score >= 55:
        return "Medium"
    if score >= 35:
        return "Low"
    return "Unmapped"


def confidence_rank(confidence: str) -> int:
    if confidence == "High":
        return 3
    if confidence == "Medium":
        return 2
    if confidence == "Low":
        return 1
    return 0


def condition_hint_from_mapping_row(row: Dict) -> str:
    value = (row.get("value") or "").upper()
    mandatory = (row.get("mandatory") or "").upper()
    status = (row.get("tspc_status") or "").upper()
    bucket = row.get("bucket") or ""
    if value != "TRUE":
        return "inactive"
    if mandatory == "TRUE":
        return "active_required"
    if bucket == "conditional" or status.startswith("C"):
        return "conditional"
    return "active_optional"


def runtime_signal_from_conditions(conditions: List[Dict]) -> str:
    if not conditions:
        return "unknown"

    hints = {condition.get("condition_hint") for condition in conditions}
    if "active_required" in hints:
        return "likely_active_mandatory"
    if hints.intersection({"active_optional", "conditional"}):
        return "likely_active_optional"
    if hints == {"inactive"}:
        return "likely_inactive"
    return "unknown"


def build_logic_eval_reason(condition_eval: Dict[str, Any], values: List[Dict[str, str]]) -> str:
    parts = []
    for entry in values or []:
        item = str(entry.get("item") or "").strip()
        value = str(entry.get("value") or "").strip().upper() or "UNKNOWN"
        if not item:
            continue
        parts.append(f"{item}={value}")

    state = str((condition_eval or {}).get("result") or "unknown").lower()
    values_text = ", ".join(parts) if parts else "ללא ערכי ICS זמינים"
    if state == "true":
        return f"ערכי ICS: {values_text}. לכן התנאי הלוגי מתקיים."
    if state == "false":
        return f"ערכי ICS: {values_text}. לכן התנאי הלוגי לא מתקיים."
    return f"ערכי ICS: {values_text}. לא ניתן להכריע את התנאי הלוגי בצורה ודאית."


def build_condition_plain_text(condition: Dict[str, Any]) -> str:
    capability = str(condition.get("tspc_capability") or condition.get("tspc_name") or "יכולת לא מזוהה")
    mandatory = str(condition.get("mandatory") or "").upper()
    value = str(condition.get("value") or "").upper()
    status = str(condition.get("tspc_status") or "").upper()
    hint = str(condition.get("condition_hint") or "unknown")
    logic_eval = str(condition.get("logic_eval") or "unknown")
    logic_reason = str(condition.get("logic_eval_reason_he") or "").strip()

    value_text = "פעיל (TRUE)" if value == "TRUE" else "כבוי (FALSE)" if value == "FALSE" else "ללא ערך ברור"
    mandatory_text = "חובה בקונפיגורציה" if mandatory == "TRUE" else "לא חובה בקונפיגורציה"
    if status.startswith("M"):
        status_text = "חובה לפי התקן (Mandatory)"
    elif status.startswith("O"):
        status_text = "אופציונלי לפי התקן (Optional)"
    elif status.startswith("C"):
        status_text = "תלוי-תנאי לפי התקן (Conditional)"
    else:
        status_text = "סטטוס תקני לא מזוהה"

    if hint == "active_required":
        impact = "במצב הזה הטסט צפוי להיות פעיל כחובה."
    elif hint == "active_optional":
        impact = "במצב הזה הטסט יכול להיות פעיל כאופציונלי."
    elif hint == "conditional":
        impact = "במצב הזה הטסט תלוי בתנאים נוספים (Conditional)."
    elif hint == "inactive":
        impact = "במצב הזה הטסט לרוב לא ירוץ כי התנאי כבוי."
    else:
        impact = "לא ניתן להסיק מצב ריצה חד-משמעי."

    logic_text = (
        "ביטוי TCMT: מתקיים (TRUE)"
        if logic_eval == "true"
        else "ביטוי TCMT: לא מתקיים (FALSE)"
        if logic_eval == "false"
        else "ביטוי TCMT: לא ידוע (UNKNOWN)"
    )
    suffix = f" {logic_reason}" if logic_reason else ""
    return f"{capability}: {value_text}, {mandatory_text}, {status_text}. {impact} {logic_text}.{suffix}".strip()


def build_what_tested_en_official(desc: Any, ts_title: Any) -> str:
    desc_text = str(desc or "").strip()
    ts_title_text = str(ts_title or "").strip()
    if desc_text and ts_title_text:
        return f"{desc_text} (TS: {ts_title_text})"
    if desc_text:
        return desc_text
    if ts_title_text:
        return f"TS: {ts_title_text}"
    return NO_OFFICIAL_ENGLISH_TEXT


def build_what_tested_he_verified(desc: Any, ts_title: Any) -> str:
    desc_text = str(desc or "").strip()
    ts_title_text = str(ts_title or "").strip()
    if desc_text and ts_title_text:
        return f"הטסט מאמת את התרחיש הרשמי: {desc_text}. כותרת TS רשמית: {ts_title_text}."
    if desc_text:
        return f"הטסט מאמת את התרחיש הרשמי: {desc_text}."
    if ts_title_text:
        return f"הטסט מאמת לפי כותרת TS רשמית: {ts_title_text}."
    return "אין תיאור טסט רשמי זמין במקורות."


def collect_what_tested_sources(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    sources: List[Dict[str, Any]] = []
    source = row.get("source") or {}
    if source.get("file"):
        sources.append(
            {
                "file": source.get("file"),
                "sheet": source.get("sheet"),
                "row": source.get("row"),
                "columns": source.get("columns"),
                "line": source.get("line"),
                "note": "תיאור טסט מתוך TCRL",
            }
        )
    ts_source = row.get("ts_title_source") or {}
    if ts_source.get("file"):
        sources.append(
            {
                "file": ts_source.get("file"),
                "line": ts_source.get("line"),
                "note": ts_source.get("note") or "כותרת טסט מתוך TS",
            }
        )
    unique: Dict[str, Dict[str, Any]] = {}
    for src in sources:
        key = "|".join(
            [
                str(src.get("file") or ""),
                str(src.get("sheet") or ""),
                str(src.get("row") or ""),
                str(src.get("line") or ""),
                str(src.get("columns") or ""),
                str(src.get("note") or ""),
            ]
        )
        unique[key] = src
    return list(unique.values())


def build_tcid_summary_fields(row: Dict[str, Any]) -> Dict[str, Any]:
    conditions = row.get("conditions") or []
    runtime_signal = str(row.get("runtime_signal") or "unknown")
    runtime_active = row.get("runtime_active")
    desc = str(row.get("desc") or "").strip()
    ts_title = str(row.get("ts_title") or "").strip()

    if runtime_active is True:
        status = "expected_active"
        status_reason = "נמצא פעיל גם ב-Runtime Snapshot וגם לפי תנאי המיפוי."
    elif runtime_active is False and runtime_signal == "likely_inactive":
        status = "expected_inactive"
        status_reason = "ב-Runtime Snapshot הטסט לא הופיע, וגם התנאים מצביעים על מצב לא פעיל."
    elif runtime_signal == "likely_active_mandatory":
        status = "expected_active"
        status_reason = "לפחות תנאי חובה אחד פעיל (Mandatory + TRUE), ולכן הטסט צפוי להיות פעיל."
    elif runtime_signal == "likely_active_optional":
        status = "maybe_active"
        status_reason = "נמצאו תנאים אופציונליים/תלויי-תנאי פעילים, ולכן הטסט עשוי להיות פעיל."
    elif runtime_signal == "likely_inactive":
        status = "expected_inactive"
        status_reason = "כל התנאים המשויכים מצביעים על מצב כבוי או לא מתקיים."
    else:
        status = "unknown"
        status_reason = "אין מספיק מידע תנאי כדי להכריע מצב הפעלה."

    what_tested_he = build_what_tested_he_verified(desc, ts_title)
    what_tested_en = build_what_tested_en_official(desc, ts_title)
    what_tested_sources = collect_what_tested_sources(row)

    if not conditions:
        why_relevant = "לא נמצא תנאי TCMT משויך ל-TCID זה."
    else:
        primary = str(conditions[0].get("plain_condition_he") or "").strip()
        if len(conditions) == 1:
            why_relevant = primary or "נמצא תנאי יחיד לקביעת הרלוונטיות."
        else:
            why_relevant = f"{primary} קיימות עוד {len(conditions) - 1} אפשרויות הפעלה חלופיות (OR).".strip()

    badges = []
    flags = row.get("bucket_flags") or {}
    if flags.get("mandatory"):
        badges.append("חובה")
    if flags.get("optional"):
        badges.append("אופציונלי")
    if flags.get("conditional"):
        badges.append("תלוי-תנאי")

    logic_values = {str(c.get("logic_eval") or "unknown") for c in conditions}
    if "true" in logic_values:
        badges.append("TCMT TRUE")
    elif logic_values == {"false"} and conditions:
        badges.append("TCMT FALSE")
    else:
        badges.append("TCMT UNKNOWN")

    if runtime_active is True:
        badges.append("Runtime Active")
    elif runtime_active is False:
        badges.append("Runtime Inactive")

    return {
        "summary_what_tested_he": what_tested_he,
        "summary_why_relevant_he": why_relevant,
        "summary_status": status,
        "summary_status_reason_he": status_reason,
        "summary_badges": badges,
        "what_tested_he_verified": what_tested_he,
        "what_tested_en_official": what_tested_en,
        "what_tested_sources": what_tested_sources,
        "translation_quality": "verified_from_mapping",
    }


def mapping_summary_template() -> Dict[str, int]:
    return {
        "tspc_count": 0,
        "mapped_tspc_count": 0,
        "unmapped_tspc_count": 0,
        "mapped_tcid_count": 0,
        "high_count": 0,
        "medium_count": 0,
        "low_count": 0,
    }


def build_tspc_tcid_mapping(
    profile: str,
    tspc_rows: List[Dict],
    tc_rows: List[Dict],
    official_sources: Dict[str, Dict],
    ts_data: Dict[str, Any],
) -> Tuple[List[Dict], Dict]:
    profile_sources = official_sources[profile]
    ics_file = Path(profile_sources["ics"]["file"])
    ts_file = Path(profile_sources["ts"]["file"])
    spec_file = Path(profile_sources["spec"]["file"])

    tc_index = {tc.get("tcid", ""): tc for tc in tc_rows if tc.get("tcid")}
    tcmt_rows = (ts_data.get("tcmt", {}) or {}).get("rows", []) if ts_data else []
    tcmt_by_item: Dict[str, List[Dict[str, Any]]] = {}
    for tcmt_row in tcmt_rows:
        for item_ref in tcmt_row.get("item_refs", []):
            item_norm = normalize_ics_item(item_ref)
            if not item_norm:
                continue
            tcmt_by_item.setdefault(item_norm, []).append(tcmt_row)

    result_rows: List[Dict] = []
    summary = {
        "mandatory": mapping_summary_template(),
        "optional": mapping_summary_template(),
        "conditional": mapping_summary_template(),
    }

    for idx, tspc in enumerate(tspc_rows, start=1):
        bucket = bucket_for_tspc_row(tspc)
        bucket_stats = summary[bucket]
        bucket_stats["tspc_count"] += 1

        site_src = {
            "file": tspc.get("source", {}).get("file"),
            "line": tspc.get("source", {}).get("desc_line") or tspc.get("source", {}).get("name_line"),
            "note": "שורת TSPC ב-Workspace",
        }

        needles = [tspc.get("capability", ""), tspc.get("item", "")]
        ics_line = tspc.get("ics_line") or find_best_line_in_pdf(ics_file, needles)
        ts_line = find_best_line_in_pdf(ts_file, needles)
        spec_line = find_best_line_in_pdf(spec_file, needles)

        row_evidence = [
            {
                "note": "שורת TSPC מול מסמך ICS",
                "site_source": site_src,
                "official_source": {
                    "file": str(ics_file),
                    "line": ics_line,
                    "note": "עוגן במסמך ICS",
                },
            }
        ]
        if ts_line is not None:
            row_evidence.append(
                {
                    "note": "עוגן משלים במסמך TS",
                    "site_source": site_src,
                    "official_source": {
                        "file": str(ts_file),
                        "line": ts_line,
                        "note": "התאמה תיאורית ב-TS",
                    },
                }
            )
        if spec_line is not None:
            row_evidence.append(
                {
                    "note": "עוגן משלים במסמך Spec",
                    "site_source": site_src,
                    "official_source": {
                        "file": str(spec_file),
                        "line": spec_line,
                        "note": "התאמה תיאורית ב-Spec",
                    },
                }
            )

        capability_norm = normalize_text(tspc.get("capability", ""))
        if not capability_norm or "no longer used" in capability_norm or tspc.get("name") == "TSPC_ALL":
            bucket_stats["unmapped_tspc_count"] += 1
            result_rows.append(
                {
                    "map_id": f"{profile.lower()}-{idx}",
                    "bucket": bucket,
                    "tspc_name": tspc.get("name", ""),
                    "tspc_item": tspc.get("item", ""),
                    "tspc_capability": tspc.get("capability", ""),
                    "tspc_status": tspc.get("status", ""),
                    "mandatory": tspc.get("mandatory", ""),
                    "value": tspc.get("value", ""),
                    "mapped_tcids": [],
                    "unmapped_reason": "לא בוצע מיפוי כי היכולת אינה פעילה/רלוונטית למיפוי (למשל 'No longer used' או TSPC_ALL).",
                    "confidence": "Unmapped",
                    "mapping_source": "TS_TCMT",
                    "evidence": row_evidence,
                }
            )
            continue

        item_norm = normalize_ics_item(tspc.get("item", ""))
        tcmt_matches = tcmt_by_item.get(item_norm, []) if item_norm else []
        mapped_index: Dict[str, Dict[str, Any]] = {}

        for tcmt_match in tcmt_matches:
            relation_source = tcmt_match.get("source", {}) or {}
            for tcid in tcmt_match.get("tcids", []):
                tc = tc_index.get(tcid)
                if not tc:
                    continue

                relation_evidence = {
                    "note": "קישור רשמי מתוך TS TCMT בין Item ל-TCID",
                    "site_source": site_src,
                    "official_source": {
                        "file": relation_source.get("file") or str(ts_file),
                        "line": relation_source.get("line_start"),
                        "note": "שורת TCMT במסמך TS",
                    },
                }
                tcrl_evidence = {
                    "note": "רשומת TCID מתוך TCRL רשמי",
                    "site_source": site_src,
                    "official_source": {
                        "file": tc.get("source", {}).get("file"),
                        "sheet": tc.get("source", {}).get("sheet"),
                        "row": tc.get("source", {}).get("row"),
                        "columns": tc.get("source", {}).get("columns"),
                        "note": "שורת TCID ב-TCRL",
                    },
                }

                existing = mapped_index.get(tcid)
                if existing is None:
                    mapped_index[tcid] = {
                        "tcid": tcid,
                        "desc": tc.get("desc", ""),
                        "category": tc.get("category", ""),
                        "active_date": tc.get("active_date", ""),
                        "ts_title": tc.get("ts_title", ""),
                        "ts_title_source": tc.get("ts_title_source", {}),
                        "score": 100.0,
                        "confidence": "High",
                        "score_details": {"source": "TS_TCMT", "item_refs": tcmt_match.get("item_refs", [])},
                        "mapping_source": "TS_TCMT",
                        "item_expression": tcmt_match.get("item_expression", ""),
                        "expression_eval": tcmt_match.get("expression_eval", {"result": "unknown", "items": []}),
                        "tcmt_feature": tcmt_match.get("feature", ""),
                        "tcmt_features": [tcmt_match.get("feature", "")] if tcmt_match.get("feature") else [],
                        "evidence": [relation_evidence, tcrl_evidence],
                    }
                    continue

                if tcmt_match.get("feature"):
                    if tcmt_match["feature"] not in existing["tcmt_features"]:
                        existing["tcmt_features"].append(tcmt_match["feature"])
                existing["evidence"].append(relation_evidence)
                existing["evidence"].append(tcrl_evidence)
                if tcmt_match.get("item_expression"):
                    existing["item_expression"] = tcmt_match["item_expression"]
                if tcmt_match.get("expression_eval"):
                    existing["expression_eval"] = tcmt_match["expression_eval"]

        mapped_tcids = sorted(mapped_index.values(), key=lambda x: x.get("tcid", ""))

        if mapped_tcids:
            bucket_stats["mapped_tspc_count"] += 1
            bucket_stats["mapped_tcid_count"] += len(mapped_tcids)
            bucket_stats["high_count"] += len(mapped_tcids)
        else:
            bucket_stats["unmapped_tspc_count"] += 1

        result_rows.append(
            {
                "map_id": f"{profile.lower()}-{idx}",
                "bucket": bucket,
                "tspc_name": tspc.get("name", ""),
                "tspc_item": tspc.get("item", ""),
                "tspc_capability": tspc.get("capability", ""),
                "tspc_status": tspc.get("status", ""),
                "mandatory": tspc.get("mandatory", ""),
                "value": tspc.get("value", ""),
                "mapped_tcids": mapped_tcids,
                "unmapped_reason": (
                    None
                    if mapped_tcids
                    else "לא נמצא קשר TCMT רשמי עבור Item זה במסמך TS."
                ),
                "confidence": "High" if mapped_tcids else "Unmapped",
                "mapping_source": "TS_TCMT",
                "tcmt_matches_count": len(tcmt_matches),
                "evidence": row_evidence,
            }
        )

    totals = mapping_summary_template()
    for bucket in ("mandatory", "optional", "conditional"):
        for key, value in summary[bucket].items():
            totals[key] += value
    summary["totals"] = totals
    return result_rows, summary


def tcid_mapping_summary_template() -> Dict[str, int]:
    return {
        "tcid_count": 0,
        "with_conditions_count": 0,
        "without_conditions_count": 0,
        "high_count": 0,
        "medium_count": 0,
        "low_count": 0,
        "runtime_active_count": 0,
        "likely_active_count": 0,
        "likely_inactive_count": 0,
        "unknown_count": 0,
    }


def validate_tcid_compact_fields(profile: str, rows: List[Dict[str, Any]]) -> None:
    for row in rows or []:
        if not row.get("summary_status"):
            raise ValueError(f"{profile}: row without summary_status for TCID {row.get('tcid')}")
        if not str(row.get("what_tested_he_verified") or "").strip():
            raise ValueError(f"{profile}: row without what_tested_he_verified for TCID {row.get('tcid')}")
        if not str(row.get("what_tested_en_official") or "").strip():
            raise ValueError(f"{profile}: row without what_tested_en_official for TCID {row.get('tcid')}")
        sources = row.get("what_tested_sources")
        if not isinstance(sources, list) or not any((src or {}).get("file") for src in sources):
            raise ValueError(f"{profile}: row without what_tested_sources for TCID {row.get('tcid')}")
        for condition in row.get("conditions") or []:
            if not str(condition.get("plain_condition_he") or "").strip():
                raise ValueError(
                    f"{profile}: condition without plain_condition_he for TCID {row.get('tcid')} map_id={condition.get('map_id')}"
                )


def attach_verified_fields_to_tc_rows(
    tc_rows: List[Dict[str, Any]],
    mapped_rows: List[Dict[str, Any]],
    profile: str,
    manual_hebrew: Optional[Dict[str, str]] = None,
) -> None:
    mapped_by_tcid = {str(row.get("tcid") or ""): row for row in mapped_rows or [] if row.get("tcid")}
    manual_map = manual_hebrew or {}
    for row in tc_rows or []:
        tcid = str(row.get("tcid") or "").strip()
        if not tcid:
            continue
        mapped = mapped_by_tcid.get(tcid)
        if mapped:
            row["what_tested_he_verified"] = str(mapped.get("what_tested_he_verified") or "").strip()
            row["what_tested_en_official"] = str(mapped.get("what_tested_en_official") or "").strip()
            row["what_tested_sources"] = [dict(src) for src in (mapped.get("what_tested_sources") or []) if src]
            row["translation_quality"] = "verified_from_mapping"
            continue

        manual_he = str(manual_map.get(tcid) or "").strip()
        if manual_he:
            row["what_tested_he_verified"] = manual_he
            row["what_tested_en_official"] = build_what_tested_en_official(row.get("desc"), row.get("ts_title"))
            row["what_tested_sources"] = collect_what_tested_sources(row)
            row["translation_quality"] = "verified_manual"
            continue

        row["what_tested_he_verified"] = build_what_tested_he_verified(row.get("desc"), row.get("ts_title"))
        row["what_tested_en_official"] = build_what_tested_en_official(row.get("desc"), row.get("ts_title"))
        row["what_tested_sources"] = collect_what_tested_sources(row)
        row["translation_quality"] = "verified_manual"


def validate_verified_fields_in_tc_group(group_name: str, rows: List[Dict[str, Any]]) -> None:
    for row in rows or []:
        tcid = row.get("tcid")
        if not str(row.get("what_tested_he_verified") or "").strip():
            raise ValueError(f"{group_name}: missing what_tested_he_verified for TCID {tcid}")
        if not str(row.get("what_tested_en_official") or "").strip():
            raise ValueError(f"{group_name}: missing what_tested_en_official for TCID {tcid}")
        sources = row.get("what_tested_sources")
        if not isinstance(sources, list) or not any((src or {}).get("file") for src in sources):
            raise ValueError(f"{group_name}: missing what_tested_sources for TCID {tcid}")


def build_tcid_first_mapping(
    profile: str,
    mapping_rows: List[Dict],
    tc_rows: List[Dict],
    runtime_active_tcids: Optional[Set[str]] = None,
) -> Tuple[List[Dict], Dict]:
    active_set = runtime_active_tcids or set()
    tc_index: Dict[str, Dict] = {}
    for tc in tc_rows:
        tcid = tc.get("tcid")
        if not tcid:
            continue
        tc_index[tcid] = tc

    rows_by_tcid: Dict[str, Dict] = {}
    bucket_tcid_sets = {
        "mandatory": set(),
        "optional": set(),
        "conditional": set(),
    }
    bucket_condition_counts = {
        "mandatory": 0,
        "optional": 0,
        "conditional": 0,
    }

    for map_row in mapping_rows:
        mapped_tcids = map_row.get("mapped_tcids", [])
        if not mapped_tcids:
            continue

        for mapped in mapped_tcids:
            tcid = mapped.get("tcid")
            if not tcid:
                continue

            tc_ref = tc_index.get(tcid, {})
            row = rows_by_tcid.get(tcid)
            if row is None:
                row = {
                    "tcid": tcid,
                    "desc": mapped.get("desc") or tc_ref.get("desc") or "",
                    "category": mapped.get("category") or tc_ref.get("category") or "",
                    "active_date": mapped.get("active_date") or tc_ref.get("active_date") or "",
                    "ts_title": tc_ref.get("ts_title") or mapped.get("ts_title") or "",
                    "ts_title_source": tc_ref.get("ts_title_source") or mapped.get("ts_title_source") or {},
                    "source": tc_ref.get("source")
                    or {
                        "file": (
                            (
                                ((mapped.get("evidence") or [{}])[0].get("official_source") or {}).get("file")
                            )
                            if mapped.get("evidence")
                            else None
                        ),
                        "sheet": (
                            (
                                ((mapped.get("evidence") or [{}])[0].get("official_source") or {}).get("sheet")
                            )
                            if mapped.get("evidence")
                            else None
                        ),
                        "row": (
                            (
                                ((mapped.get("evidence") or [{}])[0].get("official_source") or {}).get("row")
                            )
                            if mapped.get("evidence")
                            else None
                        ),
                        "columns": (
                            (
                                ((mapped.get("evidence") or [{}])[0].get("official_source") or {}).get("columns")
                            )
                            if mapped.get("evidence")
                            else None
                        ),
                    },
                    "best_confidence": "Unmapped",
                    "runtime_active": tcid in active_set,
                    "runtime_signal": "unknown",
                    "bucket_flags": {"mandatory": False, "optional": False, "conditional": False},
                    "condition_count": 0,
                    "active_conditions_count": 0,
                    "inactive_conditions_count": 0,
                    "conditions": [],
                    "tcmt_features": [],
                    "unmapped_note": None,
                }
                rows_by_tcid[tcid] = row

            bucket = map_row.get("bucket") or "optional"
            if bucket not in bucket_tcid_sets:
                bucket = "optional"

            condition = {
                "map_id": map_row.get("map_id"),
                "bucket": bucket,
                "tspc_name": map_row.get("tspc_name"),
                "tspc_item": map_row.get("tspc_item"),
                "tspc_capability": map_row.get("tspc_capability"),
                "tspc_status": map_row.get("tspc_status"),
                "mandatory": map_row.get("mandatory"),
                "value": map_row.get("value"),
                "confidence": mapped.get("confidence", "Unmapped"),
                "score": mapped.get("score"),
                "mapping_source": mapped.get("mapping_source") or map_row.get("mapping_source") or "TS_TCMT",
                "item_expression": mapped.get("item_expression"),
                "expression_eval": mapped.get("expression_eval"),
                "tcmt_feature": mapped.get("tcmt_feature"),
                "tcmt_features": mapped.get("tcmt_features") or [],
                "tspc_evidence": map_row.get("evidence") or [],
                "relation_evidence": mapped.get("evidence") or [],
            }
            condition["condition_hint"] = condition_hint_from_mapping_row(condition)
            expr_eval = condition.get("expression_eval") or {}
            condition["logic_eval"] = str(expr_eval.get("result") or "unknown").lower()
            condition["logic_eval_reason_he"] = build_logic_eval_reason(expr_eval, expr_eval.get("items") or [])
            condition["plain_condition_he"] = build_condition_plain_text(condition)

            row["conditions"].append(condition)
            if condition.get("tcmt_feature"):
                if condition["tcmt_feature"] not in row["tcmt_features"]:
                    row["tcmt_features"].append(condition["tcmt_feature"])
            for feature in condition.get("tcmt_features") or []:
                if feature and feature not in row["tcmt_features"]:
                    row["tcmt_features"].append(feature)
            row["bucket_flags"][bucket] = True
            row["condition_count"] += 1
            if condition["condition_hint"] == "inactive":
                row["inactive_conditions_count"] += 1
            else:
                row["active_conditions_count"] += 1

            if confidence_rank(condition["confidence"]) > confidence_rank(row["best_confidence"]):
                row["best_confidence"] = condition["confidence"]

            bucket_tcid_sets[bucket].add(tcid)
            bucket_condition_counts[bucket] += 1

    for row in rows_by_tcid.values():
        row["conditions"].sort(
            key=lambda c: (
                -confidence_rank(c.get("confidence", "Unmapped")),
                -(c.get("score") if isinstance(c.get("score"), (int, float)) else -9999),
                c.get("tspc_name") or "",
            )
        )
        row["runtime_signal"] = runtime_signal_from_conditions(row["conditions"])
        if not row["conditions"]:
            row["unmapped_note"] = "לא נמצאו תנאים משויכים ל-TCID זה מתוך מיפוי TSPC↔TCID."
        row.update(build_tcid_summary_fields(row))

    for tc in tc_rows:
        tcid = tc.get("tcid")
        if not tcid or tcid in rows_by_tcid:
            continue
        rows_by_tcid[tcid] = {
            "tcid": tcid,
            "desc": tc.get("desc") or "",
            "category": tc.get("category") or "",
            "active_date": tc.get("active_date") or "",
            "ts_title": tc.get("ts_title") or "",
            "ts_title_source": tc.get("ts_title_source") or {},
            "source": tc.get("source") or {},
            "best_confidence": "Unmapped",
            "runtime_active": tcid in active_set,
            "runtime_signal": "unknown",
            "bucket_flags": {"mandatory": False, "optional": False, "conditional": False},
            "condition_count": 0,
            "active_conditions_count": 0,
            "inactive_conditions_count": 0,
            "conditions": [],
            "tcmt_features": [],
            "unmapped_note": "TCID זה נמצא ב-TCRL אך ללא תנאים משויכים ממיפוי TSPC הנוכחי.",
        }
        rows_by_tcid[tcid].update(build_tcid_summary_fields(rows_by_tcid[tcid]))

    rows = sorted(rows_by_tcid.values(), key=lambda row: row.get("tcid") or "")
    summary = tcid_mapping_summary_template()
    for row in rows:
        summary["tcid_count"] += 1
        if row["condition_count"] > 0:
            summary["with_conditions_count"] += 1
        else:
            summary["without_conditions_count"] += 1

        conf = row.get("best_confidence")
        if conf == "High":
            summary["high_count"] += 1
        elif conf == "Medium":
            summary["medium_count"] += 1
        elif conf == "Low":
            summary["low_count"] += 1

        if row.get("runtime_active"):
            summary["runtime_active_count"] += 1

        signal = row.get("runtime_signal")
        if signal in ("likely_active_mandatory", "likely_active_optional"):
            summary["likely_active_count"] += 1
        elif signal == "likely_inactive":
            summary["likely_inactive_count"] += 1
        else:
            summary["unknown_count"] += 1

    by_bucket = {}
    for bucket in ("mandatory", "optional", "conditional"):
        by_bucket[bucket] = {
            "tcid_count": len(bucket_tcid_sets[bucket]),
            "condition_count": bucket_condition_counts[bucket],
        }

    return rows, {"totals": summary, "by_bucket": by_bucket, "profile": profile}


def build_comparison(data: Dict, official_sources: Dict[str, Dict]) -> Dict[str, Dict]:
    profiles = ("DIS", "BAS", "HRS", "HID")
    statuses = ("match", "partial", "conflict", "unverified")
    summary: Dict[str, Dict[str, int]] = {p: {s: 0 for s in statuses} for p in profiles}
    findings: List[Dict] = []

    def add_finding(
        profile: str,
        topic: str,
        status: str,
        site_claim: str,
        official_evidence: str,
        impact_meaning: str,
        site_source: Dict,
        official_source: Dict,
        recommended_action: str,
    ) -> None:
        fid = f"{profile.lower()}-{topic}-{len(findings) + 1}"
        findings.append(
            {
                "id": fid,
                "profile": profile,
                "topic": topic,
                "status": status,
                "site_claim": site_claim,
                "official_evidence": official_evidence,
                "impact_meaning": impact_meaning,
                "site_source": site_source,
                "official_source": official_source,
                "recommended_action": recommended_action,
            }
        )
        summary[profile][status] += 1

    # 1) HID model must be HOGP-only
    hid_rows = data.get("tspc_tables", {}).get("hid", [])
    legacy_hid_rows = [
        row
        for row in hid_rows
        if "hid11" in (row.get("capability", "").lower())
        or "human interface device v1.0" in (row.get("capability", "").lower())
    ]
    hid_spec_path = Path(official_sources["HID"]["spec"]["file"])
    hid_spec_line = find_line_in_pdf(hid_spec_path, "HID Over GATT Profile")
    add_finding(
        profile="HID",
        topic="hid_model",
        status="conflict" if legacy_hid_rows else "match",
        site_claim=(
            "זוהו ערכי HID11/Legacy בתוך מודל HID באתר."
            if legacy_hid_rows
            else "מודל HID באתר מבוסס על HOGP בלבד ללא HID11."
        ),
        official_evidence="המסמך הרשמי בתיקיית HID הוא HID Over GATT Profile (HOGP).",
        impact_meaning=(
            "ערבוב HID11 עם HOGP יכול ליצור בחירת בדיקות לא עקבית."
            if legacy_hid_rows
            else "בחירת בדיקות HID נשארת עקבית מול קו הבסיס הרשמי."
        ),
        site_source=(
            {
                "file": legacy_hid_rows[0]["source"]["file"],
                "line": legacy_hid_rows[0]["source"].get("desc_line"),
                "note": "שורת Workspace עם יכולת HID legacy",
            }
            if legacy_hid_rows
            else {"file": "data/report-data.js", "field_path": "tspc_tables.hid", "note": "מודל HID באתר"}
        ),
        official_source={"file": str(hid_spec_path), "line": hid_spec_line, "note": "מסמך פרופיל רשמי"},
        recommended_action=(
            "להסיר שורות HID11/legacy ממודל HID ולהשאיר HOGP בלבד."
            if legacy_hid_rows
            else "להמשיך לשמור על HOGP-only במודל HID."
        ),
    )

    # 2) TCID set per profile
    profile_tc_rows = {
        "DIS": data.get("tcs", {}).get("dis", []),
        "BAS": data.get("tcs", {}).get("bas", []),
        "HRS": data.get("tcs", {}).get("hrs", []),
        "HID": data.get("tcs", {}).get("hid", []),
    }
    expected_prefix = {"DIS": "DIS/", "BAS": "BAS/", "HRS": "HRS/", "HID": "HOGP/"}
    expected_sheet = {"DIS": "DIS", "BAS": "BAS", "HRS": "HRS", "HID": "HOGP"}
    for profile in profiles:
        rows = profile_tc_rows[profile]
        bad = [r for r in rows if not (r.get("tcid", "").startswith(expected_prefix[profile]))]
        status = "match"
        if not rows:
            status = "unverified"
        elif bad:
            status = "conflict"
        add_finding(
            profile=profile,
            topic="tcid_set",
            status=status,
            site_claim=(
                f"נמצאו {len(rows)} TCID עם prefixes: {', '.join(summarize_prefixes(rows)) or 'ללא'}."
            ),
            official_evidence=f"לפרופיל {profile} נדרש prefix רשמי: {expected_prefix[profile]}",
            impact_meaning=(
                "Prefix שגוי משנה את סט הבדיקות שהמשתמש מבין ש-PTS מריץ."
                if status == "conflict"
                else "סט הבדיקות בפועל מוצג תחת prefix תואם."
            ),
            site_source=(
                {
                    "file": bad[0]["source"]["file"],
                    "sheet": bad[0]["source"]["sheet"],
                    "row": bad[0]["source"]["row"],
                    "note": "TCID חריג בתצוגת אתר",
                }
                if bad
                else (
                    {
                        "file": rows[0]["source"]["file"],
                        "sheet": rows[0]["source"]["sheet"],
                        "row": rows[0]["source"]["row"],
                        "note": "TCID לדוגמה מהאתר",
                    }
                    if rows
                    else {"file": "data/report-data.js", "field_path": f"tcs.{profile.lower()}", "note": "לא נמצאו TCID"}
                )
            ),
            official_source={
                **find_official_tcid_anchor(
                    Path(official_sources[profile]["tcrl"]["gatt"]),
                    expected_sheet[profile],
                    expected_prefix[profile],
                ),
                "note": f"TCRL רשמי לפרופיל {profile}",
            },
            recommended_action=(
                "לעדכן את מקור/פילטר ה-TCID כך שייכלל רק prefix תקני."
                if status == "conflict"
                else "להמשיך לעקוב אחרי אותו prefix תקני."
            ),
        )

    # 3) ICS mapping quality
    tspc_by_profile = {
        "DIS": data.get("tspc_tables", {}).get("dis", []),
        "BAS": data.get("tspc_tables", {}).get("bas", []),
        "HRS": data.get("tspc_tables", {}).get("hrs", []),
        "HID": data.get("tspc_tables", {}).get("hid", []),
    }
    expected_ics_doc = {"DIS": "DIS", "BAS": "BAS", "HRS": "HRS", "HID": "HOGP"}
    for profile in profiles:
        rows = tspc_by_profile[profile]
        missing = [r for r in rows if not r.get("ics_doc_key")]
        wrong_doc = [
            r
            for r in rows
            if r.get("ics_doc_key") and r.get("ics_doc_key") != expected_ics_doc[profile]
        ]
        status = "match"
        if not rows:
            status = "unverified"
        elif wrong_doc:
            status = "conflict"
        elif missing:
            status = "partial"
        official_ics_path = Path(official_sources[profile]["ics"]["file"])
        official_ics_line = find_line_in_pdf(
            official_ics_path,
            "Implementation Conformance Statement",
        )
        if official_ics_line is None:
            official_ics_line = find_line_in_pdf(official_ics_path, "ICS")
        add_finding(
            profile=profile,
            topic="ics_mapping",
            status=status,
            site_claim=f"מתוך {len(rows)} שורות TSPC: חסרות התאמות ICS={len(missing)}, התאמות למסמך לא נכון={len(wrong_doc)}.",
            official_evidence=f"מסמך ICS הרשמי לפרופיל {profile}: {expected_ics_doc[profile]}",
            impact_meaning=(
                "מיפוי ICS חסר/שגוי מפחית אמינות בהסבר למה בדיקות מסוימות נבחרות."
                if status in ("partial", "conflict")
                else "מיפוי ICS עקבי ותומך עקיבות מלאה."
            ),
            site_source=(
                {
                    "file": (wrong_doc or missing)[0]["source"]["file"],
                    "line": (wrong_doc or missing)[0]["source"].get("desc_line"),
                    "note": "שורה עם בעיית מיפוי ICS",
                }
                if (wrong_doc or missing)
                else (
                    {
                        "file": rows[0]["source"]["file"],
                        "line": rows[0]["source"].get("desc_line"),
                        "note": "שורת TSPC לדוגמה",
                    }
                    if rows
                    else {"file": "data/report-data.js", "field_path": f"tspc_tables.{profile.lower()}"}
                )
            ),
            official_source={
                "file": official_sources[profile]["ics"]["file"],
                "line": official_ics_line,
                "note": (
                    "ICS רשמי בתיקיית Profiles"
                    if official_ics_line is not None
                    else "ICS רשמי בתיקיית Profiles (line-level לא זוהה ב-PDF)"
                ),
            },
            recommended_action=(
                "להשלים/לתקן התאמות capability למסמך ICS הרשמי."
                if status in ("partial", "conflict")
                else "להמשיך לשמר את מיפוי ה-ICS הנוכחי."
            ),
        )

    # 4) Source-path alignment with docs/Profiles baseline
    for profile in profiles:
        files: Set[str] = set()
        summary_entry = next((s for s in data.get("summary", []) if s.get("profile") == profile), None)
        if summary_entry:
            for src in summary_entry.get("source", []):
                f = src.get("file")
                if f:
                    files.add(str(f))

        for row in tspc_by_profile[profile]:
            s = row.get("source", {})
            if s.get("file"):
                files.add(str(s["file"]))
            doc_key = row.get("ics_doc_key")
            if doc_key and doc_key in data.get("meta", {}).get("ics_files", {}):
                files.add(data["meta"]["ics_files"][doc_key])

        for row in profile_tc_rows[profile][:10]:
            s = row.get("source", {})
            if s.get("file"):
                files.add(str(s["file"]))

        bad = [
            f
            for f in files
            if (f.lower().endswith(".pdf") or f.lower().endswith(".xlsx")) and not f.startswith("docs/profiles/")
        ]
        add_finding(
            profile=profile,
            topic="source_path",
            status="conflict" if bad else "match",
            site_claim=f"נבדקו {len(files)} נתיבי מקור רלוונטיים לפרופיל.",
            official_evidence="קו הבסיס הרשמי מחייב שימוש בקבצים מתוך docs/profiles בלבד.",
            impact_meaning=(
                "מקורות מחוץ לתיקיית Profiles עלולים לגרום לפער בין הדוח לבין המקור הרשמי."
                if bad
                else "נתיבי המקור נשארים צמודים לקבצי הבסיס הרשמיים."
            ),
            site_source=(
                {"file": bad[0], "note": "מקור מחוץ ל-baseline"}
                if bad
                else {"file": "data/report-data.js", "field_path": f"summary.{profile}.source"}
            ),
            official_source={
                "file": official_sources[profile]["profile_dir"],
                "note": "תיקיית baseline הרשמית",
            },
            recommended_action=(
                "להחליף מקורות חיצוניים בנתיבים מתוך docs/profiles."
                if bad
                else "להמשיך לאכוף docs/profiles כמקור הרשמי."
            ),
        )

    # 5) Narrative text sanity
    overview_by_id = {p.get("id"): p for p in data.get("profiles_overview", [])}
    narrative_rules = {
        "DIS": {"required": ["מידע מזהה", "יצרן"], "forbidden": []},
        "BAS": {"required": ["סוללה"], "forbidden": []},
        "HRS": {"required": ["דופק"], "forbidden": []},
        "HID": {"required": ["hogp"], "forbidden": ["hid11"]},
    }
    for profile in profiles:
        overview = overview_by_id.get(profile, {})
        text = " ".join(
            [
                str(overview.get("what_it_is", "")),
                str(overview.get("services", "")),
                str(overview.get("why_it_matters", "")),
            ]
        )
        text_norm = normalize_text(text)
        required = narrative_rules[profile]["required"]
        forbidden = narrative_rules[profile]["forbidden"]

        missing_required = [k for k in required if normalize_text(k) not in text_norm]
        found_forbidden = [k for k in forbidden if normalize_text(k) in text_norm]
        status = "match"
        if found_forbidden:
            status = "conflict"
        elif missing_required:
            status = "partial"

        spec_path = Path(official_sources[profile]["spec"]["file"])
        spec_line = find_line_in_pdf(spec_path, profile if profile != "HID" else "HID Over GATT Profile")
        add_finding(
            profile=profile,
            topic="narrative_text",
            status=status,
            site_claim=f"תיאור פרופיל: {overview.get('services', '')}",
            official_evidence="תיאור הפרופיל צריך להתאים להגדרת המסמך הרשמי.",
            impact_meaning=(
                "תיאור לא מדויק מבלבל משתמשים לגבי טווח השירותים של הפרופיל."
                if status in ("partial", "conflict")
                else "התיאור העברי תואם את ההקשר הרשמי של הפרופיל."
            ),
            site_source={
                "file": "data/report-data.js",
                "field_path": f"profiles_overview.{profile}",
                "note": "טקסט תיאורי באתר",
            },
            official_source={"file": str(spec_path), "line": spec_line, "note": "מסמך פרופיל רשמי"},
            recommended_action=(
                "לעדכן ניסוח תיאורי כך שישקף את המסמך הרשמי באופן מפורש."
                if status in ("partial", "conflict")
                else "להשאיר את הניסוח כפי שהוא."
            ),
        )

    return {
        "default_filter": {"status": "conflict", "profile": "ALL", "topic": "ALL"},
        "summary": summary,
        "findings": findings,
    }


def main() -> None:
    profile_sources = resolve_profile_sources()
    validate_profile_sources(profile_sources)
    official_sources = build_official_sources(profile_sources)
    runtime_active_path = resolve_runtime_active_export_path()
    runtime_active = load_runtime_active_export(runtime_active_path)
    runtime_active_history = collect_runtime_active_history(runtime_active_path)
    if runtime_active.get("available"):
        has_current = any(
            str(entry.get("file") or "") == str(runtime_active.get("file") or "")
            and str(entry.get("generated_at") or "") == str(runtime_active.get("generated_at") or "")
            for entry in runtime_active_history
        )
        if not has_current:
            runtime_active["id"] = make_runtime_snapshot_id(runtime_active, len(runtime_active_history))
            runtime_active_history.insert(0, runtime_active)

    pqw6 = parse_pqw6(WORKSPACE_PQW6)

    rows_bas = read_sheet_rows(profile_sources["BAS"]["tcrl_gatt"], "BAS")
    rows_dis = read_sheet_rows(profile_sources["DIS"]["tcrl_gatt"], "DIS")
    rows_hrs = read_sheet_rows(profile_sources["HRS"]["tcrl_gatt"], "HRS")
    rows_hogp = read_sheet_rows(profile_sources["HID"]["tcrl_gatt"], "HOGP")

    bas_tc = extract_tc(rows_bas, "BAS/", profile_sources["BAS"]["tcrl_gatt"], "BAS")
    dis_tc = extract_tc(rows_dis, "DIS/", profile_sources["DIS"]["tcrl_gatt"], "DIS")
    hrs_tc = extract_tc(rows_hrs, "HRS/", profile_sources["HRS"]["tcrl_gatt"], "HRS")
    hid_tc = extract_tc(rows_hogp, "HOGP/", profile_sources["HID"]["tcrl_gatt"], "HOGP")

    rows_iopt_bas = read_sheet_rows(profile_sources["BAS"]["tcrl_iopt"], "IOPT")
    rows_iopt_dis = read_sheet_rows(profile_sources["DIS"]["tcrl_iopt"], "IOPT")
    rows_iopt_hrs = read_sheet_rows(profile_sources["HRS"]["tcrl_iopt"], "IOPT")
    rows_iopt_hid = read_sheet_rows(profile_sources["HID"]["tcrl_iopt"], "IOPT")

    iopt_bas = extract_tc(rows_iopt_bas, "IOPT/BAS/", profile_sources["BAS"]["tcrl_iopt"], "IOPT")
    iopt_dis = extract_tc(rows_iopt_dis, "IOPT/DIS/", profile_sources["DIS"]["tcrl_iopt"], "IOPT")
    iopt_hrs = extract_tc(rows_iopt_hrs, "IOPT/HRS/", profile_sources["HRS"]["tcrl_iopt"], "IOPT")
    iopt_hid = extract_tc(rows_iopt_hid, "IOPT/HID/", profile_sources["HID"]["tcrl_iopt"], "IOPT")

    dis_rows = [r for r in pqw6["DIS"] if r["name"].startswith("TSPC_")]
    bas_rows = [r for r in pqw6["BAS"] if r["name"].startswith("TSPC_")]
    hrs_rows = [r for r in pqw6["HRS"] if r["name"].startswith("TSPC_")]
    hid_rows = []
    for row in pqw6["IOPT"]:
        if not row["name"].startswith("TSPC_"):
            continue
        name_norm = row["name"].lower()
        desc_norm = row["desc"].lower()
        if "hid" not in desc_norm and "hogp" not in desc_norm:
            continue
        # Keep HID over GATT items and drop explicit legacy HID11/HID v1.0 rows.
        if (
            "hid11" in name_norm
            or "hid11" in desc_norm
            or "human interface device v1.0" in desc_norm
            or "v1.1 or later" in desc_norm
        ):
            continue
        hid_rows.append(row)

    dis_tspc = build_tspc_entries(dis_rows, "DIS")
    bas_tspc = build_tspc_entries(bas_rows, "BAS")
    hrs_tspc = build_tspc_entries(hrs_rows, "HRS")
    hid_tspc = build_tspc_entries(hid_rows, "HID")

    dis_ts_data = extract_ts_profile_data("DIS", profile_sources["DIS"]["ts"], dis_tspc)
    bas_ts_data = extract_ts_profile_data("BAS", profile_sources["BAS"]["ts"], bas_tspc)
    hrs_ts_data = extract_ts_profile_data("HRS", profile_sources["HRS"]["ts"], hrs_tspc)
    hid_ts_data = extract_ts_profile_data("HID", profile_sources["HID"]["ts"], hid_tspc)

    apply_ts_titles_to_tc_rows(dis_tc, dis_ts_data.get("tcid_titles", {}), profile_sources["DIS"]["ts"])
    apply_ts_titles_to_tc_rows(bas_tc, bas_ts_data.get("tcid_titles", {}), profile_sources["BAS"]["ts"])
    apply_ts_titles_to_tc_rows(hrs_tc, hrs_ts_data.get("tcid_titles", {}), profile_sources["HRS"]["ts"])
    apply_ts_titles_to_tc_rows(hid_tc, hid_ts_data.get("tcid_titles", {}), profile_sources["HID"]["ts"])

    dis_m, dis_o, dis_c = split_mand_opt_cond(dis_tspc)
    bas_m, bas_o, bas_c = split_mand_opt_cond(bas_tspc)
    hrs_m, hrs_o, hrs_c = split_mand_opt_cond(hrs_tspc)
    hid_m, hid_o, hid_c = split_mand_opt_cond(hid_tspc)

    dis_mapping_rows, dis_mapping_summary = build_tspc_tcid_mapping(
        "DIS", dis_tspc, dis_tc, official_sources, dis_ts_data
    )
    bas_mapping_rows, bas_mapping_summary = build_tspc_tcid_mapping(
        "BAS", bas_tspc, bas_tc, official_sources, bas_ts_data
    )
    hrs_mapping_rows, hrs_mapping_summary = build_tspc_tcid_mapping(
        "HRS", hrs_tspc, hrs_tc, official_sources, hrs_ts_data
    )
    hid_mapping_rows, hid_mapping_summary = build_tspc_tcid_mapping(
        "HID", hid_tspc, hid_tc, official_sources, hid_ts_data
    )
    dis_tcid_rows, dis_tcid_summary = build_tcid_first_mapping(
        "DIS",
        dis_mapping_rows,
        dis_tc,
        set((runtime_active.get("profiles", {}).get("DIS", {}) or {}).get("active_tcids", [])),
    )
    bas_tcid_rows, bas_tcid_summary = build_tcid_first_mapping(
        "BAS",
        bas_mapping_rows,
        bas_tc,
        set((runtime_active.get("profiles", {}).get("BAS", {}) or {}).get("active_tcids", [])),
    )
    hrs_tcid_rows, hrs_tcid_summary = build_tcid_first_mapping(
        "HRS",
        hrs_mapping_rows,
        hrs_tc,
        set((runtime_active.get("profiles", {}).get("HRS", {}) or {}).get("active_tcids", [])),
    )
    hid_tcid_rows, hid_tcid_summary = build_tcid_first_mapping(
        "HID",
        hid_mapping_rows,
        hid_tc,
        set((runtime_active.get("profiles", {}).get("HID", {}) or {}).get("active_tcids", [])),
    )
    validate_tcid_compact_fields("DIS", dis_tcid_rows)
    validate_tcid_compact_fields("BAS", bas_tcid_rows)
    validate_tcid_compact_fields("HRS", hrs_tcid_rows)
    validate_tcid_compact_fields("HID", hid_tcid_rows)

    attach_verified_fields_to_tc_rows(dis_tc, dis_tcid_rows, "DIS")
    attach_verified_fields_to_tc_rows(bas_tc, bas_tcid_rows, "BAS")
    attach_verified_fields_to_tc_rows(hrs_tc, hrs_tcid_rows, "HRS")
    attach_verified_fields_to_tc_rows(hid_tc, hid_tcid_rows, "HID")
    attach_verified_fields_to_tc_rows(iopt_bas, [], "IOPT/BAS", manual_hebrew=IOPT_VERIFIED_HEBREW)
    attach_verified_fields_to_tc_rows(iopt_dis, [], "IOPT/DIS", manual_hebrew=IOPT_VERIFIED_HEBREW)
    attach_verified_fields_to_tc_rows(iopt_hrs, [], "IOPT/HRS", manual_hebrew=IOPT_VERIFIED_HEBREW)
    attach_verified_fields_to_tc_rows(iopt_hid, [], "IOPT/HID", manual_hebrew=IOPT_VERIFIED_HEBREW)

    validate_verified_fields_in_tc_group("tcs.dis", dis_tc)
    validate_verified_fields_in_tc_group("tcs.bas", bas_tc)
    validate_verified_fields_in_tc_group("tcs.hrs", hrs_tc)
    validate_verified_fields_in_tc_group("tcs.hid", hid_tc)
    validate_verified_fields_in_tc_group("tcs.iopt_bas", iopt_bas)
    validate_verified_fields_in_tc_group("tcs.iopt_dis", iopt_dis)
    validate_verified_fields_in_tc_group("tcs.iopt_hrs", iopt_hrs)
    validate_verified_fields_in_tc_group("tcs.iopt_hid", iopt_hid)

    ics_refs = find_ics_refs()

    line_get_tc = find_line(PTSCONTROL_PY, r"def get_test_case_list\(self, project_name\):")
    line_is_active = find_line(PTSCONTROL_PY, r"IsActiveTestCase\(project_name, test_case_name\)")

    line_tspc_grid = find_first_line_containing(
        ICS_RST_SCRIPT, "grid = [['Parameter Name', 'Selected', 'Description']]"
    )
    line_tspc_formula = find_first_line_containing(
        ICS_RST_SCRIPT, "parameter_name = 'TSPC_{}_{}'.format(profile, table.Item[i].replace('/', '_'))"
    )
    line_tspc_desc = find_first_line_containing(
        ICS_RST_SCRIPT, "description = f'{table.Capability[i]} ({table.Status[i]})'"
    )

    ts_extracted_public = {
        "DIS": ts_public_summary(dis_ts_data),
        "BAS": ts_public_summary(bas_ts_data),
        "HRS": ts_public_summary(hrs_ts_data),
        "HID": ts_public_summary(hid_ts_data),
    }
    mapping_authoritative = {
        "source": "TS_TCMT",
        "profiles": {
            "DIS": {"rows": dis_mapping_rows, "summary": dis_mapping_summary},
            "BAS": {"rows": bas_mapping_rows, "summary": bas_mapping_summary},
            "HRS": {"rows": hrs_mapping_rows, "summary": hrs_mapping_summary},
            "HID": {"rows": hid_mapping_rows, "summary": hid_mapping_summary},
        },
    }
    validation_report = {
        "method": "TS_TCMT authoritative only (no heuristic fallback)",
        "profiles": {
            "DIS": {
                "tcrl_tcid_count": len(dis_tc),
                "tcid_with_conditions_count": (dis_tcid_summary.get("totals") or {}).get("with_conditions_count", 0),
                "tcmt_row_count": (dis_ts_data.get("tcmt") or {}).get("row_count", 0),
                "tcmt_mapped_tcid_count": (dis_ts_data.get("tcmt") or {}).get("mapped_tcid_count", 0),
            },
            "BAS": {
                "tcrl_tcid_count": len(bas_tc),
                "tcid_with_conditions_count": (bas_tcid_summary.get("totals") or {}).get("with_conditions_count", 0),
                "tcmt_row_count": (bas_ts_data.get("tcmt") or {}).get("row_count", 0),
                "tcmt_mapped_tcid_count": (bas_ts_data.get("tcmt") or {}).get("mapped_tcid_count", 0),
            },
            "HRS": {
                "tcrl_tcid_count": len(hrs_tc),
                "tcid_with_conditions_count": (hrs_tcid_summary.get("totals") or {}).get("with_conditions_count", 0),
                "tcmt_row_count": (hrs_ts_data.get("tcmt") or {}).get("row_count", 0),
                "tcmt_mapped_tcid_count": (hrs_ts_data.get("tcmt") or {}).get("mapped_tcid_count", 0),
            },
            "HID": {
                "tcrl_tcid_count": len(hid_tc),
                "tcid_with_conditions_count": (hid_tcid_summary.get("totals") or {}).get("with_conditions_count", 0),
                "tcmt_row_count": (hid_ts_data.get("tcmt") or {}).get("row_count", 0),
                "tcmt_mapped_tcid_count": (hid_ts_data.get("tcmt") or {}).get("mapped_tcid_count", 0),
            },
        },
    }

    data = {
        "meta": {
            "workspace": {
                "file": str(WORKSPACE_PQW6),
                "project_lines": pqw6["_project_lines"],
            },
            "baseline": {
                "source": "docs/profiles",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "comparison_engine_version": "v1.0",
            },
            "ics_files": {k: str(v) for k, v in ICS_PDF.items()},
            "counts": {
                "dis": {"total": len(dis_tc), "categories": category_counts(dis_tc)},
                "bas": {"total": len(bas_tc), "categories": category_counts(bas_tc)},
                "hrs": {"total": len(hrs_tc), "categories": category_counts(hrs_tc)},
                "hid": {"total": len(hid_tc), "categories": category_counts(hid_tc)},
            },
            "active_runtime": {
                "file": str(PTSCONTROL_PY),
                "line_get_tc": line_get_tc,
                "line_is_active": line_is_active,
            },
            "tspc_formula": {
                "file": str(ICS_RST_SCRIPT),
                "line_grid": line_tspc_grid,
                "line_formula": line_tspc_formula,
                "line_desc": line_tspc_desc,
            },
        },
        "glossary": {
            "TSPC": "TSPC הוא פריט יכולת של הפרופיל (שירות/מאפיין/התנהגות) שמוגדר ב-PTS. הוא מתאר מה המוצר מצהיר שהוא תומך בו, ובאיזה מצב.",
            "TCID": "TCID הוא מזהה של בדיקת תקן ספציפית מתוך TCRL. זה השם הרשמי של הטסט שבודק בפועל את ההתנהגות מול התקן.",
            "Conditional": "פריט שתלוי בתנאי. בקונפיגורציה הנתונה הוא לא תמיד רלוונטי, ורק אם מתקיים תנאי מסוים הוא משפיע על בחירת בדיקות.",
            "IOPT": "קבוצת בדיקות שילוב בין פרופילים שונים. המטרה היא לבדוק אינטגרציה בין שירותים פעילים, לא רק תקינות של כל פרופיל בנפרד.",
            "Mandatory": "האם פריט מוגדר כחובה בקונפיגורציה הנוכחית.",
            "Value": "הערך בפועל שנבחר בקונפיגורציה (לרוב TRUE/FALSE).",
            "Category": "סוג/משפחת בדיקה לפי TCRL.",
        },
        "glossary_extended": {
            "TSPC": {
                "title": "TSPC - יכולות הפרופיל ב-PTS",
                "short": "מזהה יכולת/דרישה שהמוצר מצהיר עליה בפרופיל מסוים.",
                "long": "אפשר לחשוב על TSPC כמו 'מתג יכולת' של הפרופיל: האם שירות/מאפיין נתמך, האם חובה, ומה הערך הפעיל כרגע. זה הבסיס להבנת אילו בדיקות צפויות להיות רלוונטיות.",
                "how_to_read": [
                    "קודם קוראים את שם ה-TSPC והמשמעות שלו (למשל Battery Level או Manufacturer Name).",
                    "בודקים Mandatory/Value כדי להבין אם היכולת פעילה וחובה בקונפיגורציה הנוכחית.",
                    "משווים ל-TCID המשויכים כדי לראות אילו בדיקות מאמתות בפועל את אותה יכולת.",
                ],
                "example": {
                    "profile": "DIS",
                    "tspc_name": dis_tspc[0]["name"] if dis_tspc else None,
                    "capability": dis_tspc[0]["capability"] if dis_tspc else None,
                },
                "sources": [
                    {"file": str(WORKSPACE_PQW6), "line": pqw6["_project_lines"]["DIS"], "note": "הגדרות TSPC ב-Workspace"},
                    {"file": str(ICS_RST_SCRIPT), "line": line_tspc_formula, "note": "יצירת מזהי TSPC"},
                ],
            },
            "TCID": {
                "title": "TCID - בדיקת תקן רשמית",
                "short": "מזהה בדיקה ספציפית מתוך TCRL שה-PTS יודע להריץ.",
                "long": "TCID הוא שם הטסט הרשמי (למשל BAS/... או DIS/...). זה מה שנבדק בפועל מול התקן, עם תיאור מדויק, קטגוריה ותאריך רלוונטיות.",
                "how_to_read": [
                    "קוראים את ה-TCID ואת התיאור המלא של הבדיקה.",
                    "בודקים קטגוריה (Category) ותאריך רלוונטיות (Active Date).",
                    "פותחים מקור sheet/row כדי לראות את הרשומה המדויקת ב-TCRL.",
                ],
                "example": {
                    "profile": "BAS",
                    "tcid": bas_tc[0]["tcid"] if bas_tc else None,
                    "desc": bas_tc[0]["desc"] if bas_tc else None,
                },
                "sources": [
                    {
                        "file": str(profile_sources["BAS"]["tcrl_gatt"]),
                        "sheet": "BAS",
                        "row": bas_tc[0]["source"]["row"] if bas_tc else None,
                        "note": "רשומת TCID ב-TCRL",
                    }
                ],
            },
            "TSPC_TCID_RELATION": {
                "title": "איך TSPC ו-TCID עובדים יחד",
                "short": "TSPC מתאר יכולת, TCID בודק אותה בפועל.",
                "long": "בפועל אין תמיד מיפוי 1:1 קשיח. יכולת אחת יכולה להיבדק בכמה TCID, וחלק מה-TCID תלויים בתנאים. לכן הדוח מציג מיפוי עם רמת ודאות ומקור לכל קשר.",
                "how_to_read": [
                    "מתחילים מה-TSPC כדי להבין מה היכולת בפרופיל.",
                    "פותחים את TCID המשויכים כדי לראות אילו בדיקות מאמתות אותה.",
                    "בודקים Confidence ומקורות כדי להבין עד כמה המיפוי ודאי.",
                    "אם אין מיפוי ודאי, קוראים את סיבת ה-unmapped ולא מסיקים מסקנה אוטומטית.",
                ],
                "sources": [
                    {"file": str(PTSCONTROL_PY), "line": line_is_active, "note": "בחירת בדיקות פעילות בריצה"},
                    {"file": str(profile_sources["DIS"]["tcrl_gatt"]), "sheet": "DIS", "row": 6, "note": "שורת TCMT ב-TCRL"},
                ],
            },
        },
        "profiles_overview": [
            {
                "id": "DIS",
                "name": "DIS",
                "what_it_is": "פרופיל שמציג מידע מזהה של ההתקן.",
                "services": "שם יצרן, דגם, גרסה, PnP ID ומזהים נוספים.",
                "why_it_matters": "עוזר לאינטרופרטיביליות ולזיהוי מדויק של ההתקן בצד השני.",
            },
            {
                "id": "BAS",
                "name": "BAS",
                "what_it_is": "פרופיל למידע מצב סוללה.",
                "services": "Battery Level ונתוני סוללה נוספים (אם נתמכים).",
                "why_it_matters": "מוודא שצרכני השירות מקבלים דיווחי סוללה תקינים ואחידים.",
            },
            {
                "id": "HRS",
                "name": "HRS",
                "what_it_is": "פרופיל למדידת דופק.",
                "services": "Heart Rate Measurement ותכונות נלוות כמו RR-Interval ו-Energy Expended.",
                "why_it_matters": "קריטי לאמינות נתוני בריאות ולאינטרופרטיביליות עם אפליקציות/חיישנים.",
            },
            {
                "id": "HID",
                "name": "HID",
                "what_it_is": "HID over GATT Profile (HOGP) לקלט משתמש ב-BLE.",
                "services": "HID Service (HIDS), HID Information, דוחות קלט/פלט ושירותים תלויים לפי HOGP.",
                "why_it_matters": "מוודא שהתקני קלט BLE עובדים באמינות ובאינטרופרטיביליות מול Hosts תואמים.",
            },
        ],
        "ui_labels": {
            "overview_title": "סקירה מהירה: חובה / אופציונלי / תלוי-תנאי",
            "iopt_tab_title": "בדיקות שילוב בין פרופילים (IOPT)",
            "iopt_intro": "IOPT הן בדיקות שמוודאות שהפרופילים עובדים נכון גם יחד, ולא רק כל אחד בנפרד.",
            "iopt_deep_intro": "למשל: מוצר יכול לעבור בדיקות DIS ובדיקות BAS בנפרד, אבל להיכשל כשההתנהגות שלהם משולבת בזמן אמת. כאן IOPT נכנס לתמונה.",
            "iopt_quality_context": "הקבוצה הזו קיימת כחלק מתהליך תקינה רגיל ולא מעידה לבדה על תקלה קיימת; היא נועדה להקטין סיכוני אינטגרציה בין רכיבים.",
            "iopt_relation_to_issues": "כאשר נכשלים ב-IOPT, לרוב זו אינדיקציה לאי-התאמה בין פרופילים או תלויות קונפיגורציה, ולא בהכרח לבעיה בפרופיל יחיד.",
        },
        "ui_presentations": {
            "tcid_compact_legend": {
                "title": "מקרא תצוגה קומפקטית",
                "what_tested": "מה הטסט בודק בפועל (מתוך TCRL/TS).",
                "why_relevant": "למה הטסט רלוונטי כרגע לפי תנאי TCMT/ICS בקונפיגורציה הנוכחית.",
                "status": "סטטוס כללי: צפוי לפעול / עשוי לפעול / צפוי לא לפעול / לא ידוע.",
                "or_logic": "כאשר יש כמה תנאים עבור TCID, הם מוצגים כאפשרויות חלופיות (OR).",
            }
        },
        "column_help": {
            "profile": "שם הפרופיל שנבדק.",
            "mandatory_group": "פריטים שמסומנים כחובה בקונפיגורציה.",
            "optional_group": "פריטים אופציונליים או תלויי-תנאי בקונפיגורציה.",
            "source": "קבצי מקור ושורות שעליהם נשענת הטענה.",
            "tspc_id": "מזהה פריט קונפיגורציה ב-PTS.",
            "ics_item": "מספר הסעיף המקביל במסמך ICS.",
            "meaning": "המשמעות התפקודית של הפריט במוצר.",
            "status": "סטטוס במסמך התקן (M/O/C.x).",
            "mandatory_flag": "האם הוגדר כחובה בקובץ הקונפיגורציה.",
            "value_flag": "הערך בפועל שהוגדר בקובץ הקונפיגורציה.",
            "tcid": "מזהה בדיקת תקן רשמית מתוך TCRL.",
            "tc_category": "קטגוריית הבדיקה לפי TCRL.",
            "active_date": "תאריך ההפעלה/רלוונטיות של הבדיקה לפי TCRL.",
            "test_desc": "מה הבדיקה מבצעת בפועל לפי TCRL, ובנוסף כותרות/פירושי TS כשזמינים.",
            "mapped_tcids": "בדיקות TCID שמופו ליכולת TSPC הזו, עם פירוט נפתח.",
            "mapping_confidence": "רמת ודאות המיפוי: High כשקיים קשר רשמי ב-TS TCMT, אחרת Unmapped.",
            "mapping_bucket": "שיוך הפריט בסקירה: חובה / אופציונלי / תלוי-תנאי.",
            "tcid_conditions": "רשימת תנאי TSPC/TCMT שמשפיעים על ה-TCID הזה, כולל הערכת התנאי בקונפיגורציה הנוכחית.",
            "tcid_runtime_signal": "הערכת מצב ריצה: likely_active_mandatory / likely_active_optional / likely_inactive / unknown.",
            "tspc_links_count": "כמה תנאי TSPC משויכים ל-TCID הזה.",
            "best_confidence": "רמת הוודאות הגבוהה ביותר מתוך כל תנאי המיפוי המשויכים ל-TCID.",
            "summary_what_tested": "תקציר קצר: מה הטסט בודק בפועל (בשפה פשוטה).",
            "summary_why_relevant": "תקציר קצר: למה הטסט רלוונטי כרגע לפי תנאי המיפוי.",
            "summary_status": "סטטוס קומפקטי: expected_active / maybe_active / expected_inactive / unknown.",
            "runtime_active_fact": "עובדת Runtime מתוך Snapshot אמיתי של PTS: האם ה-TCID הופיע בפועל כפעיל.",
            "tcid_variant": "וריאנט תנאי עבור אותו TCID כאשר קיימות כמה אפשרויות הפעלה.",
            "applicable_tspc": "מזהה ה-TSPC הספציפי שרלוונטי לשורת ה-variant הזו.",
            "ics_ixit_prereq": "תנאי קדם ברמת ICS/IXIT כפי שנגזרים מהסטטוס והפריט.",
            "pics_pxit_conditions": "תנאי PICS/PXIT בקונפיגורציה (Mandatory/Value) עבור ה-variant.",
            "execution_notes": "הערות הפעלה פרקטיות: condition_hint, confidence, runtime signal ועובדת Runtime.",
        },
        "summary": [
            {
                "profile": "DIS",
                "mandatory": dis_m,
                "optional": dis_o,
                "conditional": dis_c,
                "source": [
                    source_ref(str(WORKSPACE_PQW6), pqw6["_project_lines"]["DIS"]),
                    source_ref(str(ICS_PDF["DIS"]), None),
                ],
            },
            {
                "profile": "BAS",
                "mandatory": bas_m,
                "optional": bas_o,
                "conditional": bas_c,
                "source": [
                    source_ref(str(WORKSPACE_PQW6), pqw6["_project_lines"]["BAS"]),
                    source_ref(str(ICS_PDF["BAS"]), None),
                ],
            },
            {
                "profile": "HRS",
                "mandatory": hrs_m,
                "optional": hrs_o,
                "conditional": hrs_c,
                "source": [
                    source_ref(str(WORKSPACE_PQW6), pqw6["_project_lines"]["HRS"]),
                    source_ref(str(ICS_PDF["HRS"]), None),
                ],
            },
            {
                "profile": "HID",
                "mandatory": hid_m,
                "optional": hid_o,
                "conditional": hid_c,
                "source": [
                    source_ref(str(WORKSPACE_PQW6), pqw6["_project_lines"]["IOPT"]),
                    source_ref(str(ICS_PDF["HOGP"]), None),
                ],
            },
        ],
        "tspc_tables": {
            "dis": dis_tspc,
            "bas": bas_tspc,
            "hrs": hrs_tspc,
            "hid": hid_tspc,
        },
        "ts_extracted": ts_extracted_public,
        "mapping_authoritative": mapping_authoritative,
        "validation_report": validation_report,
        "mapping": {
            "DIS": {"rows": dis_mapping_rows},
            "BAS": {"rows": bas_mapping_rows},
            "HRS": {"rows": hrs_mapping_rows},
            "HID": {"rows": hid_mapping_rows},
        },
        "mapping_summary": {
            "DIS": dis_mapping_summary,
            "BAS": bas_mapping_summary,
            "HRS": hrs_mapping_summary,
            "HID": hid_mapping_summary,
        },
        "mapping_tcid": {
            "DIS": {"rows": dis_tcid_rows},
            "BAS": {"rows": bas_tcid_rows},
            "HRS": {"rows": hrs_tcid_rows},
            "HID": {"rows": hid_tcid_rows},
        },
        "mapping_tcid_summary": {
            "DIS": dis_tcid_summary,
            "BAS": bas_tcid_summary,
            "HRS": hrs_tcid_summary,
            "HID": hid_tcid_summary,
        },
        "runtime_active": runtime_active,
        "runtime_active_history": runtime_active_history,
        "ics_refs": ics_refs,
        "tcs": {
            "dis": dis_tc,
            "bas": bas_tc,
            "hrs": hrs_tc,
            "hid": hid_tc,
            "hogp": hid_tc,
            "iopt_bas": iopt_bas,
            "iopt_dis": iopt_dis,
            "iopt_hrs": iopt_hrs,
            "iopt_hid": iopt_hid,
        },
        "notes": {
            "hid_ics_missing": [
                "TSPC_IOPT_1_14",
                "TSPC_IOPT_2_31a",
                "TSPC_IOPT_2_31b",
                "TSPC_IOPT_2_64a",
                "TSPC_IOPT_2_64b",
            ]
        },
        "links": [
            {"title": "Battery Service (BAS)", "url": "https://www.bluetooth.com/specifications/specs/battery-service/"},
            {"title": "Device Information Service (DIS)", "url": "https://www.bluetooth.com/specifications/specs/device-information-service/"},
            {"title": "Heart Rate Service (HRS)", "url": "https://www.bluetooth.com/specifications/specs/heart-rate-service-1-0/"},
            {"title": "HID over GATT Profile (HOGP)", "url": "https://www.bluetooth.com/specifications/specs/hid-over-gatt-profile/"},
        ],
    }

    data["official_sources"] = official_sources
    data["comparison"] = build_comparison(data, data["official_sources"])

    enforce_workspace_source_consistency(data)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSS.parent.mkdir(parents=True, exist_ok=True)
    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    OUT_DATA.parent.mkdir(parents=True, exist_ok=True)

    data_js = "window.REPORT_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
    OUT_DATA.write_text(data_js, encoding="utf-8")

    OUT_CSS.write_text(read_template_or_fallback(TEMPLATE_CSS, CSS_CONTENT), encoding="utf-8")
    OUT_JS.write_text(read_template_or_fallback(TEMPLATE_JS, JS_CONTENT), encoding="utf-8")
    OUT_HTML.write_text(read_template_or_fallback(TEMPLATE_HTML, HTML_TEMPLATE), encoding="utf-8")

    print(f"WROTE {OUT_HTML}")
    print(f"WROTE {OUT_CSS}")
    print(f"WROTE {OUT_JS}")
    print(f"WROTE {OUT_DATA}")


CSS_CONTENT = """
:root {
  --bg: #f4f8fb;
  --panel: #ffffff;
  --panel-alt: #f8fcff;
  --ink: #1f2a37;
  --muted: #5d6876;
  --primary: #0a4f7a;
  --primary-2: #0b7aa6;
  --line: #d8e4ee;
  --shadow: 0 12px 30px rgba(15, 49, 74, 0.10);
  --accent: #0f8a6d;
  --warn: #f9f3d1;
  --warn-border: #e8d88e;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Rubik", "Heebo", "Assistant", "Segoe UI", Arial, sans-serif;
  color: var(--ink);
  background:
    radial-gradient(1000px 560px at 95% -20%, #dff1ff 0%, transparent 60%),
    radial-gradient(1200px 700px at -10% 120%, #dff8f0 0%, transparent 55%),
    var(--bg);
  line-height: 1.55;
  direction: rtl;
}
.layout {
  max-width: 1520px;
  margin: 18px auto;
  display: grid;
  grid-template-columns: 290px 1fr;
  gap: 16px;
  padding: 0 14px 26px;
}
.sidebar {
  position: sticky;
  top: 12px;
  align-self: start;
  background: linear-gradient(155deg, #f1f8ff, #ffffff 60%);
  border: 1px solid var(--line);
  border-radius: 16px;
  box-shadow: var(--shadow);
  padding: 14px;
  max-height: calc(100vh - 24px);
  overflow: auto;
}
.brand { margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #e3edf5; }
.brand h1 { margin: 0; font-size: 1.05rem; color: #08496f; line-height: 1.35; }
.brand p { margin: 6px 0 0; font-size: 0.87rem; color: var(--muted); }
.nav { display: grid; gap: 8px; margin: 12px 0; }
.nav-btn {
  width: 100%;
  border: 1px solid #cfe0ed;
  background: #fff;
  color: #124d70;
  text-align: right;
  padding: 10px 11px;
  border-radius: 11px;
  font-size: 0.92rem;
  cursor: pointer;
}
.nav-btn:hover { border-color: #9ec2da; background: #f2f9ff; }
.nav-btn.active {
  background: linear-gradient(145deg, #0a6ca2, #0c82bf);
  color: #fff;
  border-color: #0b6a9e;
}
.meta { margin-top: 10px; border-top: 1px solid #e3edf5; padding-top: 10px; font-size: 0.84rem; color: var(--muted); }
.content { min-width: 0; display: grid; gap: 12px; }
.hero {
  background: linear-gradient(130deg, #ebf7ff, #ffffff 58%);
  border: 1px solid var(--line);
  border-radius: 16px;
  box-shadow: var(--shadow);
  padding: 16px 18px;
}
.hero h2 { margin: 0 0 6px; color: #084c73; font-size: 1.45rem; }
.hero p { margin: 5px 0; color: var(--muted); }
.toolbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 13px;
  padding: 10px;
  box-shadow: var(--shadow);
}
.toolbar input {
  flex: 1 1 320px;
  border: 1px solid #c8d9e6;
  border-radius: 10px;
  padding: 9px 10px;
  font: inherit;
  min-width: 220px;
}
.toolbar button {
  border: 1px solid #b9d0e0;
  background: #fff;
  color: #114f74;
  border-radius: 10px;
  padding: 8px 11px;
  cursor: pointer;
}
.toolbar button:hover { background: #f2f9ff; }
.panel {
  display: none;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 15px;
  padding: 14px;
  box-shadow: var(--shadow);
}
.panel.active { display: block; }
.section-title {
  margin: 0 0 10px;
  color: #095179;
  font-size: 1.18rem;
  border-bottom: 2px solid #e7f0f7;
  padding-bottom: 6px;
}
.grid { display: grid; gap: 11px; grid-template-columns: repeat(12, 1fr); }
.card { background: var(--panel-alt); border: 1px solid #dce8f2; border-radius: 12px; padding: 11px; }
.span-12 { grid-column: span 12; }
.span-6 { grid-column: span 6; }
.span-4 { grid-column: span 4; }
.kpi { font-size: 1.35rem; color: #084f77; margin: 0; font-weight: 700; }
.kpi-sub { margin: 4px 0 0; color: var(--muted); font-size: .9rem; }
.mini-list { margin: 0; padding-inline-start: 18px; }
.mini-list li { margin: 3px 0; }
.tag {
  display: inline-block;
  font-size: .75rem;
  background: #e7f4ff;
  color: #0a608f;
  border: 1px solid #b7d9ef;
  border-radius: 999px;
  padding: 1px 8px;
}
.muted { color: var(--muted); }
.small { font-size: .9rem; }
.table-wrap {
  overflow: auto;
  border: 1px solid #d3e2ed;
  border-radius: 11px;
  background: #fff;
}
table { width: 100%; border-collapse: collapse; min-width: 920px; direction: rtl; }
th, td {
  text-align: right;
  vertical-align: top;
  border-bottom: 1px solid #e8eff5;
  padding: 8px 9px;
  font-size: .92rem;
}
th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #edf6fd;
  color: #0a567d;
  font-size: .88rem;
}
tr:nth-child(even) td { background: #fcfeff; }
code {
  background: #eef5fb;
  border: 1px solid #d4e6f3;
  border-radius: 5px;
  padding: 1px 5px;
  font-family: "SFMono-Regular", Menlo, Consolas, "Liberation Mono", monospace;
  font-size: .81rem;
  direction: ltr;
  unicode-bidi: plaintext;
}
details {
  border: 1px dashed #bed2e1;
  border-radius: 10px;
  background: #fdffff;
  padding: 8px 9px;
  margin-top: 9px;
}
summary { cursor: pointer; color: #0b5f8c; font-weight: 600; }
.src-list { margin: 6px 0 0; padding-inline-start: 18px; }
.src-list li { margin: 6px 0; }
.alert { border: 1px solid var(--warn-border); background: var(--warn); color: #6f5e21; border-radius: 11px; padding: 10px; }
.okbox { border: 1px solid #bfe6d8; background: #ebfaf4; color: #0f644d; border-radius: 11px; padding: 10px; }
.footer-note { margin-top: 10px; font-size: 0.9rem; color: #536271; }
.topbar {
  display: none;
  position: sticky;
  top: 0;
  z-index: 5;
  background: #ffffff;
  border-bottom: 1px solid var(--line);
  padding: 10px 14px;
}
.topbar button {
  border: 1px solid #cfe0ed;
  background: #fff;
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
}
.overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.25);
  z-index: 4;
}
.overlay.active { display: block; }

@media (max-width: 1180px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar {
    position: fixed;
    right: 0;
    top: 0;
    height: 100vh;
    max-height: none;
    transform: translateX(110%);
    transition: transform .18s ease;
    z-index: 6;
    width: 290px;
  }
  body.nav-open .sidebar { transform: translateX(0); }
  .topbar { display: block; }
  .span-6, .span-4 { grid-column: span 12; }
}
"""


JS_CONTENT = """
const DATA = window.REPORT_DATA || {};
const navButtons = Array.from(document.querySelectorAll('.nav-btn'));
const panels = Array.from(document.querySelectorAll('.panel'));
const searchInput = document.getElementById('searchInput');

function esc(str) {
  return String(str ?? '').replace(/[&<>"']/g, (s) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', \"'\": '&#39;'
  }[s]));
}

function sourceRef(s) {
  if (!s || !s.file) return '';
  if (s.line == null) return `<code>${esc(s.file)}</code>`;
  return `<code>${esc(s.file)}:${s.line}</code>`;
}

function renderMiniList(items, title, extra) {
  if (!items || !items.length) return `<details><summary>${esc(title)} (0)</summary><div class="muted">אין</div></details>`;
  const li = items.map(i =>
    `<li>${esc(i.capability)} <span class="tag">${esc(i.status || '?')}</span> <code>${esc(i.name)}</code> <span class="muted">Value=${esc(i.value)}</span></li>`
  ).join('');
  const ext = extra ? `<div class="small muted">${esc(extra)}</div>` : '';
  return `<details><summary>${esc(title)} (${items.length})</summary><ul class="mini-list">${li}</ul>${ext}</details>`;
}

function renderSummary() {
  const rows = (DATA.summary || []).map(s => {
    const src = (s.source || []).map(sourceRef).filter(Boolean).join('<br>');
    return `<tr>
      <td>${esc(s.profile)}</td>
      <td>${renderMiniList(s.mandatory, 'חובה')}</td>
      <td>${renderMiniList(s.optional, 'אופציונלי', `Conditional: ${s.conditional?.length || 0} (ראו פענוח TSPC)`)}${renderMiniList(s.conditional, 'Conditional')}</td>
      <td>${src}</td>
    </tr>`;
  }).join('');
  return `<div class="table-wrap"><table>
    <thead><tr><th>פרופיל</th><th>חובה</th><th>לא-חובה</th><th>מקור</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

function formatCategories(obj) {
  if (!obj || !Object.keys(obj).length) return 'ללא';
  return Object.entries(obj).map(([k,v]) => `${k}:${v}`).join(', ');
}

function renderIcsRefs(list) {
  if (!list || !list.length) return '<div class="muted">אין.</div>';
  return `<ul class="src-list">${list.map(r =>
    `<li><span class="small">${esc(r.needle)}</span><br>${sourceRef({file:r.file,line:r.line})}</li>`).join('')}</ul>`;
}

function renderTspcTable(title, rows) {
  if (!rows || !rows.length) return `<h3>${esc(title)}</h3><div class="muted">אין שורות להצגה.</div>`;
  const body = rows.map(r => {
    const ws = [
      sourceRef({file:r.source?.file, line:r.source?.name_line}),
      sourceRef({file:r.source?.file, line:r.source?.desc_line}),
    ].filter(Boolean);
    if (r.ics_doc_key) {
      const file = DATA?.meta?.ics_files?.[r.ics_doc_key] || r.ics_doc_key;
      ws.push(sourceRef({file, line: r.ics_line}));
    }
    const src = ws.join('<br>');
    return `<tr>
      <td><code>${esc(r.name)}</code></td>
      <td><code>${esc(r.item)}</code></td>
      <td>${esc(r.capability)}</td>
      <td>${esc(r.status)}</td>
      <td>${esc(r.mandatory)}</td>
      <td>${esc(r.value)}</td>
      <td>${src}</td>
    </tr>`;
  }).join('');
  return `<h3>${esc(title)}</h3><div class="table-wrap"><table>
    <thead><tr><th>TSPC</th><th>ICS Item</th><th>משמעות</th><th>סטטוס</th><th>Mandatory</th><th>Value</th><th>מקור מדויק</th></tr></thead>
    <tbody>${body}</tbody></table></div>`;
}

function renderTcTable(title, rows, collapsed=true) {
  if (!rows || !rows.length) return `<h3>${esc(title)}</h3><div class="muted">אין TCIDs להצגה.</div>`;
  const body = rows.map(r => {
    const s = r.source || {};
    const src = `<code>${esc(s.file)} | ${esc(s.sheet)} | row ${esc(s.row)} | cols ${esc(s.columns)}</code>`;
    return `<tr>
      <td><code>${esc(r.tcid)}</code></td>
      <td>${esc(r.category)}</td>
      <td>${esc(r.active_date)}</td>
      <td>${esc(r.desc)}</td>
      <td>${src}</td>
    </tr>`;
  }).join('');
  const table = `<div class="table-wrap"><table>
    <thead><tr><th>TCID</th><th>קטגוריה</th><th>Active Date</th><th>תיאור</th><th>מקור מדויק</th></tr></thead>
    <tbody>${body}</tbody></table></div>`;
  return collapsed ? `<details><summary>${esc(title)} (${rows.length} פריטים)</summary>${table}</details>` : `<h3>${esc(title)}</h3>${table}`;
}

function fillPanels() {
  const counts = DATA.meta?.counts || {};
  const active = DATA.meta?.active_runtime || {};
  const tspcFormula = DATA.meta?.tspc_formula || {};

  document.getElementById('overviewContent').innerHTML = `
    <div class="grid">
      <div class="card span-4"><p class="kpi">${(DATA.summary?.[0]?.mandatory?.length || 0)} חובה / ${(DATA.summary?.[0]?.optional?.length || 0)} אופציונלי</p><p class="kpi-sub">DIS</p></div>
      <div class="card span-4"><p class="kpi">${(DATA.summary?.[1]?.mandatory?.length || 0)} חובה / ${(DATA.summary?.[1]?.optional?.length || 0)} אופציונלי</p><p class="kpi-sub">BAS</p></div>
      <div class="card span-4"><p class="kpi">${(DATA.summary?.[2]?.mandatory?.length || 0)} חובה / ${(DATA.summary?.[2]?.optional?.length || 0)} אופציונלי</p><p class="kpi-sub">HRS</p></div>

      <div class="card span-12 okbox">
        <b>על מזהי TSPC:</b> לכל מזהה יש Capability וסטטוס ICS. פירוש מלא בפאנל “פענוח TSPC”.
      </div>

      <div class="card span-12">
        <h3>טבלת סיכום חובה/אופציונלי (עם משמעות אנושית)</h3>
        ${renderSummary()}
      </div>

      <div class="card span-6 alert">
        <b>אמינות:</b> רשימת Active נקבעת בזמן ריצה ע״י <code>IsActiveTestCase</code>.
        מקור: ${sourceRef({file: active.file, line: active.line_get_tc})} ו-${sourceRef({file: active.file, line: active.line_is_active})}.
      </div>

      <div class="card span-6">
        <b>ספירת TCIDs לפי TCRL</b>
        <ul class="mini-list">
          <li>DIS: ${counts.dis?.total || 0} (${formatCategories(counts.dis?.categories)})</li>
          <li>BAS: ${counts.bas?.total || 0} (${formatCategories(counts.bas?.categories)})</li>
          <li>HRS: ${counts.hrs?.total || 0} (${formatCategories(counts.hrs?.categories)})</li>
          <li>HOGP: ${counts.hogp?.total || 0} (${formatCategories(counts.hogp?.categories)})</li>
          <li>HID11: ${counts.hid11?.total || 0} (${formatCategories(counts.hid11?.categories)})</li>
        </ul>
      </div>
    </div>
  `;

  document.getElementById('tspcContent').innerHTML = `
    <div class="grid">
      <div class="card span-12">
        <p>נוסחת יצירת מזהי TSPC: <code>TSPC_{PROFILE}_{Item}</code> כאשר <code>Item</code> הוא פריט ICS עם <code>_</code> במקום <code>/</code>.</p>
        <p class="small muted">מקור: ${sourceRef({file: tspcFormula.file, line: tspcFormula.line_grid})}, ${sourceRef({file: tspcFormula.file, line: tspcFormula.line_formula})}, ${sourceRef({file: tspcFormula.file, line: tspcFormula.line_desc})}.</p>
      </div>
      <div class="card span-12">${renderTspcTable('DIS - כל שורות TSPC', DATA.tspc_tables?.dis || [])}</div>
      <div class="card span-12">${renderTspcTable('BAS - כל שורות TSPC', DATA.tspc_tables?.bas || [])}</div>
      <div class="card span-12">${renderTspcTable('HRS - כל שורות TSPC', DATA.tspc_tables?.hrs || [])}</div>
      <div class="card span-12">${renderTspcTable('HID (מתוך IOPT) - שורות TSPC', DATA.tspc_tables?.hid || [])}</div>
    </div>
  `;

  document.getElementById('disContent').innerHTML = `
    <div class="grid">
      <div class="card span-12">${renderTspcTable('שורות DIS ב-Workspace', DATA.tspc_tables?.dis || [])}</div>
      <div class="card span-12"><h3>אסמכתאות ICS ל-DIS</h3>${renderIcsRefs(DATA.ics_refs?.DIS || [])}</div>
      <div class="card span-12">${renderTcTable('כל TCIDs של DIS', DATA.tcs?.dis || [], true)}</div>
    </div>
  `;

  document.getElementById('basContent').innerHTML = `
    <div class="grid">
      <div class="card span-12">${renderTspcTable('שורות BAS ב-Workspace', DATA.tspc_tables?.bas || [])}</div>
      <div class="card span-12"><h3>אסמכתאות ICS ל-BAS</h3>${renderIcsRefs(DATA.ics_refs?.BAS || [])}</div>
      <div class="card span-12">${renderTcTable('כל TCIDs של BAS', DATA.tcs?.bas || [], true)}</div>
    </div>
  `;

  document.getElementById('hrsContent').innerHTML = `
    <div class="grid">
      <div class="card span-12">${renderTspcTable('שורות HRS ב-Workspace', DATA.tspc_tables?.hrs || [])}</div>
      <div class="card span-12"><h3>אסמכתאות ICS ל-HRS</h3>${renderIcsRefs(DATA.ics_refs?.HRS || [])}</div>
      <div class="card span-12">${renderTcTable('כל TCIDs של HRS', DATA.tcs?.hrs || [], true)}</div>
    </div>
  `;

  document.getElementById('hidContent').innerHTML = `
    <div class="grid">
      <div class="card span-12 alert">
        שים לב: עבור חלק משורות HID ב-IOPT לא נמצאה התאמה טקסטואלית חד-חד ערכית ב-ICS של HOGP/HID11.
        במקרים אלו המקור המדויק הוא שורת ה-Workspace.
      </div>
      <div class="card span-12">${renderTspcTable('שורות HID/HOGP מתוך IOPT', DATA.tspc_tables?.hid || [])}</div>
      <div class="card span-6"><h3>אסמכתאות ICS ל-HOGP</h3>${renderIcsRefs(DATA.ics_refs?.HOGP || [])}</div>
      <div class="card span-6"><h3>אסמכתאות ICS ל-HID11</h3>${renderIcsRefs(DATA.ics_refs?.HID11 || [])}</div>
      <div class="card span-12">${renderTcTable('כל TCIDs של HOGP', DATA.tcs?.hogp || [], true)}</div>
      <div class="card span-12">${renderTcTable('כל TCIDs של HID11', DATA.tcs?.hid11 || [], true)}</div>
    </div>
  `;

  document.getElementById('ioptContent').innerHTML = `
    <div class="grid">
      <div class="card span-12">${renderTcTable('IOPT/BAS', DATA.tcs?.iopt_bas || [], false)}</div>
      <div class="card span-12">${renderTcTable('IOPT/DIS', DATA.tcs?.iopt_dis || [], false)}</div>
      <div class="card span-12">${renderTcTable('IOPT/HRS', DATA.tcs?.iopt_hrs || [], false)}</div>
      <div class="card span-12">${renderTcTable('IOPT/HID', DATA.tcs?.iopt_hid || [], false)}</div>
    </div>
  `;

  document.getElementById('appendixContent').innerHTML = `
    <div class="grid">
      <div class="card span-12 alert">
        בגרסה קודמת HRC פורש כ-HRP Collector. אחרי התיקון שלך, הדוח הראשי עבר ל-HRS.
        הנספח נשאר כדי לא לאבד מידע קיים.
      </div>
      <div class="card span-12"><h3>אסמכתאות ICS ל-HRP Collector</h3>${renderIcsRefs(DATA.ics_refs?.HRP || [])}</div>
      <div class="card span-12">${renderTcTable('HRP/COL TCIDs', DATA.tcs?.hrp_col || [], true)}</div>
    </div>
  `;

  document.getElementById('sourcesContent').innerHTML = `
    <div class="grid">
      <div class="card span-12">
        <ul class="src-list">
          <li>${sourceRef({file: DATA.meta?.workspace?.file})} — Workspace PICS/PIXIT.</li>
          <li><code>${esc(DATA.meta?.active_runtime?.file || '')}</code> — Runtime Active.</li>
          <li><code>${esc(DATA.meta?.tspc_formula?.file || '')}</code> — נוסחת TSPC.</li>
          <li>${Object.values(DATA.meta?.ics_files || {}).map(f => `<code>${esc(f)}</code>`).join('<br>')} — קבצי ICS.</li>
        </ul>
      </div>
      <div class="card span-12">
        <h3>קישורים רשמיים (Bluetooth SIG)</h3>
        <ul class="src-list">${(DATA.links || []).map(l => `<li><a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.title)}</a></li>`).join('')}</ul>
      </div>
    </div>
  `;
}

function getActivePanel() {
  return document.querySelector('.panel.active');
}

function activatePanel(id) {
  panels.forEach((p) => p.classList.toggle('active', p.id === 'panel-' + id));
  navButtons.forEach((b) => b.classList.toggle('active', b.dataset.panelTarget === id));
  applySearch();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function applySearch() {
  const q = (searchInput.value || '').trim().toLowerCase();
  const panel = getActivePanel();
  if (!panel) return;
  panel.querySelectorAll('tbody tr').forEach((tr) => {
    const txt = tr.innerText.toLowerCase();
    tr.style.display = (!q || txt.includes(q)) ? '' : 'none';
  });
}

document.getElementById('clearSearchBtn').addEventListener('click', () => {
  searchInput.value = '';
  applySearch();
  searchInput.focus();
});
searchInput.addEventListener('input', applySearch);

document.getElementById('openDetailsBtn').addEventListener('click', () => {
  const panel = getActivePanel();
  if (!panel) return;
  panel.querySelectorAll('details').forEach((d) => { d.open = true; });
});
document.getElementById('closeDetailsBtn').addEventListener('click', () => {
  const panel = getActivePanel();
  if (!panel) return;
  panel.querySelectorAll('details').forEach((d) => { d.open = false; });
});

navButtons.forEach((btn) => {
  btn.addEventListener('click', () => activatePanel(btn.dataset.panelTarget));
});

document.getElementById('toggleNav').addEventListener('click', () => {
  document.body.classList.toggle('nav-open');
  document.getElementById('overlay').classList.toggle('active');
});

document.getElementById('overlay').addEventListener('click', () => {
  document.body.classList.remove('nav-open');
  document.getElementById('overlay').classList.remove('active');
});

fillPanels();
"""


HTML_TEMPLATE = """<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>דו"ח PTS - DIS/BAS/HRS/HID</title>
  <link rel="stylesheet" href="assets/report.css" />
</head>
<body>
  <div class="topbar">
    <button id="toggleNav" type="button">תפריט</button>
  </div>
  <div class="overlay" id="overlay"></div>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <h1>דו"ח PTS אמין ומלא<br>DIS / BAS / HRS / HID</h1>
        <p>כל המידע, עם ניווט נוח ושמירה על אמינות גבוהה.</p>
      </div>
      <div class="nav">
        <button class="nav-btn active" data-panel-target="overview">סקירה מהירה</button>
        <button class="nav-btn" data-panel-target="tspc">פענוח TSPC</button>
        <button class="nav-btn" data-panel-target="dis">DIS</button>
        <button class="nav-btn" data-panel-target="bas">BAS</button>
        <button class="nav-btn" data-panel-target="hrs">HRS</button>
        <button class="nav-btn" data-panel-target="hid">HID</button>
        <button class="nav-btn" data-panel-target="iopt">IOPT Cross-Profile</button>
        <button class="nav-btn" data-panel-target="appendix">נספח שקיפות (HRC ישן)</button>
        <button class="nav-btn" data-panel-target="sources">מקורות</button>
      </div>
      <div class="meta">
        מידע מסוכם ופעיל — דרך התפריט בצד.
      </div>
    </aside>

    <main class="content">
      <section class="hero">
        <h2>דו"ח מלא: חובה מול אופציונלי ב-PTS</h2>
        <p>
          הדוח כולל את כל המידע שנאסף, בפיצול לפאנלים לצורך ניווט מהיר,
          עם מקורות מפורטים לכל פריט מידע.
        </p>
      </section>

      <section class="toolbar">
        <input id="searchInput" type="search" placeholder="חיפוש בתוך הטבלאות בפאנל הפעיל..." />
        <button id="clearSearchBtn" type="button">נקה</button>
        <button id="openDetailsBtn" type="button">פתח הכל</button>
        <button id="closeDetailsBtn" type="button">סגור הכל</button>
      </section>

      <section class="panel active" id="panel-overview"><div id="overviewContent"></div></section>
      <section class="panel" id="panel-tspc"><div id="tspcContent"></div></section>
      <section class="panel" id="panel-dis"><div id="disContent"></div></section>
      <section class="panel" id="panel-bas"><div id="basContent"></div></section>
      <section class="panel" id="panel-hrs"><div id="hrsContent"></div></section>
      <section class="panel" id="panel-hid"><div id="hidContent"></div></section>
      <section class="panel" id="panel-iopt"><div id="ioptContent"></div></section>
      <section class="panel" id="panel-appendix"><div id="appendixContent"></div></section>
      <section class="panel" id="panel-sources"><div id="sourcesContent"></div></section>

      <div class="footer-note">
        הדוח נטען מקובץ נתונים חיצוני: <code>data/report-data.js</code>.
      </div>
    </main>
  </div>

  <script src="data/report-data.js"></script>
  <script src="assets/report.js"></script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
