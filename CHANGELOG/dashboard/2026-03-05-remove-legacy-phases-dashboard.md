# Remove Legacy `phases_tracking` Dashboard

- Date: 2026-03-05
- Group: dashboard
- Status: done

## Context
הייתה תיקייה ישנה (`dashboards/phases_tracking`) ששימשה בעבר כדשבורד מעקב שלבי הקמה ל-VPC.
בפועל, הזרימה הפעילה היום מתרכזת ב-`dashboards/pts_report_he` ו-`autopts`.

## Changes
- הוסרה כל התיקייה `dashboards/phases_tracking`.
- נוקו הפניות שבורות ב-`README.md` וב-`docs/README.md`.

## Why
כדי להקטין רעש בפרויקט, למנוע בלבול בין דשבורד ישן לדשבורד פעיל, ולתחזק מקור אמת אחד לעבודה השוטפת.

## Impact
- Users: יש פחות עומס בניווט, נשאר הדשבורד הפעיל בלבד.
- Devs: פחות קוד legacy לתחזק ופחות סיכון לקישורים שבורים.

## References
- Commit: `af93ee6`
- Files:
  - `dashboards/phases_tracking/` (removed)
  - `README.md`
  - `docs/README.md`

## Notes
אם נצטרך מידע היסטורי מהדשבורד הישן, אפשר לחזור אליו דרך ההיסטוריה של git.
