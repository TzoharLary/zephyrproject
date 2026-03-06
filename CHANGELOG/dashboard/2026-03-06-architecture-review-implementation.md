# Implement ARCHITECTURE_REVIEW_HE.md — All Three Stages

- Date: 2026-03-06
- Group: dashboard
- Status: done

## Context
`dashboards/ARCHITECTURE_REVIEW_HE.md` מסמך ארכיטקטורה שהגדיר שלושה שלבי שיפור לדשבורד `pts_report_he`.
השינויים מיישמים את כל הפריטים בכל שלושת השלבים במלואם.

## Changes

### שלב 1 — תיקונים מיידיים
- **תיקון באג localStorage**: שינוי בדיקת truthy `!raw` לבדיקה מפורשת `raw === null || raw === undefined` ב-`loadRunStatusState()` — תמנע דילוג על ערכי מחרוזת ריקה.
- **הוספת שדה Reviewer + ולידציה**: הוספת שדה `reviewer` ל-`emptyTrackState()` ו-`normalizeTrackState()`. נאכף הכלל: owner ≠ reviewer בכל מקום (normalizeTrackState, updateRunEntry). הוסף `renderReviewerOptions()` לממשק המשתמש. `syncRunControls()` מסנכרן גם את שדה reviewer.
- **עדכון README**: הוסף קטע מפורש שמסביר מה נערך ב-templates ומה נוצר אוטומטית כ-artifact, כולל טבלת מיפוי וסדר הטעינה של מודולי ה-JS.

### שלב 2 — פירוק מונוליתיות (short-term)
- **פיצול `report.js` למודולים**:
  - `state.js` — קבועים (BUCKETS, PROFILE_PANEL_CONFIG, RUN_STATUS_*) ומשתני state.
  - `persistence.js` — טעינה/שמירה של run-status (localStorage + file API), CRUD על run entries.
  - `render.js` — כל פונקציות render/fill.
  - `events.js` — event binding, `activatePanel()`, `applySearch()`, ואתחול.
- **עדכון `index.html`** — טוען את 4 המודולים בסדר הנכון (state → persistence → render → events).
- **עדכון `build_pts_report_bundle.py`** — מעתיק את 4 המודולים לתיקיית ה-artifacts.
- **חוזה state מסומן** — כל מודול מתועד עם תלויותיו.
- **רינדור ממוקד**: `syncRunControls()` עושה DOM update ממוקד ל-reviewer dropdown כאשר owner משתנה, במקום לעשות re-render מלא של הווידג'ט.

### שלב 3 — שיפורים בינוניים
- **Design tokens משותפים**: יצירת `shared-tokens.css` עם כל הטוקנים המשותפים לשני הדשבורדים. שני `index.html` טוענים אותו לפני `report.css`.
- **Smoke tests**: יצירת `tools/templates/pts_report_he/tests/smoke.html` — בדיקות עישון לכל הפונקציות הקריטיות (state, persistence, reviewer validation, localStorage round-trip).
- **נגישות**: הוספת `<nav aria-label>` לניווט, `aria-controls`/`aria-pressed` לכפתורי ניווט, `aria-hidden` דינמי לפאנלים, `role="search"` לסרגל הכלים, `aria-label` לכפתורי פעולה, וקלאס `visually-hidden` ל-CSS.

## Why
ה-ARCHITECTURE_REVIEW_HE.md הגדיר את הפריטים כ"מחייבים" בכל שלב. הפירוק למודולים מקטין את סיכון שגיאות merge ומאפשר פיתוח מקבילי. הולידציה של Owner≠Reviewer נאכפת כעת בקוד ולא רק בטקסט. ה-design tokens המשותפים מבטיחים עקביות ויזואלית בין תת-הדשבורדים.

## Impact
- Users: ממשק run-tracking מציג כעת שדה "מאשר" עם ולידציה אוטומטית. שיפורי נגישות עם screen readers.
- Devs: מבנה JS מודולרי ברור; קל לתחזק ולהרחיב. README מסביר בדיוק מה לערוך ואיפה. Smoke tests לתפיסת רגרסיות.

## References
- Commit: pending (no commit in this task)
- Files:
  - `tools/templates/pts_report_he/state.js` (new)
  - `tools/templates/pts_report_he/persistence.js` (new)
  - `tools/templates/pts_report_he/render.js` (new)
  - `tools/templates/pts_report_he/events.js` (new)
  - `tools/templates/pts_report_he/shared-tokens.css` (new)
  - `tools/templates/pts_report_he/tests/smoke.html` (new)
  - `tools/templates/pts_report_he/report.js` (modified)
  - `tools/templates/pts_report_he/index.html` (modified)
  - `tools/templates/pts_report_he/autopts/index.html` (modified)
  - `tools/build_pts_report_bundle.py` (modified)
  - `dashboards/pts_report_he/assets/state.js` (new artifact)
  - `dashboards/pts_report_he/assets/persistence.js` (new artifact)
  - `dashboards/pts_report_he/assets/render.js` (new artifact)
  - `dashboards/pts_report_he/assets/events.js` (new artifact)
  - `dashboards/pts_report_he/assets/report.css` (modified)
  - `dashboards/pts_report_he/shared-tokens.css` (new artifact)
  - `dashboards/pts_report_he/index.html` (modified)
  - `dashboards/pts_report_he/autopts/index.html` (modified)
  - `dashboards/pts_report_he/README.md` (modified)

## Notes
- `dashboards/pts_report_he/assets/report.js` נשמר כ-backward-compatible fallback אך לא נטען יותר על ידי `index.html`.
- ה-phases_tracking directory הוסר ב-commit `af93ee6`; הבאגים הספציפיים לו אינם רלוונטיים לקוד הנוכחי, אך הדפוסים תוקנו ב-`pts_report_he`.
