# Modularize `build_pts_report_bundle.py` orchestration

- Date: 2026-03-09
- Group: tools
- Status: done

## Context
`tools/build_pts_report_bundle.py` עבד עד עכשיו כ-entrypoint מונוליתי של full build בלבד. כל ריצה בנתה מחדש את כל שכבות ה-data וה-assets, בלי selectors granular, בלי cache ברמת unit, ובלי `write-if-changed`. בפועל גם no-op build יצר churn מיותר ב-`report-data.js`.

## Changes
- נוספו `subcommands` ו-CLI granular: `build`, `plan`, `clean`, עם selectors נפרדים ל-`report`/`hub`, ל-`data`/`assets`, ל-profiles, ולמודולי JS.
- נוספה שכבת orchestration ליחידות build נפרדות:
  - `report.runtime`
  - `report.official_sources`
  - `report.ics_refs`
  - `report.line_refs`
  - `report.profile.<PROFILE>`
  - `report.profile_build_plans`
  - `shared.autopts_guide`
  - `report.bundle`
  - `hub.group_b`
- נוסף cache manifest תחת `.cache/pts_report_bundle/` עם fingerprints ליחידות build.
- נוספה מדיניות `write-if-changed` לכל outputs של report/hub assets ושל data bundles.
- נוספה stabilization לשדות volatile כדי למנוע churn מיותר ב-`report-data.js` וב-`hub-data.js` כשאין שינוי סמנטי.
- עודכן README של הדשבורד עם דוגמאות ל-build granular.
- נוסף מסמך שימוש ייעודי ל-builder תחת `tools/`.

## Why
כדי לאפשר פיתוח ממוקד ומהיר יותר: שינוי ב-template או בפרופיל בודד לא אמור להכריח full rebuild של כל pipeline. בנוסף, build system מקצועי צריך להיות explainable, cache-aware, ולמנוע כתיבות מיותרות ל-artifacts מנוהלים.

## Impact
- Users: אין שינוי ב-UI עצמו; paths של ה-artifacts נשארו זהים.
- Devs: אפשר לבצע full build כבעבר, אבל גם builds granular, להשתמש ב-`plan`, לנקות cache עם `clean`, ולקבל summary של `built/cached/unchanged`.

## References
- Commit: pending (no commit in this task)
- Files:
  - `tools/build_pts_report_bundle.py`
  - `tools/pts_report_bundle_build_modes.md`
  - `dashboards/pts_report_he/README.md`
  - `CHANGELOG/tools/2026-03-09-modularize-pts-report-build-orchestration.md`
  - `CHANGELOG/INDEX.md`

## Notes
- הקבוצה הראשית היא `tools`; יש עדכון משני גם תחת `dashboard` ב-`dashboards/pts_report_he/README.md`.
- ברירת המחדל נשארה backward-compatible: `python3 tools/build_pts_report_bundle.py` עדיין מבצע full build.
