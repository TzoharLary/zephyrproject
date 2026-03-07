# Close PR #9 review gaps

- Date: 2026-03-07
- Group: dashboard
- Status: done

## Context
PR #9 כבר סגר את רוב סעיפי `dashboards/ARCHITECTURE_REVIEW_HE.md`, אבל review סופי חשף שני פערים שנשארו פתוחים: `smoke.html` נשבר בזמן ריצה והנגישות ב-`pts_report_he` נשענה על `aria-labelledby` בלי `id` תואם בכפתורי הניווט. בנוסף, ה-PR לא הכיל evidence מלא ומסונכרן של האימותים שבוצעו בפועל.

## Changes
- שוכתב `tools/templates/pts_report_he/tests/smoke.html` ל-runtime harness יציב שטוען את `state.js` ו-`persistence.js` דרך HTTP, עובד מול `runtime` מפורש, ומציג bootstrap failure ברור במקום לקרוס.
- נוספו `id` יציבים לכפתורי הניווט ב-template של `pts_report_he`, נוסף `aria-hidden="false"` לפאנל הפעיל הראשוני, וה-artifacts נבנו מחדש כך שה-Markup וה-runtime נשארים מסונכרנים.
- עודכנו `dashboards/pts_report_he/README.md`, `tools/data/group_b_qa_meta.json`, `CHANGELOG/INDEX.md` וגוף ה-PR כדי לשקף את פקודת ה-build הנכונה, דרישות ה-smoke, ותוצאות האימות הסטטי וה-API-backed.

## Why
הפערים שנשארו היו קטנים בהיקף אבל מהותיים באמינות: harness שבור לא באמת מוכיח שהמודולים עובדים, ו-ARIA לא תקין משאיר סימני שאלה על חוזה ה-DOM. תיקון ממוקד, יחד עם evidence מסודר, סוגר את ה-PR בלי להוסיף churn מיותר לקבצי data שנוצרו מה-build.

## Impact
- Users: דף ה-smoke עובד באמת, ניווט הפאנלים בדשבורד נגיש ועקבי יותר, ותיעוד ההרצה ברור.
- Devs: ה-PR מכיל evidence מסודר שאפשר לבדוק, ה-QA metadata עודכן, ותהליך הבנייה/האימות נשאר ממוקד ב-templates וב-artifacts הנכונים.

## References
- Commit: 679d9cb
- Files:
  - tools/templates/pts_report_he/tests/smoke.html
  - tools/templates/pts_report_he/index.html
  - dashboards/pts_report_he/index.html
  - dashboards/pts_report_he/assets/report.js
  - dashboards/pts_report_he/README.md
  - tools/data/group_b_qa_meta.json
  - CHANGELOG/INDEX.md

## Notes
הקבוצה הראשית היא `dashboard`, אבל המשימה כוללת גם עדכון משני תחת `tools` עבור `tools/data/group_b_qa_meta.json`.
