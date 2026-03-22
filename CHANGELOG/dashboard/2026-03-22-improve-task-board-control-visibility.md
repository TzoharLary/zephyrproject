# Improve task-board control visibility

- Date: 2026-03-22
- Group: dashboard
- Status: done

## Context
במצב עבודה נוכחי (BPS/WSS/ScPS) שדות החיפוש/סינון בלוח העבודה לא נראו כשדות קלט ברורים: ללא גבולות חזותיים מספיקים וללא affordance ברור להזנה ובחירה.

## Changes
- חיזוק סגנון שדות הסינון והבקרה ב-`task-board-controls` בתבנית ה-hub:
  - מעטפת ברורה לבלוק הסינון
  - מסגרת ורקע לכל שדה
  - גבולות חזקים, מצבי hover/focus, ו-placeholder קריא
- הוספת alias-ים של design tokens ב-`shared-tokens.css` כדי למנוע נפילת סגנון ברכיבים שמשתמשים בשמות legacy (`--border`, `--text` וכו').
- הוספת cache-busting לקישורי ה-CSS ב-`autopts/index.html` כדי לוודא טעינת CSS עדכני אחרי build.
- הרצת build ממוקד לעדכון תוצרי CSS/HTML המוגשים בפועל.

## Why
הפתרון נבחר כדי לספק הבחנה חזותית מיידית בין טקסט רגיל לבין רכיבי קלט, ולהבטיח שהתוצאה תישאר יציבה גם בתרחישי cache של הדפדפן.

## Impact
- Users: שדות ההזנה/סינון בלוח העבודה ברורים יותר, עם גבולות ופוקוס נראים לעין.
- Devs: זרימת העבודה נשארת source-first דרך templates + build, עם cache-busting שמקטין בלבול בזמן אימות UI.

## References
- Commit: pending (no commit in this task)
- Files:
  - tools/templates/pts_report_he/autopts/report.css
  - tools/templates/pts_report_he/autopts/index.html
  - tools/templates/pts_report_he/shared-tokens.css
  - dashboards/pts_report_he/autopts/assets/report.css
  - dashboards/pts_report_he/autopts/index.html
  - dashboards/pts_report_he/shared-tokens.css

## Notes
- קבוצת שינוי משנית: `tools` (בשל עדכון templates תחת `tools/templates/**`).
