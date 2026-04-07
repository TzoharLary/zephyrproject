# Make `data/` Local-Only And Align Agent Loading

- Date: 2026-04-07
- Group: infra
- Status: done

## Context
לאחר מיגרציית ה-data לפריסת `data/raw|catalog|curated|derived`, התברר שהעץ החדש אמור לשרת רק משתמשים וסוכנים על המחשב המקומי ולא להיות חלק מהריפו המרוחק. במקביל, שכבת ההוראות וה-CI עדיין תיארה את `data/` כאילו הוא נשמר ב-Git.

## Changes
- הוגדר `data/` כ-local-only ב-`.gitignore` והוצא מה-git index כך שהקבצים נשארים מקומית אך לא נכללים יותר בריפו המרוחק.
- עודכנו `AGENTS.md` ו-`.github/copilot-instructions.md` כך שסוכנים יעדיפו את `data/` המקומי כשקיים, וייפלו חזרה ל-`.github/data/*` ולקבצים tracked כשהוא חסר.
- נוספה הערת הקשר היסטורית ל-`.github/docs/system-journal.md`.
- עודכן workflow של `PTS Hub Checks` כך שידלג על validation/build תלויי-`data/` כאשר עץ ה-local data אינו זמין.
- עודכנו `docs/README.md` ו-`tools/templates/pts_report_he/Group_B_data/README.md` כדי להבהיר ש-`data/` הוא עץ מקומי בלבד.

## Why
זה הפתרון הנכון כשהידע הכבד וה-local artifacts מיועדים לעבודה על מחשב מסוים בלבד, אבל עדיין צריך להשאיר ריפו נקי, seed/governance tracked, והוראות ברורות לסוכנים ול-CI.

## Impact
- Users: `data/` נשאר זמין מקומית לעבודה, אבל לא יופיע יותר כחלק ממה שנדחף לרימוט.
- Devs: סקריפטים והוראות מבחינים עכשיו בין local data לבין tracked seed/governance; CI מדלג בצורה מפורשת כש-local data חסר.

## References
- Commit: pending (no commit in this task)
- Files:
  - .gitignore
  - AGENTS.md
  - .github/copilot-instructions.md
  - .github/docs/system-journal.md
  - .github/workflows/pts-hub-check.yml
  - docs/README.md
  - tools/templates/pts_report_he/Group_B_data/README.md

## Notes
קבוצות משניות: `docs`, `tools`.
