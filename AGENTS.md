# Project Agent Instructions

מטרת הקובץ: להבטיח שכל שינוי בקוד או בתיעוד יתועד מיד תחת `CHANGELOG/` לפי הכללים הקיימים בפרויקט.

## Scope

- הקובץ חל על כל הריפו.
- אם בעתיד יתווסף `AGENTS.md` בתת-תיקייה, ההוראות המקומיות יגברו רק בתוך אותה תת-תיקייה.

## GitHub Copilot Project Parity

מטרת הסעיף: לגרום לסוכן שקורא את `AGENTS.md` להתייחס לנכסי `.github/` של הפרויקט באותו מודל עבודה שבו GitHub Copilot מתייחס אליהם ברמת הריפו.

`AGENTS.md` נשאר מקור ההוראות הראשי עבור סוכן זה. עם זאת, כדי להתנהג כמו Copilot בתוך הפרויקט, חובה להפעיל את פרוטוקול הטעינה הבא בכל משימה רלוונטית.

### Loading Protocol (Mandatory)

1. לכל משימה בתוך הריפו, להתייחס אל `.github/copilot-instructions.md` כאל repository-wide instructions ולטעון אותו לפני עבודה מהותית, אם הוא עוד לא נקרא בתור הנוכחי.
2. לבדוק האם קיימים קבצים תחת `.github/instructions/**/*.instructions.md` שה-`applyTo` שלהם תואם לקבצים שבסקופ המשימה או לנתיבים שהמשתמש מבקש לשנות. אם כן, לטעון אותם בנוסף ל-`copilot-instructions.md`, לא במקומו.
3. להתייחס אל `.github/prompts/*.prompt.md` כאל task-specific workflow, לא כאל קובץ שנטען אוטומטית בכל משימה. יש לטעון אותו כשהמשימה תואמת באופן ברור למטרה שה-prompt מגדיר, או כשהמשתמש מבקש במפורש לפעול לפי אותו workflow/mode.
4. אם נטען prompt file, יש לטעון גם את קבצי ה-data/governance שהוא מצהיר עליהם כ-context ולהשתמש בהם באופן עקבי לאורך המשימה.
5. לא לטעון את כל `.github/` בצורה עיוורת בכל משימה. כדי לשמור על parity עם Copilot, טוענים תמיד את ההוראות הרוחביות, ואז רק את קבצי `.instructions.md`, ה-prompt files וה-data files שהמשימה באמת מפעילה.

### `.github/` Asset Map

- `.github/copilot-instructions.md`
  - זהו repository-wide custom instructions file.
  - יש לטעון אותו תמיד בתחילת משימה בתוך הריפו.
  - משתמשים בו כדי ליישר שפה, מטרת מערכת, כללי changelog, והפניות לנכסי הידע המרכזיים של הפרויקט.

- `.github/instructions/zephyr-bt-profile-builder.instructions.md`
  - זהו path-specific instructions file עם `applyTo` ל-`zephyr/subsys/bluetooth/services/**,zephyr/include/zephyr/bluetooth/services/**`.
  - יש לטעון אותו כשעובדים על קבצים תואמים, או כשהמשימה היא ליצור, להרחיב, להסביר, לתעד או לדבג Zephyr BLE GATT profile גם אם השינוי עוד לא התחיל בפועל בנתיבים האלה.
  - משתמשים בו עבור classification rules, source governance, output format, quality checklist וגבולות השימוש ב-Zephyr/TI/Auto-PTS/BT SIG/Nordic.

- `.github/prompts/zephyr-bt-profile-builder.prompt.md`
  - זהו reusable prompt workflow, לא instruction file גלובלי.
  - יש לטעון אותו כשהמשימה תואמת לזרימת העבודה שלו: `create`, `extend`, `understand`, `debug` עבור Zephyr BLE GATT profiles.
  - כשמשתמשים בו, יש לפעול לפי שלבי `IDENTIFY -> CLASSIFY -> DISAMBIGUATE -> RESEARCH -> BUILD -> EXPLAIN` במידה שרלוונטית למשימה.

- `.github/data/profiles-db.yaml`
  - זהו metadata seed לידע על פרופילי BLE: `id`, `name`, `UUIDs`, `characteristics`, `type`, `complexity`, `pattern`, `similar_profiles`, `reference_files`, `notes`, `pts_tracked`.
  - משתמשים בו כדי לזהות פרופיל, לבחור reference profile, להבין mandatory/optional basics, ולהפיק summary ראשוני.
  - אין להתייחס אליו כ-source of truth בלעדי. כל טענה שמוצגת למשתמש חייבת לעבור reconciliation מול קוד, `docs/`, `Group_B_data`, `auto-pts` או מקור מוסמך אחר בתוך הפרויקט.

- `.github/data/profile-patterns.md`
  - זהו pattern library סטטי למבני מימוש ולהסברי behavior.
  - משתמשים בו כדי להסביר איך פרופיל אמור להתנהג, לבחור pattern מתאים, ולגזור מבנה Zephyr-native במקום להמציא pattern מחדש.
  - אם מזכירים pattern section, עדיף לציין את הסעיף (`§10.x` וכו') כשזה מוסיף בהירות.

- `.github/data/sources-map.yaml`
  - זהו קובץ governance, לא מאגר עובדות סופי.
  - משתמשים בו כדי להחליט איזה מקורות מותר/אסור לצרוך, באיזה סדר עדיפויות, ואיך לתייג מסקנות (`implementation`, `validation`, `spec`, `logic reference`).
  - אם יש סתירה בין `sources-map.yaml` לבין evidence מקומי בקוד או ב-`docs/`, לא מכריעים על סמך ה-map לבדו.

- `.github/docs/system-journal.md`
  - זהו מסמך rationale, history ו-schema evolution.
  - יש לטעון אותו כשעובדים על מערכת ההוראות עצמה, על `.github` assets, על שינויים ארכיטקטוניים, על חוסר עקביות בין data files, או כשצריך להבין למה מערכת ה-profile builder בנויה כפי שהיא בנויה.
  - אין להשתמש בו כמקור נורמטיבי יחיד לעובדות profile-level אם יש מקור ישיר יותר.

- `.github/workflows/pts-hub-check.yml`
  - זהו מקור האמת של CI המקומי עבור PTS Hub checks.
  - יש לעיין בו כשנוגעים בקבצים שה-workflow מאזין להם, כשמשנים builder/checks/bundles, או כשמעצבים הוראות שמשפיעות על תהליך ולידציה.
  - כאשר משנים קבצים בסקופ של workflow זה, יש להריץ מקומית את ה-checks המקבילים ככל שאפשר.

### Task-to-File Decision Rules

- משימת ריפו כללית: לטעון `.github/copilot-instructions.md`.
- משימת BLE GATT profile ב-Zephyr: לטעון גם את `.github/instructions/zephyr-bt-profile-builder.instructions.md`, את `.github/prompts/zephyr-bt-profile-builder.prompt.md`, ואת שלושת קבצי ה-data תחת `.github/data/`.
- משימת מחקר/הסבר/סיווג על פרופיל BLE בלי שינוי קוד: לטעון לפחות `copilot-instructions.md`, `profiles-db.yaml`, `profile-patterns.md`, `sources-map.yaml`, ואת ה-prompt אם ה-flow שלו מועיל למשימה.
- משימת Group B / PTS Hub שנשענת על metadata/patterns/governance: לטעון `copilot-instructions.md`, את קבצי ה-data תחת `.github/data/`, ואת `system-journal.md` אם יש צורך ב-rationale או ביישור schema.
- משימת CI/checks/validation: לטעון `copilot-instructions.md`, את workflow הרלוונטי תחת `.github/workflows/`, ואת קבצי `.github/data/` אם ה-checks תלויים בהם.

### Conflict Rules

- `AGENTS.md` מגדיר את התנהגות הסוכן בפרויקט; קבצי `.github` מגדירים context, workflow ו-governance בסגנון Copilot. כשיש התנגשות ישירה, לפעול לפי `AGENTS.md` ואז לשלב את `.github` במידה המרבית שאינה סותרת אותו.
- `profiles-db.yaml` הוא seed בלבד. אם `docs/`, קוד, workspace, או runtime evidence סותרים אותו, יש להציג למשתמש את המידע reconciled, לא את ערך ה-DB הגולמי.
- `sources-map.yaml` אינו עוקף evidence ישיר; הוא רק מסדיר סדר ומותר/אסור.
- prompt files אינם נטענים אוטומטית רק כי הם קיימים. יש להשתמש בהם כאשר המשימה תואמת למטרה שלהם.

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
