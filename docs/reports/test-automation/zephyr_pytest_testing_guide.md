<div dir="rtl" style="text-align: right;">

# מדריך מקיף: שילוב Pytest עם Zephyr ו-Twister

מסמך זה הוא תרגום מלא ומורחב של התיעוד הרשמי של Zephyr בנושא שילוב `pytest` עם `Twister`, כולל הסברים נוספים משלי לכל חלק.

---

## תוכן עניינים

1.  [מבוא](#מבוא)
2.  [מדוע להשתמש ב-Pytest?](#מדוע-להשתמש-ב-pytest)
3.  [שילוב עם Twister](#שילוב-עם-twister)
4.  [איך ליצור Test של Pytest](#איך-ליצור-test-של-pytest)
5.  [Fixtures (מתקנים) - הליבה של עולם ה-Pytest](#fixtures)
6.  [Classes (מחלקות) - ה-API שלך לדבר עם ה-Device](#classes)
7.  [דוגמאות מהפרויקט](#דוגמאות-מהפרויקט)
8.  [שאלות נפוצות (FAQ)](#faq)
9.  [מגבלות](#מגבלות)
10. [נספח: Twister - פקודות חשובות](#נספח-twister)
11. [נספח: Zephyr Shell](#נספח-shell)

---

## מבוא

> **מה זה Pytest?**
> Pytest הוא Framework פופולרי לבדיקות ב-Python שמקל על כתיבת טסטים קטנים וקריאים, וניתן להרחיב אותו לבדיקות פונקציונליות מורכבות של אפליקציות וספריות.

הרעיון המרכזי הוא לנצל את החוזקות של Python (ספריות חינמיות, קלות שימוש, סקריפטינג) יחד עם מנגנון ה-Fixtures והפלאגינים של Pytest, כדי ליצור בדיקות שניתנות להרחבה ולשימוש חוזר.

### ההסבר שלי

הבעיה ש-Pytest פותר היא שלפעמים ה-"טסטים" שאנחנו רוצים להריץ הם לא רק "הקוד קומפל?", אלא יותר מורכבים. למשל:
*   "האם כשאני שולח פקודה X למכשיר, הוא מחזיר תשובה Y?"
*   "האם תהליך OTA (עדכון תוכנה מרחוק) הושלם בהצלחה?"
*   "האם שני מכשירים מצליחים להתחבר זה לזה?"

טסטים כאלה דורשים לוגיקה חיצונית, והכלי הזה נותן לך את התשתית לכתוב אותה.

---

## מדוע להשתמש ב-Pytest?

| יתרון | הסבר |
|---|---|
| **קלות כתיבה** | Python היא שפה פשוטה ואינטואיטיבית. |
| **Fixtures** | מנגנון חזק לשימוש חוזר בקוד (למשל: פתיחת חיבור סריאלי פעם אחת לכל הטסטים). |
| **Plugins** | ניתן להרחיב את יכולות Pytest בקלות. |
| **אינטגרציה** | Twister יודע לקרוא ל-Pytest כתת-תהליך ולאסוף את התוצאות. |

---

## שילוב עם Twister

### איך זה עובד?

1.  **גילוי טסטים:** Twister סורק את עץ הקבצים ומחפש קבצי `testcase.yaml` (או `sample.yaml`).
2.  **זיהוי Harness:** אם בתוך קובץ ה-YAML יש את השורה `harness: pytest`, Twister יודע שהטסט הזה הוא טסט Pytest.
3.  **בנייה:** Twister בונה את אפליקציית Zephyr עבור ה-Platform שנבחרה (למשל, `nrf52840dk`).
4.  **הרצה:** במקום להריץ את הקוד ישירות, Twister קורא ל-pytest כ-Subprocess.
5.  **העברת פרמטרים:** Twister מעביר ל-pytest פרמטרים חשובים דרך שורת הפקודה, כמו נתיב ל-Build, סוג ה-Device, וכו'.
6.  **דיווח:** כש-pytest מסיים, הוא יוצר קובץ `results.xml`. Twister קורא את הקובץ הזה וקובע אם הטסט עבר או נכשל.

```
┌───────────────────────────────────────────────────────────────────┐
│                        Twister                                    │
│                                                                   │
│   1. Scan for testcase.yaml                                       │
│   2. Build Zephyr App        ──────► zephyr.elf / zephyr.bin      │
│   3. if harness: pytest:                                          │
│        └── Call pytest as subprocess ───┐                         │
│                                         │                         │
│                           ┌─────────────▼────────────────┐        │
│                           │         Pytest               │        │
│                           │                              │        │
│                           │  - Fixtures (dut, shell)     │        │
│                           │  - Your test_*.py files      │        │
│                           │  - Talk to Device            │        │
│                           │  - Generate results.xml      │        │
│                           └─────────────┬────────────────┘        │
│                                         │                         │
│   4. Read results.xml     ◄─────────────┘                         │
│   5. Report PASS/FAIL                                             │
└───────────────────────────────────────────────────────────────────┘
```

### מה לא צריך לעשות?

כברירת מחדל, אין צורך בשום הגדרה מיוחדת. ה-Plugin של `pytest-twister-harness` הוא חלק מעץ הקוד של Zephyr. Twister דואג להוסיף אותו ל-`PYTHONPATH` ולהריץ את pytest עם הארגומנט הנכון.

---

## איך ליצור Test של Pytest

### מבנה התיקייה המומלץ

```
my_test_project/
├── pytest/                 <-- תיקיית הטסטים של Pytest
│   └── test_my_feature.py  <-- קובץ הטסט עצמו (חייב להתחיל ב-test_)
├── src/
│   └── main.c              <-- קוד ה-Zephyr שלך
├── CMakeLists.txt
├── prj.conf
└── testcase.yaml           <-- קובץ הקונפיגורציה של Twister
```

### קובץ `testcase.yaml` לדוגמה

```yaml
tests:
  my_project.my_feature.test:
    harness: pytest          # <-- זה מה שמפעיל את Pytest!
    filter: CONFIG_SERIAL and dt_chosen_enabled("zephyr,shell-uart")
    integration_platforms:
      - native_sim
      - qemu_cortex_m3
    tags:
      - my_tag
```

**הסבר:**
*   `tests:` - שורש הקונפיגורציה.
*   `my_project.my_feature.test:` - השם הייחודי של תרחיש הבדיקה.
*   `harness: pytest` - **זוהי השורה הקריטית!** היא אומרת ל-Twister להשתמש ב-Pytest.
*   `filter:` - תנאי קימפול (פלטפורמות שעומדות בתנאי הזה בלבד ירוצו).
*   `integration_platforms:` - רשימת פלטפורמות להריץ עליהן כברירת מחדל בטסטים של אינטגרציה.
*   `tags:` - תגיות לסינון הרצות.

### מיקום הטסטים של Pytest

כברירת מחדל, Pytest מחפש טסטים בתיקייה בשם `pytest` הנמצאת ליד תיקיית הקוד. אם רוצים לשנות את המיקום, משתמשים ב-`pytest_root` תחת `harness_config`:

```yaml
tests:
  my_project.my_test:
    harness: pytest
    harness_config:
      pytest_root:
        - "tests/my_custom_pytest_dir"
        - "pytest/test_specific_file.py::test_specific_function"  # ניתן לציין פונקציה ספציפית
```

### העברת ארגומנטים ל-Pytest

יש שתי דרכים:

1.  **מתוך `testcase.yaml`:**
    ```yaml
    harness_config:
      pytest_args:
        - "-k test_shell_print_help"  # הרץ רק פונקציה ששמה מכיל את המחרוזת הזו
    ```

2.  **משורת הפקודה של Twister:**
    ```bash
    west twister ... --pytest-args='-k test_shell_print_version'
    ```
    הארגומנטים משורת הפקודה ידרסו את אלו מקובץ ה-YAML אם יש התנגשות.

---

## Fixtures

Fixtures הם אחד המנגנונים החזקים ביותר ב-Pytest. הם מאפשרים לך להגדיר "הכנה" (Setup) ו"ניקוי" (Teardown) לטסטים שלך, ולשתף משאבים בין טסטים שונים.

ה-Plugin `pytest-twister-harness` מספק לך מספר Fixtures מובנים.

### `dut` (Device Under Test)

זהו ה-Fixture הבסיסי והחשוב ביותר. הוא נותן לך גישה לאובייקט מסוג `DeviceAdapter` שמייצג את המכשיר שאתה בודק.

*   **מה הוא עושה?** אתחול מלא של ה-Device: טעינת קובץ, Flash, פתיחת חיבור סריאלי.
*   **סוגים נתמכים:** `native`, `qemu`, `hardware`. ה-API זהה לכל הסוגים, מה שמאפשר לכתוב טסטים אחידים.
*   **Scope:** ניתן לשלוט בטווח (Scope) של ה-Fixture באמצעות `pytest_dut_scope` ב-YAML. ברירת המחדל היא `function` (Flash חדש לכל פונקציית טסט). אפשר לשנות ל-`session` (Flash אחד לכל ריצת Pytest).

```python
from twister_harness import DeviceAdapter

def test_hello_world(dut: DeviceAdapter):
    # קרא שורות עד שתמצא את הפלט הרצוי, או עד Timeout
    lines = dut.readlines_until(regex='Hello World')
    assert lines  # וודא שהמערך לא ריק
```

### `shell`

Fixture ייחודי לאפליקציות שמשתמשות ב-Zephyr Shell. הוא יורש מ-`dut` ומוסיף מתודות נוחות לאינטראקציה עם ה-Shell.

*   **`shell.exec_command(cmd)`:** שולח פקודה וממתין ל-Prompt.
*   **`shell.wait_for_prompt()`:** ממתין עד שה-Shell מוכן.
*   **`shell.get_filtered_output(lines)`:** מסנן שורות ריקות, Prompts ולוגים.

```python
from twister_harness import Shell

def test_shell_help(shell: Shell):
    lines = shell.exec_command('help')
    assert 'Available commands:' in lines
```

### `mcumgr`

Fixture לעבודה עם ה-MCU Manager (לעדכוני תוכנה ועוד). דורש התקנה של `mcumgr` במערכת.

### `unlaunched_dut`

דומה ל-`dut`, אבל לא מאתחל את ה-Device אוטומטית. שימושי אם צריך שליטה מלאה על תהליך ההפעלה.

```python
from twister_harness import DeviceAdapter

def test_custom_launch(unlaunched_dut: DeviceAdapter):
    # ... עשה משהו לפני ההפעלה ...
    unlaunched_dut.launch()
    unlaunched_dut.readlines_until(regex='Booting Zephyr')
```

---

## Classes

### `DeviceAdapter`

זוהי המחלקה המרכזית שמהווה את ה-API לתקשורת עם ה-Device. היא מופשטת מסוג ה-Device (חומרה, QEMU, Native Sim).

**מתודות עיקריות:**

| מתודה | תיאור |
|---|---|
| `launch()` | מאתחל את ה-Device (Flash לחומרה, הרצה לסימולטור). |
| `close()` | סוגר את החיבור ומנקה משאבים. |
| `readline()` | קורא שורה אחת מהפלט. |
| `readlines()` | קורא את כל השורות הזמינות בבאפר. |
| `readlines_until(regex=..., timeout=...)` | קורא שורות עד שמתקיים Regex או נגמר ה-Timeout. |
| `write(data: bytes)` | כותב Bytes ל-Device. |

**דוגמה:**
```python
lines = dut.readlines_until(regex='Bluetooth initialized', timeout=10)
```

### `Shell`

יורש מ-`DeviceAdapter` ומוסיף פונקציונליות ייחודית ל-Shell.

| מתודה | תיאור |
|---|---|
| `exec_command(cmd)` | שולח פקודה, מוסיף Enter, ומחזיר את הפלט. |
| `wait_for_prompt()` | ממתין ל-Prompt של Shell (למשל `uart:~$`). |
| `get_filtered_output(lines)` | מסנן Prompts והודעות Log מהפלט. |

---

## דוגמאות מהפרויקט

### קובץ `test_shell.py` (מתוך `samples/subsys/testsuite/pytest/shell`)

```python
# /zephyr/samples/subsys/testsuite/pytest/shell/pytest/test_shell.py
import logging
from twister_harness import Shell

logger = logging.getLogger(__name__)

def test_shell_print_help(shell: Shell):
    logger.info('send "help" command')
    lines = shell.exec_command('help')
    assert 'Available commands:' in lines, 'expected response not found'
    logger.info('response is valid')

def test_shell_print_version(shell: Shell):
    logger.info('send "kernel version" command')
    lines = shell.exec_command('kernel version')
    assert any(['Zephyr version' in line for line in lines]), 'expected response not found'
    logger.info('response is valid')
```

**ניתוח:**
1.  **Import:** מייבאים את `Shell` מ-`twister_harness`.
2.  **Fixture:** כל פונקציית טסט מקבלת `shell` כפרמטר. Pytest דואג להזריק את ה-Fixture.
3.  **Action:** שולחים פקודה עם `shell.exec_command()`.
4.  **Assertion:** בודקים שהפלט מכיל את המחרוזת הצפויה.

---

## FAQ

### איך לצרוב/להריץ את האפליקציה רק פעם אחת לכל Session?

השתמש ב-`pytest_dut_scope`:

```yaml
harness: pytest
harness_config:
  pytest_dut_scope: session  # אפשרויות: function, class, module, session
```

### איך להריץ רק טסט אחד ספציפי?

1.  **מתוך YAML:**
    ```yaml
    harness_config:
      pytest_root:
        - "pytest/test_shell.py::test_shell_print_help"
    ```
2.  **משורת הפקודה:**
    ```bash
    west twister ... --pytest-args='-k test_shell_print_help'
    ```

### איך לדעת אם אני רץ על חומרה או סימולטור?

```python
def test_hardware_specific(dut: DeviceAdapter):
    device_type = dut.device_config.type
    if device_type == 'hardware':
        # לוגיקה ייחודית לחומרה
        pass
    elif device_type == 'native':
        # לוגיקה ייחודית לסימולטור
        pass
```

### איך להריץ שוב בלי לבנות מחדש?

הוסף `--test-only` לפקודת Twister:

```bash
west twister ... --test-only
```

---

## מגבלות

*   לא כל סוג ה-Platform נתמך עדיין ב-Plugin.
*   הרצה במקביל (`pytest-xdist`) לא נבדקה רשמית ועלולה לגרום לבעיות.

---

## נספח: Twister - פקודות חשובות

| פקודה | תיאור |
|---|---|
| `west twister -T <path>` | סרוק והרץ טסטים מתיקייה מסוימת. |
| `west twister -p <platform>` | הרץ רק על Platform מסוים (למשל `nrf52840dk/nrf52840`). |
| `west twister -b` / `--build-only` | בנה בלבד, לא להריץ. |
| `west twister --test-only` | הרץ את הטסטים ללא בנייה מחדש. |
| `west twister --device-testing --device-serial /dev/ttyACM0` | הרץ על חומרה פיזית. |
| `west twister -s <test_id>` | הרץ תרחיש בדיקה ספציפי. |
| `west twister --pytest-args='-k <filter>'` | העבר ארגומנטים ל-Pytest. |
| `west twister --hardware-map <file.yaml>` | טען מפת חומרה להרצה על מספר מכשירים. |
| `west twister -v` / `-vv` | הגבר את רמת ה-Verbosity. |

---

## נספח: Zephyr Shell

ה-Shell של Zephyr הוא מודול שמאפשר ליצור ממשק שורת פקודה במבובנייה. הוא דומה ל-Unix Shell ומספק:

*   תמיכה ב-Tab Completion.
*   היסטוריית פקודות.
*   עריכת שורה (Backspace, Delete, Home, End).
*   תמיכה ב-Wildcards (* ?).
*   פקודות מובנות: `clear`, `history`, `help`.

### Backends (שכבות תקשורת) נתמכות:

*   UART (הנפוץ ביותר)
*   USB CDC ACM
*   Telnet
*   Bluetooth LE (NUS)
*   Segger RTT
*   RPMSG
*   MQTT

### הפעלת Shell באפליקציה שלך

1.  הוסף ל-`prj.conf`:
    ```ini
    CONFIG_SHELL=y
    ```

2.  צור פקודות משלך בקוד C:
    ```c
    #include <zephyr/shell/shell.h>

    static int cmd_my_handler(const struct shell *sh, size_t argc, char **argv)
    {
        shell_print(sh, "Hello from my command!");
        return 0;
    }

    SHELL_CMD_REGISTER(mycommand, NULL, "My custom command", cmd_my_handler);
    ```

### פקודות מובנות:

| פקודה | תיאור |
|---|---|
| `help` | הצג את כל הפקודות הזמינות. |
| `clear` | נקה מסך. |
| `history` | הצג היסטוריית פקודות. |
| `kernel version` | הצג גרסת Zephyr. |
| `shell echo <on/off>` | הפעל/כבה Echo. |

---

## סיכום

| שאלה | תשובה |
|---|---|
| מה מפעיל את ה-Pytest? | `harness: pytest` בקובץ `testcase.yaml`. |
| איפה ה-Tests? | בתיקיית `pytest/` ליד הקוד, או במיקום שהוגדר ב-`pytest_root`. |
| מה ה-Fixture העיקרי? | `dut` (או `shell` לאפליקציות Shell). |
| איך לשלוח פקודה ל-Shell? | `shell.exec_command('my_command')`. |
| איך לבדוק את הפלט? | `dut.readlines_until(regex='...')` ואז `assert`. |

</div>
