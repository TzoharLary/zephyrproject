# Align Copilot Ecosystem Data Path References

- Date: 2026-04-14
- Group: infra
- Status: done

## Context
אחרי שינויי המיגרציה של `data/` ל-local-only, נשארו כמה הפניות legacy בשכבת ה-Copilot ecosystem שיצרו פער בין ההנחיות הפעילות לבין הנתיבים ההיסטוריים.

## Changes
- הוסרו מה-workflow `pts-hub-check.yml` הפניות trigger ישנות ל-`tools/data/group_b_*.json`, שלא רלוונטיות יותר למבנה הנוכחי.
- עודכנה ב-`.github/data/profiles-db.yaml` הערת header שהזכירה `tools/data/`, כך שתשקף רק את הנתיב הקנוני הנוכחי תחת `data/raw/...`.
- עודכן ב-`.github/docs/system-journal.md` תיאור היסטורי של `docs/profiles/BPS/` כך שיובהר שהוא historical, ובמקביל עודכנה דוגמת `spec_doc` לנתיב העדכני `data/raw/bluetooth_sig/profiles/<PROFILE>/...`.

## Why
כדי להבטיח עקביות בין ההוראות, ה-governance וה-CI, ולמנוע בלבול בין נתיבי עבר לבין נתיבים פעילים במצב הפרויקט הנוכחי.

## Impact
- Users: פחות סיכון לקבלת הנחיות עם נתיבי legacy שלא קיימים כיום בזרימת העבודה הפעילה.
- Devs: מסמכי ה-ecosystem ו-workflow מיושרים טוב יותר למודל `data/` local-only ולנתיבי ה-seed/governance העדכניים.

## References
- Commit: pending (no commit in this task)
- Files:
  - .github/workflows/pts-hub-check.yml
  - .github/data/profiles-db.yaml
  - .github/docs/system-journal.md
  - CHANGELOG/infra/2026-04-14-align-copilot-ecosystem-data-path-references.md
  - CHANGELOG/INDEX.md

## Notes
העדכון שומר על תוכן היסטורי נחוץ בתוך `system-journal.md`, אך מבהיר במפורש מה historical ומה הנתיב התקף כיום.
