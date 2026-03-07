# Fix PTS Hub CI Submodule Checkout

- Date: 2026-03-07
- Group: infra
- Status: done

## Context
בדיקת `PTS Hub Checks` נפלה ב-GitHub Actions בזמן `python tools/check_group_b_hub.py` כי ה-runner לא משך את submodule `auto-pts`, אף שהבדיקה תלויה בקבצים מתוכו.

## Changes
- עודכן `.github/workflows/pts-hub-check.yml` כך ש-`actions/checkout` ימשוך submodules בצורה רקורסיבית.
- נוספה רשומת changelog שמתעדת את תיקון תצורת ה-CI ואת סיבת הכשל.

## Why
כדי שה-CI יריץ את אותן בדיקות על עץ קבצים מלא, ולא ייכשל על `FileNotFoundError` שנובע מסביבת checkout חלקית.

## Impact
- Users: אין שינוי ישיר במוצר.
- Devs: `PTS Hub Checks` ב-GitHub Actions משקף טוב יותר את מצב הריפו בפועל ולא נופל בגלל חוסר ב-submodule.

## References
- Commit: `pending (no commit in this task)`
- Files:
  - `.github/workflows/pts-hub-check.yml`
  - `CHANGELOG/infra/2026-03-07-fix-pts-hub-ci-submodule-checkout.md`
  - `CHANGELOG/INDEX.md`

## Notes
האבחון הראה שהכשל המקורי היה תצורתי: ה-submodule commit שהריפו מצמיד כן מכיל את `auto-pts/autopts/ptsprojects/zephyr/__init__.py`.
