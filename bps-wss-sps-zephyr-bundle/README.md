# חבילת העברה BPS/WSS/SPS עבור Zephyr

## מהי התיקיה הזאת
זאת חבילת העברה ברמת הריפו הראשי של הפרויקט. היא מכילה עותקים מדויקים של קבצי המימוש עבור:

- `BPS`
- `WSS`
- `SPS`
- `SCPS` כ-alias compatibility

הקבצים המקוריים נשארו במקומם תחת `zephyr/`. התיקיה הזאת נועדה כדי שאפשר יהיה לבצע `commit` ו-`push` מהריפו הראשי, בלי להיות תלויים ב-commit נפרד בתוך ה-submodule של `zephyr`.

## איפה הקבצים נמצאים עכשיו
שורש החבילה הוא:

`bps-wss-sps-zephyr-bundle/`

בתוך החבילה:

- `zephyr/` מכיל את עץ הקבצים המועתק כפי שהוא צריך להיראות בתוך Zephyr.
- `docs/` מכיל מסמכי רקע והיסטוריית עבודה.

## לאן צריך להעתיק את הקבצים בפרויקט אחר
יש להתייחס אל:

`bps-wss-sps-zephyr-bundle/zephyr/`

כאל מראה מלאה של שורש Zephyr אצל המשתמש השני.

אם אצל המשתמש השני Zephyr נמצא בנתיב:

`<their-project>/zephyr/`

אז כל קובץ שנמצא אצלך תחת:

`bps-wss-sps-zephyr-bundle/zephyr/...`

צריך להיות מועתק אל:

`<their-project>/zephyr/...`

כלומר, שומרים בדיוק על אותו נתיב יחסי אחרי `zephyr/`.

## טבלת מיפוי מדויקת: מאיפה לקחת ולאן להדביק

| קובץ בחבילה הנוכחית | יעד בפרויקט אחר |
|---|---|
| `bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/bps.h` | `<their-project>/zephyr/include/zephyr/bluetooth/services/bps.h` |
| `bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/wss.h` | `<their-project>/zephyr/include/zephyr/bluetooth/services/wss.h` |
| `bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/sps.h` | `<their-project>/zephyr/include/zephyr/bluetooth/services/sps.h` |
| `bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/scps.h` | `<their-project>/zephyr/include/zephyr/bluetooth/services/scps.h` |
| `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/bps.c` | `<their-project>/zephyr/subsys/bluetooth/services/bps.c` |
| `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/wss.c` | `<their-project>/zephyr/subsys/bluetooth/services/wss.c` |
| `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/sps.c` | `<their-project>/zephyr/subsys/bluetooth/services/sps.c` |
| `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig.bps` | `<their-project>/zephyr/subsys/bluetooth/services/Kconfig.bps` |
| `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig.wss` | `<their-project>/zephyr/subsys/bluetooth/services/Kconfig.wss` |
| `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig.sps` | `<their-project>/zephyr/subsys/bluetooth/services/Kconfig.sps` |
| `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig` | `<their-project>/zephyr/subsys/bluetooth/services/Kconfig` |
| `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/CMakeLists.txt` | `<their-project>/zephyr/subsys/bluetooth/services/CMakeLists.txt` |
| `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/Kconfig.logging` | `<their-project>/zephyr/subsys/bluetooth/Kconfig.logging` |
| `bps-wss-sps-zephyr-bundle/zephyr/README-bps-wss-sps-transfer.md` | אופציונלי: `<their-project>/zephyr/README-bps-wss-sps-transfer.md` |
| `bps-wss-sps-zephyr-bundle/docs/plans/2026-04-14-bps-wss-sps-implementation-worklog.md` | אופציונלי בלבד, לא חייב להיכנס לעץ `zephyr/` של הפרויקט היעד |

## מה משתמש חדש צריך לקרוא קודם

1. קודם לקרוא את הקובץ הזה.
2. אחר כך לקרוא את `zephyr/README-bps-wss-sps-transfer.md` כדי להבין את הוראות ההעתקה והמיזוג ברמת השירותים עצמם.
3. אם צריך היסטוריה מלאה של ההחלטות, לפתוח גם את `docs/plans/2026-04-14-bps-wss-sps-implementation-worklog.md`.

## כלל חשוב: מה מעתיקים כקובץ מלא ומה ממזגים בזהירות
בדרך כלל אפשר להעתיק כקבצים מלאים:

- `zephyr/include/zephyr/bluetooth/services/bps.h`
- `zephyr/include/zephyr/bluetooth/services/wss.h`
- `zephyr/include/zephyr/bluetooth/services/sps.h`
- `zephyr/include/zephyr/bluetooth/services/scps.h`
- `zephyr/subsys/bluetooth/services/bps.c`
- `zephyr/subsys/bluetooth/services/wss.c`
- `zephyr/subsys/bluetooth/services/sps.c`
- `zephyr/subsys/bluetooth/services/Kconfig.bps`
- `zephyr/subsys/bluetooth/services/Kconfig.wss`
- `zephyr/subsys/bluetooth/services/Kconfig.sps`

את הקבצים הבאים בדרך כלל צריך למזג בזהירות, ולא לדרוס אוטומטית, אלא אם פרויקט היעד הוא בדיוק על אותו baseline:

- `zephyr/subsys/bluetooth/services/Kconfig`
- `zephyr/subsys/bluetooth/services/CMakeLists.txt`
- `zephyr/subsys/bluetooth/Kconfig.logging`

## בלוק מוכן להדבקה לסוכן אחר
אם אתה רוצה שסוכן אחר יבצע את ההעתקה והמיזוג בשבילך, אפשר להדביק לו את הטקסט הבא:

```text
יש לי חבילת העברה מקומית בשם `bps-wss-sps-zephyr-bundle/` שמכילה מימושי Zephyr עבור `BPS`, `WSS`, `SPS`, ו-`SCPS` alias.

אני רוצה שתעתיק את המימושים מהחבילה הזאת אל פרויקט Zephyr היעד שלי, תוך שמירה מדויקת על הנתיבים.

פעל כך:

1. התייחס אל `bps-wss-sps-zephyr-bundle/zephyr/` כאל מראה של שורש Zephyr.
2. ברר מהו שורש Zephyr בפרויקט היעד שלי. נסמן אותו כאן כ-`<TARGET_ZEPHYR_ROOT>`.
3. העתק כקבצים מלאים את הקבצים הבאים:
   - `bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/bps.h` -> `<TARGET_ZEPHYR_ROOT>/include/zephyr/bluetooth/services/bps.h`
   - `bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/wss.h` -> `<TARGET_ZEPHYR_ROOT>/include/zephyr/bluetooth/services/wss.h`
   - `bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/sps.h` -> `<TARGET_ZEPHYR_ROOT>/include/zephyr/bluetooth/services/sps.h`
   - `bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/scps.h` -> `<TARGET_ZEPHYR_ROOT>/include/zephyr/bluetooth/services/scps.h`
   - `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/bps.c` -> `<TARGET_ZEPHYR_ROOT>/subsys/bluetooth/services/bps.c`
   - `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/wss.c` -> `<TARGET_ZEPHYR_ROOT>/subsys/bluetooth/services/wss.c`
   - `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/sps.c` -> `<TARGET_ZEPHYR_ROOT>/subsys/bluetooth/services/sps.c`
   - `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig.bps` -> `<TARGET_ZEPHYR_ROOT>/subsys/bluetooth/services/Kconfig.bps`
   - `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig.wss` -> `<TARGET_ZEPHYR_ROOT>/subsys/bluetooth/services/Kconfig.wss`
   - `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig.sps` -> `<TARGET_ZEPHYR_ROOT>/subsys/bluetooth/services/Kconfig.sps`
4. מזג בזהירות, ואל תדרוס אוטומטית, את הקבצים הבאים:
   - `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig` -> `<TARGET_ZEPHYR_ROOT>/subsys/bluetooth/services/Kconfig`
   - `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/CMakeLists.txt` -> `<TARGET_ZEPHYR_ROOT>/subsys/bluetooth/services/CMakeLists.txt`
   - `bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/Kconfig.logging` -> `<TARGET_ZEPHYR_ROOT>/subsys/bluetooth/Kconfig.logging`
5. השתמש גם במסמך `bps-wss-sps-zephyr-bundle/zephyr/README-bps-wss-sps-transfer.md` כהנחיית handoff נוספת בזמן ההעתקה והמיזוג.
6. אם צריך הקשר מלא, קרא גם את `bps-wss-sps-zephyr-bundle/docs/plans/2026-04-14-bps-wss-sps-implementation-worklog.md`.
7. בסיום, דווח לי:
   - אילו קבצים הועתקו כמות שהם
   - אילו קבצים מוזגו ידנית
   - אילו קונפליקטים היו
   - מה עוד נשאר לבדוק או לבנות

אל תשנה את הקבצים שבתוך `bps-wss-sps-zephyr-bundle/`. השתמש בהם כמקור בלבד.
```
