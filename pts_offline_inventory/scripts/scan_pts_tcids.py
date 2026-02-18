#!/usr/bin/env python3
"""
Recursive TCID scanner for PTS offline artifacts.

What this script does:
1. Scans source roots for files.
2. Recursively extracts archive/container candidates (zip/docx/cab/msi/exe/7z/rar)
   with 7-Zip into a workspace.
3. Runs ripgrep with a broad TCID pattern on original + expanded content.
4. Generates normalized reports (by-prefix lists, sources, summaries, full markdown views).
5. Produces coverage audit files, including which files were outside the previous scan scope.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import subprocess
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple


ARCHIVE_SUFFIXES = {
    ".zip",
    ".docx",
    ".xlsx",
    ".pptx",
    ".jar",
    ".7z",
    ".rar",
    ".cab",
    ".msi",
    ".exe",
}

# Broad enough to cover nested profile paths like:
# MESH/NODE/CFG/HBS/BV-05-C
# GATT/SR/GPA/BV-12-C
TCID_PATTERN = (
    r"(?<![A-Za-z0-9_/])"
    r"[A-Z][A-Z0-9_]{1,20}"
    r"(?:/[A-Z0-9][A-Za-z0-9_.-]{0,40}){1,8}"
    r"/B[A-Z]{1,3}-[0-9A-Za-z]{1,10}-[A-Z]"
    r"(?![A-Za-z0-9_/])"
)

RAW_MATCH_LINE = re.compile(r"^(.*?):(\d+):(.*)$")


@dataclass(frozen=True)
class FileMeta:
    path: Path
    root: str
    depth: int
    previous_scope: bool
    extracted_from: str


def sha_tag(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:12]


def workspace_rel(path_value: str | Path, workspace_root: Path) -> str:
    p = Path(path_value).resolve()
    ws = workspace_root.resolve()
    try:
        rel = p.relative_to(ws)
        return f"{ws.name}/{rel.as_posix()}"
    except ValueError:
        return p.as_posix()


def is_archive_candidate(path: Path) -> bool:
    if path.suffix.lower() in ARCHIVE_SUFFIXES:
        return True
    try:
        with path.open("rb") as f:
            magic = f.read(4)
        return magic == b"PK\x03\x04"
    except OSError:
        return False


def run_7z_extract(bin_7z: str, src: Path, dst: Path) -> Tuple[bool, str]:
    dst.mkdir(parents=True, exist_ok=True)
    cmd = [bin_7z, "x", "-y", "-bd", str(src), f"-o{dst}"]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    return proc.returncode == 0, proc.stdout


def discover_root_files(root: Path, root_name: str, previous_scope: bool) -> List[FileMeta]:
    metas: List[FileMeta] = []
    if not root.exists():
        return metas
    for p in sorted(root.rglob("*")):
        if p.is_file():
            metas.append(
                FileMeta(
                    path=p.resolve(),
                    root=root_name,
                    depth=0,
                    previous_scope=previous_scope,
                    extracted_from="",
                )
            )
    return metas


def recursive_expand_archives(
    initial_files: Iterable[FileMeta],
    workspace_dir: Path,
    bin_7z: str,
    max_depth: int,
) -> Tuple[Dict[Path, FileMeta], List[Dict[str, str]]]:
    files: Dict[Path, FileMeta] = {}
    extraction_log: List[Dict[str, str]] = []

    queue: deque[FileMeta] = deque()
    visited_archive_keys: Set[Tuple[str, int]] = set()

    for meta in initial_files:
        files[meta.path] = meta
        if is_archive_candidate(meta.path):
            queue.append(meta)

    while queue:
        meta = queue.popleft()
        if meta.depth >= max_depth:
            extraction_log.append(
                {
                    "archive_path": str(meta.path),
                    "depth": str(meta.depth),
                    "status": "skipped_max_depth",
                    "output_dir": "",
                }
            )
            continue

        key = (str(meta.path), meta.depth)
        if key in visited_archive_keys:
            continue
        visited_archive_keys.add(key)

        out_dir = workspace_dir / f"d{meta.depth + 1}_{sha_tag(str(meta.path))}"
        if out_dir.exists():
            shutil.rmtree(out_dir)

        ok, log_text = run_7z_extract(bin_7z, meta.path, out_dir)
        status = "ok" if ok else "failed_extract"
        extracted_count = 0
        if ok and out_dir.exists():
            children = sorted([p for p in out_dir.rglob("*") if p.is_file()])
            extracted_count = len(children)
            for child in children:
                child_meta = FileMeta(
                    path=child.resolve(),
                    root=meta.root,
                    depth=meta.depth + 1,
                    previous_scope=False,  # expanded content was not in previous scope
                    extracted_from=str(meta.path),
                )
                files[child_meta.path] = child_meta
                if is_archive_candidate(child_meta.path):
                    queue.append(child_meta)

        extraction_log.append(
            {
                "archive_path": str(meta.path),
                "depth": str(meta.depth),
                "status": status,
                "output_dir": str(out_dir),
                "extracted_files": str(extracted_count),
                "log_excerpt": " | ".join(log_text.splitlines()[:3]),
            }
        )

    return files, extraction_log


def run_rg_scan(rg_bin: str, roots: List[Path], pattern: str, output_file: Path) -> None:
    cmd = [rg_bin, "-a", "-n", "-o", "-P", pattern] + [str(r) for r in roots]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    # rg returns 1 when no matches.
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"rg failed: rc={proc.returncode}\n{proc.stderr}")
    output_file.write_text(proc.stdout, encoding="utf-8")


def parse_matches(
    raw_matches_file: Path, workspace_root: Path
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    tcid_to_sources: Dict[str, Set[str]] = defaultdict(set)
    file_to_tcids: Dict[str, Set[str]] = defaultdict(set)

    for line in raw_matches_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = RAW_MATCH_LINE.match(line)
        if not m:
            continue
        file_path, _, tcid = m.groups()
        tcid = tcid.strip()
        if not tcid:
            continue
        norm_path = workspace_rel(file_path, workspace_root)
        tcid_to_sources[tcid].add(norm_path)
        file_to_tcids[norm_path].add(tcid)

    return tcid_to_sources, file_to_tcids


def write_tsv(path: Path, rows: List[Dict[str, str]], headers: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_reports(
    reports_dir: Path,
    workspace_root: Path,
    tcid_to_sources: Dict[str, Set[str]],
) -> None:
    by_prefix_dir = reports_dir / "tcids_by_prefix"
    by_prefix_dir.mkdir(parents=True, exist_ok=True)

    tcids_sorted = sorted(tcid_to_sources.keys())

    # Main normalized lists
    (reports_dir / "tcids_unique_all.txt").write_text("\n".join(tcids_sorted) + "\n", encoding="utf-8")

    with (reports_dir / "tcid_unique_with_sources.tsv").open("w", encoding="utf-8") as f:
        f.write("prefix\ttcid\tsource_count\tone_source\n")
        for tcid in tcids_sorted:
            prefix = tcid.split("/", 1)[0]
            srcs = sorted(tcid_to_sources[tcid])
            f.write(f"{prefix}\t{tcid}\t{len(srcs)}\t{srcs[0]}\n")

    with (reports_dir / "tcid_all_sources.tsv").open("w", encoding="utf-8") as f:
        f.write("tcid\tsources\n")
        for tcid in tcids_sorted:
            srcs = sorted(tcid_to_sources[tcid])
            f.write(f"{tcid}\t{' ; '.join(srcs)}\n")

    prefix_to_tcids: Dict[str, List[str]] = defaultdict(list)
    for tcid in tcids_sorted:
        prefix_to_tcids[tcid.split("/", 1)[0]].append(tcid)

    # Per-prefix files
    with (reports_dir / "tcids_by_prefix_summary.tsv").open("w", encoding="utf-8") as f:
        f.write("prefix\tunique_tcid_count\tsource_file_count\tfirst5\tlast5\n")
        for prefix in sorted(prefix_to_tcids.keys()):
            tcids = sorted(prefix_to_tcids[prefix])
            sources = sorted({s for t in tcids for s in tcid_to_sources[t]})
            (by_prefix_dir / f"{prefix}.txt").write_text("\n".join(tcids) + "\n", encoding="utf-8")
            (by_prefix_dir / f"{prefix}_sources.txt").write_text(
                "\n".join(sources) + "\n", encoding="utf-8"
            )
            first5 = ", ".join(tcids[:5])
            last5 = ", ".join(tcids[-5:])
            f.write(f"{prefix}\t{len(tcids)}\t{len(sources)}\t{first5}\t{last5}\n")

    with (reports_dir / "prefix_counts_unique_tcids.txt").open("w", encoding="utf-8") as f:
        for prefix in sorted(prefix_to_tcids, key=lambda p: len(prefix_to_tcids[p]), reverse=True):
            f.write(f"{len(prefix_to_tcids[prefix]):4d} {prefix}\n")

    with (reports_dir / "prefix_brief.tsv").open("w", encoding="utf-8") as out:
        out.write("prefix\tunique_tcid_count\tfirst5\tlast5\ttop_sources\n")
        for prefix in sorted(prefix_to_tcids.keys()):
            tcids = sorted(prefix_to_tcids[prefix])
            src_file = by_prefix_dir / f"{prefix}_sources.txt"
            srcs = [x for x in src_file.read_text(encoding="utf-8").splitlines() if x.strip()]
            out.write(
                f"{prefix}\t{len(tcids)}\t{', '.join(tcids[:5])}\t{', '.join(tcids[-5:])}\t"
                f"{' | '.join(srcs[:3])}\n"
            )

    build_markdown_views(reports_dir, workspace_root, sorted(prefix_to_tcids.keys()))


def build_markdown_views(reports_dir: Path, workspace_root: Path, prefixes: List[str]) -> None:
    by_prefix_dir = reports_dir / "tcids_by_prefix"
    rows = []
    for p in prefixes:
        tcid_file = by_prefix_dir / f"{p}.txt"
        src_file = by_prefix_dir / f"{p}_sources.txt"
        tcids = [x for x in tcid_file.read_text(encoding="utf-8").splitlines() if x.strip()]
        rows.append((p, len(tcids), tcid_file, src_file))

    # prefix_table_rows.md
    lines = []
    lines.append("# Prefix Coverage Table (Complete)")
    lines.append("")
    lines.append(f"- Total prefixes: **{len(rows)}**")
    lines.append("- The table below is followed by complete per-prefix TCID and source lists.")
    lines.append("")
    lines.append("| Prefix | Unique TCIDs | Full List File | Sources File |")
    lines.append("|---|---:|---|---|")
    for p, c, tcid_file, src_file in rows:
        lines.append(
            f"| `{p}` | {c} | `{workspace_rel(tcid_file, workspace_root)}` | "
            f"`{workspace_rel(src_file, workspace_root)}` |"
        )
    lines.append("")
    lines.append("## Complete Lists By Prefix")
    for p, c, tcid_file, src_file in rows:
        tcids = [x for x in tcid_file.read_text(encoding="utf-8").splitlines() if x.strip()]
        srcs = [x for x in src_file.read_text(encoding="utf-8").splitlines() if x.strip()]
        lines.append(f"### {p}")
        lines.append("")
        lines.append(f"- Count: **{c}**")
        lines.append(f"- Full list file: `{workspace_rel(tcid_file, workspace_root)}`")
        lines.append(f"- Sources file: `{workspace_rel(src_file, workspace_root)}`")
        lines.append("")
        lines.append(f"**All TCIDs ({len(tcids)})**")
        for i, t in enumerate(tcids, 1):
            lines.append(f"{i}. `{t}`")
        lines.append("")
        lines.append(f"**All Source Files ({len(srcs)})**")
        for i, s in enumerate(srcs, 1):
            lines.append(f"{i}. `{s}`")
        lines.append("")
    (reports_dir / "prefix_table_rows.md").write_text("\n".join(lines), encoding="utf-8")

    # profiles_markdown_en.md
    lines = []
    lines.append("# Profiles Detailed View (Complete TCIDs)")
    lines.append("")
    lines.append(f"- Total profiles: **{len(rows)}**")
    lines.append("- This document now includes the full TCID list for each profile (not only first/last samples).")
    lines.append("")
    lines.append("## Quick Index")
    lines.append(" | ".join([f"[`{p}`](#{p.lower()})" for p, *_ in rows]))
    lines.append("")
    lines.append("## Summary Table")
    lines.append("| Prefix | Count | Full List File | Sources File |")
    lines.append("|---|---:|---|---|")
    for p, c, tcid_file, src_file in rows:
        lines.append(
            f"| `{p}` | {c} | `{workspace_rel(tcid_file, workspace_root)}` | "
            f"`{workspace_rel(src_file, workspace_root)}` |"
        )
    lines.append("")
    lines.append("## Detailed Profiles")
    for p, c, tcid_file, src_file in rows:
        tcids = [x for x in tcid_file.read_text(encoding="utf-8").splitlines() if x.strip()]
        srcs = [x for x in src_file.read_text(encoding="utf-8").splitlines() if x.strip()]
        lines.append(f"### {p}")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|---|---|")
        lines.append(f"| Count | **{c}** |")
        lines.append(f"| Full List File | `{workspace_rel(tcid_file, workspace_root)}` |")
        lines.append(f"| Sources File | `{workspace_rel(src_file, workspace_root)}` |")
        lines.append("")
        lines.append("**Examples (first 5)**")
        for i, t in enumerate(tcids[:5], 1):
            lines.append(f"{i}. `{t}`")
        lines.append("")
        lines.append("**Examples (last 5)**")
        for i, t in enumerate(tcids[-5:], 1):
            lines.append(f"{i}. `{t}`")
        lines.append("")
        lines.append(f"**All TCIDs ({len(tcids)})**")
        for i, t in enumerate(tcids, 1):
            lines.append(f"{i}. `{t}`")
        lines.append("")
        lines.append(f"**All Source Files ({len(srcs)})**")
        for i, s in enumerate(srcs, 1):
            lines.append(f"{i}. `{s}`")
        lines.append("")
    (reports_dir / "profiles_markdown_en.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Recursive scanner for PTS TCIDs.")
    parser.add_argument("--workspace", default="pts_offline_inventory", help="Workspace root path")
    parser.add_argument("--max-archive-depth", type=int, default=2, help="Recursive archive extraction depth")
    parser.add_argument("--rg", default="rg", help="Path to ripgrep binary")
    parser.add_argument("--sevenzip", default="7z", help="Path to 7z binary")
    args = parser.parse_args()

    ws = Path(args.workspace).resolve()
    reports_dir = ws / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    expanded_dir = ws / "scan_workspace" / "expanded_archives"
    if expanded_dir.exists():
        shutil.rmtree(expanded_dir)
    expanded_dir.mkdir(parents=True, exist_ok=True)

    extracted_root = ws / "extracted"
    rawscan_root = ws / "tmp" / "rawscan"

    root_files = []
    root_files.extend(discover_root_files(extracted_root, "extracted", previous_scope=True))
    root_files.extend(discover_root_files(rawscan_root, "tmp/rawscan", previous_scope=False))

    files_map, extraction_log = recursive_expand_archives(
        initial_files=root_files,
        workspace_dir=expanded_dir,
        bin_7z=args.sevenzip,
        max_depth=args.max_archive_depth,
    )

    # Build scan roots: original roots + all expansion directories
    scan_roots = [extracted_root, rawscan_root]
    scan_roots.extend(sorted([p for p in expanded_dir.glob("*") if p.is_dir()]))
    scan_roots = [p for p in scan_roots if p.exists()]

    raw_matches_file = reports_dir / "tcid_matches_fullscan_raw.txt"
    run_rg_scan(args.rg, scan_roots, TCID_PATTERN, raw_matches_file)

    tcid_to_sources, file_to_tcids = parse_matches(raw_matches_file, ws)
    build_reports(reports_dir, ws, tcid_to_sources)

    # Coverage files
    inventory_rows: List[Dict[str, str]] = []
    for path, meta in sorted(files_map.items(), key=lambda x: str(x[0])):
        inventory_rows.append(
            {
                "path": workspace_rel(path, ws),
                "root": meta.root,
                "depth": str(meta.depth),
                "previous_scope": "yes" if meta.previous_scope else "no",
                "extracted_from": workspace_rel(meta.extracted_from, ws)
                if meta.extracted_from
                else "",
                "archive_candidate": "yes" if is_archive_candidate(path) else "no",
                "tcid_hits": str(len(file_to_tcids.get(workspace_rel(path, ws), set()))),
            }
        )

    write_tsv(
        reports_dir / "scan_coverage_inventory.tsv",
        inventory_rows,
        ["path", "root", "depth", "previous_scope", "extracted_from", "archive_candidate", "tcid_hits"],
    )

    # Files outside previous scope (newly covered in improved scan)
    outside_scope_rows = [r for r in inventory_rows if r["previous_scope"] == "no"]
    write_tsv(
        reports_dir / "outside_previous_scope.tsv",
        outside_scope_rows,
        ["path", "root", "depth", "previous_scope", "extracted_from", "archive_candidate", "tcid_hits"],
    )

    outside_with_hits = [r for r in outside_scope_rows if int(r["tcid_hits"]) > 0]
    write_tsv(
        reports_dir / "outside_previous_scope_with_tcid_hits.tsv",
        outside_with_hits,
        ["path", "root", "depth", "previous_scope", "extracted_from", "archive_candidate", "tcid_hits"],
    )

    write_tsv(
        reports_dir / "archive_extraction_log.tsv",
        extraction_log,
        ["archive_path", "depth", "status", "output_dir", "extracted_files", "log_excerpt"],
    )

    print(f"unique_tcids={len(tcid_to_sources)}")
    print(f"unique_prefixes={len({t.split('/', 1)[0] for t in tcid_to_sources})}")
    print(f"outside_scope_files={len(outside_scope_rows)}")
    print(f"outside_scope_files_with_hits={len(outside_with_hits)}")
    print(f"reports_dir={reports_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
