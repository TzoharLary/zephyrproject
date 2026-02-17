# 🚀 פרויקט Zephyr עם TI CC2745R10-Q1

ברוכים הבאים! זהו סביבת פיתוח מלאה של **Zephyr RTOS** עם תמיכה בלוח **TI LP-EM-CC2745R10-Q1**, כולל כלי בדיקות Bluetooth, סימולציה BabbleSim, וכלים להנדסה מוטמעת.

> **מבנה הריפו:** פרויקט זה מנוהל כ-Git Repository ראשי המכיל שני **Git Submodules**:
> - `zephyr/` — [TexasInstruments/simplelink-zephyr](https://github.com/TexasInstruments/simplelink-zephyr) (ענף: `v3.7.0-ti-9.14`)
> - `auto-pts/` — [intel/auto-pts](https://github.com/intel/auto-pts) (ענף: `master`)
>
> שאר התיקיות (`modules/`, `bootloader/` וכו') מנוהלות על ידי **West** ואינן חלק מה-Git של פרויקט זה.

---

## 📑 תוכן עניינים מהיר

| קטגוריה | לקורא... |
|---------|----------|
| 🚀 **דוגמת הפעלת סביבה + build + flash** | → ראה [🎯 דוגמא מהירה](#-דוגמא-מהירה) |
| 📁 **מפת תיקיות** | → ראה [📊 מבנה מלא](#-מבנה-הפרויקט-מלא) |
| 🔨 **בנייה וצריבה** | → ראה [🛠️ בנייה וצריבה](#-בנייה-וצריבה) |
| 🧪 **בדיקות** | → ראה [🧪 בדיקות ובדיקה](#-בדיקות-ובדיקה-qa) |
| 📚 **תיעוד מפורט** | → ראה תיקיית [`docs/`](docs/README.md) |
| ❓ **שאלות נפוצות?** | → ראה [📞 שאלות נפוצות](#-שאלות-נפוצות) |

---

## 🎯 דוגמא מהירה

```bash
# 1. הפעלת Python environment
source .venv/bin/activate

# 2. בנייה של דוגמה ראשונה (blinky - להבהיב LED)
west build -b lp_em_cc2745r10_q1/cc2745r10_q1 samples/basic/blinky -p always

# 3. צריבה ללוח (דורש חיבור)
west flash

# ✅ סיים! ה-LED של הלוח אמור לההבהב עכשיו
```

> **בעיה?** עבור לסעיף [🆘 פתרון בעיות](#-פתרון-בעיות-נפוצות)

---

## 📊 סקירה כללית של הפרויקט

```
Zephyr RTOS (ליבה)
    ├─ 🎯 מטרה: RTOS קלה לחומרה מוקדשת (embedded)
    ├─ 🏆 חוזקות: קוד פתוח, תמיכה 300+ לוחות, מובנה Bluetooth
    └─ 📍 בפרויקט שלנו: מותאמת עבור TI CC2745R10-Q1

BabbleSim (סימולציה)
    ├─ 🎯 מטרה: סימולציה של טופולוגיות Bluetooth מורכבות
    ├─ ✅ יתרון: בדיקות ללא חומרה פיזית
    └─ 📍 בפרויקט שלנו: בדיקות HOST, Crypto, Controller

AutoPTS (בדיקות Compliance)
    ├─ 🎯 מטרה: בדיקות עם PTS (Profile Tuning Suite)
    ├─ ✅ יתרון: עמידה בסטנדרטים Bluetooth רשמיים
    └─ 📍 בפרויקט שלנו: בדיקות אוטומטיות של Bluetooth

OpenOCD (צריבה וניקוד)
    ├─ 🎯 מטרה: צריבה וניקוד של חומרה
    ├─ ✅ יתרון: תומך 100+ מעבדים ודיבאגים
    └─ 📍 בפרויקט שלנו: צריבה מהירה של קוד ללוח
```

---

## 📁 מבנה הפרויקט (מלא)

### 📂 מבנה מלא (עם הסברים)

```
/Users/tzoharlary/zephyrproject/   ← ריפו Git ראשי
│
├─── 🎯 START HERE ────────────────────────────────────────
│    ├── README.md                  ← אתה כאן!
│    ├── docs/                      ← תיעוד מלא
│    ├── west_boards.txt            ← רשימת לוחות West
│    └── workspace_projects.txt    ← פרויקטים פעילים
│
├─── 📚 DOCUMENTATION ─────────────────────────────────────
│    └── docs/
│        ├── README.md              📍 מדריך לתיקייה
│        ├── CHANGELOG.md           📋 יומן שינויים
│        ├── plans/                 🗺️ תוכניות עבודה
│        ├── phases_tracking/       🎛️ דשבורד מעקב (HTML)
│        ├── Profiles/              📄 פרופילי Bluetooth (BAS, DIS, HID, HRS)
│        ├── pts_report_he/         📊 דוחות PTS בעברית (HTML)
│        └── reports/               📑 דוחות לפי תחום
│            ├── bluetooth/
│            ├── build-and-flash/
│            ├── simulation/
│            ├── test-automation/
│            └── templates/
│
├─── 🔧 ZEPHYR CORE — Git Submodule ────────────────────────
│    └── zephyr/                    🏆 TexasInstruments/simplelink-zephyr
│        ├── boards/ti/             🎛️ תצורות לוחות TI
│        ├── tests/                 ✅ בדיקות
│        ├── samples/               💡 דוגמאות
│        └── west.yml               📋 West Manifest
│
├─── 🤖 BLUETOOTH TESTING ──────────────────────────────────
│    ├── auto-pts/                  🧪 Git Submodule — intel/auto-pts
│    │   ├── autoptsclient_bot.py   🤖 Bot אוטומטי
│    │   ├── autoptsserver.py       🖥️ שרת PTS
│    │   └── autopts/              💻 קוד ראשי
│    │
│    └── phys_bt_test/             📱 בדיקות Bluetooth פיזיות (קוד שלנו)
│        ├── runner.py
│        ├── config.yaml
│        ├── functional_tests/
│        └── utils/
│
├─── 🔌 MODULES & TOOLS (West-managed, לא ב-Git) ──────────
│    ├── modules/                   📚 West modules חיצוניים (HAL, Crypto...)
│    ├── bootloader/mcuboot/        🔐 MCUBoot
│    └── tools/edtt, tools/net-tools/  🧪 כלי בדיקות חיצוניים
│
├─── 🛠️ LOCAL TOOLS ─────────────────────────────────────────
│    ├── ti-openocd/                🛠️ OpenOCD של TI (צריבה + ניקוד)
│    └── tools/twister_report.py    📊 יוצר דוחות Twister
│
└─── ⚙️ CONFIGURATION ──────────────────────────────────────
     ├── .west/                     📋 הגדרות West (לא ב-Git)
     ├── .env                       🔑 משתנים סביבה (לא ב-Git)
     └── .venv/                     🐍 Python Virtual Environment (לא ב-Git)
```

---

## 🎯 תא הקטיגוריות (בחר את שלך)

### 🛠️ בנייה וצריבה

**מתחילים עם בנייה ראשונה?**
```bash
# 1️⃣ הפעלת Environment
source .venv/bin/activate

# 2️⃣ בנייה של blinky (דוגמה פשוטה)
west build -b lp_em_cc2745r10_q1/cc2745r10_q1 samples/basic/blinky -p always

# 3️⃣ צריבה ללוח
west flash

# ✅ כל סיימת! הלוח אמור להבהיב עכשיו
```

**פקודות בנייה שימושיות:**
| פקודה | מה זה עושה |
|-------|----------|
| `west build -b <board> <path>` | בנייה לבורדה מסוימת |
| `west build -p always` | ניקוי מלא לפני בנייה |
| `west build --pristine=always` | ניקוי עמוק מלא |
| `west flash` | צריבה עם OpenOCD |
| `west flash --recovery` | צריבה בגזירה אם תקוע |
| `west debug` | הפעלת GDB debugger |

📖 **למידע מלא:** ראה [`docs/reports/build-and-flash/blinky_build_flash_report.md`](docs/reports/build-and-flash/blinky_build_flash_report.md) ו-[`docs/reports/build-and-flash/west_build_flash_openocd_report.md`](docs/reports/build-and-flash/west_build_flash_openocd_report.md)

---

### 🧪 בדיקות ובדיקה (QA)

**הרצת בדיקות מהירות:**
```bash
# בדיקות לבורד מסוים
west twister -p lp_em_cc2745r10_q1/cc2745r10_q1 --build-only

# בדיקות Bluetooth בלבד
west twister -p lp_em_cc2745r10_q1/cc2745r10_q1 -s tests/bluetooth

# בדיקה מסוימת בלבד
west twister -p lp_em_cc2745r10_q1/cc2745r10_q1 -c tests/bluetooth/tester

# הרצה עם דוח מפורט
west twister -p lp_em_cc2745r10_q1/cc2745r10_q1 --build-only -v
```

**סוגי בדיקות בפרויקט:**
- 🧬 **Unit Tests** - בדיקות יחידה יחידניות
- 🔗 **Integration Tests** - בדיקות בתוך מודולים
- 🤖 **BabbleSim** - סימולציה Bluetooth (ב-Linux בלבד)
- 🎯 **AutoPTS** - בדיקות Compliance עם PTS
- 📱 **Physical Hardware** - בדיקות על לוח תקוע

📖 **למידע מלא:** ראה [`docs/reports/test-automation/west_twister_report.md`](docs/reports/test-automation/west_twister_report.md), [`docs/reports/test-automation/zephyr_pytest_testing_guide.md`](docs/reports/test-automation/zephyr_pytest_testing_guide.md)

---

### 🔵 בדיקות Bluetooth

**סוגי בדיקות Bluetooth:**

| סוג | מכשיר | מתאים ל- | דוגמה |
|-----|------|---------|--------|
| **BabbleSim** | סימולציה | בדיקות אוטומטיות מלאות | `west twister -p lp_em_cc2745r10_q1/cc2745r10_q1 -s tests/bsim` |
| **AutoPTS** | PTS Dongle + מכשיר | בדיקות Compliance רשמיות | ריצה של `autoptsclient_bot.py` |
| **Shell** | מכשירים פיזיים | בדיקות ידניות אינטראקטיביות | `west build ... & miniterm.py /dev/ttyUSB0` |
| **Custom Apps** | מכשירים פיזיים | בדיקות מותאמות אישית | בנייה של יישומון משלך |

📖 **למידע מלא:** ראה [`docs/reports/bluetooth/physical_bluetooth_testing_report.md`](docs/reports/bluetooth/physical_bluetooth_testing_report.md), [`docs/reports/bluetooth/custom_physical_bt_testing_guide.md`](docs/reports/bluetooth/custom_physical_bt_testing_guide.md)

---

### 🌐 סימולציה BabbleSim

**מה זה BabbleSim?**
- סימולטור Bluetooth שמאפשר להריץ בדיקות ללא חומרה פיזית
- פועל רק ב-**Linux** (לא ב-macOS או Windows)
- מאפשר סימולציה של טופולוגיות מורכבות

**בדיקות BabbleSim זמינות:**
```
HOST Tests:
  - Advertising (פרסום)
  - Scanning (סריקה)
  - Connection (חיבור)
  - GATT (העברת ערכים)
  - L2CAP (ערוצים)
  - Isochronous (LE Audio)

Controller Tests:
  - Link Layer
  - PHY Management
  - Crypto & Security
```

📖 **למידע מלא:** ראה [`docs/reports/simulation/bsim_test_locations.md`](docs/reports/simulation/bsim_test_locations.md)

---

## 🔨 פקודות חיוניות

### West
```bash
# בנייה
west build -b <board> <app-path> [-p always]

# צריבה
west flash

# ניקוד
west debug

# הרצת בדיקות
west twister -p <board> [filters...]

# הצגת לוחות זמינים
west boards
```

### Python Development
```bash
# הפעלת Environment
source .venv/bin/activate

# בדיקות Pytest
pytest tests/ -v

# הרצת AutoPTS
python auto-pts/autoptsclient_bot.py
```

### OpenOCD (צריבה ידנית)
```bash
# התחברות ישירה ל-OpenOCD
telnet localhost 4444

# צריבה ידנית
openocd -f ti-openocd/share/openocd/scripts/board/lp_em_cc2745r10_q1.cfg
```

---

## 📊 סטטיסטיקות הפרויקט

| מדד | ערך |
|------|-------|
| **קוד Zephyr** | ~40K+ קבצים, מעל 5 מיליון שורות |
| **לוחות מתמכים** | 300+ לוחות |
| **לוחות TI בפרויקט** | 50+ לוחות (כולל שלנו CC2745R10) |
| **אפליקציות לדוגמה** | 100+ דוגמאות |
| **בדיקות** | 1000+ בדיקות |
| **תיעוד** | 15 קבצי markdown בתיקיית `docs/` |

---

## 🌍 משאבים חיצוניים

### תיעוד רשמי
- 🔗 [Zephyr Documentation](https://docs.zephyrproject.org/) - תיעוד רשמי
- 🔗 [West Documentation](https://docs.zephyrproject.org/latest/develop/west/) - Meta-tool
- 🔗 [Twister Test Framework](https://docs.zephyrproject.org/latest/develop/test/twister.html) - בדיקות
- 🔗 [Bluetooth Stack](https://docs.zephyrproject.org/latest/connectivity/bluetooth/) - Bluetooth

### כלים וריפוזיטוריים
- 🔗 [AutoPTS Repository](https://github.com/auto-pts/auto-pts) - בדיקות PTS
- 🔗 [BabbleSim](https://github.com/BabbleSim/babble-sim) - סימולטור Bluetooth
- 🔗 [OpenOCD](http://openocd.org/) - debugger וצרייה

---

## 📖 מפת קריאה מומלצת

### 👶 למתחילים (שעה 1)
1. קרא את סעיף [🎯 דוגמא מהירה](#-דוגמא-מהירה) כאן
2. בצע את הפקודות - עד שה-LED יהבהב
3. קרא [`docs/README.md`](docs/README.md) - מדריך לתיעוד

### 🧑‍💻 למפתחים (שעות 2-4)
1. [`docs/reports/build-and-flash/blinky_build_flash_report.md`](docs/reports/build-and-flash/blinky_build_flash_report.md) - הבנה מעמיקה
2. [`docs/reports/build-and-flash/west_build_flash_openocd_report.md`](docs/reports/build-and-flash/west_build_flash_openocd_report.md) - איך עובד הבנייה
3. [`docs/reports/test-automation/west_twister_report.md`](docs/reports/test-automation/west_twister_report.md) - בדיקות אוטומטיות

### 👨‍🔬 למהנדסי בדיקות (שעות 4-8)
1. [`docs/reports/bluetooth/physical_bluetooth_testing_report.md`](docs/reports/bluetooth/physical_bluetooth_testing_report.md)
2. [`docs/reports/bluetooth/edtt_test_specs_report.md`](docs/reports/bluetooth/edtt_test_specs_report.md)
3. [`docs/reports/simulation/bsim_test_locations.md`](docs/reports/simulation/bsim_test_locations.md)

---

| בעיה | סיבה | פתרון |
|------|------|--------|
| ❌ `west not found` | Environment לא הופעל | הרץ: `source .venv/bin/activate` |
| ❌ OpenOCD לא מוצא | נתיב שגוי | בדוק: `$TI_OPENOCD_INSTALL_DIR` או `../ti-openocd` |
| ❌ Build נכשל | CMake cache זקן | הרץ: `west build -p always` |
| ❌ Flash נכשל | לוח לא מחובר | בדוק חיבור USB וחוקי udev ב-Linux |
| ❌ Twister דלג על בדיקות | לוח לא ברשימה | עדכן `testcase.yaml` ל-`platform_allow` |
| ❌ Pytest לא עובד | צריך Python >= 3.8 | בדוק: `python --version` בתוך `.venv` |

📖 **טיפולים מפורטים:** ראה את קובץ התיעוד הרלוונטי ב-`docs/`

---

## 📞 שאלות נפוצות

### 🔧 שאלות טכניות

**Q: איפה אני מוסיף יישומיה חדשה?**
```
A: שתי אפשרויות:
   1. תוך Zephyr: zephyr/samples/<category>/<app>/
   2. בחוץ: אפליקציה משלך + zephyr/ כ-module
```

**Q: מה ההבדל בין blinky ל-shell?**
```
A: 
   - blinky: דוגמה פשוטה - מהבהיב LED
   - shell: יישום עם shell אינטראקטיבי
```

**Q: איך אני מתקן בדוקים?**
```
A: תגיד לי:
   1. אי הבנת בעיה ספציפית?
   2. צריך לשנות קוד?
   3. צריך בדיקה חדשה?
   → כל אחד דורש גישה שונה
```

### 🧪 שאלות בדיקות

**Q: מה זה Twister?**
```
A: כלי בדיקות של Zephyr ש:
   - סורק אפליקציות בדיקה
   - בונה אותן לכמה לוחות
   - מריץ אותן (בLinux בלבד)
   - יוצר דוחות
```

**Q: מה זה BabbleSim?**
```
A: סימולטור Bluetooth ש:
   - מתחזה ל-300+ Bluetooth תקנים
   - עובד רק ב-Linux
   - משמש לבדיקות אוטומטיות ללא חומרה
```

**Q: איך אני בודק Bluetooth?**
```
A: 3 דרכים:
   1. BabbleSim (סימולציה, Linux בלבד)
   2. AutoPTS (Compliance, Windows, PTS Dongle)
   3. Shell/Custom (חומרה פיזית)
```

### 📊 שאלות קריאה

**Q: איפה אני מוצא בדיקה מסוימת?**
```
A: 
   - בדיקות HOST: zephyr/tests/bsim/bluetooth/host/
   - בדיקות Controller: zephyr/tests/bsim/bluetooth/controller/
   - בדיקות יחידה: zephyr/tests/
   - AutoPTS: auto-pts/autopts/
```

**Q: איך אני קורא דוח בדיקות?**
```
A: תוצאות ב-twister-out/:
   - testplan.json: תוכנית הבדיקה
   - twister_report.html: דוח יפה
   - twister.json: פרטים מלאים
```

### 🤔 שאלות כלליות

**Q: זה פרויקט קטן או גדול?**
```
A: גדול מאד:
   - 300+ לוחות
   - 1000+ בדיקות
   - 5+ מיליון שורות קוד
   - → אבל תחזיק עם קטעים קטנים בכל פעם
```

**Q: איפה אני מתחיל?**
```
A: תלוי במה אתה עושה:
   - משימה כללית → קרא התחלה מהירה
   - בדיקות → ראה בדיקות ובדיקה
   - בנייה → ראה בנייה וצריבה
```

---

## 📚 פרטים קלינים למתקדמים

### Board Configuration
```cmake
# board.cmake מכיל:
# - OpenOCD parameters
# - Flashing rules
# - Debug configuration
# מיקום: zephyr/boards/ti/lp_em_cc2745r10_q1/board.cmake
```

### West Manifest
```yaml
# west.yml מגדיר:
# - Dependencies
# - Module locations
# - Remotes
# מיקום: .west/config
```

### Custom Application
```bash
# YML testcase example:
tests:
  bluetooth.tester:
    harness: bluetooth
    platform_allow: lp_em_cc2745r10_q1/cc2745r10_q1
    build_only: true
```

---

## 🎓 הבנת Zephyr - 5 מושגים חיוניים

| מושג | הסבר | דוגמה |
|------|------|--------|
| **Board** | תצורה לחומרה ספציפית | `lp_em_cc2745r10_q1` |
| **Sample** | יישומון לדוגמה | `samples/basic/blinky` |
| **Test** | בדיקה אוטומטית | `tests/bluetooth/tester` |
| **Module** | ספרייה חיצונית | `modules/bsim_hw_models` |
| **Device Tree** | תיאור חומרה | `boards/arm/board.dts` |

---

## 🎯 הסבר קצר על תיקיות עיקריות

| תיקייה | תוכן | דרוש ל- |
|-------|------|---------|
| **`docs/`** | 15 קבצי markdown + דשבורדים HTML | הבנת כל הsystem |
| **`zephyr/`** | Git Submodule — קוד RTOS (5M+ שורות) | בנייה וטעינה |
| **`auto-pts/`** | Git Submodule — כלי בדיקות AutoPTS | בדיקות compliance |
| **`phys_bt_test/`** | בדיקות Bluetooth פיזיות (קוד שלנו) | בדיקות מותאמות |
| **`modules/`** | West modules חיצוניים — **לא ב-Git** | (מנוהל ע"י West) |
| **`ti-openocd/`** | כלי צריבה וניקוד של TI | צריבה פיזית |
| **`tools/`** | כלים: `twister_report.py` + West tools | דוחות ובדיקות |
| **`build/`, `twister-out/`** | נוצרים locally בלבד — **אינם ב-Git** | (generated) |

---

## 🎁 בונוס: Cheat Sheet מהיריות 

```bash
# Build
west build -b lp_em_cc2745r10_q1/cc2745r10_q1 samples/basic/blinky -p always

# Flash
west flash

# Debug
west debug

# Test all
west twister -p lp_em_cc2745r10_q1/cc2745r10_q1 --build-only

# Test Bluetooth only
west twister -p lp_em_cc2745r10_q1/cc2745r10_q1 -s tests/bluetooth --build-only

# View boards
west boards
```

---

## 🎉 סיום

**אתה מוכן!** בחר מה אתה רוצה לעשות:

1. **👶 מתחיל** → בצע את [🎯 דוגמא מהירה](#-דוגמא-מהירה)
2. **🧑‍💻 מפתח** → קרא [`docs/README.md`](docs/README.md)
3. **🧪 בדיקות** → קפוץ לסעיף [🧪 בדיקות ובדיקה](#-בדיקות-ובדיקה-qa)
4. **❓ יש לך שאלה** → בדוק [📞 שאלות נפוצות](#-שאלות-נפוצות)

---

**עדכון אחרון:** יולי 2025

🚀 **עכשיו בואו נתחיל!**
