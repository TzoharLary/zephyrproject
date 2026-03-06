# PTS Report Dashboard (`pts_report_he`)

מדריך קצר למפתחים: איך לפתוח ולהריץ את הדשבורד מתוך VSCode / VSCode Insiders, כך ש־"סטטוס וניהול הרצה" יישמר לקובץ `run-status-state.json` (ולא רק ל־`localStorage`).

## מה חשוב לדעת

הדשבורד תומך בשתי צורות הרצה:

1. פתיחה כאתר סטטי (למשל Live Server)
- האתר ייפתח ויעבוד.
- אבל שדות "סטטוס וניהול הרצה" יישמרו רק בדפדפן (`localStorage`).
- השינויים לא ייכתבו לקובץ JSON בריפו.

2. הרצה דרך שרת Python הייעודי (מומלץ)
- האתר ייפתח.
- יש API מקומי (`/api/run-status`) שכותב לקובץ.
- שדות "סטטוס וניהול הרצה" יישמרו לקובץ:
  - `dashboards/pts_report_he/data/run-status-state.json`
- אפשר לבצע `git add/commit/push` כדי לשתף סטטוסים עם אחרים.

## דרישות מקדימות

- Python 3 מותקן (מומלץ `python3`)
- VSCode או VSCode Insiders
- (מומלץ) תוסף Python של Microsoft ב־VSCode

## הדרך המומלצת (עובדת גם ב־mac וגם ב־Windows)

### 1. לפתוח Terminal בתוך VSCode

ב־VSCode:
- `Terminal` -> `New Terminal`

ודא/י שאת/ה נמצא/ת בשורש הריפו (`zephyrproject`).

### 2. להריץ את השרת הייעודי

#### macOS / Linux

```bash
python3 dashboards/pts_report_he/serve_with_run_status.py
```

#### Windows (PowerShell / CMD)

```powershell
py dashboards/pts_report_he/serve_with_run_status.py
```

אם `py` לא קיים:

```powershell
python dashboards/pts_report_he/serve_with_run_status.py
```

### 3. מה אמור לקרות

- השרת יעלה על `http://127.0.0.1:8000/`
- הדפדפן ברירת המחדל ייפתח אוטומטית
- תראה/י בטרמינל הודעות כמו:
  - `Serving ... at http://127.0.0.1:8000/`
  - `Run-status API: http://127.0.0.1:8000/api/run-status`
  - `File-backed storage: .../dashboards/pts_report_he/data/run-status-state.json`

## שימוש דרך קליק ימני על הקובץ (VSCode)

אפשרי, אבל פחות מומלץ מהטרמינל כי בטרמינל יותר קל לראות לוגים ולעצור/להריץ שוב.

### macOS / Windows (עם Python extension)

ב־Explorer של VSCode:
- קליק ימני על `dashboards/pts_report_he/serve_with_run_status.py`
- לבחור `Run Python File in Terminal`

מה *לא* לבחור אם רוצים שמירה לקובץ:
- `Open with Live Server` (זה לא כותב ל־JSON)
- `Run Code` (של Code Runner) אם הוא לא משאיר שרת רץ בצורה תקינה

## עצירת השרת

בטרמינל שבו השרת רץ:
- `Ctrl+C`

## שינוי פורט (אם 8000 תפוס)

### macOS / Linux

```bash
python3 dashboards/pts_report_he/serve_with_run_status.py --port 8010
```

### Windows

```powershell
py dashboards/pts_report_he/serve_with_run_status.py --port 8010
```

## ביטול פתיחה אוטומטית של הדפדפן

### macOS / Linux

```bash
python3 dashboards/pts_report_he/serve_with_run_status.py --no-open
```

### Windows

```powershell
py dashboards/pts_report_he/serve_with_run_status.py --no-open
```

## איך לוודא שהשמירה באמת הולכת לקובץ

1. לפתוח את הדשבורד דרך השרת הייעודי (לא Live Server).
2. לשנות ערך כלשהו ב־"סטטוס וניהול הרצה".
3. לפתוח את הקובץ:
   - `dashboards/pts_report_he/data/run-status-state.json`
4. לוודא שהשדה `updated_at` השתנה ו/או שיש עדכון תחת `entries`.

## תקלות נפוצות

### הדשבורד נפתח אבל השמירה לא נכנסת ל־JSON

סיבה נפוצה:
- פתחת את האתר דרך `Live Server` / שרת סטטי רגיל.

פתרון:
- להריץ את `serve_with_run_status.py` ולפתוח את הכתובת שהוא מדפיס.

### `python3` / `py` לא מזוהה

פתרון:
- לוודא ש־Python מותקן
- ב־VSCode לבחור interpreter נכון:
  - `Cmd+Shift+P` (mac) / `Ctrl+Shift+P` (Windows)
  - `Python: Select Interpreter`

### פורט 8000 תפוס

פתרון:
- להשתמש ב־`--port 8010` (או פורט אחר)

## קבצים רלוונטיים

- דף ראשי: `dashboards/pts_report_he/index.html`
- שרת עם שמירה לקובץ: `dashboards/pts_report_he/serve_with_run_status.py`
- קובץ סטטוסים משותף: `dashboards/pts_report_he/data/run-status-state.json`
- assets generated:
  - `dashboards/pts_report_he/assets/state.js`
  - `dashboards/pts_report_he/assets/persistence.js`
  - `dashboards/pts_report_he/assets/render.js`
  - `dashboards/pts_report_he/assets/events.js`
  - `dashboards/pts_report_he/assets/report.css`
  - `dashboards/pts_report_he/shared-tokens.css`
  - `dashboards/pts_report_he/data/report-data.js`

---

## ⚠️ חשוב: מה לערוך ומה נוצר אוטומטית

**אל תערוך ישירות** את הקבצים תחת `dashboards/pts_report_he/assets/` ו-`dashboards/pts_report_he/data/`.
אלה **תוצרי בנייה** (build artifacts) שנוצרים על ידי:

```
tools/build_pts_report_bundle.py
```

**מקור העריכה האמיתי** נמצא ב:

| קובץ לעריכה | מה הוא אחראי עליו |
|---|---|
| `tools/templates/pts_report_he/state.js` | קבועים ומשתני state |
| `tools/templates/pts_report_he/persistence.js` | שמירת/טעינת run-status (localStorage + file API) |
| `tools/templates/pts_report_he/render.js` | כל פונקציות הרינדור (HTML) |
| `tools/templates/pts_report_he/events.js` | event binding ואתחול |
| `tools/templates/pts_report_he/report.css` | סגנון הדשבורד הראשי |
| `tools/templates/pts_report_he/shared-tokens.css` | design tokens משותפים לכל תת-עמודי הדשבורד |
| `tools/templates/pts_report_he/index.html` | מבנה HTML הדשבורד הראשי |
| `tools/templates/pts_report_he/autopts/` | כל תת-עמוד AutoPTS + Group B |

אחרי כל עריכה ב-templates, יש להריץ את הבנייה כדי לעדכן את ה-artifacts:

```bash
cd tools
python3 build_pts_report_bundle.py
```

ה-artifacts המעודכנים ייכתבו ל-`dashboards/pts_report_he/`.

### ארכיטקטורת ה-JS (מודולרית)

ה-JS נטען בסדר הבא (כל מודול תלוי במודולים לפניו):

```
state.js → persistence.js → render.js → events.js
```

- `state.js`: קבועים (BUCKETS, PROFILE_PANEL_CONFIG, RUN_STATUS_*) ומשתני state
- `persistence.js`: שמירה/טעינה של run-status ב-localStorage ו-file API; CRUD על run entries
- `render.js`: כל פונקציות `render*` ו-`fill*` שבונות את ה-DOM
- `events.js`: event listeners, `activatePanel()`, `applySearch()`, ואתחול הדף
