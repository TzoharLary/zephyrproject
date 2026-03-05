# Project Agent Instructions

מטרת הקובץ: להבטיח שכל שינוי בקוד או בתיעוד יתועד מיד תחת `CHANGELOG/` לפי הכללים הקיימים בפרויקט.

## Scope

- הקובץ חל על כל הריפו.
- אם בעתיד יתווסף `AGENTS.md` בתת-תיקייה, ההוראות המקומיות יגברו רק בתוך אותה תת-תיקייה.

## Changelog Policy (Mandatory)

כל משימה שכוללת שינוי בקבצים מנוהלים ב-Git חייבת לכלול גם עדכון `CHANGELOG` באותה עבודה.

חובה לבצע:

1. לבחור קבוצת שינוי ראשית לפי מיפוי הנתיבים בטבלה למטה.
2. ליצור או לעדכן רשומה תחת `CHANGELOG/<group>/`.
3. לעדכן את `CHANGELOG/INDEX.md`.
4. לוודא שהרשומה כוללת את כל שדות החובה מהתבנית.

לא מסיימים משימה עם שינויי קבצים בלי סעיפים 2-3.

## Group Mapping (Single Meaning)

הקצאת קבוצה לפי נתיב הקובץ שהשתנה:

- `dashboards/**` -> `dashboard`
- `docs/**` -> `docs`
- `tools/**` -> `tools`
- `zephyr/**`, `auto-pts/**`, `modules/**`, `bootloader/**` -> `firmware`
- `.github/**`, `.vscode/**`, קבצי root של ריפו (כמו `README.md`, `.gitignore`, `west_boards.txt`) -> `infra`

אם שינוי כולל כמה קבוצות:

1. הקבוצה הראשית נקבעת לפי מספר הקבצים הגבוה ביותר.
2. במקרה תיקו משתמשים בסדר הכרעה קבוע: `dashboard`, `docs`, `tools`, `firmware`, `infra`.
3. הקבוצות המשניות נרשמות ב-`## Notes` ברשומה הראשית.
4. ב-`CHANGELOG/INDEX.md` מוסיפים שורת primary אחת בלבד (ללא שכפול שורות משניות).

## Entry File Rules

- תיקייה: `CHANGELOG/<group>/`
- שם קובץ: `YYYY-MM-DD-short-topic.md` (kebab-case באנגלית קטנה)
- תאריך: תאריך מקומי נוכחי (Asia/Jerusalem)

אם כבר יש קובץ לאותו נושא ולאותו יום, מעדכנים אותו במקום ליצור קובץ חדש.

## Required Content (Per Entry)

הרשומה חייבת לכלול בדיוק את המבנה של `CHANGELOG/ENTRY_TEMPLATE.md`:

- `Date`
- `Group`
- `Status`
- `## Context`
- `## Changes`
- `## Why`
- `## Impact`
- `## References`

`## Notes` הוא רשות, אך מומלץ כשיש קבוצות משניות או follow-up.

## References Field Rule

- אם נוצר קומיט באותה משימה: לרשום hash קצר ב-`Commit`.
- אם לא נוצר קומיט: לרשום `Commit: pending (no commit in this task)`.
- כשנוצר קומיט מאוחר יותר באותה משימה, מעדכנים את `Commit` מ-`pending` ל-hash בפועל.

## Index Rule

בכל יצירה/עדכון של רשומת changelog, מעדכנים גם את `CHANGELOG/INDEX.md` עם שורה חדשה בפורמט הקיים:

`Date | Group | Title | Reason (Short) | Commit`

אם מעדכנים רשומה קיימת (ולא יוצרים חדשה), מעדכנים את שורת ה-index הקיימת לאותה רשומה במקום להוסיף שורה כפולה.

## Exceptions

אין חובת changelog רק במקרים הבאים:

- לא השתנה אף קובץ מנוהל ב-Git (שיחה בלבד/ניתוח בלבד).
- שינוי זמני שלא נכנס ל-Git (artefacts מקומיים בלבד).

בכל מקרה אחר: חובה לעדכן `CHANGELOG`.
