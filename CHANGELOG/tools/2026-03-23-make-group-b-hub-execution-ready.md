# Make Group B Hub Execution-Ready

- Date: 2026-03-23
- Group: tools
- Status: done

## Context
אחרי חיבור metadata/patterns מ-`.github`, מסכי `BPS` / `WSS` / `ScPS` עדיין הרגישו כמו מסכי ידע צפופים: הייתה פתיחה מיותרת, כרטיסי “איך לקרוא” במקום ניווט פנימי, ערבוב בין “מה עושים” לבין “למה”, וחסר מסלול ברור שמחבר מהבנת הפרופיל אל קבצי המימוש בפועל.

## Changes
- הסרתי את טקסט הפתיחה המיותר והחלפתי את כרטיסי ההסבר בניווט פעולה `מה תרצה לראות?` לכל לשונית, עם קפיצה נגישה ל-sections.
- הרחבתי את `סקירה` עם יכולות copy לטסטים: כפתור `העתק את כל שמות הטסטים`, כפתורי copy לטסט בודד, ושדה `tcid_cli/copy_value` שנגזר ב-builder בפורמט CLI.
- שיניתי את `לוגיקה` למבנה Execution-first: `תכלס, מה הפרופיל צריך לדעת לעשות`, `יכולות ופירוט מקורות`, ו-`מקורות שנחקרו`, בלי בלוק `מה לא כלול כרגע / נדחה`.
- שכתבתי את pattern cards לפורמט `נלמד מ / הכלל שנלקח / למה זה רלוונטי / תגיות תבנית / פירוט מקורות`, והוספתי glossary inline למונחים טכניים בהופעה ראשונה.
- ארגנתי מחדש את `מבנה` סביב בחירת מבנה, תכנית קבצים, blueprint פנימי ופירוט מקורות, עם הפרדה ברורה יותר בין Zephyr/TI/Nordic.
- הוספתי לשונית חדשה `מימוש`, מבוססת על מסמכי `Implementation/*.md`, עם Accordion לכל קובץ, `Copy Filename`, `Copy Code`, Relative Path, קוד מלא, החלטות מימוש ו-traceability למקורות.
- הרחבתי את ה-builder ואת ה-checks כדי לטעון, לבנות ולאמת `implementation_presentation`, קבצי implementation, ותקינות שדות ה-copy לטסטים.
- חידדתי את תוכן `WSS` ו-`SCPS` כך ש-`WSS` יישאר ללא serializer file נפרד ב-Phase 1 ו-`SCPS` יעבוד עם `scan_policy` במקום `logic` גנרי.
- עדכנתי cache-busting ב-`autopts/index.html` עבור `report.css`, `report.js` ו-`hub-data.js`, כדי ש-Chrome יטען את ה-Hub המעודכן ולא יישאר על assets ישנים מה-cache.

## Why
המטרה הייתה להפוך את המסך מ-knowledge screen למסך שמוביל לביצוע: קודם להבין מה הפרופיל עושה ומה חייבים לממש, אחר כך לראות איך זה בנוי, ולבסוף להעתיק שמות טסטים או קוד מימוש בלי לחפש את המידע בין מסמכי עומק.

## Impact
- Users: יכולים לנווט במהירות בתוך כל לשונית, להעתיק טסטים בפורמט CLI, להבין את הפעולות העיקריות של הפרופיל, ולראות קבצי מימוש מלאים עם הסבר פשוט.
- Devs: יש schema חדש ל-`implementation_presentation`, מסמכי תוכן ייעודיים ל-Implementation, ולידציות חדשות ל-copy fields, implementation files וקישור בינם לבין `מבנה`.

## References
- Commit: pending (no commit in this task)
- Files:
  - dashboards/pts_report_he/autopts/assets/report.css
  - dashboards/pts_report_he/autopts/assets/report.js
  - dashboards/pts_report_he/autopts/data/hub-data.js
  - dashboards/pts_report_he/autopts/index.html
  - tools/check_group_b_hub.py
  - tools/group_b_hub_data.py
  - tools/templates/pts_report_he/Group_B_data/Implementation/BPS.md
  - tools/templates/pts_report_he/Group_B_data/Implementation/WSS.md
  - tools/templates/pts_report_he/Group_B_data/Implementation/SCPS.md
  - tools/templates/pts_report_he/Group_B_data/Structure/SCPS.md
  - tools/templates/pts_report_he/Group_B_data/Structure/WSS.md
  - tools/templates/pts_report_he/autopts/index.html
  - tools/templates/pts_report_he/autopts/report.css
  - tools/templates/pts_report_he/autopts/report.js

## Notes
קבוצות משניות שנגעו בשינוי: `dashboard`. במהלך ה-QA זוהה ותוקן באג בכפתור copy לטסט בודד, שנגרם מפירוק שגוי של `official_row_id` המכיל `:`.
