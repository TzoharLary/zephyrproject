#!/usr/bin/env python3
"""
analyze_report_data_integrity.py
=================================
Capabilities:
1) Reads window.REPORT_DATA from dashboards/pts_report_he/data/report-data.js
   and runs read-only consistency checks (no source data mutation).
2) Detects common build/mapping issues, including:
   - set misalignment (for example, tcs vs mapping_tcid)
   - count mismatches across summary / meta / mapping summaries
   - wrong mapped_tcids type (objects instead of TCID strings)
   - TCIDs without conditions / bucket flags
   - gaps between mapping_authoritative and tspc_tables
   - runtime_active and run-status key inconsistencies
3) Aggregates findings into a severity-ranked Markdown report
   (ERROR/WARNING/INFO/OK) by modules A..F and by profile.

Purpose:
- Provide a fast data-integrity gate before/after build-script or mapping
  changes, so data regressions are caught before they surface in the UI.

Outputs:
- Report file: docs/reports/data_integrity_<date>.md
- Terminal summary: ERROR/WARNING/INFO/OK counts
"""

import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
DASHBOARD_ROOT = WORKSPACE / "dashboards/pts_report_he"
DATA_JS    = DASHBOARD_ROOT / "data/report-data.js"
RSJ        = DASHBOARD_ROOT / "data/run-status-state.json"
OUT_DIR    = WORKSPACE / "docs/reports"

PROFILE_LOWER = {"DIS": "dis", "BAS": "bas", "HRS": "hrs", "HID": "hid"}
PROFILES      = list(PROFILE_LOWER.keys())

SEV_ORDER = {"ERROR": 0, "WARNING": 1, "INFO": 2, "OK": 3}

# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

class Finding:
    """One check result."""
    __slots__ = ("module", "check_id", "profile", "severity", "title", "details")

    def __init__(self, module, check_id, profile, severity, title, details=""):
        self.module    = module
        self.check_id  = check_id
        self.profile   = profile
        self.severity  = severity   # ERROR | WARNING | INFO | OK
        self.title     = title
        self.details   = details


findings: list[Finding] = []


def add(module, check_id, profile, severity, title, details=""):
    findings.append(Finding(module, check_id, profile, severity, title, details))


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_data() -> dict:
    print(f"Loading {DATA_JS.name} ({DATA_JS.stat().st_size // 1024} KB)…")
    raw = DATA_JS.read_text(encoding="utf-8")
    m   = re.search(r"window\.REPORT_DATA\s*=\s*(\{.*\})\s*;?\s*$", raw, re.DOTALL)
    if not m:
        sys.exit("ERROR: could not find window.REPORT_DATA in report-data.js")
    return json.loads(m.group(1))


def load_run_status() -> dict:
    if not RSJ.exists():
        return {}
    return json.loads(RSJ.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# MODULE A: TSPC internal consistency
# ---------------------------------------------------------------------------

def check_a(data: dict):
    """TSPC internal consistency."""

    # ── A1: summary totals match tspc_tables row counts ────────────────────
    for entry in data.get("summary", []):
        p  = entry.get("profile", "?")
        pl = PROFILE_LOWER.get(p, p.lower())
        mand = len(entry.get("mandatory", []))
        opt  = len(entry.get("optional",  []))
        cond = len(entry.get("conditional", []))
        total_summary = mand + opt + cond
        tspc_count    = len(data.get("tspc_tables", {}).get(pl, []))
        if total_summary != tspc_count:
            add("A", "A1", p, "ERROR",
                f"summary bucket totals ({total_summary}) ≠ tspc_tables count ({tspc_count})",
                f"M={mand} O={opt} C={cond} → sum={total_summary}, tspc_tables.{pl}={tspc_count}")
        else:
            add("A", "A1", p, "OK",
                f"summary bucket totals match tspc_tables ({tspc_count} rows)")

    # ── A2: each TSPC row in the bucket it should be in ────────────────────
    for entry in data.get("summary", []):
        p    = entry.get("profile", "?")
        errs = []
        for row in entry.get("mandatory", []):
            if row.get("mandatory") != "TRUE":
                errs.append(f"{row.get('name')}: mandatory={row.get('mandatory')!r} status={row.get('status')!r}")
        for row in entry.get("optional", []):
            if not str(row.get("status", "")).startswith("O"):
                errs.append(f"{row.get('name')}: status={row.get('status')!r} (expected O…)")
        for row in entry.get("conditional", []):
            if row.get("mandatory") == "TRUE" or str(row.get("status", "")).startswith("O"):
                errs.append(f"{row.get('name')}: mandatory={row.get('mandatory')!r} status={row.get('status')!r}")
        if errs:
            add("A", "A2", p, "ERROR",
                f"{len(errs)} TSPC rows placed in the wrong bucket",
                "\n".join(f"  - {e}" for e in errs))
        else:
            add("A", "A2", p, "OK", "All TSPC bucket assignments match mandatory/status fields")

    # ── A3: duplicate TSPC names / items ──────────────────────────────────
    for pl_key, rows in data.get("tspc_tables", {}).items():
        p = pl_key.upper()
        names = [r.get("name") for r in rows]
        items = [r.get("item") for r in rows]
        dup_n = {k: v for k, v in Counter(names).items() if v > 1}
        dup_i = {k: v for k, v in Counter(items).items() if v > 1}
        if dup_n or dup_i:
            add("A", "A3", p, "ERROR",
                f"Duplicate TSPC entries in tspc_tables",
                f"Duplicate names: {dup_n or 'none'}  |  Duplicate items: {dup_i or 'none'}")
        else:
            add("A", "A3", p, "OK", "No duplicate TSPC names/items")

    # ── A4: meta.counts[profile].total matches tcs count ──────────────────
    meta_counts = data.get("meta", {}).get("counts", {})
    for p, pl in PROFILE_LOWER.items():
        meta_total = meta_counts.get(pl, {}).get("total", None)
        tcs_count  = len(data.get("tcs", {}).get(pl, []))
        if meta_total is None:
            add("A", "A4", p, "WARNING",
                f"meta.counts.{pl}.total is missing")
        elif meta_total != tcs_count:
            add("A", "A4", p, "ERROR",
                f"meta.counts.{pl}.total ({meta_total}) ≠ tcs.{pl} count ({tcs_count})")
        else:
            add("A", "A4", p, "OK",
                f"meta.counts.{pl}.total matches tcs count ({tcs_count})")


# ---------------------------------------------------------------------------
# MODULE B: TCID internal consistency
# ---------------------------------------------------------------------------

def check_b(data: dict):
    """TCID internal consistency."""

    # ── B1: tcs vs mapping_tcid alignment ──────────────────────────────────
    for p, pl in PROFILE_LOWER.items():
        tcs_set = {r.get("tcid") for r in data.get("tcs", {}).get(pl, [])}
        mt_rows = data.get("mapping_tcid", {}).get(p, {}).get("rows", [])
        mt_set  = {r.get("tcid") for r in mt_rows}
        only_tcs = tcs_set - mt_set
        only_mt  = mt_set  - tcs_set
        if only_tcs or only_mt:
            detail = ""
            if only_tcs:
                detail += f"  In tcs but NOT in mapping_tcid ({len(only_tcs)}): {sorted(only_tcs)[:20]}\n"
            if only_mt:
                detail += f"  In mapping_tcid but NOT in tcs ({len(only_mt)}): {sorted(only_mt)[:20]}\n"
            add("B", "B1", p, "ERROR",
                f"tcs ↔ mapping_tcid TCID sets do not align",
                detail.strip())
        else:
            add("B", "B1", p, "OK",
                f"tcs and mapping_tcid contain exactly the same {len(tcs_set)} TCIDs")

    # ── B2: mapping_tcid_summary.by_bucket.tcid_count vs row-level bucket_flags ─
    for p in PROFILES:
        mt_rows = data.get("mapping_tcid", {}).get(p, {}).get("rows", [])
        row_m   = sum(1 for r in mt_rows if r.get("bucket_flags", {}).get("mandatory"))
        row_o   = sum(1 for r in mt_rows if r.get("bucket_flags", {}).get("optional"))
        row_c   = sum(1 for r in mt_rows if r.get("bucket_flags", {}).get("conditional"))
        bb      = data.get("mapping_tcid_summary", {}).get(p, {}).get("by_bucket", {})
        sum_m   = bb.get("mandatory",    {}).get("tcid_count", None)
        sum_o   = bb.get("optional",     {}).get("tcid_count", None)
        sum_c   = bb.get("conditional",  {}).get("tcid_count", None)
        if (row_m, row_o, row_c) == (sum_m, sum_o, sum_c):
            add("B", "B2", p, "OK",
                f"mapping_tcid_summary.by_bucket counts match row-level bucket_flags (M={row_m} O={row_o} C={row_c})")
        else:
            add("B", "B2", p, "ERROR",
                f"bucket_flags totals (M={row_m} O={row_o} C={row_c}) ≠ mapping_tcid_summary (M={sum_m} O={sum_o} C={sum_c})")

    # ── B3: duplicate TCIDs ────────────────────────────────────────────────
    for p, pl in PROFILE_LOWER.items():
        for label, rows in [(f"tcs.{pl}",             data.get("tcs", {}).get(pl, [])),
                            (f"mapping_tcid.{p}",     data.get("mapping_tcid", {}).get(p, {}).get("rows", []))]:
            tcids    = [r.get("tcid") for r in rows]
            dups     = {t: n for t, n in Counter(tcids).items() if n > 1}
            if dups:
                add("B", "B3", p, "ERROR",
                    f"Duplicate TCIDs in {label}: {len(dups)} TCID(s) appear more than once",
                    "  " + ", ".join(f"{t}(×{n})" for t, n in dups.items()))
            else:
                add("B", "B3", p, "OK",
                    f"No duplicate TCIDs in {label} ({len(tcids)} rows)")

    # ── B4: mapping_authoritative rows vs tcs ─────────────────────────────
    for p, pl in PROFILE_LOWER.items():
        auth_data = data.get("mapping_authoritative", {}).get("profiles", {}).get(p, {})
        auth_rows = auth_data.get("rows", []) if isinstance(auth_data, dict) else []
        auth_tspc = {r.get("tspc_name") for r in auth_rows}
        tspc_names= {r.get("name") for r in data.get("tspc_tables", {}).get(pl, [])}
        only_auth = auth_tspc - tspc_names
        only_tspc = tspc_names - auth_tspc
        if only_auth or only_tspc:
            detail = ""
            if only_auth:
                detail += f"  In mapping_authoritative but NOT in tspc_tables ({len(only_auth)}): {sorted(only_auth)}\n"
            if only_tspc:
                detail += f"  In tspc_tables but NOT in mapping_authoritative ({len(only_tspc)}): {sorted(only_tspc)}\n"
            add("B", "B4", p, "ERROR",
                "mapping_authoritative TSPC names ≠ tspc_tables TSPC names",
                detail.strip())
        else:
            add("B", "B4", p, "OK",
                f"mapping_authoritative and tspc_tables reference the same {len(auth_tspc)} TSPC names")

    # ── B5: BAS — TCID without any conditions ─────────────────────────────
    for p in PROFILES:
        totals = data.get("mapping_tcid_summary", {}).get(p, {}).get("totals", {})
        no_cond = totals.get("without_conditions_count", 0)
        if no_cond > 0:
            mt_rows  = data.get("mapping_tcid", {}).get(p, {}).get("rows", [])
            no_c_ids = [r.get("tcid") for r in mt_rows if not r.get("conditions")]
            add("B", "B5", p, "WARNING" if no_cond < 5 else "ERROR",
                f"{no_cond} TCID(s) have no conditions (→ unclassified / bucket unknown)",
                "  " + "\n  ".join(no_c_ids[:30]))
        else:
            add("B", "B5", p, "OK",
                "All TCIDs have at least one condition entry")


# ---------------------------------------------------------------------------
# MODULE C: TSPC ↔ TCID relationship
# ---------------------------------------------------------------------------

def check_c(data: dict):
    """TSPC ↔ TCID relationship consistency."""

    # ── C1: conditions reference valid TSPC names ──────────────────────────
    for p, pl in PROFILE_LOWER.items():
        valid_tspc = {r.get("name") for r in data.get("tspc_tables", {}).get(pl, [])}
        mt_rows    = data.get("mapping_tcid", {}).get(p, {}).get("rows", [])
        bad = []
        for row in mt_rows:
            for cond in row.get("conditions", []):
                tspc_name = cond.get("tspc_name")
                if tspc_name and tspc_name not in valid_tspc:
                    bad.append(f"{row.get('tcid')} → {tspc_name}")
        if bad:
            add("C", "C1", p, "ERROR",
                f"{len(bad)} conditions reference TSPC names not in tspc_tables",
                "\n".join(f"  - {b}" for b in bad[:20]))
        else:
            add("C", "C1", p, "OK",
                "All conditions reference valid TSPC names")

    # ── C2: mapping[profile].rows[].mapped_tcids must be strings not objects ─
    for p, pl in PROFILE_LOWER.items():
        valid_tcids = {r.get("tcid") for r in data.get("tcs", {}).get(pl, [])}
        map_rows    = data.get("mapping", {}).get(p, {}).get("rows", [])
        bad_type    = []   # mapped_tcid is a dict (object) instead of a string
        bad_ref     = []   # mapped_tcid is a string but tcid not in tcs
        for row in map_rows:
            for tcid_val in row.get("mapped_tcids", []):
                if isinstance(tcid_val, dict):
                    bad_type.append((row.get("tspc_name"), tcid_val.get("tcid", "?")))
                elif isinstance(tcid_val, str) and tcid_val not in valid_tcids:
                    bad_ref.append((row.get("tspc_name"), tcid_val))
        if bad_type:
            add("C", "C2", p, "ERROR",
                f"mapping.{p}.rows[].mapped_tcids contains {len(bad_type)} full TCID objects "
                f"(dicts) instead of TCID strings — build script data type bug",
                f"  Affected TSPC rows (first 10): "
                + ", ".join(f"{tspc}→{tcid}" for tspc, tcid in bad_type[:10]))
        elif bad_ref:
            add("C", "C2", p, "ERROR",
                f"{len(bad_ref)} mapped_tcids strings reference TCIDs not found in tcs",
                "\n".join(f"  - {tspc} → {tcid}" for tspc, tcid in bad_ref[:15]))
        else:
            add("C", "C2", p, "OK",
                "All mapped_tcids are strings referencing valid TCIDs")

    # ── C3: unmapped TSPC items (no associated TCIDs at all) ───────────────
    # Note: if C2 found that mapped_tcids contains dicts instead of strings,
    # this check will also flag 100% unmapped — it's a direct consequence of the
    # same data type bug.  We detect that and downgrade severity accordingly.
    for p, pl in PROFILE_LOWER.items():
        map_rows = data.get("mapping", {}).get(p, {}).get("rows", [])
        total    = len(map_rows)

        # Check whether this profile has the C2 dict-type bug (all mapped_tcids are dicts)
        c2_bug_rows = [r for r in map_rows
                       if r.get("mapped_tcids") and
                       all(isinstance(v, dict) for v in r.get("mapped_tcids", []))]
        c2_bug_present = len(c2_bug_rows) > 0

        unmapped = [r.get("tspc_name") for r in map_rows
                    if not _any_valid_tcid(r.get("mapped_tcids", []))]

        if unmapped:
            pct  = 100 * len(unmapped) / total if total else 0
            if c2_bug_present:
                # Downgrade: this is a consequence of C2, not an independent root issue
                note = (f"⚠️ This finding is a CONSEQUENCE of the C2 data-type bug above: "
                        f"mapped_tcids contains full dict objects instead of TCID strings, so "
                        f"no TCIDs appear mapped. Fix C2 first and re-run.")
                sev = "WARNING"
            else:
                sev  = "ERROR" if pct > 80 else ("WARNING" if pct > 30 else "INFO")
                note = ""
            detail = "  " + "\n  ".join(unmapped[:20])
            if note:
                detail = note + "\n" + detail
            add("C", "C3", p, sev,
                f"{len(unmapped)}/{total} TSPC items show no associated TCIDs ({pct:.0f}%)"
                + (" [caused by C2 bug]" if c2_bug_present else ""),
                detail)
        else:
            add("C", "C3", p, "OK",
                f"All {total} TSPC items have at least one mapped TCID")

    # ── C4: HID — all TCIDs completely unclassified ─────────────────────────
    p = "HID"
    mt_rows     = data.get("mapping_tcid", {}).get(p, {}).get("rows", [])
    unclassified = [r.get("tcid") for r in mt_rows
                    if not any(r.get("bucket_flags", {}).values())]
    if unclassified:
        add("C", "C4", p, "ERROR",
            f"{len(unclassified)}/{len(mt_rows)} HID TCIDs have no bucket classification "
            f"(no TSPC conditions linked — profile mapping incomplete)",
            f"  All {len(unclassified)} HOGP/* TCIDs are unclassified: "
            f"cannot determine mandatory/optional/conditional status.\n"
            f"  Root cause: HID/HOGP TSPC items in workspace are IOPT-based and have "
            f"no TCMT mapping in the TS PDF (or parser did not extract them).")
    else:
        add("C", "C4", p, "OK",
            "All HID TCIDs have at least one bucket classification")

    # ── C5: ts_extracted vs validation_report count alignment ──────────────
    vr_profiles = data.get("validation_report", {}).get("profiles", {})
    for p in PROFILES:
        vr = vr_profiles.get(p, {})
        tcrl_count  = vr.get("tcrl_tcid_count",         None)
        mapped_count= vr.get("tcmt_mapped_tcid_count",  None)
        tcs_count   = len(data.get("tcs", {}).get(PROFILE_LOWER[p], []))
        if tcrl_count is None:
            add("C", "C5", p, "WARNING", "validation_report missing for this profile")
        elif tcrl_count != tcs_count:
            add("C", "C5", p, "ERROR",
                f"validation_report.tcrl_tcid_count ({tcrl_count}) ≠ tcs count ({tcs_count})")
        elif mapped_count is not None and mapped_count != tcs_count:
            add("C", "C5", p, "WARNING",
                f"validation_report.tcmt_mapped_tcid_count ({mapped_count}) ≠ tcs count ({tcs_count})",
                "Some TCIDs were not mapped via TS TCMT section (may be OK if unmapped_note present).")
        else:
            add("C", "C5", p, "OK",
                f"validation_report counts are consistent with tcs ({tcs_count} TCIDs)")


def _any_valid_tcid(mapped_tcids: list) -> bool:
    """Return True if mapped_tcids has at least one string entry (real TCID)."""
    return any(isinstance(v, str) for v in mapped_tcids)


# ---------------------------------------------------------------------------
# MODULE D: Runtime data consistency
# ---------------------------------------------------------------------------

def check_d(data: dict, run_status: dict):
    """Runtime data consistency."""

    # ── D1: runtime_active availability ────────────────────────────────────
    ra = data.get("runtime_active", {})
    if not ra.get("available"):
        for p in PROFILES:
            add("D", "D1", p, "WARNING",
                "runtime_active data not available — runtime checks skipped",
                "Regenerate by running export_runtime_active_tcids.py while PTS is open.")
    else:
        for p in PROFILES:
            valid_tcids = {r.get("tcid") for r in data.get("tcs", {}).get(PROFILE_LOWER[p], [])}
            active_ids  = set(ra.get("profiles", {}).get(p, {}).get("active_tcids", []))
            orphan      = active_ids - valid_tcids
            if orphan:
                add("D", "D1", p, "ERROR",
                    f"{len(orphan)} runtime_active TCIDs not found in tcs",
                    "  " + "\n  ".join(sorted(orphan)[:20]))
            else:
                add("D", "D1", p, "OK",
                    f"All {len(active_ids)} runtime_active TCIDs exist in tcs")

        # ── D2: mapping_tcid.runtime_active field vs actual runtime set ──
        for p in PROFILES:
            active_ids = set(ra.get("profiles", {}).get(p, {}).get("active_tcids", []))
            mt_rows    = data.get("mapping_tcid", {}).get(p, {}).get("rows", [])
            wrong = []
            for row in mt_rows:
                tcid        = row.get("tcid")
                field_val   = row.get("runtime_active")
                should_be   = (tcid in active_ids) if tcid else None
                if isinstance(field_val, bool) and field_val != should_be:
                    wrong.append(f"{tcid}: field={field_val} expected={should_be}")
            if wrong:
                add("D", "D2", p, "ERROR",
                    f"{len(wrong)} mapping_tcid rows have stale runtime_active field",
                    "\n".join(f"  - {w}" for w in wrong[:10]))
            else:
                add("D", "D2", p, "OK",
                    "All mapping_tcid.runtime_active fields match actual runtime data")

    # ── D3: run-status-state.json key validity ─────────────────────────────
    entries = run_status.get("entries", {})
    if not entries:
        for p in PROFILES:
            add("D", "D3", p, "INFO",
                "run-status-state.json has no entries yet (no test outcomes recorded)")
        return

    all_tcids_by_profile: dict[str, set] = {}
    for p, pl in PROFILE_LOWER.items():
        all_tcids_by_profile[p] = {r.get("tcid") for r in data.get("tcs", {}).get(pl, [])}

    orphan_keys = []
    for key in (entries if isinstance(entries, dict) else {}):
        if "::" not in key:
            orphan_keys.append(f"  Bad format: {key!r}")
            continue
        prof, tcid = key.split("::", 1)
        if prof not in all_tcids_by_profile:
            orphan_keys.append(f"  Unknown profile: {key!r}")
        elif tcid not in all_tcids_by_profile[prof]:
            orphan_keys.append(f"  TCID not in tcs.{PROFILE_LOWER.get(prof, prof)}: {key!r}")

    if orphan_keys:
        add("D", "D3", "ALL", "WARNING",
            f"{len(orphan_keys)} run-status entries reference unknown TCIDs or profiles",
            "\n".join(orphan_keys[:20]))
    else:
        total = len(entries) if isinstance(entries, dict) else len(entries)
        add("D", "D3", "ALL", "OK",
            f"All {total} run-status entries reference valid PROFILE::TCID keys")


# ---------------------------------------------------------------------------
# MODULE E: Existing comparison / validation findings
# ---------------------------------------------------------------------------

def check_e(data: dict):
    """Surface existing comparison and validation findings."""

    # ── E1: comparison.findings — list all non-match ────────────────────
    comp_findings = data.get("comparison", {}).get("findings", [])
    if not comp_findings:
        for p in PROFILES:
            add("E", "E1", p, "INFO", "No comparison findings in DATA.comparison")
        return

    by_profile: dict[str, list] = {p: [] for p in PROFILES}
    by_profile["ALL"] = []
    for f in comp_findings:
        prof   = f.get("profile", "ALL")
        status = f.get("status", "?")
        topic  = f.get("topic",  "?")
        claim  = f.get("site_claim", "")
        offic  = f.get("official_evidence", "")
        entry  = f"[{topic}] status={status}\n  Claim: {claim}\n  Official: {offic}"
        target = by_profile.get(prof, by_profile["ALL"])
        target.append((status, topic, entry))

    for p, items in by_profile.items():
        if not items:
            continue
        non_match = [(s, t, e) for s, t, e in items if s != "match"]
        match     = [(s, t, e) for s, t, e in items if s == "match"]
        for status, topic, entry in non_match:
            sev = "WARNING" if status == "partial" else "ERROR"
            add("E", "E1", p, sev,
                f"comparison finding [{topic}] status='{status}'",
                entry)
        if match and not non_match:
            add("E", "E1", p, "OK",
                f"{len(match)} comparison finding(s) all status=match", "")

    # ── E2: ICS mapping gaps from comparison ──────────────────────────────
    for p, pl in PROFILE_LOWER.items():
        tspc_rows = data.get("tspc_tables", {}).get(pl, [])
        no_ics    = [r.get("name") for r in tspc_rows if not r.get("ics_line")]
        total     = len(tspc_rows)
        if no_ics:
            pct = 100 * len(no_ics) / total if total else 0
            sev = "ERROR" if pct >= 80 else ("WARNING" if pct >= 10 else "INFO")
            add("E", "E2", p, sev,
                f"{len(no_ics)}/{total} TSPC items lack an ICS document anchor ({pct:.0f}%)",
                "  " + "\n  ".join(no_ics[:20]))
        else:
            add("E", "E2", p, "OK",
                f"All {total} TSPC items have an ICS document anchor")

    # ── E3: notes.hid_ics_missing ─────────────────────────────────────────
    hid_missing = data.get("notes", {}).get("hid_ics_missing", [])
    if hid_missing:
        add("E", "E3", "HID", "WARNING",
            f"{len(hid_missing)} IOPT TSPC items listed in notes.hid_ics_missing (no ICS mapping)",
            "  " + "\n  ".join(hid_missing))
    else:
        add("E", "E3", "HID", "OK", "notes.hid_ics_missing is empty")


# ---------------------------------------------------------------------------
# MODULE F: UI representation notes
# ---------------------------------------------------------------------------

def check_f(data: dict):
    """UI representation notes (informational, not data bugs)."""

    # ── F1: Overview tab shows TCID bucket counts, not TSPC counts ─────────
    for entry in data.get("summary", []):
        p    = entry.get("profile", "?")
        pl   = PROFILE_LOWER.get(p, p.lower())
        tspc_m = len(entry.get("mandatory",   []))
        tspc_o = len(entry.get("optional",    []))
        tspc_c = len(entry.get("conditional", []))
        bb = data.get("mapping_tcid_summary", {}).get(p, {}).get("by_bucket", {})
        tcid_m = bb.get("mandatory",   {}).get("tcid_count", 0) or 0
        tcid_o = bb.get("optional",    {}).get("tcid_count", 0) or 0
        tcid_c = bb.get("conditional", {}).get("tcid_count", 0) or 0
        tcid_unique = len(data.get("tcs", {}).get(pl, []))

        tspc_matches_tcid = (tspc_m, tspc_o, tspc_c) == (tcid_m, tcid_o, tcid_c)

        msg  = (f"Overview tab shows TCID bucket counts (M={tcid_m} O={tcid_o} C={tcid_c} "
                f"sum={tcid_m+tcid_o+tcid_c}) vs {tcid_unique} unique TCIDs.")
        tspc_note = (f"TSPC counts for reference: M={tspc_m} O={tspc_o} C={tspc_c} "
                     f"(sum={tspc_m+tspc_o+tspc_c}). ")
        if tcid_m + tcid_o + tcid_c > tcid_unique:
            diff = (tcid_m + tcid_o + tcid_c) - tcid_unique
            note = (f"{diff} TCID(s) appear in multiple buckets — "
                    f"sum of bucket counts ({tcid_m+tcid_o+tcid_c}) > unique TCIDs ({tcid_unique}). "
                    "This is expected design: a test case that covers both an optional and a "
                    "conditional feature is counted in both buckets. "
                    "The UI does NOT display the unique TCID count in the overview.")
            add("F", "F1", p, "INFO", msg, tspc_note + note)
        elif not tspc_matches_tcid:
            note = ("TSPC counts differ from TCID bucket counts — expected, "
                    "because one TSPC item can map to multiple TCIDs.")
            add("F", "F1", p, "INFO", msg, tspc_note + note)
        else:
            add("F", "F1", p, "OK",
                f"TSPC counts happen to equal TCID bucket counts (M={tspc_m} O={tspc_o} C={tspc_c})")

    # ── F2: Glossary covers TSPC vs TCID distinction ───────────────────────
    glossary_keys = set(data.get("glossary", {}).keys())
    missing_terms = []
    for term in ("TSPC", "TCID"):
        if not any(term.lower() in k.lower() for k in glossary_keys):
            missing_terms.append(term)
    if missing_terms:
        add("F", "F2", "ALL", "WARNING",
            f"Glossary is missing definitions for: {missing_terms}",
            "Users may not understand the difference between TSPC and TCID counts.")
    else:
        add("F", "F2", "ALL", "OK",
            f"Glossary contains definitions for TSPC and TCID")


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

SEV_EMOJI   = {"ERROR": "🔴", "WARNING": "🟡", "INFO": "🔵", "OK": "✅"}
SEV_LABEL   = {"ERROR": "שגיאה", "WARNING": "אזהרה", "INFO": "מידע", "OK": "תקין"}
MODULE_NAMES = {
    "A": "A — עקביות TSPC פנימית",
    "B": "B — עקביות TCID פנימית",
    "C": "C — קשר TSPC ↔ TCID",
    "D": "D — נתוני Runtime",
    "E": "E — ממצאי comparison ו-validation קיימים",
    "F": "F — ייצוג UI (מידע בלבד)",
}


def sev_counts(items: list[Finding]) -> dict:
    c = Counter(f.severity for f in items)
    return {s: c.get(s, 0) for s in ("ERROR", "WARNING", "INFO", "OK")}


def render_report(all_findings: list[Finding]) -> str:
    today = date.today().strftime("%Y-%m-%d")
    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines += [
        f"# דוח ניתוח שלמות נתוני Dashboard PTS",
        f"",
        f"**תאריך:** {today}",
        f"**מקור נתונים:** `dashboards/pts_report_he/data/report-data.js`",
        f"**סטטוס:** קריאה בלבד — אין שינוי בקבצים",
        f"",
        "---",
        "",
    ]

    # ── Executive Summary Table ─────────────────────────────────────────────
    lines += [
        "## סיכום מנהלים",
        "",
        "| פרופיל | A — TSPC | B — TCID | C — TSPC↔TCID | D — Runtime | E — Comparison | F — UI |",
        "|--------|----------|----------|---------------|-------------|----------------|--------|",
    ]

    all_profiles = PROFILES + ["ALL"]
    modules      = list("ABCDEF")

    def cell(f_list: list[Finding]) -> str:
        sc = sev_counts(f_list)
        if sc["ERROR"]:
            return f"🔴 {sc['ERROR']} שגיאה"
        if sc["WARNING"]:
            return f"🟡 {sc['WARNING']} אזהרה"
        if sc["INFO"]:
            return f"🔵 {sc['INFO']} מידע"
        return "✅ תקין"

    for p in all_profiles:
        row = [f"**{p}**"]
        for mod in modules:
            subset = [f for f in all_findings if f.profile == p and f.module == mod]
            row.append(cell(subset) if subset else "—")
        lines.append("| " + " | ".join(row) + " |")

    lines += [""]

    # ── Counts summary ──────────────────────────────────────────────────────
    total_sc = sev_counts(all_findings)
    lines += [
        "### ספירה כוללת",
        "",
        f"- 🔴 שגיאות: **{total_sc['ERROR']}**",
        f"- 🟡 אזהרות: **{total_sc['WARNING']}**",
        f"- 🔵 מידע: **{total_sc['INFO']}**",
        f"- ✅ תקין: **{total_sc['OK']}**",
        "",
        "---",
        "",
    ]

    # ── Per-module breakdown ─────────────────────────────────────────────────
    lines += ["## פירוט לפי מודול", ""]

    for mod in modules:
        lines += [f"### {MODULE_NAMES.get(mod, mod)}", ""]
        mod_findings = [f for f in all_findings if f.module == mod]

        # group by check_id
        check_ids = sorted({f.check_id for f in mod_findings})
        for check_id in check_ids:
            chk_items = [f for f in mod_findings if f.check_id == check_id]
            lines += [f"#### בדיקה {check_id}", ""]
            for fi in sorted(chk_items, key=lambda x: (SEV_ORDER.get(x.severity, 9), x.profile)):
                emoji = SEV_EMOJI.get(fi.severity, "?")
                label = SEV_LABEL.get(fi.severity, fi.severity)
                lines.append(f"- {emoji} **[{fi.severity}] [{fi.profile}]** {fi.title}")
                if fi.details.strip():
                    for detail_line in fi.details.strip().splitlines():
                        lines.append(f"  {detail_line}")
            lines.append("")

        lines += ["---", ""]

    # ── Conclusions ──────────────────────────────────────────────────────────
    lines += [
        "## מסקנות",
        "",
        "### שגיאות אמיתיות שדורשות תיקון בבניית הנתונים",
        "",
        "> **שים לב:** ממצאי C3 (TSPC ללא TCIDs) עבור DIS/BAS/HRS הם **תוצאת לוואי** של",
        "> באג C2 (mapped_tcids מכיל דיקשנרים במקום strings). תיקון C2 בסקריפט הבנייה",
        "> ישפיע ישירות על C3.",
        "",
    ]

    error_findings = [f for f in all_findings if f.severity == "ERROR"]
    if error_findings:
        for fi in error_findings:
            lines.append(f"- **[{fi.check_id}][{fi.profile}]** {fi.title}")
    else:
        lines.append("*לא נמצאו שגיאות.*")

    lines += [
        "",
        "### אזהרות — כדאי לבדוק",
        "",
    ]
    warn_findings = [f for f in all_findings if f.severity == "WARNING"]
    if warn_findings:
        for fi in warn_findings:
            lines.append(f"- **[{fi.check_id}][{fi.profile}]** {fi.title}")
    else:
        lines.append("*לא נמצאו אזהרות.*")

    lines += [
        "",
        "### בלבול UI בלבד (לא שגיאות נתונים)",
        "",
        "- **[F1]** הלשונית 'סקירה מהירה' מציגה **ספירת TCID לפי bucket** (לא ספירת TSPC).",
        "  סכום ה-buckets גדול ממספר ה-TCID הייחודיים כי TCID אחד יכול להיות בכמה buckets.",
        "  — הUI כבר מציין זאת בטקסט: 'המספרים נספרים לפי TCID ולא לפי TSPC'.",
        "- **[C3]** TSPC items רבים 'לא ממופים' ל-TCIDs — זה צפוי: לא לכל יכולת ICS יש test case",
        "  בTCRL, במיוחד לפריטים מסוג Version/General (section 0) ו-Optional features.",
        "",
        "---",
        "",
        f"*הדוח נוצר אוטומטית ב-{today} על ידי `dashboards/pts_report_he/tools/analyze_report_data_integrity.py`.*",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    data       = load_data()
    run_status = load_run_status()

    print("Running checks…")
    check_a(data)
    check_b(data)
    check_c(data)
    check_d(data, run_status)
    check_e(data)
    check_f(data)

    report_text = render_report(findings)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"data_integrity_{date.today()}.md"
    out_path.write_text(report_text, encoding="utf-8")
    print(f"\nDone. Report written to: {out_path}")

    # quick terminal summary
    sc = sev_counts(findings)
    print(f"  🔴 Errors:   {sc['ERROR']}")
    print(f"  🟡 Warnings: {sc['WARNING']}")
    print(f"  🔵 Info:     {sc['INFO']}")
    print(f"  ✅ OK:       {sc['OK']}")


if __name__ == "__main__":
    main()
