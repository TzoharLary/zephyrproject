# Add Report Data Integrity Analyzer

- Date: 2026-03-05
- Group: dashboard
- Status: done

## Context
נדרש כלי בדיקה מהיר שמאתר חוסר עקביות בנתוני `report-data.js` לפני/אחרי שינויי build ומיפוי, כדי למנוע רגרסיות ב-UI.

## Changes
- נוסף סקריפט `dashboards/pts_report_he/tools/analyze_report_data_integrity.py`.
- הסקריפט קורא `window.REPORT_DATA` ומבצע בדיקות עקביות מדורגות חומרה.
- הסקריפט מייצר דוח Markdown ומציג סיכום במטריקה לפי ERROR/WARNING/INFO/OK.

## Why
כדי לתפוס שגיאות נתונים מוקדם במקום לגלות אותן בדשבורד אחרי פריסה.

## Impact
- Users: פחות סיכוי לנתונים לא עקביים בדשבורד.
- Devs: כלי בדיקה ברור לפני merge לשינויי mapping/build.

## References
- Commit: `pending (no commit in this task)`
- Files:
  - `dashboards/pts_report_he/tools/analyze_report_data_integrity.py`
  - `CHANGELOG/dashboard/2026-03-05-add-report-data-integrity-analyzer.md`
  - `CHANGELOG/INDEX.md`

## Notes
השינוי ממוקד בבדיקות שלמות נתונים ואינו משנה את מקורות הנתונים עצמם.
