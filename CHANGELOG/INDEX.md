# CHANGELOG Index

רשימת קבוצות השינויים שנוהלו בתיקייה זו.

| Date | Group | Title | Reason (Short) | Commit |
|---|---|---|---|---|
| 2026-03-09 | infra | Install `pdftotext` for PTS Hub CI | הוספת `poppler-utils` ל-runner כדי שה-build של דשבורד PTS לא ייכשל על חסר סביבתי | a3d955f |
| 2026-03-07 | infra | Fix PTS Hub CI submodule checkout | תיקון checkout של submodules כדי שבדיקות PTS Hub ירוצו על עץ קבצים מלא | pending |
| 2026-03-05 | dashboard | Remove legacy `phases_tracking` | דשבורד ישן של מעקב שלבי VPC שלא משרת את הזרימה הפעילה | af93ee6 |
| 2026-03-05 | dashboard | Add report data integrity analyzer | הוספת כלי בדיקה לאיתור חוסר עקביות בנתוני report לפני רגרסיות UI | pending |
| 2026-03-05 | infra | Enforce changelog agent instructions | החלת מדיניות מחייבת לתיעוד כל שינוי דרך `AGENTS.md` ו-`copilot-instructions` | pending |
| 2026-03-06 | dashboard | Implement ARCHITECTURE_REVIEW_HE.md — All Three Stages | יישום כל הפריטים מסקירת הארכיטקטורה: מודולריזציה, ולידציה, נגישות, design tokens, smoke tests | a2bcee4 |
