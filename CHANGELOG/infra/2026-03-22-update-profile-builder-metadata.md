# Update Profile Builder Metadata

- Date: 2026-03-22
- Group: infra
- Status: done

## Context
שני קבצי metadata של מערכת ה-Profile Builder עודכנו מקומית: תיקון טקסטואלי קטן ב-`profiles-db.yaml`, והתאמת frontmatter בקובץ ה-prompt כך שישקף את המצב הרצוי של הגדרת ה-agent.

## Changes
- תוקן מחרוזת `notes` חסרה ב-`.github/data/profiles-db.yaml`.
- עודכן frontmatter ב-`.github/prompts/zephyr-bt-profile-builder.prompt.md`.

## Why
כדי שה-metadata של מערכת ה-Profile Builder יהיה תקין, עקבי, ולא יכיל שגיאת טקסט או frontmatter מיושן.

## Impact
- Users: אין שינוי ישיר במוצר.
- Devs: metadata תקין יותר עבור קבצי הידע/הגדרה של מערכת ה-Profile Builder.

## References
- Commit: pending (no commit in this task)
- Files:
  - `.github/data/profiles-db.yaml`
  - `.github/prompts/zephyr-bt-profile-builder.prompt.md`
  - `CHANGELOG/infra/2026-03-22-update-profile-builder-metadata.md`
  - `CHANGELOG/INDEX.md`
