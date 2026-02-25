---
name: pts-hub-smoke-qa
description: Run desktop-only smoke QA for the PTS main dashboard and the AutoPTS+Group B Hub using a local static server and Playwright MCP (or an equivalent local Playwright flow), including expected console-error classification.
---

# PTS Hub Smoke QA (Desktop)

Use this skill after changes to:
- Hub templates/data
- `Group_B_data`
- builder outputs
- source manifests that affect rendering

## Preconditions

- Local static server is running from repo root:
  - `python3 -m http.server 8000`
- Open pages:
  - `http://127.0.0.1:8000/dashboards/pts_report_he/index.html`
  - `http://127.0.0.1:8000/dashboards/pts_report_he/autopts/index.html`

## Required smoke path

1. Main dashboard loads
2. CTA to Hub exists and is clickable
3. Hub loads
4. Top tabs switch correctly
5. For each profile (`BPS/WSS/ScPS`):
   - open `לוגיקה`
   - open `מבנה`
   - verify sections exist:
     - summary
     - findings
     - source observations
     - methods
     - gaps
     - raw markdown drawer
6. `מצב עבודה / פערים` shows readiness/check status

## Expected console errors (static server)

These are acceptable during local static QA:
- `api/run-status` 404
- `favicon.ico` 404

Any JS runtime error in hub rendering is a failure.

## QA output (recommended)

Record/update:
- `tools/data/group_b_qa_meta.json`
  - `last_smoke_test_at`
  - `smoke_test_mode`
  - `last_manual_review_notes_he[]`

