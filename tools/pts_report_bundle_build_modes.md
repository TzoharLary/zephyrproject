# `build_pts_report_bundle.py` - מדריך שימוש

המטרה של הסקריפט הזה היא לעדכן את קבצי הדשבורד של `pts_report_he` בלי להכריח full build על כל שינוי קטן.

הוא יודע לעבוד בשני סגנונות:
- build מלא של הכל
- build ממוקד של רק מה שבאמת צריך

הוא לא משנה את מיקום ה-artifacts. הכל עדיין נכתב תחת `dashboards/pts_report_he/`.

## מתי להשתמש במה

### Full build

להשתמש כשאת/ה רוצה לרענן את כל הדשבורד, או כשנגעת בכמה אזורים במקביל ולא שווה לדייק.

```bash
python3 tools/build_pts_report_bundle.py
```

אפשר גם במפורש:

```bash
python3 tools/build_pts_report_bundle.py build --scope all
```

### Build ממוקד

להשתמש כשברור מה בדיוק השתנה, ואת/ה רוצה build מהיר יותר ומדויק יותר.

דוגמאות:

```bash
# רק מודול JS אחד
python3 tools/build_pts_report_bundle.py build \
  --scope report \
  --report-component js \
  --report-js-module events

# רק BAS בתוך נתוני ה-report
python3 tools/build_pts_report_bundle.py build \
  --scope report \
  --report-component data \
  --report-data-unit profiles \
  --report-profile BAS

# רק נתוני hub
python3 tools/build_pts_report_bundle.py build \
  --scope hub \
  --hub-component data \
  --hub-data-unit group-b
```

## מה `plan` עושה

`plan` הוא תצוגה מקדימה.

הוא לא כותב קבצים. במקום זה הוא אומר מראש:
- אילו חלקים באמת ירוצו
- אילו קבצים באמת ייכתבו
- אילו קבצים לא ייכתבו
- ולמה

דוגמה:

```bash
python3 tools/build_pts_report_bundle.py plan \
  --scope report \
  --report-component data \
  --report-data-unit profiles \
  --report-profile BAS
```

זה שימושי כשלא בטוחים אם הבחירה באמת ממוקדת, או לפני שמריצים build יותר גדול.

## מה build ממוקד עושה בפועל

### בחירה של profile מסוים

אם בוחרים:

```bash
python3 tools/build_pts_report_bundle.py build \
  --scope report \
  --report-component data \
  --report-data-unit profiles \
  --report-profile BAS
```

אז בפועל:
- נבנה מחדש רק `BAS`
- נבנות גם התלויות הישירות שלו
- profiles אחרים לא נבנים אם לא נדרשו
- `report-data.js` לא נכתב

כלומר: זה טוב לרענון ממוקד של `BAS`, אבל זה לא full rebuild של כל שכבת הנתונים של הדוח.

### בחירה של `comparison`

אם בוחרים:

```bash
python3 tools/build_pts_report_bundle.py plan \
  --scope report \
  --report-component data \
  --report-data-unit comparison
```

אז צריך לדעת:
- `comparison` עדיין לא חי כיחידה עצמאית לגמרי
- בפועל הבחירה הזו מתרחבת ל-build מלא של `report-data.js`
- `plan` ו-`build` מסבירים את זה במפורש

### בחירה של `autopts-guide` ב-hub

אם בוחרים:

```bash
python3 tools/build_pts_report_bundle.py build \
  --scope hub \
  --hub-component data \
  --hub-data-unit autopts-guide
```

אז בפועל:
- מתרענן רק הנתון המשותף שנבחר
- `hub-data.js` לא נכתב

אם רוצים את קובץ הנתונים הסופי של ה-hub, צריך לבחור build שכולל `group-b` או full build של data ב-hub.

## מה `clean` עושה

`clean` לא מוחק את קבצי הדשבורד עצמם. הוא מוחק רק cache פנימי של יחידות build.

דוגמאות:

```bash
# ניקוי כל ה-cache
python3 tools/build_pts_report_bundle.py clean --scope all

# ניקוי ה-cache של report
python3 tools/build_pts_report_bundle.py clean --scope report

# ניקוי ה-cache של יחידה מסוימת בלבד
python3 tools/build_pts_report_bundle.py clean --scope report --unit report.profile.BAS
```

זה שימושי כשצריך לאלץ רענון של חלק קטן, בלי למחוק הכל.

## אפשרויות חשובות

- `--force`
  - מאלץ רענון של מה שנבחר במפורש, גם אם יש cache.

- `--no-cache`
  - מריץ בלי להשתמש ב-cache לקריאה או כתיבה.

- `--json-summary <path>`
  - כותב לקובץ JSON גם את התוכנית וגם את תוצאות הריצה.

## החלקים שאפשר לבחור

### פקודות

- `build`
- `plan`
- `clean`
- `legacy-full-build`

### scope

- `all`
- `report`
- `hub`

### report components

- `data`
- `assets`
- `html`
- `css`
- `shared-tokens`
- `js`
- `run-status-seed`

### report data units

- `runtime`
- `official-sources`
- `ics-refs`
- `line-refs`
- `profiles`
- `profile-build-plans`
- `comparison`
- `autopts-guide`
- `core`

### report profiles

- `DIS`
- `BAS`
- `HRS`
- `HID`

### report js modules

- `legacy`
- `state`
- `persistence`
- `render`
- `events`

### hub components

- `data`
- `assets`
- `html`
- `css`
- `js`

### hub data units

- `group-b`
- `autopts-guide`

## מה נשאר נכון תמיד

- ברירת המחדל נשארה backward-compatible: אם לא כתבת command, זה `build`.
- cache נשמר תחת `.cache/pts_report_bundle/`.
- אם ה-output זהה למה שכבר קיים, הקובץ לא נכתב מחדש.
- בשדות volatile של `report-data.js` ו-`hub-data.js` יש ייצוב כדי לצמצם churn מיותר.
