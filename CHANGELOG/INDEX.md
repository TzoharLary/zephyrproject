# CHANGELOG Index

רשימת קבוצות השינויים שנוהלו בתיקייה זו.

| Date | Group | Title | Reason (Short) | Commit |
|---|---|---|---|---|
| 2026-04-07 | infra | Make `data/` Local-Only And Align Agent Loading | `data/` יוצא מה־remote, ההוראות לסוכנים מיושרות למבנה local-only, ו-CI מדלג כשעץ ה-data המקומי חסר | pending (no commit in this task) |
| 2026-04-07 | tools | Extend Canonical Data Migration To Raw Specs And PTS Artifact Data | השלמת המיגרציה כך שגם artifacts רשמיים וגם datasets של PTS analysis חיים תחת `data/`, עם ניקוי `.gitignore`, `docs/` ו-`tmp` | pending (no commit in this task) |
| 2026-03-23 | infra | Refresh Profile Builder Seed Docs And Spec Paths | תיקון פתיח `profile-patterns.md` ויישור הפניות ה-seed לנתיבי spec החדשים תחת `data/raw/bluetooth_sig/profiles` | pending (no commit in this task) |
| 2026-03-23 | tools | Refine Group B Implementation View | הסרת section כפול בלשונית `מימוש`, אכיפת LTR לקוד, הוספת הסבר עברי צמוד, והסתרת `confidence` מה-Hub | 53ca9b9 |
| 2026-03-23 | tools | Make Group B Hub Execution-Ready | הפיכת מסכי Group B למסכי פעולה עם ניווט פנימי, copy לטסטים, לשונית `מימוש`, ו-schema/build חדשים ל-implementation | pending (no commit in this task) |
| 2026-03-23 | dashboard | Integrate `.github` metadata into Group B hub | חיבור metadata/patterns/governance מ-`.github` למסכי `סקירה`/`לוגיקה`/`מבנה`/`מצב עבודה` והוספת טבלת בדיקות + API להערות | pending (no commit in this task) |
| 2026-03-23 | infra | Codify Copilot-Style `.github` Loading | קיבוע פרוטוקול טעינה ושימוש ב-`.github/` דרך `AGENTS.md` כך שהסוכן יחקה את מודל העבודה של Copilot ברמת הפרויקט | pending (no commit in this task) |
| 2026-03-22 | dashboard | Improve task-board control visibility | חיזוק חזותי לשדות סינון/חיפוש בלוח העבודה + cache-busting לטעינת CSS עדכני לאחר build | pending (no commit in this task) |
| 2026-03-22 | dashboard | Right-Size PTS Build Documentation | קיצור README של הדשבורד והעברת פירוט מצבי ה-build למסמך ייעודי עקבי עם המימוש בפועל | pending |
| 2026-03-22 | dashboard | Make AutoPTS hub the default entry page | שינוי ברירת המחדל של השרת כך שייפתח קודם עמוד AutoPTS + Group B, עם מעבר ברור בין שני העמודים | pending |
| 2026-03-22 | tools | Align PTS build selection with runtime behavior | יישור build/plan/clean כך שבחירה ממוקדת תריץ רק את מה שנבחר ותסביר אמת על קבצים שייכתבו או ידולגו | pending |
| 2026-03-09 | tools | Modularize `build_pts_report_bundle.py` orchestration | הוספת CLI granular, cache ברמת unit, ו-write-if-changed ל-build של report/hub | pending |
| 2026-03-22 | infra | Update profile builder metadata | תיקון metadata קטן ב-profiles DB וב-frontmatter של prompt ה-Profile Builder | pending |
| 2026-03-09 | infra | Reconcile changelog after PR #9 rebase | עדכון hashes של רשומות PR #9 אחרי rebase כך שישקפו את ה-hashes הממוזגים בפועל | pending |
| 2026-03-09 | infra | Install `pdftotext` for PTS Hub CI | הוספת `poppler-utils` ל-runner כדי שה-build של דשבורד PTS לא ייכשל על חסר סביבתי | a3d955f |
| 2026-03-09 | dashboard | Fix Copilot PR Review Comments | הסר owner/reviewer enforcement, guard CSS.escape, update README assets | 61db778 |
| 2026-03-07 | infra | Fix PTS Hub CI submodule checkout | תיקון checkout של submodules כדי שבדיקות PTS Hub ירוצו על עץ קבצים מלא | pending |
| 2026-03-05 | dashboard | Remove legacy `phases_tracking` | דשבורד ישן של מעקב שלבי VPC שלא משרת את הזרימה הפעילה | af93ee6 |
| 2026-03-05 | dashboard | Add report data integrity analyzer | הוספת כלי בדיקה לאיתור חוסר עקביות בנתוני report לפני רגרסיות UI | pending |
| 2026-03-05 | infra | Enforce changelog agent instructions | החלת מדיניות מחייבת לתיעוד כל שינוי דרך `AGENTS.md` ו-`copilot-instructions` | pending |
| 2026-03-06 | dashboard | Implement ARCHITECTURE_REVIEW_HE.md — All Three Stages | יישום כל הפריטים מסקירת הארכיטקטורה: מודולריזציה, ולידציה, נגישות, design tokens, smoke tests | 00004a6 |
| 2026-03-07 | dashboard | Close PR #9 review gaps | סגירת פערי smoke, a11y ו-evidence שנשארו אחרי היישום הראשי | 562a929 |
