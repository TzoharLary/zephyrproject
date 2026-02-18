#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path


KEYWORDS = ["ets", "suite", "test", "module", "bluetooth", "pts", "assets"]

ETS_TRACE_PATTERNS = [
    ("Bluetooth\\\\Ets", r"Bluetooth\\\\Ets"),
    ("\\\\Ets\\\\", r"\\\\Ets\\\\"),
    ("Executable Test Suite", r"Executable\s+Test\s+Suite"),
    ("ETS Update", r"ETS\s+Update"),
    ("*.ets", r"\*\.ets"),
    ("*.xml", r"\*\.xml"),
    ("EtsUpdate", r"EtsUpdate"),
]

DOWNLOAD_KEYWORD_RE = r"(?i)\b(download|payload|package|cache|container|testsuite|module)\b"
URL_RE = r"(?i)https?://[^\\s\"'<>]+"
DOMAIN_RE = r"(?i)\\b(?:[a-z0-9-]+\\.)+(?:com|org|net|io|edu|gov|biz|co)(?:/[^\\s\"'<>]*)?"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        encoding="utf-8",
        errors="ignore",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def clean_text(s: str, limit: int = 240) -> str:
    s = s.replace("\t", " ").replace("\r", " ").replace("\n", " ")
    s = "".join(ch if (ch.isprintable() or ch == " ") else " " for ch in s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > limit:
        s = s[: limit - 3] + "..."
    return s


def rel(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def write_tsv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in headers})


def parse_msi_table(msi: Path, table: str, msiinfo: str) -> list[dict[str, str]]:
    pr = run([msiinfo, "export", str(msi), table])
    if pr.returncode != 0:
        raise RuntimeError(f"msiinfo export failed for {table}: {pr.stderr.strip()}")

    lines = [ln.rstrip("\r") for ln in pr.stdout.splitlines() if ln.strip()]
    if len(lines) < 3:
        return []

    headers = lines[0].split("\t")
    rows: list[dict[str, str]] = []
    for ln in lines[2:]:
        cols = ln.split("\t")
        if len(cols) < len(headers):
            cols += [""] * (len(headers) - len(cols))
        elif len(cols) > len(headers):
            cols = cols[: len(headers)]
        if cols and cols[0] == table:
            continue
        rows.append({h: c for h, c in zip(headers, cols)})
    return rows


def decode_msi_name(name: str) -> str:
    if not name:
        return ""
    if "|" in name:
        return name.split("|", 1)[1]
    return name


def decode_default_dir(default_dir: str) -> str:
    if not default_dir:
        return ""
    target = default_dir.split(":", 1)[0]
    if target == ".":
        return ""
    return decode_msi_name(target)


def resolve_directory_paths(directory_rows: list[dict[str, str]]) -> dict[str, str]:
    by_id = {r.get("Directory", ""): r for r in directory_rows}
    memo: dict[str, str] = {}

    def _resolve(dir_id: str) -> str:
        if not dir_id:
            return "TARGETDIR"
        if dir_id in memo:
            return memo[dir_id]
        if dir_id == "TARGETDIR":
            memo[dir_id] = "TARGETDIR"
            return memo[dir_id]

        row = by_id.get(dir_id)
        if not row:
            memo[dir_id] = dir_id
            return memo[dir_id]

        parent = row.get("Directory_Parent", "") or "TARGETDIR"
        base = _resolve(parent)
        part = decode_default_dir(row.get("DefaultDir", ""))

        if not part:
            out = base
        elif base == "TARGETDIR":
            out = f"TARGETDIR/{part}"
        else:
            out = f"{base}/{part}"
        memo[dir_id] = out
        return out

    for did in by_id:
        _resolve(did)
    return memo


def load_tsv_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            clean = {k.strip(): (v.strip() if isinstance(v, str) else "") for k, v in row.items() if k is not None}
            rows.append(clean)
    return rows


def detect_file_type(path: Path) -> str:
    pr = run(["file", "-b", str(path)])
    t = pr.stdout.strip() if pr.returncode == 0 else "unknown"
    return clean_text(t, 300)


def get_rg_bin() -> str:
    candidates = [
        shutil.which("rg"),
        "/Users/tzoharlary/.vscode-insiders/extensions/openai.chatgpt-0.5.75-darwin-x64/bin/macos-x86_64/rg",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise RuntimeError("rg binary not found")


def rg_search(rg_bin: str, regex: str, roots: list[Path], ignore_case: bool = True, only_matching: bool = False) -> list[tuple[str, str, str]]:
    real_roots = [r for r in roots if r.exists()]
    if not real_roots:
        return []

    cmd = [rg_bin, "-a", "-n", "-H", "-P"]
    if ignore_case:
        cmd.append("-i")
    if only_matching:
        cmd.append("-o")
    cmd += [regex] + [str(r) for r in real_roots]
    pr = run(cmd)

    out: list[tuple[str, str, str]] = []
    for ln in pr.stdout.splitlines():
        parts = ln.split(":", 2)
        if len(parts) != 3:
            continue
        out.append((parts[0], parts[1], parts[2]))
    return out


def load_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="ignore")


def discover_burn_manifests(root: Path) -> list[Path]:
    manifests: list[Path] = []
    if not root.exists():
        return manifests
    for fp in root.rglob("*"):
        if not fp.is_file():
            continue
        if fp.stat().st_size > 5_000_000:
            continue
        try:
            text = load_text(fp)
        except OSError:
            continue
        if "BurnManifest" in text and "<Payload " in text:
            manifests.append(fp)
    return sorted(set(manifests))


def burn_manifest_indicators(manifest: Path, repo_root: Path) -> list[dict[str, str]]:
    text = load_text(manifest)
    out: list[dict[str, str]] = []
    patterns = [
        ("payload_file", r"<Payload[^>]*\bFilePath=\"([^\"]+)\""),
        ("container_file", r"<Container[^>]*\bFilePath=\"([^\"]+)\""),
        ("msi_package_id", r"<MsiPackage[^>]*\bId=\"([^\"]+)\""),
        ("msu_package_id", r"<MsuPackage[^>]*\bId=\"([^\"]+)\""),
        ("exe_package_id", r"<ExePackage[^>]*\bId=\"([^\"]+)\""),
        ("cache_id", r"\bCacheId=\"([^\"]+)\""),
        ("download_url", r"\bDownloadUrl=\"([^\"]+)\""),
    ]
    for itype, rx in patterns:
        for m in re.finditer(rx, text, flags=re.IGNORECASE):
            val = m.group(1)
            ctx = text[max(0, m.start() - 90) : m.end() + 90]
            out.append(
                {
                    "indicator_type": itype,
                    "match": clean_text(val, 160),
                    "file": rel(manifest, repo_root),
                    "line": "1",
                    "context": clean_text(ctx, 260),
                }
            )
    return out


def binary_string_indicators(path: Path, repo_root: Path) -> list[dict[str, str]]:
    pr = run(["strings", "-n", "8", str(path)])
    if pr.returncode != 0:
        return []
    out: list[dict[str, str]] = []
    url_rx = re.compile(URL_RE, flags=re.IGNORECASE)
    dom_rx = re.compile(DOMAIN_RE, flags=re.IGNORECASE)
    kw_rx = re.compile(DOWNLOAD_KEYWORD_RE, flags=re.IGNORECASE)
    for i, ln in enumerate(pr.stdout.splitlines(), start=1):
        if len(ln) > 600:
            continue
        line = ln.strip()
        if not line:
            continue

        for m in url_rx.finditer(line):
            val = m.group(0)
            if len(val) < 16 or "." not in val:
                continue
            out.append(
                {
                    "indicator_type": "url",
                    "match": clean_text(val, 160),
                    "file": rel(path, repo_root),
                    "line": str(i),
                    "context": clean_text(line, 260),
                }
            )

        for m in dom_rx.finditer(line):
            val = m.group(0)
            if len(val) < 8 or "." not in val:
                continue
            out.append(
                {
                    "indicator_type": "domain",
                    "match": clean_text(val, 160),
                    "file": rel(path, repo_root),
                    "line": str(i),
                    "context": clean_text(line, 260),
                }
            )

        m_kw = kw_rx.search(line)
        if m_kw:
            out.append(
                {
                    "indicator_type": "keyword",
                    "match": clean_text(m_kw.group(0), 60),
                    "file": rel(path, repo_root),
                    "line": str(i),
                    "context": clean_text(line, 260),
                }
            )
    return out


def main() -> int:
    ws = Path("/Users/tzoharlary/zephyrproject/pts_offline_inventory").resolve()
    repo_root = ws.parent
    report_root = ws / "reports" / "payload_investigation"
    report_root.mkdir(parents=True, exist_ok=True)

    msiinfo = "/usr/local/bin/msiinfo"
    msi_path = report_root / "setup_scan" / "rawscan" / "5.msi"
    if not msi_path.exists():
        msi_path = ws / "tmp" / "rawscan" / "5.msi"

    tables_dir = report_root / "msi_tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    table_names = ["Directory", "Component", "File", "Feature", "FeatureComponents", "Media"]
    table_rows: dict[str, list[dict[str, str]]] = {}

    for t in table_names:
        rows = parse_msi_table(msi_path, t, msiinfo)
        table_rows[t] = rows
        if rows:
            write_tsv(tables_dir / f"{t}.tsv", list(rows[0].keys()), rows)
        else:
            write_tsv(tables_dir / f"{t}.tsv", ["empty"], [])

    directory_paths = resolve_directory_paths(table_rows["Directory"])
    component_dir = {r.get("Component", ""): r.get("Directory_", "") for r in table_rows["Component"]}

    file_install_rows: list[dict[str, str]] = []
    keyword_hits: list[dict[str, str]] = []

    for r in table_rows["File"]:
        component = r.get("Component_", "")
        dir_id = component_dir.get(component, "")
        install_dir = directory_paths.get(dir_id, dir_id or "TARGETDIR")
        file_name = decode_msi_name(r.get("FileName", ""))
        install_path = f"{install_dir}/{file_name}" if install_dir else file_name
        size = int(r.get("FileSize", "0") or "0")

        out = {
            "File": r.get("File", ""),
            "Component": component,
            "DirectoryId": dir_id,
            "InstallDir": install_dir,
            "FileName": file_name,
            "InstallPath": install_path,
            "FileSize": str(size),
            "Version": r.get("Version", ""),
            "Language": r.get("Language", ""),
            "Sequence": r.get("Sequence", ""),
        }
        file_install_rows.append(out)

        hay = f"{install_path} {component}".lower()
        for kw in KEYWORDS:
            if kw in hay:
                keyword_hits.append(
                    {
                        "keyword": kw,
                        "File": out["File"],
                        "InstallPath": install_path,
                        "Component": component,
                        "FileSize": str(size),
                    }
                )

    file_install_rows.sort(key=lambda x: int(x["FileSize"]), reverse=True)
    write_tsv(
        report_root / "msi_file_install_map.tsv",
        ["File", "Component", "DirectoryId", "InstallDir", "FileName", "InstallPath", "FileSize", "Version", "Language", "Sequence"],
        file_install_rows,
    )
    write_tsv(
        report_root / "msi_keyword_hits.tsv",
        ["keyword", "File", "InstallPath", "Component", "FileSize"],
        keyword_hits,
    )

    feature_to_components: dict[str, list[str]] = defaultdict(list)
    for r in table_rows["FeatureComponents"]:
        feature_to_components[r.get("Feature_", "")].append(r.get("Component_", ""))

    feature_summary_rows: list[dict[str, str]] = []
    for fr in table_rows["Feature"]:
        fid = fr.get("Feature", "")
        feature_summary_rows.append(
            {
                "Feature": fid,
                "Title": fr.get("Title", ""),
                "Description": fr.get("Description", ""),
                "Components": str(len(feature_to_components.get(fid, []))),
            }
        )
    write_tsv(report_root / "msi_feature_summary.tsv", ["Feature", "Title", "Description", "Components"], feature_summary_rows)

    media_rows = table_rows["Media"]
    media_embedded = [m for m in media_rows if m.get("Cabinet", "").startswith("#")]

    # CAB inventory based on msi_cab_tool_status
    status_rows = load_tsv_rows(report_root / "msi_cab_tool_status.tsv")
    cab_rows = [r for r in status_rows if r.get("type", "").lower() == "cab"]

    cab_full_rows: list[dict[str, str]] = []
    cab_top_rows: list[dict[str, str]] = []

    for cab in cab_rows:
        cab_path = repo_root / cab.get("path", "")
        extract_dest = repo_root / cab.get("extract_dest", "")
        file_rows: list[dict[str, str]] = []
        for fp in sorted(extract_dest.rglob("*")):
            if not fp.is_file():
                continue
            sz = fp.stat().st_size
            ftype = detect_file_type(fp)
            file_rows.append(
                {
                    "cab_path": rel(cab_path, repo_root),
                    "extract_dest": rel(extract_dest, repo_root),
                    "file": rel(fp, extract_dest),
                    "size_bytes": str(sz),
                    "file_type": ftype,
                }
            )
        file_rows.sort(key=lambda x: int(x["size_bytes"]), reverse=True)
        cab_full_rows.extend(file_rows)
        cab_top_rows.extend(file_rows[:30])

    write_tsv(
        report_root / "cab_inventory_full.tsv",
        ["cab_path", "extract_dest", "file", "size_bytes", "file_type"],
        cab_full_rows,
    )
    write_tsv(
        report_root / "cab_inventory_top30.tsv",
        ["cab_path", "extract_dest", "file", "size_bytes", "file_type"],
        cab_top_rows,
    )

    # ETS trace hits across all extracted content
    rg_bin = get_rg_bin()
    trace_roots = [
        report_root / "setup_scan",
        report_root / "extract_msi",
        report_root / "extract_cab",
        ws / "tmp" / "rawscan",
        ws / "extracted" / "rawscan_2",
        ws / "extracted" / "rawscan_3",
    ]

    trace_hits: list[dict[str, str]] = []
    seen_trace: set[tuple[str, str, str, str]] = set()
    for label, regex in ETS_TRACE_PATTERNS:
        matches = rg_search(rg_bin, regex, trace_roots, ignore_case=True, only_matching=False)
        rx = re.compile(regex, flags=re.IGNORECASE)
        for file_path, line_no, text in matches:
            m = rx.search(text)
            found = m.group(0) if m else label
            row = {
                "pattern": label,
                "file": rel(Path(file_path), repo_root),
                "line": line_no,
                "match": clean_text(found, 120),
                "context": clean_text(text, 260),
            }
            k = (row["pattern"], row["file"], row["line"], row["context"])
            if k in seen_trace:
                continue
            seen_trace.add(k)
            trace_hits.append(row)

    trace_hits.sort(key=lambda r: (r["pattern"], r["file"], int(r["line"]) if r["line"].isdigit() else 0))
    write_tsv(
        report_root / "string_hits_ets_and_paths.tsv",
        ["pattern", "file", "line", "match", "context"],
        trace_hits,
    )

    # Burn download indicators - focused extraction from manifest + strings.
    indicators: list[dict[str, str]] = []
    seen_ind: set[tuple[str, str, str, str]] = set()

    setup_scan_root = report_root / "setup_scan"
    manifests = discover_burn_manifests(setup_scan_root)
    for mf in manifests:
        for row in burn_manifest_indicators(mf, repo_root):
            key = (row["indicator_type"], row["match"], row["file"], row["context"])
            if key in seen_ind:
                continue
            seen_ind.add(key)
            indicators.append(row)

    binary_sources = [
        Path("/Users/tzoharlary/PTS files/pts_setup_8_11_1.exe"),
        setup_scan_root / "rawscan" / "2.exe",
        setup_scan_root / "rawscan" / "3.exe",
        setup_scan_root / "rawscan" / "4.NDP481-Web.exe",
    ]
    for bp in binary_sources:
        if not bp.exists():
            continue
        for row in binary_string_indicators(bp, repo_root):
            key = (row["indicator_type"], row["match"], row["file"], row["context"])
            if key in seen_ind:
                continue
            seen_ind.add(key)
            indicators.append(row)

    indicators.sort(key=lambda r: (r["indicator_type"], r["file"], int(r["line"]) if r["line"].isdigit() else 0, r["match"]))
    write_tsv(
        report_root / "burn_download_indicators.tsv",
        ["indicator_type", "match", "file", "line", "context"],
        indicators,
    )

    # Markdown: msi summary
    msi_summary_md = report_root / "msi_tables_summary.md"
    uniq_dirs = sorted({r["InstallDir"] for r in file_install_rows})
    biggest = file_install_rows[:15]

    md = []
    md.append("# MSI Tables Summary (pts_setup_8_11_1)\n")
    md.append(f"- קובץ MSI מנותח: `{rel(msi_path, repo_root)}`")
    md.append(f"- Directory rows: **{len(table_rows['Directory'])}**")
    md.append(f"- Component rows: **{len(table_rows['Component'])}**")
    md.append(f"- File rows: **{len(table_rows['File'])}**")
    md.append(f"- Feature rows: **{len(table_rows['Feature'])}**")
    md.append(f"- FeatureComponents rows: **{len(table_rows['FeatureComponents'])}**")
    md.append(f"- Media rows: **{len(table_rows['Media'])}**\n")

    md.append("## Media / Cabinets")
    if media_rows:
        md.append("| DiskId | Cabinet | LastSequence |")
        md.append("|---|---|---|")
        for m in media_rows:
            md.append(f"| {m.get('DiskId','')} | `{m.get('Cabinet','')}` | {m.get('LastSequence','')} |")
    else:
        md.append("- אין שורות בטבלת Media")

    md.append("\n## Feature Summary")
    md.append("| Feature | Title | Components |")
    md.append("|---|---|---|")
    for fr in feature_summary_rows:
        md.append(f"| `{fr['Feature']}` | {fr['Title']} | {fr['Components']} |")

    md.append("\n## קבצים גדולים ב-MSI (Top 15)")
    md.append("| File | InstallPath | Size (bytes) |")
    md.append("|---|---|---|")
    for r in biggest:
        md.append(f"| `{r['File']}` | `{r['InstallPath']}` | {r['FileSize']} |")

    md.append("\n## חיפוש מילות ETS/Test במודל ההתקנה")
    if keyword_hits:
        md.append("| Keyword | InstallPath | Size |")
        md.append("|---|---|---|")
        for r in keyword_hits[:40]:
            md.append(f"| `{r['keyword']}` | `{r['InstallPath']}` | {r['FileSize']} |")
        if len(keyword_hits) > 40:
            md.append(f"- ... ועוד {len(keyword_hits)-40} התאמות בקובץ `msi_keyword_hits.tsv`")
    else:
        md.append("- לא נמצאו התאמות למילות ETS/Test/Module/Bluetooth/PTS/Assets בשמות קבצים/נתיבי התקנה בטבלאות MSI.")

    md.append("\n## תיקיות התקנה ייחודיות (סימבוליות)")
    for d in uniq_dirs:
        md.append(f"- `{d}`")

    msi_summary_md.write_text("\n".join(md), encoding="utf-8")

    # Markdown: cab top files
    cab_md = report_root / "cab_inventory_top_files.md"
    cab_grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in cab_top_rows:
        cab_grouped[r["cab_path"]].append(r)

    cmd = []
    cmd.append("# CAB Inventory Top Files\n")
    cmd.append(f"- קובץ מלא לכל הקבצים: `pts_offline_inventory/reports/payload_investigation/cab_inventory_full.tsv`")
    cmd.append(f"- Top 30 לכל CAB: `pts_offline_inventory/reports/payload_investigation/cab_inventory_top30.tsv`\n")

    for cab_path in sorted(cab_grouped):
        rows = cab_grouped[cab_path]
        cmd.append(f"## `{cab_path}`")
        cmd.append("| File | Size (bytes) | Type |")
        cmd.append("|---|---|---|")
        for r in rows:
            cmd.append(f"| `{r['file']}` | {r['size_bytes']} | {r['file_type']} |")
        cmd.append("")

    cab_md.write_text("\n".join(cmd), encoding="utf-8")

    # Final conclusion markdown
    final_md = report_root / "final_conclusion.md"

    ets_path_like = [r for r in trace_hits if r["pattern"] in {"Bluetooth\\\\Ets", "\\\\Ets\\\\", "*.ets", "ETS Update", "Executable Test Suite"}]
    has_ets_path_hits = len(ets_path_like) > 0

    url_hits = [r for r in indicators if r["indicator_type"] == "url"]
    keyword_hits_dl = [r for r in indicators if r["indicator_type"] == "keyword"]
    download_url_hits = [r for r in indicators if r["indicator_type"] == "download_url"]
    payload_file_hits = [r for r in indicators if r["indicator_type"] == "payload_file"]
    container_file_hits = [r for r in indicators if r["indicator_type"] == "container_file"]
    msi_pkg_hits = [r for r in indicators if r["indicator_type"] == "msi_package_id"]
    msu_pkg_hits = [r for r in indicators if r["indicator_type"] == "msu_package_id"]

    concl = []
    concl.append("# Final Conclusion\n")
    concl.append("## מסקנה")

    if has_ets_path_hits:
        concl.append("**א) ה-setup מכיל עקבות ETS בפורמט לא גלוי/לא מזוהה.**")
        concl.append("- נמצאו עקבות ישירים שמרמזים על ETS. ראה `string_hits_ets_and_paths.tsv`.")
    else:
        concl.append("**ב) ה-setup לא מכיל ETS; הוא מתקין תשתית/Prerequisites בלבד, ו-ETS צפוי להגיע מחבילת ETS Update נפרדת.**")
        concl.append("- בטבלאות MSI שנפרסו אין רכיבי ETS/Test Suite; ה-MSI שנמצא הוא `MSXML 4.0 redist`.")
        concl.append("- ב-CAB וב-MSI שחולצו לא נמצאו קבצי `.ets`/`.xml` שמייצגים מאגר ETS של PTS.")
        concl.append("- בסריקות מחרוזות לא נמצאו עקבות נתיב ETS קלאסיים (`Bluetooth\\Ets`, `\\Ets\\`, `*.ets`).")

    concl.append("\n## ראיות תומכות")
    concl.append(f"- MSI summary: `pts_offline_inventory/reports/payload_investigation/msi_tables_summary.md`")
    concl.append(f"- CAB inventory: `pts_offline_inventory/reports/payload_investigation/cab_inventory_top_files.md`")
    concl.append(f"- ETS string hits: `pts_offline_inventory/reports/payload_investigation/string_hits_ets_and_paths.tsv`")
    concl.append(f"- Download indicators: `pts_offline_inventory/reports/payload_investigation/burn_download_indicators.tsv`")

    concl.append("\n## אינדיקציות Download/External packages")
    concl.append(f"- URL hits: **{len(url_hits)}**")
    concl.append(f"- keyword hits (download/payload/package/cache/container/...): **{len(keyword_hits_dl)}**")
    concl.append(f"- payload_file hits (מתוך BurnManifest): **{len(payload_file_hits)}**")
    concl.append(f"- container_file hits (מתוך BurnManifest): **{len(container_file_hits)}**")
    concl.append(f"- MsiPackage IDs: **{len(msi_pkg_hits)}**, MsuPackage IDs: **{len(msu_pkg_hits)}**")
    concl.append(f"- DownloadUrl attributes ב-BurnManifest: **{len(download_url_hits)}**")
    if len(download_url_hits) == 0:
        concl.append("- לא נמצאו `DownloadUrl=` מפורשים במניפסטים שנחצבו מתוך ה-bundle.")
    concl.append("- קיימים קבצי bootstrapper פנימיים (`NDP481-Web.exe`, `vcredist/VC_redist`), מה שמחזק מודל של prerequisites ולא מאגר ETS.")

    concl.append("\n## מה חסר כדי להפיק inventory אמיתי של TCIDs על mac")
    concl.append("1. חבילת ETS Update עצמה (קובץ/ארכיון ETS) או תיקיית ETS לאחר עדכון על Windows.")
    concl.append("2. אם אפשר, Snapshot של תיקיית ETS מותקנת בפועל ממכונת PTS לאחר Apply ETS Updates.")
    concl.append("3. לאחר קבלת החבילה/תיקייה: להריץ את סורק ה-TCID הקיים על הקבצים האלה בלבד ולהפיק רשימת Prefix/TCID מלאה.")

    final_md.write_text("\n".join(concl), encoding="utf-8")

    print(f"msi_files={len(file_install_rows)}")
    print(f"cab_files={len(cab_full_rows)}")
    print(f"ets_trace_hits={len(trace_hits)}")
    print(f"download_indicators={len(indicators)}")
    print(f"outputs={report_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
