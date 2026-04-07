# Refresh Profile Builder Seed Docs And Spec Paths

- Date: 2026-03-23
- Group: infra
- Status: done

## Context
שכבת ה-seed של profile builder תחת `.github/data/` סבלה משתי בעיות קטנות אך מצטברות:
- מבנה פתיח לא תקין ב-`.github/data/profile-patterns.md`, עם שורות `#` ששימשו כהערות במקום Markdown תקני
- הפניות ישנות ל-`docs/profiles/**` גם אחרי שמעבר ה-artifacts הרשמיים בוצע ל-`data/raw/bluetooth_sig/profiles/**`

## Changes
- הוחלף פתיח לא תקין במבנה Markdown תקני:
  - כותרת ראשית אחת
  - פסקת תיאור רגילה
  - `## Contents` עם רשימת קישורים פנימיים לסעיפים 1–10
- עודכנו ההפניות במסמכי ה-seed אל נתיבי ה-spec החדשים תחת `data/raw/bluetooth_sig/profiles/**`.
- נשמר התוכן המקצועי של המסמכים ללא שינוי לוגי.

## Why
מבנה Markdown תקני משפר קריאות, יציבות עוגנים פנימיים, והפעלה עקבית של תצוגת תוכן/ניווט בכלי עריכה ופלטפורמות צפייה; עדכון נתיבי ה-spec שומר על התאמה בין שכבת ה-seed לבין מבנה ה-data החדש.

## Impact
- Users: ה-seed docs וה-metadata מצביעים לנתיבי spec עקביים וברורים יותר.
- Devs: תחזוקת מסמכי ה-seed פשוטה יותר, הכותרות אינן ״מזויפות״, ואין הפניות legacy ל-`docs/profiles/**`.

## References
- Commit: 8497a21
- Files:
  - .github/data/profile-patterns.md
  - .github/data/profiles-db.yaml
  - CHANGELOG/infra/2026-03-23-normalize-profile-patterns-markdown-header.md
  - CHANGELOG/INDEX.md

## Notes
Primary group נקבע ל-`infra` משום שהשינוי העיקרי הוא בקובץ תחת `.github/`.
