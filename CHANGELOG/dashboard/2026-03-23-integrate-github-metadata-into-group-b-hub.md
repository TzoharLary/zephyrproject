# Integrate `.github` Metadata Into Group B Hub

- Date: 2026-03-23
- Group: dashboard
- Status: done

## Context
עמוד הפרופילים של Group B הציג בעיקר לוח עבודה פנימי שנבנה מסוכנים ומסכמות משימות, בלי להסביר למשתמש חדש מהו הפרופיל, מה ידוע עליו, מה מצב הבדיקות, ועל בסיס אילו מקורות גובשו הלוגיקה והמבנה. בנוסף, נכסי `.github` שהכילו metadata, patterns וכללי governance לא הזינו ישירות את ה-Hub.

## Changes
- חיברתי את ה-Hub ל-`.github/data/profiles-db.yaml`, `profile-patterns.md` ו-`sources-map.yaml`, עם reconciliation מול `docs/profiles`, `Group_B_data` ו-`auto-pts`.
- הוספתי `overview_presentation` לכל `BPS` / `WSS` / `SCPS`, שכולל `סקירה` ברירת מחדל, characteristics, artifacts רשמיים, errata, pattern cards, open points וטבלת בדיקות רשמית.
- הרחבתי את לשוניות `לוגיקה` ו-`מבנה` עם pattern cards, capability summaries, reference profile cards, Zephyr reference files ותיוג מקור ברור.
- הוספתי `מצב עבודה נוכחי` במבנה דו-שכבתי: `סקירה פשוטה` כברירת מחדל ו-`מצב מתקדם` ללוח המשימות המלא.
- הוספתי API וקובץ state להערות בדיקות (`/api/group-b-test-notes`) עם שמירה/מחיקה תקינות וניקוי entries ריקים.
- הרחבתי את `tools/check_group_b_hub.py` ואת workflow `pts-hub-check.yml` כך שיבדקו גם את נכסי `.github` ואת עקביות ה-seed מול הנתונים הנגזרים.
- יישרתי את ניסוח טבלת הבדיקות ל-`קיים ב-PTS` מול `מימוש ב-AutoPTS`, כדי להבדיל בין נוכחות ב-workspace לבין שכבת אוטומציה ממומשת.

## Why
הפתרון הנוכחי מעביר את ה-Hub ממצב של “לוח משימות לצוות” למצב של “מסך הבנה + עבודה”. הוא שומר את העומק הקיים והעקיבות למקורות, אבל מציג קודם את המידע שהמשתמש באמת צריך כדי להבין את הפרופיל ואת מצב הבדיקות, ורק אחר כך את שכבת ניהול העבודה.

## Impact
- Users: מסך הפרופיל נפתח על `סקירה`, מסביר מהו הפרופיל, מה ידוע עליו, מה מצב הבדיקות, ואיפה נשענים על specs/Zephyr/vendor sources.
- Devs: נכסי `.github` משמשים עכשיו כ-input פעיל ל-builder, ה-checks מזהים mismatch מול seeds, ויש API ייעודי להערות על טסטים.

## References
- Commit: pending (no commit in this task)
- Files:
  - .github/workflows/pts-hub-check.yml
  - dashboards/pts_report_he/autopts/assets/report.css
  - dashboards/pts_report_he/autopts/assets/report.js
  - dashboards/pts_report_he/autopts/data/hub-data.js
  - dashboards/pts_report_he/serve_with_run_status.py
  - tools/check_group_b_hub.py
  - tools/group_b_hub_data.py
  - tools/templates/pts_report_he/autopts/report.css
  - tools/templates/pts_report_he/autopts/report.js

## Notes
קבוצות משניות שנגעו בשינוי: `tools`, `infra`.
