#!/usr/bin/env python3
"""
Investigate PTS installers for:
- WiX Burn signatures
- MSI/CAB payloads and extraction with dedicated tools (msiinfo/msiextract/cabextract)
- ETS/XML inventory and TCID prefixes from ETS/XML
- Extra pass for PTSFirmwareUpgradeSoftware.exe
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


TCID_PATTERN = (
    r"(?<![A-Za-z0-9_/])"
    r"[A-Z][A-Z0-9_]{1,20}"
    r"(?:/[A-Z0-9][A-Za-z0-9_.-]{0,40}){1,8}"
    r"/B[A-Z]{1,3}-[0-9A-Za-z]{1,10}-[A-Z]"
    r"(?![A-Za-z0-9_/])"
)

BURN_TOKENS = [
    b"WixAttachedContainer",
    b"BootstrapperApplicationData",
    b".wixburn",
    b"Burn v",
    b"WixBundle",
    b"BootstrapperApplication",
]


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding="utf-8",
        errors="ignore",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def sha12(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:12]


def rel(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def write_tsv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def find_burn_signatures(files: list[Path], base: Path, out_tsv: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for fp in files:
        try:
            data = fp.read_bytes()
        except OSError:
            continue
        for token in BURN_TOKENS:
            start = 0
            while True:
                idx = data.find(token, start)
                if idx < 0:
                    break
                rows.append(
                    {
                        "file": rel(fp, base),
                        "token": token.decode("ascii", errors="ignore"),
                        "offset": str(idx),
                    }
                )
                start = idx + 1
    write_tsv(out_tsv, ["file", "token", "offset"], rows)
    return rows


def list_payload_files(candidates: list[Path], base: Path, out_tsv: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for p in sorted(candidates):
        rows.append(
            {
                "type": p.suffix.lower().lstrip("."),
                "size_bytes": str(p.stat().st_size),
                "path": rel(p, base),
            }
        )
    write_tsv(out_tsv, ["type", "size_bytes", "path"], rows)
    return rows


def process_msi_cab(
    payloads: list[Path],
    base: Path,
    out_dir: Path,
    msiinfo_bin: str,
    msiextract_bin: str,
    cabextract_bin: str,
) -> list[dict[str, str]]:
    logs = out_dir / "logs"
    msi_extract = out_dir / "extract_msi"
    cab_extract = out_dir / "extract_cab"
    logs.mkdir(parents=True, exist_ok=True)
    msi_extract.mkdir(parents=True, exist_ok=True)
    cab_extract.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for p in payloads:
        ptype = p.suffix.lower().lstrip(".")
        sid = sha12(str(p))
        if ptype == "msi":
            table_log = logs / f"msi_tables_{sid}.log"
            extract_log = logs / f"msi_extract_{sid}.log"
            extract_dest = msi_extract / sid
            extract_dest.mkdir(parents=True, exist_ok=True)

            pr1 = run([msiinfo_bin, "tables", str(p)])
            table_log.write_text(pr1.stdout + ("\nSTDERR:\n" + pr1.stderr if pr1.stderr else ""), encoding="utf-8")

            pr2 = run([msiextract_bin, "-C", str(extract_dest), str(p)])
            extract_log.write_text(pr2.stdout + ("\nSTDERR:\n" + pr2.stderr if pr2.stderr else ""), encoding="utf-8")
            extracted_files = len([x for x in extract_dest.rglob("*") if x.is_file()])

            rows.append(
                {
                    "type": "msi",
                    "path": rel(p, base),
                    "size_bytes": str(p.stat().st_size),
                    "list_status": "ok" if pr1.returncode == 0 else f"failed({pr1.returncode})",
                    "extract_status": "ok" if pr2.returncode == 0 else f"failed({pr2.returncode})",
                    "list_log": rel(table_log, base),
                    "extract_log": rel(extract_log, base),
                    "extract_dest": rel(extract_dest, base),
                    "extracted_files": str(extracted_files),
                }
            )
        elif ptype == "cab":
            list_log = logs / f"cab_list_{sid}.log"
            extract_log = logs / f"cab_extract_{sid}.log"
            extract_dest = cab_extract / sid
            extract_dest.mkdir(parents=True, exist_ok=True)

            pr1 = run([cabextract_bin, "-l", str(p)])
            list_log.write_text(pr1.stdout + ("\nSTDERR:\n" + pr1.stderr if pr1.stderr else ""), encoding="utf-8")

            pr2 = run([cabextract_bin, "-d", str(extract_dest), str(p)])
            extract_log.write_text(pr2.stdout + ("\nSTDERR:\n" + pr2.stderr if pr2.stderr else ""), encoding="utf-8")
            extracted_files = len([x for x in extract_dest.rglob("*") if x.is_file()])

            rows.append(
                {
                    "type": "cab",
                    "path": rel(p, base),
                    "size_bytes": str(p.stat().st_size),
                    "list_status": "ok" if pr1.returncode == 0 else f"failed({pr1.returncode})",
                    "extract_status": "ok" if pr2.returncode == 0 else f"failed({pr2.returncode})",
                    "list_log": rel(list_log, base),
                    "extract_log": rel(extract_log, base),
                    "extract_dest": rel(extract_dest, base),
                    "extracted_files": str(extracted_files),
                }
            )
    return rows


def collect_ets_xml_inventory(search_roots: list[Path], base: Path, out_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rg_bin = "/Users/tzoharlary/.vscode-insiders/extensions/openai.chatgpt-0.5.75-darwin-x64/bin/macos-x86_64/rg"
    files = []
    for root in search_roots:
        if not root.exists():
            continue
        files.extend([p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".ets", ".xml"}])
    files = sorted(set(files))

    inventory_rows: list[dict[str, str]] = []
    hits_rows: list[dict[str, str]] = []
    prefix_counter: Counter[str] = Counter()

    for fp in files:
        pr = run([rg_bin, "-a", "-n", "-o", "-P", TCID_PATTERN, str(fp)])
        raw = pr.stdout
        tcids = set()
        for line in raw.splitlines():
            parts = line.split(":", 2)
            if len(parts) == 3:
                tcids.add(parts[2].strip())
        inventory_rows.append(
            {
                "file": rel(fp, base),
                "size_bytes": str(fp.stat().st_size),
                "tcid_count": str(len(tcids)),
            }
        )
        if tcids:
            prefixes = sorted({t.split("/", 1)[0] for t in tcids if "/" in t})
            for pfx in prefixes:
                prefix_counter[pfx] += 1
            hits_rows.append(
                {
                    "file": rel(fp, base),
                    "tcid_count": str(len(tcids)),
                    "prefixes": ", ".join(prefixes),
                    "sample_tcids": ", ".join(sorted(tcids)[:10]),
                }
            )

    write_tsv(out_dir / "ets_xml_inventory.tsv", ["file", "size_bytes", "tcid_count"], inventory_rows)
    write_tsv(out_dir / "ets_xml_with_tcids.tsv", ["file", "tcid_count", "prefixes", "sample_tcids"], hits_rows)

    with (out_dir / "ets_xml_prefix_counts.tsv").open("w", encoding="utf-8") as f:
        f.write("prefix\tfile_count\n")
        for pfx, cnt in sorted(prefix_counter.items(), key=lambda x: (-x[1], x[0])):
            f.write(f"{pfx}\t{cnt}\n")

    return inventory_rows, hits_rows


def extract_firmware_exe(
    firmware_exe: Path,
    out_root: Path,
    sevenzip_bin: str,
) -> dict[str, str]:
    raw_dir = out_root / "rawscan"
    exp_dir = out_root / "expanded"
    logs_dir = out_root / "logs"
    for d in (raw_dir, exp_dir, logs_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    log_main = logs_dir / "firmware_7z_extract_main.log"
    log_fallback = logs_dir / "firmware_7z_extract_fallback_tsharp.log"

    # Prefer regular extraction first; some EXEs fail with forced parser mode (-t#).
    pr = run([sevenzip_bin, "x", "-y", str(firmware_exe), f"-o{raw_dir}"])
    log_main.write_text(pr.stdout + ("\nSTDERR:\n" + pr.stderr if pr.stderr else ""), encoding="utf-8")
    used_mode = "regular"
    if pr.returncode != 0:
        pr = run([sevenzip_bin, "x", "-y", "-t#", str(firmware_exe), f"-o{raw_dir}"])
        log_fallback.write_text(pr.stdout + ("\nSTDERR:\n" + pr.stderr if pr.stderr else ""), encoding="utf-8")
        used_mode = "tsharp_fallback"

    # one extra recursive layer for common archive/container extensions
    archive_exts = {".exe", ".msi", ".cab", ".zip", ".7z", ".rar"}
    extracted_count = 0
    for fp in sorted([p for p in raw_dir.rglob("*") if p.is_file() and p.suffix.lower() in archive_exts]):
        dest = exp_dir / sha12(str(fp))
        dest.mkdir(parents=True, exist_ok=True)
        prx = run([sevenzip_bin, "x", "-y", str(fp), f"-o{dest}"])
        (logs_dir / f"expand_{sha12(str(fp))}.log").write_text(
            prx.stdout + ("\nSTDERR:\n" + prx.stderr if prx.stderr else ""),
            encoding="utf-8",
        )
        if prx.returncode == 0:
            extracted_count += 1

    rg_bin = "/Users/tzoharlary/.vscode-insiders/extensions/openai.chatgpt-0.5.75-darwin-x64/bin/macos-x86_64/rg"
    scan_roots = [raw_dir, exp_dir]
    pr_tcid = run([rg_bin, "-a", "-n", "-o", "-P", TCID_PATTERN] + [str(x) for x in scan_roots])
    tcid_raw = out_root / "firmware_tcid_matches_raw.txt"
    tcid_raw.write_text(pr_tcid.stdout, encoding="utf-8")
    tcids = set()
    for line in pr_tcid.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3:
            tcids.add(parts[2].strip())

    xml_ets = [p for p in raw_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".xml", ".ets"}]
    xml_ets += [p for p in exp_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".xml", ".ets"}]
    xml_ets = sorted(set(xml_ets))

    return {
        "main_extract_status": "ok" if pr.returncode == 0 else f"failed({pr.returncode})",
        "main_extract_mode": used_mode,
        "rawscan_dir": out_root.joinpath("rawscan").as_posix(),
        "expanded_dir": out_root.joinpath("expanded").as_posix(),
        "expanded_archives_ok": str(extracted_count),
        "xml_ets_files": str(len(xml_ets)),
        "tcid_unique_count": str(len(tcids)),
        "tcid_raw_file": rel(tcid_raw, out_root.parents[1]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="/Users/tzoharlary/zephyrproject/pts_offline_inventory")
    ap.add_argument("--pts-files", default="/Users/tzoharlary/PTS files")
    ap.add_argument("--sevenzip", default="/usr/local/bin/7z")
    ap.add_argument("--msiinfo", default="/usr/local/bin/msiinfo")
    ap.add_argument("--msiextract", default="/usr/local/bin/msiextract")
    ap.add_argument("--cabextract", default="/usr/local/bin/cabextract")
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    pts_files = Path(args.pts_files).resolve()
    out_dir = ws / "reports" / "payload_investigation"
    out_dir.mkdir(parents=True, exist_ok=True)

    setup_exe = pts_files / "pts_setup_8_11_1.exe"
    firmware_exe = pts_files / "PTSFirmwareUpgradeSoftware.exe"

    setup_related_exes = []
    setup_related_exes.append(setup_exe)
    for root in [
        ws / "tmp" / "rawscan",
        ws / "extracted" / "rawscan_2",
        ws / "extracted" / "rawscan_3",
        ws / "scan_workspace" / "expanded_archives",
    ]:
        if root.exists():
            setup_related_exes.extend([p for p in root.rglob("*.exe") if p.is_file()])
    setup_related_exes = sorted(set(setup_related_exes))

    burn_rows = find_burn_signatures(setup_related_exes, ws.parent, out_dir / "burn_signature_hits.tsv")

    # Payload files for setup investigation
    payload_roots = [
        ws / "tmp" / "rawscan",
        ws / "extracted" / "rawscan_2",
        ws / "extracted" / "rawscan_3",
        ws / "scan_workspace" / "expanded_archives",
    ]
    payload_files = []
    for root in payload_roots:
        if root.exists():
            payload_files.extend([p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".msi", ".cab"}])
    payload_files = sorted(set(payload_files))
    list_payload_files(payload_files, ws.parent, out_dir / "payload_msi_cab_list.tsv")

    msi_cab_rows = process_msi_cab(
        payload_files, ws.parent, out_dir, args.msiinfo, args.msiextract, args.cabextract
    )
    write_tsv(
        out_dir / "msi_cab_tool_status.tsv",
        ["type", "path", "size_bytes", "list_status", "extract_status", "list_log", "extract_log", "extract_dest", "extracted_files"],
        msi_cab_rows,
    )

    ets_search_roots = [
        ws / "extracted",
        ws / "tmp" / "rawscan",
        ws / "scan_workspace" / "expanded_archives",
        out_dir / "extract_msi",
        out_dir / "extract_cab",
    ]
    ets_inventory, ets_with_hits = collect_ets_xml_inventory(ets_search_roots, ws.parent, out_dir)

    # Extra firmware pass
    firmware_out = out_dir / "firmware_scan"
    firmware_summary = extract_firmware_exe(firmware_exe, firmware_out, args.sevenzip)
    write_tsv(
        out_dir / "firmware_summary.tsv",
        [
            "main_extract_status",
            "main_extract_mode",
            "rawscan_dir",
            "expanded_dir",
            "expanded_archives_ok",
            "xml_ets_files",
            "tcid_unique_count",
            "tcid_raw_file",
        ],
        [firmware_summary],
    )

    # Human summary markdown
    burn_files = sorted({r["file"] for r in burn_rows})
    burn_token_counts = Counter(r["token"] for r in burn_rows)
    msi_count = len([r for r in msi_cab_rows if r["type"] == "msi"])
    cab_count = len([r for r in msi_cab_rows if r["type"] == "cab"])
    msi_fail = len([r for r in msi_cab_rows if r["type"] == "msi" and ("failed" in r["extract_status"] or "failed" in r["list_status"])])
    cab_fail = len([r for r in msi_cab_rows if r["type"] == "cab" and ("failed" in r["extract_status"] or "failed" in r["list_status"])])

    md = []
    md.append("# PTS Payload Investigation")
    md.append("")
    md.append("## Burn Signature Check")
    md.append(f"- setup exe checked: `{rel(setup_exe, ws.parent)}`")
    md.append(f"- files checked for burn tokens: **{len(setup_related_exes)}**")
    md.append(f"- files with burn token hits: **{len(burn_files)}**")
    md.append(f"- detailed hits: `pts_offline_inventory/reports/payload_investigation/burn_signature_hits.tsv`")
    if burn_token_counts:
        md.append("- token counts:")
        for token, cnt in sorted(burn_token_counts.items(), key=lambda x: (-x[1], x[0])):
            md.append(f"  - `{token}`: {cnt}")
    md.append("")
    md.append("## Payload MSI/CAB")
    md.append(f"- payload files found: MSI={msi_count}, CAB={cab_count}")
    md.append(f"- payload list (size+path): `pts_offline_inventory/reports/payload_investigation/payload_msi_cab_list.tsv`")
    md.append(f"- MSI/CAB tool status: `pts_offline_inventory/reports/payload_investigation/msi_cab_tool_status.tsv`")
    md.append(f"- failures: MSI={msi_fail}, CAB={cab_fail}")
    md.append("")
    md.append("## ETS/XML Inventory")
    md.append(f"- ETS/XML files scanned: **{len(ets_inventory)}**")
    md.append(f"- ETS/XML files with TCID hits: **{len(ets_with_hits)}**")
    md.append(f"- inventory: `pts_offline_inventory/reports/payload_investigation/ets_xml_inventory.tsv`")
    md.append(f"- hits: `pts_offline_inventory/reports/payload_investigation/ets_xml_with_tcids.tsv`")
    md.append(f"- prefix counts from ETS/XML hits: `pts_offline_inventory/reports/payload_investigation/ets_xml_prefix_counts.tsv`")
    md.append("")
    md.append("## Firmware EXE Extra Pass")
    md.append(f"- firmware exe checked: `{rel(firmware_exe, ws.parent)}`")
    md.append(f"- summary: `pts_offline_inventory/reports/payload_investigation/firmware_summary.tsv`")
    md.append("")
    (out_dir / "investigation_summary.md").write_text("\n".join(md), encoding="utf-8")

    print(f"burn_hits={len(burn_rows)}")
    print(f"payload_files={len(msi_cab_rows)}")
    print(f"ets_xml_scanned={len(ets_inventory)}")
    print(f"ets_xml_with_tcid_hits={len(ets_with_hits)}")
    print(f"firmware_tcid_unique_count={firmware_summary['tcid_unique_count']}")
    print(f"summary={out_dir / 'investigation_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
