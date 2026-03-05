# Enforce Changelog Agent Instructions

- Date: 2026-03-05
- Group: infra
- Status: done

## Context
נוצרה תיקיית `CHANGELOG/` עם כללים ותבנית, אבל לא הייתה הוראת סוכן ראשית מחייבת ברמת הריפו שמבטיחה שכל שינוי יתועד מיד.

## Changes
- נוצר קובץ `AGENTS.md` בשורש הריפו כמדיניות ראשית לתיעוד שינויים.
- נוספו כללי מיפוי חד-משמעיים בין נתיבי קבצים לקבוצות changelog.
- עודכן `.github/copilot-instructions.md` כדי להחיל את אותה מדיניות גם ב-VS Code/Copilot.
- עודכן `.gitignore` כדי למנוע הכנסת `cache` מקומי וקובץ state דינמי לריפו.

## Why
כדי להבטיח עבודה עקבית: אין שינוי קוד/תיעוד ללא רשומת changelog ו-`INDEX.md` מעודכן.

## Impact
- Users: קל יותר להבין מה השתנה ולמה, באופן עקבי.
- Devs: פחות החמצות תיעוד ופחות חוסר אחידות בין כלים/סוכנים.

## References
- Commit: `pending (no commit in this task)`
- Files:
  - `AGENTS.md`
  - `.github/copilot-instructions.md`
  - `.gitignore`
  - `CHANGELOG/infra/2026-03-05-enforce-changelog-agent-instructions.md`
  - `CHANGELOG/INDEX.md`

## Notes
המדיניות נשענת על הכללים הקיימים ב-`CHANGELOG/README.md` וב-`CHANGELOG/ENTRY_TEMPLATE.md`, ולא מחליפה אותם.
