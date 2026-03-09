# Install `pdftotext` For PTS Hub CI

- Date: 2026-03-09
- Group: infra
- Status: done

## Context
בדיקת `PTS Hub Checks` נפלה ב-GitHub Actions בשלב `Build dashboard + hub bundles` כי ה-runner לא כלל את `pdftotext`, אף שה-build script תלוי בו כדי לחלץ טקסט ממסמכי PDF.

## Changes
- עודכן `.github/workflows/pts-hub-check.yml` כך שה-runner מתקין `poppler-utils` לפני שלב ה-build.
- נוסף verify קצר באמצעות `pdftotext -v` כדי להכשיל מוקדם אם התלות לא זמינה.
- נוספה רשומת changelog לתיעוד תיקון ה-CI והסיבה לו.

## Why
כדי להפוך את סביבת ה-CI למפורשת ותואמת לתלויות האמיתיות של `tools/build_pts_report_bundle.py`, במקום להסתמך על קיומו המקרי של `pdftotext`.

## Impact
- Users: אין שינוי ישיר במוצר.
- Devs: בדיקת `PTS Hub Checks` יכולה להריץ את build ה-dashboard בצורה עקבית ב-GitHub Actions במקום להיכשל על חסר סביבתי.

## References
- Commit: `a3d955f`
- Files:
  - `.github/workflows/pts-hub-check.yml`
  - `CHANGELOG/infra/2026-03-09-install-pdftotext-for-pts-hub-ci.md`
  - `CHANGELOG/INDEX.md`

## Notes
התיקון הזה פותר רק את חסר ה-dependency ב-CI. הוא לא משנה עדיין את מודל ה-full rebuild של הבדיקות.
