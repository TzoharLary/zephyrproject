# Add BPS/WSS/SPS Transfer Bundle

- Date: 2026-04-14
- Group: infra
- Status: done

## Context
המימושים ל-`BPS`/`WSS`/`SPS` יושבים בפועל תחת `zephyr/`, אבל אי אפשר להסתמך על commit/push ל-submodule הזה. לכן נדרש bundle ברמת הריפו הראשי שמכיל עותקים מדויקים של הקבצים והסבר ברור לאן כל קובץ אמור להיכנס אצל משתמש אחר.

## Changes
- נוספה תיקיית bundle חדשה בשורש הריפו: `bps-wss-sps-zephyr-bundle/`.
- הועתקו אליה עותקים מדויקים של קבצי המימוש, ה-headers וקבצי האינטגרציה מתוך `zephyr/`.
- הועתקו אליה גם מסמכי ההסבר הרלוונטיים:
  - `zephyr/README-bps-wss-sps-transfer.md`
  - `docs/plans/2026-04-14-bps-wss-sps-implementation-worklog.md`
- נוסף `bps-wss-sps-zephyr-bundle/README.md` עם מיפוי מפורש בין המיקום החדש של כל קובץ לבין היעד שלו תחת `zephyr/` בפרויקט אחר.
- `bps-wss-sps-zephyr-bundle/README.md` תורגם לעברית ונוסף בו בלוק prompt מוכן להדבקה לסוכן אחר לצורך העתקה ומיזוג של המימושים.

## Why
כדי לאפשר handoff ו-commit בריפו הראשי בלי להזיז או למחוק את הקבצים המקוריים, ובו בזמן לתת למשתמש חדש חבילה אחת ברורה עם מבנה העתקה חד-משמעי.

## Impact
- Users: יש עכשיו חבילת העברה אחת בשורש הפרויקט שאפשר למסור לאחרים בלי להיכנס ל-submodule.
- Devs: אפשר לעקוב אחרי המימושים ולשנע אותם לפרויקט Zephyr אחר תוך שמירה על מיפוי נתיבים מדויק, הנחיות בעברית, והבדלה בין full copy ל-manual merge.

## References
- Commit: b9292c8
- Files:
  - bps-wss-sps-zephyr-bundle/README.md
  - bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/bps.h
  - bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/wss.h
  - bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/sps.h
  - bps-wss-sps-zephyr-bundle/zephyr/include/zephyr/bluetooth/services/scps.h
  - bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/bps.c
  - bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/wss.c
  - bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/sps.c
  - bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig.bps
  - bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig.wss
  - bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig.sps
  - bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/Kconfig
  - bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/services/CMakeLists.txt
  - bps-wss-sps-zephyr-bundle/zephyr/subsys/bluetooth/Kconfig.logging
  - bps-wss-sps-zephyr-bundle/zephyr/README-bps-wss-sps-transfer.md
  - bps-wss-sps-zephyr-bundle/docs/plans/2026-04-14-bps-wss-sps-implementation-worklog.md

## Notes
הקבצים המקוריים תחת `zephyr/` לא שונו ולא הוסרו כחלק מהמשימה הזאת; ה-bundle הוא שכבת העתקה והסבר בלבד.
