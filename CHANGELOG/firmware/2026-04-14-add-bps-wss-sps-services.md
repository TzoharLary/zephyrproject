# Add BPS/WSS/SPS GATT Services

- Date: 2026-04-14
- Group: firmware
- Status: in-progress

## Context
נדרש לממש שלושה פרופילי BLE חדשים בסגנון Zephyr-native (`BPS`, `WSS`, `SPS/SCPS`) כולל שילוב מלא ב־Kconfig/CMake, תיעוד עבודה מתמשך, והכנת חבילת העברה למהנדסים אחרים.

## Changes
- נוספו שירותים חדשים:
  - `subsys/bluetooth/services/bps.c`
  - `subsys/bluetooth/services/wss.c`
  - `subsys/bluetooth/services/sps.c`
- נוספו headers ציבוריים:
  - `include/zephyr/bluetooth/services/bps.h`
  - `include/zephyr/bluetooth/services/wss.h`
  - `include/zephyr/bluetooth/services/sps.h`
  - `include/zephyr/bluetooth/services/scps.h` (alias compatibility)
- נוספו קבצי Kconfig ייעודיים:
  - `subsys/bluetooth/services/Kconfig.bps`
  - `subsys/bluetooth/services/Kconfig.wss`
  - `subsys/bluetooth/services/Kconfig.sps`
- עודכנו קבצי אינטגרציה:
  - `subsys/bluetooth/services/Kconfig`
  - `subsys/bluetooth/services/CMakeLists.txt`
  - `subsys/bluetooth/Kconfig.logging`
- נוצר README להעברה:
  - `README-bps-wss-sps-transfer.md`
- נוצר ועודכן worklog מתמשך:
  - `../docs/plans/2026-04-14-bps-wss-sps-implementation-worklog.md`

## Why
כדי לאפשר הרחבת פרופילי BLE בפרויקט בצורה עקבית עם Zephyr, לקבע מיפוי ברור בין `SPS` ל־`SCPS`, ולאפשר handoff מסודר בין סשנים/מהנדסים בלי לאבד הקשר ארכיטקטוני או אינטגרטיבי.

## Impact
- Users: שירותי BLE חדשים זמינים לבנייה ושילוב, כולל תאימות שם עבור `SCPS`.
- Devs: יש API ציבורי, Kconfig, CMake ולוגינג משולבים; יש README העברה ו-worklog מפורט להפחתת friction בהמשך פיתוח.

## References
- Commit: b9292c8
- Files:
  - zephyr/include/zephyr/bluetooth/services/bps.h
  - zephyr/include/zephyr/bluetooth/services/wss.h
  - zephyr/include/zephyr/bluetooth/services/sps.h
  - zephyr/include/zephyr/bluetooth/services/scps.h
  - zephyr/subsys/bluetooth/services/bps.c
  - zephyr/subsys/bluetooth/services/wss.c
  - zephyr/subsys/bluetooth/services/sps.c
  - zephyr/subsys/bluetooth/services/Kconfig.bps
  - zephyr/subsys/bluetooth/services/Kconfig.wss
  - zephyr/subsys/bluetooth/services/Kconfig.sps
  - zephyr/subsys/bluetooth/services/Kconfig
  - zephyr/subsys/bluetooth/services/CMakeLists.txt
  - zephyr/subsys/bluetooth/Kconfig.logging
  - zephyr/README-bps-wss-sps-transfer.md
  - docs/plans/2026-04-14-bps-wss-sps-implementation-worklog.md

## Notes
קבוצות משניות: `docs` (worklog), `infra` (אין שינוי תשתית ראשי במשימה זו; הרשומה הראשית נשארת `firmware` לפי מיפוי הנתיבים).
