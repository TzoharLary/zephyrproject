# 📚 מדריך לתיקיית `docs`

התיקייה אורגנה לפי תחומים כדי להקל ניווט.  
**לא נמחקו דוחות תוכן** — הקבצים עברו לתת־תיקיות מסודרות.

## מבנה התיקייה

```text
docs/
├── README.md
├── CHANGELOG.md
├── plans/
│   ├── README.md
│   └── ble_pts_plan.md
├── phases_tracking/
│   ├── index.html
│   ├── css/
│   └── js/
└── reports/
    ├── README.md
    ├── build-and-flash/
    ├── test-automation/
    ├── bluetooth/
    └── simulation/
```

## ניווט מהיר

| מה מחפשים | קובץ / תיקייה |
|---|---|
| תוכנית VPC | [`plans/ble_pts_plan.md`](plans/ble_pts_plan.md) |
| דף המעקב הויזואלי | [`phases_tracking/index.html`](phases_tracking/index.html) |
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
4. [`phases_tracking/index.html`](phases_tracking/index.html)

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

- דוחות חדשים נכנסים תחת `reports/<category>/`.
- תוכניות עבודה נכנסות תחת `plans/`.
- נכסי UI (HTML/CSS/JS) נשארים תחת `phases_tracking/`.
- כל הוספת קובץ חדש מחייבת עדכון `docs/README.md`.

---

עדכון אחרון: פברואר 2026
