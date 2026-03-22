# Align PTS Build Selection With Runtime Behavior

- Date: 2026-03-22
- Group: tools
- Status: done

## Context
ה-CLI המודולרי של `tools/build_pts_report_bundle.py` כבר היה קיים, אבל בפועל חלק מהבחירות הממוקדות עדיין הובילו ל-build רחב יותר ממה שהממשק רמז. בנוסף, `plan` הציג רק בחירה מנורמלת ולא את מה שבאמת ירוץ, ו-`clean` לא ידע למחוק cache של unit יחיד.

## Changes
- הוספתי שכבת planning פנימית שמחשבת את היחידות, התלויות והקבצים שבאמת יירוצו לפני `plan` ו-`build`.
- שיניתי את build ה-data של report כך שבחירה ממוקדת ב-profile או ב-unit פנימי לא תכתוב אוטומטית את `report-data.js`.
- שיניתי את build ה-data של hub כך שבחירה של `autopts-guide` בלבד לא תכתוב את `hub-data.js`.
- שדרגתי את `plan` ואת `--json-summary` כך שישקפו גם קבצים מתוכננים וגם קבצים שנדחו במכוון.
- הוספתי `clean --unit <name>` למחיקה מדויקת של cache unit יחיד.
- עדכנתי את מסמכי השימוש של builder כך שישקפו את ההתנהגות החדשה בפועל.

## Why
כדי ליישר את ההתנהגות האמיתית של ה-build עם מה שה-CLI מבטיח. אם מפתח בוחר רענון ממוקד, הוא צריך לקבל build ממוקד באמת, ו-`plan` צריך להסביר מראש מה יקרה ולא רק להראות את ה-flags אחרי נרמול.

## Impact
- Users: אין שינוי בנתיבי ה-artifacts או ב-full build הרגיל.
- Devs: אפשר להבין מראש מה ירוץ, להריץ build ממוקד בלי לכתוב bundle סופי שלא התבקש, ולנקות cache unit בודד בלי למחוק הכל.

## References
- Commit: pending (no commit in this task)
- Files:
  - `tools/build_pts_report_bundle.py`
  - `tools/pts_report_bundle_build_modes.md`
  - `dashboards/pts_report_he/README.md`
  - `CHANGELOG/tools/2026-03-22-align-pts-build-selection-with-runtime-behavior.md`
  - `CHANGELOG/INDEX.md`

## Notes
הקבוצה הראשית היא `tools`; יש עדכון משני גם תחת `dashboard` ב-`dashboards/pts_report_he/README.md`.
