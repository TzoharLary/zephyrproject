# Right-Size PTS Build Documentation

- Date: 2026-03-22
- Group: dashboard
- Status: done

## Context
אחרי הוספת מצבי ה-build החדשים ל-`tools/build_pts_report_bundle.py`, ה-`README` של הדשבורד התחיל להכיל יותר מדי פירוט טכני, בעוד שהמסמך הייעודי ל-build עוד לא שימש כמקום הראשי לכל הפרטים. בפועל היה צורך ליישר בין מה שממומש בקוד לבין איפה כל סוג מידע צריך להופיע.

## Changes
- קיצרתי את סעיף ה-build ב-`dashboards/pts_report_he/README.md` כך שיישאר בו רק המידע הקריטי: מה הסקריפט עושה, מתי עושים full build, מתי עושים build ממוקד, ואיפה מריצים `plan`.
- שכתבתי את `tools/pts_report_bundle_build_modes.md` כך שיהיה מסמך ה-build הראשי והמפורט, עם דוגמאות שימוש שמבוססות על ההתנהגות הממומשת בפועל.
- שמרתי את ההסברים עקביים עם ההתנהגות האמיתית של `build`, `plan`, `clean`, ועם ההבדל בין build ממוקד לבין full build.

## Why
כדי שה-`README` יישאר קל לסריקה ומהיר להבנה, בזמן שהמסמך הייעודי יכיל את כל פירוט ה-build במקום אחד. זה מקטין עומס במסמך הראשי, ומפחית סיכון לכך שהתיעוד יטען דברים שלא תואמים למה שהקוד באמת עושה.

## Impact
- Users: קל יותר להבין במהירות איך להרים את הדשבורד ואיזו פקודת build לבחור.
- Devs: יש הפרדה ברורה בין "כניסה מהירה" ב-`README` לבין "תיעוד build מלא" במסמך הייעודי.

## References
- Commit: pending (no commit in this task)
- Files:
  - `dashboards/pts_report_he/README.md`
  - `tools/pts_report_bundle_build_modes.md`
  - `CHANGELOG/dashboard/2026-03-22-right-size-pts-build-documentation.md`
  - `CHANGELOG/INDEX.md`

## Notes
הקבוצה הראשית היא `dashboard` בגלל תיקו במספר הקבצים בין `dashboard` ל-`tools`; הקבוצה המשנית היא `tools`.
