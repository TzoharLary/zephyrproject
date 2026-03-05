# סקירת ארכיטקטורה — Dashboards

**תאריך:** 5 במרץ 2026
**סקופ:** `dashboards/phases_tracking` ו-`dashboards/pts_report_he`

## מטרה
לתת תמונה מדויקת וחד-משמעית על מצב הארכיטקטורה: מה נכון, מה לא נכון, ומה לשפר קודם.

---

## עובדות מחייבות

1. מבנה התיקיות הנכון:

```text
dashboards/
├── phases_tracking/
└── pts_report_he/
    └── autopts/
```

אין תיקייה `dashboards/autopts`.

2. ב-`pts_report_he` קובצי `assets/*` ו-`data/*` הם תוצרי בנייה. מקור העריכה:
- `tools/templates/pts_report_he/`
- `tools/templates/pts_report_he/autopts/`
- `tools/build_pts_report_bundle.py`

מסקנה: שינוי ארכיטקטוני צריך להתבצע קודם ב-templates/build script.

---

## בדיקת טענות מהגרסה הקודמת

### נכון
1. `pts_report_he` מונוליטי וקשה לתחזוקה.
2. ניהול state מפוזר בקבצי JS גדולים.
3. אין בדיקות אוטומטיות ייעודיות ל-`dashboards/`.

### נכון חלקית
1. "אין מודולריות": נכון בעיקר ל-`pts_report_he`; ב-`phases_tracking` המצב טוב יותר.
2. "נגישות חלשה": נכון חלקית; יש שימוש ב-ARIA/role אך לא מלא ועקבי.

### לא נכון
1. "אין ניווט בין עמודים": לא נכון. יש ניווט בין `pts_report_he` ל-`autopts` וחזרה.
2. "אין error handling ל-API": לא נכון. יש try/catch, fallback, ומצב read-only.
3. "יש `dashboards/autopts`": לא נכון.

---

## חולשות אמיתיות לפי עדיפות

### עדיפות גבוהה
1. מונוליתיות ב-`pts_report_he` (ערבוב rendering/state/events/persistence).
2. רינדור רחב עם `innerHTML` במקום עדכונים ממוקדים.
3. בלבול אפשרי בין artifacts לבין templates.

### עדיפות בינונית
4. state מבוזר ללא מנגנון מרכזי אחיד.
5. CSS לא אחיד בין הדשבורדים.

### עדיפות נמוכה
6. פערי נגישות נקודתיים.
7. היעדר בדיקות אוטומטיות.

---

## תקלות פונקציונליות קונקרטיות

1. ב-`phases_tracking` טעינת ערכים מ-localStorage מבוססת truthy; ערך ריק יכול לא להיטען.
2. הכלל "Owner ו-Reviewer שונים" מופיע בטקסט אך לא נאכף בלוגיקה.

---

## תוכנית פעולה חד-משמעית

### שלב 1 (מיידי)
1. לתקן את באג הערך הריק ב-`phases_tracking`.
2. להוסיף ולידציה ל-Owner/Reviewer.
3. להוסיף README ברור: מה נערך ב-templates ומה נוצר אוטומטית.

### שלב 2 (קצר טווח)
1. לפרק את `tools/templates/pts_report_he/report.js` למודולים: `state`, `render`, `events`, `persistence`.
2. להגדיר חוזה state יחיד לכל פאנל ראשי.
3. לצמצם רינדור מלא ולעבור לעדכונים ממוקדים.

### שלב 3 (בינוני)
1. להוסיף smoke tests לניווט/חיפוש/שמירת state.
2. לאחד design tokens.
3. להשלים פערי נגישות לפי checklist.

---

## סיכום
המערכת עובדת. הסיכון המרכזי הוא מונוליתיות ב-`pts_report_he` ותלות בתהליך build שלא תמיד ברור לעורך חדש.
הסדר הנכון: תיקוני דיוק קטנים -> פירוק מונוליתיות -> בדיקות ואחידות UI.
