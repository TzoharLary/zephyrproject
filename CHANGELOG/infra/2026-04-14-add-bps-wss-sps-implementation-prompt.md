# Add BPS/WSS/SPS Implementation Prompt

- Date: 2026-04-14
- Group: infra
- Status: done

## Context
נדרש לייצר prompt ייעודי ומוכן לשימוש עבור סשן Copilot אחר, שיכוון מימוש של שלושת הפרופילים הפעילים (BPS, WSS, SPS/SCPS) עם כללי reconciliation, תיעוד ביניים, ותוצר handoff ברור למהנדס נוסף.

## Changes
- נוצר קובץ prompt חדש: `.github/prompts/zephyr-bps-wss-sps-implementation.prompt.md`.
- הוגדרה ב-prompt זרימת עבודה מלאה: source reconciliation, סיווג פרופיל-לפי-פרופיל, בחירת reference מותאמת לכל פרופיל, מימוש Zephyr-native, worklog מתמשך, וולידציה.
- נוספה דרישה מפורשת ליצירת `zephyr/README-bps-wss-sps-transfer.md` עם הוראות העברה מפורטות, כולל מטריצת artifacts וצעדי copy/merge.
- עודכן אינדקס changelog.

## Why
כדי להפוך את הרצת הסוכן בסשן נפרד לדטרמיניסטית ועקבית, לצמצם סיכון לבלבול בין `SPS` ל-`SCPS`, ולהבטיח שתוצרי המימוש יהיו ניתנים להעברה לצוות/מהנדס אחר בצורה ברורה.

## Impact
- Users: אפשר להפעיל סוכן אחר עם prompt קבוע ומדויק, בלי לנסח מחדש הנחיות מורכבות בכל פעם.
- Devs: יש source-of-truth ברור תחת `.github/prompts/`, כולל דרישות תיעוד והעברה שמפחיתות איבוד הקשר בין סשנים.

## References
- Commit: b9292c8
- Files:
  - .github/prompts/zephyr-bps-wss-sps-implementation.prompt.md
  - CHANGELOG/infra/2026-04-14-add-bps-wss-sps-implementation-prompt.md
  - CHANGELOG/INDEX.md

## Notes
ה-prompt החדש מניח נתיבים יחסיים תחת `zephyr/` כדי לשמור על ניידות בין סביבות פיתוח שונות.
