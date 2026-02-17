#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ----------------------------
# Input paths
# ----------------------------
WORKSPACE_PQW6 = Path("auto-pts/autopts/workspaces/zephyr/zephyr-master/zephyr-master.pqw6")
PTSCONTROL_PY = Path("auto-pts/autopts/ptscontrol.py")
ICS_RST_SCRIPT = Path("auto-pts/tools/ics_rst_from_html.py")

TCRL_GATT = Path("/tmp/bt_docs/tcrl_unpack/TCRLpkg101p1/GATTBased.TCRL.p27.xlsx")
TCRL_TRAD = Path("/tmp/bt_docs/tcrl_unpack/TCRLpkg101p1/Traditional.TCRL.p47.xlsx")
TCRL_IOPT = Path("/tmp/bt_docs/tcrl_unpack/TCRLpkg101p1/IOPT.TCRL.p8.xlsx")

ICS_TXT = {
    "BAS": Path("/tmp/bt_docs/bas-ics-p5-pdf.txt"),
    "DIS": Path("/tmp/bt_docs/dis-ics-p5-pdf.txt"),
    "HRS": Path("/tmp/bt_docs/hrs-ics-p3-pdf.txt"),
    "HRP": Path("/tmp/bt_docs/hrp-ics-p3-pdf.txt"),
    "HOGP": Path("/tmp/bt_docs/hogp-ics-p8-pdf.txt"),
    "HID11": Path("/tmp/bt_docs/hid11-ics-p12ed2-pdf.txt"),
}

OUT_HTML = Path("docs/reports/pts_dis_bas_hrs_hid_report_he.html")
OUT_HTML_ALIAS = Path("docs/reports/pts_dis_bas_hrc_hid_report_he.html")


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


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


def normalize_text(s: str) -> str:
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


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

    def find_from(needle: str, start_line: int) -> Optional[int]:
        start = max(1, start_line)
        for i in range(start - 1, len(lines)):
            if needle in lines[i]:
                return i + 1
        return None

    project_start_lines = {
        name: find_first_line_containing(path, f'<PROJECT_INFORMATION NAME="{name}"')
        for name in projects.keys()
    }

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
    }
    data["_project_lines"] = {
        "BAS": project_start_lines.get("BAS"),
        "DIS": project_start_lines.get("DIS"),
        "HRS": project_start_lines.get("HRS"),
        "IOPT": project_start_lines.get("IOPT"),
        "HRC": find_first_line_containing(path, '<PROJECT_INFORMATION NAME="HRC"'),
    }
    data["_project_names"] = sorted(projects.keys())
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
        "HID11": [
            "HID Device Role                                  [1] 2.1.2                 C.2",
            "Mandatory to support at least one.",
            "2.5       HID Device Role",
        ],
        "HRP": [
            "Collector                                                             [1] 2.1           C.1",
            "2.5       Collector role",
            "Prerequisite: HRP 1/2 “Collector”",
        ],
    }
    refs = {}
    for doc_key, needle_list in needles.items():
        lines = read_lines(ICS_TXT[doc_key])
        doc_refs = []
        for needle in needle_list:
            ln = None
            for i, line in enumerate(lines, start=1):
                if needle in line:
                    ln = i
                    break
            doc_refs.append({"needle": needle, "line": ln, "file": str(ICS_TXT[doc_key])})
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
        lines = read_lines(ICS_TXT[doc])
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

            if status:
                st = status.lower()
                if st in ln_norm:
                    score += 3

            if "mandatory if" in ln_norm or "optional if" in ln_norm:
                score -= 2

            # Prefer better score; if tie, earlier line.
            if score > best[0] or (score == best[0] and i < best[1]):
                best = (score, i, doc)

    if best[2] is None:
        return None, None
    return best[2], best[1]


def source_ref_file_line(file: str, line: Optional[int]) -> str:
    if line is None:
        return f"<code>{esc(file)}</code>"
    return f"<code>{esc(file)}:{line}</code>"


def category_counts(tcs: List[Dict[str, str]]) -> str:
    c = Counter(t["category"] for t in tcs)
    if not c:
        return "ללא"
    return ", ".join([f"{k}:{v}" for k, v in sorted(c.items())])


def render_ics_refs(ics_refs: Dict[str, List[Dict[str, Optional[str]]]], doc_key: str) -> str:
    items = []
    for r in ics_refs.get(doc_key, []):
        line_txt = f":{r['line']}" if r["line"] is not None else ""
        items.append(
            "<li>"
            f"<span class='small'>{esc(r['needle'])}</span><br>"
            f"<code>{esc(r['file'])}{line_txt}</code>"
            "</li>"
        )
    return "<ul class='src-list'>" + "".join(items) + "</ul>"


def render_tc_table(title: str, tcs: List[Dict[str, str]], collapsed: bool = True) -> str:
    if not tcs:
        return f"<h3>{esc(title)}</h3><p class='muted'>אין TCIDs להצגה.</p>"

    rows_html = []
    for t in tcs:
        s = t["source"]
        src = f"<code>{esc(s['file'])} | {esc(s['sheet'])} | row {s['row']} | cols {esc(s['columns'])}</code>"
        rows_html.append(
            "<tr>"
            f"<td><code>{esc(t['tcid'])}</code></td>"
            f"<td>{esc(t['category'])}</td>"
            f"<td>{esc(t['active_date'])}</td>"
            f"<td>{esc(t['desc'])}</td>"
            f"<td>{src}</td>"
            "</tr>"
        )

    table = (
        "<div class='table-wrap'><table>"
        "<thead><tr><th>TCID</th><th>קטגוריה</th><th>Active Date</th><th>תיאור</th><th>מקור מדויק</th></tr></thead>"
        "<tbody>"
        + "".join(rows_html)
        + "</tbody></table></div>"
    )
    if collapsed:
        return f"<details><summary>{esc(title)} ({len(tcs)} פריטים)</summary>{table}</details>"
    return f"<h3>{esc(title)}</h3>{table}"


def render_tspc_table(title: str, rows: List[Dict[str, str]]) -> str:
    if not rows:
        return f"<h3>{esc(title)}</h3><p class='muted'>אין שורות להצגה.</p>"

    trs = []
    for r in rows:
        ws_src = [
            source_ref_file_line(r["source"]["file"], r["source"].get("name_line")),
            source_ref_file_line(r["source"]["file"], r["source"].get("desc_line"))
            if r["source"].get("desc_line")
            else "",
        ]
        src_parts = [x for x in ws_src if x]
        if r.get("ics_doc_key"):
            src_parts.append(source_ref_file_line(str(ICS_TXT[r["ics_doc_key"]]), r["ics_line"]))
        src_html = "<br>".join(src_parts)
        trs.append(
            "<tr>"
            f"<td><code>{esc(r['name'])}</code></td>"
            f"<td><code>{esc(r['item'])}</code></td>"
            f"<td>{esc(r['capability'])}</td>"
            f"<td>{esc(r['status'])}</td>"
            f"<td>{esc(r['mandatory'])}</td>"
            f"<td>{esc(r['value'])}</td>"
            f"<td>{src_html}</td>"
            "</tr>"
        )
    return (
        f"<h3>{esc(title)}</h3>"
        "<div class='table-wrap'><table>"
        "<thead><tr>"
        "<th>TSPC</th><th>ICS Item</th><th>משמעות (Capability)</th><th>סטטוס ICS</th>"
        "<th>Mandatory ב-Workspace</th><th>Value ב-Workspace</th><th>מקור מדויק</th>"
        "</tr></thead><tbody>"
        + "".join(trs)
        + "</tbody></table></div>"
    )


def profile_list_html(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return "<span class='muted'>אין</span>"
    out = []
    for r in rows:
        out.append(
            "<li>"
            f"{esc(r['capability'])} "
            f"<span class='tag'>{esc(r['status'] or '?')}</span> "
            f"<code>{esc(r['name'])}</code> "
            f"<span class='muted'>Value={esc(r['value'])}</span>"
            "</li>"
        )
    return "<ul class='mini-list'>" + "".join(out) + "</ul>"


def build_tspc_entries(rows: List[Dict[str, str]], profile: str) -> List[Dict[str, str]]:
    out = []
    for r in rows:
        capability, status = split_desc_status(r["desc"])
        item = ics_item_from_tspc_name(r["name"])

        if profile in ("DIS", "BAS", "HRS"):
            docs = [profile]
        else:
            d = r["desc"].lower()
            if "hogp" in d or "hid iso service" in d or "hids" in d:
                docs = ["HOGP", "HID11"]
            elif "hid11" in d or "hid device role" in d or "human interface device v1.0" in d:
                docs = ["HID11", "HOGP"]
            else:
                docs = ["HOGP", "HID11"]

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


def split_mand_opt_cond(
    rows: List[Dict[str, str]],
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    mandatory = [r for r in rows if r["mandatory"] == "TRUE"]
    optional = [r for r in rows if r["status"].startswith("O")]
    conditional = [
        r
        for r in rows
        if r["mandatory"] == "FALSE" and not r["status"].startswith("O")
    ]
    return mandatory, optional, conditional


def main() -> None:
    pqw6 = parse_pqw6(WORKSPACE_PQW6)

    rows_bas = read_sheet_rows(TCRL_GATT, "BAS")
    rows_dis = read_sheet_rows(TCRL_GATT, "DIS")
    rows_hrs = read_sheet_rows(TCRL_GATT, "HRS")
    rows_hogp = read_sheet_rows(TCRL_GATT, "HOGP")
    rows_hid11 = read_sheet_rows(TCRL_TRAD, "HID11")
    rows_hrp = read_sheet_rows(TCRL_GATT, "HRP")
    rows_iopt = read_sheet_rows(TCRL_IOPT, "IOPT")

    bas_tc = extract_tc(rows_bas, "BAS/", TCRL_GATT, "BAS")
    dis_tc = extract_tc(rows_dis, "DIS/", TCRL_GATT, "DIS")
    hrs_tc = extract_tc(rows_hrs, "HRS/", TCRL_GATT, "HRS")
    hogp_tc = extract_tc(rows_hogp, "HOGP/", TCRL_GATT, "HOGP")
    hid11_tc = extract_tc(rows_hid11, "HID11/", TCRL_TRAD, "HID11")
    hrp_col_tc = extract_tc(rows_hrp, "HRP/COL/", TCRL_GATT, "HRP")

    iopt_bas = extract_tc(rows_iopt, "IOPT/BAS/", TCRL_IOPT, "IOPT")
    iopt_dis = extract_tc(rows_iopt, "IOPT/DIS/", TCRL_IOPT, "IOPT")
    iopt_hrs = extract_tc(rows_iopt, "IOPT/HRS/", TCRL_IOPT, "IOPT")
    iopt_hid = extract_tc(rows_iopt, "IOPT/HID/", TCRL_IOPT, "IOPT")

    dis_rows = [r for r in pqw6["DIS"] if r["name"].startswith("TSPC_")]
    bas_rows = [r for r in pqw6["BAS"] if r["name"].startswith("TSPC_")]
    hrs_rows = [r for r in pqw6["HRS"] if r["name"].startswith("TSPC_")]
    hid_rows = [
        r
        for r in pqw6["IOPT"]
        if r["name"].startswith("TSPC_") and ("hid" in r["desc"].lower() or "hogp" in r["desc"].lower())
    ]

    dis_tspc = build_tspc_entries(dis_rows, "DIS")
    bas_tspc = build_tspc_entries(bas_rows, "BAS")
    hrs_tspc = build_tspc_entries(hrs_rows, "HRS")
    hid_tspc = build_tspc_entries(hid_rows, "HID")

    dis_m, dis_o, dis_c = split_mand_opt_cond(dis_tspc)
    bas_m, bas_o, bas_c = split_mand_opt_cond(bas_tspc)
    hrs_m, hrs_o, hrs_c = split_mand_opt_cond(hrs_tspc)
    hid_m, hid_o, hid_c = split_mand_opt_cond(hid_tspc)

    line_get_tc = find_line(PTSCONTROL_PY, r"def get_test_case_list\(self, project_name\):")
    line_is_active = find_line(PTSCONTROL_PY, r"IsActiveTestCase\(project_name, test_case_name\)")

    line_tspc_formula = find_first_line_containing(
        ICS_RST_SCRIPT,
        "parameter_name = 'TSPC_{}_{}'.format(profile, table.Item[i].replace('/', '_'))",
    )
    line_tspc_grid = find_first_line_containing(
        ICS_RST_SCRIPT, "grid = [['Parameter Name', 'Selected', 'Description']]"
    )
    line_tspc_desc = find_first_line_containing(
        ICS_RST_SCRIPT, "description = f'{table.Capability[i]} ({table.Status[i]})'"
    )

    ics_refs = find_ics_refs()

    summary_rows_html = "".join(
        [
            "<tr><td>DIS</td>"
            f"<td>{profile_list_html(dis_m)}</td>"
            f"<td>{profile_list_html(dis_o)}<p class='small muted'>Conditional: {len(dis_c)} (ראו פענוח TSPC)</p></td>"
            f"<td>{source_ref_file_line(str(WORKSPACE_PQW6), pqw6['_project_lines']['DIS'])}<br>{source_ref_file_line(str(ICS_TXT['DIS']), None)}</td></tr>",
            "<tr><td>BAS</td>"
            f"<td>{profile_list_html(bas_m)}</td>"
            f"<td>{profile_list_html(bas_o)}<p class='small muted'>Conditional: {len(bas_c)} (ראו פענוח TSPC)</p></td>"
            f"<td>{source_ref_file_line(str(WORKSPACE_PQW6), pqw6['_project_lines']['BAS'])}<br>{source_ref_file_line(str(ICS_TXT['BAS']), None)}</td></tr>",
            "<tr><td>HRS</td>"
            f"<td>{profile_list_html(hrs_m)}</td>"
            f"<td>{profile_list_html(hrs_o)}<p class='small muted'>Conditional: {len(hrs_c)} (ראו פענוח TSPC)</p></td>"
            f"<td>{source_ref_file_line(str(WORKSPACE_PQW6), pqw6['_project_lines']['HRS'])}<br>{source_ref_file_line(str(ICS_TXT['HRS']), None)}</td></tr>",
            "<tr><td>HID</td>"
            f"<td>{profile_list_html(hid_m)}</td>"
            f"<td>{profile_list_html(hid_o)}<p class='small muted'>Conditional: {len(hid_c)} (ראו פענוח TSPC)</p></td>"
            f"<td>{source_ref_file_line(str(WORKSPACE_PQW6), pqw6['_project_lines']['IOPT'])}<br>{source_ref_file_line(str(ICS_TXT['HOGP']), None)}<br>{source_ref_file_line(str(ICS_TXT['HID11']), None)}</td></tr>",
        ]
    )

    css = """
:root {
  --bg: #f4f8fb;
  --panel: #ffffff;
  --panel-alt: #f8fcff;
  --ink: #1f2a37;
  --muted: #5d6876;
  --primary: #085a8c;
  --line: #d8e4ee;
  --shadow: 0 12px 30px rgba(15, 49, 74, 0.10);
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
table { width: 100%; border-collapse: collapse; min-width: 920px; }
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
.alert { border: 1px solid #f0e2a9; background: #fff8de; color: #6f5e21; border-radius: 11px; padding: 10px; }
.okbox { border: 1px solid #bfe6d8; background: #ebfaf4; color: #0f644d; border-radius: 11px; padding: 10px; }
.footer-note { margin-top: 10px; font-size: 0.9rem; color: #536271; }
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }
@media (max-width: 1180px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { position: static; max-height: none; }
  .span-6, .span-4 { grid-column: span 12; }
}
"""

    js = """
const navButtons = Array.from(document.querySelectorAll('.nav-btn'));
const panels = Array.from(document.querySelectorAll('.panel'));
const searchInput = document.getElementById('searchInput');

function getActivePanel() {
  return document.querySelector('.panel.active');
}

function activatePanel(id) {
  panels.forEach((p) => {
    p.classList.toggle('active', p.id === 'panel-' + id);
  });
  navButtons.forEach((b) => {
    b.classList.toggle('active', b.dataset.panelTarget === id);
  });
  applySearch();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

navButtons.forEach((btn) => {
  btn.addEventListener('click', () => activatePanel(btn.dataset.panelTarget));
});

function applySearch() {
  const q = (searchInput.value || '').trim().toLowerCase();
  const panel = getActivePanel();
  if (!panel) return;
  panel.querySelectorAll('tbody tr').forEach((tr) => {
    const txt = tr.innerText.toLowerCase();
    tr.style.display = (!q || txt.includes(q)) ? '' : 'none';
  });
}

searchInput.addEventListener('input', applySearch);
document.getElementById('clearSearchBtn').addEventListener('click', () => {
  searchInput.value = '';
  applySearch();
  searchInput.focus();
});

function setDetails(openState) {
  const panel = getActivePanel();
  if (!panel) return;
  panel.querySelectorAll('details').forEach((d) => {
    d.open = openState;
  });
}

document.getElementById('openDetailsBtn').addEventListener('click', () => setDetails(true));
document.getElementById('closeDetailsBtn').addEventListener('click', () => setDetails(false));
"""

    html_doc = f"""<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>דו"ח PTS - DIS/BAS/HRS/HID</title>
  <style>{css}</style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <h1>דו"ח PTS אמין ומלא<br>DIS / BAS / HRS / HID</h1>
        <p>ניווט מהיר בין כל המידע, כולל מקורות ברמת שורה כשזמין.</p>
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
        <div><b>ספירת TCIDs</b></div>
        <div>DIS: {len(dis_tc)} | BAS: {len(bas_tc)} | HRS: {len(hrs_tc)}</div>
        <div>HOGP: {len(hogp_tc)} | HID11: {len(hid11_tc)}</div>
        <div style="margin-top:6px;">Runtime Active:</div>
        <div>{source_ref_file_line(str(PTSCONTROL_PY), line_is_active)}</div>
      </div>
    </aside>

    <main class="content">
      <section class="hero">
        <h2>דו"ח מלא: חובה מול אופציונלי ב-PTS עבור DIS / BAS / HRS / HID</h2>
        <p>
          הדוח שומר את כל המידע מהגרסה הקודמת, מתקן את הבלבול <b>HRC→HRS</b>,
          ומוסיף פירוש אנושי מלא לכל מזהה <code>TSPC_*</code>.
        </p>
        <p class="small muted">
          קובץ Workspace: {source_ref_file_line(str(WORKSPACE_PQW6), None)}.
          שורת <code>HRC</code> לא נמצאה: <code>&lt;PROJECT_INFORMATION NAME="HRC"</code>.
          שורת <code>HRS</code>: {source_ref_file_line(str(WORKSPACE_PQW6), pqw6['_project_lines']['HRS'])}.
        </p>
      </section>

      <section class="toolbar">
        <input id="searchInput" type="search" placeholder="חיפוש בתוך הטבלאות בפאנל הפעיל (TSPC, TCID, תיאור, מקור...)" />
        <button id="clearSearchBtn" type="button">נקה חיפוש</button>
        <button id="openDetailsBtn" type="button">פתח הכל בפאנל</button>
        <button id="closeDetailsBtn" type="button">סגור הכל בפאנל</button>
      </section>

      <section class="panel active" id="panel-overview">
        <h3 class="section-title">סקירה מהירה</h3>
        <div class="grid">
          <div class="card span-4"><p class="kpi">{len(dis_m)} חובה / {len(dis_o)} לא-חובה</p><p class="kpi-sub">DIS</p></div>
          <div class="card span-4"><p class="kpi">{len(bas_m)} חובה / {len(bas_o)} לא-חובה</p><p class="kpi-sub">BAS</p></div>
          <div class="card span-4"><p class="kpi">{len(hrs_m)} חובה / {len(hrs_o)} לא-חובה</p><p class="kpi-sub">HRS</p></div>

          <div class="card span-12 okbox">
            <b>על מזהי TSPC:</b> יש מידע מלא מעבר לשם הטכני. לכל מזהה יש Capability, סטטוס ICS (M/O/C.x),
            ערך Workspace ומקור מדויק. פירוט מלא בפאנל <b>פענוח TSPC</b>.
          </div>

          <div class="card span-12">
            <h3>טבלת סיכום חובה/אופציונלי (עם משמעות אנושית)</h3>
            <div class="table-wrap">
              <table>
                <thead><tr><th>פרופיל</th><th>חובה</th><th>לא-חובה (Optional/Conditional)</th><th>מקור</th></tr></thead>
                <tbody>{summary_rows_html}</tbody>
              </table>
            </div>
          </div>

          <div class="card span-6 alert">
            <b>אמינות:</b> רשימת Active הסופית נקבעת בזמן ריצה ע"י
            <code>IsActiveTestCase(project_name, test_case_name)</code> ולא רק מקובץ ה-Workspace.
            מקור: {source_ref_file_line(str(PTSCONTROL_PY), line_get_tc)} ו-{source_ref_file_line(str(PTSCONTROL_PY), line_is_active)}.
          </div>

          <div class="card span-6">
            <b>ספירת TCIDs לפי TCRL</b>
            <ul class="mini-list">
              <li>DIS: {len(dis_tc)} ({category_counts(dis_tc)})</li>
              <li>BAS: {len(bas_tc)} ({category_counts(bas_tc)})</li>
              <li>HRS: {len(hrs_tc)} ({category_counts(hrs_tc)})</li>
              <li>HOGP: {len(hogp_tc)} ({category_counts(hogp_tc)})</li>
              <li>HID11: {len(hid11_tc)} ({category_counts(hid11_tc)})</li>
            </ul>
            <p class="small muted">מקור: {source_ref_file_line(str(TCRL_GATT), None)} + {source_ref_file_line(str(TCRL_TRAD), None)}.</p>
          </div>
        </div>
      </section>

      <section class="panel" id="panel-tspc">
        <h3 class="section-title">פענוח מזהי TSPC</h3>
        <div class="grid">
          <div class="card span-12">
            <p>
              לפי הקוד המקומי, מזהה <code>TSPC</code> נבנה מפורמט פריט ICS:
              <code>TSPC_{{PROFILE}}_{{Item עם _ במקום /}}</code>.
              לכן לדוגמה <code>TSPC_DIS_2_1</code> מייצג פריט ICS <code>DIS 2/1</code>.
            </p>
            <p class="small muted">
              מקור: {source_ref_file_line(str(ICS_RST_SCRIPT), line_tspc_grid)},
              {source_ref_file_line(str(ICS_RST_SCRIPT), line_tspc_formula)},
              {source_ref_file_line(str(ICS_RST_SCRIPT), line_tspc_desc)}.
            </p>
          </div>
          <div class="card span-12">{render_tspc_table("DIS - כל שורות TSPC עם פירוש", dis_tspc)}</div>
          <div class="card span-12">{render_tspc_table("BAS - כל שורות TSPC עם פירוש", bas_tspc)}</div>
          <div class="card span-12">{render_tspc_table("HRS - כל שורות TSPC עם פירוש", hrs_tspc)}</div>
          <div class="card span-12">{render_tspc_table("HID (מתוך IOPT) - שורות TSPC עם פירוש", hid_tspc)}</div>
        </div>
      </section>

      <section class="panel" id="panel-dis">
        <h3 class="section-title">DIS - פירוט מלא</h3>
        <div class="grid">
          <div class="card span-12">{render_tspc_table("שורות DIS ב-Workspace", dis_tspc)}</div>
          <div class="card span-12"><h3>אסמכתאות ICS ל-DIS</h3>{render_ics_refs(ics_refs, "DIS")}</div>
          <div class="card span-12">{render_tc_table("כל TCIDs של DIS מתוך TCRL", dis_tc, collapsed=True)}</div>
        </div>
      </section>

      <section class="panel" id="panel-bas">
        <h3 class="section-title">BAS - פירוט מלא</h3>
        <div class="grid">
          <div class="card span-12">{render_tspc_table("שורות BAS ב-Workspace", bas_tspc)}</div>
          <div class="card span-12"><h3>אסמכתאות ICS ל-BAS</h3>{render_ics_refs(ics_refs, "BAS")}</div>
          <div class="card span-12">{render_tc_table("כל TCIDs של BAS מתוך TCRL", bas_tc, collapsed=True)}</div>
        </div>
      </section>

      <section class="panel" id="panel-hrs">
        <h3 class="section-title">HRS - פירוט מלא (תיקון HRC→HRS)</h3>
        <div class="grid">
          <div class="card span-12">{render_tspc_table("שורות HRS ב-Workspace", hrs_tspc)}</div>
          <div class="card span-12"><h3>אסמכתאות ICS ל-HRS</h3>{render_ics_refs(ics_refs, "HRS")}</div>
          <div class="card span-12">{render_tc_table("כל TCIDs של HRS מתוך TCRL", hrs_tc, collapsed=True)}</div>
        </div>
      </section>

      <section class="panel" id="panel-hid">
        <h3 class="section-title">HID - פירוט מלא (IOPT + HOGP + HID11)</h3>
        <div class="grid">
          <div class="card span-12 alert">
            שים לב: עבור חלק משורות HID ב-IOPT (למשל <code>TSPC_IOPT_1_14</code>, <code>TSPC_IOPT_2_31b</code>)
            לא נמצאה התאמה טקסטואלית חד-חד ערכית ב-ICS של HOGP/HID11.
            במקרים אלו המקור המדויק הוא שורת ה-Workspace עצמה.
          </div>
          <div class="card span-12">{render_tspc_table("שורות HID/HOGP מתוך IOPT", hid_tspc)}</div>
          <div class="card span-6"><h3>אסמכתאות ICS ל-HOGP</h3>{render_ics_refs(ics_refs, "HOGP")}</div>
          <div class="card span-6"><h3>אסמכתאות ICS ל-HID11</h3>{render_ics_refs(ics_refs, "HID11")}</div>
          <div class="card span-12">{render_tc_table("כל TCIDs של HOGP מתוך TCRL", hogp_tc, collapsed=True)}</div>
          <div class="card span-12">{render_tc_table("כל TCIDs של HID11 מתוך TCRL", hid11_tc, collapsed=True)}</div>
        </div>
      </section>

      <section class="panel" id="panel-iopt">
        <h3 class="section-title">IOPT Cross-Profile Verification TCIDs</h3>
        <div class="grid">
          <div class="card span-12">{render_tc_table("IOPT/BAS", iopt_bas, collapsed=False)}</div>
          <div class="card span-12">{render_tc_table("IOPT/DIS", iopt_dis, collapsed=False)}</div>
          <div class="card span-12">{render_tc_table("IOPT/HRS", iopt_hrs, collapsed=False)}</div>
          <div class="card span-12">{render_tc_table("IOPT/HID", iopt_hid, collapsed=False)}</div>
        </div>
      </section>

      <section class="panel" id="panel-appendix">
        <h3 class="section-title">נספח שקיפות: סעיף HRC מהגרסה הקודמת</h3>
        <div class="grid">
          <div class="card span-12 alert">
            בגרסה הקודמת פורש HRC כ-HRP Collector. אחרי התיקון שלך, הדוח הראשי עבר ל-HRS.
            המידע הישן נשמר כאן כדי לא לאבד שום פרט.
          </div>
          <div class="card span-12"><h3>אסמכתאות ICS ל-HRP Collector</h3>{render_ics_refs(ics_refs, "HRP")}</div>
          <div class="card span-12">{render_tc_table("HRP/COL TCIDs (מהדוח הקודם)", hrp_col_tc, collapsed=True)}</div>
        </div>
      </section>

      <section class="panel" id="panel-sources">
        <h3 class="section-title">מקורות ששימשו בפועל</h3>
        <div class="grid">
          <div class="card span-12">
            <ul class="src-list">
              <li>{source_ref_file_line(str(WORKSPACE_PQW6), None)} — Workspace PICS/PIXIT.</li>
              <li><code>{esc(str(TCRL_GATT))}</code>, <code>{esc(str(TCRL_TRAD))}</code>, <code>{esc(str(TCRL_IOPT))}</code> — TCRL package.</li>
              <li><code>{esc(str(ICS_TXT['BAS']))}</code>, <code>{esc(str(ICS_TXT['DIS']))}</code>, <code>{esc(str(ICS_TXT['HRS']))}</code>, <code>{esc(str(ICS_TXT['HRP']))}</code>, <code>{esc(str(ICS_TXT['HOGP']))}</code>, <code>{esc(str(ICS_TXT['HID11']))}</code> — טקסטי ICS.</li>
              <li>{source_ref_file_line(str(PTSCONTROL_PY), line_get_tc)} ו-{source_ref_file_line(str(PTSCONTROL_PY), line_is_active)} — Runtime Active.</li>
              <li>{source_ref_file_line(str(ICS_RST_SCRIPT), line_tspc_formula)} — נוסחת יצירת TSPC.</li>
            </ul>
          </div>
          <div class="card span-12">
            <h3>קישורים רשמיים (Bluetooth SIG)</h3>
            <ul class="src-list">
              <li><a href="https://www.bluetooth.com/specifications/specs/battery-service/" target="_blank" rel="noopener">Battery Service (BAS)</a></li>
              <li><a href="https://www.bluetooth.com/specifications/specs/device-information-service/" target="_blank" rel="noopener">Device Information Service (DIS)</a></li>
              <li><a href="https://www.bluetooth.com/specifications/specs/heart-rate-service-1-0/" target="_blank" rel="noopener">Heart Rate Service (HRS)</a></li>
              <li><a href="https://www.bluetooth.com/specifications/specs/hid-over-gatt-profile/" target="_blank" rel="noopener">HID over GATT Profile (HOGP)</a></li>
              <li><a href="https://www.bluetooth.com/specifications/specs/human-interface-device-profile-1-1-1/" target="_blank" rel="noopener">Human Interface Device Profile 1.1.1 (HID11)</a></li>
            </ul>
          </div>
        </div>
      </section>

      <div class="footer-note">
        נבנה אוטומטית מתוך מקורות מקומיים שנבדקו. קובץ פלט: <code>{esc(str(OUT_HTML))}</code>.
      </div>
    </main>
  </div>
  <script>{js}</script>
</body>
</html>
"""

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html_doc, encoding="utf-8")
    OUT_HTML_ALIAS.write_text(html_doc, encoding="utf-8")

    print(f"WROTE {OUT_HTML}")
    print(f"WROTE {OUT_HTML_ALIAS}")
    print(f"SIZE  {OUT_HTML.stat().st_size} bytes")


if __name__ == "__main__":
    main()
