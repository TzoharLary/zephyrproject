# 📚 מדריך לתיקיית `docs`

התיקייה מכילה תיעוד כתוב בלבד.  
דשבורדים ויזואליים (HTML) עברו אל `dashboards/`, סקריפטים לייצור נתונים עברו אל `tools/`.

## מבנה התיקייה

```text
docs/
├── README.md
├── CHANGELOG.md
├── plans/
│   ├── README.md
│   └── ble_pts_plan.md
├── profiles/              ← פרופילי Bluetooth (BAS, DIS, HID, HRS) – PDF + TCRL
└── reports/
    ├── README.md
    ├── TS_DATA_EXTRACTION_GUIDE.md
    ├── templates/         ← תבניות HTML לסקריפטים (tools/)
    ├── build-and-flash/
    ├── test-automation/
    ├── bluetooth/
    └── simulation/
```

> **דשבורדים HTML** נמצאים כעת ב-[`../dashboards/`](../dashboards/):
> - [`../dashboards/phases_tracking/index.html`](../dashboards/phases_tracking/index.html) — מעקב שלבים
> - [`../dashboards/pts_report_he/index.html`](../dashboards/pts_report_he/index.html) — דוחות PTS בעברית
>
> **סקריפטי ייצור** נמצאים כעת ב-[`../tools/`](../tools/):
> - `build_pts_report_bundle.py` — יוצר דוח PTS HTML
> - `build_pts_dis_bas_hrs_hid_report.py` — דוח DIS/BAS/HRS/HID
> - `export_runtime_active_tcids.py` — מייצא TCIDs פעילים

## ניווט מהיר

| מה מחפשים | קובץ / תיקייה |
|---|---|
| תוכנית VPC | [`plans/ble_pts_plan.md`](plans/ble_pts_plan.md) |
| דף המעקב הויזואלי | [`../dashboards/phases_tracking/index.html`](../dashboards/phases_tracking/index.html) |
| דוח PTS בעברית | [`../dashboards/pts_report_he/index.html`](../dashboards/pts_report_he/index.html) |
| דוחות Build/Flash | [`reports/build-and-flash/`](reports/build-and-flash/) |
| דוחות Twister/Pytest | [`reports/test-automation/`](reports/test-automation/) |
| דוחות Bluetooth | [`reports/bluetooth/`](reports/bluetooth/) |
| דוחות סימולציה | [`reports/simulation/`](reports/simulation/) |
| יומן שינויים | [`CHANGELOG.md`](CHANGELOG.md) |

## רשימת קבצים מפורטת

### `plans/`
- [`plans/ble_pts_plan.md`](plans/ble_pts_plan.md) — תוכנית העבודה הראשית להקמת VPC.

### `reports/build-and-flash/`
- [`reports/build-and-flash/blinky_build_flash_report.md`](reports/build-and-flash/blinky_build_flash_report.md) — דוח מעשי לבנייה/צריבה ראשונה.
- [`reports/build-and-flash/west_build_flash_openocd_report.md`](reports/build-and-flash/west_build_flash_openocd_report.md) — עומק על `west`, CMake ו-OpenOCD.

### `reports/test-automation/`
- [`reports/test-automation/west_twister_report.md`](reports/test-automation/west_twister_report.md) — שימוש ב-Twister והרצות בדיקות.
- [`reports/test-automation/zephyr_pytest_testing_guide.md`](reports/test-automation/zephyr_pytest_testing_guide.md) — שילוב `pytest` עם Zephyr/Twister.

### `reports/bluetooth/`
- [`reports/bluetooth/bluetooth_tester_build_changes.md`](reports/bluetooth/bluetooth_tester_build_changes.md) — שינויים שנדרשו לבניית Bluetooth tester.
- [`reports/bluetooth/edtt_test_specs_report.md`](reports/bluetooth/edtt_test_specs_report.md) — פירוט מפרטי EDTT.
- [`reports/bluetooth/physical_bluetooth_testing_report.md`](reports/bluetooth/physical_bluetooth_testing_report.md) — בדיקות BT על חומרה פיזית.
- [`reports/bluetooth/custom_physical_bt_testing_guide.md`](reports/bluetooth/custom_physical_bt_testing_guide.md) — בניית בדיקות BT מותאמות אישית.

### `reports/simulation/`
- [`reports/simulation/bsim_test_locations.md`](reports/simulation/bsim_test_locations.md) — מפת מיקומי בדיקות BabbleSim.

## מסלול קריאה לפי תפקיד

### מתחיל חדש (30–60 דקות)
1. [`reports/build-and-flash/blinky_build_flash_report.md`](reports/build-and-flash/blinky_build_flash_report.md)
2. [`reports/build-and-flash/west_build_flash_openocd_report.md`](reports/build-and-flash/west_build_flash_openocd_report.md)
3. [`reports/test-automation/west_twister_report.md`](reports/test-automation/west_twister_report.md)

### מפתח בדיקות / אוטומציה
1. [`reports/test-automation/west_twister_report.md`](reports/test-automation/west_twister_report.md)
2. [`reports/test-automation/zephyr_pytest_testing_guide.md`](reports/test-automation/zephyr_pytest_testing_guide.md)
3. [`plans/ble_pts_plan.md`](plans/ble_pts_plan.md)
4. [`../dashboards/phases_tracking/index.html`](../dashboards/phases_tracking/index.html)

### מפתח Bluetooth
1. [`reports/bluetooth/physical_bluetooth_testing_report.md`](reports/bluetooth/physical_bluetooth_testing_report.md)
2. [`reports/bluetooth/edtt_test_specs_report.md`](reports/bluetooth/edtt_test_specs_report.md)
3. [`reports/bluetooth/bluetooth_tester_build_changes.md`](reports/bluetooth/bluetooth_tester_build_changes.md)
4. [`reports/bluetooth/custom_physical_bt_testing_guide.md`](reports/bluetooth/custom_physical_bt_testing_guide.md)

## עזרה מהירה

- בעיית Build/Flash → [`reports/build-and-flash/west_build_flash_openocd_report.md`](reports/build-and-flash/west_build_flash_openocd_report.md)
- צריבה ראשונה לא עובדת → [`reports/build-and-flash/blinky_build_flash_report.md`](reports/build-and-flash/blinky_build_flash_report.md)
- בעיית Twister → [`reports/test-automation/west_twister_report.md`](reports/test-automation/west_twister_report.md)
- בעיית Pytest → [`reports/test-automation/zephyr_pytest_testing_guide.md`](reports/test-automation/zephyr_pytest_testing_guide.md)
- בדיקות Bluetooth פיזיות → [`reports/bluetooth/physical_bluetooth_testing_report.md`](reports/bluetooth/physical_bluetooth_testing_report.md)
- מיפוי בדיקות סימולציה → [`reports/simulation/bsim_test_locations.md`](reports/simulation/bsim_test_locations.md)

## כללי סדר להמשך

- דוחות כתובים (markdown) נכנסים תחת `reports/<category>/`.
- תוכניות עבודה נכנסות תחת `plans/`.
- נכסי UI (HTML/CSS/JS) נכנסים תחת `../dashboards/<name>/`.
- סקריפטי Python לייצור נתונים נכנסים תחת `../tools/`.
- כל הוספת קובץ מחייבת עדכון `docs/README.md`.

---

עדכון אחרון: פברואר 2026
