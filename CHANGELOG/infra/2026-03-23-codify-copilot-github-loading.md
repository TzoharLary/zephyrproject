# Codify Copilot-Style `.github` Loading

- Date: 2026-03-23
- Group: infra
- Status: done

## Context
נדרש ליישר את התנהגות הסוכן בפרויקט כך שתחקה בצורה מפורשת את האופן שבו GitHub Copilot מתייחס לקבצי `.github/` של הריפו: אילו קבצים נטענים תמיד, אילו נטענים לפי `applyTo`, ואילו משמשים רק כ-workflow או knowledge base לפי סוג המשימה.

## Changes
- הוספתי ל-`AGENTS.md` סעיף `GitHub Copilot Project Parity` שמגדיר פרוטוקול טעינה ושימוש עבור `copilot-instructions`, `instructions`, `prompts`, `data`, `system-journal` ו-`workflows`.
- תיעדתי בקובץ ההוראות מתי להשתמש בכל קובץ תחת `.github/`, מה התפקיד שלו, ומהם כללי ההכרעה במקרה של סתירה בין metadata לבין evidence ישיר מהריפו.

## Why
הסוכן טוען את `AGENTS.md` אוטומטית בכל משימה, ולכן זה המקום הנכון לקבע בו policy שיגרום לו לעבוד עם נכסי `.github/` באותו מודל החלטה של Copilot במקום להסתמך על זיכרון אד-הוק או על טעינה ידנית לא עקבית.

## Impact
- Users: בקשות עתידיות שמערבות BLE profiles, Group B hub, checks או metadata של `.github` יקבלו התנהגות עקבית יותר מול נכסי הפרויקט.
- Devs: יש עכשיו map ברור של קבצי `.github/` והטריגרים לשימוש בהם, מה שמפחית ambiguity ומקל על תחזוקת הוראות הפרויקט.

## References
- Commit: pending (no commit in this task)
- Files:
  - AGENTS.md
  - CHANGELOG/infra/2026-03-23-codify-copilot-github-loading.md
  - CHANGELOG/INDEX.md

## Notes
ה-policy החדש מגדיר parity ברמת הפרויקט בלבד. הוא לא מנסה לחקות הוראות או skills גלובליים של GitHub Copilot מחוץ לריפו הזה.
