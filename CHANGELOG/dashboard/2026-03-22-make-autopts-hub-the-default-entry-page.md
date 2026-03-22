# Make AutoPTS Hub The Default Entry Page

- Date: 2026-03-22
- Group: dashboard
- Status: done

## Context
השרת של `pts_report_he` פתח כברירת מחדל את הדשבורד הראשי, בעוד שהפוקוס הנוכחי של העבודה עבר לעמוד `AutoPTS + Group B`. בנוסף, הניסוח בדפים גרם לעמוד ה-`autopts` להרגיש כמו אזור פנימי של אותו דשבורד, למרות שבפועל מדובר בשני עמודי HTML נפרדים.

## Changes
- שיניתי את `serve_with_run_status.py` כך שה-root יפנה כברירת מחדל ל-`/autopts/index.html`.
- שיניתי את פתיחת הדפדפן האוטומטית כך שתפתח את עמוד `AutoPTS + Group B` ולא את הדשבורד הראשי.
- הוספתי בלוגי השרת הדפסה מפורשת של שני הנתיבים: עמוד ברירת המחדל ועמוד הדשבורד הראשי.
- עדכנתי את templates ה-HTML וה-artifacts כך שיהיה ברור שמדובר בשני עמודים נפרדים שאפשר לעבור ביניהם.
- עדכנתי את README של הדשבורד כך שישקף את ברירת המחדל החדשה ואת חלוקת העמודים.

## Why
כדי ליישר את סביבת העבודה עם הפוקוס הנוכחי: כשמעלים את האתר, העמוד הראשון שנפתח צריך להיות העמוד שעליו עובדים עכשיו באמת. בנוסף, חשוב להציג בצורה ברורה שמדובר בשני עמודים נפרדים ולא ב"עמוד פנימי" בתוך אותו דשבורד.

## Impact
- Users: פתיחת השרת תוביל כברירת מחדל לעמוד `AutoPTS + Group B`, ועדיין יהיה מעבר ברור לדשבורד הראשי.
- Devs: קל יותר לבדוק ולעבוד על העמוד הפעיל כרגע, בלי לזכור URL אחר או להיכנס ידנית כל פעם לעמוד המשני.

## References
- Commit: pending (no commit in this task)
- Files:
  - `dashboards/pts_report_he/serve_with_run_status.py`
  - `dashboards/pts_report_he/README.md`
  - `dashboards/pts_report_he/index.html`
  - `dashboards/pts_report_he/autopts/index.html`
  - `tools/templates/pts_report_he/index.html`
  - `tools/templates/pts_report_he/autopts/index.html`
  - `CHANGELOG/dashboard/2026-03-22-make-autopts-hub-the-default-entry-page.md`
  - `CHANGELOG/INDEX.md`

## Notes
- הקבוצה הראשית היא `dashboard`; יש עדכון משני גם תחת `tools` בגלל שינוי templates.
