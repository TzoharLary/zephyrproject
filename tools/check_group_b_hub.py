#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from group_b_hub_data import PROFILE_IDS, build_group_b_hub_data, enforce_group_b_hub_source_policy
except Exception:
    from tools.group_b_hub_data import PROFILE_IDS, build_group_b_hub_data, enforce_group_b_hub_source_policy  # type: ignore


def _scan_utf8_markdown(repo_root: Path) -> list[str]:
    issues: list[str] = []
    root = repo_root / "tools" / "templates" / "pts_report_he" / "Group_B_data"
    for path in sorted(root.rglob("*.md")):
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            issues.append(f"Invalid UTF-8: {path} ({exc})")
    return issues


def _summarize_profile_thresholds(data: dict, findings_min: int, obs_min: int) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    group_b = data.get("group_b", {})
    for kind in ("logic_analysis", "structure_analysis"):
        rows = group_b.get(kind, {}) if isinstance(group_b, dict) else {}
        for pid in PROFILE_IDS:
            row = rows.get(pid, {}) if isinstance(rows, dict) else {}
            findings = len(row.get("core_findings", []) if isinstance(row.get("core_findings"), list) else [])
            obs = len(row.get("source_observations", []) if isinstance(row.get("source_observations"), list) else [])
            if findings < findings_min:
                failures.append(f"{kind}.{pid}: findings={findings} < {findings_min}")
            if obs < obs_min:
                failures.append(f"{kind}.{pid}: source_observations={obs} < {obs_min}")
            for warning in row.get("warnings", []) if isinstance(row.get("warnings"), list) else []:
                warnings.append(f"{kind}.{pid}: {warning.get('code')}: {warning.get('message_he')}")
    return failures, warnings


def _print_readiness_summary(data: dict) -> None:
    summary = ((((data.get("group_b") or {}).get("readiness_gates") or {}).get("summary")) or {})
    print("Readiness summary:")
    for key in (
        "profiles",
        "spec_sync_complete",
        "logic_analysis_baselined",
        "structure_analysis_baselined",
        "phase1_subset_decided",
        "logic_analysis_reviewed",
        "structure_analysis_reviewed",
        "ready_for_impl_phase1",
    ):
        print(f"  {key}: {summary.get(key)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Group B Hub data/schema/readiness thresholds.")
    parser.add_argument("--repo-root", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--findings-min", type=int, default=5, help="Minimum findings per profile doc kind")
    parser.add_argument("--source-obs-min", type=int, default=4, help="Minimum source observations per profile doc kind")
    parser.add_argument("--json-out", default="", help="Optional path to write hub-data JSON snapshot")
    parser.add_argument("--allow-threshold-fail", action="store_true", help="Do not fail process on threshold misses")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    failures: list[str] = []

    utf8_issues = _scan_utf8_markdown(repo_root)
    failures.extend(utf8_issues)

    try:
        data = build_group_b_hub_data(repo_root)
    except Exception as exc:  # pragma: no cover - CLI surfacing
        print(f"[FAIL] build_group_b_hub_data: {exc}", file=sys.stderr)
        return 2

    try:
        enforce_group_b_hub_source_policy(data)
    except Exception as exc:  # pragma: no cover - CLI surfacing
        print(f"[FAIL] enforce_group_b_hub_source_policy: {exc}", file=sys.stderr)
        return 3

    threshold_failures, warnings = _summarize_profile_thresholds(data, args.findings_min, args.source_obs_min)
    if not args.allow_threshold_fail:
        failures.extend(threshold_failures)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote JSON snapshot: {out_path}")

    print("Group B Hub validation OK (schema/source policy)" if not utf8_issues else "Group B Hub validation partial")
    _print_readiness_summary(data)
    print("Threshold checks:")
    if threshold_failures:
        for item in threshold_failures:
            print(f"  - {item}")
    else:
        print("  - all profile docs meet baseline thresholds")

    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"  - {item}")

    if failures:
        print("Failures:")
        for item in failures:
            print(f"  - {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
